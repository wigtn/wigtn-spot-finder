"""
Rate Limiter Middleware.
Implements sliding window rate limiting using Redis.
"""

import logging
import time
from typing import Any

import redis.asyncio as aioredis

from src.config.settings import settings

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class RateLimiter:
    """
    Sliding window rate limiter using Redis.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        requests_per_minute: int | None = None,
        requests_per_hour: int | None = None,
        burst_limit: int | None = None,
    ):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL
            requests_per_minute: Max requests per minute per user
            requests_per_hour: Max requests per hour per user
            burst_limit: Max burst requests allowed
        """
        self.redis_url = redis_url or settings.redis_url
        self.requests_per_minute = requests_per_minute or settings.rate_limit_requests_per_minute
        self.requests_per_hour = requests_per_hour or settings.rate_limit_requests_per_hour
        self.burst_limit = burst_limit or (self.requests_per_minute * 2)

        self._redis: aioredis.Redis | None = None
        self._prefix = "ratelimit:"

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
            )
        return self._redis

    def _get_minute_key(self, identifier: str) -> str:
        """Generate minute window key."""
        minute = int(time.time() / 60)
        return f"{self._prefix}minute:{identifier}:{minute}"

    def _get_hour_key(self, identifier: str) -> str:
        """Generate hour window key."""
        hour = int(time.time() / 3600)
        return f"{self._prefix}hour:{identifier}:{hour}"

    async def check_rate_limit(
        self,
        identifier: str,
        increment: bool = True,
    ) -> dict[str, Any]:
        """
        Check if request is within rate limits.

        Args:
            identifier: User/client identifier (user_id, IP, etc.)
            increment: Whether to increment the counter

        Returns:
            Dict with rate limit info

        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        redis = await self._get_redis()

        minute_key = self._get_minute_key(identifier)
        hour_key = self._get_hour_key(identifier)

        # Get current counts
        minute_count = await redis.get(minute_key)
        hour_count = await redis.get(hour_key)

        minute_count = int(minute_count) if minute_count else 0
        hour_count = int(hour_count) if hour_count else 0

        # Check minute limit
        if minute_count >= self.requests_per_minute:
            # Calculate retry after
            current_second = int(time.time()) % 60
            retry_after = 60 - current_second

            logger.warning(
                f"Rate limit exceeded (minute): {identifier}, "
                f"count={minute_count}, limit={self.requests_per_minute}"
            )

            raise RateLimitExceeded(
                f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
                retry_after=retry_after,
            )

        # Check hour limit
        if hour_count >= self.requests_per_hour:
            current_minute = int(time.time() / 60) % 60
            retry_after = (60 - current_minute) * 60

            logger.warning(
                f"Rate limit exceeded (hour): {identifier}, "
                f"count={hour_count}, limit={self.requests_per_hour}"
            )

            raise RateLimitExceeded(
                f"Rate limit exceeded. Maximum {self.requests_per_hour} requests per hour.",
                retry_after=retry_after,
            )

        # Increment counters if requested
        if increment:
            pipe = redis.pipeline()

            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)  # 2 minute expiry for safety

            pipe.incr(hour_key)
            pipe.expire(hour_key, 7200)  # 2 hour expiry for safety

            await pipe.execute()

            minute_count += 1
            hour_count += 1

        return {
            "allowed": True,
            "minute_count": minute_count,
            "minute_limit": self.requests_per_minute,
            "minute_remaining": self.requests_per_minute - minute_count,
            "hour_count": hour_count,
            "hour_limit": self.requests_per_hour,
            "hour_remaining": self.requests_per_hour - hour_count,
        }

    async def get_remaining(self, identifier: str) -> dict[str, int]:
        """
        Get remaining requests for an identifier.

        Args:
            identifier: User/client identifier

        Returns:
            Dict with remaining counts
        """
        redis = await self._get_redis()

        minute_key = self._get_minute_key(identifier)
        hour_key = self._get_hour_key(identifier)

        minute_count = await redis.get(minute_key)
        hour_count = await redis.get(hour_key)

        minute_count = int(minute_count) if minute_count else 0
        hour_count = int(hour_count) if hour_count else 0

        return {
            "minute_remaining": max(0, self.requests_per_minute - minute_count),
            "hour_remaining": max(0, self.requests_per_hour - hour_count),
        }

    async def reset(self, identifier: str) -> bool:
        """
        Reset rate limits for an identifier.

        Args:
            identifier: User/client identifier

        Returns:
            True if reset successful
        """
        redis = await self._get_redis()

        minute_key = self._get_minute_key(identifier)
        hour_key = self._get_hour_key(identifier)

        await redis.delete(minute_key, hour_key)

        logger.info(f"Rate limit reset for: {identifier}")
        return True

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


class UserRateLimiter(RateLimiter):
    """
    Rate limiter specialized for user-based limiting.
    Falls back to IP-based limiting for anonymous users.
    """

    async def check_user_rate_limit(
        self,
        user_id: str | None = None,
        client_ip: str | None = None,
    ) -> dict[str, Any]:
        """
        Check rate limit for a user or IP.

        Args:
            user_id: Optional user ID
            client_ip: Client IP address

        Returns:
            Rate limit info dict

        Raises:
            RateLimitExceeded: If rate limit exceeded
        """
        # Use user_id if available, otherwise fall back to IP
        identifier = f"user:{user_id}" if user_id else f"ip:{client_ip or 'unknown'}"

        return await self.check_rate_limit(identifier)


# Global instance
_rate_limiter: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def get_user_rate_limiter() -> UserRateLimiter:
    """Get user-specialized rate limiter."""
    return UserRateLimiter()
