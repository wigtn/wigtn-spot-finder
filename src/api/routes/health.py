"""
Health check endpoints.
Provides /health and /ready endpoints for container orchestration.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Response, status

from src.config.settings import settings
from src.db.postgres.connection import check_db_health

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Basic health check endpoint.
    Returns 200 if the service is running.
    Used for liveness probes in Kubernetes.
    """
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready")
async def readiness_check(response: Response):
    """
    Readiness check endpoint.
    Checks if all required services are available.
    Used for readiness probes in Kubernetes.
    """
    checks = {
        "database": False,
        "redis": False,
        "vllm": False,
    }

    # Check database
    try:
        checks["database"] = await check_db_health()
    except Exception as e:
        logger.warning(f"Database health check failed: {e}")
        checks["database"] = False

    # Check Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        checks["redis"] = True
        await r.close()
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        checks["redis"] = False

    # Check vLLM
    try:
        import httpx

        async with httpx.AsyncClient() as client:
            vllm_health_url = f"{settings.vllm_base_url.replace('/v1', '')}/health"
            resp = await client.get(vllm_health_url, timeout=5.0)
            checks["vllm"] = resp.status_code == 200
    except Exception as e:
        logger.warning(f"vLLM health check failed: {e}")
        checks["vllm"] = False

    # Determine overall status
    # Service is ready if at least database is available
    # vLLM can be unavailable during warm-up
    is_ready = checks["database"]

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics")
async def prometheus_metrics():
    """
    Prometheus metrics endpoint.
    Returns metrics in Prometheus text format.
    """
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
