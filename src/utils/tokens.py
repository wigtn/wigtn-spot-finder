"""
Token counting utilities.
Uses transformers tokenizer for accurate token counting.
"""

import logging
from functools import lru_cache
from typing import Any

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Global tokenizer instance
_tokenizer = None


def get_tokenizer():
    """
    Get or create the tokenizer instance.
    Uses the same model's tokenizer as vLLM for accuracy.
    """
    global _tokenizer

    if _tokenizer is None:
        try:
            from transformers import AutoTokenizer

            # Try to load tokenizer for the vLLM model
            model_name = settings.vllm_model_name
            logger.info(f"Loading tokenizer for model: {model_name}")

            _tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,  # Required for some models like Qwen
            )
            logger.info(f"Tokenizer loaded successfully: {type(_tokenizer).__name__}")

        except Exception as e:
            logger.warning(f"Failed to load model tokenizer: {e}. Using tiktoken fallback.")
            # Fallback to tiktoken (GPT-4 tokenizer as approximation)
            try:
                import tiktoken

                _tokenizer = tiktoken.encoding_for_model("gpt-4")
                logger.info("Using tiktoken (gpt-4) as fallback tokenizer")
            except Exception as e2:
                logger.error(f"Failed to load fallback tokenizer: {e2}")
                raise RuntimeError("No tokenizer available") from e2

    return _tokenizer


def count_tokens(text: str) -> int:
    """
    Count tokens in a text string.

    Args:
        text: Text to count tokens for

    Returns:
        Number of tokens
    """
    if not text:
        return 0

    tokenizer = get_tokenizer()

    try:
        # transformers tokenizer
        if hasattr(tokenizer, "encode"):
            tokens = tokenizer.encode(text, add_special_tokens=False)
            return len(tokens)
        # tiktoken tokenizer
        elif hasattr(tokenizer, "encode_ordinary"):
            tokens = tokenizer.encode_ordinary(text)
            return len(tokens)
        else:
            # Rough estimation fallback
            return len(text) // 4
    except Exception as e:
        logger.warning(f"Token counting failed: {e}. Using estimation.")
        return len(text) // 4


def count_messages_tokens(messages: list[Any]) -> int:
    """
    Count total tokens in a list of messages.

    Args:
        messages: List of message objects or dicts

    Returns:
        Total token count
    """
    total = 0

    for msg in messages:
        # Handle different message formats
        if hasattr(msg, "content"):
            content = msg.content
        elif isinstance(msg, dict) and "content" in msg:
            content = msg["content"]
        else:
            content = str(msg)

        total += count_tokens(content)

        # Add overhead for message structure (role, etc.)
        # Approximately 4 tokens per message for role and formatting
        total += 4

    return total


def estimate_response_tokens(prompt_tokens: int, max_response: int | None = None) -> int:
    """
    Estimate tokens that will be used for response.

    Args:
        prompt_tokens: Number of tokens in the prompt
        max_response: Maximum response tokens (default from settings)

    Returns:
        Estimated response tokens
    """
    max_response = max_response or settings.llm_max_tokens

    # Assume response will use about 50% of max tokens on average
    estimated = min(max_response, max_response // 2)

    return estimated


def check_token_budget(
    messages: list[Any],
    soft_limit: int | None = None,
    hard_limit: int | None = None,
) -> dict[str, Any]:
    """
    Check if messages fit within token budget.

    Args:
        messages: List of messages to check
        soft_limit: Soft token limit (start trimming)
        hard_limit: Hard token limit (must summarize)

    Returns:
        Dict with token info and recommendations
    """
    soft_limit = soft_limit or settings.context_soft_limit_tokens
    hard_limit = hard_limit or settings.context_hard_limit_tokens

    current_tokens = count_messages_tokens(messages)
    response_estimate = estimate_response_tokens(current_tokens)
    total_estimate = current_tokens + response_estimate

    return {
        "current_tokens": current_tokens,
        "estimated_response": response_estimate,
        "total_estimate": total_estimate,
        "soft_limit": soft_limit,
        "hard_limit": hard_limit,
        "within_soft": current_tokens <= soft_limit,
        "within_hard": current_tokens <= hard_limit,
        "needs_trimming": current_tokens > soft_limit,
        "needs_summarization": current_tokens > hard_limit,
        "utilization_percent": round((current_tokens / hard_limit) * 100, 1),
    }


@lru_cache(maxsize=1000)
def cached_count_tokens(text: str) -> int:
    """
    Cached version of token counting for repeated strings.
    Uses LRU cache to avoid re-counting the same strings.
    """
    return count_tokens(text)
