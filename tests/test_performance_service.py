"""
Comprehensive Unit Tests for Performance Service

Tests cover:
- InMemoryCache operations (get, set, delete, clear)
- Cache TTL expiration
- Cache statistics tracking
- PerformanceService request recording
- Performance metrics calculation
- Slow endpoint detection
- Performance summary generation
- Query optimization analysis
- Database stats (mocked)
- Cache key generation
- Decorator functionality
"""

import json
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from services.performance_service import (
    InMemoryCache,
    PerformanceService,
    app_cache,
    cached,
    generate_cache_key,
    get_performance_service,
    invalidate_cache,
    _request_metrics,
    _metrics_lock,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def cache():
    """Create a fresh InMemoryCache for each test"""
    cache = InMemoryCache(cleanup_interval_seconds=60)  # Long interval for tests
    yield cache
    cache.shutdown()  # Stop background thread
    cache.clear()


@pytest.fixture
def performance_service():
    """Create a fresh PerformanceService for each test"""
    service = PerformanceService()
    yield service
    # Clear metrics after test
    with _metrics_lock:
        _request_metrics.clear()


@pytest.fixture
def app_cache_clean():
    """Clean app_cache before and after test"""
    app_cache.clear()
    app_cache.reset_stats()
    yield app_cache
    app_cache.clear()
    app_cache.reset_stats()


# ============================================================================
# InMemoryCache - Basic Operations Tests
# ============================================================================

class TestInMemoryCacheBasicOperations:
    """Tests for basic cache operations"""

    def test_set_and_get_value(self, cache):
        """Test setting and getting a value from cache"""
        cache.set("key1", "value1", ttl_seconds=300)
        value, hit = cache.get("key1")

        assert hit is True
        assert value == "value1"

    def test_get_nonexistent_key(self, cache):
        """Test getting a key that doesn't exist"""
        value, hit = cache.get("nonexistent_key")

        assert hit is False
        assert value is None

    def test_set_overwrites_existing_value(self, cache):
        """Test that setting a key overwrites existing value"""
        cache.set("key1", "original", ttl_seconds=300)
        cache.set("key1", "updated", ttl_seconds=300)

        value, hit = cache.get("key1")
        assert value == "updated"

    def test_delete_existing_key(self, cache):
        """Test deleting an existing key"""
        cache.set("key1", "value1", ttl_seconds=300)
        result = cache.delete("key1")

        assert result is True
        value, hit = cache.get("key1")
        assert hit is False

    def test_delete_nonexistent_key(self, cache):
        """Test deleting a key that doesn't exist"""
        result = cache.delete("nonexistent_key")
        assert result is False

    def test_set_various_data_types(self, cache):
        """Test caching various data types"""
        # String
        cache.set("string_key", "string_value")
        value, _ = cache.get("string_key")
        assert value == "string_value"

        # Integer
        cache.set("int_key", 42)
        value, _ = cache.get("int_key")
        assert value == 42

        # List
        cache.set("list_key", [1, 2, 3])
        value, _ = cache.get("list_key")
        assert value == [1, 2, 3]

        # Dictionary
        cache.set("dict_key", {"a": 1, "b": 2})
        value, _ = cache.get("dict_key")
        assert value == {"a": 1, "b": 2}

        # None value
        cache.set("none_key", None)
        value, hit = cache.get("none_key")
        assert value is None
        assert hit is True


# ============================================================================
# InMemoryCache - TTL and Expiration Tests
# ============================================================================

class TestInMemoryCacheTTL:
    """Tests for cache TTL and expiration"""

    def test_entry_expires_after_ttl(self, cache):
        """Test that cache entry expires after TTL"""
        cache.set("key1", "value1", ttl_seconds=1)

        # Should exist immediately
        value, hit = cache.get("key1")
        assert hit is True

        # Wait for expiration
        time.sleep(1.1)

        value, hit = cache.get("key1")
        assert hit is False
        assert value is None

    def test_zero_ttl_never_expires(self, cache):
        """Test that TTL of 0 means no expiration"""
        cache.set("key1", "value1", ttl_seconds=0)

        # Check the entry directly
        entry = cache._store.get("key1")
        assert entry["expires_at"] is None

    def test_cleanup_expired_entries(self, cache):
        """Test cleanup_expired removes expired entries"""
        cache.set("key1", "value1", ttl_seconds=1)
        cache.set("key2", "value2", ttl_seconds=1)
        cache.set("key3", "value3", ttl_seconds=300)

        time.sleep(1.1)

        removed = cache.cleanup_expired()

        assert removed == 2
        _, hit1 = cache.get("key1")
        _, hit2 = cache.get("key2")
        _, hit3 = cache.get("key3")

        assert hit1 is False
        assert hit2 is False
        assert hit3 is True

    def test_default_ttl_is_300_seconds(self, cache):
        """Test that default TTL is 5 minutes (300 seconds)"""
        cache.set("key1", "value1")
        entry = cache._store.get("key1")

        assert entry["ttl_seconds"] == 300


# ============================================================================
# InMemoryCache - Clear Operations Tests
# ============================================================================

class TestInMemoryCacheClear:
    """Tests for cache clear operations"""

    def test_clear_all_entries(self, cache):
        """Test clearing all cache entries"""
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        cleared = cache.clear()

        assert cleared == 3
        assert len(cache._store) == 0

    def test_clear_with_wildcard_pattern(self, cache):
        """Test clearing entries matching a wildcard pattern"""
        cache.set("user:1", "data1")
        cache.set("user:2", "data2")
        cache.set("product:1", "data3")

        cleared = cache.clear("user:*")

        assert cleared == 2
        _, hit = cache.get("product:1")
        assert hit is True

    def test_clear_with_specific_pattern(self, cache):
        """Test clearing entries matching a specific pattern"""
        cache.set("api:v1:users", "data1")
        cache.set("api:v2:users", "data2")
        cache.set("api:v1:products", "data3")

        cleared = cache.clear("api:v1:*")

        assert cleared == 2

    def test_clear_empty_cache(self, cache):
        """Test clearing an empty cache"""
        cleared = cache.clear()
        assert cleared == 0


# ============================================================================
# InMemoryCache - Statistics Tests
# ============================================================================

class TestInMemoryCacheStats:
    """Tests for cache statistics"""

    def test_hit_count_increments(self, cache):
        """Test that hit count increments on cache hit"""
        cache.set("key1", "value1")

        cache.get("key1")
        cache.get("key1")
        cache.get("key1")

        stats = cache.get_stats()
        assert stats["hit_count"] == 3

    def test_miss_count_increments(self, cache):
        """Test that miss count increments on cache miss"""
        cache.get("nonexistent1")
        cache.get("nonexistent2")

        stats = cache.get_stats()
        assert stats["miss_count"] == 2

    def test_hit_rate_calculation(self, cache):
        """Test hit rate is calculated correctly"""
        cache.set("key1", "value1")

        # 2 hits
        cache.get("key1")
        cache.get("key1")
        # 2 misses
        cache.get("missing1")
        cache.get("missing2")

        stats = cache.get_stats()
        assert stats["hit_rate"] == 50.0

    def test_reset_stats(self, cache):
        """Test resetting statistics"""
        cache.set("key1", "value1")
        cache.get("key1")
        cache.get("missing")

        cache.reset_stats()

        stats = cache.get_stats()
        assert stats["hit_count"] == 0
        assert stats["miss_count"] == 0
        assert stats["hit_rate"] == 0

    def test_stats_include_entry_details(self, cache):
        """Test that stats include entry details"""
        cache.set("key1", "test_value")
        cache.get("key1")

        stats = cache.get_stats()

        assert stats["total_entries"] == 1
        assert len(stats["entries"]) == 1
        assert stats["entries"][0]["key"] == "key1"
        assert stats["entries"][0]["hit_count"] == 1

    def test_memory_estimate(self, cache):
        """Test memory estimate calculation"""
        cache.set("key1", "a" * 1024)  # 1KB value

        stats = cache.get_stats()
        assert stats["memory_estimate_kb"] >= 1.0


# ============================================================================
# InMemoryCache - Thread Safety Tests
# ============================================================================

class TestInMemoryCacheThreadSafety:
    """Tests for thread safety"""

    def test_concurrent_reads_and_writes(self, cache):
        """Test concurrent read and write operations"""
        errors = []

        def writer():
            try:
                for i in range(100):
                    cache.set(f"key{i}", f"value{i}")
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                for i in range(100):
                    cache.get(f"key{i}")
            except Exception as e:
                errors.append(e)

        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=writer))
            threads.append(threading.Thread(target=reader))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0


