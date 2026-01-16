"""
Memory Retrieval Pipeline.
Retrieves and ranks relevant memories for conversation context.
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from src.services.memory.memory_store import (
    MemoryStore,
    Memory,
    MemoryType,
    get_memory_store,
)

logger = logging.getLogger(__name__)


class RetrievalConfig:
    """Configuration for memory retrieval."""

    def __init__(
        self,
        max_memories: int = 5,
        score_threshold: float = 0.7,
        recency_weight: float = 0.2,
        relevance_weight: float = 0.8,
        include_user_preferences: bool = True,
        include_recent_context: bool = True,
        recency_window_hours: int = 24,
    ):
        """
        Initialize retrieval configuration.

        Args:
            max_memories: Maximum memories to return
            score_threshold: Minimum similarity score
            recency_weight: Weight for recency in ranking
            relevance_weight: Weight for relevance in ranking
            include_user_preferences: Include user preference memories
            include_recent_context: Include recent conversation context
            recency_window_hours: Hours to consider for "recent"
        """
        self.max_memories = max_memories
        self.score_threshold = score_threshold
        self.recency_weight = recency_weight
        self.relevance_weight = relevance_weight
        self.include_user_preferences = include_user_preferences
        self.include_recent_context = include_recent_context
        self.recency_window_hours = recency_window_hours


class MemoryRetrievalPipeline:
    """
    Pipeline for retrieving relevant memories for conversation.
    Combines semantic search with recency-based ranking.
    """

    def __init__(
        self,
        memory_store: MemoryStore | None = None,
        config: RetrievalConfig | None = None,
    ):
        """
        Initialize retrieval pipeline.

        Args:
            memory_store: Memory store instance
            config: Retrieval configuration
        """
        self._memory_store = memory_store
        self.config = config or RetrievalConfig()

    @property
    def memory_store(self) -> MemoryStore:
        """Get memory store."""
        if self._memory_store is None:
            self._memory_store = get_memory_store()
        return self._memory_store

    async def retrieve_for_context(
        self,
        query: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        additional_context: str | None = None,
    ) -> list[str]:
        """
        Retrieve relevant memories formatted for LLM context.

        Args:
            query: Current user message
            user_id: User ID for filtering
            thread_id: Thread ID for filtering
            additional_context: Additional context to consider

        Returns:
            List of memory strings for prompt context
        """
        memories = await self.retrieve(
            query=query,
            user_id=user_id,
            thread_id=thread_id,
            additional_context=additional_context,
        )

        # Format memories for context
        formatted = []
        for memory in memories:
            formatted_memory = self._format_memory_for_context(memory)
            formatted.append(formatted_memory)

        return formatted

    async def retrieve(
        self,
        query: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        additional_context: str | None = None,
        memory_types: list[str] | None = None,
    ) -> list[Memory]:
        """
        Retrieve and rank relevant memories.

        Args:
            query: Search query
            user_id: User ID for filtering
            thread_id: Thread ID for filtering
            additional_context: Additional search context
            memory_types: Specific memory types to retrieve

        Returns:
            List of Memory objects, ranked by relevance
        """
        all_memories = []

        # Combine query with additional context if provided
        search_query = query
        if additional_context:
            search_query = f"{query} {additional_context}"

        # 1. Semantic search for relevant memories
        semantic_memories = await self.memory_store.search_memories(
            query=search_query,
            user_id=user_id,
            thread_id=thread_id,
            memory_types=memory_types,
            limit=self.config.max_memories * 2,  # Get more for re-ranking
            score_threshold=self.config.score_threshold,
        )
        all_memories.extend(semantic_memories)

        # 2. Include user preferences if configured
        if self.config.include_user_preferences and user_id:
            preference_memories = await self.memory_store.search_memories(
                query=search_query,
                user_id=user_id,
                memory_types=[MemoryType.PREFERENCE],
                limit=3,
                score_threshold=0.5,  # Lower threshold for preferences
            )

            # Add preferences not already in results
            existing_ids = {m.id for m in all_memories}
            for mem in preference_memories:
                if mem.id not in existing_ids:
                    all_memories.append(mem)

        # 3. Include recent context if configured
        if self.config.include_recent_context and thread_id:
            recent_memories = await self._get_recent_memories(
                thread_id=thread_id,
                hours=self.config.recency_window_hours,
                limit=3,
            )

            existing_ids = {m.id for m in all_memories}
            for mem in recent_memories:
                if mem.id not in existing_ids:
                    all_memories.append(mem)

        # 4. Re-rank by combined score
        ranked_memories = self._rank_memories(all_memories)

        # 5. Return top N
        return ranked_memories[:self.config.max_memories]

    async def _get_recent_memories(
        self,
        thread_id: str,
        hours: int,
        limit: int,
    ) -> list[Memory]:
        """Get memories from the last N hours."""
        # Use scroll to get recent memories
        from qdrant_client.http import models
        from src.db.qdrant.connection import MEMORY_COLLECTION

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        results, _ = self.memory_store.client.scroll(
            collection_name=MEMORY_COLLECTION,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="thread_id",
                        match=models.MatchValue(value=thread_id),
                    ),
                ]
            ),
            limit=limit * 2,  # Get more to filter by time
            with_payload=True,
            with_vectors=False,
        )

        memories = []
        for result in results:
            payload = result.payload or {}
            created_at_str = payload.get("created_at")

            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str)
                if created_at >= cutoff_time:
                    memory = Memory(
                        id=str(result.id),
                        content=payload.get("content", ""),
                        memory_type=payload.get("memory_type", "unknown"),
                        user_id=payload.get("user_id"),
                        thread_id=payload.get("thread_id"),
                        metadata={
                            k: v for k, v in payload.items()
                            if k not in ["content", "memory_type", "user_id", "thread_id", "created_at"]
                        },
                        score=0.5,  # Default score for recent memories
                        created_at=created_at,
                    )
                    memories.append(memory)

                    if len(memories) >= limit:
                        break

        return memories

    def _rank_memories(self, memories: list[Memory]) -> list[Memory]:
        """
        Rank memories by combined relevance and recency score.

        Args:
            memories: List of memories to rank

        Returns:
            Sorted list of memories
        """
        if not memories:
            return []

        now = datetime.utcnow()
        scored_memories = []

        for memory in memories:
            # Relevance score (from semantic search)
            relevance_score = memory.score

            # Recency score (decay over time)
            if memory.created_at:
                age_hours = (now - memory.created_at).total_seconds() / 3600
                recency_score = max(0, 1 - (age_hours / (self.config.recency_window_hours * 7)))
            else:
                recency_score = 0.5

            # Combined score
            combined_score = (
                self.config.relevance_weight * relevance_score +
                self.config.recency_weight * recency_score
            )

            # Boost for preference memories
            if memory.memory_type == MemoryType.PREFERENCE:
                combined_score *= 1.2

            scored_memories.append((memory, combined_score))

        # Sort by combined score
        scored_memories.sort(key=lambda x: x[1], reverse=True)

        # Update memory scores and return
        result = []
        for memory, score in scored_memories:
            memory.score = score
            result.append(memory)

        return result

    def _format_memory_for_context(self, memory: Memory) -> str:
        """
        Format a memory for inclusion in prompt context.

        Args:
            memory: Memory object

        Returns:
            Formatted string
        """
        type_labels = {
            MemoryType.CONVERSATION: "Previous conversation",
            MemoryType.PREFERENCE: "User preference",
            MemoryType.PLACE: "Visited place",
            MemoryType.ITINERARY: "Previous itinerary",
            MemoryType.FEEDBACK: "User feedback",
            MemoryType.ENTITY: "Known information",
        }

        label = type_labels.get(memory.memory_type, "Memory")

        # Add time context for recent memories
        if memory.created_at:
            age = datetime.utcnow() - memory.created_at
            if age < timedelta(hours=1):
                time_context = "just now"
            elif age < timedelta(hours=24):
                time_context = f"{int(age.total_seconds() / 3600)} hours ago"
            elif age < timedelta(days=7):
                time_context = f"{age.days} days ago"
            else:
                time_context = memory.created_at.strftime("%Y-%m-%d")
        else:
            time_context = ""

        if time_context:
            return f"[{label} - {time_context}] {memory.content}"
        else:
            return f"[{label}] {memory.content}"


class ConversationMemoryManager:
    """
    High-level manager for conversation memory operations.
    Handles storing conversation turns and extracting memories.
    """

    def __init__(
        self,
        memory_store: MemoryStore | None = None,
        retrieval_pipeline: MemoryRetrievalPipeline | None = None,
    ):
        """
        Initialize memory manager.

        Args:
            memory_store: Memory store instance
            retrieval_pipeline: Retrieval pipeline instance
        """
        self._memory_store = memory_store
        self._retrieval_pipeline = retrieval_pipeline

    @property
    def memory_store(self) -> MemoryStore:
        """Get memory store."""
        if self._memory_store is None:
            self._memory_store = get_memory_store()
        return self._memory_store

    @property
    def retrieval_pipeline(self) -> MemoryRetrievalPipeline:
        """Get retrieval pipeline."""
        if self._retrieval_pipeline is None:
            self._retrieval_pipeline = MemoryRetrievalPipeline(
                memory_store=self.memory_store
            )
        return self._retrieval_pipeline

    async def store_conversation_turn(
        self,
        user_message: str,
        assistant_message: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        extracted_entities: list[str] | None = None,
    ) -> list[str]:
        """
        Store a conversation turn as memories.

        Args:
            user_message: User's message
            assistant_message: Assistant's response
            user_id: User ID
            thread_id: Thread ID
            extracted_entities: Entities extracted from the turn

        Returns:
            List of stored memory IDs
        """
        memories_to_store = []
        memory_ids = []

        # Store conversation context
        conversation_content = f"User asked: {user_message}\nAssistant responded: {assistant_message[:500]}"

        memories_to_store.append({
            "content": conversation_content,
            "memory_type": MemoryType.CONVERSATION,
            "user_id": user_id,
            "thread_id": thread_id,
        })

        # Store entities as separate memories
        if extracted_entities:
            for entity in extracted_entities:
                if ":" in entity:
                    entity_type, entity_value = entity.split(":", 1)

                    memories_to_store.append({
                        "content": f"{entity_type}: {entity_value}",
                        "memory_type": MemoryType.ENTITY,
                        "user_id": user_id,
                        "thread_id": thread_id,
                        "metadata": {
                            "entity_type": entity_type,
                            "entity_value": entity_value,
                        },
                    })

        # Batch store
        if memories_to_store:
            memory_ids = await self.memory_store.store_memories(memories_to_store)

        return memory_ids

    async def store_user_preference(
        self,
        preference_key: str,
        preference_value: str,
        user_id: str,
        thread_id: str | None = None,
    ) -> str:
        """
        Store a user preference.

        Args:
            preference_key: Preference key (e.g., "dietary", "budget")
            preference_value: Preference value
            user_id: User ID
            thread_id: Optional thread ID

        Returns:
            Memory ID
        """
        content = f"User preference - {preference_key}: {preference_value}"

        return await self.memory_store.store_memory(
            content=content,
            memory_type=MemoryType.PREFERENCE,
            user_id=user_id,
            thread_id=thread_id,
            metadata={
                "preference_key": preference_key,
                "preference_value": preference_value,
            },
        )

    async def store_place_visit(
        self,
        place_name: str,
        place_type: str,
        user_id: str,
        thread_id: str | None = None,
        rating: float | None = None,
        notes: str | None = None,
    ) -> str:
        """
        Store a place visit memory.

        Args:
            place_name: Name of the place
            place_type: Type (restaurant, attraction, etc.)
            user_id: User ID
            thread_id: Optional thread ID
            rating: Optional user rating
            notes: Optional notes

        Returns:
            Memory ID
        """
        content_parts = [f"Visited {place_type}: {place_name}"]
        if rating:
            content_parts.append(f"Rating: {rating}/5")
        if notes:
            content_parts.append(f"Notes: {notes}")

        content = ". ".join(content_parts)

        return await self.memory_store.store_memory(
            content=content,
            memory_type=MemoryType.PLACE,
            user_id=user_id,
            thread_id=thread_id,
            metadata={
                "place_name": place_name,
                "place_type": place_type,
                "rating": rating,
            },
        )

    async def get_relevant_context(
        self,
        query: str,
        user_id: str | None = None,
        thread_id: str | None = None,
    ) -> list[str]:
        """
        Get relevant memories formatted for LLM context.

        Args:
            query: Current query/message
            user_id: User ID
            thread_id: Thread ID

        Returns:
            List of formatted memory strings
        """
        return await self.retrieval_pipeline.retrieve_for_context(
            query=query,
            user_id=user_id,
            thread_id=thread_id,
        )


# Global instances
_retrieval_pipeline: MemoryRetrievalPipeline | None = None
_memory_manager: ConversationMemoryManager | None = None


def get_retrieval_pipeline() -> MemoryRetrievalPipeline:
    """Get global retrieval pipeline instance."""
    global _retrieval_pipeline
    if _retrieval_pipeline is None:
        _retrieval_pipeline = MemoryRetrievalPipeline()
    return _retrieval_pipeline


def get_memory_manager() -> ConversationMemoryManager:
    """Get global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = ConversationMemoryManager()
    return _memory_manager
