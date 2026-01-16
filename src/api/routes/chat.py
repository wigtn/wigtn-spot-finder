"""
Chat API endpoints.
Handles conversation with the travel assistant agent.
"""

import logging
import time
from datetime import datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.agents.business_agent import create_business_agent
from src.config.settings import settings
from src.models.state import AgentState, ConversationStage, TravelPreferences

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str = Field(..., min_length=1, max_length=4000, description="User's message")
    thread_id: str | None = Field(default=None, description="Conversation thread ID")
    user_id: str | None = Field(default=None, description="User identifier")
    language: str = Field(default="en", description="Preferred response language")


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    response: str = Field(..., description="Agent's response")
    thread_id: str = Field(..., description="Conversation thread ID")
    turn_number: int = Field(default=0, description="Current turn number")
    stage: str = Field(default="init", description="Conversation stage")
    latency_ms: float = Field(default=0.0, description="Response latency in milliseconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ConversationInfo(BaseModel):
    """Information about a conversation."""

    thread_id: str
    user_id: str | None
    stage: str
    turn_count: int
    created_at: str
    last_message_at: str | None


# =============================================================================
# State Management (In-memory for MVP, will be replaced with DB/Redis)
# =============================================================================

# Simple in-memory state store for MVP
# TODO: Replace with Redis/PostgreSQL backed store
_conversation_states: dict[str, AgentState] = {}


def get_or_create_state(thread_id: str, user_id: str | None = None) -> AgentState:
    """Get existing state or create new one for a thread."""
    if thread_id not in _conversation_states:
        _conversation_states[thread_id] = AgentState(
            thread_id=thread_id,
            user_id=user_id,
            stage=ConversationStage.INIT,
            travel_preferences=TravelPreferences(),
        )
    return _conversation_states[thread_id]


def update_state(thread_id: str, updates: dict[str, Any]) -> AgentState:
    """Update state for a thread."""
    state = _conversation_states.get(thread_id)
    if state:
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
    return state


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Send a message to the travel assistant and get a response.

    This is the main conversation endpoint. It:
    1. Creates or retrieves conversation state
    2. Processes the message through the Business Agent
    3. Returns the agent's response
    """
    start_time = time.time()

    try:
        # Generate thread_id if not provided
        thread_id = request.thread_id or f"thread_{uuid4().hex[:12]}"

        # Get or create conversation state
        state = get_or_create_state(thread_id, request.user_id)

        # Update language preference if provided
        if request.language and request.language != state.travel_preferences.language:
            state.travel_preferences.language = request.language

        # Create agent and invoke
        agent = create_business_agent()
        result = await agent.invoke(
            message=request.message,
            thread_id=thread_id,
            state=state,
        )

        # Update turn metadata
        state.turn_metadata.turn_number += 1
        state.turn_metadata.timestamp = datetime.utcnow()

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000
        state.turn_metadata.latency_ms = latency_ms

        logger.info(
            f"Chat completed: thread={thread_id}, turn={state.turn_metadata.turn_number}, "
            f"latency={latency_ms:.2f}ms"
        )

        return ChatResponse(
            response=result["response"],
            thread_id=thread_id,
            turn_number=state.turn_metadata.turn_number,
            stage=state.stage.value,
            latency_ms=latency_ms,
        )

    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}",
        )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Stream a response from the travel assistant.

    Returns Server-Sent Events (SSE) for real-time streaming.
    """
    thread_id = request.thread_id or f"thread_{uuid4().hex[:12]}"
    state = get_or_create_state(thread_id, request.user_id)

    if request.language:
        state.travel_preferences.language = request.language

    agent = create_business_agent()

    async def generate():
        try:
            async for chunk in agent.stream(
                message=request.message,
                thread_id=thread_id,
                state=state,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Thread-ID": thread_id,
        },
    )


@router.get("/conversations/{thread_id}", response_model=ConversationInfo)
async def get_conversation(thread_id: str):
    """
    Get information about a specific conversation.
    """
    state = _conversation_states.get(thread_id)
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation not found: {thread_id}",
        )

    return ConversationInfo(
        thread_id=thread_id,
        user_id=state.user_id,
        stage=state.stage.value,
        turn_count=state.turn_metadata.turn_number,
        created_at=datetime.utcnow().isoformat(),  # TODO: Store actual creation time
        last_message_at=state.turn_metadata.timestamp.isoformat()
        if state.turn_metadata.timestamp
        else None,
    )


@router.delete("/conversations/{thread_id}")
async def delete_conversation(thread_id: str):
    """
    Delete a conversation and its state.
    """
    if thread_id not in _conversation_states:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation not found: {thread_id}",
        )

    del _conversation_states[thread_id]
    logger.info(f"Deleted conversation: {thread_id}")

    return {"message": f"Conversation {thread_id} deleted successfully"}


@router.get("/conversations")
async def list_conversations(
    user_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
):
    """
    List conversations, optionally filtered by user_id.
    """
    conversations = []
    for thread_id, state in _conversation_states.items():
        if user_id and state.user_id != user_id:
            continue
        conversations.append(
            ConversationInfo(
                thread_id=thread_id,
                user_id=state.user_id,
                stage=state.stage.value,
                turn_count=state.turn_metadata.turn_number,
                created_at=datetime.utcnow().isoformat(),
                last_message_at=state.turn_metadata.timestamp.isoformat()
                if state.turn_metadata.timestamp
                else None,
            )
        )

    # Apply pagination
    total = len(conversations)
    conversations = conversations[offset : offset + limit]

    return {
        "conversations": conversations,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
