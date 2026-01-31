"""
Naver Map Directions Tool.
Provides route and directions using Naver Directions API.
"""

import logging
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Exchange rate for display purposes
KRW_TO_USD_RATE = settings.krw_to_usd_rate

# Naver Directions API endpoint
NAVER_DIRECTIONS_URL = "https://naveropenapi.apigw.ntruss.com/map-direction/v1/driving"
NAVER_DIRECTIONS15_URL = "https://naveropenapi.apigw.ntruss.com/map-direction-15/v1/driving"


class RouteSegment(BaseModel):
    """Route segment model."""

    instruction: str = Field(description="Navigation instruction")
    distance_meters: int = Field(description="Distance in meters")
    duration_seconds: int = Field(description="Duration in seconds")


class DirectionsResult(BaseModel):
    """Directions result model."""

    origin: str = Field(description="Starting point")
    destination: str = Field(description="Destination")
    total_distance_km: float = Field(description="Total distance in kilometers")
    total_duration_minutes: int = Field(description="Total duration in minutes")
    toll_fare: int = Field(default=0, description="Toll fare in KRW")
    fuel_price: int = Field(default=0, description="Estimated fuel cost in KRW")
    taxi_fare: int = Field(default=0, description="Estimated taxi fare in KRW")
    summary: str = Field(description="Route summary")
    segments: list[RouteSegment] = Field(default_factory=list)


class Coordinates(BaseModel):
    """Geographic coordinates."""

    latitude: float
    longitude: float


async def get_directions_naver(
    start_coords: tuple[float, float],
    end_coords: tuple[float, float],
    waypoints: list[tuple[float, float]] | None = None,
) -> DirectionsResult | None:
    """
    Get directions using Naver Directions API.

    Args:
        start_coords: (longitude, latitude) of start point
        end_coords: (longitude, latitude) of end point
        waypoints: Optional list of waypoint coordinates

    Returns:
        DirectionsResult or None if failed
    """
    if not settings.naver_map_client_id or not settings.naver_map_client_secret:
        logger.warning("Naver API credentials not configured")
        return None

    headers = {
        "X-NCP-APIGW-API-KEY-ID": settings.naver_map_client_id,
        "X-NCP-APIGW-API-KEY": settings.naver_map_client_secret,
    }

    # Format coordinates as "longitude,latitude"
    start = f"{start_coords[0]},{start_coords[1]}"
    goal = f"{end_coords[0]},{end_coords[1]}"

    params = {
        "start": start,
        "goal": goal,
        "option": "trafast",  # Fastest route with real-time traffic
    }

    if waypoints:
        wp_str = "|".join(f"{wp[0]},{wp[1]}" for wp in waypoints)
        params["waypoints"] = wp_str

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                NAVER_DIRECTIONS_URL,
                headers=headers,
                params=params,
            )
            response.raise_for_status()

            data = response.json()

            if data.get("code") != 0:
                logger.warning(f"Naver Directions API error: {data.get('message')}")
                return None

            route = data.get("route", {})
            trafast = route.get("trafast", [{}])[0]
            summary = trafast.get("summary", {})

            # Parse segments/guide
            segments = []
            for guide in trafast.get("guide", [])[:10]:  # Limit to first 10
                segments.append(RouteSegment(
                    instruction=guide.get("instructions", ""),
                    distance_meters=guide.get("distance", 0),
                    duration_seconds=guide.get("duration", 0),
                ))

            result = DirectionsResult(
                origin=start,
                destination=goal,
                total_distance_km=round(summary.get("distance", 0) / 1000, 2),
                total_duration_minutes=round(summary.get("duration", 0) / 60000),
                toll_fare=summary.get("tollFare", 0),
                fuel_price=summary.get("fuelPrice", 0),
                taxi_fare=summary.get("taxiFare", 0),
                summary=f"Distance: {round(summary.get('distance', 0) / 1000, 1)}km, "
                        f"Duration: {round(summary.get('duration', 0) / 60000)}min",
                segments=segments,
            )

            return result

    except httpx.HTTPError as e:
        logger.error(f"Naver Directions API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Directions error: {e}")
        return None


def format_directions_result(result: DirectionsResult | None) -> str:
    """
    Format directions result for display.

    Args:
        result: DirectionsResult object

    Returns:
        Formatted string
    """
    if not result:
        return "Could not get directions. Please try with different locations."

    lines = [
        f"## Route from {result.origin} to {result.destination}",
        "",
        f"**Total Distance:** {result.total_distance_km} km",
        f"**Estimated Time:** {result.total_duration_minutes} minutes",
        "",
    ]

    # Add cost estimates
    if result.taxi_fare > 0:
        lines.append(f"**Estimated Taxi Fare:** ₩{result.taxi_fare:,} (~${result.taxi_fare / KRW_TO_USD_RATE:.2f} USD)")

    if result.toll_fare > 0:
        lines.append(f"**Toll Fare:** ₩{result.toll_fare:,}")

    if result.fuel_price > 0:
        lines.append(f"**Fuel Cost (driving):** ₩{result.fuel_price:,}")

    # Add navigation steps
    if result.segments:
        lines.append("")
        lines.append("### Navigation Steps:")
        for i, segment in enumerate(result.segments, 1):
            if segment.instruction:
                dist = f"{segment.distance_meters}m" if segment.distance_meters < 1000 else f"{segment.distance_meters / 1000:.1f}km"
                lines.append(f"{i}. {segment.instruction} ({dist})")

    return "\n".join(lines)


