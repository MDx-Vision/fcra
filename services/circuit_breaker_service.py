"""
Circuit Breaker Service for External API Calls

Implements the circuit breaker pattern to prevent cascade failures
when external services are unavailable or experiencing issues.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Service is failing, requests fail fast without calling the service
- HALF-OPEN: Testing if service has recovered

Usage:
    from services.circuit_breaker_service import (
        get_circuit_breaker,
        circuit_protected,
        CircuitBreakerError
    )

    # Using decorator
    @circuit_protected("stripe")
    def create_payment():
        return stripe.Charge.create(...)

    # Using context manager
    breaker = get_circuit_breaker("twilio")
    with breaker:
        send_sms(...)

    # Check status
    status = get_all_circuit_status()
"""

import functools
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

logger = logging.getLogger("circuit_breaker")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerError(Exception):
    """Raised when circuit is open and call is rejected."""

    def __init__(self, service_name: str, message: str = None):
        self.service_name = service_name
        self.message = message or f"Circuit breaker open for service: {service_name}"
        super().__init__(self.message)


@dataclass
class CircuitBreakerConfig:
    """Configuration for a circuit breaker."""

    failure_threshold: int = 5  # Failures before opening
    success_threshold: int = 2  # Successes in half-open before closing
    timeout: float = 30.0  # Seconds before trying half-open
    excluded_exceptions: Tuple[
        Type[Exception], ...
    ] = ()  # Don't count these as failures


