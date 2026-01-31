"""
Event models for Agent communication.
Defines the event schema used between Business Agent and Observer Agent.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Types of events emitted by the Business Agent."""

    # Request lifecycle
    REQUEST_STARTED = "request_started"
    REQUEST_COMPLETED = "request_completed"

    # Errors
    ERROR_OCCURRED = "error_occurred"

    # Context engineering
    SUMMARIZATION_TRIGGERED = "summarization_triggered"
    SUMMARIZATION_COMPLETED = "summarization_completed"
    SUMMARIZATION_FALLBACK = "summarization_fallback"
    CONTEXT_TRIMMED = "context_trimmed"

    # Memory
    MEMORY_RETRIEVED = "memory_retrieved"
    MEMORY_STORED = "memory_stored"

    # Entity extraction
    ENTITY_EXTRACTED = "entity_extracted"

    # Security
    RATE_LIMITED = "rate_limited"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"

    # Travel-specific events
    NAVER_API_CALLED = "naver_api_called"
    PLACE_SEARCHED = "place_searched"
    DIRECTIONS_REQUESTED = "directions_requested"
    ITINERARY_GENERATED = "itinerary_generated"
    ITINERARY_OPTIMIZED = "itinerary_optimized"

    # User preferences
    PREFERENCE_EXTRACTED = "preference_extracted"
    LANGUAGE_DETECTED = "language_detected"

    # Translation
    TRANSLATION_PERFORMED = "translation_performed"


class AgentEvent(BaseModel):
    """
    Event model for inter-agent communication.
    Emitted by Business Agent, processed by Observer Agent.
    """

    # Event identification
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    event_type: EventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Context
    thread_id: str
    user_id: str | None = None

    # Event-specific data
    payload: dict[str, Any] = Field(default_factory=dict)

    # Performance metrics
    latency_ms: float | None = None
    token_count: int | None = None

    # Error information (if applicable)
    error_code: str | None = None
    error_message: str | None = None
    stack_trace: str | None = None

    class Config:
        use_enum_values = True


class EventEmitter:
    """
    Helper class to emit events to the Redis queue.
    Used by Business Agent to send events to Observer Agent.
    """

    def __init__(self, redis_client, queue_name: str = "agent:events"):
        """
        Initialize the event emitter.

        Args:
            redis_client: Async Redis client
            queue_name: Name of the Redis queue
        """
        self.redis = redis_client
        self.queue_name = queue_name

    async def emit(self, event: AgentEvent):
        """Emit an event to the queue."""
        await self.redis.rpush(self.queue_name, event.model_dump_json())

    async def emit_request_started(self, thread_id: str, user_id: str | None = None):
        """Emit request started event."""
        await self.emit(
            AgentEvent(
                event_type=EventType.REQUEST_STARTED,
                thread_id=thread_id,
                user_id=user_id,
                payload={"status": "started"},
            )
        )

    async def emit_request_completed(
        self,
        thread_id: str,
        user_id: str | None,
        latency_ms: float,
        token_count: int | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Emit request completed event."""
        await self.emit(
            AgentEvent(
                event_type=EventType.REQUEST_COMPLETED,
                thread_id=thread_id,
                user_id=user_id,
                payload=metadata or {},
                latency_ms=latency_ms,
                token_count=token_count,
            )
        )

    async def emit_error(
        self,
        thread_id: str,
        user_id: str | None,
        error: Exception,
        error_code: str | None = None,
    ):
        """Emit error event."""
        import traceback

        await self.emit(
            AgentEvent(
                event_type=EventType.ERROR_OCCURRED,
                thread_id=thread_id,
                user_id=user_id,
                payload={"error_class": type(error).__name__},
                error_code=error_code or type(error).__name__,
                error_message=str(error),
                stack_trace=traceback.format_exc(),
            )
        )

    async def emit_naver_api_called(
        self,
        thread_id: str,
        api_type: str,
        latency_ms: float,
        success: bool,
    ):
        """Emit Naver API call event."""
        await self.emit(
            AgentEvent(
                event_type=EventType.NAVER_API_CALLED,
                thread_id=thread_id,
                payload={
                    "api_type": api_type,
                    "success": success,
                },
                latency_ms=latency_ms,
            )
        )

    async def emit_prompt_injection_detected(
        self,
        thread_id: str,
        user_id: str | None,
        pattern: str,
        input_preview: str,
    ):
        """Emit prompt injection detection event."""
        await self.emit(
            AgentEvent(
                event_type=EventType.PROMPT_INJECTION_DETECTED,
                thread_id=thread_id,
                user_id=user_id,
                payload={
                    "pattern": pattern,
                    "input_preview": input_preview[:100],  # Truncate for safety
                },
            )
        )
