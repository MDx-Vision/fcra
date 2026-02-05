"""
Feature Flag Service

Provides feature flag functionality for safe feature rollouts:
- Simple on/off flags
- Percentage-based rollouts
- User/role targeting
- Caching for performance
- Decorator and context manager support

Usage:
    from services.feature_flag_service import (
        is_enabled,
        feature_flag,
        get_feature_flag_service,
    )

    # Simple check
    if is_enabled("new_dashboard"):
        show_new_dashboard()

    # With user context
    if is_enabled("beta_feature", user_id=123):
        show_beta_feature()

    # Decorator
    @feature_flag("new_api")
    def new_api_endpoint():
        ...

    # Get service for more control
    service = get_feature_flag_service()
    service.set_flag("new_feature", enabled=True)
"""

import functools
import hashlib
import logging
import threading
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

# Cache configuration
CACHE_TTL_SECONDS = 60  # Cache flags for 1 minute
_cache: Dict[str, Any] = {}
_cache_timestamps: Dict[str, float] = {}
_cache_lock = threading.RLock()


# =============================================================================
# Flag Categories
# =============================================================================

FLAG_CATEGORIES = [
    "feature",  # New features
    "experiment",  # A/B tests
    "ops",  # Operational flags (maintenance mode, etc.)
    "ui",  # UI variations
    "kill_switch",  # Emergency kill switches
]


# =============================================================================
# Default Flags
# =============================================================================

DEFAULT_FLAGS = [
    {
        "key": "maintenance_mode",
        "name": "Maintenance Mode",
        "description": "Enable maintenance mode for the entire application",
        "category": "ops",
        "enabled": False,
    },
    {
        "key": "new_dashboard",
        "name": "New Dashboard Design",
        "description": "Enable the redesigned dashboard",
        "category": "ui",
        "enabled": False,
    },
    {
        "key": "ai_dispute_writer_v2",
        "name": "AI Dispute Writer V2",
        "description": "Use the improved AI dispute writer",
        "category": "feature",
        "enabled": True,
    },
    {
        "key": "credit_import_auto_retry",
        "name": "Credit Import Auto-Retry",
        "description": "Automatically retry failed credit imports",
        "category": "feature",
        "enabled": True,
    },
    {
        "key": "slack_notifications",
        "name": "Slack Notifications",
        "description": "Send critical alerts to Slack",
        "category": "ops",
        "enabled": True,
    },
]


# =============================================================================
# Feature Flag Service
# =============================================================================


