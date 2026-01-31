"""
Instagram post models for scraping.
Defines the data structure for Instagram posts and parsed popup info.
"""

from datetime import date, datetime

from pydantic import BaseModel, Field


class InstagramPost(BaseModel):
    """Instagram post model."""

    shortcode: str = Field(description="Post shortcode (ID)")
    caption: str = Field(default="", description="Post caption text")
    image_urls: list[str] = Field(default_factory=list, description="Image URLs")
    timestamp: datetime = Field(description="Post timestamp")
    likes: int = Field(default=0)
    comments_count: int = Field(default=0)
    hashtags: list[str] = Field(default_factory=list)
    location_tag: str | None = Field(default=None)

    # Processing state
    is_processed: bool = Field(default=False)
    processed_at: datetime | None = Field(default=None)

    @property
    def post_url(self) -> str:
        """Get full Instagram post URL."""
        return f"https://www.instagram.com/p/{self.shortcode}/"


class ParsedPopupInfo(BaseModel):
    """LLM-parsed popup information from Instagram post."""

    name: str = Field(description="Popup store name")
    name_korean: str | None = Field(default=None, description="Korean name")
    brand: str | None = Field(default=None, description="Brand name")
    location: str = Field(description="Location description")
    address: str | None = Field(default=None, description="Full address")
    period_start: date | None = Field(default=None, description="Start date")
    period_end: date | None = Field(default=None, description="End date")
    operating_hours: str | None = Field(default=None, description="Business hours")
    description: str = Field(description="Description")
    category: str = Field(default="other", description="Popup category")
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Parsing confidence (0-1)"
    )

    # Validation flags
    has_valid_name: bool = Field(default=True)
    has_valid_period: bool = Field(default=False)
    has_valid_location: bool = Field(default=False)


class ScrapeLog(BaseModel):
    """Scraping log entry."""

    id: int | None = Field(default=None)
    started_at: datetime
    completed_at: datetime | None = None
    posts_fetched: int = Field(default=0)
    posts_parsed: int = Field(default=0)
    popups_created: int = Field(default=0)
    popups_updated: int = Field(default=0)
    status: str = Field(default="running")  # running, completed, failed
    error_message: str | None = None
