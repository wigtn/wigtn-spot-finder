"""
Naver Map Place Search Tool.
Provides place search functionality using Naver Local API.
"""

import logging
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Naver API endpoints
NAVER_LOCAL_SEARCH_URL = "https://openapi.naver.com/v1/search/local.json"
NAVER_MAP_SEARCH_URL = "https://map.naver.com/v5/api/search"


class PlaceResult(BaseModel):
    """Place search result model."""

    name: str = Field(description="Place name")
    name_korean: str = Field(default="", description="Korean name")
    address: str = Field(description="Address")
    road_address: str = Field(default="", description="Road address")
    category: str = Field(default="", description="Category")
    telephone: str = Field(default="", description="Phone number")
    latitude: float | None = Field(default=None, description="Latitude")
    longitude: float | None = Field(default=None, description="Longitude")
    link: str = Field(default="", description="Naver Map link")
    description: str = Field(default="", description="Description")


class PlaceSearchInput(BaseModel):
    """Input for place search tool."""

    query: str = Field(description="Search query (e.g., '강남역 맛집', 'Gangnam restaurant')")
    display: int = Field(default=5, description="Number of results to return (1-5)", ge=1, le=5)


async def search_places_naver(
    query: str,
    display: int = 5,
) -> list[PlaceResult]:
    """
    Search for places using Naver Local Search API.

    Args:
        query: Search query
        display: Number of results

    Returns:
        List of PlaceResult objects
    """
    if not settings.naver_map_client_id or not settings.naver_map_client_secret:
        logger.warning("Naver API credentials not configured")
        return []

    headers = {
        "X-Naver-Client-Id": settings.naver_map_client_id,
        "X-Naver-Client-Secret": settings.naver_map_client_secret,
    }

    params = {
        "query": query,
        "display": display,
        "start": 1,
        "sort": "random",  # Can be "random" or "comment"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NAVER_LOCAL_SEARCH_URL,
                headers=headers,
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            results = []
            for item in items:
                # Clean HTML tags from title
                name = item.get("title", "").replace("<b>", "").replace("</b>", "")

                # Parse coordinates if available
                mapx = item.get("mapx", "")
                mapy = item.get("mapy", "")

                latitude = None
                longitude = None
                if mapx and mapy:
                    try:
                        # Naver uses KATECH coordinates, need conversion
                        # For simplicity, we'll store raw values
                        longitude = float(mapx) / 10000000
                        latitude = float(mapy) / 10000000
                    except (ValueError, TypeError):
                        pass

                result = PlaceResult(
                    name=name,
                    name_korean=name,  # Naver returns Korean by default
                    address=item.get("address", ""),
                    road_address=item.get("roadAddress", ""),
                    category=item.get("category", ""),
                    telephone=item.get("telephone", ""),
                    latitude=latitude,
                    longitude=longitude,
                    link=item.get("link", ""),
                    description=item.get("description", ""),
                )
                results.append(result)

            logger.info(f"Found {len(results)} places for query: {query}")
            return results

    except httpx.HTTPError as e:
        logger.error(f"Naver API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Place search error: {e}")
        return []


def format_place_results(results: list[PlaceResult]) -> str:
    """
    Format place results for display.

    Args:
        results: List of PlaceResult objects

    Returns:
        Formatted string
    """
    if not results:
        return "No places found."

    lines = []
    for i, place in enumerate(results, 1):
        parts = [f"{i}. **{place.name}**"]

        if place.category:
            parts.append(f"   Category: {place.category}")

        if place.road_address:
            parts.append(f"   Address: {place.road_address}")
        elif place.address:
            parts.append(f"   Address: {place.address}")

        if place.telephone:
            parts.append(f"   Tel: {place.telephone}")

        if place.link:
            parts.append(f"   [View on Naver Map]({place.link})")

        lines.append("\n".join(parts))

    return "\n\n".join(lines)


@tool
async def search_places(query: str, count: int = 5) -> str:
    """
    Search for places in Korea using Naver Map.

    Use this tool when the user wants to find:
    - Restaurants, cafes, or food places
    - Tourist attractions and landmarks
    - Hotels and accommodations
    - Shops and stores
    - Any location in Korea

    Args:
        query: What to search for (e.g., "Korean BBQ in Gangnam", "경복궁 근처 카페")
        count: Number of results to return (1-5)

    Returns:
        Formatted list of places with details
    """
    results = await search_places_naver(query, min(count, 5))
    return format_place_results(results)


@tool
async def search_restaurants(location: str, cuisine: str = "", count: int = 5) -> str:
    """
    Search for restaurants in a specific location.

    Use this tool when the user specifically wants restaurant recommendations.

    Args:
        location: Area or location (e.g., "Hongdae", "명동", "near Gyeongbokgung")
        cuisine: Type of cuisine (e.g., "Korean BBQ", "seafood", "vegetarian")
        count: Number of results (1-5)

    Returns:
        Formatted list of restaurants
    """
    query_parts = [location]
    if cuisine:
        query_parts.append(cuisine)
    query_parts.append("맛집")  # "good restaurant" in Korean

    query = " ".join(query_parts)
    results = await search_places_naver(query, min(count, 5))
    return format_place_results(results)


@tool
async def search_attractions(location: str, category: str = "", count: int = 5) -> str:
    """
    Search for tourist attractions and landmarks.

    Use this tool when the user wants to find sightseeing spots.

    Args:
        location: Area or city (e.g., "Seoul", "Busan", "Jeju")
        category: Type of attraction (e.g., "palace", "museum", "park", "temple")
        count: Number of results (1-5)

    Returns:
        Formatted list of attractions
    """
    query_parts = [location]
    if category:
        query_parts.append(category)
    query_parts.append("관광지")  # "tourist spot" in Korean

    query = " ".join(query_parts)
    results = await search_places_naver(query, min(count, 5))
    return format_place_results(results)


# Export tools for agent
place_search_tools = [
    search_places,
    search_restaurants,
    search_attractions,
]
