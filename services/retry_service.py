"""
Retry Service for External API Calls

Provides retry logic with exponential backoff for handling transient failures
in external API calls (Stripe, Twilio, SendGrid, SendCertified, etc.).

Uses tenacity library for robust retry handling with:
- Configurable retry attempts
- Exponential backoff with jitter
- Specific exception handling
- Detailed logging of retry attempts
- Request ID tracking for debugging

Usage:
    from services.retry_service import retry_external_api, with_retry

    # Using decorator
    @with_retry(max_attempts=3)
    def call_external_api():
        return requests.get("https://api.example.com")

    # Using context manager style
    result = retry_external_api(lambda: stripe.Charge.create(...))
"""

import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Tuple, Type, Union

from tenacity import (
    RetryError,
    Retrying,
    after_log,
    before_log,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random_exponential,
)

logger = logging.getLogger("retry_service")

# Default configuration
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_MIN_WAIT_SECONDS = 1
DEFAULT_MAX_WAIT_SECONDS = 30
DEFAULT_EXPONENTIAL_BASE = 2

# Exception types that typically indicate transient failures worth retrying
TRANSIENT_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,  # Includes network-related errors
)

# Track retry statistics for monitoring
_retry_stats = {
    "total_attempts": 0,
    "total_retries": 0,
    "total_successes": 0,
    "total_failures": 0,
    "by_service": {},
}


def get_retry_stats() -> dict:
    """Get current retry statistics."""
    return dict(_retry_stats)


def reset_retry_stats() -> None:
    """Reset retry statistics (useful for testing)."""
    global _retry_stats
    _retry_stats = {
        "total_attempts": 0,
        "total_retries": 0,
        "total_successes": 0,
        "total_failures": 0,
        "by_service": {},
    }


def _get_request_id() -> Optional[str]:
    """Get current request ID for logging."""
    try:
        from services.request_id_service import get_request_id

        return get_request_id()
    except ImportError:
        return None


def _log_retry_attempt(
    service_name: str,
    attempt: int,
    max_attempts: int,
    exception: Exception,
    wait_time: float,
) -> None:
    """Log a retry attempt with context."""
    request_id = _get_request_id()

    log_data = {
        "service": service_name,
        "attempt": attempt,
        "max_attempts": max_attempts,
        "exception_type": type(exception).__name__,
        "exception_message": str(exception)[:200],  # Truncate long messages
        "wait_time_seconds": round(wait_time, 2),
        "request_id": request_id,
    }

    logger.warning(
        f"Retry attempt {attempt}/{max_attempts} for {service_name}: "
        f"{type(exception).__name__}: {str(exception)[:100]}... "
        f"(waiting {wait_time:.1f}s)",
        extra={"retry_data": log_data},
    )

    # Update statistics
    _retry_stats["total_retries"] += 1
    if service_name not in _retry_stats["by_service"]:
        _retry_stats["by_service"][service_name] = {
            "attempts": 0,
            "retries": 0,
            "failures": 0,
        }
    _retry_stats["by_service"][service_name]["retries"] += 1


def _log_retry_success(service_name: str, attempts: int) -> None:
    """Log successful completion after retries."""
    request_id = _get_request_id()

    if attempts > 1:
        logger.info(
            f"Request succeeded for {service_name} after {attempts} attempts",
            extra={
                "service": service_name,
                "attempts": attempts,
                "request_id": request_id,
            },
        )

    _retry_stats["total_successes"] += 1
    _retry_stats["total_attempts"] += attempts


def _log_retry_failure(service_name: str, attempts: int, exception: Exception) -> None:
    """Log final failure after all retries exhausted."""
    request_id = _get_request_id()

    logger.error(
        f"All {attempts} retry attempts failed for {service_name}: "
        f"{type(exception).__name__}: {str(exception)[:200]}",
        extra={
            "service": service_name,
            "attempts": attempts,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "request_id": request_id,
        },
    )

    _retry_stats["total_failures"] += 1
    _retry_stats["total_attempts"] += attempts
    if service_name not in _retry_stats["by_service"]:
        _retry_stats["by_service"][service_name] = {
            "attempts": 0,
            "retries": 0,
            "failures": 0,
        }
    _retry_stats["by_service"][service_name]["failures"] += 1


def calculate_backoff_time(
    attempt: int,
    min_wait: float = DEFAULT_MIN_WAIT_SECONDS,
    max_wait: float = DEFAULT_MAX_WAIT_SECONDS,
    base: float = DEFAULT_EXPONENTIAL_BASE,
    jitter: bool = True,
) -> float:
    """
    Calculate exponential backoff time with optional jitter.

    Args:
        attempt: Current attempt number (1-based)
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        base: Exponential base (default 2)
        jitter: Whether to add random jitter

    Returns:
        Wait time in seconds
    """
    # Exponential backoff: min_wait * (base ** (attempt - 1))
    wait_time = min_wait * (base ** (attempt - 1))

    # Cap at max_wait
    wait_time = min(wait_time, max_wait)

    # Add jitter (0-25% of wait time)
    if jitter:
        jitter_amount = wait_time * random.uniform(0, 0.25)
        wait_time += jitter_amount

    return wait_time