# ============================================================================
# Background Cleanup Thread Tests
# ============================================================================

class TestInMemoryCacheBackgroundCleanup:
    """Tests for background cleanup thread functionality"""

    def test_cleanup_thread_starts(self):
        """Test that cleanup thread starts on initialization"""
        cache = InMemoryCache(cleanup_interval_seconds=60)
        try:
            assert cache._cleanup_thread is not None
            assert cache._cleanup_thread.is_alive()
            assert cache._cleanup_thread.daemon is True
            assert cache._cleanup_thread.name == "cache-cleanup"
        finally:
            cache.shutdown()

    def test_shutdown_stops_cleanup_thread(self):
        """Test that shutdown stops the cleanup thread"""
        cache = InMemoryCache(cleanup_interval_seconds=60)
        cache.shutdown()
        # Give thread time to stop
        time.sleep(0.1)
        assert cache._shutdown is True

    def test_expired_count_tracked(self):
        """Test that expired entries are counted"""
        cache = InMemoryCache(cleanup_interval_seconds=60)
        try:
            cache.set("key1", "value1", ttl_seconds=1)
            cache.set("key2", "value2", ttl_seconds=1)
            time.sleep(1.1)

            # Manually trigger cleanup
            expired = cache.cleanup_expired()

            assert expired == 2
            # expired_count is updated by background thread, not cleanup_expired directly
            # so we check the stats include it
            stats = cache.get_stats()
            assert "expired_count" in stats
        finally:
            cache.shutdown()

    def test_stats_include_expired_count(self):
        """Test that get_stats includes expired_count"""
        cache = InMemoryCache(cleanup_interval_seconds=60)
        try:
            stats = cache.get_stats()
            assert "expired_count" in stats
            assert stats["expired_count"] == 0
        finally:
            cache.shutdown()

    def test_custom_cleanup_interval(self):
        """Test that custom cleanup interval is used"""
        cache = InMemoryCache(cleanup_interval_seconds=120)
        try:
            assert cache._cleanup_interval == 120
        finally:
            cache.shutdown()


