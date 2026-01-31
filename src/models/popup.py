"""
Popup Store models for Seongsu popup finder.
Defines the data structure for popup stores.
"""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)


class PopupCategory(str, Enum):
    """Popup store category."""

    FASHION = "fashion"  # 패션/의류
    CAFE = "cafe"  # 카페/디저트
    ART = "art"  # 전시/아트
    COSMETICS = "cosmetics"  # 화장품/뷰티
    FOOD = "food"  # 음식/식품
    LIFESTYLE = "lifestyle"  # 라이프스타일
    ENTERTAINMENT = "entertainment"  # 엔터테인먼트
    COLLABORATION = "collaboration"  # 브랜드 콜라보
    OTHER = "other"  # 기타


class PopupStore(BaseModel):
    """Popup store main model."""

    # Identifiers
    id: str = Field(description="Unique popup ID (UUID)")

    # Basic info
    name: str = Field(description="Popup store name")
    name_korean: str | None = Field(default=None, description="Korean name")
    brand: str | None = Field(default=None, description="Brand name")

    # Classification
    category: PopupCategory = Field(default=PopupCategory.OTHER)
    tags: list[str] = Field(default_factory=list, description="Search tags")

    # Location
    location: str = Field(description="Location description")
    address: str | None = Field(default=None, description="Full address")
    coordinates: tuple[float, float] | None = Field(
        default=None,
        description="(longitude, latitude)"
    )

    # Period
    period_start: date | None = Field(default=None, description="Start date")
    period_end: date | None = Field(default=None, description="End date")
    operating_hours: str | None = Field(default=None, description="Business hours")

    # Description
    description: str = Field(description="Description in Korean")
    description_ja: str | None = Field(default=None, description="Japanese translation")
    description_en: str | None = Field(default=None, description="English translation")

    # Media
    images: list[str] = Field(default_factory=list, description="Image URLs")
    thumbnail_url: str | None = Field(default=None, description="Main thumbnail")

    # Source
    source_post_url: str = Field(description="Instagram post URL")
    source_post_id: str = Field(description="Instagram post shortcode")

    # Metadata
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    is_active: bool = Field(default=True)

    # Vector search
    embedding_id: str | None = Field(default=None, description="Qdrant point ID")

    def is_currently_active(self, as_of: date | None = None) -> bool:
        """Check if popup is currently active."""
        check_date = as_of or date.today()

        if not self.is_active:
            return False

        if self.period_start and check_date < self.period_start:
            return False

        if self.period_end and check_date > self.period_end:
            return False

        return True

    def to_search_text(self) -> str:
        """Generate text for embedding/search."""
        parts = [
            self.name,
            self.name_korean or "",
            self.brand or "",
            self.description,
            self.location,
            self.category.value,
            " ".join(self.tags),
        ]
        return " ".join(filter(None, parts))


class PopupSummary(BaseModel):
    """Popup summary for list views."""

    id: str
    name: str
    name_korean: str | None = None
    category: str
    location: str
    period_start: date | None = None
    period_end: date | None = None
    thumbnail_url: str | None = None
    is_active: bool = True


class PopupDetail(BaseModel):
    """Popup detail response model."""

    id: str
    name: str
    name_korean: str | None = None
    brand: str | None = None
    category: str
    location: str
    address: str | None = None
    coordinates: tuple[float, float] | None = None
    period_start: date | None = None
    period_end: date | None = None
    operating_hours: str | None = None
    description: str
    description_ja: str | None = None
    images: list[str] = Field(default_factory=list)
    source_url: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
