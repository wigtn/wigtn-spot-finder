"""
Itinerary Tool for travel planning.
Helps create and optimize travel itineraries.
"""

import logging
from datetime import datetime, time, timedelta
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from src.tools.naver.place_search import search_places_naver, PlaceResult
from src.tools.naver.directions import get_coordinates

logger = logging.getLogger(__name__)


class ItineraryItem(BaseModel):
    """Single item in an itinerary."""

    time_start: str = Field(description="Start time (HH:MM)")
    time_end: str = Field(description="End time (HH:MM)")
    activity: str = Field(description="Activity description")
    location: str = Field(description="Location name")
    location_korean: str = Field(default="", description="Korean name")
    category: str = Field(description="Category (attraction/meal/transport/etc)")
    duration_minutes: int = Field(description="Duration in minutes")
    notes: str = Field(default="", description="Additional notes")
    estimated_cost: int = Field(default=0, description="Estimated cost in KRW")


class DayItinerary(BaseModel):
    """Itinerary for a single day."""

    day_number: int = Field(description="Day number")
    date: str | None = Field(default=None, description="Date if specified")
    theme: str = Field(default="", description="Day theme")
    items: list[ItineraryItem] = Field(default_factory=list)
    total_estimated_cost: int = Field(default=0, description="Total cost for the day")


class TravelItinerary(BaseModel):
    """Complete travel itinerary."""

    title: str = Field(description="Itinerary title")
    duration_days: int = Field(description="Number of days")
    start_date: str | None = Field(default=None)
    days: list[DayItinerary] = Field(default_factory=list)
    total_estimated_cost: int = Field(default=0)
    tips: list[str] = Field(default_factory=list)


# Default activity durations (minutes)
ACTIVITY_DURATIONS = {
    "palace": 120,
    "museum": 90,
    "temple": 60,
    "market": 90,
    "shopping": 120,
    "park": 60,
    "tower": 90,
    "neighborhood": 120,
    "meal": 60,
    "cafe": 45,
    "transport": 30,
}

# Default costs (KRW)
ACTIVITY_COSTS = {
    "palace": 3000,
    "museum": 5000,
    "temple": 0,
    "market": 20000,
    "shopping": 50000,
    "park": 0,
    "tower": 16000,
    "meal_budget": 10000,
    "meal_mid": 20000,
    "meal_high": 50000,
    "cafe": 6000,
    "transport": 3000,
}

# Popular Seoul attractions with metadata
SEOUL_ATTRACTIONS = {
    "gyeongbokgung": {
        "name": "Gyeongbokgung Palace",
        "korean": "경복궁",
        "category": "palace",
        "duration": 120,
        "cost": 3000,
        "hours": "09:00-18:00",
        "closed": "Tuesday",
        "tips": "Free hanbok rental allows free entry",
    },
    "bukchon": {
        "name": "Bukchon Hanok Village",
        "korean": "북촌한옥마을",
        "category": "neighborhood",
        "duration": 90,
        "cost": 0,
        "hours": "Always open (residential area)",
        "tips": "Please be quiet - people live here",
    },
    "myeongdong": {
        "name": "Myeongdong Shopping District",
        "korean": "명동",
        "category": "shopping",
        "duration": 120,
        "cost": 0,
        "tips": "Great for cosmetics and street food",
    },
    "namsan": {
        "name": "N Seoul Tower (Namsan)",
        "korean": "남산타워",
        "category": "tower",
        "duration": 90,
        "cost": 16000,
        "hours": "10:00-23:00",
        "tips": "Cable car available, beautiful at sunset",
    },
    "insadong": {
        "name": "Insadong",
        "korean": "인사동",
        "category": "neighborhood",
        "duration": 90,
        "cost": 0,
        "tips": "Traditional crafts and tea houses",
    },
    "hongdae": {
        "name": "Hongdae",
        "korean": "홍대",
        "category": "neighborhood",
        "duration": 180,
        "cost": 0,
        "tips": "Best nightlife and street performances",
    },
    "dongdaemun": {
        "name": "Dongdaemun Design Plaza",
        "korean": "동대문디자인플라자",
        "category": "landmark",
        "duration": 60,
        "cost": 0,
        "hours": "24/7 (exterior)",
        "tips": "Night market nearby opens at 10pm",
    },
    "gwangjang": {
        "name": "Gwangjang Market",
        "korean": "광장시장",
        "category": "market",
        "duration": 90,
        "cost": 15000,
        "hours": "09:00-22:00",
        "tips": "Try bindaetteok and mayak gimbap",
    },
}


