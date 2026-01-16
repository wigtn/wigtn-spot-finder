"""
Distributed Lock using Redis.
Prevents race conditions in concurrent conversation processing.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as aioredis

from src.config.settings import settings

logger = logging.getLogger(__name__)


class LockAcquisitionError(Exception):
    """Raised when lock cannot be acquired."""
    pass


class LockReleaseError(Exception):
    """Raised when lock release fails."""
    pass


class DistributedLock:
    """
    Redis-based distributed lock implementation.
    Uses SET NX with automatic expiration for safety.
    """

    def __init__(
        self,
        redis_url: str | None = None,
        default_ttl: int = 30,
        retry_interval: float = 0.1,
        max_retries: int = 50,
    ):
        """
        Initialize the distributed lock.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default lock TTL in seconds
            retry_interval: Time between retry attempts in seconds
            max_retries: Maximum number of acquisition attempts
        """
        self.redis_url = redis_url or settings.redis_url
        self.default_ttl = default_ttl
        self.retry_interval = retry_interval
        self.max_retries = max_retries

        self._redis: aioredis.Redis | None = None
        self._lock_prefix = "lock:"

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
            )
        return self._redis

    def _get_lock_key(self, resource: str) -> str:
        """Generate lock key for a resource."""
        return f"{self._lock_prefix}{resource}"

    def _generate_token(self) -> str:
        """Generate unique token for lock ownership."""
        import uuid
        return f"{uuid.uuid4().hex}:{time.time()}"

    async def acquire(
        self,
        resource: str,
        ttl: int | None = None,
        blocking: bool = True,
        timeout: float | None = None,
    ) -> str | None:
        """
        Acquire a lock on a resource.

        Args:
            resource: Resource identifier to lock
            ttl: Lock TTL in seconds (uses default if not specified)
            blocking: Whether to wait for lock acquisition
            timeout: Maximum time to wait (None = use max_retries)

        Returns:
            Lock token if acquired, None if not blocking and lock unavailable

        Raises:
            LockAcquisitionError: If blocking and lock cannot be acquired
        """
        redis = await self._get_redis()
        lock_key = self._get_lock_key(resource)
        token = self._generate_token()
        lock_ttl = ttl or self.default_ttl

        start_time = time.time()
        attempts = 0

        while True:
            # Try to acquire lock using SET NX EX
            acquired = await redis.set(
                lock_key,
                token,
                nx=True,
                ex=lock_ttl,
            )

            if acquired:
                logger.debug(f"Lock acquired: {resource} (token: {token[:8]}...)")
                return token

            if not blocking:
                return None

            attempts += 1

            # Check timeout
            if timeout is not None:
                if time.time() - start_time >= timeout:
                    raise LockAcquisitionError(
                        f"Timeout acquiring lock for {resource} after {timeout}s"
                    )
            elif attempts >= self.max_retries:
                raise LockAcquisitionError(
                    f"Max retries ({self.max_retries}) exceeded for lock {resource}"
                )

            # Wait before retry
            await asyncio.sleep(self.retry_interval)

    async def release(self, resource: str, token: str) -> bool:
        """
        Release a lock.

        Args:
            resource: Resource identifier
            token: Lock token from acquire()

        Returns:
            True if released, False if lock was not held

        Raises:
            LockReleaseError: If release fails unexpectedly
        """
        redis = await self._get_redis()
        lock_key = self._get_lock_key(resource)

        # Lua script for atomic check-and-delete
        # Only delete if the token matches (we own the lock)
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """

        try:
            result = await redis.eval(lua_script, 1, lock_key, token)

            if result == 1:
                logger.debug(f"Lock released: {resource}")
                return True
            else:
                logger.warning(
                    f"Lock release failed - not owned: {resource} "
                    f"(token: {token[:8]}...)"
                )
                return False

        except Exception as e:
            raise LockReleaseError(f"Failed to release lock {resource}: {e}")

    async def extend(
        self,
        resource: str,
        token: str,
        additional_ttl: int | None = None,
    ) -> bool:
        """
        Extend lock TTL.

        Args:
            resource: Resource identifier
            token: Lock token from acquire()
            additional_ttl: Additional TTL in seconds

        Returns:
            True if extended, False if lock was not held
        """
        redis = await self._get_redis()
        lock_key = self._get_lock_key(resource)
        extend_ttl = additional_ttl or self.default_ttl

        # Lua script for atomic check-and-extend
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
        """

        result = await redis.eval(lua_script, 1, lock_key, token, extend_ttl)

        if result == 1:
            logger.debug(f"Lock extended: {resource} (+{extend_ttl}s)")
            return True
        else:
            logger.warning(f"Lock extend failed - not owned: {resource}")
            return False

    async def is_locked(self, resource: str) -> bool:
        """
        Check if a resource is currently locked.

        Args:
            resource: Resource identifier

        Returns:
            True if locked, False otherwise
        """
        redis = await self._get_redis()
        lock_key = self._get_lock_key(resource)

        return await redis.exists(lock_key) == 1

    async def get_lock_info(self, resource: str) -> dict | None:
        """
        Get information about a lock.

        Args:
            resource: Resource identifier

        Returns:
            Dict with lock info or None if not locked
        """
        redis = await self._get_redis()
        lock_key = self._get_lock_key(resource)

        token = await redis.get(lock_key)
        if not token:
            return None

        ttl = await redis.ttl(lock_key)

        return {
            "resource": resource,
            "token": token,
            "ttl_remaining": ttl,
        }

    @asynccontextmanager
    async def lock(
        self,
        resource: str,
        ttl: int | None = None,
        timeout: float | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Context manager for lock acquisition and release.

        Usage:
            async with distributed_lock.lock("thread:123") as token:
                # Critical section
                await process_conversation()

        Args:
            resource: Resource identifier
            ttl: Lock TTL in seconds
            timeout: Maximum time to wait for lock

        Yields:
            Lock token
        """
        token = await self.acquire(resource, ttl=ttl, blocking=True, timeout=timeout)

        try:
            yield token
        finally:
            await self.release(resource, token)

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