@dataclass
class CircuitBreakerStats:
    """Statistics for a circuit breaker."""

    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: List[Dict[str, Any]] = field(default_factory=list)
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.

    The circuit breaker monitors calls to external services and
    opens (stops allowing calls) when failures exceed a threshold.
    After a timeout, it enters half-open state to test if the
    service has recovered.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 30.0,
        excluded_exceptions: Tuple[Type[Exception], ...] = (),
        fallback: Optional[Callable] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Name of the service (for logging)
            failure_threshold: Number of failures before opening circuit
            success_threshold: Successes in half-open before closing
            timeout: Seconds to wait before trying half-open
            excluded_exceptions: Exceptions that don't count as failures
            fallback: Optional fallback function when circuit is open
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.excluded_exceptions = excluded_exceptions
        self.fallback = fallback

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.RLock()

        self.stats = CircuitBreakerStats()

        logger.info(
            f"Circuit breaker '{name}' initialized: "
            f"failure_threshold={failure_threshold}, "
            f"timeout={timeout}s"
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if we should transition to half-open
                if self._should_attempt_reset():
                    self._transition_to(CircuitState.HALF_OPEN)
            return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return True
        return time.time() - self._last_failure_time >= self.timeout

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to a new state."""
        old_state = self._state
        self._state = new_state

        if new_state == CircuitState.CLOSED:
            self._failure_count = 0
            self._success_count = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._success_count = 0

        # Log state change
        change = {
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.stats.state_changes.append(change)

        # Keep only last 100 state changes
        if len(self.stats.state_changes) > 100:
            self.stats.state_changes = self.stats.state_changes[-100:]

        logger.warning(
            f"Circuit breaker '{self.name}' state change: "
            f"{old_state.value} -> {new_state.value}"
        )

    def _record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            self.stats.total_calls += 1
            self.stats.successful_calls += 1
            self.stats.last_success_time = datetime.utcnow()
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0

            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
                    logger.info(
                        f"Circuit breaker '{self.name}' closed after "
                        f"{self._success_count} successful calls"
                    )

    def _record_failure(self, exception: Exception) -> None:
        """Record a failed call."""
        with self._lock:
            # Check if this exception should be excluded
            if isinstance(exception, self.excluded_exceptions):
                logger.debug(
                    f"Circuit breaker '{self.name}' ignoring excluded exception: "
                    f"{type(exception).__name__}"
                )
                return

            self.stats.total_calls += 1
            self.stats.failed_calls += 1
            self.stats.last_failure_time = datetime.utcnow()
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0

            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open goes back to open
                self._transition_to(CircuitState.OPEN)
                logger.warning(
                    f"Circuit breaker '{self.name}' reopened after failure in half-open"
                )
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
                    logger.error(
                        f"Circuit breaker '{self.name}' opened after "
                        f"{self._failure_count} failures"
                    )

    def _record_rejection(self) -> None:
        """Record a rejected call (circuit open)."""
        with self._lock:
            self.stats.total_calls += 1
            self.stats.rejected_calls += 1

    def allow_request(self) -> bool:
        """Check if a request should be allowed."""
        state = self.state  # This may trigger half-open transition
        return state != CircuitState.OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to call
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result of func if successful

        Raises:
            CircuitBreakerError: If circuit is open
            Exception: Any exception from func (also recorded as failure)
        """
        if not self.allow_request():
            self._record_rejection()

            # Try fallback if available
            if self.fallback:
                logger.info(f"Circuit breaker '{self.name}' using fallback")
                return self.fallback(*args, **kwargs)

            raise CircuitBreakerError(self.name)

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure(e)
            raise

    def __enter__(self):
        """Context manager entry."""
        if not self.allow_request():
            self._record_rejection()
            raise CircuitBreakerError(self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self._record_success()
        elif exc_val is not None:
            self._record_failure(exc_val)
        return False  # Don't suppress exceptions

    def reset(self) -> None:
        """Manually reset the circuit breaker to closed state."""
        with self._lock:
            self._transition_to(CircuitState.CLOSED)
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            logger.info(f"Circuit breaker '{self.name}' manually reset")

    def get_status(self) -> Dict[str, Any]:
        """Get current status and statistics."""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self._failure_count,
                "failure_threshold": self.failure_threshold,
                "success_count": self._success_count,
                "success_threshold": self.success_threshold,
                "timeout": self.timeout,
                "stats": {
                    "total_calls": self.stats.total_calls,
                    "successful_calls": self.stats.successful_calls,
                    "failed_calls": self.stats.failed_calls,
                    "rejected_calls": self.stats.rejected_calls,
                    "consecutive_failures": self.stats.consecutive_failures,
                    "consecutive_successes": self.stats.consecutive_successes,
                    "last_failure_time": (
                        self.stats.last_failure_time.isoformat()
                        if self.stats.last_failure_time
                        else None
                    ),
                    "last_success_time": (
                        self.stats.last_success_time.isoformat()
                        if self.stats.last_success_time
                        else None
                    ),
                    "recent_state_changes": self.stats.state_changes[-10:],
                },
            }


# Global registry of circuit breakers
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_registry_lock = threading.Lock()

# Default configurations for known services
DEFAULT_CONFIGS: Dict[str, CircuitBreakerConfig] = {
    "stripe": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout=30.0,
    ),
    "twilio": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout=30.0,
    ),
    "email": CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=60.0,  # Email servers may take longer to recover
    ),
    "usps": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0,
    ),
    "claude_ai": CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=1,
        timeout=30.0,
    ),
    "sendcertified": CircuitBreakerConfig(
        failure_threshold=5,
        success_threshold=2,
        timeout=60.0,
    ),
    "credit_import": CircuitBreakerConfig(
        failure_threshold=3,
        success_threshold=1,
        timeout=120.0,  # Credit imports are slow
    ),
}


def get_circuit_breaker(
    name: str,
    failure_threshold: Optional[int] = None,
    success_threshold: Optional[int] = None,
    timeout: Optional[float] = None,
    fallback: Optional[Callable] = None,
) -> CircuitBreaker:
    """
    Get or create a circuit breaker for a service.

    Args:
        name: Service name
        failure_threshold: Override default failure threshold
        success_threshold: Override default success threshold
        timeout: Override default timeout
        fallback: Optional fallback function

    Returns:
        CircuitBreaker instance (same instance for same name)
    """
    with _registry_lock:
        if name not in _circuit_breakers:
            # Get default config or use defaults
            config = DEFAULT_CONFIGS.get(name, CircuitBreakerConfig())

            _circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold or config.failure_threshold,
                success_threshold=success_threshold or config.success_threshold,
                timeout=timeout or config.timeout,
                excluded_exceptions=config.excluded_exceptions,
                fallback=fallback,
            )

        return _circuit_breakers[name]


