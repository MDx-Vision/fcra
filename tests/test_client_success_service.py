"""
Unit tests for ClientSuccessService

Tests client success metrics calculation including:
- Metric calculation
- Score changes
- Item tracking
- Success grades
- Aggregate reports
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from services.client_success_service import ClientSuccessService


class TestServiceInit:
    """Tests for ClientSuccessService initialization."""

    def test_init_with_db(self):
        """Test initialization with database."""
        mock_db = MagicMock(spec=Session)
        service = ClientSuccessService(mock_db)
        assert service.db == mock_db


class TestCalculateClientMetrics:
    """Tests for calculate_client_metrics method."""

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientSuccessService(mock_db)
        result = service.calculate_client_metrics(client_id=999)

        assert 'error' in result
        assert 'not found' in result['error']

    def test_success_returns_metrics(self):
        """Test successful metrics calculation."""
        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        mock_client.status = 'active'
        mock_client.dispute_status = 'active'
        mock_client.current_dispute_round = 2
        mock_client.created_at = datetime.utcnow() - timedelta(days=30)

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        service = ClientSuccessService(mock_db)
        result = service.calculate_client_metrics(client_id=1)

        assert result['client_id'] == 1
        assert result['client_name'] == 'Test Client'
        assert result['dispute_rounds_completed'] == 2
        assert result['days_in_program'] == 30


class TestGetInitialData:
    """Tests for _get_initial_data method."""

    def test_with_snapshot(self):
        """Test getting initial data from snapshot."""
        mock_db = MagicMock(spec=Session)

        mock_snapshot = MagicMock()
        mock_snapshot.equifax_score = 550
        mock_snapshot.experian_score = 560
        mock_snapshot.transunion_score = 570
        mock_snapshot.average_score = 560
        mock_snapshot.total_negatives = 15
        mock_snapshot.equifax_negatives = 5
        mock_snapshot.experian_negatives = 5
        mock_snapshot.transunion_negatives = 5

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_snapshot

        service = ClientSuccessService(mock_db)
        result = service._get_initial_data(client_id=1)

        assert result['equifax_score'] == 550
        assert result['total_negatives'] == 15

    def test_without_snapshot(self):
        """Test getting initial data without snapshot."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        service = ClientSuccessService(mock_db)
        result = service._get_initial_data(client_id=1)

        assert result['equifax_score'] is None
        assert result['total_negatives'] == 10


class TestCalculateItemMetrics:
    """Tests for _calculate_item_metrics method."""

    def test_empty_items(self):
        """Test with no items."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ClientSuccessService(mock_db)
        result = service._calculate_item_metrics(client_id=1)

        assert result['total_deleted'] == 0
        assert result['total_verified'] == 0

    def test_counts_deleted_items(self):
        """Test counting deleted items."""
        mock_db = MagicMock(spec=Session)

        mock_items = [
            MagicMock(status='deleted', bureau='Equifax'),
            MagicMock(status='deleted', bureau='Experian'),
            MagicMock(status='verified', bureau='TransUnion'),
        ]

        # First call returns dispute items, second returns CRA responses
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            mock_items, []
        ]

        service = ClientSuccessService(mock_db)
        result = service._calculate_item_metrics(client_id=1)

        assert result['total_deleted'] == 2
        assert result['equifax_deleted'] == 1
        assert result['experian_deleted'] == 1


class TestCalculateScoreChanges:
    """Tests for _calculate_score_changes method."""

    def test_score_improvement(self):
        """Test calculating score improvements."""
        mock_db = MagicMock(spec=Session)
        service = ClientSuccessService(mock_db)

        initial = {
            'equifax_score': 550,
            'experian_score': 560,
            'transunion_score': 570,
            'avg_score': 560
        }

        current = {
            'equifax_score': 620,
            'experian_score': 630,
            'transunion_score': 640,
            'avg_score': 630
        }

        result = service._calculate_score_changes(initial, current)

        assert result['equifax'] == 70
        assert result['experian'] == 70
        assert result['transunion'] == 70
        assert result['avg'] == 70

    def test_no_score_data(self):
        """Test with no score data."""
        mock_db = MagicMock(spec=Session)
        service = ClientSuccessService(mock_db)

        initial = {}
        current = {}

        result = service._calculate_score_changes(initial, current)

        assert result['equifax'] == 0
        assert result['avg'] == 0


class TestCalculateSuccessGrade:
    """Tests for _calculate_success_grade method."""

    def test_a_plus_grade(self):
        """Test A+ grade with high metrics."""
        mock_db = MagicMock(spec=Session)
        service = ClientSuccessService(mock_db)

        metrics = {
            'deletion_rate': 85,
            'avg_score_change': 100,
            'items_deleted': 25
        }

        result = service._calculate_success_grade(metrics)

        assert result == 'A+'

    def test_f_grade(self):
        """Test F grade with low metrics."""
        mock_db = MagicMock(spec=Session)
        service = ClientSuccessService(mock_db)

        metrics = {
            'deletion_rate': 5,
            'avg_score_change': 0,
            'items_deleted': 0
        }

        result = service._calculate_success_grade(metrics)

        assert result == 'F'

    def test_b_grade(self):
        """Test B grade with moderate metrics."""
        mock_db = MagicMock(spec=Session)
        service = ClientSuccessService(mock_db)

        # Score calculation: deletion_rate 60 → 30pts, avg_score_change 50 → 30pts, items_deleted 12 → 12pts
        # Total: 72 points → B+ grade (70-79 = B+, 60-69 = B)
        metrics = {
            'deletion_rate': 60,
            'avg_score_change': 50,
            'items_deleted': 12
        }

        result = service._calculate_success_grade(metrics)

        assert result in ['B+', 'B']


class TestCreateSnapshot:
    """Tests for create_snapshot method."""

    def test_client_not_found(self):
        """Test with client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientSuccessService(mock_db)
        result = service.create_snapshot(client_id=999)

        assert result is None


