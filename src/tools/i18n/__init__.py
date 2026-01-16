"""
Internationalization tools for translation.
"""

from src.tools.i18n.translation import (
    translate,
    translate_to_korean,
    translate_from_korean,
    get_korean_phrase,
    translate_text,
    detect_language,
    translation_tools,
    SUPPORTED_LANGUAGES,
)

__all__ = [
    "translate",
    "translate_to_korean",
    "translate_from_korean",
    "get_korean_phrase",
    "translate_text",
    "detect_language",
    "translation_tools",
    "SUPPORTED_LANGUAGES",
]
