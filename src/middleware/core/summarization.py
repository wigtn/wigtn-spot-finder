"""
Summarization Middleware with Fallback Strategy.
Automatically summarizes old messages when context limit is exceeded.
"""

import logging
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage

from src.config.settings import settings
from src.services.llm.vllm_client import get_summarization_model
from src.utils.tokens import count_tokens, count_messages_tokens

logger = logging.getLogger(__name__)

# Summarization prompt template
SUMMARIZATION_PROMPT = """Summarize the following conversation concisely, preserving key information:
- User's travel plans and preferences
- Important places, dates, and times mentioned
- Any specific requests or constraints
- Decisions made during the conversation

Keep the summary under 500 words. Focus on actionable information.

Conversation to summarize:
{conversation}

Summary:"""

# Fallback summarization (extractive) - no LLM required
EXTRACTIVE_KEYWORDS = [
    "want", "need", "prefer", "like", "visit", "go", "travel",
    "hotel", "restaurant", "food", "museum", "palace", "temple",
    "subway", "bus", "taxi", "walk",
    "morning", "afternoon", "evening", "night",
    "budget", "cheap", "expensive", "luxury",
    "day", "days", "week", "hour", "hours",
    "seoul", "busan", "jeju", "incheon", "gyeongju",
]


class SummarizationError(Exception):
    """Exception raised when summarization fails."""
    pass


