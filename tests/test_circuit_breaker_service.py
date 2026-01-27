"""
Unit tests for Circuit Breaker Service.

Tests the circuit breaker pattern implementation including:
- State transitions (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)
- Failure threshold handling
- Success threshold in half-open state
- Timeout mechanism
- Excluded exceptions
- Fallback functions
- Context manager support
- Decorator functionality
- Statistics tracking
- Thread safety
"""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from services.circuit_breaker_service import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    CircuitBreakerConfig,
    CircuitBreakerStats,
    get_circuit_breaker,
    circuit_protected,
    get_all_circuit_status,
    reset_circuit,
    reset_all_circuits,
    get_open_circuits,
    get_circuit_health_summary,
    DEFAULT_CONFIGS,
    _circuit_breakers,
    _registry_lock,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def fresh_circuit_breakers():
    """Clear and restore circuit breaker registry for each test."""
    with _registry_lock:
        original = _circuit_breakers.copy()
        _circuit_breakers.clear()
    yield
    with _registry_lock:
        _circuit_breakers.clear()
        _circuit_breakers.update(original)


@pytest.fixture
def circuit_breaker():
    """Create a fresh circuit breaker for testing."""
    return CircuitBreaker(
        name="test_service",
        failure_threshold=3,
        success_threshold=2,
        timeout=1.0,
    )


@pytest.fixture
def circuit_breaker_with_fallback():
    """Create a circuit breaker with fallback function."""
    fallback_fn = Mock(return_value="fallback_result")
    return CircuitBreaker(
        name="test_fallback",
        failure_threshold=2,
        success_threshold=1,
        timeout=0.5,
        fallback=fallback_fn,
    )


# =============================================================================
# CircuitState Enum Tests
# =============================================================================

class TestCircuitState:
    """Tests for CircuitState enum."""

    def test_closed_value(self):
        """CLOSED state has correct value."""
        assert CircuitState.CLOSED.value == "closed"

    def test_open_value(self):
        """OPEN state has correct value."""
        assert CircuitState.OPEN.value == "open"

    def test_half_open_value(self):
        """HALF_OPEN state has correct value."""
        assert CircuitState.HALF_OPEN.value == "half_open"

    def test_all_states_defined(self):
        """All three states are defined."""
        states = list(CircuitState)
        assert len(states) == 3
        assert CircuitState.CLOSED in states
        assert CircuitState.OPEN in states
        assert CircuitState.HALF_OPEN in states


# =============================================================================
# CircuitBreakerError Tests
# =============================================================================

class TestCircuitBreakerError:
    """Tests for CircuitBreakerError exception."""

    def test_default_message(self):
        """Error has default message with service name."""
        error = CircuitBreakerError("stripe")
        assert error.service_name == "stripe"
        assert "stripe" in str(error)
        assert "Circuit breaker open" in str(error)

    def test_custom_message(self):
        """Error can have custom message."""
        error = CircuitBreakerError("twilio", "Custom error message")
        assert error.service_name == "twilio"
        assert str(error) == "Custom error message"

    def test_exception_inheritance(self):
        """Error inherits from Exception."""
        error = CircuitBreakerError("test")
        assert isinstance(error, Exception)


# =============================================================================
# CircuitBreakerConfig Tests
# =============================================================================

class TestCircuitBreakerConfig:
    """Tests for CircuitBreakerConfig dataclass."""

    def test_default_values(self):
        """Config has sensible defaults."""
        config = CircuitBreakerConfig()
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 30.0
        assert config.excluded_exceptions == ()

    def test_custom_values(self):
        """Config accepts custom values."""
        config = CircuitBreakerConfig(
            failure_threshold=10,
            success_threshold=3,
            timeout=60.0,
            excluded_exceptions=(ValueError, KeyError),
        )
        assert config.failure_threshold == 10
        assert config.success_threshold == 3
        assert config.timeout == 60.0
        assert ValueError in config.excluded_exceptions
        assert KeyError in config.excluded_exceptions


# =============================================================================
# CircuitBreakerStats Tests
# =============================================================================

class TestCircuitBreakerStats:
    """Tests for CircuitBreakerStats dataclass."""

    def test_default_values(self):
        """Stats have zero defaults."""
        stats = CircuitBreakerStats()
        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.rejected_calls == 0
        assert stats.last_failure_time is None
        assert stats.last_success_time is None
        assert stats.state_changes == []
        assert stats.consecutive_failures == 0
        assert stats.consecutive_successes == 0


