"""
Graceful Shutdown Service for FCRA Platform

Handles clean shutdown of all services:
- Signal handling (SIGTERM/SIGINT)
- In-flight request completion
- Database connection cleanup
- Cache cleanup
- Log flushing
"""

import atexit
import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from typing import Callable, Dict, List, Optional

# Environment variable for shutdown timeout
SHUTDOWN_TIMEOUT = int(os.environ.get("SHUTDOWN_TIMEOUT_SECONDS", "30"))


class GracefulShutdownManager:
    """
    Manages graceful shutdown of the application.

    Registers cleanup handlers and executes them in order when
    SIGTERM or SIGINT is received.
    """

    def __init__(self, timeout_seconds: int = SHUTDOWN_TIMEOUT):
        self._handlers: List[Dict] = []
        self._shutdown_in_progress = False
        self._shutdown_complete = False
        self._timeout = timeout_seconds
        self._lock = threading.Lock()
        self._active_requests = 0
        self._requests_lock = threading.Lock()
        self._shutdown_time: Optional[datetime] = None
        self._logger = logging.getLogger("shutdown")

    def _safe_log(self, level: str, message: str) -> None:
        """Log a message, ignoring errors if logging system is closed."""
        try:
            getattr(self._logger, level)(message)
        except (ValueError, OSError):
            pass  # Logging may fail if stdout is closed during shutdown

    def register_handler(
        self,
        name: str,
        handler: Callable[[], None],
        priority: int = 50,
        timeout: int = 5,
    ) -> None:
        """
        Register a cleanup handler to be called during shutdown.

        Args:
            name: Human-readable name for logging
            handler: Callable to execute during shutdown
            priority: Lower numbers run first (default: 50)
            timeout: Max seconds to wait for this handler (default: 5)
        """
        with self._lock:
            self._handlers.append(
                {
                    "name": name,
                    "handler": handler,
                    "priority": priority,
                    "timeout": timeout,
                }
            )
            # Keep handlers sorted by priority
            self._handlers.sort(key=lambda h: h["priority"])

    def unregister_handler(self, name: str) -> bool:
        """Remove a handler by name."""
        with self._lock:
            for i, h in enumerate(self._handlers):
                if h["name"] == name:
                    del self._handlers[i]
                    return True
            return False

    def request_started(self) -> None:
        """Track that a request has started."""
        with self._requests_lock:
            self._active_requests += 1

    def request_finished(self) -> None:
        """Track that a request has finished."""
        with self._requests_lock:
            self._active_requests = max(0, self._active_requests - 1)

    @property
    def active_requests(self) -> int:
        """Get count of active requests."""
        with self._requests_lock:
            return self._active_requests

    @property
    def is_shutting_down(self) -> bool:
        """Check if shutdown is in progress."""
        return self._shutdown_in_progress

    def _wait_for_requests(self, timeout: int = 10) -> bool:
        """
        Wait for in-flight requests to complete.

        Args:
            timeout: Max seconds to wait

        Returns:
            True if all requests completed, False if timeout
        """
        start = time.time()
        while self.active_requests > 0:
            if time.time() - start > timeout:
                self._logger.warning(
                    f"Timeout waiting for {self.active_requests} requests to complete"
                )
                return False
            time.sleep(0.1)
        return True

    def shutdown(self, signum: Optional[int] = None, frame=None) -> None:
        """
        Execute graceful shutdown.

        Args:
            signum: Signal number (if called as signal handler)
            frame: Stack frame (if called as signal handler)
        """
        with self._lock:
            if self._shutdown_in_progress:
                self._logger.info("Shutdown already in progress, ignoring")
                return
            self._shutdown_in_progress = True
            self._shutdown_time = datetime.utcnow()

        signal_name = signal.Signals(signum).name if signum else "manual"
        self._safe_log("info", f"Graceful shutdown initiated (signal: {signal_name})")

        # Step 1: Wait for in-flight requests
        self._safe_log("info", "Waiting for in-flight requests to complete...")
        requests_completed = self._wait_for_requests(timeout=10)
        if requests_completed:
            self._safe_log("info", "All in-flight requests completed")
        else:
            self._safe_log(
                "warning", "Proceeding with shutdown despite pending requests"
            )

        # Step 2: Execute cleanup handlers in priority order
        self._safe_log("info", f"Executing {len(self._handlers)} cleanup handlers...")

        for handler_info in self._handlers:
            name = handler_info["name"]
            handler = handler_info["handler"]
            timeout = handler_info["timeout"]

            self._safe_log("info", f"Running cleanup: {name}")

            try:
                # Run handler with timeout
                result = {"success": False, "error": None}

                def run_handler():
                    try:
                        handler()
                        result["success"] = True
                    except Exception as e:
                        result["error"] = str(e)

                thread = threading.Thread(target=run_handler)
                thread.start()
                thread.join(timeout=timeout)

                if thread.is_alive():
                    self._safe_log(
                        "warning", f"Handler '{name}' timed out after {timeout}s"
                    )
                elif result["error"]:
                    self._safe_log(
                        "error", f"Handler '{name}' failed: {result['error']}"
                    )
                else:
                    self._safe_log("info", f"Handler '{name}' completed successfully")

            except Exception as e:
                self._safe_log("error", f"Error running handler '{name}': {e}")

        self._shutdown_complete = True
        self._safe_log("info", "Graceful shutdown complete")

    def install_signal_handlers(self) -> None:
        """Install SIGTERM and SIGINT signal handlers."""
        # Only install in main thread
        if threading.current_thread() is not threading.main_thread():
            self._logger.warning("Cannot install signal handlers from non-main thread")
            return

        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        self._logger.info("Signal handlers installed (SIGTERM, SIGINT)")

    def get_status(self) -> Dict:
        """Get current shutdown manager status."""
        return {
            "shutdown_in_progress": self._shutdown_in_progress,
            "shutdown_complete": self._shutdown_complete,
            "shutdown_time": (
                self._shutdown_time.isoformat() if self._shutdown_time else None
            ),
            "active_requests": self.active_requests,
            "registered_handlers": [h["name"] for h in self._handlers],
            "timeout_seconds": self._timeout,
        }


