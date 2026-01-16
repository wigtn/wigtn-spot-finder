"""
Summary Store for persisting conversation summaries.
"""

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres.connection import get_db_session

logger = logging.getLogger(__name__)


class SummaryStore:
    """
    Store for conversation summaries.
    Handles CRUD operations for summaries in PostgreSQL.
    """

    def __init__(self, session: AsyncSession | None = None):
        """
        Initialize the summary store.

        Args:
            session: Optional SQLAlchemy async session
        """
        self._session = session

    async def _get_session(self) -> AsyncSession:
        """Get or create a database session."""
        if self._session:
            return self._session
        return await anext(get_db_session())

    async def save_summary(
        self,
        thread_id: str,
        summary_text: str,
        messages_summarized: int,
        token_count: int,
        summary_type: str = "auto",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """
        Save a conversation summary.

        Args:
            thread_id: The conversation thread ID
            summary_text: The summary content
            messages_summarized: Number of messages that were summarized
            token_count: Token count of the summary
            summary_type: Type of summary (auto, manual, extractive)
            metadata: Optional metadata dict

        Returns:
            The summary ID
        """
        session = await self._get_session()

        query = text("""
            INSERT INTO conversation_summaries (
                thread_id, summary_text, messages_summarized,
                token_count, summary_type, metadata, created_at
            )
            VALUES (
                :thread_id, :summary_text, :messages_summarized,
                :token_count, :summary_type, :metadata, :created_at
            )
            RETURNING id
        """)

        result = await session.execute(
            query,
            {
                "thread_id": thread_id,
                "summary_text": summary_text,
                "messages_summarized": messages_summarized,
                "token_count": token_count,
                "summary_type": summary_type,
                "metadata": metadata or {},
                "created_at": datetime.utcnow(),
            },
        )

        await session.commit()
        row = result.fetchone()

        logger.info(
            f"Saved summary for thread {thread_id}: "
            f"{messages_summarized} messages -> {token_count} tokens"
        )

        return str(row[0])

    async def get_latest_summary(self, thread_id: str) -> dict[str, Any] | None:
        """
        Get the most recent summary for a thread.

        Args:
            thread_id: The conversation thread ID

        Returns:
            Summary dict or None if not found
        """
        session = await self._get_session()

        query = text("""
            SELECT id, summary_text, messages_summarized, token_count,
                   summary_type, metadata, created_at
            FROM conversation_summaries
            WHERE thread_id = :thread_id
            ORDER BY created_at DESC
            LIMIT 1
        """)

        result = await session.execute(query, {"thread_id": thread_id})
        row = result.fetchone()

        if not row:
            return None

        return {
            "id": str(row[0]),
            "summary_text": row[1],
            "messages_summarized": row[2],
            "token_count": row[3],
            "summary_type": row[4],
            "metadata": row[5],
            "created_at": row[6],
        }

    async def get_all_summaries(
        self,
        thread_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get all summaries for a thread.

        Args:
            thread_id: The conversation thread ID
            limit: Maximum number of summaries to return

        Returns:
            List of summary dicts
        """
        session = await self._get_session()

        query = text("""
            SELECT id, summary_text, messages_summarized, token_count,
                   summary_type, metadata, created_at
            FROM conversation_summaries
            WHERE thread_id = :thread_id
            ORDER BY created_at DESC
            LIMIT :limit
        """)

        result = await session.execute(
            query,
            {"thread_id": thread_id, "limit": limit},
        )

        summaries = []
        for row in result.fetchall():
            summaries.append({
                "id": str(row[0]),
                "summary_text": row[1],
                "messages_summarized": row[2],
                "token_count": row[3],
                "summary_type": row[4],
                "metadata": row[5],
                "created_at": row[6],
            })

        return summaries

    async def get_combined_summary(self, thread_id: str) -> str | None:
        """
        Get a combined summary from all summaries for a thread.
        Useful for long conversations with multiple summarization rounds.

        Args:
            thread_id: The conversation thread ID

        Returns:
            Combined summary text or None
        """
        summaries = await self.get_all_summaries(thread_id, limit=5)

        if not summaries:
            return None

        if len(summaries) == 1:
            return summaries[0]["summary_text"]

        # Combine summaries in chronological order
        summaries.reverse()
        combined_parts = []

        for i, summary in enumerate(summaries, 1):
            if len(summaries) > 1:
                combined_parts.append(f"[Part {i}]")
            combined_parts.append(summary["summary_text"])

        return "\n\n".join(combined_parts)

    async def delete_old_summaries(
        self,
        thread_id: str,
        keep_count: int = 3,
    ) -> int:
        """
        Delete old summaries, keeping only the most recent ones.

        Args:
            thread_id: The conversation thread ID
            keep_count: Number of summaries to keep

        Returns:
            Number of deleted summaries
        """
        session = await self._get_session()

        # Find IDs to keep
        keep_query = text("""
            SELECT id FROM conversation_summaries
            WHERE thread_id = :thread_id
            ORDER BY created_at DESC
            LIMIT :keep_count
        """)

        result = await session.execute(
            keep_query,
            {"thread_id": thread_id, "keep_count": keep_count},
        )
        keep_ids = [row[0] for row in result.fetchall()]

        if not keep_ids:
            return 0

        # Delete others
        delete_query = text("""
            DELETE FROM conversation_summaries
            WHERE thread_id = :thread_id
            AND id NOT IN :keep_ids
        """)

        result = await session.execute(
            delete_query,
            {"thread_id": thread_id, "keep_ids": tuple(keep_ids)},
        )

        await session.commit()
        deleted_count = result.rowcount

        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} old summaries for thread {thread_id}")

        return deleted_count

    async def get_total_messages_summarized(self, thread_id: str) -> int:
        """
        Get total number of messages that have been summarized.

        Args:
            thread_id: The conversation thread ID

        Returns:
            Total message count
        """
        session = await self._get_session()

        query = text("""
            SELECT COALESCE(SUM(messages_summarized), 0)
            FROM conversation_summaries
            WHERE thread_id = :thread_id
        """)

        result = await session.execute(query, {"thread_id": thread_id})
        row = result.fetchone()

        return int(row[0]) if row else 0


def create_summary_store(session: AsyncSession | None = None) -> SummaryStore:
    """Factory function for creating summary store."""
    return SummaryStore(session=session)