# =============================================================================
# CircuitBreaker Initialization Tests
# =============================================================================

class TestCircuitBreakerInit:
    """Tests for CircuitBreaker initialization."""

    def test_basic_initialization(self, circuit_breaker):
        """Circuit breaker initializes with correct values."""
        assert circuit_breaker.name == "test_service"
        assert circuit_breaker.failure_threshold == 3
        assert circuit_breaker.success_threshold == 2
        assert circuit_breaker.timeout == 1.0
        assert circuit_breaker.excluded_exceptions == ()
        assert circuit_breaker.fallback is None

    def test_initial_state_is_closed(self, circuit_breaker):
        """Circuit starts in CLOSED state."""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.is_closed
        assert not circuit_breaker.is_open
        assert not circuit_breaker.is_half_open

    def test_initial_counts_are_zero(self, circuit_breaker):
        """Initial failure and success counts are zero."""
        assert circuit_breaker._failure_count == 0
        assert circuit_breaker._success_count == 0

    def test_with_fallback(self, circuit_breaker_with_fallback):
        """Circuit breaker can be initialized with fallback."""
        assert circuit_breaker_with_fallback.fallback is not None

    def test_with_excluded_exceptions(self):
        """Circuit breaker can exclude specific exceptions."""
        breaker = CircuitBreaker(
            name="test",
            excluded_exceptions=(ValueError, TypeError),
        )
        assert ValueError in breaker.excluded_exceptions
        assert TypeError in breaker.excluded_exceptions


# =============================================================================
# State Transition Tests
# =============================================================================

class TestStateTransitions:
    """Tests for circuit breaker state transitions."""

    def test_closed_to_open_on_failures(self, circuit_breaker):
        """Circuit opens after failure threshold is reached."""
        # Start closed
        assert circuit_breaker.is_closed

        # Trigger failures
        for i in range(3):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("fail")))
            except RuntimeError:
                pass

        # Should be open now
        assert circuit_breaker.is_open

    def test_open_to_half_open_after_timeout(self, circuit_breaker):
        """Circuit transitions to half-open after timeout."""
        # Open the circuit
        for i in range(3):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                pass

        assert circuit_breaker.is_open

        # Wait for timeout
        time.sleep(1.1)

        # Accessing state should trigger half-open
        assert circuit_breaker.is_half_open

    def test_half_open_to_closed_on_success(self, circuit_breaker):
        """Circuit closes after success threshold in half-open."""
        # Open the circuit
        for i in range(3):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                pass

        # Wait for half-open
        time.sleep(1.1)
        assert circuit_breaker.is_half_open

        # Succeed twice (success_threshold=2)
        circuit_breaker.call(lambda: "success")
        circuit_breaker.call(lambda: "success")

        # Should be closed now
        assert circuit_breaker.is_closed

    def test_half_open_to_open_on_failure(self, circuit_breaker):
        """Circuit reopens on any failure in half-open state."""
        # Open the circuit
        for i in range(3):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                pass

        # Wait for half-open
        time.sleep(1.1)
        assert circuit_breaker.is_half_open

        # Fail once
        try:
            circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass

        # Should be back to open
        assert circuit_breaker.is_open


# =============================================================================
# Call Method Tests
# =============================================================================

class TestCallMethod:
    """Tests for CircuitBreaker.call() method."""

    def test_successful_call(self, circuit_breaker):
        """Successful calls pass through and return result."""
        result = circuit_breaker.call(lambda: "hello")
        assert result == "hello"

    def test_successful_call_with_args(self, circuit_breaker):
        """Call passes arguments to function."""
        def add(a, b):
            return a + b

        result = circuit_breaker.call(add, 2, 3)
        assert result == 5

    def test_successful_call_with_kwargs(self, circuit_breaker):
        """Call passes keyword arguments to function."""
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = circuit_breaker.call(greet, name="World")
        assert result == "Hello, World!"

    def test_failed_call_raises_exception(self, circuit_breaker):
        """Failed calls raise the original exception."""
        with pytest.raises(ValueError, match="test error"):
            circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("test error")))

    def test_open_circuit_raises_error(self, circuit_breaker):
        """Open circuit raises CircuitBreakerError."""
        # Open the circuit
        for i in range(3):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                pass

        # Should raise CircuitBreakerError
        with pytest.raises(CircuitBreakerError) as exc_info:
            circuit_breaker.call(lambda: "should not run")

        assert exc_info.value.service_name == "test_service"

    def test_open_circuit_uses_fallback(self, circuit_breaker_with_fallback):
        """Open circuit with fallback returns fallback result."""
        breaker = circuit_breaker_with_fallback

        # Open the circuit
        for i in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                pass

        # Should use fallback
        result = breaker.call(lambda: "should not run")
        assert result == "fallback_result"
        breaker.fallback.assert_called()


