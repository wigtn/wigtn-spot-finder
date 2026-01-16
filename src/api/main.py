"""
FastAPI application entry point.
Main API server for spotfinder-agent-for-foreigner.
"""

import logging
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from src.api.routes import chat, health
from src.api.middleware.error_handler import ErrorHandlerMiddleware, setup_error_handlers
from src.config.settings import settings
from src.db.postgres.connection import init_db, close_db
from src.db.qdrant.connection import init_collections as init_qdrant

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def init_sentry() -> None:
    """Initialize Sentry for error tracking and performance monitoring."""
    if not settings.sentry_dsn:
        logger.warning("Sentry DSN not configured, skipping Sentry initialization")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=f"{settings.app_name}@{settings.app_version}",
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
            LoggingIntegration(level=logging.WARNING, event_level=logging.ERROR),
        ],
        send_default_pii=False,
    )
    logger.info(f"Sentry initialized for environment: {settings.sentry_environment}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize Sentry
    init_sentry()

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        # Continue anyway - database might not be required for all endpoints

    # Initialize Qdrant vector database
    try:
        await init_qdrant()
        logger.info("Qdrant initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI Agent that helps foreigners find travel hotspots and build travel schedules in Korea",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add error handler middleware
app.add_middleware(ErrorHandlerMiddleware)

# Setup exception handlers
setup_error_handlers(app)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])


@app.get("/")
async def root():
    """Root endpoint - basic API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "Travel assistant for foreigners visiting Korea",
        "docs": "/docs" if settings.debug else "Disabled in production",
    }


def main():
    """Run the application using uvicorn."""
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.debug,
        workers=1 if settings.debug else 4,
    )


if __name__ == "__main__":
    main()