class TestGetLatestSnapshot:
    """Tests for get_latest_snapshot method."""

    def test_returns_snapshot(self):
        """Test returns latest snapshot."""
        mock_db = MagicMock(spec=Session)
        mock_snapshot = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_snapshot

        service = ClientSuccessService(mock_db)
        result = service.get_latest_snapshot(client_id=1)

        assert result == mock_snapshot

    def test_no_snapshot(self):
        """Test with no snapshot."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        service = ClientSuccessService(mock_db)
        result = service.get_latest_snapshot(client_id=1)

        assert result is None


class TestGetSnapshotHistory:
    """Tests for get_snapshot_history method."""

    def test_returns_history(self):
        """Test returns snapshot history."""
        mock_db = MagicMock(spec=Session)
        mock_snapshots = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_snapshots

        service = ClientSuccessService(mock_db)
        result = service.get_snapshot_history(client_id=1)

        assert len(result) == 2


class TestGetClientSummary:
    """Tests for get_client_summary method."""

    def test_client_not_found(self):
        """Test error when client not found."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ClientSuccessService(mock_db)
        result = service.get_client_summary(client_id=999)

        assert 'error' in result


class TestGetAggregateReport:
    """Tests for get_aggregate_report method."""

    def test_no_clients(self):
        """Test with no clients."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ClientSuccessService(mock_db)
        result = service.get_aggregate_report()

        assert result['total_clients'] == 0
        assert result['total_items_deleted'] == 0

    def test_period_filter(self):
        """Test period filtering."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = ClientSuccessService(mock_db)

        for period in ['month', 'quarter', 'year']:
            result = service.get_aggregate_report(period=period)
            assert 'total_clients' in result


class TestGetTopPerformers:
    """Tests for get_top_performers method."""

    def test_returns_list(self):
        """Test returns performer list."""
        mock_db = MagicMock(spec=Session)

        # Empty result
        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = ClientSuccessService(mock_db)
        result = service.get_top_performers()

        assert isinstance(result, list)


class TestGetSuccessTrend:
    """Tests for get_success_trend method."""

    def test_returns_trend_data(self):
        """Test returns trend data."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = ClientSuccessService(mock_db)
        result = service.get_success_trend()

        assert isinstance(result, list)


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary method."""

    def test_returns_summary(self):
        """Test returns dashboard summary."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = ClientSuccessService(mock_db)

        with patch.object(service, 'get_aggregate_report') as mock_aggregate:
            mock_aggregate.return_value = {
                'total_clients': 0,
                'completed_cases': 0,
                'completion_rate': 0,
                'total_items_deleted': 0,
                'avg_deletion_rate': 0,
                'avg_score_improvement': 0,
                'total_estimated_value': 0,
                'grade_distribution': {}
            }

            with patch.object(service, 'get_top_performers') as mock_top:
                mock_top.return_value = []

                with patch.object(service, 'get_success_trend') as mock_trend:
                    mock_trend.return_value = []

                    result = service.get_dashboard_summary()

        assert 'stats' in result
        assert 'monthly_stats' in result


class TestGetBureauBreakdown:
    """Tests for get_bureau_breakdown method."""

    def test_returns_breakdown(self):
        """Test returns bureau breakdown."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.group_by.return_value.subquery.return_value = MagicMock()
        mock_db.query.return_value.join.return_value.all.return_value = []

        service = ClientSuccessService(mock_db)
        result = service.get_bureau_breakdown()

        assert 'items_deleted' in result
        assert 'avg_score_improvement' in result


class TestExportSuccessData:
    """Tests for export_success_data method."""

    def test_empty_export(self):
        """Test export with no clients."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.all.return_value = []

        service = ClientSuccessService(mock_db)
        result = service.export_success_data()

        assert result == []