class FeatureFlagService:
    """
    Service for managing feature flags.

    Supports:
    - Simple on/off flags
    - Percentage-based rollouts
    - User ID targeting
    - Role-based targeting
    - Caching for performance
    """

    def __init__(self, db_session=None):
        """
        Initialize the service.

        Args:
            db_session: SQLAlchemy session (optional, will get from database module)
        """
        self._db = db_session
        self._local_overrides: Dict[str, bool] = {}

    def _get_db(self):
        """Get database session."""
        if self._db:
            return self._db
        from database import SessionLocal

        return SessionLocal()

    def _should_close_db(self):
        """Check if we should close the database session."""
        return self._db is None

    # -------------------------------------------------------------------------
    # Core Flag Operations
    # -------------------------------------------------------------------------

    def is_enabled(
        self,
        key: str,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        default: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Check if a feature flag is enabled.

        Args:
            key: Flag key
            user_id: User ID for targeting
            user_role: User role for targeting
            default: Default value if flag not found
            context: Additional context for evaluation

        Returns:
            True if enabled, False otherwise
        """
        # Check local overrides first (for testing)
        if key in self._local_overrides:
            return self._local_overrides[key]

        # Check cache
        cached = self._get_from_cache(key)
        if cached is not None:
            return self._evaluate_flag(cached, user_id, user_role, context)

        # Get from database
        db = self._get_db()
        try:
            from database import FeatureFlag

            flag = db.query(FeatureFlag).filter_by(key=key).first()

            if flag is None:
                logger.debug(
                    f"Feature flag '{key}' not found, using default: {default}"
                )
                return default

            # Check expiration
            if flag.is_expired():
                logger.debug(f"Feature flag '{key}' has expired")
                return default

            # Update evaluation stats
            flag.last_evaluated_at = datetime.utcnow()
            flag.evaluation_count = (flag.evaluation_count or 0) + 1
            db.commit()

            # Cache the flag
            self._set_cache(key, flag.to_dict())

            return self._evaluate_flag(flag.to_dict(), user_id, user_role, context)

        except Exception as e:
            logger.error(f"Error checking feature flag '{key}': {e}")
            return default
        finally:
            if self._should_close_db():
                db.close()

    def _evaluate_flag(
        self,
        flag_data: Dict[str, Any],
        user_id: Optional[int],
        user_role: Optional[str],
        context: Optional[Dict[str, Any]],
    ) -> bool:
        """
        Evaluate a flag with targeting rules.

        Args:
            flag_data: Flag data dictionary
            user_id: User ID
            user_role: User role
            context: Additional context

        Returns:
            True if flag should be enabled for this context
        """
        # If flag is disabled, return False
        if not flag_data.get("enabled", False):
            return False

        # Check targeting rules
        rules = flag_data.get("targeting_rules")
        if not rules:
            return True  # No rules, flag is simply on

        # Check percentage rollout
        percentage = rules.get("percentage")
        if percentage is not None and user_id:
            if not self._is_in_percentage(user_id, flag_data["key"], percentage):
                return False

        # Check user whitelist
        user_whitelist = rules.get("user_ids", [])
        if user_whitelist and user_id:
            if user_id in user_whitelist:
                return True

        # Check user blacklist
        user_blacklist = rules.get("excluded_user_ids", [])
        if user_blacklist and user_id:
            if user_id in user_blacklist:
                return False

        # Check role whitelist
        role_whitelist = rules.get("roles", [])
        if role_whitelist and user_role:
            if user_role not in role_whitelist:
                return False

        # Check environment
        environments = rules.get("environments", [])
        if environments:
            import os

            current_env = os.environ.get("ENVIRONMENT", "development")
            if current_env not in environments:
                return False

        return True

    def _is_in_percentage(self, user_id: int, flag_key: str, percentage: int) -> bool:
        """
        Check if a user falls within a percentage rollout.

        Uses consistent hashing so the same user always gets the same result.

        Args:
            user_id: User ID
            flag_key: Flag key (for consistent hashing)
            percentage: Rollout percentage (0-100)

        Returns:
            True if user is in the rollout percentage
        """
        if percentage >= 100:
            return True
        if percentage <= 0:
            return False

        # Create a consistent hash
        hash_input = f"{flag_key}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        bucket = hash_value % 100

        return bucket < percentage

    # -------------------------------------------------------------------------
    # Flag Management
    # -------------------------------------------------------------------------

    def get_flag(self, key: str) -> Optional[Dict[str, Any]]:
        """Get a feature flag by key."""
        db = self._get_db()
        try:
            from database import FeatureFlag

            flag = db.query(FeatureFlag).filter_by(key=key).first()
            return flag.to_dict() if flag else None
        finally:
            if self._should_close_db():
                db.close()

    def get_all_flags(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all feature flags, optionally filtered by category."""
        db = self._get_db()
        try:
            from database import FeatureFlag

            query = db.query(FeatureFlag)
            if category:
                query = query.filter_by(category=category)
            flags = query.order_by(FeatureFlag.key).all()
            return [f.to_dict() for f in flags]
        finally:
            if self._should_close_db():
                db.close()

    def create_flag(
        self,
        key: str,
        name: str,
        description: Optional[str] = None,
        enabled: bool = False,
        category: str = "feature",
        targeting_rules: Optional[Dict] = None,
        owner: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        created_by_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create a new feature flag."""
        db = self._get_db()
        try:
            from database import FeatureFlag

            # Check if flag already exists
            existing = db.query(FeatureFlag).filter_by(key=key).first()
            if existing:
                raise ValueError(f"Feature flag with key '{key}' already exists")

            flag = FeatureFlag(
                key=key,
                name=name,
                description=description,
                enabled=enabled,
                category=category,
                targeting_rules=targeting_rules,
                owner=owner,
                expires_at=expires_at,
                created_by_id=created_by_id,
            )
            db.add(flag)
            db.commit()
            db.refresh(flag)

            # Invalidate cache
            self._invalidate_cache(key)

            logger.info(f"Created feature flag: {key}")
            return flag.to_dict()

        finally:
            if self._should_close_db():
                db.close()

    def update_flag(
        self,
        key: str,
        enabled: Optional[bool] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        targeting_rules: Optional[Dict] = None,
        category: Optional[str] = None,
        owner: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        updated_by_id: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """Update an existing feature flag."""
        db = self._get_db()
        try:
            from database import FeatureFlag

            flag = db.query(FeatureFlag).filter_by(key=key).first()
            if not flag:
                return None

            if enabled is not None:
                flag.enabled = enabled
            if name is not None:
                flag.name = name
            if description is not None:
                flag.description = description
            if targeting_rules is not None:
                flag.targeting_rules = targeting_rules
            if category is not None:
                flag.category = category
            if owner is not None:
                flag.owner = owner
            if expires_at is not None:
                flag.expires_at = expires_at
            if updated_by_id is not None:
                flag.updated_by_id = updated_by_id

            flag.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(flag)

            # Invalidate cache
            self._invalidate_cache(key)

            logger.info(f"Updated feature flag: {key}")
            return flag.to_dict()

        finally:
            if self._should_close_db():
                db.close()

    def delete_flag(self, key: str) -> bool:
        """Delete a feature flag."""
        db = self._get_db()
        try:
            from database import FeatureFlag

            flag = db.query(FeatureFlag).filter_by(key=key).first()
            if not flag:
                return False

            db.delete(flag)
            db.commit()

            # Invalidate cache
            self._invalidate_cache(key)

            logger.info(f"Deleted feature flag: {key}")
            return True

        finally:
            if self._should_close_db():
                db.close()

    def set_flag(
        self, key: str, enabled: bool, updated_by_id: Optional[int] = None
    ) -> bool:
        """Quick method to enable/disable a flag."""
        result = self.update_flag(key, enabled=enabled, updated_by_id=updated_by_id)
        return result is not None

    def toggle_flag(
        self, key: str, updated_by_id: Optional[int] = None
    ) -> Optional[bool]:
        """Toggle a flag's enabled state."""
        flag = self.get_flag(key)
        if not flag:
            return None

        new_state = not flag["enabled"]
        self.update_flag(key, enabled=new_state, updated_by_id=updated_by_id)
        return new_state

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    def initialize_default_flags(self) -> int:
        """
        Initialize default feature flags.

        Returns:
            Number of flags created
        """
        created = 0
        for flag_data in DEFAULT_FLAGS:
            try:
                self.create_flag(**flag_data)
                created += 1
            except ValueError:
                pass  # Flag already exists

        if created:
            logger.info(f"Initialized {created} default feature flags")

        return created

    # -------------------------------------------------------------------------
    # Local Overrides (for testing)
    # -------------------------------------------------------------------------

    def set_override(self, key: str, enabled: bool) -> None:
        """Set a local override for testing."""
        self._local_overrides[key] = enabled

    def clear_override(self, key: str) -> None:
        """Clear a local override."""
        self._local_overrides.pop(key, None)

    def clear_all_overrides(self) -> None:
        """Clear all local overrides."""
        self._local_overrides.clear()

    # -------------------------------------------------------------------------
    # Caching
    # -------------------------------------------------------------------------

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get flag from cache if not expired."""
        with _cache_lock:
            if key not in _cache:
                return None

            timestamp = _cache_timestamps.get(key, 0)
            if time.time() - timestamp > CACHE_TTL_SECONDS:
                del _cache[key]
                del _cache_timestamps[key]
                return None

            return _cache[key]

    def _set_cache(self, key: str, value: Dict[str, Any]) -> None:
        """Set flag in cache."""
        with _cache_lock:
            _cache[key] = value
            _cache_timestamps[key] = time.time()

    def _invalidate_cache(self, key: str) -> None:
        """Invalidate a specific cache entry."""
        with _cache_lock:
            _cache.pop(key, None)
            _cache_timestamps.pop(key, None)

    def clear_cache(self) -> None:
        """Clear entire cache."""
        with _cache_lock:
            _cache.clear()
            _cache_timestamps.clear()

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get feature flag statistics."""
        db = self._get_db()
        try:
            from sqlalchemy import func

            from database import FeatureFlag

            total = db.query(func.count(FeatureFlag.id)).scalar()
            enabled = (
                db.query(func.count(FeatureFlag.id))
                .filter(FeatureFlag.enabled == True)
                .scalar()
            )
            expired = (
                db.query(func.count(FeatureFlag.id))
                .filter(FeatureFlag.expires_at < datetime.utcnow())
                .scalar()
            )

            by_category = {}
            categories = (
                db.query(FeatureFlag.category, func.count(FeatureFlag.id))
                .group_by(FeatureFlag.category)
                .all()
            )
            for cat, count in categories:
                by_category[cat or "uncategorized"] = count

            return {
                "total_flags": total,
                "enabled_flags": enabled,
                "disabled_flags": total - enabled,
                "expired_flags": expired,
                "by_category": by_category,
                "cache_size": len(_cache),
            }

        finally:
            if self._should_close_db():
                db.close()


# =============================================================================
# Module-Level Convenience Functions
# =============================================================================

_service: Optional[FeatureFlagService] = None


def get_feature_flag_service() -> FeatureFlagService:
    """Get or create the singleton feature flag service."""
    global _service
    if _service is None:
        _service = FeatureFlagService()
    return _service


def is_enabled(
    key: str,
    user_id: Optional[int] = None,
    user_role: Optional[str] = None,
    default: bool = False,
    context: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Check if a feature flag is enabled.

    Args:
        key: Flag key
        user_id: User ID for targeting
        user_role: User role for targeting
        default: Default value if flag not found
        context: Additional context

    Returns:
        True if enabled, False otherwise

    Example:
        if is_enabled("new_feature"):
            use_new_feature()

        if is_enabled("beta", user_id=current_user.id):
            show_beta()
    """
    return get_feature_flag_service().is_enabled(
        key, user_id, user_role, default, context
    )


def feature_flag(
    key: str,
    default: bool = False,
    fallback: Optional[Callable] = None,
):
    """
    Decorator to conditionally execute a function based on a feature flag.

    Args:
        key: Feature flag key
        default: Default if flag not found
        fallback: Optional fallback function to call if flag is disabled

    Example:
        @feature_flag("new_api")
        def new_api_handler():
            return {"version": 2}

        @feature_flag("experimental", fallback=stable_handler)
        def experimental_handler():
            return {"experimental": True}
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract user context from kwargs or Flask
            user_id = kwargs.pop("_flag_user_id", None)
            user_role = kwargs.pop("_flag_user_role", None)

            # Try to get from Flask session if not provided
            if user_id is None:
                try:
                    from flask import session

                    user_id = session.get("staff_id") or session.get("client_id")
                    user_role = session.get("staff_role")
                except RuntimeError:
                    pass  # Not in Flask context

            if is_enabled(key, user_id, user_role, default):
                return func(*args, **kwargs)
            elif fallback:
                return fallback(*args, **kwargs)
            else:
                return None

        # Attach flag info for introspection
        wrapper._feature_flag = key
        return wrapper

    return decorator


class FeatureFlagContext:
    """
    Context manager for feature flags.

    Example:
        with FeatureFlagContext("new_feature") as enabled:
            if enabled:
                do_new_thing()
            else:
                do_old_thing()
    """

    def __init__(
        self,
        key: str,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        default: bool = False,
    ):
        self.key = key
        self.user_id = user_id
        self.user_role = user_role
        self.default = default
        self.enabled = False

    def __enter__(self) -> bool:
        self.enabled = is_enabled(
            self.key,
            self.user_id,
            self.user_role,
            self.default,
        )
        return self.enabled

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # Service
    "FeatureFlagService",
    "get_feature_flag_service",
    # Convenience functions
    "is_enabled",
    "feature_flag",
    "FeatureFlagContext",
    # Constants
    "FLAG_CATEGORIES",
    "DEFAULT_FLAGS",
    "CACHE_TTL_SECONDS",
]