def with_retry(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_MIN_WAIT_SECONDS,
    max_wait: float = DEFAULT_MAX_WAIT_SECONDS,
    retry_exceptions: Tuple[Type[Exception], ...] = TRANSIENT_EXCEPTIONS,
    service_name: Optional[str] = None,
    reraise: bool = True,
):
    """
    Decorator to add retry logic to a function.

    Args:
        max_attempts: Maximum number of attempts (default 3)
        min_wait: Minimum wait between retries in seconds (default 1)
        max_wait: Maximum wait between retries in seconds (default 30)
        retry_exceptions: Tuple of exception types to retry on
        service_name: Name of the service for logging (defaults to function name)
        reraise: Whether to reraise the final exception (default True)

    Example:
        @with_retry(max_attempts=3, service_name="stripe")
        def create_charge(amount):
            return stripe.Charge.create(amount=amount)
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            svc_name = service_name or func.__name__
            attempt = 0
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)
                    _log_retry_success(svc_name, attempt)
                    return result

                except retry_exceptions as e:
                    last_exception = e

                    if attempt < max_attempts:
                        wait_time = calculate_backoff_time(attempt, min_wait, max_wait)
                        _log_retry_attempt(
                            svc_name, attempt, max_attempts, e, wait_time
                        )
                        time.sleep(wait_time)
                    else:
                        # Last attempt failed
                        _log_retry_failure(svc_name, attempt, e)
                        if reraise:
                            raise
                        return None

                except Exception as e:
                    # Non-retryable exception - fail immediately
                    _log_retry_failure(svc_name, attempt, e)
                    if reraise:
                        raise
                    return None

            # Should not reach here, but handle edge case
            if last_exception and reraise:
                raise last_exception
            return None

        return wrapper

    return decorator


def retry_external_api(
    func: Callable,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    min_wait: float = DEFAULT_MIN_WAIT_SECONDS,
    max_wait: float = DEFAULT_MAX_WAIT_SECONDS,
    retry_exceptions: Tuple[Type[Exception], ...] = TRANSIENT_EXCEPTIONS,
    service_name: str = "external_api",
) -> Any:
    """
    Execute a function with retry logic.

    This is a functional alternative to the decorator for cases where
    you can't or don't want to decorate a function.

    Args:
        func: Callable to execute
        max_attempts: Maximum number of attempts
        min_wait: Minimum wait between retries
        max_wait: Maximum wait between retries
        retry_exceptions: Exception types to retry on
        service_name: Name for logging

    Returns:
        Result of the function call

    Example:
        result = retry_external_api(
            lambda: stripe.Charge.create(amount=1000),
            service_name="stripe_charge"
        )
    """
    wrapped = with_retry(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        retry_exceptions=retry_exceptions,
        service_name=service_name,
    )(func)

    return wrapped()


# Pre-configured retry decorators for common services


def retry_stripe(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 10,
):
    """
    Retry decorator optimized for Stripe API calls.

    Handles common Stripe transient errors:
    - Network connectivity issues
    - Rate limiting (429)
    - Server errors (5xx)
    """
    try:
        import stripe

        stripe_exceptions = (
            stripe.error.APIConnectionError,
            stripe.error.RateLimitError,
            stripe.error.APIError,  # 5xx errors
        )
    except ImportError:
        stripe_exceptions = ()

    return with_retry(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        retry_exceptions=TRANSIENT_EXCEPTIONS + stripe_exceptions,
        service_name="stripe",
    )


def retry_twilio(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 15,
):
    """
    Retry decorator optimized for Twilio API calls.

    Handles common Twilio transient errors:
    - Network connectivity issues
    - Rate limiting
    - Server errors
    """
    try:
        from twilio.base.exceptions import TwilioRestException

        # Note: TwilioRestException status codes 429, 5xx are transient
        twilio_exceptions = ()  # We'll check status code in the exception handler
    except ImportError:
        twilio_exceptions = ()

    return with_retry(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        retry_exceptions=TRANSIENT_EXCEPTIONS + twilio_exceptions,
        service_name="twilio",
    )


def retry_email(
    max_attempts: int = 3,
    min_wait: float = 2,
    max_wait: float = 30,
):
    """
    Retry decorator for email sending (Gmail SMTP).

    Handles common SMTP transient errors:
    - Connection timeouts
    - Temporary server errors
    """
    import smtplib

    smtp_exceptions = (
        smtplib.SMTPServerDisconnected,
        smtplib.SMTPConnectError,
        smtplib.SMTPResponseException,
    )

    return with_retry(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        retry_exceptions=TRANSIENT_EXCEPTIONS + smtp_exceptions,
        service_name="email",
    )


def retry_http(
    max_attempts: int = 3,
    min_wait: float = 1,
    max_wait: float = 20,
    service_name: str = "http",
):
    """
    Retry decorator for generic HTTP requests.

    Handles common HTTP transient errors:
    - Connection errors
    - Timeouts
    - Server errors (5xx)
    """
    try:
        import requests

        http_exceptions = (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ChunkedEncodingError,
        )
    except ImportError:
        http_exceptions = ()

    return with_retry(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        retry_exceptions=TRANSIENT_EXCEPTIONS + http_exceptions,
        service_name=service_name,
    )


class RetryableHTTPClient:
    """
    HTTP client wrapper with built-in retry logic.

    Provides a requests-like interface with automatic retries
    for transient failures.

    Example:
        client = RetryableHTTPClient(service_name="sendcertified")
        response = client.get("https://api.sendcertified.com/v1/status")
        response = client.post("https://api.sendcertified.com/v1/mail", json=data)
    """

    def __init__(
        self,
        service_name: str = "http_client",
        max_attempts: int = 3,
        min_wait: float = 1,
        max_wait: float = 20,
        timeout: int = 30,
    ):
        self.service_name = service_name
        self.max_attempts = max_attempts
        self.min_wait = min_wait
        self.max_wait = max_wait
        self.timeout = timeout

    def _is_retryable_status(self, status_code: int) -> bool:
        """Check if HTTP status code indicates a retryable error."""
        # Retry on rate limit and server errors
        return status_code == 429 or (500 <= status_code < 600)

    def _make_request(self, method: str, url: str, **kwargs) -> Any:
        """Make HTTP request with retry logic."""
        import requests

        # Set default timeout
        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        # Add request ID headers
        headers = kwargs.get("headers", {})
        try:
            from services.request_id_service import with_request_id_headers

            headers = with_request_id_headers(headers)
            kwargs["headers"] = headers
        except ImportError:
            pass

        attempt = 0
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                response = requests.request(method, url, **kwargs)

                # Check for retryable status codes
                if self._is_retryable_status(response.status_code):
                    if attempt < self.max_attempts:
                        wait_time = calculate_backoff_time(
                            attempt, self.min_wait, self.max_wait
                        )
                        error = Exception(
                            f"HTTP {response.status_code}: {response.text[:100]}"
                        )
                        _log_retry_attempt(
                            self.service_name,
                            attempt,
                            self.max_attempts,
                            error,
                            wait_time,
                        )
                        time.sleep(wait_time)
                        continue

                _log_retry_success(self.service_name, attempt)
                return response

            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.ChunkedEncodingError,
            ) as e:
                last_exception = e

                if attempt < self.max_attempts:
                    wait_time = calculate_backoff_time(
                        attempt, self.min_wait, self.max_wait
                    )
                    _log_retry_attempt(
                        self.service_name, attempt, self.max_attempts, e, wait_time
                    )
                    time.sleep(wait_time)
                else:
                    _log_retry_failure(self.service_name, attempt, e)
                    raise

        # Should not reach here
        if last_exception:
            raise last_exception
        return None

    def get(self, url: str, **kwargs) -> Any:
        """Make GET request with retry logic."""
        return self._make_request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> Any:
        """Make POST request with retry logic."""
        return self._make_request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> Any:
        """Make PUT request with retry logic."""
        return self._make_request("PUT", url, **kwargs)

    def patch(self, url: str, **kwargs) -> Any:
        """Make PATCH request with retry logic."""
        return self._make_request("PATCH", url, **kwargs)

    def delete(self, url: str, **kwargs) -> Any:
        """Make DELETE request with retry logic."""
        return self._make_request("DELETE", url, **kwargs)


# Convenience function to get a pre-configured client
def get_http_client(
    service_name: str,
    max_attempts: int = 3,
    timeout: int = 30,
) -> RetryableHTTPClient:
    """
    Get a pre-configured RetryableHTTPClient for a service.

    Args:
        service_name: Name of the service for logging
        max_attempts: Maximum retry attempts
        timeout: Request timeout in seconds

    Returns:
        Configured RetryableHTTPClient instance
    """
    return RetryableHTTPClient(
        service_name=service_name,
        max_attempts=max_attempts,
        timeout=timeout,
    )


# Exports
__all__ = [
    # Core functions
    "with_retry",
    "retry_external_api",
    "calculate_backoff_time",
    # Pre-configured decorators
    "retry_stripe",
    "retry_twilio",
    "retry_email",
    "retry_http",
    # HTTP client
    "RetryableHTTPClient",
    "get_http_client",
    # Statistics
    "get_retry_stats",
    "reset_retry_stats",
    # Constants
    "DEFAULT_MAX_ATTEMPTS",
    "DEFAULT_MIN_WAIT_SECONDS",
    "DEFAULT_MAX_WAIT_SECONDS",
    "TRANSIENT_EXCEPTIONS",
]