def circuit_protected(
    service_name: str,
    failure_threshold: Optional[int] = None,
    success_threshold: Optional[int] = None,
    timeout: Optional[float] = None,
    fallback: Optional[Callable] = None,
):
    """
    Decorator to protect a function with a circuit breaker.

    Args:
        service_name: Name of the service for circuit breaker
        failure_threshold: Override default failure threshold
        success_threshold: Override default success threshold
        timeout: Override default timeout
        fallback: Optional fallback function

    Example:
        @circuit_protected("stripe")
        def create_charge(amount):
            return stripe.Charge.create(amount=amount)

        @circuit_protected("email", fallback=lambda *args: {"queued": True})
        def send_email(to, subject, body):
            return smtp.send(to, subject, body)
    """

    def decorator(func: Callable) -> Callable:
        breaker = get_circuit_breaker(
            service_name,
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout=timeout,
            fallback=fallback,
        )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        # Attach breaker for inspection
        wrapper._circuit_breaker = breaker
        return wrapper

    return decorator


def get_all_circuit_status() -> Dict[str, Dict[str, Any]]:
    """Get status of all registered circuit breakers."""
    with _registry_lock:
        return {
            name: breaker.get_status() for name, breaker in _circuit_breakers.items()
        }


def reset_circuit(name: str) -> bool:
    """
    Reset a circuit breaker to closed state.

    Args:
        name: Service name

    Returns:
        True if circuit was found and reset, False otherwise
    """
    with _registry_lock:
        if name in _circuit_breakers:
            _circuit_breakers[name].reset()
            return True
        return False


def reset_all_circuits() -> int:
    """
    Reset all circuit breakers to closed state.

    Returns:
        Number of circuits reset
    """
    with _registry_lock:
        count = 0
        for breaker in _circuit_breakers.values():
            breaker.reset()
            count += 1
        return count


def get_open_circuits() -> List[str]:
    """Get list of currently open circuit breakers."""
    with _registry_lock:
        return [name for name, breaker in _circuit_breakers.items() if breaker.is_open]


def get_circuit_health_summary() -> Dict[str, Any]:
    """
    Get a health summary of all circuits.

    Returns:
        Dict with summary statistics
    """
    with _registry_lock:
        total = len(_circuit_breakers)
        open_circuits = []
        half_open_circuits = []
        closed_circuits = []

        total_calls = 0
        total_failures = 0
        total_rejections = 0

        for name, breaker in _circuit_breakers.items():
            status = breaker.get_status()
            state = status["state"]

            if state == "open":
                open_circuits.append(name)
            elif state == "half_open":
                half_open_circuits.append(name)
            else:
                closed_circuits.append(name)

            total_calls += status["stats"]["total_calls"]
            total_failures += status["stats"]["failed_calls"]
            total_rejections += status["stats"]["rejected_calls"]

        return {
            "total_circuits": total,
            "healthy_count": len(closed_circuits),
            "degraded_count": len(half_open_circuits),
            "unhealthy_count": len(open_circuits),
            "open_circuits": open_circuits,
            "half_open_circuits": half_open_circuits,
            "total_calls": total_calls,
            "total_failures": total_failures,
            "total_rejections": total_rejections,
            "failure_rate": (
                round(total_failures / total_calls * 100, 2) if total_calls > 0 else 0
            ),
        }


# Exports
__all__ = [
    # Main class
    "CircuitBreaker",
    "CircuitState",
    "CircuitBreakerError",
    "CircuitBreakerConfig",
    # Factory functions
    "get_circuit_breaker",
    "circuit_protected",
    # Status functions
    "get_all_circuit_status",
    "get_open_circuits",
    "get_circuit_health_summary",
    # Control functions
    "reset_circuit",
    "reset_all_circuits",
    # Constants
    "DEFAULT_CONFIGS",
]