def format_itinerary(itinerary: TravelItinerary) -> str:
    """
    Format itinerary for display.

    Args:
        itinerary: TravelItinerary object

    Returns:
        Formatted markdown string
    """
    lines = [
        f"# {itinerary.title}",
        f"**Duration:** {itinerary.duration_days} day(s)",
        "",
    ]

    if itinerary.start_date:
        lines.append(f"**Start Date:** {itinerary.start_date}")
        lines.append("")

    for day in itinerary.days:
        date_str = f" ({day.date})" if day.date else ""
        lines.append(f"## Day {day.day_number}{date_str}")

        if day.theme:
            lines.append(f"*Theme: {day.theme}*")
        lines.append("")

        for item in day.items:
            location_display = item.location
            if item.location_korean and item.location_korean != item.location:
                location_display = f"{item.location} ({item.location_korean})"

            lines.append(f"### {item.time_start} - {item.time_end}")
            lines.append(f"**{item.activity}**")
            lines.append(f"📍 {location_display}")

            if item.estimated_cost > 0:
                cost_usd = round(item.estimated_cost / 1400, 2)
                lines.append(f"💰 ~₩{item.estimated_cost:,} (~${cost_usd})")

            if item.notes:
                lines.append(f"💡 {item.notes}")

            lines.append("")

        if day.total_estimated_cost > 0:
            day_usd = round(day.total_estimated_cost / 1400, 2)
            lines.append(f"**Day Total:** ~₩{day.total_estimated_cost:,} (~${day_usd})")
            lines.append("")

    # Add tips
    if itinerary.tips:
        lines.append("## Tips")
        for tip in itinerary.tips:
            lines.append(f"- {tip}")
        lines.append("")

    # Total cost
    if itinerary.total_estimated_cost > 0:
        total_usd = round(itinerary.total_estimated_cost / 1400, 2)
        lines.append(f"## Estimated Total Cost")
        lines.append(f"₩{itinerary.total_estimated_cost:,} (~${total_usd} USD)")

    return "\n".join(lines)


