"""
Popup Store Search Tools for Seongsu popup finder.
Provides LangChain tools for searching and retrieving popup store information.
"""

import logging
from datetime import date
from typing import Any

from langchain_core.tools import tool

from src.db.sqlite.popup_store import get_popup_db
from src.models.popup import PopupCategory

logger = logging.getLogger(__name__)

# Category descriptions for user-friendly display
CATEGORY_DESCRIPTIONS = {
    "fashion": "패션/의류 (Fashion/Clothing)",
    "cafe": "카페/디저트 (Cafe/Dessert)",
    "art": "전시/아트 (Exhibition/Art)",
    "cosmetics": "화장품/뷰티 (Cosmetics/Beauty)",
    "food": "음식/식품 (Food/F&B)",
    "lifestyle": "라이프스타일 (Lifestyle)",
    "entertainment": "엔터테인먼트 (Entertainment)",
    "collaboration": "브랜드 콜라보 (Brand Collaboration)",
    "other": "기타 (Other)",
}


def _format_popup_for_display(popup: Any, include_details: bool = False) -> str:
    """Format a popup store for display."""
    lines = [f"**{popup.name}**"]

    if popup.name_korean:
        lines[0] += f" ({popup.name_korean})"

    if popup.brand:
        lines.append(f"  Brand: {popup.brand}")

    lines.append(f"  Location: {popup.location}")

    if popup.period_start or popup.period_end:
        period = ""
        if popup.period_start:
            period += popup.period_start.strftime("%Y.%m.%d")
        period += " ~ "
        if popup.period_end:
            period += popup.period_end.strftime("%Y.%m.%d")
        lines.append(f"  Period: {period}")

    if popup.operating_hours:
        lines.append(f"  Hours: {popup.operating_hours}")

    category_desc = CATEGORY_DESCRIPTIONS.get(
        popup.category.value if hasattr(popup.category, 'value') else popup.category,
        popup.category
    )
    lines.append(f"  Category: {category_desc}")

    if include_details:
        if popup.description:
            desc = popup.description[:200] + "..." if len(popup.description) > 200 else popup.description
            lines.append(f"  Description: {desc}")

        if popup.address:
            lines.append(f"  Address: {popup.address}")

        if popup.source_post_url:
            lines.append(f"  Instagram: {popup.source_post_url}")

    return "\n".join(lines)


@tool
async def search_seongsu_popups(
    query: str | None = None,
    category: str | None = None,
    active_only: bool = True,
) -> str:
    """
    Search for popup stores in Seongsu-dong, Seoul.

    Use this tool when the user asks about:
    - Popup stores in Seongsu
    - Current/ongoing popups
    - Specific types of popups (fashion, cafe, art, etc.)
    - Brand collaborations or special events

    Args:
        query: Search keyword (brand name, popup name, etc.)
        category: Filter by category (fashion, cafe, art, cosmetics, food, lifestyle, entertainment, collaboration, other)
        active_only: Only show currently active popups (default: True)

    Returns:
        List of matching popup stores with details
    """
    try:
        db = await get_popup_db()

        # Validate category
        if category:
            category = category.lower()
            valid_categories = [c.value for c in PopupCategory]
            if category not in valid_categories:
                return f"Invalid category. Valid categories are: {', '.join(valid_categories)}"

        # Search popups
        popups = await db.search_popups(
            keyword=query,
            category=category,
            active_only=active_only,
            limit=10,
        )

        if not popups:
            msg = "No popup stores found"
            if query:
                msg += f" matching '{query}'"
            if category:
                msg += f" in category '{category}'"
            if active_only:
                msg += " (currently active)"
            return msg + ". Try broadening your search."

        # Format results
        result_lines = [f"Found {len(popups)} popup store(s) in Seongsu-dong:\n"]

        for i, popup in enumerate(popups, 1):
            result_lines.append(f"{i}. {_format_popup_for_display(popup)}")
            result_lines.append("")

        return "\n".join(result_lines)

    except Exception as e:
        logger.error(f"Popup search failed: {e}")
        return "Failed to search popup stores. Please try again."


@tool
async def get_popup_details(popup_id: str) -> str:
    """
    Get detailed information about a specific popup store.

    Use this tool when the user wants more details about a specific popup.

    Args:
        popup_id: The popup store ID

    Returns:
        Detailed information about the popup store
    """
    try:
        db = await get_popup_db()
        popup = await db.get_popup(popup_id)

        if not popup:
            return f"Popup store with ID '{popup_id}' not found."

        return _format_popup_for_display(popup, include_details=True)

    except Exception as e:
        logger.error(f"Failed to get popup details: {e}")
        return "Failed to get popup details. Please try again."