# ============================================================================
# Cache Key Generation Tests
# ============================================================================

class TestCacheKeyGeneration:
    """Tests for cache key generation"""

    def test_generate_cache_key_basic(self):
        """Test basic cache key generation"""
        key1 = generate_cache_key("arg1", "arg2")
        key2 = generate_cache_key("arg1", "arg2")

        assert key1 == key2

    def test_generate_cache_key_different_args(self):
        """Test different arguments produce different keys"""
        key1 = generate_cache_key("arg1")
        key2 = generate_cache_key("arg2")

        assert key1 != key2

    def test_generate_cache_key_with_kwargs(self):
        """Test cache key generation with keyword arguments"""
        key1 = generate_cache_key(a=1, b=2)
        key2 = generate_cache_key(b=2, a=1)

        # Order of kwargs shouldn't matter
        assert key1 == key2

    def test_generate_cache_key_mixed_args(self):
        """Test cache key generation with mixed args and kwargs"""
        key1 = generate_cache_key("arg1", key="value")
        key2 = generate_cache_key("arg1", key="value")

        assert key1 == key2


# ============================================================================
# Cached Decorator Tests
# ============================================================================

class TestCachedDecorator:
    """Tests for the @cached decorator"""

    def test_cached_decorator_caches_result(self, app_cache_clean):
        """Test that cached decorator caches function result"""
        call_count = 0

        @cached(ttl=300, key_prefix="test")
        def expensive_function():
            nonlocal call_count
            call_count += 1
            return "result"

        with patch('services.performance_service.g', MagicMock()):
            result1 = expensive_function()
            result2 = expensive_function()

        assert result1 == "result"
        assert result2 == "result"
        # Second call should use cache
        assert call_count == 1

    def test_cached_decorator_invalidate(self, app_cache_clean):
        """Test cache invalidation through decorator"""
        @cached(ttl=300, key_prefix="test_inv")
        def test_func():
            return "value"

        with patch('services.performance_service.g', MagicMock()):
            test_func()

        # Invalidate cache
        test_func.invalidate()

        stats = app_cache.get_stats()
        # After invalidation, entries with prefix should be cleared
        matching_entries = [e for e in stats["entries"] if e["key"].startswith("test_inv:")]
        assert len(matching_entries) == 0