@tool
async def create_day_itinerary(
    interests: str,
    area: str = "Seoul",
    budget_level: str = "mid",
    start_time: str = "09:00",
) -> str:
    """
    Create a one-day itinerary based on interests.

    Use this tool when the user wants a full day plan.

    Args:
        interests: User interests (e.g., "history, food, shopping")
        area: Area to explore (default: Seoul)
        budget_level: Budget level (budget/mid/high)
        start_time: Day start time (HH:MM)

    Returns:
        Formatted day itinerary
    """
    interests_list = [i.strip().lower() for i in interests.split(",")]

    items = []
    current_time = datetime.strptime(start_time, "%H:%M")
    total_cost = 0

    # Select attractions based on interests
    selected = []

    if any(i in interests_list for i in ["history", "culture", "palace"]):
        selected.append("gyeongbokgung")
        selected.append("bukchon")

    if any(i in interests_list for i in ["shopping", "cosmetics"]):
        selected.append("myeongdong")

    if any(i in interests_list for i in ["food", "market", "local"]):
        selected.append("gwangjang")

    if any(i in interests_list for i in ["nightlife", "music", "young"]):
        selected.append("hongdae")

    if any(i in interests_list for i in ["view", "romantic", "tower"]):
        selected.append("namsan")

    if any(i in interests_list for i in ["art", "traditional", "craft"]):
        selected.append("insadong")

    # Default selection if nothing matched
    if not selected:
        selected = ["gyeongbokgung", "bukchon", "insadong", "myeongdong"]

    # Limit to 4-5 attractions per day
    selected = selected[:5]

    # Build itinerary
    for i, key in enumerate(selected):
        attraction = SEOUL_ATTRACTIONS.get(key, {})
        if not attraction:
            continue

        duration = attraction.get("duration", 90)

        # Add meal breaks
        if current_time.hour >= 12 and current_time.hour < 14 and not any(
            item.category == "meal" for item in items
        ):
            # Lunch break
            meal_cost = ACTIVITY_COSTS.get(f"meal_{budget_level}", 15000)
            items.append(ItineraryItem(
                time_start=current_time.strftime("%H:%M"),
                time_end=(current_time + timedelta(minutes=60)).strftime("%H:%M"),
                activity="Lunch",
                location=f"Near {attraction['name']}",
                location_korean="",
                category="meal",
                duration_minutes=60,
                estimated_cost=meal_cost,
            ))
            current_time += timedelta(minutes=60)
            total_cost += meal_cost

        # Add attraction
        items.append(ItineraryItem(
            time_start=current_time.strftime("%H:%M"),
            time_end=(current_time + timedelta(minutes=duration)).strftime("%H:%M"),
            activity=f"Visit {attraction['name']}",
            location=attraction["name"],
            location_korean=attraction.get("korean", ""),
            category=attraction.get("category", "attraction"),
            duration_minutes=duration,
            notes=attraction.get("tips", ""),
            estimated_cost=attraction.get("cost", 0),
        ))
        total_cost += attraction.get("cost", 0)
        current_time += timedelta(minutes=duration)

        # Add transport time between locations
        if i < len(selected) - 1:
            items.append(ItineraryItem(
                time_start=current_time.strftime("%H:%M"),
                time_end=(current_time + timedelta(minutes=20)).strftime("%H:%M"),
                activity="Travel to next location",
                location="Subway/Walking",
                location_korean="",
                category="transport",
                duration_minutes=20,
                estimated_cost=1400,
            ))
            current_time += timedelta(minutes=20)
            total_cost += 1400

    # Add dinner
    if current_time.hour >= 18:
        meal_cost = ACTIVITY_COSTS.get(f"meal_{budget_level}", 20000)
        items.append(ItineraryItem(
            time_start=current_time.strftime("%H:%M"),
            time_end=(current_time + timedelta(minutes=75)).strftime("%H:%M"),
            activity="Dinner",
            location="Local restaurant",
            location_korean="",
            category="meal",
            duration_minutes=75,
            estimated_cost=meal_cost,
        ))
        total_cost += meal_cost

    day = DayItinerary(
        day_number=1,
        theme=f"Exploring {area}: {', '.join(interests_list[:3])}",
        items=items,
        total_estimated_cost=total_cost,
    )

    itinerary = TravelItinerary(
        title=f"One Day in {area}",
        duration_days=1,
        days=[day],
        total_estimated_cost=total_cost,
        tips=[
            "Get a T-money card for easy subway/bus payment",
            "Download Naver Map app - Google Maps doesn't work well in Korea",
            "Many places close on Mondays (especially palaces)",
            "Cash is still preferred at traditional markets",
        ],
    )

    return format_itinerary(itinerary)