class SummarizationMiddleware:
    """
    Middleware to summarize conversation history when context limit is exceeded.

    Fallback Strategy:
    1. Try LLM-based summarization (best quality)
    2. If timeout/error, try with reduced content
    3. If still failing, use extractive summarization
    4. Last resort: simple truncation with marker
    """

    def __init__(
        self,
        soft_limit: int | None = None,
        hard_limit: int | None = None,
        summary_max_tokens: int = 500,
        timeout_seconds: float = 30.0,
    ):
        """
        Initialize the summarization middleware.

        Args:
            soft_limit: Token count to start considering summarization
            hard_limit: Token count that triggers mandatory summarization
            summary_max_tokens: Maximum tokens for generated summary
            timeout_seconds: Timeout for LLM summarization
        """
        self.soft_limit = soft_limit or settings.context_soft_limit_tokens
        self.hard_limit = hard_limit or settings.context_hard_limit_tokens
        self.summary_max_tokens = summary_max_tokens
        self.timeout_seconds = timeout_seconds

        self._model = None

    @property
    def model(self):
        """Lazy load summarization model."""
        if self._model is None:
            self._model = get_summarization_model()
        return self._model

    async def process(
        self,
        messages: list[BaseMessage],
        removed_messages: list[BaseMessage] | None = None,
        state: dict[str, Any] | None = None,
    ) -> tuple[list[BaseMessage], str | None, dict[str, Any]]:
        """
        Process messages and summarize if necessary.

        Args:
            messages: Current conversation messages
            removed_messages: Messages that were trimmed (to be summarized)
            state: Optional state dict

        Returns:
            Tuple of (updated messages, summary text, updated state)
        """
        state = state or {}

        # If no removed messages, no summarization needed
        if not removed_messages:
            return messages, None, state

        logger.info(f"Summarizing {len(removed_messages)} removed messages")

        # Try summarization with fallback strategy
        summary = await self._summarize_with_fallback(removed_messages)

        if summary:
            # Create summary message and prepend to conversation
            summary_message = SystemMessage(
                content=f"[Previous conversation summary]\n{summary}\n[End of summary]"
            )

            # Find where to insert (after system prompt, before conversation)
            system_messages = [m for m in messages if isinstance(m, SystemMessage)]
            other_messages = [m for m in messages if not isinstance(m, SystemMessage)]

            # Combine: system prompts + summary + conversation
            updated_messages = system_messages + [summary_message] + other_messages

            state["summarization_performed"] = True
            state["summary_token_count"] = count_tokens(summary)
            state["messages_summarized"] = len(removed_messages)

            logger.info(
                f"Summarization complete: {len(removed_messages)} messages -> "
                f"{state['summary_token_count']} tokens"
            )

            return updated_messages, summary, state

        # If all fallbacks failed, just return original messages
        logger.warning("All summarization strategies failed")
        state["summarization_failed"] = True
        return messages, None, state

    async def _summarize_with_fallback(
        self,
        messages: list[BaseMessage],
    ) -> str | None:
        """
        Attempt summarization with fallback strategies.

        Strategy order:
        1. Full LLM summarization
        2. LLM with reduced content
        3. Extractive summarization
        4. Simple truncation
        """
        # Strategy 1: Full LLM summarization
        try:
            summary = await self._llm_summarize(messages)
            if summary:
                logger.debug("LLM summarization succeeded")
                return summary
        except Exception as e:
            logger.warning(f"LLM summarization failed: {e}")

        # Strategy 2: LLM with reduced content (last 50% of messages)
        try:
            reduced_messages = messages[len(messages) // 2:]
            summary = await self._llm_summarize(reduced_messages)
            if summary:
                # Add note about partial summarization
                summary = f"[Partial summary - earlier context omitted]\n{summary}"
                logger.debug("Reduced LLM summarization succeeded")
                return summary
        except Exception as e:
            logger.warning(f"Reduced LLM summarization failed: {e}")

        # Strategy 3: Extractive summarization (no LLM)
        try:
            summary = self._extractive_summarize(messages)
            if summary:
                logger.debug("Extractive summarization succeeded")
                return summary
        except Exception as e:
            logger.warning(f"Extractive summarization failed: {e}")

        # Strategy 4: Simple truncation with marker
        try:
            summary = self._truncation_fallback(messages)
            logger.debug("Truncation fallback used")
            return summary
        except Exception as e:
            logger.error(f"All summarization strategies failed: {e}")
            return None

    async def _llm_summarize(self, messages: list[BaseMessage]) -> str | None:
        """Summarize using LLM."""
        import asyncio

        # Format messages for summarization
        conversation_text = self._format_messages_for_summary(messages)

        # Check if content is too long
        if count_tokens(conversation_text) > 4000:
            # Truncate to fit
            conversation_text = conversation_text[:12000]  # Rough char limit

        prompt = SUMMARIZATION_PROMPT.format(conversation=conversation_text)

        try:
            # Use asyncio.wait_for for timeout
            response = await asyncio.wait_for(
                self.model.ainvoke([HumanMessage(content=prompt)]),
                timeout=self.timeout_seconds,
            )

            summary = response.content.strip()

            # Validate summary
            if summary and len(summary) > 50:  # Minimum viable summary
                return summary

            return None

        except asyncio.TimeoutError:
            logger.warning(f"LLM summarization timed out after {self.timeout_seconds}s")
            raise
        except Exception as e:
            logger.warning(f"LLM summarization error: {e}")
            raise

    def _extractive_summarize(self, messages: list[BaseMessage]) -> str:
        """
        Extractive summarization - extract key sentences without LLM.
        Uses keyword matching to identify important content.
        """
        important_content = []

        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            content_lower = content.lower()

            # Check for keyword matches
            keyword_count = sum(1 for kw in EXTRACTIVE_KEYWORDS if kw in content_lower)

            # Include messages with 2+ keywords or that are user messages
            if keyword_count >= 2 or isinstance(msg, HumanMessage):
                # Truncate long messages
                if len(content) > 200:
                    content = content[:200] + "..."

                role = "User" if isinstance(msg, HumanMessage) else "Assistant"
                important_content.append(f"- {role}: {content}")

        if important_content:
            # Limit to most recent important content
            recent_content = important_content[-10:]
            summary = "Key points from previous conversation:\n" + "\n".join(recent_content)
            return summary

        return None

    def _truncation_fallback(self, messages: list[BaseMessage]) -> str:
        """
        Last resort: simple truncation with context marker.
        """
        # Get first and last few messages
        if len(messages) <= 4:
            return None

        first_messages = messages[:2]
        last_messages = messages[-2:]

        parts = []

        for msg in first_messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            parts.append(f"{role}: {content[:100]}...")

        parts.append(f"[... {len(messages) - 4} messages omitted ...]")

        for msg in last_messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            role = "User" if isinstance(msg, HumanMessage) else "Assistant"
            parts.append(f"{role}: {content[:100]}...")

        return "\n".join(parts)

    def _format_messages_for_summary(self, messages: list[BaseMessage]) -> str:
        """Format messages into a string for summarization."""
        lines = []

        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)

            if isinstance(msg, HumanMessage):
                lines.append(f"User: {content}")
            elif isinstance(msg, AIMessage):
                lines.append(f"Assistant: {content}")
            elif isinstance(msg, SystemMessage):
                continue  # Skip system messages in summary
            else:
                lines.append(f"Message: {content}")

        return "\n\n".join(lines)


def create_summarization_middleware(
    soft_limit: int | None = None,
    hard_limit: int | None = None,
) -> SummarizationMiddleware:
    """Factory function for creating summarization middleware."""
    return SummarizationMiddleware(
        soft_limit=soft_limit,
        hard_limit=hard_limit,
    )
