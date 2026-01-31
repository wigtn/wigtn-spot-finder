"""
Naver Geocoding API - 주소를 GPS 좌표로 변환.
Converts addresses to GPS coordinates using Naver Cloud Platform Geocoding API.
"""

import logging
from urllib.parse import quote, urlencode

import httpx
from pydantic import BaseModel, Field

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Naver Cloud Platform Geocoding API endpoint
NAVER_GEOCODING_URL = "https://maps.apigw.ntruss.com/map-geocode/v2/geocode"


class GeocodingResult(BaseModel):
    """Result from geocoding an address."""

    address: str = Field(description="Original query address")
    road_address: str = Field(default="", description="Road name address")
    jibun_address: str = Field(default="", description="Lot number address")
    latitude: float = Field(description="Latitude (위도)")
    longitude: float = Field(description="Longitude (경도)")
    confidence: float = Field(default=1.0, description="Confidence score (0-1)")


async def geocode_address(address: str) -> GeocodingResult | None:
    """
    Convert an address to GPS coordinates using Naver Geocoding API.

    Args:
        address: Korean address string (e.g., "서울 성동구 성수이로 88")

    Returns:
        GeocodingResult with coordinates or None if not found
    """
    if not settings.naver_map_client_id or not settings.naver_map_client_secret:
        logger.warning("Naver Map API credentials not configured")
        return None

    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.naver_map_client_id,
        "X-NCP-APIGW-API-KEY": settings.naver_map_client_secret,
        "Accept": "application/json",
    }

    params = {"query": address}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NAVER_GEOCODING_URL,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "OK":
                logger.warning(f"Geocoding failed for '{address}': {data.get('errorMessage', 'Unknown error')}")
                return None

            addresses = data.get("addresses", [])
            if not addresses:
                logger.info(f"No geocoding results for: {address}")
                return None

            # Use first result
            result = addresses[0]

            return GeocodingResult(
                address=address,
                road_address=result.get("roadAddress", ""),
                jibun_address=result.get("jibunAddress", ""),
                latitude=float(result.get("y", 0)),
                longitude=float(result.get("x", 0)),
                confidence=float(result.get("distance", 0)) if result.get("distance") else 1.0,
            )

    except httpx.HTTPStatusError as e:
        logger.error(f"Geocoding HTTP error for '{address}': {e.response.status_code}")
        return None
    except Exception as e:
        logger.error(f"Geocoding error for '{address}': {e}")
        return None


async def batch_geocode_addresses(addresses: list[str]) -> dict[str, GeocodingResult | None]:
    """
    Geocode multiple addresses.

    Args:
        addresses: List of address strings

    Returns:
        Dictionary mapping address to GeocodingResult (or None if failed)
    """
    results: dict[str, GeocodingResult | None] = {}

    for address in addresses:
        result = await geocode_address(address)
        results[address] = result

    success_count = sum(1 for r in results.values() if r is not None)
    logger.info(f"Batch geocoding complete: {success_count}/{len(addresses)} successful")

    return results


def generate_naver_map_url(
    latitude: float,
    longitude: float,
    name: str,
    zoom: int = 17,
) -> str:
    """
    Generate a Naver Map URL for a location.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        name: Place name for the marker
        zoom: Zoom level (default 17 for detailed view)

    Returns:
        Naver Map URL string
    """
    # Naver Map place marker URL format
    # https://map.naver.com/p/search/{query}?c={lng},{lat},{zoom},0,0,0,dh
    encoded_name = quote(name)

    # Alternative: direct coordinate link
    # Format: https://map.naver.com/p?c={lng},{lat},{zoom},0,0,0,dh
    url = f"https://map.naver.com/p?c={longitude},{latitude},{zoom},0,0,0,dh"

    return url


def generate_naver_place_search_url(query: str) -> str:
    """
    Generate a Naver Map search URL.

    Args:
        query: Search query (place name or address)

    Returns:
        Naver Map search URL
    """
    encoded_query = quote(query)
    return f"https://map.naver.com/p/search/{encoded_query}"


def generate_naver_directions_url(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    start_name: str = "출발지",
    end_name: str = "도착지",
) -> str:
    """
    Generate a Naver Map directions URL.

    Args:
        start_lat: Starting latitude
        start_lng: Starting longitude
        end_lat: Destination latitude
        end_lng: Destination longitude
        start_name: Name for start location
        end_name: Name for end location

    Returns:
        Naver Map directions URL
    """
    params = {
        "start": f"{start_lng},{start_lat},{quote(start_name)}",
        "goal": f"{end_lng},{end_lat},{quote(end_name)}",
    }
    return f"https://map.naver.com/p/directions/-/-/-/transit?{urlencode(params, safe=',')}"
