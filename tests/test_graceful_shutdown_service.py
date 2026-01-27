"""
Tests for Graceful Shutdown Service

Tests cover:
- Handler registration and execution
- Request tracking
- Signal handling
- Shutdown ordering
- Timeout handling
"""

import signal
import threading
import time
from unittest.mock import MagicMock, patch

import pytest

from services.graceful_shutdown_service import (
    GracefulShutdownManager,
    get_shutdown_manager,
    register_shutdown_handler,
    init_graceful_shutdown,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def manager():
    """Create a fresh shutdown manager for each test."""
    mgr = GracefulShutdownManager(timeout_seconds=10)
    yield mgr


@pytest.fixture
def clean_global_manager():
    """Reset the global shutdown manager."""
    import services.graceful_shutdown_service as svc
    original = svc._shutdown_manager
    svc._shutdown_manager = None
    yield
    svc._shutdown_manager = original


# ============================================================================
# Handler Registration Tests
# ============================================================================

class TestHandlerRegistration:
    """Tests for handler registration."""

    def test_register_handler(self, manager):
        """Test registering a cleanup handler."""
        handler = MagicMock()
        manager.register_handler("test_handler", handler, priority=50)

        assert len(manager._handlers) == 1
        assert manager._handlers[0]["name"] == "test_handler"
        assert manager._handlers[0]["priority"] == 50

    def test_register_multiple_handlers(self, manager):
        """Test registering multiple handlers."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        manager.register_handler("handler1", handler1, priority=50)
        manager.register_handler("handler2", handler2, priority=30)

        assert len(manager._handlers) == 2

    def test_handlers_sorted_by_priority(self, manager):
        """Test that handlers are sorted by priority (lower first)."""
        manager.register_handler("low", MagicMock(), priority=10)
        manager.register_handler("high", MagicMock(), priority=90)
        manager.register_handler("medium", MagicMock(), priority=50)

        names = [h["name"] for h in manager._handlers]
        assert names == ["low", "medium", "high"]

    def test_unregister_handler(self, manager):
        """Test unregistering a handler."""
        manager.register_handler("test", MagicMock(), priority=50)
        assert len(manager._handlers) == 1

        result = manager.unregister_handler("test")
        assert result is True
        assert len(manager._handlers) == 0

    def test_unregister_nonexistent_handler(self, manager):
        """Test unregistering a handler that doesn't exist."""
        result = manager.unregister_handler("nonexistent")
        assert result is False


# ============================================================================
# Request Tracking Tests
# ============================================================================

class TestRequestTracking:
    """Tests for request tracking."""

    def test_request_started(self, manager):
        """Test tracking request start."""
        assert manager.active_requests == 0

        manager.request_started()
        assert manager.active_requests == 1

        manager.request_started()
        assert manager.active_requests == 2

    def test_request_finished(self, manager):
        """Test tracking request finish."""
        manager.request_started()
        manager.request_started()
        assert manager.active_requests == 2

        manager.request_finished()
        assert manager.active_requests == 1

        manager.request_finished()
        assert manager.active_requests == 0

    def test_request_finished_does_not_go_negative(self, manager):
        """Test that active requests never goes negative."""
        manager.request_finished()
        manager.request_finished()
        assert manager.active_requests == 0

    def test_concurrent_request_tracking(self, manager):
        """Test thread-safe request tracking."""
        errors = []

        def add_requests():
            try:
                for _ in range(100):
                    manager.request_started()
            except Exception as e:
                errors.append(e)

        def remove_requests():
            try:
                for _ in range(100):
                    manager.request_finished()
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=add_requests),
            threading.Thread(target=add_requests),
            threading.Thread(target=remove_requests),
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        # 200 added, 100 removed = 100 remaining
        assert manager.active_requests == 100


# ============================================================================
# Shutdown Execution Tests
# ============================================================================

