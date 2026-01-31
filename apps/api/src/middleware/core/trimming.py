"""
Context Trimming Middleware.
Manages context window size by removing old messages when limits are exceeded.
"""

import logging
from typing import Any

from langchain_core.messages import BaseMessage, SystemMessage

from src.config.settings import settings
from src.utils.tokens import count_tokens, count_messages_tokens

logger = logging.getLogger(__name__)


class ContextTrimmingMiddleware:
    """
    Middleware to trim conversation context to fit within token limits.

    Strategy:
    1. Always keep system message
    2. Always keep most recent N messages (configurable)
    3. Remove oldest messages when soft limit is exceeded
    4. Hard limit triggers summarization (handled by SummarizationMiddleware)
    """

    def __init__(
        self,
        soft_limit: int | None = None,
        hard_limit: int | None = None,
        keep_recent: int | None = None,
    ):
        """
        Initialize the trimming middleware.

        Args:
            soft_limit: Token count to start trimming (default: 6000)
            hard_limit: Token count to trigger summarization (default: 8000)
            keep_recent: Number of recent messages to always keep (default: 20)
        """
        self.soft_limit = soft_limit or settings.context_soft_limit_tokens
        self.hard_limit = hard_limit or settings.context_hard_limit_tokens
        self.keep_recent = keep_recent or settings.recent_messages_count

    async def process(
        self,
        messages: list[BaseMessage],
        state: dict[str, Any] | None = None,
    ) -> tuple[list[BaseMessage], dict[str, Any]]:
        """
        Process messages and trim if necessary.

        Args:
            messages: List of conversation messages
            state: Optional state dict to update

        Returns:
            Tuple of (trimmed messages, updated state)
        """
        state = state or {}

        # Count current tokens
        total_tokens = count_messages_tokens(messages)
        state["context_token_count"] = total_tokens

        logger.debug(f"Context tokens: {total_tokens} (soft: {self.soft_limit}, hard: {self.hard_limit})")

        # Check if trimming is needed
        if total_tokens <= self.soft_limit:
            state["summarization_needed"] = False
            return messages, state

        # Separate system message from conversation
        system_messages = [m for m in messages if isinstance(m, SystemMessage)]
        conversation_messages = [m for m in messages if not isinstance(m, SystemMessage)]

        # If we have fewer messages than keep_recent, no trimming possible
        if len(conversation_messages) <= self.keep_recent:
            # Check if hard limit exceeded (needs summarization)
            state["summarization_needed"] = total_tokens > self.hard_limit
            return messages, state

        # Trim from the oldest messages, keeping the most recent
        trimmed_messages = []
        removed_messages = []
        target_tokens = self.soft_limit - count_messages_tokens(system_messages)

        # Start from the end (most recent) and work backwards
        recent_messages = conversation_messages[-self.keep_recent :]
        older_messages = conversation_messages[: -self.keep_recent]

        # Count tokens in recent messages
        recent_tokens = count_messages_tokens(recent_messages)

        # Add older messages from most recent until we hit the limit
        remaining_budget = target_tokens - recent_tokens
        kept_older = []

        for msg in reversed(older_messages):
            msg_tokens = count_tokens(msg.content if hasattr(msg, "content") else str(msg))
            if remaining_budget >= msg_tokens:
                kept_older.insert(0, msg)
                remaining_budget -= msg_tokens
            else:
                removed_messages.insert(0, msg)

        # Combine: system + kept older + recent
        trimmed_messages = system_messages + kept_older + recent_messages

        # Update state
        new_token_count = count_messages_tokens(trimmed_messages)
        state["context_token_count"] = new_token_count
        state["messages_removed"] = len(removed_messages)
        state["removed_messages"] = removed_messages  # For potential summarization
        state["summarization_needed"] = len(removed_messages) > 0

        logger.info(
            f"Trimmed context: {total_tokens} -> {new_token_count} tokens, "
            f"removed {len(removed_messages)} messages"
        )

        return trimmed_messages, state


def create_trimming_middleware(
    soft_limit: int | None = None,
    hard_limit: int | None = None,
    keep_recent: int | None = None,
) -> ContextTrimmingMiddleware:
    """Factory function for creating trimming middleware."""
    return ContextTrimmingMiddleware(
        soft_limit=soft_limit,
        hard_limit=hard_limit,
        keep_recent=keep_recent,
    )