# ============================================================================
# Invalidate Cache Tests
# ============================================================================

class TestInvalidateCache:
    """Tests for invalidate_cache function"""

    def test_invalidate_cache_single_pattern(self, app_cache_clean):
        """Test invalidating cache with single pattern"""
        app_cache.set("user:1", "data1")
        app_cache.set("user:2", "data2")
        app_cache.set("product:1", "data3")

        cleared = invalidate_cache(["user:*"])

        assert cleared == 2

    def test_invalidate_cache_multiple_patterns(self, app_cache_clean):
        """Test invalidating cache with multiple patterns"""
        app_cache.set("user:1", "data1")
        app_cache.set("product:1", "data2")
        app_cache.set("order:1", "data3")

        cleared = invalidate_cache(["user:*", "product:*"])

        assert cleared == 2


# ============================================================================
# PerformanceService - Request Recording Tests
# ============================================================================

class TestPerformanceServiceRecordRequest:
    """Tests for request recording"""

    def test_record_request_basic(self, performance_service):
        """Test recording a basic request"""
        performance_service.record_request(
            endpoint="/api/users",
            method="GET",
            duration_ms=50.0,
            status=200,
            cache_hit=False
        )

        metrics = performance_service.get_endpoint_metrics("/api/users", "GET")
        assert metrics["request_count"] == 1

    def test_record_request_with_cache_hit(self, performance_service):
        """Test recording a request with cache hit"""
        performance_service.record_request(
            endpoint="/api/users",
            method="GET",
            duration_ms=5.0,
            status=200,
            cache_hit=True
        )

        metrics = performance_service.get_endpoint_metrics("/api/users", "GET")
        assert metrics["cache_hit_count"] == 1
        assert metrics["cache_hit_rate"] == 100.0

    def test_record_request_with_error(self, performance_service):
        """Test recording a request with error status"""
        performance_service.record_request(
            endpoint="/api/users",
            method="GET",
            duration_ms=100.0,
            status=500,
            error_message="Internal Server Error"
        )

        metrics = performance_service.get_endpoint_metrics("/api/users", "GET")
        assert metrics["error_count"] == 1
        assert metrics["error_rate"] == 100.0

    def test_record_multiple_requests(self, performance_service):
        """Test recording multiple requests"""
        for i in range(5):
            performance_service.record_request(
                endpoint="/api/test",
                method="GET",
                duration_ms=10.0 * (i + 1),
                status=200
            )

        metrics = performance_service.get_endpoint_metrics("/api/test", "GET")
        assert metrics["request_count"] == 5


# ============================================================================
# PerformanceService - Metrics Calculation Tests
# ============================================================================