@tool
async def list_current_popups(category: str | None = None) -> str:
    """
    List all currently active popup stores in Seongsu-dong.

    Use this tool when the user asks:
    - "What popups are happening now?"
    - "Show me current popups"
    - "List all active popups"

    Args:
        category: Optional category filter (fashion, cafe, art, cosmetics, food, lifestyle, entertainment, collaboration, other)

    Returns:
        List of all currently active popup stores
    """
    try:
        db = await get_popup_db()

        # Validate category
        if category:
            category = category.lower()
            valid_categories = [c.value for c in PopupCategory]
            if category not in valid_categories:
                return f"Invalid category. Valid categories are: {', '.join(valid_categories)}"

        # Get active popups
        popups = await db.get_active_popups(
            as_of=date.today(),
            category=category,
            limit=20,
        )

        if not popups:
            msg = "No active popup stores found"
            if category:
                msg += f" in category '{category}'"
            return msg + ". Check back later for new popups!"

        # Format results
        result_lines = []

        if category:
            cat_desc = CATEGORY_DESCRIPTIONS.get(category, category)
            result_lines.append(f"Active {cat_desc} popups in Seongsu-dong ({len(popups)}):\n")
        else:
            result_lines.append(f"Currently active popups in Seongsu-dong ({len(popups)}):\n")

        for i, popup in enumerate(popups, 1):
            result_lines.append(f"{i}. {_format_popup_for_display(popup)}")
            result_lines.append("")

        return "\n".join(result_lines)

    except Exception as e:
        logger.error(f"Failed to list popups: {e}")
        return "Failed to list popup stores. Please try again."


@tool
async def get_popup_categories() -> str:
    """
    Get all popup store categories with counts.

    Use this tool when the user asks:
    - "What types of popups are there?"
    - "Show me popup categories"
    - "What kind of popups can I find?"

    Returns:
        List of categories with popup counts
    """
    try:
        db = await get_popup_db()
        categories = await db.get_categories()

        if not categories:
            return "No popup categories found. The database might be empty."

        result_lines = ["Popup store categories in Seongsu-dong:\n"]

        for cat in categories:
            cat_name = cat["category"]
            count = cat["count"]
            desc = CATEGORY_DESCRIPTIONS.get(cat_name, cat_name)
            result_lines.append(f"- {desc}: {count} popup(s)")

        return "\n".join(result_lines)

    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        return "Failed to get popup categories. Please try again."


@tool
async def recommend_popups_for_interest(interest: str) -> str:
    """
    Recommend popup stores based on user's interests.

    Use this tool when the user mentions their interests or asks for recommendations.

    Args:
        interest: User's interest (e.g., "fashion", "art", "coffee", "beauty", "food")

    Returns:
        Recommended popup stores matching the interest
    """
    # Map common interests to categories
    interest_to_category = {
        # Fashion
        "fashion": "fashion",
        "clothes": "fashion",
        "clothing": "fashion",
        "apparel": "fashion",
        "shoes": "fashion",
        "accessories": "fashion",
        # Cafe
        "cafe": "cafe",
        "coffee": "cafe",
        "dessert": "cafe",
        "cake": "cafe",
        "bakery": "cafe",
        # Art
        "art": "art",
        "exhibition": "art",
        "gallery": "art",
        "museum": "art",
        "photo": "art",
        # Cosmetics
        "cosmetics": "cosmetics",
        "beauty": "cosmetics",
        "makeup": "cosmetics",
        "skincare": "cosmetics",
        # Food
        "food": "food",
        "restaurant": "food",
        "dining": "food",
        "snack": "food",
        # Lifestyle
        "lifestyle": "lifestyle",
        "home": "lifestyle",
        "interior": "lifestyle",
        "goods": "lifestyle",
        # Entertainment
        "entertainment": "entertainment",
        "game": "entertainment",
        "character": "entertainment",
        "anime": "entertainment",
        "idol": "entertainment",
        "kpop": "entertainment",
    }

    interest_lower = interest.lower().strip()
    category = interest_to_category.get(interest_lower)

    if category:
        # Use category-based search
        return await list_current_popups.ainvoke({"category": category})
    else:
        # Use keyword search
        return await search_seongsu_popups.ainvoke({
            "query": interest,
            "active_only": True,
        })


# Export tools for agent
popup_search_tools = [
    search_seongsu_popups,
    get_popup_details,
    list_current_popups,
    get_popup_categories,
    recommend_popups_for_interest,
]
