"""
Qdrant Vector Database connection management.
"""

import logging
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse

from src.config.settings import settings

logger = logging.getLogger(__name__)

# Global client instance
_qdrant_client: QdrantClient | None = None

# Collection configuration
MEMORY_COLLECTION = "travel_memories"
POPUP_COLLECTION = "seongsu_popups"


def get_vector_size() -> int:
    """Get vector size from settings (Upstage embedding dimension)."""
    return settings.upstage_embedding_dimension


def get_qdrant_client() -> QdrantClient:
    """
    Get or create Qdrant client instance.

    Returns:
        QdrantClient instance
    """
    global _qdrant_client

    if _qdrant_client is None:
        _qdrant_client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key if settings.qdrant_api_key else None,
            timeout=30,
        )
        logger.info(f"Connected to Qdrant at {settings.qdrant_url}")

    return _qdrant_client


async def init_collections():
    """
    Initialize required Qdrant collections.
    Creates collections if they don't exist.
    """
    client = get_qdrant_client()

    try:
        # Check if collection exists
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        if MEMORY_COLLECTION not in collection_names:
            # Create memory collection
            client.create_collection(
                collection_name=MEMORY_COLLECTION,
                vectors_config=models.VectorParams(
                    size=get_vector_size(),
                    distance=models.Distance.COSINE,
                ),
                # Optimized for filtering by user/thread
                hnsw_config=models.HnswConfigDiff(
                    payload_m=16,
                    m=16,
                    ef_construct=100,
                ),
            )

            # Create payload indexes for efficient filtering
            client.create_payload_index(
                collection_name=MEMORY_COLLECTION,
                field_name="user_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            client.create_payload_index(
                collection_name=MEMORY_COLLECTION,
                field_name="thread_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            client.create_payload_index(
                collection_name=MEMORY_COLLECTION,
                field_name="memory_type",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            client.create_payload_index(
                collection_name=MEMORY_COLLECTION,
                field_name="created_at",
                field_schema=models.PayloadSchemaType.DATETIME,
            )

            logger.info(f"Created collection: {MEMORY_COLLECTION}")
        else:
            logger.info(f"Collection already exists: {MEMORY_COLLECTION}")

        # Create popup collection for Seongsu popup stores
        if POPUP_COLLECTION not in collection_names:
            client.create_collection(
                collection_name=POPUP_COLLECTION,
                vectors_config=models.VectorParams(
                    size=get_vector_size(),
                    distance=models.Distance.COSINE,
                ),
                hnsw_config=models.HnswConfigDiff(
                    payload_m=16,
                    m=16,
                    ef_construct=100,
                ),
            )

            # Create payload indexes for popup filtering
            client.create_payload_index(
                collection_name=POPUP_COLLECTION,
                field_name="popup_id",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            client.create_payload_index(
                collection_name=POPUP_COLLECTION,
                field_name="category",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

            client.create_payload_index(
                collection_name=POPUP_COLLECTION,
                field_name="is_active",
                field_schema=models.PayloadSchemaType.BOOL,
            )

            client.create_payload_index(
                collection_name=POPUP_COLLECTION,
                field_name="period_start",
                field_schema=models.PayloadSchemaType.DATETIME,
            )

            client.create_payload_index(
                collection_name=POPUP_COLLECTION,
                field_name="period_end",
                field_schema=models.PayloadSchemaType.DATETIME,
            )

            logger.info(f"Created collection: {POPUP_COLLECTION}")
        else:
            logger.info(f"Collection already exists: {POPUP_COLLECTION}")

    except UnexpectedResponse as e:
        logger.error(f"Failed to initialize Qdrant collections: {e}")
        raise


async def check_qdrant_health() -> dict[str, Any]:
    """
    Check Qdrant health status.

    Returns:
        Health status dict
    """
    try:
        client = get_qdrant_client()
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]

        # Get memory collection info
        memory_info = None
        if MEMORY_COLLECTION in collection_names:
            col = client.get_collection(MEMORY_COLLECTION)
            memory_info = {
                "name": MEMORY_COLLECTION,
                "points_count": col.points_count,
                "vectors_count": col.vectors_count,
            }

        # Get popup collection info
        popup_info = None
        if POPUP_COLLECTION in collection_names:
            col = client.get_collection(POPUP_COLLECTION)
            popup_info = {
                "name": POPUP_COLLECTION,
                "points_count": col.points_count,
                "vectors_count": col.vectors_count,
            }

        return {
            "status": "healthy",
            "collections": len(collections.collections),
            "memory_collection": memory_info,
            "popup_collection": popup_info,
        }

    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


def close_qdrant_client():
    """Close Qdrant client connection."""
    global _qdrant_client

    if _qdrant_client is not None:
        _qdrant_client.close()
        _qdrant_client = None
        logger.info("Qdrant client closed")