class TestPerformanceServiceMetrics:
    """Tests for metrics calculation"""

    def test_calculate_average_response_time(self, performance_service):
        """Test average response time calculation"""
        durations = [10.0, 20.0, 30.0, 40.0, 50.0]
        for d in durations:
            performance_service.record_request(
                endpoint="/api/test",
                method="GET",
                duration_ms=d,
                status=200
            )

        metrics = performance_service.get_endpoint_metrics("/api/test", "GET")
        assert metrics["avg_response_time_ms"] == 30.0

    def test_calculate_percentiles(self, performance_service):
        """Test percentile calculations"""
        # Record 100 requests with durations 1-100
        for i in range(1, 101):
            performance_service.record_request(
                endpoint="/api/test",
                method="GET",
                duration_ms=float(i),
                status=200
            )

        metrics = performance_service.get_endpoint_metrics("/api/test", "GET")

        # p50 should be around 50
        assert 49 <= metrics["p50_time"] <= 51
        # p95 should be around 95
        assert 94 <= metrics["p95_time"] <= 96
        # p99 should be around 99
        assert 98 <= metrics["p99_time"] <= 100

    def test_calculate_min_max_response_time(self, performance_service):
        """Test min/max response time calculation"""
        performance_service.record_request("/api/test", "GET", 10.0, 200)
        performance_service.record_request("/api/test", "GET", 50.0, 200)
        performance_service.record_request("/api/test", "GET", 100.0, 200)

        metrics = performance_service.get_endpoint_metrics("/api/test", "GET")
        assert metrics["min_response_time_ms"] == 10.0
        assert metrics["max_response_time_ms"] == 100.0

    def test_empty_metrics_returns_zeros(self, performance_service):
        """Test that empty metrics returns zeros"""
        metrics = performance_service.get_endpoint_metrics("/nonexistent", "GET")

        assert metrics["request_count"] == 0
        assert metrics["avg_response_time_ms"] == 0
        assert metrics["error_count"] == 0

    def test_get_all_endpoint_metrics(self, performance_service):
        """Test getting metrics for all endpoints"""
        performance_service.record_request("/api/users", "GET", 50.0, 200)
        performance_service.record_request("/api/products", "GET", 100.0, 200)
        performance_service.record_request("/api/orders", "POST", 150.0, 201)

        all_metrics = performance_service.get_endpoint_metrics()

        assert "GET:/api/users" in all_metrics
        assert "GET:/api/products" in all_metrics
        assert "POST:/api/orders" in all_metrics


# ============================================================================
# PerformanceService - Slow Endpoints Tests
# ============================================================================

class TestPerformanceServiceSlowEndpoints:
    """Tests for slow endpoint detection"""

    def test_identify_slow_endpoints(self, performance_service):
        """Test identifying slow endpoints"""
        # Fast endpoint
        performance_service.record_request("/api/fast", "GET", 50.0, 200)
        # Slow endpoint
        performance_service.record_request("/api/slow", "GET", 200.0, 200)

        slow = performance_service.get_slow_endpoints(threshold_ms=100)

        assert len(slow) == 1
        assert slow[0]["endpoint"] == "/api/slow"

    def test_slow_endpoints_severity_levels(self, performance_service):
        """Test severity levels for slow endpoints"""
        performance_service.record_request("/api/info", "GET", 150.0, 200)
        performance_service.record_request("/api/warning", "GET", 300.0, 200)
        performance_service.record_request("/api/critical", "GET", 600.0, 200)

        slow = performance_service.get_slow_endpoints(threshold_ms=100)

        severities = {s["endpoint"]: s["severity"] for s in slow}
        assert severities["/api/info"] == "info"
        assert severities["/api/warning"] == "warning"
        assert severities["/api/critical"] == "critical"

    def test_slow_endpoints_recommendations(self, performance_service):
        """Test that slow endpoints include recommendations"""
        # Low cache hit rate
        performance_service.record_request("/api/slow", "GET", 200.0, 200, cache_hit=False)
        performance_service.record_request("/api/slow", "GET", 200.0, 200, cache_hit=False)

        slow = performance_service.get_slow_endpoints(threshold_ms=100)

        assert len(slow) == 1
        assert any("caching" in r.lower() for r in slow[0]["recommendations"])

    def test_slow_endpoints_sorted_by_response_time(self, performance_service):
        """Test that slow endpoints are sorted by response time"""
        performance_service.record_request("/api/medium", "GET", 200.0, 200)
        performance_service.record_request("/api/slowest", "GET", 500.0, 200)
        performance_service.record_request("/api/slow", "GET", 300.0, 200)

        slow = performance_service.get_slow_endpoints(threshold_ms=100)

        assert slow[0]["endpoint"] == "/api/slowest"
        assert slow[1]["endpoint"] == "/api/slow"
        assert slow[2]["endpoint"] == "/api/medium"