@tool
async def suggest_attraction(
    interest: str,
    area: str = "Seoul",
) -> str:
    """
    Suggest an attraction based on interest.

    Use this for quick attraction recommendations.

    Args:
        interest: Type of attraction (history, food, shopping, nightlife, etc.)
        area: Area (default: Seoul)

    Returns:
        Attraction recommendation
    """
    interest_lower = interest.lower()

    recommendations = {
        "history": ["gyeongbokgung", "bukchon"],
        "culture": ["insadong", "bukchon"],
        "food": ["gwangjang", "myeongdong"],
        "shopping": ["myeongdong", "dongdaemun"],
        "nightlife": ["hongdae", "itaewon"],
        "view": ["namsan"],
        "art": ["insadong", "dongdaemun"],
        "traditional": ["bukchon", "insadong"],
    }

    keys = recommendations.get(interest_lower, ["gyeongbokgung"])

    results = []
    for key in keys[:2]:
        attraction = SEOUL_ATTRACTIONS.get(key)
        if attraction:
            lines = [
                f"## {attraction['name']} ({attraction.get('korean', '')})",
                f"**Category:** {attraction.get('category', 'attraction')}",
                f"**Duration:** ~{attraction.get('duration', 90)} minutes",
            ]

            if attraction.get("cost", 0) > 0:
                cost_usd = round(attraction["cost"] / 1400, 2)
                lines.append(f"**Entry:** ₩{attraction['cost']:,} (~${cost_usd})")
            else:
                lines.append("**Entry:** Free")

            if attraction.get("hours"):
                lines.append(f"**Hours:** {attraction['hours']}")

            if attraction.get("closed"):
                lines.append(f"**Closed:** {attraction['closed']}")

            if attraction.get("tips"):
                lines.append(f"**Tip:** {attraction['tips']}")

            results.append("\n".join(lines))

    return "\n\n".join(results) if results else f"No specific recommendations for '{interest}'. Try: history, food, shopping, nightlife, view, art, traditional"


@tool
async def estimate_trip_cost(
    days: int,
    budget_level: str = "mid",
    include_accommodation: bool = True,
) -> str:
    """
    Estimate total trip cost.

    Use this when users ask about budget for their Korea trip.

    Args:
        days: Number of days
        budget_level: Budget level (budget/mid/high)
        include_accommodation: Include hotel costs

    Returns:
        Cost breakdown
    """
    costs = {
        "budget": {
            "hotel": 50000,
            "meals": 30000,
            "transport": 10000,
            "attractions": 15000,
            "misc": 10000,
        },
        "mid": {
            "hotel": 100000,
            "meals": 50000,
            "transport": 15000,
            "attractions": 25000,
            "misc": 20000,
        },
        "high": {
            "hotel": 250000,
            "meals": 100000,
            "transport": 30000,
            "attractions": 40000,
            "misc": 50000,
        },
    }

    level_costs = costs.get(budget_level, costs["mid"])
    daily_total = sum(level_costs.values())
    if not include_accommodation:
        daily_total -= level_costs["hotel"]

    total = daily_total * days

    lines = [
        f"## Estimated Trip Cost ({days} days, {budget_level} budget)",
        "",
        "### Daily Breakdown:",
    ]

    for category, amount in level_costs.items():
        if category == "hotel" and not include_accommodation:
            continue
        usd = round(amount / 1400, 2)
        lines.append(f"- **{category.capitalize()}:** ₩{amount:,} (~${usd})")

    daily_usd = round(daily_total / 1400, 2)
    total_usd = round(total / 1400, 2)

    lines.extend([
        "",
        f"**Daily Total:** ₩{daily_total:,} (~${daily_usd})",
        f"**{days}-Day Total:** ₩{total:,} (~${total_usd})",
        "",
        "### Tips to Save Money:",
        "- Use T-money card for transport (10% discount)",
        "- Eat at local markets and convenience stores",
        "- Visit free attractions (parks, neighborhoods)",
        "- Book accommodations in advance",
        "- Use subway instead of taxi",
    ])

    return "\n".join(lines)


# Export tools for agent
itinerary_tools = [
    create_day_itinerary,
    suggest_attraction,
    estimate_trip_cost,
]