class ConversationLock:
    """
    Specialized lock for conversation processing.
    Ensures only one request processes a thread at a time.
    """

    def __init__(self, distributed_lock: DistributedLock | None = None):
        """
        Initialize conversation lock.

        Args:
            distributed_lock: Optional DistributedLock instance
        """
        self._lock = distributed_lock or DistributedLock()

    def _get_resource_key(self, thread_id: str) -> str:
        """Generate resource key for a thread."""
        return f"conversation:{thread_id}"

    @asynccontextmanager
    async def acquire_for_thread(
        self,
        thread_id: str,
        ttl: int = 60,
        timeout: float = 10.0,
    ) -> AsyncGenerator[str, None]:
        """
        Acquire lock for processing a conversation thread.

        Args:
            thread_id: Conversation thread ID
            ttl: Lock TTL in seconds
            timeout: Maximum wait time

        Yields:
            Lock token

        Raises:
            LockAcquisitionError: If lock cannot be acquired
        """
        resource = self._get_resource_key(thread_id)

        async with self._lock.lock(resource, ttl=ttl, timeout=timeout) as token:
            logger.debug(f"Processing lock acquired for thread {thread_id}")
            yield token

    async def is_thread_locked(self, thread_id: str) -> bool:
        """
        Check if a thread is currently being processed.

        Args:
            thread_id: Conversation thread ID

        Returns:
            True if locked
        """
        resource = self._get_resource_key(thread_id)
        return await self._lock.is_locked(resource)


# Global instances
_distributed_lock: DistributedLock | None = None
_conversation_lock: ConversationLock | None = None


def get_distributed_lock() -> DistributedLock:
    """Get global distributed lock instance."""
    global _distributed_lock
    if _distributed_lock is None:
        _distributed_lock = DistributedLock()
    return _distributed_lock


def get_conversation_lock() -> ConversationLock:
    """Get global conversation lock instance."""
    global _conversation_lock
    if _conversation_lock is None:
        _conversation_lock = ConversationLock(get_distributed_lock())
    return _conversation_lock