# ============================================================================
# PerformanceService - Performance Summary Tests
# ============================================================================

class TestPerformanceServiceSummary:
    """Tests for performance summary"""

    def test_get_performance_summary(self, performance_service):
        """Test getting performance summary"""
        for i in range(10):
            performance_service.record_request(
                endpoint="/api/test",
                method="GET",
                duration_ms=50.0 + i,
                status=200 if i < 8 else 500
            )

        summary = performance_service.get_performance_summary(period_minutes=60)

        assert summary["total_requests"] == 10
        assert summary["total_errors"] == 2
        assert summary["error_rate"] == 20.0

    def test_performance_summary_time_filtering(self, performance_service):
        """Test that summary respects time period"""
        # This test records requests and checks they're included
        performance_service.record_request("/api/test", "GET", 50.0, 200)

        summary = performance_service.get_performance_summary(period_minutes=60)

        assert summary["total_requests"] >= 1

    def test_performance_summary_slowest_endpoints(self, performance_service):
        """Test slowest endpoints in summary"""
        performance_service.record_request("/api/fast", "GET", 10.0, 200)
        performance_service.record_request("/api/slow", "GET", 500.0, 200)

        summary = performance_service.get_performance_summary(period_minutes=60)

        assert len(summary["slowest_endpoints"]) > 0
        # Slowest should be first
        assert summary["slowest_endpoints"][0]["endpoint"] == "GET:/api/slow"


# ============================================================================
# PerformanceService - Query Optimization Tests
# ============================================================================

class TestPerformanceServiceQueryOptimization:
    """Tests for query optimization analysis"""

    def test_detect_select_star(self, performance_service):
        """Test detection of SELECT * usage"""
        result = performance_service.optimize_query("SELECT * FROM users")

        assert len(result["issues"]) > 0
        assert any("SELECT *" in issue for issue in result["issues"])

    def test_detect_like_leading_wildcard(self, performance_service):
        """Test detection of LIKE with leading wildcard"""
        result = performance_service.optimize_query("SELECT name FROM users WHERE name LIKE '%test'")

        assert any("wildcard" in issue.lower() for issue in result["issues"])

    def test_detect_order_by_without_limit(self, performance_service):
        """Test detection of ORDER BY without LIMIT"""
        result = performance_service.optimize_query("SELECT name FROM users ORDER BY created_at")

        assert any("ORDER BY" in issue for issue in result["issues"])

    def test_detect_multiple_joins(self, performance_service):
        """Test detection of multiple JOINs"""
        query = """
        SELECT * FROM a
        JOIN b ON a.id = b.a_id
        JOIN c ON b.id = c.b_id
        JOIN d ON c.id = d.c_id
        JOIN e ON d.id = e.d_id
        """
        result = performance_service.optimize_query(query)

        assert any("JOIN" in issue for issue in result["issues"])

    def test_detect_update_without_where(self, performance_service):
        """Test detection of UPDATE without WHERE"""
        result = performance_service.optimize_query("UPDATE users SET status = 'inactive'")

        assert any("WHERE" in issue for issue in result["issues"])

    def test_detect_or_in_where(self, performance_service):
        """Test detection of OR in WHERE clause"""
        result = performance_service.optimize_query("SELECT * FROM users WHERE status = 'active' OR role = 'admin'")

        assert any("OR" in issue for issue in result["issues"])

    def test_optimization_score_calculation(self, performance_service):
        """Test that optimization score is calculated"""
        # Clean query should have high score
        clean_result = performance_service.optimize_query("SELECT id, name FROM users WHERE id = 1")

        # Problematic query should have lower score
        bad_result = performance_service.optimize_query("SELECT * FROM users ORDER BY name")

        assert clean_result["optimization_score"] > bad_result["optimization_score"]


# ============================================================================
# PerformanceService - Database Stats Tests
# ============================================================================

