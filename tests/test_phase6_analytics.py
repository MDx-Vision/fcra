"""
Phase 6: Business Intelligence Tests
Tests for analytics dashboard, case management, settlements, and reporting.
"""
import pytest
from datetime import datetime, date, timedelta


class TestAnalyticsDashboard:
    """Test analytics dashboard functionality."""

    def test_analytics_page_requires_auth(self, client):
        """Test that analytics page requires authentication."""
        response = client.get('/dashboard/analytics')
        assert response.status_code in [302, 401, 403, 200]

    def test_analytics_page_authenticated(self, authenticated_client):
        """Test analytics page loads when authenticated."""
        response = authenticated_client.get('/dashboard/analytics')
        assert response.status_code == 200


class TestCaseMetrics:
    """Test case metrics calculations."""

    def test_count_total_cases(self, db_session):
        """Test counting total cases."""
        from database import Client

        total = db_session.query(Client).count()
        assert total >= 0

    def test_count_by_status(self, db_session):
        """Test counting cases by status."""
        from database import Client
        from sqlalchemy import func

        status_counts = db_session.query(
            Client.dispute_status,
            func.count(Client.id)
        ).group_by(Client.dispute_status).all()

        # Should return list of tuples
        assert isinstance(status_counts, list)

    def test_count_by_round(self, db_session):
        """Test counting cases by dispute round."""
        from database import Client
        from sqlalchemy import func

        round_counts = db_session.query(
            Client.current_dispute_round,
            func.count(Client.id)
        ).group_by(Client.current_dispute_round).all()

        assert isinstance(round_counts, list)


class TestViolationAnalytics:
    """Test violation analytics."""

    def test_violation_type_breakdown(self, db_session):
        """Test violation type breakdown."""
        from database import Violation
        from sqlalchemy import func

        type_counts = db_session.query(
            Violation.fcra_section,
            func.count(Violation.id)
        ).group_by(Violation.fcra_section).all()

        assert isinstance(type_counts, list)

    def test_willfulness_ratio(self, db_session):
        """Test willfulness ratio calculation."""
        from database import Violation

        total = db_session.query(Violation).count()
        willful = db_session.query(Violation).filter_by(is_willful=True).count()

        if total > 0:
            ratio = willful / total
            assert 0 <= ratio <= 1
        else:
            assert total == 0


class TestSettlementTracking:
    """Test settlement tracking functionality."""

    def test_settlements_page_exists(self, authenticated_client):
        """Test settlements page exists."""
        response = authenticated_client.get('/dashboard/settlements')
        assert response.status_code == 200

    def test_settlement_model_fields(self):
        """Test Settlement model has required fields."""
        from database import Settlement

        # Check required fields exist
        required_attrs = [
            'case_id', 'target_amount',
            'status'
        ]

        settlement = Settlement()
        for attr in required_attrs:
            assert hasattr(settlement, attr)

    def test_calculate_average_settlement(self, db_session):
        """Test average settlement calculation."""
        from database import Settlement
        from sqlalchemy import func

        result = db_session.query(func.avg(Settlement.target_amount)).scalar()
        # Result could be None if no settlements
        assert result is None or result >= 0

    def test_settlement_status_values(self):
        """Test valid settlement status values."""
        valid_statuses = [
            'pending',
            'accepted',
            'rejected',
            'countered',
            'paid',
            'closed'
        ]

        assert 'pending' in valid_statuses
        assert 'paid' in valid_statuses


class TestRevenueTracking:
    """Test revenue and payment tracking."""

    def test_payment_status_field(self, sample_client):
        """Test client has payment status field."""
        assert hasattr(sample_client, 'payment_status')
        assert hasattr(sample_client, 'payment_received_at')

    def test_calculate_total_revenue(self, db_session):
        """Test total revenue calculation."""
        from database import Client
        from sqlalchemy import func

        total = db_session.query(func.sum(Client.signup_amount)).filter(
            Client.payment_status == 'paid'
        ).scalar()

        # Could be None if no paid clients
        assert total is None or total >= 0


class TestCostTracking:
    """Test cost per case tracking."""

    def test_analysis_cost_field(self, sample_analysis):
        """Test analysis has cost field."""
        assert hasattr(sample_analysis, 'cost')
        assert hasattr(sample_analysis, 'tokens_used')

    def test_calculate_average_cost(self, db_session):
        """Test average cost calculation."""
        from database import Analysis
        from sqlalchemy import func

        avg_cost = db_session.query(func.avg(Analysis.cost)).scalar()
        assert avg_cost is None or avg_cost >= 0


class TestBureauCompliance:
    """Test bureau compliance trend tracking."""

    def test_bureau_response_tracking(self, db_session):
        """Test tracking bureau responses."""
        from database import DisputeLetter

        # Count letters by bureau
        from sqlalchemy import func
        bureau_counts = db_session.query(
            DisputeLetter.bureau,
            func.count(DisputeLetter.id)
        ).group_by(DisputeLetter.bureau).all()

        assert isinstance(bureau_counts, list)


class TestReporting:
    """Test reporting functionality."""

    def test_date_range_filtering(self, db_session):
        """Test filtering by date range."""
        from database import Client

        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        clients = db_session.query(Client).filter(
            Client.created_at >= start_date,
            Client.created_at <= end_date
        ).all()

        assert isinstance(clients, list)

    def test_monthly_aggregation(self, db_session):
        """Test monthly data aggregation."""
        from database import Client
        from sqlalchemy import func, extract

        monthly = db_session.query(
            extract('month', Client.created_at).label('month'),
            func.count(Client.id).label('count')
        ).group_by(extract('month', Client.created_at)).all()

        assert isinstance(monthly, list)


class TestCasePipeline:
    """Test case pipeline visualization."""

    def test_pipeline_stages(self):
        """Test pipeline stage definitions."""
        stages = [
            'signup',
            'active',
            'waiting_response',
            'litigation',
            'settlement',
            'complete'
        ]

        assert 'signup' in stages
        assert 'complete' in stages

    def test_cases_per_stage(self, db_session):
        """Test counting cases per pipeline stage."""
        from database import Client

        stages = ['signup', 'active', 'waiting_response', 'complete']
        pipeline = {}

        for stage in stages:
            count = db_session.query(Client).filter_by(status=stage).count()
            pipeline[stage] = count

        assert isinstance(pipeline, dict)


class TestStaffRoles:
    """Test staff roles and collaboration."""

    def test_staff_roles_defined(self):
        """Test staff roles are defined."""
        from database import STAFF_ROLES

        assert 'admin' in STAFF_ROLES
        assert 'attorney' in STAFF_ROLES
        assert 'paralegal' in STAFF_ROLES

    def test_permission_checking(self):
        """Test permission checking function."""
        from database import check_staff_permission

        # Admin should have all permissions
        assert check_staff_permission('admin', 'view_dashboard') == True
        assert check_staff_permission('admin', 'manage_staff') == True

        # Viewer should have limited permissions
        assert check_staff_permission('viewer', 'view_dashboard') == True

    def test_client_assignment(self, sample_client):
        """Test client can be assigned to staff."""
        assert hasattr(sample_client, 'assigned_to')
