"""
Instagram post parser using LLM.
Extracts structured popup store information from post captions and images.
"""

import json
import logging
import re
from datetime import date, datetime
from uuid import uuid4

from src.models.instagram import InstagramPost, ParsedPopupInfo
from src.models.popup import PopupCategory, PopupStore
from src.services.llm.upstage_client import get_chat_model
from src.services.llm.upstage_document_parser import get_document_parser

logger = logging.getLogger(__name__)

# LLM prompt for parsing popup information
POPUP_PARSING_PROMPT = """You are an expert at extracting popup store information from Instagram posts.

Analyze the following Instagram post and extract popup store information.
The post is from @seongsu_bible, which introduces popup stores in Seongsu-dong, Seoul.

Post Caption:
{caption}

{image_text_section}

Extract the following information in JSON format:
{{
    "name": "popup store name (English or original)",
    "name_korean": "popup store name in Korean (if available)",
    "brand": "brand name (if mentioned)",
    "location": "location description (e.g., near Seongsu Station Exit 2)",
    "address": "full address if mentioned",
    "period_start": "start date in YYYY-MM-DD format (null if not mentioned)",
    "period_end": "end date in YYYY-MM-DD format (null if not mentioned)",
    "operating_hours": "operating hours (e.g., 11:00-21:00)",
    "description": "brief description of the popup store in Korean",
    "category": "one of: fashion, cafe, art, cosmetics, food, lifestyle, entertainment, collaboration, other",
    "confidence_score": 0.0-1.0 (how confident you are in the extraction)
}}

Important:
- If information is not available, use null
- For dates, try to parse Korean date formats (e.g., "1월 15일" -> "2024-01-15")
- Category should be one of the specified values
- Confidence score should reflect how much relevant popup information was found

Respond ONLY with the JSON object, no additional text."""


class InstagramPostParser:
    """
    Parser for Instagram posts to extract popup store information.
    Uses Upstage Document Parser for image text and Solar Pro 2 for structuring.
    """

    def __init__(self):
        """Initialize the parser."""
        self._llm = None
        self._doc_parser = None

    @property
    def llm(self):
        """Lazy load LLM."""
        if self._llm is None:
            self._llm = get_chat_model()
        return self._llm

    @property
    def doc_parser(self):
        """Lazy load document parser."""
        if self._doc_parser is None:
            self._doc_parser = get_document_parser()
        return self._doc_parser

    async def parse_post(self, post: InstagramPost) -> ParsedPopupInfo | None:
        """
        Parse an Instagram post to extract popup information.

        Args:
            post: Instagram post to parse

        Returns:
            ParsedPopupInfo or None if parsing fails
        """
        try:
            # Extract text from images if available
            image_text = ""
            if post.image_urls:
                try:
                    # Parse first image only to save API calls
                    result = await self.doc_parser.parse_image_url(post.image_urls[0])
                    if result.text:
                        image_text = result.text
                except Exception as e:
                    logger.warning(f"Image parsing failed: {e}")

            # Build prompt
            image_text_section = ""
            if image_text:
                image_text_section = f"\nText extracted from image:\n{image_text}"

            prompt = POPUP_PARSING_PROMPT.format(
                caption=post.caption[:2000],  # Limit caption length
                image_text_section=image_text_section,
            )

            # Call LLM
            response = await self.llm.ainvoke([{"role": "user", "content": prompt}])
            response_text = response.content.strip()

            # Parse JSON response
            parsed = self._parse_llm_response(response_text)

            if parsed:
                # Validate and fix dates
                parsed = self._validate_dates(parsed)

                return ParsedPopupInfo(
                    name=parsed.get("name", "Unknown Popup"),
                    name_korean=parsed.get("name_korean"),
                    brand=parsed.get("brand"),
                    location=parsed.get("location", "성수동"),
                    address=parsed.get("address"),
                    period_start=self._parse_date(parsed.get("period_start")),
                    period_end=self._parse_date(parsed.get("period_end")),
                    operating_hours=parsed.get("operating_hours"),
                    description=parsed.get("description", post.caption[:500]),
                    category=parsed.get("category", "other"),
                    confidence_score=float(parsed.get("confidence_score", 0.5)),
                    has_valid_name=bool(parsed.get("name")),
                    has_valid_period=bool(parsed.get("period_start") or parsed.get("period_end")),
                    has_valid_location=bool(parsed.get("location") or parsed.get("address")),
                )

        except Exception as e:
            logger.error(f"Failed to parse post {post.shortcode}: {e}")

        return None

    def _parse_llm_response(self, response: str) -> dict | None:
        """Parse JSON from LLM response."""
        try:
            # Try direct JSON parsing
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in response
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        logger.warning(f"Failed to parse LLM response as JSON: {response[:200]}")
        return None

    def _parse_date(self, date_str: str | None) -> date | None:
        """Parse date string to date object."""
        if not date_str:
            return None

        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

        # Try other formats
        formats = ["%Y.%m.%d", "%Y/%m/%d", "%m/%d/%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        return None

    def _validate_dates(self, parsed: dict) -> dict:
        """Validate and fix date values."""
        current_year = datetime.now().year

        for key in ["period_start", "period_end"]:
            if parsed.get(key):
                try:
                    dt = datetime.strptime(parsed[key], "%Y-%m-%d")
                    # If year is in past, assume current year
                    if dt.year < current_year:
                        parsed[key] = f"{current_year}-{dt.month:02d}-{dt.day:02d}"
                except ValueError:
                    parsed[key] = None

        return parsed

    async def create_popup_from_post(
        self,
        post: InstagramPost,
        parsed_info: ParsedPopupInfo,
    ) -> PopupStore:
        """
        Create a PopupStore object from parsed information.

        Args:
            post: Original Instagram post
            parsed_info: Parsed popup information

        Returns:
            PopupStore object
        """
        # Map category string to enum
        try:
            category = PopupCategory(parsed_info.category.lower())
        except ValueError:
            category = PopupCategory.OTHER

        # Extract tags from hashtags
        tags = [tag for tag in post.hashtags if not tag.startswith("seongsu")]

        return PopupStore(
            id=uuid4().hex,
            name=parsed_info.name,
            name_korean=parsed_info.name_korean,
            brand=parsed_info.brand,
            category=category,
            tags=tags[:10],  # Limit tags
            location=parsed_info.location,
            address=parsed_info.address,
            period_start=parsed_info.period_start,
            period_end=parsed_info.period_end,
            operating_hours=parsed_info.operating_hours,
            description=parsed_info.description,
            images=post.image_urls[:5],  # Limit images
            thumbnail_url=post.image_urls[0] if post.image_urls else None,
            source_post_url=post.post_url,
            source_post_id=post.shortcode,
        )


# Global instance
_post_parser: InstagramPostParser | None = None


def get_post_parser() -> InstagramPostParser:
    """Get global post parser instance."""
    global _post_parser
    if _post_parser is None:
        _post_parser = InstagramPostParser()
    return _post_parser
