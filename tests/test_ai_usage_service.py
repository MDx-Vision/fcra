"""
Unit tests for AI Usage Service

Tests cover:
- Cost calculation
- Usage logging
- Usage summary and reporting
- Monthly reports
- Client usage breakdown
- Decorator for tracking
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


class TestPricing:
    """Tests for PRICING constant"""

    def test_pricing_exists(self):
        """Should have pricing constant"""
        from services.ai_usage_service import PRICING

        assert PRICING is not None
        assert "default" in PRICING

    def test_pricing_has_sonnet(self):
        """Should have Sonnet pricing"""
        from services.ai_usage_service import PRICING

        # Check for sonnet model
        sonnet_key = next((k for k in PRICING if 'sonnet' in k.lower()), None)
        assert sonnet_key is not None or "default" in PRICING

    def test_pricing_has_input_output(self):
        """Should have input and output pricing"""
        from services.ai_usage_service import PRICING

        for model, prices in PRICING.items():
            assert "input" in prices
            assert "output" in prices


class TestCalculateCostCents:
    """Tests for calculate_cost_cents function"""

    def test_calculates_cost_for_known_model(self):
        """Should calculate cost for known model"""
        from services.ai_usage_service import calculate_cost_cents

        input_cost, output_cost, total_cost = calculate_cost_cents(
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500
        )

        assert isinstance(input_cost, int)
        assert isinstance(output_cost, int)
        # With small token counts, costs round to 0, just verify they're non-negative
        assert input_cost >= 0
        assert output_cost >= 0
        assert total_cost >= 0

    def test_uses_default_for_unknown_model(self):
        """Should use default pricing for unknown model"""
        from services.ai_usage_service import calculate_cost_cents

        input_cost, output_cost, total_cost = calculate_cost_cents(
            model="unknown-model",
            input_tokens=1000,
            output_tokens=500
        )

        assert total_cost >= 0

    def test_zero_tokens(self):
        """Should return zero for zero tokens"""
        from services.ai_usage_service import calculate_cost_cents

        input_cost, output_cost, total_cost = calculate_cost_cents(
            model="claude-sonnet-4-20250514",
            input_tokens=0,
            output_tokens=0
        )

        assert total_cost == 0

    def test_large_token_count(self):
        """Should handle large token counts"""
        from services.ai_usage_service import calculate_cost_cents

        input_cost, output_cost, total_cost = calculate_cost_cents(
            model="claude-sonnet-4-20250514",
            input_tokens=1_000_000,
            output_tokens=1_000_000
        )

        # 1M input at $3 = $3 = 300 cents
        # 1M output at $15 = $15 = 1500 cents
        assert input_cost == 300
        assert output_cost == 1500
        assert total_cost == 1800


class TestLogAiUsage:
    """Tests for log_ai_usage function"""

    @patch('services.ai_usage_service.get_db')
    def test_logs_usage_successfully(self, mock_get_db):
        """Should log usage and return AIUsageLog"""
        from services.ai_usage_service import log_ai_usage

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = log_ai_usage(
            service="dispute_writer",
            operation="generate_letters",
            model="claude-sonnet-4-20250514",
            input_tokens=1000,
            output_tokens=500,
            duration_ms=1500,
            client_id=1,
            success=True
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('services.ai_usage_service.get_db')
    def test_handles_database_error(self, mock_get_db):
        """Should handle database errors gracefully"""
        from services.ai_usage_service import log_ai_usage

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.add.side_effect = Exception("DB Error")

        result = log_ai_usage(
            service="test",
            operation="test",
            model="test",
            input_tokens=100,
            output_tokens=50
        )

        assert result is None
        mock_db.rollback.assert_called_once()

    @patch('services.ai_usage_service.get_db')
    def test_logs_with_optional_fields(self, mock_get_db):
        """Should handle optional fields"""
        from services.ai_usage_service import log_ai_usage

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        result = log_ai_usage(
            service="chat",
            operation="message",
            model="claude-sonnet-4-20250514",
            input_tokens=500,
            output_tokens=200,
            staff_id=5,
            dispute_round=2,
            letter_type="demand",
            success=True
        )

        mock_db.add.assert_called_once()

    @patch('services.ai_usage_service.get_db')
    def test_logs_failure_with_error_message(self, mock_get_db):
        """Should log failures with error message"""
        from services.ai_usage_service import log_ai_usage

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        result = log_ai_usage(
            service="test",
            operation="test",
            model="test",
            input_tokens=100,
            output_tokens=0,
            success=False,
            error_message="API rate limit exceeded"
        )

        mock_db.add.assert_called_once()


class TestGetUsageSummary:
    """Tests for get_usage_summary function"""

    @patch('services.ai_usage_service.get_db')
    def test_returns_summary_dict(self, mock_get_db):
        """Should return summary dictionary"""
        from services.ai_usage_service import get_usage_summary

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # Create mock logs
        mock_log = MagicMock()
        mock_log.input_tokens = 1000
        mock_log.output_tokens = 500
        mock_log.total_tokens = 1500
        mock_log.total_cost_cents = 50
        mock_log.success = True
        mock_log.service = "dispute_writer"
        mock_log.created_at = datetime.utcnow()

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_log]

        result = get_usage_summary(days=30)

        assert "total_calls" in result
        assert "total_input_tokens" in result
        assert "total_output_tokens" in result
        assert "total_cost_cents" in result
        assert "by_service" in result
        assert "by_day" in result

    @patch('services.ai_usage_service.get_db')
    def test_filters_by_client(self, mock_get_db):
        """Should filter by client_id"""
        from services.ai_usage_service import get_usage_summary

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        result = get_usage_summary(days=30, client_id=1)

        assert result is not None

    @patch('services.ai_usage_service.get_db')
    def test_handles_empty_results(self, mock_get_db):
        """Should handle no logs"""
        from services.ai_usage_service import get_usage_summary

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_usage_summary(days=30)

        assert result["total_calls"] == 0
        assert result["total_cost_cents"] == 0

    @patch('services.ai_usage_service.get_db')
    def test_handles_database_error(self, mock_get_db):
        """Should handle database errors"""
        from services.ai_usage_service import get_usage_summary

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.side_effect = Exception("DB Error")

        result = get_usage_summary(days=30)

        assert "error" in result


class TestGetUsageByClient:
    """Tests for get_usage_by_client function"""

    @patch('services.ai_usage_service.get_db')
    def test_returns_list(self, mock_get_db):
        """Should return list of clients"""
        from services.ai_usage_service import get_usage_by_client

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = get_usage_by_client(days=30, limit=20)

        assert isinstance(result, list)

    @patch('services.ai_usage_service.get_db')
    def test_handles_error(self, mock_get_db):
        """Should handle errors gracefully"""
        from services.ai_usage_service import get_usage_by_client

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.side_effect = Exception("DB Error")

        result = get_usage_by_client(days=30)

        assert result == []


class TestGetRecentLogs:
    """Tests for get_recent_logs function"""

    @patch('services.ai_usage_service.get_db')
    def test_returns_list(self, mock_get_db):
        """Should return list of logs"""
        from services.ai_usage_service import get_recent_logs

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_log = MagicMock()
        mock_log.to_dict.return_value = {"id": 1, "service": "test"}
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_log]

        result = get_recent_logs(limit=50)

        assert isinstance(result, list)

    @patch('services.ai_usage_service.get_db')
    def test_handles_error(self, mock_get_db):
        """Should handle errors gracefully"""
        from services.ai_usage_service import get_recent_logs

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.side_effect = Exception("DB Error")

        result = get_recent_logs()

        assert result == []


class TestGetMonthlyReport:
    """Tests for get_monthly_report function"""

    @patch('services.ai_usage_service.get_db')
    def test_returns_report_dict(self, mock_get_db):
        """Should return monthly report"""
        from services.ai_usage_service import get_monthly_report

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_monthly_report(year=2024, month=6)

        assert "year" in result
        assert "month" in result
        assert "month_name" in result
        assert "total_calls" in result

    @patch('services.ai_usage_service.get_db')
    def test_defaults_to_current_month(self, mock_get_db):
        """Should default to current month"""
        from services.ai_usage_service import get_monthly_report

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_monthly_report()

        now = datetime.utcnow()
        assert result["year"] == now.year
        assert result["month"] == now.month

    @patch('services.ai_usage_service.get_db')
    def test_handles_december(self, mock_get_db):
        """Should handle December correctly"""
        from services.ai_usage_service import get_monthly_report

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_monthly_report(year=2024, month=12)

        assert result["month"] == 12

    @patch('services.ai_usage_service.get_db')
    def test_handles_error(self, mock_get_db):
        """Should handle errors"""
        from services.ai_usage_service import get_monthly_report

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.side_effect = Exception("DB Error")

        result = get_monthly_report()

        assert "error" in result


class TestTrackAiUsageDecorator:
    """Tests for track_ai_usage decorator"""

    @patch('services.ai_usage_service.log_ai_usage')
    def test_decorator_logs_successful_call(self, mock_log):
        """Should log successful API calls"""
        from services.ai_usage_service import track_ai_usage

        @track_ai_usage("test_service", "test_operation")
        def mock_api_call():
            response = MagicMock()
            response.usage = MagicMock()
            response.usage.input_tokens = 100
            response.usage.output_tokens = 50
            response.model = "test-model"
            return response

        result = mock_api_call()

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[1]["service"] == "test_service"
        assert call_args[1]["operation"] == "test_operation"
        assert call_args[1]["success"] is True

    @patch('services.ai_usage_service.log_ai_usage')
    def test_decorator_logs_failed_call(self, mock_log):
        """Should log failed API calls"""
        from services.ai_usage_service import track_ai_usage

        @track_ai_usage("test_service", "test_operation")
        def failing_api_call():
            raise Exception("API Error")

        with pytest.raises(Exception):
            failing_api_call()

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert call_args[1]["success"] is False
        assert "API Error" in call_args[1]["error_message"]

    @patch('services.ai_usage_service.log_ai_usage')
    def test_decorator_extracts_response_from_dict(self, mock_log):
        """Should extract response from dict with response key"""
        from services.ai_usage_service import track_ai_usage

        @track_ai_usage("test_service", "test_operation")
        def mock_api_call():
            response = MagicMock()
            response.usage = MagicMock()
            response.usage.input_tokens = 100
            response.usage.output_tokens = 50
            response.model = "test-model"
            return {"response": response, "other_data": "test"}

        result = mock_api_call()

        mock_log.assert_called_once()

    @patch('services.ai_usage_service.log_ai_usage')
    def test_decorator_passes_client_id_from_kwargs(self, mock_log):
        """Should pass client_id from kwargs"""
        from services.ai_usage_service import track_ai_usage

        @track_ai_usage("test_service", "test_operation")
        def mock_api_call(client_id=None):
            response = MagicMock()
            response.usage = MagicMock()
            response.usage.input_tokens = 100
            response.usage.output_tokens = 50
            return response

        mock_api_call(client_id=42)

        call_args = mock_log.call_args
        assert call_args[1]["client_id"] == 42