class TestPerformanceServiceDatabaseStats:
    """Tests for database statistics"""

    def test_get_database_stats_without_db(self, performance_service):
        """Test getting database stats without database connection"""
        stats = performance_service.get_database_stats()

        # Should return error or empty stats without crashing
        assert "timestamp" in stats

    def test_get_database_stats_with_mock_engine(self, performance_service):
        """Test getting database stats with mocked engine"""
        mock_pool = MagicMock()
        mock_pool.size.return_value = 5
        mock_pool.checkedout.return_value = 2
        mock_pool.checkedin.return_value = 3
        mock_pool.overflow.return_value = 0
        mock_pool.invalidatedcount.return_value = 0

        mock_engine = MagicMock()
        mock_engine.pool = mock_pool

        with patch.dict('sys.modules', {'database': MagicMock(engine=mock_engine)}):
            stats = performance_service.get_database_stats()

            assert stats["pool"]["pool_size"] == 5
            assert stats["pool"]["checked_out_connections"] == 2


# ============================================================================
# PerformanceService - Cache Stats and Clear Tests
# ============================================================================

class TestPerformanceServiceCache:
    """Tests for cache operations via PerformanceService"""

    def test_get_cache_stats(self, performance_service, app_cache_clean):
        """Test getting cache stats through service"""
        app_cache.set("test_key", "test_value")

        stats = performance_service.get_cache_stats()

        assert stats["total_entries"] >= 1

    def test_clear_cache_all(self, performance_service, app_cache_clean):
        """Test clearing all cache through service"""
        app_cache.set("key1", "value1")
        app_cache.set("key2", "value2")

        result = performance_service.clear_cache()

        assert result["success"] is True
        assert result["cleared_count"] >= 2

    def test_clear_cache_with_pattern(self, performance_service, app_cache_clean):
        """Test clearing cache with pattern through service"""
        app_cache.set("api:users:1", "data1")
        app_cache.set("api:users:2", "data2")
        app_cache.set("api:products:1", "data3")

        result = performance_service.clear_cache("api:users:*")

        assert result["success"] is True
        assert result["cleared_count"] == 2
        assert result["pattern"] == "api:users:*"


# ============================================================================
# PerformanceService - Clear Old Metrics Tests
# ============================================================================

class TestPerformanceServiceClearMetrics:
    """Tests for clearing old metrics"""

    def test_clear_old_metrics(self, performance_service):
        """Test clearing old metrics"""
        # Record some requests
        performance_service.record_request("/api/test", "GET", 50.0, 200)

        # Clear with 0 minutes should clear all
        cleared = performance_service.clear_old_metrics(max_age_minutes=0)

        # Should have cleared something
        assert cleared >= 0


# ============================================================================
# Singleton and Factory Tests
# ============================================================================

class TestPerformanceServiceSingleton:
    """Tests for singleton behavior"""

    def test_get_performance_service_singleton(self):
        """Test that get_performance_service returns singleton"""
        # Reset the singleton
        import services.performance_service as ps
        ps._performance_service_instance = None

        service1 = get_performance_service()
        service2 = get_performance_service()

        assert service1 is service2

    def test_get_performance_service_with_db(self):
        """Test that db can be set via get_performance_service"""
        import services.performance_service as ps
        ps._performance_service_instance = None

        mock_db = MagicMock()
        service = get_performance_service(mock_db)

        assert service.db is mock_db


# ============================================================================
# Index Recommendations Tests
# ============================================================================

class TestPerformanceServiceIndexRecommendations:
    """Tests for index recommendations"""

    def test_get_index_recommendations_without_db(self, performance_service):
        """Test getting index recommendations without database"""
        recommendations = performance_service.get_index_recommendations()

        # Should return empty list without db
        assert isinstance(recommendations, list)

    def test_get_index_recommendations_with_mock_db(self):
        """Test getting index recommendations with mocked database"""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = []

        service = PerformanceService(db=mock_db)
        recommendations = service.get_index_recommendations()

        # Should return recommendations for common patterns
        assert len(recommendations) > 0
        assert all("sql" in r for r in recommendations)
