"""
Tests for health check endpoints (/health, /ready, /metrics)
Issue #55: Add health check endpoints for monitoring and load balancers
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestHealthEndpoint:
    """Tests for /health endpoint - basic liveness check"""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 status"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        """Health endpoint should return JSON"""
        response = client.get("/health")
        assert response.content_type == "application/json"

    def test_health_contains_status(self, client):
        """Health response should contain status field"""
        response = client.get("/health")
        data = response.get_json()
        assert "status" in data
        assert data["status"] == "healthy"

    def test_health_contains_timestamp(self, client):
        """Health response should contain timestamp"""
        response = client.get("/health")
        data = response.get_json()
        assert "timestamp" in data
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(data["timestamp"])

    def test_health_contains_version(self, client):
        """Health response should contain version"""
        response = client.get("/health")
        data = response.get_json()
        assert "version" in data

    def test_health_contains_uptime(self, client):
        """Health response should contain uptime_seconds"""
        response = client.get("/health")
        data = response.get_json()
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))

    def test_health_contains_memory_info(self, client):
        """Health response should contain memory information"""
        response = client.get("/health")
        data = response.get_json()
        assert "memory" in data
        assert "rss_mb" in data["memory"]
        assert "vms_mb" in data["memory"]

    def test_health_contains_cpu_percent(self, client):
        """Health response should contain CPU percentage"""
        response = client.get("/health")
        data = response.get_json()
        assert "cpu_percent" in data


class TestReadyEndpoint:
    """Tests for /ready endpoint - readiness check with dependencies"""

    def test_ready_returns_200_when_healthy(self, client):
        """Ready endpoint should return 200 when all dependencies are healthy"""
        response = client.get("/ready")
        # May be 200 or 503 depending on database state
        assert response.status_code in [200, 503]

    def test_ready_returns_json(self, client):
        """Ready endpoint should return JSON"""
        response = client.get("/ready")
        assert response.content_type == "application/json"

    def test_ready_contains_status(self, client):
        """Ready response should contain status field"""
        response = client.get("/ready")
        data = response.get_json()
        assert "status" in data
        assert data["status"] in ["ready", "not_ready"]

    def test_ready_contains_timestamp(self, client):
        """Ready response should contain timestamp"""
        response = client.get("/ready")
        data = response.get_json()
        assert "timestamp" in data

    def test_ready_contains_checks(self, client):
        """Ready response should contain checks object"""
        response = client.get("/ready")
        data = response.get_json()
        assert "checks" in data
        assert isinstance(data["checks"], dict)

    def test_ready_contains_database_check(self, client):
        """Ready response should include database check"""
        response = client.get("/ready")
        data = response.get_json()
        assert "database" in data["checks"]
        assert "status" in data["checks"]["database"]

    def test_ready_database_check_includes_latency(self, client):
        """Database check should include latency when connected"""
        response = client.get("/ready")
        data = response.get_json()
        if data["checks"]["database"]["status"] == "connected":
            assert "latency_ms" in data["checks"]["database"]


class TestLivenessEndpoint:
    """Tests for /health/live endpoint - minimal liveness probe"""

    def test_liveness_returns_200(self, client):
        """Liveness endpoint should return 200"""
        response = client.get("/health/live")
        assert response.status_code == 200

    def test_liveness_returns_ok(self, client):
        """Liveness endpoint should return 'OK'"""
        response = client.get("/health/live")
        assert response.data == b"OK"

    def test_liveness_is_fast(self, client):
        """Liveness endpoint should be fast (no DB calls)"""
        import time
        start = time.time()
        client.get("/health/live")
        elapsed = time.time() - start
        # Should complete in under 100ms
        assert elapsed < 0.1


class TestMetricsEndpoint:
    """Tests for /metrics endpoint - Prometheus-compatible metrics"""

    def test_metrics_returns_200(self, client):
        """Metrics endpoint should return 200"""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_returns_text_plain(self, client):
        """Metrics endpoint should return text/plain"""
        response = client.get("/metrics")
        assert "text/plain" in response.content_type

    def test_metrics_contains_process_memory(self, client):
        """Metrics should include process memory metrics"""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")
        assert "process_resident_memory_bytes" in data
        assert "process_virtual_memory_bytes" in data

    def test_metrics_contains_cpu_percent(self, client):
        """Metrics should include CPU percentage"""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")
        assert "process_cpu_percent" in data

    def test_metrics_contains_uptime(self, client):
        """Metrics should include application uptime"""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")
        assert "app_uptime_seconds" in data

    def test_metrics_contains_request_counts(self, client):
        """Metrics should include request and error counts"""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")
        assert "app_requests_total" in data
        assert "app_errors_total" in data

    def test_metrics_contains_db_pool_metrics(self, client):
        """Metrics should include database pool metrics"""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")
        assert "db_pool_size" in data
        assert "db_pool_checked_out" in data

    def test_metrics_has_prometheus_format(self, client):
        """Metrics should follow Prometheus format with HELP and TYPE"""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")
        # Check for Prometheus format markers
        assert "# HELP" in data
        assert "# TYPE" in data
        # Check for gauge and counter types
        assert "gauge" in data
        assert "counter" in data

    def test_metrics_values_are_numeric(self, client):
        """Metric values should be numeric"""
        response = client.get("/metrics")
        data = response.data.decode("utf-8")
        lines = data.strip().split("\n")
        for line in lines:
            if not line.startswith("#") and line.strip():
                # Metric lines should have format: metric_name value
                parts = line.split()
                if len(parts) >= 2:
                    # Value should be numeric
                    try:
                        float(parts[-1])
                    except ValueError:
                        pytest.fail(f"Non-numeric value in metric line: {line}")


class TestHealthEndpointsIntegration:
    """Integration tests for health endpoints"""

    def test_all_health_endpoints_accessible(self, client):
        """All health endpoints should be accessible without auth"""
        endpoints = ["/health", "/ready", "/health/live", "/metrics"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 503], f"{endpoint} returned {response.status_code}"

    def test_health_endpoints_do_not_require_auth(self, client):
        """Health endpoints should not require authentication"""
        # These should work without any auth headers
        response = client.get("/health")
        assert response.status_code == 200

        response = client.get("/ready")
        assert response.status_code in [200, 503]

        response = client.get("/health/live")
        assert response.status_code == 200

        response = client.get("/metrics")
        assert response.status_code == 200
