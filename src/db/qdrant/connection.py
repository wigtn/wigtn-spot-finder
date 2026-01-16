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
MEMORY_VECTOR_SIZE = 1536  # OpenAI embedding size (also works with many others)


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
                    size=MEMORY_VECTOR_SIZE,
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

        # Get collection info
        collection_info = None
        for col in collections.collections:
            if col.name == MEMORY_COLLECTION:
                collection_info = client.get_collection(MEMORY_COLLECTION)
                break

        return {
            "status": "healthy",
            "collections": len(collections.collections),
            "memory_collection": {
                "name": MEMORY_COLLECTION,
                "points_count": collection_info.points_count if collection_info else 0,
                "vectors_count": collection_info.vectors_count if collection_info else 0,
            } if collection_info else None,
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