class TestShutdownExecution:
    """Tests for shutdown execution."""

    def test_shutdown_executes_handlers(self, manager):
        """Test that shutdown executes all handlers."""
        handler1 = MagicMock()
        handler2 = MagicMock()

        manager.register_handler("h1", handler1, priority=10)
        manager.register_handler("h2", handler2, priority=20)

        manager.shutdown()

        handler1.assert_called_once()
        handler2.assert_called_once()

    def test_shutdown_executes_handlers_in_order(self, manager):
        """Test that handlers are executed in priority order."""
        call_order = []

        def handler1():
            call_order.append("h1")

        def handler2():
            call_order.append("h2")

        def handler3():
            call_order.append("h3")

        manager.register_handler("h1", handler1, priority=30)
        manager.register_handler("h2", handler2, priority=10)
        manager.register_handler("h3", handler3, priority=20)

        manager.shutdown()

        assert call_order == ["h2", "h3", "h1"]

    def test_shutdown_only_runs_once(self, manager):
        """Test that shutdown only runs once even if called multiple times."""
        handler = MagicMock()
        manager.register_handler("test", handler)

        manager.shutdown()
        manager.shutdown()
        manager.shutdown()

        handler.assert_called_once()

    def test_is_shutting_down_flag(self, manager):
        """Test that is_shutting_down flag is set."""
        assert manager.is_shutting_down is False

        manager.shutdown()

        assert manager.is_shutting_down is True

    def test_shutdown_waits_for_requests(self, manager):
        """Test that shutdown waits for in-flight requests."""
        manager.request_started()

        shutdown_started = threading.Event()
        shutdown_completed = threading.Event()

        def shutdown_thread():
            shutdown_started.set()
            manager.shutdown()
            shutdown_completed.set()

        t = threading.Thread(target=shutdown_thread)
        t.start()

        # Wait for shutdown to start
        shutdown_started.wait(timeout=1)
        time.sleep(0.2)

        # Shutdown should not complete while request is active
        # (but has a timeout so will eventually complete)
        manager.request_finished()

        # Now shutdown should complete
        shutdown_completed.wait(timeout=15)
        assert manager._shutdown_complete is True

        t.join()

    def test_handler_timeout(self, manager):
        """Test that slow handlers are timed out."""
        def slow_handler():
            time.sleep(10)  # Very slow

        manager.register_handler("slow", slow_handler, timeout=1)

        start = time.time()
        manager.shutdown()
        elapsed = time.time() - start

        # Should complete in ~1 second (the timeout), not 10 seconds
        assert elapsed < 5

    def test_handler_exception_does_not_stop_shutdown(self, manager):
        """Test that handler exceptions don't stop other handlers."""
        handler1 = MagicMock(side_effect=Exception("Error!"))
        handler2 = MagicMock()

        manager.register_handler("h1", handler1, priority=10)
        manager.register_handler("h2", handler2, priority=20)

        manager.shutdown()

        # Both handlers should have been called
        handler1.assert_called_once()
        handler2.assert_called_once()


# ============================================================================
# Status Tests
# ============================================================================

class TestStatus:
    """Tests for shutdown status."""

    def test_get_status_initial(self, manager):
        """Test initial status."""
        status = manager.get_status()

        assert status["shutdown_in_progress"] is False
        assert status["shutdown_complete"] is False
        assert status["shutdown_time"] is None
        assert status["active_requests"] == 0
        assert status["registered_handlers"] == []

    def test_get_status_with_handlers(self, manager):
        """Test status with registered handlers."""
        manager.register_handler("h1", MagicMock())
        manager.register_handler("h2", MagicMock())

        status = manager.get_status()
        assert status["registered_handlers"] == ["h1", "h2"]

    def test_get_status_after_shutdown(self, manager):
        """Test status after shutdown."""
        manager.shutdown()

        status = manager.get_status()
        assert status["shutdown_in_progress"] is True
        assert status["shutdown_complete"] is True
        assert status["shutdown_time"] is not None


# ============================================================================
# Global Manager Tests
# ============================================================================

class TestGlobalManager:
    """Tests for global manager functions."""

    def test_get_shutdown_manager_creates_singleton(self, clean_global_manager):
        """Test that get_shutdown_manager creates a singleton."""
        manager1 = get_shutdown_manager()
        manager2 = get_shutdown_manager()

        assert manager1 is manager2

    def test_register_shutdown_handler_convenience(self, clean_global_manager):
        """Test the convenience function for registering handlers."""
        handler = MagicMock()
        register_shutdown_handler("test", handler, priority=50)

        manager = get_shutdown_manager()
        assert len(manager._handlers) > 0  # Has default handlers too


# ============================================================================
# Flask Integration Tests
# ============================================================================

class TestFlaskIntegration:
    """Tests for Flask integration."""

    def test_init_graceful_shutdown_without_app(self, clean_global_manager):
        """Test initialization without Flask app."""
        with patch('services.graceful_shutdown_service.signal.signal'):
            manager = init_graceful_shutdown(app=None)

        assert manager is not None
        # Should have default handlers registered
        handler_names = [h["name"] for h in manager._handlers]
        assert "cache_cleanup" in handler_names
        assert "database_connections" in handler_names
        assert "flush_logs" in handler_names

    def test_default_handler_priorities(self, clean_global_manager):
        """Test that default handlers have correct priorities."""
        with patch('services.graceful_shutdown_service.signal.signal'):
            manager = init_graceful_shutdown(app=None)

        handlers = {h["name"]: h["priority"] for h in manager._handlers}

        # Cache should be cleaned before database is closed
        assert handlers["cache_cleanup"] < handlers["database_connections"]
        # Logs should be flushed last
        assert handlers["flush_logs"] > handlers["database_connections"]