# Coordinate lookup helper (simplified - in production, use geocoding API)
KNOWN_LOCATIONS = {
    # Major landmarks
    "gyeongbokgung": (126.9769, 37.5788),
    "경복궁": (126.9769, 37.5788),
    "myeongdong": (126.9856, 37.5636),
    "명동": (126.9856, 37.5636),
    "hongdae": (126.9246, 37.5563),
    "홍대": (126.9246, 37.5563),
    "gangnam station": (127.0276, 37.4979),
    "강남역": (127.0276, 37.4979),
    "itaewon": (126.9947, 37.5345),
    "이태원": (126.9947, 37.5345),
    "namsan tower": (126.9882, 37.5512),
    "남산타워": (126.9882, 37.5512),
    "bukchon": (126.9849, 37.5826),
    "북촌": (126.9849, 37.5826),
    "dongdaemun": (127.0095, 37.5662),
    "동대문": (127.0095, 37.5662),
    "insadong": (126.9850, 37.5744),
    "인사동": (126.9850, 37.5744),
    "lotte tower": (127.1025, 37.5126),
    "롯데타워": (127.1025, 37.5126),
    "seoul station": (126.9706, 37.5547),
    "서울역": (126.9706, 37.5547),
    "incheon airport": (126.4407, 37.4602),
    "인천공항": (126.4407, 37.4602),

    # Seongsu-dong landmarks (성수동)
    "seongsu station": (127.0558, 37.5447),
    "seongsu": (127.0558, 37.5447),
    "성수역": (127.0558, 37.5447),
    "성수": (127.0558, 37.5447),
    "seoul forest": (127.0375, 37.5443),
    "서울숲": (127.0375, 37.5443),
    "onion seongsu": (127.0561, 37.5449),
    "어니언 성수": (127.0561, 37.5449),
    "daelim warehouse": (127.0522, 37.5448),
    "대림창고": (127.0522, 37.5448),
    "seongsu-dong": (127.0550, 37.5445),
    "성수동": (127.0550, 37.5445),
    "ttukseom": (127.0656, 37.5475),
    "뚝섬": (127.0656, 37.5475),
    "ttukseom station": (127.0470, 37.5475),
    "뚝섬역": (127.0470, 37.5475),
    "seongsu 2-ga": (127.0580, 37.5440),
    "성수2가": (127.0580, 37.5440),
    "kcoffee": (127.0545, 37.5442),
    "common ground": (127.0472, 37.5444),
    "커먼그라운드": (127.0472, 37.5444),
}


def get_coordinates(location: str) -> tuple[float, float] | None:
    """
    Get coordinates for a known location.

    Args:
        location: Location name

    Returns:
        (longitude, latitude) or None
    """
    location_lower = location.lower().strip()
    return KNOWN_LOCATIONS.get(location_lower)


@tool
async def get_directions(
    start: str,
    destination: str,
) -> str:
    """
    Get directions between two locations in Korea.

    Use this tool when the user asks:
    - How to get from one place to another
    - Travel time between locations
    - Route information
    - Distance between places

    Note: Currently supports major landmarks. For custom addresses,
    coordinates need to be provided.

    Args:
        start: Starting location (e.g., "Gangnam Station", "경복궁")
        destination: Destination (e.g., "Myeongdong", "남산타워")

    Returns:
        Directions with distance, time, and cost estimates
    """
    start_coords = get_coordinates(start)
    end_coords = get_coordinates(destination)

    if not start_coords:
        return f"Could not find coordinates for '{start}'. Please try a well-known landmark like 'Gyeongbokgung', 'Gangnam Station', 'Hongdae', etc."

    if not end_coords:
        return f"Could not find coordinates for '{destination}'. Please try a well-known landmark."

    result = await get_directions_naver(start_coords, end_coords)
    return format_directions_result(result)


@tool
async def get_travel_time(
    start: str,
    destination: str,
) -> str:
    """
    Get estimated travel time between two locations.

    A simpler version of get_directions that focuses on time estimates.

    Args:
        start: Starting location
        destination: Destination

    Returns:
        Travel time estimate
    """
    start_coords = get_coordinates(start)
    end_coords = get_coordinates(destination)

    if not start_coords or not end_coords:
        return "Could not calculate travel time. Please use well-known landmarks."

    result = await get_directions_naver(start_coords, end_coords)

    if not result:
        return "Could not calculate travel time."

    return (
        f"Travel from **{start}** to **{destination}**:\n"
        f"- Distance: {result.total_distance_km} km\n"
        f"- By car/taxi: ~{result.total_duration_minutes} minutes\n"
        f"- Estimated taxi fare: ₩{result.taxi_fare:,} (~${result.taxi_fare / KRW_TO_USD_RATE:.2f} USD)"
    )


# Export tools for agent
directions_tools = [
    get_directions,
    get_travel_time,
]
