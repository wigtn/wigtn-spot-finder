"""
Memory Store for long-term memory management.
Stores and retrieves memories from Qdrant vector database.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.db.qdrant.connection import get_qdrant_client, MEMORY_COLLECTION
from src.services.memory.embeddings import EmbeddingService, get_embedding_service

logger = logging.getLogger(__name__)


class MemoryType:
    """Types of memories that can be stored."""

    CONVERSATION = "conversation"  # General conversation context
    PREFERENCE = "preference"  # User preferences
    PLACE = "place"  # Place visited or mentioned
    ITINERARY = "itinerary"  # Travel itinerary
    FEEDBACK = "feedback"  # User feedback
    ENTITY = "entity"  # Extracted entities


class Memory:
    """Memory data class."""

    def __init__(
        self,
        id: str,
        content: str,
        memory_type: str,
        user_id: str | None,
        thread_id: str | None,
        metadata: dict[str, Any],
        score: float = 0.0,
        created_at: datetime | None = None,
    ):
        self.id = id
        self.content = content
        self.memory_type = memory_type
        self.user_id = user_id
        self.thread_id = thread_id
        self.metadata = metadata
        self.score = score
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type,
            "user_id": self.user_id,
            "thread_id": self.thread_id,
            "metadata": self.metadata,
            "score": self.score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class MemoryStore:
    """
    Store for managing long-term memories in Qdrant.
    """

    def __init__(
        self,
        client: QdrantClient | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        """
        Initialize memory store.

        Args:
            client: Qdrant client instance
            embedding_service: Embedding service instance
        """
        self._client = client
        self._embedding_service = embedding_service

    @property
    def client(self) -> QdrantClient:
        """Get Qdrant client."""
        if self._client is None:
            self._client = get_qdrant_client()
        return self._client

    @property
    def embedding_service(self) -> EmbeddingService:
        """Get embedding service."""
        if self._embedding_service is None:
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    async def store_memory(
        self,
        content: str,
        memory_type: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        memory_id: str | None = None,
    ) -> str:
        """
        Store a memory in the vector database.

        Args:
            content: Memory content text
            memory_type: Type of memory (see MemoryType)
            user_id: Associated user ID
            thread_id: Associated thread ID
            metadata: Additional metadata
            memory_id: Optional specific memory ID

        Returns:
            Memory ID
        """
        memory_id = memory_id or uuid4().hex

        # Generate embedding
        embedding = await self.embedding_service.embed_text(content)

        # Prepare payload
        payload = {
            "content": content,
            "memory_type": memory_type,
            "user_id": user_id,
            "thread_id": thread_id,
            "created_at": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        # Store in Qdrant
        self.client.upsert(
            collection_name=MEMORY_COLLECTION,
            points=[
                models.PointStruct(
                    id=memory_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )

        logger.debug(
            f"Stored memory {memory_id}: type={memory_type}, "
            f"user={user_id}, thread={thread_id}"
        )

        return memory_id

    async def store_memories(
        self,
        memories: list[dict[str, Any]],
    ) -> list[str]:
        """
        Store multiple memories in batch.

        Args:
            memories: List of memory dicts with keys:
                - content: Memory text
                - memory_type: Type of memory
                - user_id: Optional user ID
                - thread_id: Optional thread ID
                - metadata: Optional additional metadata

        Returns:
            List of memory IDs
        """
        if not memories:
            return []

        # Generate embeddings in batch
        contents = [m["content"] for m in memories]
        embeddings = await self.embedding_service.embed_texts(contents)

        # Prepare points
        points = []
        memory_ids = []

        for i, memory in enumerate(memories):
            memory_id = memory.get("id") or uuid4().hex
            memory_ids.append(memory_id)

            payload = {
                "content": memory["content"],
                "memory_type": memory["memory_type"],
                "user_id": memory.get("user_id"),
                "thread_id": memory.get("thread_id"),
                "created_at": datetime.utcnow().isoformat(),
                **(memory.get("metadata") or {}),
            }

            points.append(
                models.PointStruct(
                    id=memory_id,
                    vector=embeddings[i],
                    payload=payload,
                )
            )

        # Batch upsert
        self.client.upsert(
            collection_name=MEMORY_COLLECTION,
            points=points,
        )

        logger.info(f"Stored {len(memories)} memories in batch")

        return memory_ids

    async def search_memories(
        self,
        query: str,
        user_id: str | None = None,
        thread_id: str | None = None,
        memory_types: list[str] | None = None,
        limit: int = 5,
        score_threshold: float = 0.7,
    ) -> list[Memory]:
        """
        Search for relevant memories using semantic similarity.

        Args:
            query: Search query text
            user_id: Filter by user ID
            thread_id: Filter by thread ID
            memory_types: Filter by memory types
            limit: Maximum results to return
            score_threshold: Minimum similarity score

        Returns:
            List of Memory objects
        """
        # Generate query embedding
        query_embedding = await self.embedding_service.embed_text(query)

        # Build filter conditions
        filter_conditions = []

        if user_id:
            filter_conditions.append(
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id),
                )
            )

        if thread_id:
            filter_conditions.append(
                models.FieldCondition(
                    key="thread_id",
                    match=models.MatchValue(value=thread_id),
                )
            )

        if memory_types:
            filter_conditions.append(
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchAny(any=memory_types),
                )
            )

        # Build query filter
        query_filter = None
        if filter_conditions:
            query_filter = models.Filter(must=filter_conditions)

        # Search
        results = self.client.search(
            collection_name=MEMORY_COLLECTION,
            query_vector=query_embedding,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
        )

        # Convert to Memory objects
        memories = []
        for result in results:
            payload = result.payload or {}
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
                score=result.score,
                created_at=datetime.fromisoformat(payload["created_at"])
                if payload.get("created_at") else None,
            )
            memories.append(memory)

        logger.debug(
            f"Found {len(memories)} memories for query: {query[:50]}..."
        )

        return memories

    async def get_user_memories(
        self,
        user_id: str,
        memory_types: list[str] | None = None,
        limit: int = 20,
    ) -> list[Memory]:
        """
        Get all memories for a user (without semantic search).

        Args:
            user_id: User ID
            memory_types: Optional filter by types
            limit: Maximum results

        Returns:
            List of Memory objects
        """
        filter_conditions = [
            models.FieldCondition(
                key="user_id",
                match=models.MatchValue(value=user_id),
            )
        ]

        if memory_types:
            filter_conditions.append(
                models.FieldCondition(
                    key="memory_type",
                    match=models.MatchAny(any=memory_types),
                )
            )

        results, _ = self.client.scroll(
            collection_name=MEMORY_COLLECTION,
            scroll_filter=models.Filter(must=filter_conditions),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        memories = []
        for result in results:
            payload = result.payload or {}
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
                created_at=datetime.fromisoformat(payload["created_at"])
                if payload.get("created_at") else None,
            )
            memories.append(memory)

        return memories

    async def delete_memory(self, memory_id: str) -> bool:
        """
        Delete a specific memory.

        Args:
            memory_id: Memory ID to delete

        Returns:
            True if deleted
        """
        self.client.delete(
            collection_name=MEMORY_COLLECTION,
            points_selector=models.PointIdsList(
                points=[memory_id],
            ),
        )

        logger.debug(f"Deleted memory: {memory_id}")
        return True

    async def delete_user_memories(self, user_id: str) -> int:
        """
        Delete all memories for a user.

        Args:
            user_id: User ID

        Returns:
            Number of deleted memories
        """
        # Count before deletion
        count_result = self.client.count(
            collection_name=MEMORY_COLLECTION,
            count_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id),
                    )
                ]
            ),
        )

        # Delete
        self.client.delete(
            collection_name=MEMORY_COLLECTION,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="user_id",
                            match=models.MatchValue(value=user_id),
                        )
                    ]
                )
            ),
        )

        deleted_count = count_result.count
        logger.info(f"Deleted {deleted_count} memories for user {user_id}")

        return deleted_count

    async def delete_thread_memories(self, thread_id: str) -> int:
        """
        Delete all memories for a thread.

        Args:
            thread_id: Thread ID

        Returns:
            Number of deleted memories
        """
        count_result = self.client.count(
            collection_name=MEMORY_COLLECTION,
            count_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="thread_id",
                        match=models.MatchValue(value=thread_id),
                    )
                ]
            ),
        )

        self.client.delete(
            collection_name=MEMORY_COLLECTION,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="thread_id",
                            match=models.MatchValue(value=thread_id),
                        )
                    ]
                )
            ),
        )

        deleted_count = count_result.count
        logger.info(f"Deleted {deleted_count} memories for thread {thread_id}")

        return deleted_count


# Global instance
_memory_store: MemoryStore | None = None


def get_memory_store() -> MemoryStore:
    """Get global memory store instance."""
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store
