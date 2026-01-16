"""
Input Validation Middleware.
Validates and sanitizes user input to prevent prompt injection and other attacks.
"""

import logging
import re
from typing import Any

from src.config.settings import settings

logger = logging.getLogger(__name__)


# Patterns that may indicate prompt injection attempts
PROMPT_INJECTION_PATTERNS = [
    # Instruction override attempts
    r"ignore\s+(previous|all|above)\s+(instructions?|prompts?|rules?)",
    r"disregard\s+(previous|all|above)",
    r"forget\s+(everything|all|previous)",
    r"new\s+instructions?:",
    r"system\s*:\s*",
    r"<\|system\|>",
    r"<\|assistant\|>",

    # Role playing attempts
    r"you\s+are\s+now\s+(a\s+)?different",
    r"pretend\s+(to\s+be|you\s+are)",
    r"act\s+as\s+(if|a)",
    r"roleplay\s+as",

    # Jailbreak attempts
    r"DAN\s+mode",
    r"developer\s+mode",
    r"bypass\s+(filters?|restrictions?|safety)",
    r"unlock\s+(hidden|secret)",

    # Instruction injection
    r"\[\s*INST\s*\]",
    r"\[\s*SYS(TEM)?\s*\]",
    r"</?(system|user|assistant)>",
]

# Maximum input length (characters)
MAX_INPUT_LENGTH = 4000


class InputValidationError(Exception):
    """Exception raised when input validation fails."""

    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class InputValidationMiddleware:
    """
    Middleware to validate and sanitize user input.

    Checks for:
    1. Input length limits
    2. Prompt injection patterns
    3. Malicious content
    4. Character encoding issues
    """

    def __init__(
        self,
        max_length: int = MAX_INPUT_LENGTH,
        check_injection: bool = True,
        custom_patterns: list[str] | None = None,
    ):
        """
        Initialize the validation middleware.

        Args:
            max_length: Maximum allowed input length
            check_injection: Whether to check for prompt injection
            custom_patterns: Additional regex patterns to block
        """
        self.max_length = max_length
        self.check_injection = check_injection

        # Compile patterns for efficiency
        patterns = PROMPT_INJECTION_PATTERNS + (custom_patterns or [])
        self.injection_patterns = [
            re.compile(p, re.IGNORECASE | re.MULTILINE) for p in patterns
        ]

    def validate(self, text: str) -> tuple[str, dict[str, Any]]:
        """
        Validate and sanitize input text.

        Args:
            text: User input text

        Returns:
            Tuple of (sanitized text, validation metadata)

        Raises:
            InputValidationError: If validation fails
        """
        metadata = {
            "original_length": len(text),
            "sanitized": False,
            "warnings": [],
        }

        # Check for empty input
        if not text or not text.strip():
            raise InputValidationError("Empty input", "EMPTY_INPUT")

        # Check length
        if len(text) > self.max_length:
            raise InputValidationError(
                f"Input too long: {len(text)} characters (max: {self.max_length})",
                "INPUT_TOO_LONG",
            )

        # Sanitize whitespace
        sanitized = self._normalize_whitespace(text)

        # Check for prompt injection
        if self.check_injection:
            injection_match = self._check_prompt_injection(sanitized)
            if injection_match:
                logger.warning(
                    f"Prompt injection detected: pattern='{injection_match}', "
                    f"input_preview='{sanitized[:100]}...'"
                )
                raise InputValidationError(
                    "Input contains disallowed patterns",
                    "PROMPT_INJECTION_DETECTED",
                )

        # Escape potentially dangerous characters
        sanitized = self._escape_special_chars(sanitized)

        if sanitized != text:
            metadata["sanitized"] = True
            metadata["sanitized_length"] = len(sanitized)

        return sanitized, metadata

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        # Replace multiple spaces/newlines with single ones
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _check_prompt_injection(self, text: str) -> str | None:
        """Check for prompt injection patterns."""
        for pattern in self.injection_patterns:
            match = pattern.search(text)
            if match:
                return match.group(0)
        return None

    def _escape_special_chars(self, text: str) -> str:
        """Escape special characters that might be interpreted as markup."""
        # Escape potential markdown/HTML injection
        # But be careful not to break legitimate content
        replacements = {
            "<script": "&lt;script",
            "</script": "&lt;/script",
            "javascript:": "javascript&#58;",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text


def create_input_validation_middleware(
    max_length: int = MAX_INPUT_LENGTH,
    check_injection: bool = True,
    custom_patterns: list[str] | None = None,
) -> InputValidationMiddleware:
    """Factory function for creating input validation middleware."""
    return InputValidationMiddleware(
        max_length=max_length,
        check_injection=check_injection,
        custom_patterns=custom_patterns,
    )


# Convenience function for quick validation
def validate_input(text: str) -> str:
    """
    Validate input using default settings.

    Args:
        text: User input text

    Returns:
        Sanitized text

    Raises:
        InputValidationError: If validation fails
    """
    middleware = InputValidationMiddleware()
    sanitized, _ = middleware.validate(text)
    return sanitized
