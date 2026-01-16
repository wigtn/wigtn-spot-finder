"""
Translation Tool using Papago API.
Provides translation between Korean and other languages.
"""

import logging
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Papago API endpoint
PAPAGO_TRANSLATE_URL = "https://openapi.naver.com/v1/papago/n2mt"
PAPAGO_DETECT_URL = "https://openapi.naver.com/v1/papago/detectLangs"

# Supported language pairs
SUPPORTED_LANGUAGES = {
    "ko": "Korean",
    "en": "English",
    "ja": "Japanese",
    "zh-CN": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "th": "Thai",
    "de": "German",
    "ru": "Russian",
    "es": "Spanish",
    "it": "Italian",
    "fr": "French",
}


class TranslationResult(BaseModel):
    """Translation result model."""

    original_text: str
    translated_text: str
    source_language: str
    target_language: str


async def detect_language(text: str) -> str | None:
    """
    Detect the language of text using Papago.

    Args:
        text: Text to analyze

    Returns:
        Language code or None
    """
    if not settings.naver_map_client_id or not settings.naver_map_client_secret:
        logger.warning("Naver API credentials not configured")
        return None

    headers = {
        "X-Naver-Client-Id": settings.naver_map_client_id,
        "X-Naver-Client-Secret": settings.naver_map_client_secret,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                PAPAGO_DETECT_URL,
                headers=headers,
                data={"query": text[:1000]},  # Limit text length
            )
            response.raise_for_status()

            data = response.json()
            return data.get("langCode")

    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return None


async def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
) -> TranslationResult | None:
    """
    Translate text using Papago API.

    Args:
        text: Text to translate
        source_lang: Source language code
        target_lang: Target language code

    Returns:
        TranslationResult or None
    """
    if not settings.naver_map_client_id or not settings.naver_map_client_secret:
        logger.warning("Naver API credentials not configured")
        return None

    headers = {
        "X-Naver-Client-Id": settings.naver_map_client_id,
        "X-Naver-Client-Secret": settings.naver_map_client_secret,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "source": source_lang,
        "target": target_lang,
        "text": text,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                PAPAGO_TRANSLATE_URL,
                headers=headers,
                data=data,
            )
            response.raise_for_status()

            result = response.json()
            translated = result.get("message", {}).get("result", {}).get("translatedText", "")

            if translated:
                return TranslationResult(
                    original_text=text,
                    translated_text=translated,
                    source_language=source_lang,
                    target_language=target_lang,
                )

            return None

    except httpx.HTTPStatusError as e:
        logger.error(f"Papago API error: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return None


@tool
async def translate(
    text: str,
    target_language: str = "en",
    source_language: str | None = None,
) -> str:
    """
    Translate text between Korean and other languages.

    Use this tool when:
    - User needs to translate Korean text to their language
    - User wants to know how to say something in Korean
    - Translating menu items, signs, or directions

    Supported languages: Korean, English, Japanese, Chinese, Vietnamese,
    Indonesian, Thai, German, Russian, Spanish, Italian, French

    Args:
        text: Text to translate
        target_language: Target language code (en, ko, ja, zh-CN, etc.)
        source_language: Source language (auto-detected if not provided)

    Returns:
        Translated text
    """
    # Auto-detect source language if not provided
    if not source_language:
        source_language = await detect_language(text)
        if not source_language:
            # Fallback: assume Korean if target is not Korean
            source_language = "ko" if target_language != "ko" else "en"

    # Validate languages
    if source_language not in SUPPORTED_LANGUAGES:
        return f"Source language '{source_language}' is not supported."

    if target_language not in SUPPORTED_LANGUAGES:
        return f"Target language '{target_language}' is not supported. Supported: {', '.join(SUPPORTED_LANGUAGES.keys())}"

    if source_language == target_language:
        return text

    result = await translate_text(text, source_language, target_language)

    if result:
        source_name = SUPPORTED_LANGUAGES.get(source_language, source_language)
        target_name = SUPPORTED_LANGUAGES.get(target_language, target_language)

        return (
            f"**Translation** ({source_name} → {target_name}):\n\n"
            f"Original: {result.original_text}\n\n"
            f"Translated: {result.translated_text}"
        )
    else:
        return "Translation failed. Please try again."


@tool
async def translate_to_korean(text: str) -> str:
    """
    Translate text to Korean.

    Use this when the user wants to learn how to say something in Korean.

    Args:
        text: Text to translate to Korean

    Returns:
        Korean translation
    """
    source_lang = await detect_language(text)
    if not source_lang or source_lang == "ko":
        return f"'{text}' appears to already be in Korean."

    result = await translate_text(text, source_lang, "ko")

    if result:
        return f"**In Korean:** {result.translated_text}"
    else:
        return "Translation failed."


@tool
async def translate_from_korean(text: str, target_language: str = "en") -> str:
    """
    Translate Korean text to another language.

    Use this when the user encounters Korean text they don't understand.

    Args:
        text: Korean text to translate
        target_language: Target language (default: English)

    Returns:
        Translated text
    """
    result = await translate_text(text, "ko", target_language)

    if result:
        target_name = SUPPORTED_LANGUAGES.get(target_language, target_language)
        return f"**Translation to {target_name}:** {result.translated_text}"
    else:
        return "Translation failed."


# Common phrases helper
COMMON_PHRASES = {
    "hello": "안녕하세요 (annyeonghaseyo)",
    "thank you": "감사합니다 (gamsahamnida)",
    "excuse me": "실례합니다 (sillyehamnida)",
    "sorry": "죄송합니다 (joesonghamnida)",
    "yes": "네 (ne)",
    "no": "아니요 (aniyo)",
    "how much": "얼마예요? (eolmayeyo?)",
    "where is": "어디예요? (eodiyeyo?)",
    "bathroom": "화장실 (hwajangsil)",
    "water": "물 (mul)",
    "help": "도와주세요 (dowajuseyo)",
    "delicious": "맛있어요 (masisseoyo)",
    "check please": "계산해 주세요 (gyesanhae juseyo)",
    "one": "하나 (hana)",
    "two": "둘 (dul)",
    "three": "셋 (set)",
}


@tool
async def get_korean_phrase(phrase: str) -> str:
    """
    Get common Korean phrases for tourists.

    Use this for quick translations of common travel phrases.

    Args:
        phrase: Common phrase to translate (e.g., "hello", "thank you", "how much")

    Returns:
        Korean phrase with pronunciation
    """
    phrase_lower = phrase.lower().strip()

    if phrase_lower in COMMON_PHRASES:
        return f"**{phrase.capitalize()}** in Korean: {COMMON_PHRASES[phrase_lower]}"

    # If not in common phrases, do a full translation
    result = await translate_text(phrase, "en", "ko")
    if result:
        return f"**{phrase}** in Korean: {result.translated_text}"

    return f"Could not translate '{phrase}'. Try using the translate tool."


# Export tools for agent
translation_tools = [
    translate,
    translate_to_korean,
    translate_from_korean,
    get_korean_phrase,
]
