"""
Unit tests for RevenueMetricsService

Tests revenue analytics including MRR/ARR, LTV, churn, and revenue tracking.
"""

import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from services.revenue_metrics_service import RevenueMetricsService, get_revenue_metrics_service


class TestRevenueMetricsServiceInit:
    """Tests for RevenueMetricsService initialization."""

    def test_init_with_db_session(self):
        """Test initialization with database session."""
        mock_db = MagicMock(spec=Session)
        service = RevenueMetricsService(mock_db)

        assert service.db == mock_db

    def test_factory_function(self):
        """Test the factory function creates service instance."""
        mock_db = MagicMock(spec=Session)
        service = get_revenue_metrics_service(mock_db)

        assert isinstance(service, RevenueMetricsService)
        assert service.db == mock_db


class TestGetTotalRevenue:
    """Tests for get_total_revenue method."""

    def test_get_total_revenue_all_time(self):
        """Test getting total revenue without date filters."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.total = 100000  # $1000.00 in cents
        mock_result.count = 10
        mock_result.average = 10000  # $100.00 average

        mock_db.query.return_value.filter.return_value.first.return_value = mock_result

        service = RevenueMetricsService(mock_db)
        result = service.get_total_revenue()

        assert result['total_cents'] == 100000
        assert result['total_dollars'] == 1000.00
        assert result['paying_clients'] == 10
        assert result['average_cents'] == 10000
        assert result['average_dollars'] == 100.00

    def test_get_total_revenue_with_date_range(self):
        """Test getting total revenue with date filters."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.total = 50000
        mock_result.count = 5
        mock_result.average = 10000

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        start = datetime.utcnow() - timedelta(days=30)
        end = datetime.utcnow()
        result = service.get_total_revenue(start_date=start, end_date=end)

        assert result['total_cents'] == 50000
        assert result['total_dollars'] == 500.00
        assert result['paying_clients'] == 5

    def test_get_total_revenue_no_data(self):
        """Test getting total revenue when no data exists."""
        mock_db = MagicMock(spec=Session)
        mock_result = MagicMock()
        mock_result.total = None
        mock_result.count = None
        mock_result.average = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_result

        service = RevenueMetricsService(mock_db)
        result = service.get_total_revenue()

        assert result['total_cents'] == 0
        assert result['total_dollars'] == 0
        assert result['paying_clients'] == 0
        assert result['average_cents'] == 0
        assert result['average_dollars'] == 0


