"""
Agent State definitions for LangGraph.
Defines the state structure for both Business Agent and Observer Agent.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class ConversationStage(str, Enum):
    """Conversation stage for dynamic prompt generation."""

    INIT = "init"  # Initial greeting, collecting basic info
    INVESTIGATION = "investigation"  # Understanding user needs
    PLANNING = "planning"  # Creating travel itinerary
    RESOLUTION = "resolution"  # Finalizing and confirming


class TravelPreferences(BaseModel):
    """User's travel preferences extracted from conversation."""

    language: str = Field(default="en", description="User's preferred language")
    budget_level: str | None = Field(default=None, description="budget/mid-range/luxury")
    dietary_restrictions: list[str] = Field(default_factory=list, description="halal, vegetarian, etc.")
    mobility_level: str | None = Field(default=None, description="full/limited/wheelchair")
    interests: list[str] = Field(default_factory=list, description="history, food, nature, etc.")
    travel_dates: dict[str, str] | None = Field(default=None, description="start_date, end_date")
    accommodation_area: str | None = Field(default=None, description="Where user is staying")


class TurnMetadata(BaseModel):
    """Metadata for each conversation turn."""

    turn_number: int = Field(default=0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_intent: str | None = Field(default=None)
    entities_extracted: list[str] = Field(default_factory=list)
    latency_ms: float | None = Field(default=None)
    token_count: int | None = Field(default=None)


class AgentState(BaseModel):
    """
    Main state for Business Agent (Travel Assistant).
    Used with LangGraph's create_react_agent.
    """

    # Core conversation state - uses add_messages reducer
    messages: Annotated[list[BaseMessage], add_messages] = Field(default_factory=list)

    # Thread identification
    thread_id: str = Field(default="")
    user_id: str | None = Field(default=None)

    # Conversation context
    stage: ConversationStage = Field(default=ConversationStage.INIT)
    turn_metadata: TurnMetadata = Field(default_factory=TurnMetadata)

    # Travel-specific state
    travel_preferences: TravelPreferences = Field(default_factory=TravelPreferences)
    current_itinerary: list[dict[str, Any]] = Field(default_factory=list)
    saved_places: list[str] = Field(default_factory=list)  # List of place IDs

    # Memory context
    retrieved_memories: list[str] = Field(default_factory=list)
    conversation_summary: str | None = Field(default=None)

    # Context management
    context_token_count: int = Field(default=0)
    summarization_needed: bool = Field(default=False)

    # Error tracking
    last_error: str | None = Field(default=None)

    class Config:
        arbitrary_types_allowed = True


class ObserverState(BaseModel):
    """
    State for Observer Agent (Monitoring).
    Tracks events and metrics.
    """

    # Event processing
    pending_events: list[dict[str, Any]] = Field(default_factory=list)
    processed_count: int = Field(default=0)

    # Metrics buffers
    latency_buffer: list[float] = Field(default_factory=list)
    error_counts: dict[str, int] = Field(default_factory=dict)
    api_call_counts: dict[str, int] = Field(default_factory=dict)

    # Analysis results
    last_report_time: datetime | None = Field(default=None)
    anomalies_detected: list[dict[str, Any]] = Field(default_factory=list)

    # Health status
    is_healthy: bool = Field(default=True)
    last_heartbeat: datetime = Field(default_factory=datetime.utcnow)