# =============================================================================
# Context Manager Tests
# =============================================================================

class TestContextManager:
    """Tests for circuit breaker context manager support."""

    def test_context_manager_success(self, circuit_breaker):
        """Context manager records success on clean exit."""
        with circuit_breaker:
            pass  # Success

        assert circuit_breaker.stats.successful_calls == 1

    def test_context_manager_failure(self, circuit_breaker):
        """Context manager records failure on exception."""
        with pytest.raises(ValueError):
            with circuit_breaker:
                raise ValueError("test")

        assert circuit_breaker.stats.failed_calls == 1

    def test_context_manager_open_circuit(self, circuit_breaker):
        """Context manager raises error when circuit is open."""
        # Open the circuit
        for i in range(3):
            try:
                with circuit_breaker:
                    raise RuntimeError()
            except RuntimeError:
                pass

        # Should raise on entry
        with pytest.raises(CircuitBreakerError):
            with circuit_breaker:
                pass


# =============================================================================
# Excluded Exceptions Tests
# =============================================================================

class TestExcludedExceptions:
    """Tests for excluded exception handling."""

    def test_excluded_exception_not_counted(self):
        """Excluded exceptions don't count as failures."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            excluded_exceptions=(ValueError,),
        )

        # Raise excluded exception multiple times
        for i in range(5):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(ValueError()))
            except ValueError:
                pass

        # Should still be closed
        assert breaker.is_closed
        assert breaker._failure_count == 0

    def test_non_excluded_exception_counted(self):
        """Non-excluded exceptions count as failures."""
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            excluded_exceptions=(ValueError,),
        )

        # Raise non-excluded exception
        for i in range(2):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(TypeError()))
            except TypeError:
                pass

        # Should be open
        assert breaker.is_open


# =============================================================================
# Statistics Tests
# =============================================================================

class TestStatistics:
    """Tests for statistics tracking."""

    def test_successful_call_stats(self, circuit_breaker):
        """Successful calls update stats correctly."""
        circuit_breaker.call(lambda: "ok")

        assert circuit_breaker.stats.total_calls == 1
        assert circuit_breaker.stats.successful_calls == 1
        assert circuit_breaker.stats.failed_calls == 0
        assert circuit_breaker.stats.consecutive_successes == 1
        assert circuit_breaker.stats.consecutive_failures == 0
        assert circuit_breaker.stats.last_success_time is not None

    def test_failed_call_stats(self, circuit_breaker):
        """Failed calls update stats correctly."""
        try:
            circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass

        assert circuit_breaker.stats.total_calls == 1
        assert circuit_breaker.stats.successful_calls == 0
        assert circuit_breaker.stats.failed_calls == 1
        assert circuit_breaker.stats.consecutive_successes == 0
        assert circuit_breaker.stats.consecutive_failures == 1
        assert circuit_breaker.stats.last_failure_time is not None

    def test_rejected_call_stats(self, circuit_breaker):
        """Rejected calls update stats correctly."""
        # Open the circuit
        for i in range(3):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                pass

        # Try again (rejected)
        try:
            circuit_breaker.call(lambda: "should not run")
        except CircuitBreakerError:
            pass

        assert circuit_breaker.stats.rejected_calls == 1

    def test_state_changes_tracked(self, circuit_breaker):
        """State changes are tracked in stats."""
        # Open the circuit
        for i in range(3):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                pass

        # Check state changes
        assert len(circuit_breaker.stats.state_changes) >= 1
        change = circuit_breaker.stats.state_changes[-1]
        assert change["from"] == "closed"
        assert change["to"] == "open"
        assert "timestamp" in change

    def test_get_status(self, circuit_breaker):
        """get_status returns complete status dict."""
        circuit_breaker.call(lambda: "ok")

        status = circuit_breaker.get_status()

        assert status["name"] == "test_service"
        assert status["state"] == "closed"
        assert status["failure_count"] == 0
        assert status["failure_threshold"] == 3
        assert status["success_count"] == 0
        assert status["success_threshold"] == 2
        assert status["timeout"] == 1.0
        assert "stats" in status
        assert status["stats"]["total_calls"] == 1
        assert status["stats"]["successful_calls"] == 1


# =============================================================================
# Reset Tests
# =============================================================================

class TestReset:
    """Tests for circuit breaker reset functionality."""

    def test_manual_reset(self, circuit_breaker):
        """Manual reset returns circuit to closed state."""
        # Open the circuit
        for i in range(3):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                pass

        assert circuit_breaker.is_open

        # Reset
        circuit_breaker.reset()

        # Should be closed
        assert circuit_breaker.is_closed
        assert circuit_breaker._failure_count == 0
        assert circuit_breaker._success_count == 0
        assert circuit_breaker._last_failure_time is None


# =============================================================================
# Factory Function Tests
# =============================================================================

class TestGetCircuitBreaker:
    """Tests for get_circuit_breaker factory function."""

    def test_creates_new_breaker(self, fresh_circuit_breakers):
        """Creates new circuit breaker if not exists."""
        breaker = get_circuit_breaker("new_service")

        assert breaker.name == "new_service"
        assert breaker.is_closed

    def test_returns_same_instance(self, fresh_circuit_breakers):
        """Returns same instance for same name."""
        breaker1 = get_circuit_breaker("same_service")
        breaker2 = get_circuit_breaker("same_service")

        assert breaker1 is breaker2

    def test_uses_default_config(self, fresh_circuit_breakers):
        """Uses default config for known services."""
        breaker = get_circuit_breaker("stripe")

        config = DEFAULT_CONFIGS["stripe"]
        assert breaker.failure_threshold == config.failure_threshold
        assert breaker.success_threshold == config.success_threshold
        assert breaker.timeout == config.timeout

    def test_override_config(self, fresh_circuit_breakers):
        """Can override default config values."""
        breaker = get_circuit_breaker(
            "stripe",
            failure_threshold=10,
            timeout=60.0,
        )

        assert breaker.failure_threshold == 10
        assert breaker.timeout == 60.0

    def test_with_fallback(self, fresh_circuit_breakers):
        """Can provide fallback function."""
        fallback = Mock(return_value="fallback")
        breaker = get_circuit_breaker("test", fallback=fallback)

        assert breaker.fallback is fallback


# =============================================================================
# Decorator Tests
# =============================================================================

class TestCircuitProtectedDecorator:
    """Tests for circuit_protected decorator."""

    def test_decorator_wraps_function(self, fresh_circuit_breakers):
        """Decorator preserves function metadata."""
        @circuit_protected("test")
        def my_function():
            """My docstring."""
            return "result"

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "My docstring."

    def test_decorator_success(self, fresh_circuit_breakers):
        """Decorated function returns result on success."""
        @circuit_protected("test")
        def my_function():
            return "success"

        result = my_function()
        assert result == "success"

    def test_decorator_failure(self, fresh_circuit_breakers):
        """Decorated function raises exception on failure."""
        @circuit_protected("test")
        def my_function():
            raise ValueError("error")

        with pytest.raises(ValueError):
            my_function()

    def test_decorator_opens_circuit(self, fresh_circuit_breakers):
        """Decorated function opens circuit after failures."""
        @circuit_protected("test", failure_threshold=2)
        def my_function():
            raise RuntimeError()

        for i in range(2):
            try:
                my_function()
            except RuntimeError:
                pass

        with pytest.raises(CircuitBreakerError):
            my_function()

    def test_decorator_with_fallback(self, fresh_circuit_breakers):
        """Decorated function uses fallback when circuit is open."""
        fallback = Mock(return_value="fallback")

        @circuit_protected("test", failure_threshold=1, fallback=fallback)
        def my_function():
            raise RuntimeError()

        # Fail to open circuit
        try:
            my_function()
        except RuntimeError:
            pass

        # Should use fallback
        result = my_function()
        assert result == "fallback"

    def test_decorator_attaches_breaker(self, fresh_circuit_breakers):
        """Decorated function has breaker attached."""
        @circuit_protected("test")
        def my_function():
            return "ok"

        assert hasattr(my_function, "_circuit_breaker")
        assert isinstance(my_function._circuit_breaker, CircuitBreaker)


# =============================================================================
# Registry Function Tests
# =============================================================================

class TestRegistryFunctions:
    """Tests for registry management functions."""

    def test_get_all_circuit_status(self, fresh_circuit_breakers):
        """get_all_circuit_status returns all breakers."""
        get_circuit_breaker("service1")
        get_circuit_breaker("service2")

        status = get_all_circuit_status()

        assert "service1" in status
        assert "service2" in status
        assert status["service1"]["state"] == "closed"
        assert status["service2"]["state"] == "closed"

    def test_reset_circuit(self, fresh_circuit_breakers):
        """reset_circuit resets specific breaker."""
        breaker = get_circuit_breaker("test", failure_threshold=1)

        # Open it
        try:
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass

        assert breaker.is_open

        # Reset
        result = reset_circuit("test")

        assert result is True
        assert breaker.is_closed

    def test_reset_circuit_not_found(self, fresh_circuit_breakers):
        """reset_circuit returns False for unknown breaker."""
        result = reset_circuit("nonexistent")
        assert result is False

    def test_reset_all_circuits(self, fresh_circuit_breakers):
        """reset_all_circuits resets all breakers."""
        breaker1 = get_circuit_breaker("service1", failure_threshold=1)
        breaker2 = get_circuit_breaker("service2", failure_threshold=1)

        # Open both
        try:
            breaker1.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass
        try:
            breaker2.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass

        assert breaker1.is_open
        assert breaker2.is_open

        # Reset all
        count = reset_all_circuits()

        assert count == 2
        assert breaker1.is_closed
        assert breaker2.is_closed

    def test_get_open_circuits(self, fresh_circuit_breakers):
        """get_open_circuits returns list of open breakers."""
        breaker1 = get_circuit_breaker("healthy", failure_threshold=1)
        breaker2 = get_circuit_breaker("failing", failure_threshold=1)

        # Open one
        try:
            breaker2.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass

        open_circuits = get_open_circuits()

        assert "failing" in open_circuits
        assert "healthy" not in open_circuits

    def test_get_circuit_health_summary(self, fresh_circuit_breakers):
        """get_circuit_health_summary returns correct summary."""
        breaker1 = get_circuit_breaker("healthy")
        breaker2 = get_circuit_breaker("failing", failure_threshold=1)

        # Make one call to healthy
        breaker1.call(lambda: "ok")

        # Open failing
        try:
            breaker2.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass

        summary = get_circuit_health_summary()

        assert summary["total_circuits"] == 2
        assert summary["healthy_count"] == 1
        assert summary["unhealthy_count"] == 1
        assert summary["degraded_count"] == 0
        assert "failing" in summary["open_circuits"]
        assert summary["total_calls"] == 2
        assert summary["total_failures"] == 1


# =============================================================================
# Default Config Tests
# =============================================================================

class TestDefaultConfigs:
    """Tests for default service configurations."""

    def test_stripe_config(self):
        """Stripe has expected config."""
        config = DEFAULT_CONFIGS["stripe"]
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 30.0

    def test_twilio_config(self):
        """Twilio has expected config."""
        config = DEFAULT_CONFIGS["twilio"]
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 30.0

    def test_email_config(self):
        """Email has expected config (longer timeout)."""
        config = DEFAULT_CONFIGS["email"]
        assert config.failure_threshold == 3
        assert config.timeout == 60.0

    def test_credit_import_config(self):
        """Credit import has long timeout."""
        config = DEFAULT_CONFIGS["credit_import"]
        assert config.timeout == 120.0

    def test_all_known_services(self):
        """All expected services have configs."""
        expected = ["stripe", "twilio", "email", "usps", "claude_ai", "sendcertified", "credit_import"]
        for service in expected:
            assert service in DEFAULT_CONFIGS


# =============================================================================
# Thread Safety Tests
# =============================================================================

class TestThreadSafety:
    """Basic thread safety tests."""

    def test_concurrent_calls(self, fresh_circuit_breakers):
        """Circuit breaker handles concurrent calls."""
        breaker = get_circuit_breaker("concurrent_test", failure_threshold=10)
        results = []
        errors = []

        def make_call():
            try:
                result = breaker.call(lambda: "ok")
                results.append(result)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=make_call) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 20
        assert len(errors) == 0
        assert breaker.stats.total_calls == 20

    def test_concurrent_failures(self, fresh_circuit_breakers):
        """Circuit breaker handles concurrent failures correctly."""
        breaker = get_circuit_breaker("fail_test", failure_threshold=5)
        errors = []

        def make_failing_call():
            try:
                breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                errors.append("runtime")
            except CircuitBreakerError:
                errors.append("circuit")

        threads = [threading.Thread(target=make_failing_call) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have some runtime errors and possibly some circuit errors
        assert len(errors) == 10
        # Circuit should be open after 5 failures
        assert breaker.is_open


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_zero_failure_threshold(self):
        """Zero failure threshold opens immediately."""
        breaker = CircuitBreaker(name="zero", failure_threshold=0)
        # Already open because 0 failures = threshold
        try:
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except:
            pass
        assert breaker.is_open

    def test_very_short_timeout(self):
        """Very short timeout transitions quickly."""
        breaker = CircuitBreaker(
            name="fast",
            failure_threshold=1,
            timeout=0.01,
        )

        # Open it
        try:
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
        except RuntimeError:
            pass

        # Wait briefly
        time.sleep(0.02)

        # Should be half-open
        assert breaker.is_half_open

    def test_allow_request_check(self, circuit_breaker):
        """allow_request returns correct values."""
        assert circuit_breaker.allow_request() is True

        # Open it
        for i in range(3):
            try:
                circuit_breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except RuntimeError:
                pass

        assert circuit_breaker.allow_request() is False

    def test_state_changes_limit(self):
        """State changes list is limited to 100 entries."""
        breaker = CircuitBreaker(name="many_changes", failure_threshold=1, timeout=0.001)

        # Cause many state changes
        for _ in range(60):
            try:
                breaker.call(lambda: (_ for _ in ()).throw(RuntimeError()))
            except:
                pass
            time.sleep(0.002)
            breaker.call(lambda: "ok")

        # Should be capped at 100
        assert len(breaker.stats.state_changes) <= 100


# =============================================================================
# Integration-Like Tests
# =============================================================================

class TestIntegrationPatterns:
    """Tests for common integration patterns."""

    def test_service_protection_pattern(self, fresh_circuit_breakers):
        """Test typical service protection pattern."""
        call_count = 0

        @circuit_protected("api_service", failure_threshold=3, timeout=0.1)
        def call_external_api(data):
            nonlocal call_count
            call_count += 1
            if call_count <= 3:
                raise ConnectionError("Service unavailable")
            return {"status": "ok", "data": data}

        # First 3 calls fail
        for i in range(3):
            try:
                call_external_api({"id": i})
            except ConnectionError:
                pass

        assert call_count == 3

        # Circuit should be open now
        with pytest.raises(CircuitBreakerError):
            call_external_api({"id": 4})

        # call_count should not increase (function not called)
        assert call_count == 3

        # Wait for timeout
        time.sleep(0.15)

        # Now should be half-open and function gets called
        result = call_external_api({"id": 5})
        assert result == {"status": "ok", "data": {"id": 5}}
        assert call_count == 4

    def test_fallback_pattern(self, fresh_circuit_breakers):
        """Test fallback function pattern."""
        cache = {"last_value": "cached_data"}

        def fallback_to_cache(*args, **kwargs):
            return cache["last_value"]

        @circuit_protected("cache_service", failure_threshold=1, fallback=fallback_to_cache)
        def get_fresh_data():
            raise ConnectionError("Primary service down")

        # First call fails and opens circuit
        try:
            get_fresh_data()
        except ConnectionError:
            pass

        # Second call uses fallback
        result = get_fresh_data()
        assert result == "cached_data"

    def test_multiple_services_isolation(self, fresh_circuit_breakers):
        """Test that different services have isolated circuits."""
        @circuit_protected("service_a", failure_threshold=1)
        def call_service_a():
            raise RuntimeError()

        @circuit_protected("service_b", failure_threshold=1)
        def call_service_b():
            return "success"

        # Fail service A
        try:
            call_service_a()
        except RuntimeError:
            pass

        # Service A should be open
        with pytest.raises(CircuitBreakerError):
            call_service_a()

        # Service B should still work
        result = call_service_b()
        assert result == "success"
