"""
SQLite database for popup store data.
Provides async operations for popup store CRUD.
"""

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

import aiosqlite

from src.config.settings import settings
from src.models.instagram import ScrapeLog
from src.models.popup import PopupCategory, PopupStore, PopupSummary

logger = logging.getLogger(__name__)

# Schema SQL
SCHEMA_SQL = """
-- Popup stores table
CREATE TABLE IF NOT EXISTS popup_stores (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_korean TEXT,
    brand TEXT,
    category TEXT NOT NULL DEFAULT 'other',
    tags TEXT,
    location TEXT NOT NULL,
    address TEXT,
    longitude REAL,
    latitude REAL,
    period_start DATE,
    period_end DATE,
    operating_hours TEXT,
    description TEXT NOT NULL,
    description_ja TEXT,
    description_en TEXT,
    images TEXT,
    thumbnail_url TEXT,
    source_post_url TEXT NOT NULL,
    source_post_id TEXT NOT NULL UNIQUE,
    embedding_id TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_popup_category ON popup_stores(category);
CREATE INDEX IF NOT EXISTS idx_popup_period ON popup_stores(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_popup_active ON popup_stores(is_active);
CREATE INDEX IF NOT EXISTS idx_popup_source ON popup_stores(source_post_id);

-- Instagram posts cache table
CREATE TABLE IF NOT EXISTS instagram_posts (
    shortcode TEXT PRIMARY KEY,
    caption TEXT,
    image_urls TEXT,
    timestamp TIMESTAMP,
    likes INTEGER DEFAULT 0,
    hashtags TEXT,
    location_tag TEXT,
    is_processed BOOLEAN DEFAULT 0,
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_insta_processed ON instagram_posts(is_processed);
CREATE INDEX IF NOT EXISTS idx_insta_timestamp ON instagram_posts(timestamp DESC);

-- Scraping logs table
CREATE TABLE IF NOT EXISTS scrape_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    posts_fetched INTEGER DEFAULT 0,
    posts_parsed INTEGER DEFAULT 0,
    popups_created INTEGER DEFAULT 0,
    popups_updated INTEGER DEFAULT 0,
    status TEXT DEFAULT 'running',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class PopupStoreDB:
    """
    SQLite database for popup store operations.
    """

    def __init__(self, db_path: Path | str | None = None):
        """
        Initialize the database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path) if db_path else Path(settings.sqlite_db_path)
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> aiosqlite.Connection:
        """Get or create database connection."""
        if self._conn is None:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            self._conn = await aiosqlite.connect(self.db_path)
            self._conn.row_factory = aiosqlite.Row

            # Initialize schema
            await self._conn.executescript(SCHEMA_SQL)
            await self._conn.commit()

            logger.info(f"Connected to SQLite: {self.db_path}")

        return self._conn

    async def close(self):
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None
            logger.info("SQLite connection closed")

    # Popup Store Operations

    async def create_popup(
        self,
        popup: PopupStore,
        embedding: list[float] | None = None,
    ) -> str:
        """
        Create a new popup store.

        Args:
            popup: PopupStore object
            embedding: Optional embedding vector (stored in Qdrant)

        Returns:
            Popup ID
        """
        conn = await self.connect()

        # Prepare coordinates
        longitude, latitude = None, None
        if popup.coordinates:
            longitude, latitude = popup.coordinates

        await conn.execute(
            """
            INSERT INTO popup_stores (
                id, name, name_korean, brand, category, tags,
                location, address, longitude, latitude,
                period_start, period_end, operating_hours,
                description, description_ja, description_en,
                images, thumbnail_url, source_post_url, source_post_id,
                embedding_id, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                popup.id,
                popup.name,
                popup.name_korean,
                popup.brand,
                popup.category.value,
                json.dumps(popup.tags),
                popup.location,
                popup.address,
                longitude,
                latitude,
                popup.period_start.isoformat() if popup.period_start else None,
                popup.period_end.isoformat() if popup.period_end else None,
                popup.operating_hours,
                popup.description,
                popup.description_ja,
                popup.description_en,
                json.dumps(popup.images),
                popup.thumbnail_url,
                popup.source_post_url,
                popup.source_post_id,
                popup.embedding_id,
                popup.is_active,
                popup.created_at.isoformat(),
                popup.updated_at.isoformat(),
            ),
        )
        await conn.commit()

        # Store embedding in Qdrant if provided
        if embedding and popup.embedding_id:
            await self._store_embedding(popup, embedding)

        return popup.id

    async def _store_embedding(self, popup: PopupStore, embedding: list[float]):
        """Store embedding in Qdrant."""
        try:
            from qdrant_client.models import PointStruct

            from src.db.qdrant.connection import POPUP_COLLECTION, get_qdrant_client

            client = get_qdrant_client()

            point = PointStruct(
                id=popup.embedding_id,
                vector=embedding,
                payload={
                    "popup_id": popup.id,
                    "name": popup.name,
                    "category": popup.category.value,
                    "is_active": popup.is_active,
                    "period_start": popup.period_start.isoformat() if popup.period_start else None,
                    "period_end": popup.period_end.isoformat() if popup.period_end else None,
                },
            )

            client.upsert(collection_name=POPUP_COLLECTION, points=[point])

        except Exception as e:
            logger.warning(f"Failed to store embedding: {e}")

    async def update_popup(self, popup: PopupStore) -> bool:
        """
        Update an existing popup store.

        Args:
            popup: PopupStore with updated data

        Returns:
            True if updated
        """
        conn = await self.connect()

        longitude, latitude = None, None
        if popup.coordinates:
            longitude, latitude = popup.coordinates

        result = await conn.execute(
            """
            UPDATE popup_stores SET
                name = ?, name_korean = ?, brand = ?, category = ?, tags = ?,
                location = ?, address = ?, longitude = ?, latitude = ?,
                period_start = ?, period_end = ?, operating_hours = ?,
                description = ?, description_ja = ?, description_en = ?,
                images = ?, thumbnail_url = ?,
                is_active = ?, updated_at = ?
            WHERE id = ?
            """,
            (
                popup.name,
                popup.name_korean,
                popup.brand,
                popup.category.value,
                json.dumps(popup.tags),
                popup.location,
                popup.address,
                longitude,
                latitude,
                popup.period_start.isoformat() if popup.period_start else None,
                popup.period_end.isoformat() if popup.period_end else None,
                popup.operating_hours,
                popup.description,
                popup.description_ja,
                popup.description_en,
                json.dumps(popup.images),
                popup.thumbnail_url,
                popup.is_active,
                datetime.utcnow().isoformat(),
                popup.id,
            ),
        )
        await conn.commit()

        return result.rowcount > 0

    async def get_popup(self, popup_id: str) -> PopupStore | None:
        """
        Get a popup by ID.

        Args:
            popup_id: Popup ID

        Returns:
            PopupStore or None
        """
        conn = await self.connect()

        cursor = await conn.execute(
            "SELECT * FROM popup_stores WHERE id = ?",
            (popup_id,),
        )
        row = await cursor.fetchone()

        if row:
            return self._row_to_popup(row)
        return None

    async def get_popup_by_source_id(self, source_post_id: str) -> PopupStore | None:
        """
        Get a popup by Instagram post ID.

        Args:
            source_post_id: Instagram post shortcode

        Returns:
            PopupStore or None
        """
        conn = await self.connect()

        cursor = await conn.execute(
            "SELECT * FROM popup_stores WHERE source_post_id = ?",
            (source_post_id,),
        )
        row = await cursor.fetchone()

        if row:
            return self._row_to_popup(row)
        return None

    async def get_active_popups(
        self,
        as_of: date | None = None,
        category: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PopupStore]:
        """
        Get currently active popups.

        Args:
            as_of: Date to check (default: today)
            category: Optional category filter
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of active PopupStore objects
        """
        conn = await self.connect()
        check_date = (as_of or date.today()).isoformat()

        query = """
            SELECT * FROM popup_stores
            WHERE is_active = 1
            AND (period_start IS NULL OR period_start <= ?)
            AND (period_end IS NULL OR period_end >= ?)
        """
        params: list[Any] = [check_date, check_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_popup(row) for row in rows]

    async def search_popups(
        self,
        keyword: str | None = None,
        category: str | None = None,
        active_only: bool = True,
        limit: int = 20,
    ) -> list[PopupStore]:
        """
        Search popups by keyword and filters.

        Args:
            keyword: Search keyword
            category: Category filter
            active_only: Only return active popups
            limit: Maximum results

        Returns:
            List of matching PopupStore objects
        """
        conn = await self.connect()

        query = "SELECT * FROM popup_stores WHERE 1=1"
        params: list[Any] = []

        if active_only:
            check_date = date.today().isoformat()
            query += """
                AND is_active = 1
                AND (period_start IS NULL OR period_start <= ?)
                AND (period_end IS NULL OR period_end >= ?)
            """
            params.extend([check_date, check_date])

        if keyword:
            query += """
                AND (
                    name LIKE ? OR name_korean LIKE ?
                    OR brand LIKE ? OR description LIKE ?
                    OR location LIKE ?
                )
            """
            like_keyword = f"%{keyword}%"
            params.extend([like_keyword] * 5)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        cursor = await conn.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_popup(row) for row in rows]

    async def get_popup_summaries(
        self,
        active_only: bool = True,
        category: str | None = None,
        limit: int = 50,
    ) -> list[PopupSummary]:
        """
        Get popup summaries for list views.

        Args:
            active_only: Only return active popups
            category: Category filter
            limit: Maximum results

        Returns:
            List of PopupSummary objects
        """
        popups = await self.get_active_popups(
            category=category,
            limit=limit,
        ) if active_only else await self.search_popups(
            category=category,
            active_only=False,
            limit=limit,
        )

        return [
            PopupSummary(
                id=p.id,
                name=p.name,
                name_korean=p.name_korean,
                category=p.category.value,
                location=p.location,
                period_start=p.period_start,
                period_end=p.period_end,
                thumbnail_url=p.thumbnail_url,
                is_active=p.is_currently_active(),
            )
            for p in popups
        ]

    async def get_all_popups(self, limit: int = 1000) -> list[PopupStore]:
        """
        Get all popup stores from database.

        Args:
            limit: Maximum results

        Returns:
            List of all PopupStore objects
        """
        conn = await self.connect()

        cursor = await conn.execute(
            "SELECT * FROM popup_stores ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()

        return [self._row_to_popup(row) for row in rows]

    async def get_categories(self) -> list[dict[str, Any]]:
        """Get all categories with counts."""
        conn = await self.connect()

        cursor = await conn.execute(
            """
            SELECT category, COUNT(*) as count
            FROM popup_stores
            WHERE is_active = 1
            GROUP BY category
            ORDER BY count DESC
            """
        )
        rows = await cursor.fetchall()

        return [{"category": row["category"], "count": row["count"]} for row in rows]

    # Instagram Post Operations

    async def get_existing_post_ids(self) -> set[str]:
        """Get set of already processed post IDs."""
        conn = await self.connect()

        cursor = await conn.execute(
            "SELECT shortcode FROM instagram_posts WHERE is_processed = 1"
        )
        rows = await cursor.fetchall()

        return {row["shortcode"] for row in rows}

    async def mark_post_processed(self, shortcode: str):
        """Mark a post as processed."""
        conn = await self.connect()

        await conn.execute(
            """
            INSERT INTO instagram_posts (shortcode, is_processed, processed_at)
            VALUES (?, 1, ?)
            ON CONFLICT(shortcode) DO UPDATE SET
                is_processed = 1,
                processed_at = ?
            """,
            (shortcode, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()),
        )
        await conn.commit()

    # Scrape Log Operations

    async def save_scrape_log(self, log: ScrapeLog) -> int:
        """Save a scrape log entry."""
        conn = await self.connect()

        cursor = await conn.execute(
            """
            INSERT INTO scrape_logs (
                started_at, completed_at, posts_fetched, posts_parsed,
                popups_created, popups_updated, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                log.started_at.isoformat(),
                log.completed_at.isoformat() if log.completed_at else None,
                log.posts_fetched,
                log.posts_parsed,
                log.popups_created,
                log.popups_updated,
                log.status,
                log.error_message,
            ),
        )
        await conn.commit()

        return cursor.lastrowid

    async def get_recent_scrape_logs(self, limit: int = 10) -> list[ScrapeLog]:
        """Get recent scrape logs."""
        conn = await self.connect()

        cursor = await conn.execute(
            "SELECT * FROM scrape_logs ORDER BY started_at DESC LIMIT ?",
            (limit,),
        )
        rows = await cursor.fetchall()

        return [
            ScrapeLog(
                id=row["id"],
                started_at=datetime.fromisoformat(row["started_at"]),
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                posts_fetched=row["posts_fetched"],
                posts_parsed=row["posts_parsed"],
                popups_created=row["popups_created"],
                popups_updated=row["popups_updated"],
                status=row["status"],
                error_message=row["error_message"],
            )
            for row in rows
        ]

    # Helper Methods

    def _row_to_popup(self, row: aiosqlite.Row) -> PopupStore:
        """Convert database row to PopupStore."""
        coordinates = None
        if row["longitude"] and row["latitude"]:
            coordinates = (row["longitude"], row["latitude"])

        try:
            category = PopupCategory(row["category"])
        except ValueError:
            category = PopupCategory.OTHER

        return PopupStore(
            id=row["id"],
            name=row["name"],
            name_korean=row["name_korean"],
            brand=row["brand"],
            category=category,
            tags=json.loads(row["tags"]) if row["tags"] else [],
            location=row["location"],
            address=row["address"],
            coordinates=coordinates,
            period_start=date.fromisoformat(row["period_start"]) if row["period_start"] else None,
            period_end=date.fromisoformat(row["period_end"]) if row["period_end"] else None,
            operating_hours=row["operating_hours"],
            description=row["description"],
            description_ja=row["description_ja"],
            description_en=row["description_en"],
            images=json.loads(row["images"]) if row["images"] else [],
            thumbnail_url=row["thumbnail_url"],
            source_post_url=row["source_post_url"],
            source_post_id=row["source_post_id"],
            embedding_id=row["embedding_id"],
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )


# Global instance
_popup_db: PopupStoreDB | None = None


async def get_popup_db() -> PopupStoreDB:
    """Get global popup database instance."""
    global _popup_db
    if _popup_db is None:
        _popup_db = PopupStoreDB()
        await _popup_db.connect()
    return _popup_db