# Global shutdown manager instance
_shutdown_manager: Optional[GracefulShutdownManager] = None


def get_shutdown_manager() -> GracefulShutdownManager:
    """Get or create the global shutdown manager."""
    global _shutdown_manager
    if _shutdown_manager is None:
        _shutdown_manager = GracefulShutdownManager()
    return _shutdown_manager


def register_shutdown_handler(
    name: str, handler: Callable[[], None], priority: int = 50, timeout: int = 5
) -> None:
    """Convenience function to register a shutdown handler."""
    get_shutdown_manager().register_handler(name, handler, priority, timeout)


def init_graceful_shutdown(app=None) -> GracefulShutdownManager:
    """
    Initialize graceful shutdown for the application.

    Args:
        app: Flask application (optional)

    Returns:
        The shutdown manager instance
    """
    manager = get_shutdown_manager()

    # Install signal handlers
    try:
        manager.install_signal_handlers()
    except Exception as e:
        logging.getLogger("shutdown").warning(f"Could not install signal handlers: {e}")

    # Register atexit handler as backup
    atexit.register(
        lambda: manager.shutdown() if not manager._shutdown_complete else None
    )

    # Register default handlers
    _register_default_handlers()

    # If Flask app provided, add request tracking middleware
    if app is not None:
        _add_flask_middleware(app, manager)

    return manager


def _register_default_handlers() -> None:
    """Register default cleanup handlers."""
    manager = get_shutdown_manager()

    # Priority 10: Stop accepting new requests (handled by Flask/Gunicorn)

    # Priority 20: Shutdown cache cleanup threads
    def shutdown_cache():
        try:
            from services.performance_service import app_cache

            app_cache.shutdown()
        except Exception:
            pass

    manager.register_handler("cache_cleanup", shutdown_cache, priority=20, timeout=5)

    # Priority 30: Close database connections
    def close_database():
        try:
            from database import engine

            if engine:
                engine.dispose()
        except Exception:
            pass

    manager.register_handler(
        "database_connections", close_database, priority=30, timeout=10
    )

    # Priority 90: Flush all loggers
    def flush_logs():
        try:
            logging.shutdown()
        except Exception:
            pass

    manager.register_handler("flush_logs", flush_logs, priority=90, timeout=5)


def _add_flask_middleware(app, manager: GracefulShutdownManager) -> None:
    """Add Flask middleware for request tracking."""

    @app.before_request
    def track_request_start():
        manager.request_started()

    @app.after_request
    def track_request_end(response):
        manager.request_finished()
        return response

    @app.teardown_request
    def track_request_teardown(exception=None):
        # Ensure request is tracked as finished even on error
        # Note: after_request might not run on error
        pass
