"""
Metadata Store for persisting turn metadata.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres.connection import get_db_session
from src.models.state import TurnMetadata

logger = logging.getLogger(__name__)


class MetadataStore:
    """
    Store for conversation turn metadata.
    Tracks metrics and analytics data in PostgreSQL.
    """

    def __init__(self, session: AsyncSession | None = None):
        """
        Initialize the metadata store.

        Args:
            session: Optional SQLAlchemy async session
        """
        self._session = session

    async def _get_session(self) -> AsyncSession:
        """Get or create a database session."""
        if self._session:
            return self._session
        return await anext(get_db_session())

    async def save_turn_metadata(
        self,
        thread_id: str,
        user_id: str | None,
        metadata: TurnMetadata,
        entities: list[str] | None = None,
    ) -> str:
        """
        Save turn metadata.

        Args:
            thread_id: The conversation thread ID
            user_id: Optional user ID
            metadata: TurnMetadata object
            entities: Optional list of extracted entities

        Returns:
            The metadata record ID
        """
        session = await self._get_session()

        query = text("""
            INSERT INTO turn_metadata (
                thread_id, user_id, turn_number, timestamp,
                user_intent, latency_ms, token_count, entities, created_at
            )
            VALUES (
                :thread_id, :user_id, :turn_number, :timestamp,
                :user_intent, :latency_ms, :token_count, :entities, :created_at
            )
            RETURNING id
        """)

        result = await session.execute(
            query,
            {
                "thread_id": thread_id,
                "user_id": user_id,
                "turn_number": metadata.turn_number,
                "timestamp": metadata.timestamp,
                "user_intent": metadata.user_intent,
                "latency_ms": metadata.latency_ms,
                "token_count": metadata.token_count,
                "entities": entities or [],
                "created_at": datetime.utcnow(),
            },
        )

        await session.commit()
        row = result.fetchone()

        logger.debug(
            f"Saved turn metadata for thread {thread_id}: "
            f"turn {metadata.turn_number}, intent={metadata.user_intent}"
        )

        return str(row[0])

    async def get_turn_metadata(
        self,
        thread_id: str,
        turn_number: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get turn metadata for a thread.

        Args:
            thread_id: The conversation thread ID
            turn_number: Optional specific turn number

        Returns:
            List of metadata dicts
        """
        session = await self._get_session()

        if turn_number is not None:
            query = text("""
                SELECT id, turn_number, timestamp, user_intent,
                       latency_ms, token_count, entities, created_at
                FROM turn_metadata
                WHERE thread_id = :thread_id AND turn_number = :turn_number
                ORDER BY created_at DESC
            """)
            params = {"thread_id": thread_id, "turn_number": turn_number}
        else:
            query = text("""
                SELECT id, turn_number, timestamp, user_intent,
                       latency_ms, token_count, entities, created_at
                FROM turn_metadata
                WHERE thread_id = :thread_id
                ORDER BY turn_number ASC
            """)
            params = {"thread_id": thread_id}

        result = await session.execute(query, params)

        metadata_list = []
        for row in result.fetchall():
            metadata_list.append({
                "id": str(row[0]),
                "turn_number": row[1],
                "timestamp": row[2],
                "user_intent": row[3],
                "latency_ms": row[4],
                "token_count": row[5],
                "entities": row[6],
                "created_at": row[7],
            })

        return metadata_list

    async def get_conversation_stats(self, thread_id: str) -> dict[str, Any]:
        """
        Get aggregated statistics for a conversation.

        Args:
            thread_id: The conversation thread ID

        Returns:
            Dict with statistics
        """
        session = await self._get_session()

        query = text("""
            SELECT
                COUNT(*) as total_turns,
                AVG(latency_ms) as avg_latency_ms,
                MAX(latency_ms) as max_latency_ms,
                MIN(latency_ms) as min_latency_ms,
                SUM(token_count) as total_tokens,
                MIN(timestamp) as first_turn,
                MAX(timestamp) as last_turn
            FROM turn_metadata
            WHERE thread_id = :thread_id
        """)

        result = await session.execute(query, {"thread_id": thread_id})
        row = result.fetchone()

        if not row or row[0] == 0:
            return {
                "total_turns": 0,
                "avg_latency_ms": 0,
                "max_latency_ms": 0,
                "min_latency_ms": 0,
                "total_tokens": 0,
                "first_turn": None,
                "last_turn": None,
                "intent_distribution": {},
            }

        # Get intent distribution
        intent_query = text("""
            SELECT user_intent, COUNT(*) as count
            FROM turn_metadata
            WHERE thread_id = :thread_id
            GROUP BY user_intent
        """)

        intent_result = await session.execute(intent_query, {"thread_id": thread_id})
        intent_distribution = {row[0]: row[1] for row in intent_result.fetchall()}

        return {
            "total_turns": row[0],
            "avg_latency_ms": round(float(row[1]) if row[1] else 0, 2),
            "max_latency_ms": float(row[2]) if row[2] else 0,
            "min_latency_ms": float(row[3]) if row[3] else 0,
            "total_tokens": int(row[4]) if row[4] else 0,
            "first_turn": row[5],
            "last_turn": row[6],
            "intent_distribution": intent_distribution,
        }

    async def get_all_entities(self, thread_id: str) -> list[str]:
        """
        Get all unique entities extracted from a conversation.

        Args:
            thread_id: The conversation thread ID

        Returns:
            List of unique entities
        """
        session = await self._get_session()

        query = text("""
            SELECT DISTINCT unnest(entities) as entity
            FROM turn_metadata
            WHERE thread_id = :thread_id
            AND entities IS NOT NULL
            AND array_length(entities, 1) > 0
        """)

        result = await session.execute(query, {"thread_id": thread_id})
        entities = [row[0] for row in result.fetchall()]

        return entities

    async def save_extracted_entity(
        self,
        thread_id: str,
        entity_type: str,
        entity_value: str,
        confidence: float = 1.0,
        source_turn: int | None = None,
    ) -> str:
        """
        Save an extracted entity to the entities table.

        Args:
            thread_id: The conversation thread ID
            entity_type: Type of entity (place, date, budget, etc.)
            entity_value: The entity value
            confidence: Confidence score (0-1)
            source_turn: Turn number where entity was extracted

        Returns:
            The entity record ID
        """
        session = await self._get_session()

        query = text("""
            INSERT INTO entities (
                thread_id, entity_type, entity_value,
                confidence, source_turn, created_at
            )
            VALUES (
                :thread_id, :entity_type, :entity_value,
                :confidence, :source_turn, :created_at
            )
            ON CONFLICT (thread_id, entity_type, entity_value)
            DO UPDATE SET
                confidence = GREATEST(entities.confidence, EXCLUDED.confidence),
                source_turn = COALESCE(EXCLUDED.source_turn, entities.source_turn)
            RETURNING id
        """)

        result = await session.execute(
            query,
            {
                "thread_id": thread_id,
                "entity_type": entity_type,
                "entity_value": entity_value,
                "confidence": confidence,
                "source_turn": source_turn,
                "created_at": datetime.utcnow(),
            },
        )

        await session.commit()
        row = result.fetchone()

        return str(row[0])

    async def get_entities_by_type(
        self,
        thread_id: str,
        entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get entities from the entities table.

        Args:
            thread_id: The conversation thread ID
            entity_type: Optional entity type filter

        Returns:
            List of entity dicts
        """
        session = await self._get_session()

        if entity_type:
            query = text("""
                SELECT id, entity_type, entity_value, confidence, source_turn, created_at
                FROM entities
                WHERE thread_id = :thread_id AND entity_type = :entity_type
                ORDER BY confidence DESC, created_at DESC
            """)
            params = {"thread_id": thread_id, "entity_type": entity_type}
        else:
            query = text("""
                SELECT id, entity_type, entity_value, confidence, source_turn, created_at
                FROM entities
                WHERE thread_id = :thread_id
                ORDER BY entity_type, confidence DESC
            """)
            params = {"thread_id": thread_id}

        result = await session.execute(query, params)

        entities = []
        for row in result.fetchall():
            entities.append({
                "id": str(row[0]),
                "entity_type": row[1],
                "entity_value": row[2],
                "confidence": float(row[3]),
                "source_turn": row[4],
                "created_at": row[5],
            })

        return entities

    async def delete_thread_metadata(self, thread_id: str) -> int:
        """
        Delete all metadata for a thread.

        Args:
            thread_id: The conversation thread ID

        Returns:
            Number of deleted records
        """
        session = await self._get_session()

        query = text("""
            DELETE FROM turn_metadata
            WHERE thread_id = :thread_id
        """)

        result = await session.execute(query, {"thread_id": thread_id})
        await session.commit()

        deleted_count = result.rowcount
        logger.info(f"Deleted {deleted_count} metadata records for thread {thread_id}")

        return deleted_count


def create_metadata_store(session: AsyncSession | None = None) -> MetadataStore:
    """Factory function for creating metadata store."""
    return MetadataStore(session=session)