class TestGetRevenueByPeriod:
    """Tests for get_revenue_by_period method."""

    def test_get_revenue_by_month(self):
        """Test getting revenue by month."""
        mock_db = MagicMock(spec=Session)

        # Results are returned DESC order from DB, then reversed
        mock_results = [
            MagicMock(period=datetime(2025, 12, 1), total=150000, count=15),
            MagicMock(period=datetime(2025, 11, 1), total=100000, count=10),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_revenue_by_period(period='month', limit=12)

        # After reversing, Nov should be first, Dec second
        assert len(result) == 2
        assert result[0]['total_cents'] == 100000
        assert result[0]['client_count'] == 10
        assert result[1]['total_cents'] == 150000
        assert result[1]['client_count'] == 15

    def test_get_revenue_by_day(self):
        """Test getting revenue by day."""
        mock_db = MagicMock(spec=Session)

        mock_results = [
            MagicMock(period=datetime(2025, 12, 15), total=5000, count=1),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_revenue_by_period(period='day', limit=30)

        assert len(result) == 1
        assert result[0]['total_dollars'] == 50.00

    def test_get_revenue_by_year(self):
        """Test getting revenue by year."""
        mock_db = MagicMock(spec=Session)

        mock_results = [
            MagicMock(period=datetime(2025, 1, 1), total=1000000, count=100),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_revenue_by_period(period='year', limit=5)

        assert len(result) == 1
        assert result[0]['total_dollars'] == 10000.00


class TestGetRevenueByPaymentMethod:
    """Tests for get_revenue_by_payment_method method."""

    def test_get_revenue_by_payment_method(self):
        """Test getting revenue breakdown by payment method."""
        mock_db = MagicMock(spec=Session)

        mock_results = [
            MagicMock(payment_method='stripe', total=80000, count=8),
            MagicMock(payment_method='paypal', total=20000, count=2),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_revenue_by_payment_method()

        assert 'stripe' in result
        assert result['stripe']['total_cents'] == 80000
        assert result['stripe']['count'] == 8
        assert 'paypal' in result
        assert result['paypal']['total_dollars'] == 200.00

    def test_get_revenue_by_payment_method_unknown(self):
        """Test handling of None payment method."""
        mock_db = MagicMock(spec=Session)

        mock_results = [
            MagicMock(payment_method=None, total=10000, count=1),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_revenue_by_payment_method()

        assert 'unknown' in result
        assert result['unknown']['total_cents'] == 10000


class TestGetRevenueByPlan:
    """Tests for get_revenue_by_plan method."""

    def test_get_revenue_by_plan(self):
        """Test getting revenue breakdown by signup plan."""
        mock_db = MagicMock(spec=Session)

        mock_results = [
            MagicMock(signup_plan='starter', total=50000, count=5),
            MagicMock(signup_plan='pro', total=100000, count=5),
            MagicMock(signup_plan='enterprise', total=200000, count=2),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_revenue_by_plan()

        assert 'starter' in result
        assert result['starter']['total_dollars'] == 500.00
        assert 'pro' in result
        assert result['pro']['count'] == 5
        assert 'enterprise' in result
        assert result['enterprise']['total_dollars'] == 2000.00


class TestGetMRR:
    """Tests for get_mrr method (Monthly Recurring Revenue)."""

    def test_get_mrr_with_subscriptions(self):
        """Test calculating MRR with active subscriptions."""
        mock_db = MagicMock(spec=Session)

        mock_result = MagicMock()
        mock_result.mrr = 50000  # $500/month
        mock_result.count = 10  # 10 subscribers

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_mrr()

        assert result['mrr_cents'] == 50000
        assert result['mrr_dollars'] == 500.00
        assert result['arr_cents'] == 600000  # MRR * 12
        assert result['arr_dollars'] == 6000.00
        assert result['subscriber_count'] == 10
        assert result['arpu_cents'] == 5000  # MRR / subscribers
        assert result['arpu_dollars'] == 50.00

    def test_get_mrr_no_subscriptions(self):
        """Test calculating MRR with no subscriptions."""
        mock_db = MagicMock(spec=Session)

        mock_result = MagicMock()
        mock_result.mrr = None
        mock_result.count = 0

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_mrr()

        assert result['mrr_cents'] == 0
        assert result['mrr_dollars'] == 0
        assert result['arr_cents'] == 0
        assert result['subscriber_count'] == 0
        assert result['arpu_cents'] == 0


class TestGetMRRGrowth:
    """Tests for get_mrr_growth method."""

    def test_get_mrr_growth(self):
        """Test getting MRR growth over time."""
        mock_db = MagicMock(spec=Session)

        # Mock subscription count
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5
        # Mock avg plan price
        mock_db.query.return_value.filter.return_value.scalar.return_value = 4900  # $49

        service = RevenueMetricsService(mock_db)
        result = service.get_mrr_growth(months=6)

        assert len(result) == 6
        assert 'month' in result[0]
        assert 'month_label' in result[0]
        assert 'mrr_cents' in result[0]
        assert 'subscriber_count' in result[0]


class TestGetChurnRate:
    """Tests for get_churn_rate method."""

    def test_get_churn_rate_with_churn(self):
        """Test calculating churn rate with some churn."""
        mock_db = MagicMock(spec=Session)

        # Active at start: 100, Churned: 5
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [100, 5]

        service = RevenueMetricsService(mock_db)
        result = service.get_churn_rate(period_days=30)

        assert result['period_days'] == 30
        assert result['active_at_start'] == 100
        assert result['churned'] == 5
        assert result['retained'] == 95
        assert result['churn_rate'] == 5.0
        assert result['retention_rate'] == 95.0

    def test_get_churn_rate_no_churn(self):
        """Test calculating churn rate with no churn."""
        mock_db = MagicMock(spec=Session)

        mock_db.query.return_value.filter.return_value.scalar.side_effect = [50, 0]

        service = RevenueMetricsService(mock_db)
        result = service.get_churn_rate(period_days=30)

        assert result['churned'] == 0
        assert result['retained'] == 50
        assert result['churn_rate'] == 0
        assert result['retention_rate'] == 100.0

    def test_get_churn_rate_no_active_clients(self):
        """Test calculating churn rate with no active clients."""
        mock_db = MagicMock(spec=Session)

        mock_db.query.return_value.filter.return_value.scalar.side_effect = [0, 0]

        service = RevenueMetricsService(mock_db)
        result = service.get_churn_rate(period_days=30)

        assert result['churn_rate'] == 0
        assert result['retention_rate'] == 100.0


class TestGetClientRetentionCohorts:
    """Tests for get_client_retention_cohorts method."""

    def test_get_retention_cohorts(self):
        """Test getting retention by monthly cohorts."""
        mock_db = MagicMock(spec=Session)

        # Acquired: 20, Retained: 18
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [20, 18] * 6

        service = RevenueMetricsService(mock_db)
        result = service.get_client_retention_cohorts(months=6)

        assert len(result) == 6
        assert 'cohort' in result[0]
        assert 'cohort_label' in result[0]
        assert 'acquired' in result[0]
        assert 'retained' in result[0]
        assert 'churned' in result[0]
        assert 'retention_rate' in result[0]


class TestGetLTV:
    """Tests for get_ltv method (Lifetime Value)."""

    def test_get_ltv_with_data(self):
        """Test calculating LTV with customer data."""
        mock_db = MagicMock(spec=Session)

        mock_avg_result = MagicMock()
        mock_avg_result.avg_revenue = 29700  # $297 average
        mock_avg_result.count = 100

        mock_lifespan_result = MagicMock()
        mock_lifespan_result.avg_months = 6.5

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_avg_result, mock_lifespan_result]
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_ltv()

        assert result['ltv_cents'] == 29700
        assert result['ltv_dollars'] == 297.00
        assert result['avg_revenue_cents'] == 29700
        assert result['avg_revenue_dollars'] == 297.00
        assert result['avg_lifespan_months'] == 6.5
        assert result['paying_customers'] == 100

    def test_get_ltv_no_data(self):
        """Test calculating LTV with no customer data."""
        mock_db = MagicMock(spec=Session)

        mock_avg_result = MagicMock()
        mock_avg_result.avg_revenue = None
        mock_avg_result.count = 0

        mock_lifespan_result = MagicMock()
        mock_lifespan_result.avg_months = None

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_avg_result, mock_lifespan_result]
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_ltv()

        assert result['ltv_cents'] == 0
        assert result['paying_customers'] == 0


class TestGetCommissionMetrics:
    """Tests for get_commission_metrics method."""

    def test_get_commission_metrics(self):
        """Test getting commission/affiliate metrics."""
        mock_db = MagicMock(spec=Session)

        mock_result = MagicMock()
        mock_result.total_commissions = 10000  # $100
        mock_result.total_triggered = 50000  # $500 triggered
        mock_result.commission_count = 10

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        mock_query.scalar.side_effect = [8000, 2000, 5]  # paid, pending, active affiliates
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_commission_metrics()

        assert result['total_commissions'] == 10000
        assert result['total_triggered_revenue'] == 50000
        assert result['commission_count'] == 10
        assert result['paid_commissions'] == 8000
        assert result['pending_commissions'] == 2000
        assert result['active_affiliates'] == 5


class TestGetTopAffiliates:
    """Tests for get_top_affiliates method."""

    def test_get_top_affiliates(self):
        """Test getting top performing affiliates."""
        mock_db = MagicMock(spec=Session)

        mock_results = [
            SimpleNamespace(
                id=1,
                name='John Doe',
                email='john@example.com',
                total_referrals=50,
                total_earnings=100000,
                pending_earnings=5000
            ),
            SimpleNamespace(
                id=2,
                name='Jane Smith',
                email='jane@example.com',
                total_referrals=30,
                total_earnings=60000,
                pending_earnings=3000
            ),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_top_affiliates(limit=10)

        assert len(result) == 2
        assert result[0]['name'] == 'John Doe'
        assert result[0]['total_referrals'] == 50
        assert result[0]['total_earnings'] == 100000
        assert result[1]['name'] == 'Jane Smith'

    def test_get_top_affiliates_no_name(self):
        """Test handling affiliates with no name."""
        mock_db = MagicMock(spec=Session)

        mock_results = [
            SimpleNamespace(
                id=1,
                name=None,
                email='anon@example.com',
                total_referrals=10,
                total_earnings=10000,
                pending_earnings=1000
            ),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_top_affiliates(limit=10)

        assert result[0]['name'] == 'anon@example.com'


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary method."""

    def test_get_dashboard_summary(self):
        """Test getting comprehensive dashboard summary."""
        mock_db = MagicMock(spec=Session)
        service = RevenueMetricsService(mock_db)

        # Mock all the internal method calls
        with patch.object(service, 'get_total_revenue') as mock_revenue, \
             patch.object(service, 'get_mrr') as mock_mrr, \
             patch.object(service, 'get_ltv') as mock_ltv, \
             patch.object(service, 'get_churn_rate') as mock_churn, \
             patch.object(service, 'get_commission_metrics') as mock_commissions:

            mock_revenue.side_effect = [
                {'total_cents': 100000, 'total_dollars': 1000.00, 'paying_clients': 10, 'average_cents': 10000, 'average_dollars': 100.00},
                {'total_cents': 80000, 'total_dollars': 800.00, 'paying_clients': 8, 'average_cents': 10000, 'average_dollars': 100.00},
            ]
            mock_mrr.return_value = {'mrr_cents': 50000, 'mrr_dollars': 500.00, 'arr_cents': 600000, 'arr_dollars': 6000.00, 'subscriber_count': 10, 'arpu_cents': 5000, 'arpu_dollars': 50.00}
            mock_ltv.return_value = {'ltv_cents': 29700, 'ltv_dollars': 297.00, 'avg_revenue_cents': 29700, 'avg_revenue_dollars': 297.00, 'avg_lifespan_months': 6.5, 'paying_customers': 100}
            mock_churn.return_value = {'period_days': 30, 'active_at_start': 100, 'churned': 5, 'retained': 95, 'churn_rate': 5.0, 'retention_rate': 95.0}
            mock_commissions.return_value = {'total_commissions': 10000, 'pending_commissions': 2000, 'active_affiliates': 5}

            mock_db.query.return_value.filter.return_value.scalar.side_effect = [50, 25]

            result = service.get_dashboard_summary()

            assert 'period' in result
            assert 'revenue' in result
            assert 'mrr' in result
            assert 'ltv' in result
            assert 'churn' in result
            assert 'clients' in result
            assert 'affiliates' in result

            assert result['revenue']['growth_percent'] == 25.0  # (100000-80000)/80000 * 100


class TestGetRevenueChartData:
    """Tests for get_revenue_chart_data method."""

    def test_get_chart_data(self):
        """Test getting data formatted for Chart.js."""
        mock_db = MagicMock(spec=Session)
        service = RevenueMetricsService(mock_db)

        with patch.object(service, 'get_revenue_by_period') as mock_period:
            mock_period.return_value = [
                {'period': '2025-11-01T00:00:00', 'total_dollars': 1000.00, 'client_count': 10},
                {'period': '2025-12-01T00:00:00', 'total_dollars': 1500.00, 'client_count': 15},
            ]

            result = service.get_revenue_chart_data(period='month', limit=12)

            assert 'labels' in result
            assert 'datasets' in result
            assert len(result['labels']) == 2
            assert result['datasets']['revenue'] == [1000.00, 1500.00]
            assert result['datasets']['clients'] == [10, 15]


class TestExportRevenueData:
    """Tests for export_revenue_data method."""

    def test_export_revenue_data(self):
        """Test exporting detailed revenue data."""
        mock_db = MagicMock(spec=Session)

        mock_results = [
            MagicMock(
                id=1,
                first_name='John',
                last_name='Doe',
                email='john@example.com',
                signup_plan='pro',
                total_paid=29700,
                payment_status='paid',
                payment_method='stripe',
                payment_received_at=datetime(2025, 12, 1),
                created_at=datetime(2025, 11, 15)
            ),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.export_revenue_data()

        assert len(result) == 1
        assert result[0]['client_id'] == 1
        assert result[0]['name'] == 'John Doe'
        assert result[0]['email'] == 'john@example.com'
        assert result[0]['plan'] == 'pro'
        assert result[0]['amount_cents'] == 29700
        assert result[0]['amount_dollars'] == 297.00
        assert result[0]['status'] == 'paid'
        assert result[0]['method'] == 'stripe'

    def test_export_with_date_range(self):
        """Test exporting with date range filter."""
        mock_db = MagicMock(spec=Session)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        start = datetime(2025, 12, 1)
        end = datetime(2025, 12, 31)
        result = service.export_revenue_data(start_date=start, end_date=end)

        assert result == []

    def test_export_handles_null_dates(self):
        """Test export handles clients with null dates."""
        mock_db = MagicMock(spec=Session)

        mock_results = [
            MagicMock(
                id=1,
                first_name='Test',
                last_name='User',
                email='test@example.com',
                signup_plan=None,
                total_paid=10000,
                payment_status='pending',
                payment_method=None,
                payment_received_at=None,
                created_at=None
            ),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = mock_results
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.export_revenue_data()

        assert result[0]['payment_date'] is None
        assert result[0]['signup_date'] is None


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_handles_zero_division_in_churn(self):
        """Test churn calculation handles zero division."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [0, 0]

        service = RevenueMetricsService(mock_db)
        result = service.get_churn_rate()

        assert result['churn_rate'] == 0

    def test_handles_zero_division_in_arpu(self):
        """Test ARPU calculation handles zero subscribers."""
        mock_db = MagicMock(spec=Session)

        mock_result = MagicMock()
        mock_result.mrr = 0
        mock_result.count = 0

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_result
        mock_db.query.return_value = mock_query

        service = RevenueMetricsService(mock_db)
        result = service.get_mrr()

        assert result['arpu_cents'] == 0

    def test_handles_negative_growth(self):
        """Test dashboard handles negative revenue growth."""
        mock_db = MagicMock(spec=Session)
        service = RevenueMetricsService(mock_db)

        with patch.object(service, 'get_total_revenue') as mock_revenue, \
             patch.object(service, 'get_mrr') as mock_mrr, \
             patch.object(service, 'get_ltv') as mock_ltv, \
             patch.object(service, 'get_churn_rate') as mock_churn, \
             patch.object(service, 'get_commission_metrics') as mock_commissions:

            # Current period less than previous (negative growth)
            mock_revenue.side_effect = [
                {'total_cents': 50000, 'total_dollars': 500.00, 'paying_clients': 5, 'average_cents': 10000, 'average_dollars': 100.00},
                {'total_cents': 100000, 'total_dollars': 1000.00, 'paying_clients': 10, 'average_cents': 10000, 'average_dollars': 100.00},
            ]
            mock_mrr.return_value = {'mrr_cents': 0, 'mrr_dollars': 0, 'arr_cents': 0, 'arr_dollars': 0, 'subscriber_count': 0, 'arpu_cents': 0, 'arpu_dollars': 0}
            mock_ltv.return_value = {'ltv_cents': 0, 'ltv_dollars': 0, 'avg_revenue_cents': 0, 'avg_revenue_dollars': 0, 'avg_lifespan_months': 0, 'paying_customers': 0}
            mock_churn.return_value = {'period_days': 30, 'active_at_start': 0, 'churned': 0, 'retained': 0, 'churn_rate': 0, 'retention_rate': 100}
            mock_commissions.return_value = {'total_commissions': 0, 'pending_commissions': 0, 'active_affiliates': 0}

            mock_db.query.return_value.filter.return_value.scalar.side_effect = [0, 0]

            result = service.get_dashboard_summary()

            # Growth should be -50%
            assert result['revenue']['growth_percent'] == -50.0
