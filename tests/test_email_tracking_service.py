"""
Unit tests for the Email Tracking Service.

Tests cover:
- Tracking ID generation and management
- HTML injection (pixel + link rewriting)
- Open event recording
- Click event recording
- Statistics
- Recent emails listing
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from services.email_tracking_service import (
    EmailTrackingService,
    get_email_tracking_service,
    generate_tracking_id,
    TRACKING_PIXEL,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """Create an email tracking service with a mock database."""
    return EmailTrackingService(db_session=mock_db)


@pytest.fixture
def mock_email_log():
    """Create a mock email log object."""
    log = MagicMock()
    log.id = 1
    log.email_address = "test@example.com"
    log.subject = "Test Email"
    log.template_type = "welcome"
    log.status = "sent"
    log.tracking_id = "abc123def456"
    log.opened_at = None
    log.open_count = 0
    log.clicked_at = None
    log.click_count = 0
    log.sent_at = datetime.utcnow()
    return log


# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_tracking_pixel_is_bytes(self):
        assert isinstance(TRACKING_PIXEL, bytes)

    def test_tracking_pixel_is_gif(self):
        assert TRACKING_PIXEL[:3] == b"GIF"

    def test_tracking_pixel_length(self):
        assert len(TRACKING_PIXEL) == 43

    def test_generate_tracking_id(self):
        tid = generate_tracking_id()
        assert isinstance(tid, str)
        assert len(tid) == 64  # SHA256 hex

    def test_generate_tracking_id_unique(self):
        ids = {generate_tracking_id() for _ in range(10)}
        assert len(ids) == 10


# =============================================================================
# Service Initialization Tests
# =============================================================================


class TestServiceInitialization:

    def test_init_with_db_session(self, mock_db):
        service = EmailTrackingService(db_session=mock_db)
        assert service._db == mock_db
        assert service._owns_session is False

    def test_init_without_db_session(self):
        service = EmailTrackingService()
        assert service._db is None
        assert service._owns_session is True

    def test_should_close_db(self, service):
        assert service._should_close_db() is False


# =============================================================================
# Create Tracking ID Tests
# =============================================================================


class TestCreateTrackingId:

    def test_create_tracking_id_success(self, service, mock_db, mock_email_log):
        mock_email_log.tracking_id = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_email_log

        result = service.create_tracking_id(1)

        assert result["success"] is True
        assert "tracking_id" in result
        mock_db.commit.assert_called_once()

    def test_create_tracking_id_already_exists(self, service, mock_db, mock_email_log):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_email_log

        result = service.create_tracking_id(1)

        assert result["success"] is True
        assert result["tracking_id"] == "abc123def456"

    def test_create_tracking_id_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.create_tracking_id(999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# HTML Injection Tests
# =============================================================================


class TestInjectTracking:

    def test_inject_pixel_before_body(self, service):
        html = "<html><body><p>Hello</p></body></html>"
        result = service.inject_tracking(html, "track123", "https://app.example.com")

        assert 'src="https://app.example.com/api/email/track/open/track123"' in result
        assert "width=\"1\"" in result
        assert result.index("track/open") < result.index("</body>")

    def test_inject_pixel_no_body_tag(self, service):
        html = "<p>Hello</p>"
        result = service.inject_tracking(html, "track123", "https://app.example.com")

        assert "track/open/track123" in result

    def test_rewrite_links(self, service):
        html = '<a href="https://example.com/page">Click</a>'
        result = service.inject_tracking(html, "track123", "https://app.example.com")

        assert "track/click/track123" in result
        assert "url=" in result

    def test_skip_mailto_links(self, service):
        html = '<a href="mailto:test@example.com">Email</a>'
        result = service.inject_tracking(html, "track123", "https://app.example.com")

        assert "mailto:test@example.com" in result
        assert "track/click" not in result.split("track/open")[0]

    def test_skip_tel_links(self, service):
        html = '<a href="tel:5551234">Call</a>'
        result = service.inject_tracking(html, "track123", "https://app.example.com")

        assert "tel:5551234" in result

    def test_skip_anchor_links(self, service):
        html = '<a href="#section">Jump</a>'
        result = service.inject_tracking(html, "track123", "https://app.example.com")

        assert 'href="#section"' in result

    def test_empty_html(self, service):
        result = service.inject_tracking("", "track123", "https://app.example.com")
        assert result == ""

    def test_none_tracking_id(self, service):
        html = "<p>Hello</p>"
        result = service.inject_tracking(html, None, "https://app.example.com")
        assert result == html


# =============================================================================
# Record Open Tests
# =============================================================================


class TestRecordOpen:

    def test_record_open_first_time(self, service, mock_db, mock_email_log):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_email_log

        result = service.record_open("abc123def456")

        assert result["success"] is True
        assert result["open_count"] == 1
        assert mock_email_log.opened_at is not None
        mock_db.commit.assert_called_once()

    def test_record_open_subsequent(self, service, mock_db, mock_email_log):
        mock_email_log.opened_at = datetime.utcnow()
        mock_email_log.open_count = 3
        mock_db.query.return_value.filter.return_value.first.return_value = mock_email_log

        result = service.record_open("abc123def456")

        assert result["success"] is True
        assert result["open_count"] == 4

    def test_record_open_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.record_open("nonexistent")

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# Record Click Tests
# =============================================================================


class TestRecordClick:

    def test_record_click_first_time(self, service, mock_db, mock_email_log):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_email_log

        result = service.record_click("abc123def456", "https://example.com")

        assert result["success"] is True
        assert result["click_count"] == 1
        assert mock_email_log.clicked_at is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_record_click_subsequent(self, service, mock_db, mock_email_log):
        mock_email_log.clicked_at = datetime.utcnow()
        mock_email_log.click_count = 2
        mock_db.query.return_value.filter.return_value.first.return_value = mock_email_log

        result = service.record_click("abc123def456", "https://example.com")

        assert result["success"] is True
        assert result["click_count"] == 3

    def test_record_click_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.record_click("nonexistent", "https://example.com")

        assert result["success"] is False


# =============================================================================
# Email Stats Tests
# =============================================================================


class TestGetEmailStats:

    def test_get_email_stats_success(self, service, mock_db, mock_email_log):
        mock_email_log.opened_at = datetime.utcnow()
        mock_email_log.open_count = 5
        mock_email_log.clicked_at = datetime.utcnow()
        mock_email_log.click_count = 2
        mock_db.query.return_value.filter.return_value.first.return_value = mock_email_log
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = service.get_email_stats(1)

        assert result["success"] is True
        assert result["open_count"] == 5
        assert result["click_count"] == 2
        assert result["tracking_id"] == "abc123def456"

    def test_get_email_stats_not_found(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_email_stats(999)

        assert result["success"] is False


# =============================================================================
# Overall Stats Tests
# =============================================================================


class TestGetOverallStats:

    def test_get_overall_stats(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.scalar.return_value = 100
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        result = service.get_overall_stats(days=30)

        assert result["success"] is True
        assert "total_sent" in result
        assert "open_rate" in result
        assert "click_rate" in result
        assert "click_to_open_rate" in result
        assert "top_templates" in result
        assert "daily_stats" in result


# =============================================================================
# Recent Emails Tests
# =============================================================================


class TestGetRecentEmails:

    def test_get_recent_emails(self, service, mock_db, mock_email_log):
        mock_db.query.return_value.filter.return_value.scalar.return_value = 1
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_email_log]

        result = service.get_recent_emails(page=1, per_page=50)

        assert result["success"] is True
        assert result["total"] == 1
        assert len(result["emails"]) == 1
        assert result["emails"][0]["email_address"] == "test@example.com"

    def test_get_recent_emails_empty(self, service, mock_db):
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = service.get_recent_emails()

        assert result["success"] is True
        assert result["total"] == 0
        assert len(result["emails"]) == 0


# =============================================================================
# Singleton Tests
# =============================================================================


class TestModuleLevelFunctions:

    def test_get_email_tracking_service_singleton(self):
        service1 = get_email_tracking_service()
        service2 = get_email_tracking_service()
        assert service1 is service2
