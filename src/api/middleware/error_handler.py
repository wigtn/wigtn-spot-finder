"""
Global Error Handler Middleware for FastAPI.
Provides consistent error responses and logging.
"""

import logging
import traceback
from typing import Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.middleware.core.rate_limiter import RateLimitExceeded
from src.middleware.core.circuit_breaker import CircuitBreakerError
from src.middleware.core.input_validation import PromptInjectionError

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standard error response format."""

    @staticmethod
    def create(
        status_code: int,
        error_code: str,
        message: str,
        details: dict | None = None,
        retry_after: int | None = None,
    ) -> JSONResponse:
        """
        Create a standardized error response.

        Args:
            status_code: HTTP status code
            error_code: Application error code
            message: Human-readable message
            details: Additional error details
            retry_after: Retry-After header value

        Returns:
            JSONResponse
        """
        content = {
            "error": {
                "code": error_code,
                "message": message,
            }
        }

        if details:
            content["error"]["details"] = details

        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        return JSONResponse(
            status_code=status_code,
            content=content,
            headers=headers,
        )


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling exceptions globally.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and handle any exceptions."""
        try:
            return await call_next(request)

        except RateLimitExceeded as e:
            logger.warning(f"Rate limit exceeded: {request.client.host}")
            return ErrorResponse.create(
                status_code=429,
                error_code="RATE_LIMIT_EXCEEDED",
                message=str(e),
                retry_after=e.retry_after,
            )

        except CircuitBreakerError as e:
            logger.warning(f"Circuit breaker open: {e}")
            return ErrorResponse.create(
                status_code=503,
                error_code="SERVICE_UNAVAILABLE",
                message="Service temporarily unavailable. Please try again later.",
                details={"circuit": e.state.value},
                retry_after=int(e.retry_after),
            )

        except PromptInjectionError as e:
            logger.warning(f"Prompt injection detected from {request.client.host}")
            return ErrorResponse.create(
                status_code=400,
                error_code="INVALID_INPUT",
                message="Invalid input detected. Please rephrase your message.",
            )

        except ValueError as e:
            logger.warning(f"Validation error: {e}")
            return ErrorResponse.create(
                status_code=400,
                error_code="VALIDATION_ERROR",
                message=str(e),
            )

        except Exception as e:
            # Log full traceback for unexpected errors
            logger.error(f"Unhandled exception: {e}\n{traceback.format_exc()}")

            # Don't expose internal errors to clients
            return ErrorResponse.create(
                status_code=500,
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred. Please try again.",
            )


def setup_error_handlers(app: FastAPI):
    """
    Set up exception handlers for the FastAPI app.

    Args:
        app: FastAPI application instance
    """

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return ErrorResponse.create(
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            message=str(exc),
            retry_after=exc.retry_after,
        )

    @app.exception_handler(CircuitBreakerError)
    async def circuit_breaker_handler(request: Request, exc: CircuitBreakerError):
        return ErrorResponse.create(
            status_code=503,
            error_code="SERVICE_UNAVAILABLE",
            message="Service temporarily unavailable.",
            retry_after=int(exc.retry_after),
        )

    @app.exception_handler(PromptInjectionError)
    async def prompt_injection_handler(request: Request, exc: PromptInjectionError):
        return ErrorResponse.create(
            status_code=400,
            error_code="INVALID_INPUT",
            message="Invalid input detected.",
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}\n{traceback.format_exc()}")
        return ErrorResponse.create(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred.",
        )

    logger.info("Error handlers configured")
