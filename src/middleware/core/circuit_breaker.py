"""
Circuit Breaker Pattern Implementation.
Prevents cascade failures by failing fast when a service is unhealthy.
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, TypeVar

from src.config.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Exception raised when circuit is open."""

    def __init__(self, message: str, state: CircuitState, retry_after: float):
        super().__init__(message)
        self.state = state
        self.retry_after = retry_after


class CircuitBreaker:
    """
    Circuit breaker for protecting external service calls.

    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Service is failing, requests fail immediately
    - HALF_OPEN: Testing if service recovered
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2,
        excluded_exceptions: tuple = (),
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Circuit breaker identifier
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
            half_open_max_calls: Max calls during half-open state
            success_threshold: Successes needed to close circuit
            excluded_exceptions: Exceptions that don't count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        self.excluded_exceptions = excluded_exceptions

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self._state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self._state == CircuitState.OPEN

    async def _should_attempt_recovery(self) -> bool:
        """Check if we should attempt to recover from open state."""
        if self._state != CircuitState.OPEN:
            return False

        if self._last_failure_time is None:
            return True

        elapsed = time.time() - self._last_failure_time
        return elapsed >= self.recovery_timeout

    async def _transition_to(self, new_state: CircuitState):
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_calls = 0
            self._success_count = 0

        logger.info(
            f"Circuit '{self.name}' transitioned: {old_state.value} -> {new_state.value}"
        )

    async def _record_success(self):
        """Record a successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1

                if self._success_count >= self.success_threshold:
                    await self._transition_to(CircuitState.CLOSED)
                    self._failure_count = 0

            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                self._failure_count = 0

    async def _record_failure(self, error: Exception):
        """Record a failed call."""
        # Don't count excluded exceptions
        if isinstance(error, self.excluded_exceptions):
            return

        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)

            elif self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open returns to open
                await self._transition_to(CircuitState.OPEN)

    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: If circuit is open
        """
        async with self._lock:
            # Check if we should attempt recovery
            if await self._should_attempt_recovery():
                await self._transition_to(CircuitState.HALF_OPEN)

            # Fail fast if circuit is open
            if self._state == CircuitState.OPEN:
                retry_after = self.recovery_timeout
                if self._last_failure_time:
                    elapsed = time.time() - self._last_failure_time
                    retry_after = max(0, self.recovery_timeout - elapsed)

                raise CircuitBreakerError(
                    f"Circuit '{self.name}' is open. Service unavailable.",
                    state=self._state,
                    retry_after=retry_after,
                )

            # Limit calls in half-open state
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise CircuitBreakerError(
                        f"Circuit '{self.name}' is half-open. Max test calls reached.",
                        state=self._state,
                        retry_after=1.0,
                    )
                self._half_open_calls += 1

        # Execute the call
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            await self._record_success()
            return result

        except Exception as e:
            await self._record_failure(e)
            raise

    def __call__(self, func: Callable) -> Callable:
        """
        Decorator to protect a function with circuit breaker.

        Usage:
            @circuit_breaker
            async def call_external_api():
                ...
        """
        async def wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)

        return wrapper

    async def reset(self):
        """Manually reset the circuit breaker."""
        async with self._lock:
            await self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None

        logger.info(f"Circuit '{self.name}' manually reset")

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
        }


class CircuitBreakerRegistry:
    """
    Registry for managing multiple circuit breakers.
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}

    def get_or_create(
        self,
        name: str,
        **kwargs,
    ) -> CircuitBreaker:
        """
        Get or create a circuit breaker.

        Args:
            name: Circuit breaker name
            **kwargs: CircuitBreaker constructor arguments

        Returns:
            CircuitBreaker instance
        """
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(name=name, **kwargs)

        return self._breakers[name]

    def get(self, name: str) -> CircuitBreaker | None:
        """Get a circuit breaker by name."""
        return self._breakers.get(name)

    def get_all_stats(self) -> dict[str, dict[str, Any]]:
        """Get stats for all circuit breakers."""
        return {name: cb.get_stats() for name, cb in self._breakers.items()}

    async def reset_all(self):
        """Reset all circuit breakers."""
        for cb in self._breakers.values():
            await cb.reset()


# Global registry
_registry = CircuitBreakerRegistry()


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    """Get or create a circuit breaker from the global registry."""
    return _registry.get_or_create(name, **kwargs)


def get_circuit_breaker_registry() -> CircuitBreakerRegistry:
    """Get the global circuit breaker registry."""
    return _registry


# Pre-defined circuit breakers for common services
naver_api_breaker = get_circuit_breaker(
    "naver_api",
    failure_threshold=5,
    recovery_timeout=30.0,
)

llm_breaker = get_circuit_breaker(
    "llm",
    failure_threshold=3,
    recovery_timeout=60.0,
)

qdrant_breaker = get_circuit_breaker(
    "qdrant",
    failure_threshold=5,
    recovery_timeout=30.0,
)
