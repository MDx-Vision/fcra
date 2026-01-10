"""
Unit tests for StaffPerformanceService

Tests staff performance tracking including:
- Activity logging
- Performance metrics
- Leaderboard
- Trends
- Dashboard summary
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from services.staff_performance_service import (
    StaffPerformanceService,
    ACTIVITY_TYPES,
    log_staff_activity,
    get_staff_leaderboard,
    get_performance_dashboard,
)


class TestActivityTypes:
    """Tests for activity type configuration."""

    def test_activity_types_defined(self):
        """Test all expected activity types are defined."""
        expected = [
            'case_assigned', 'case_completed', 'document_reviewed',
            'letter_sent', 'response_processed', 'message_sent',
            'call_completed', 'note_added', 'status_changed',
            'analysis_reviewed', 'dispute_filed'
        ]

        for activity in expected:
            assert activity in ACTIVITY_TYPES

    def test_activity_has_points(self):
        """Test each activity type has point value."""
        for activity_type, info in ACTIVITY_TYPES.items():
            assert 'name' in info
            assert 'points' in info
            assert info['points'] >= 0

    def test_case_completed_high_value(self):
        """Test case_completed has high point value."""
        assert ACTIVITY_TYPES['case_completed']['points'] >= 15


class TestServiceInit:
    """Tests for StaffPerformanceService initialization."""

    def test_init_with_session(self):
        """Test initialization with session."""
        mock_session = MagicMock(spec=Session)
        service = StaffPerformanceService(session=mock_session)

        assert service._session == mock_session
        assert service._owns_session == False

    def test_init_without_session(self):
        """Test initialization without session."""
        service = StaffPerformanceService()

        assert service._session is None
        assert service._owns_session == True


class TestLogActivity:
    """Tests for log_activity method."""

    def test_invalid_activity_type(self):
        """Test error for invalid activity type."""
        mock_session = MagicMock(spec=Session)
        service = StaffPerformanceService(session=mock_session)

        success, message, data = service.log_activity(
            staff_id=1,
            activity_type='invalid_type'
        )

        assert success == False
        assert 'Invalid activity type' in message

    def test_valid_activity_logged(self):
        """Test valid activity is logged."""
        mock_session = MagicMock(spec=Session)
        mock_activity = MagicMock()
        mock_activity.to_dict.return_value = {'id': 1}

        with patch('services.staff_performance_service.StaffActivity') as MockActivity:
            MockActivity.return_value = mock_activity

            service = StaffPerformanceService(session=mock_session)
            success, message, data = service.log_activity(
                staff_id=1,
                activity_type='case_completed',
                description='Completed case #123'
            )

        assert success == True
        assert 'logged' in message

    def test_calculates_response_time(self):
        """Test response time is calculated when request time provided."""
        mock_session = MagicMock(spec=Session)
        mock_activity = MagicMock()
        mock_activity.to_dict.return_value = {'id': 1}

        with patch('services.staff_performance_service.StaffActivity') as MockActivity:
            MockActivity.return_value = mock_activity

            service = StaffPerformanceService(session=mock_session)

            request_time = datetime.utcnow() - timedelta(minutes=30)
            success, message, data = service.log_activity(
                staff_id=1,
                activity_type='response_processed',
                request_received_at=request_time
            )

        # Check that response_time_minutes was set
        call_kwargs = MockActivity.call_args[1]
        assert call_kwargs['response_time_minutes'] == 30

    def test_handles_exception(self):
        """Test exception handling."""
        mock_session = MagicMock(spec=Session)
        mock_session.add.side_effect = Exception("Database error")

        with patch('services.staff_performance_service.StaffActivity'):
            service = StaffPerformanceService(session=mock_session)
            success, message, data = service.log_activity(
                staff_id=1,
                activity_type='case_completed'
            )

        assert success == False
        assert 'Error' in message


class TestMarkEscalated:
    """Tests for mark_escalated method."""

    def test_activity_not_found(self):
        """Test error when activity not found."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = StaffPerformanceService(session=mock_session)
        success, message = service.mark_escalated(activity_id=999)

        assert success == False
        assert 'not found' in message

    def test_marks_as_escalated(self):
        """Test marking activity as escalated."""
        mock_session = MagicMock(spec=Session)
        mock_activity = MagicMock()
        mock_activity.was_escalated = False
        mock_session.query.return_value.filter.return_value.first.return_value = mock_activity

        service = StaffPerformanceService(session=mock_session)
        success, message = service.mark_escalated(activity_id=1)

        assert success == True
        assert mock_activity.was_escalated == True


class TestMarkRevisionRequired:
    """Tests for mark_revision_required method."""

    def test_activity_not_found(self):
        """Test error when activity not found."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = StaffPerformanceService(session=mock_session)
        success, message = service.mark_revision_required(activity_id=999)

        assert success == False

    def test_marks_as_revision_required(self):
        """Test marking activity as requiring revision."""
        mock_session = MagicMock(spec=Session)
        mock_activity = MagicMock()
        mock_activity.required_revision = False
        mock_session.query.return_value.filter.return_value.first.return_value = mock_activity

        service = StaffPerformanceService(session=mock_session)
        success, message = service.mark_revision_required(activity_id=1)

        assert success == True
        assert mock_activity.required_revision == True


class TestGetStaffMetrics:
    """Tests for get_staff_metrics method."""

    def test_staff_not_found(self):
        """Test error when staff not found."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = StaffPerformanceService(session=mock_session)
        result = service.get_staff_metrics(staff_id=999)

        assert 'error' in result
        assert 'not found' in result['error']

    def test_returns_metrics(self):
        """Test returns comprehensive metrics."""
        mock_session = MagicMock(spec=Session)

        mock_staff = MagicMock()
        mock_staff.id = 1
        mock_staff.full_name = 'John Doe'
        mock_staff.role = 'admin'

        mock_session.query.return_value.filter.return_value.first.return_value = mock_staff

        mock_activities = [
            MagicMock(activity_type='case_completed', response_time_minutes=30, quality_score=8, was_escalated=False, required_revision=False),
            MagicMock(activity_type='letter_sent', response_time_minutes=15, quality_score=9, was_escalated=False, required_revision=False),
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_activities

        service = StaffPerformanceService(session=mock_session)
        result = service.get_staff_metrics(staff_id=1)

        assert result['staff_id'] == 1
        assert result['staff_name'] == 'John Doe'
        assert 'summary' in result
        assert 'cases' in result
        assert 'response_time' in result
        assert 'quality' in result
        assert 'activity_breakdown' in result

    def test_calculates_averages(self):
        """Test average calculations."""
        mock_session = MagicMock(spec=Session)

        mock_staff = MagicMock()
        mock_staff.id = 1
        mock_staff.full_name = 'John Doe'
        mock_staff.role = 'admin'

        mock_session.query.return_value.filter.return_value.first.return_value = mock_staff

        mock_activities = [
            MagicMock(activity_type='case_completed', response_time_minutes=30, quality_score=8, was_escalated=False, required_revision=False),
            MagicMock(activity_type='letter_sent', response_time_minutes=60, quality_score=10, was_escalated=False, required_revision=False),
        ]
        mock_session.query.return_value.filter.return_value.all.return_value = mock_activities

        service = StaffPerformanceService(session=mock_session)
        result = service.get_staff_metrics(staff_id=1)

        assert result['response_time']['average_minutes'] == 45.0  # (30+60)/2
        assert result['quality']['average_score'] == 9.0  # (8+10)/2


class TestGetTeamMetrics:
    """Tests for get_team_metrics method."""

    def test_returns_team_metrics(self):
        """Test returns team metrics."""
        mock_session = MagicMock(spec=Session)

        mock_staff = [
            MagicMock(id=1, full_name='John', role='admin', is_active=True),
            MagicMock(id=2, full_name='Jane', role='staff', is_active=True),
        ]
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            mock_staff,  # Staff query
            [],  # Activities query
        ]

        service = StaffPerformanceService(session=mock_session)
        result = service.get_team_metrics()

        assert 'summary' in result
        assert 'staff_breakdown' in result
        assert result['summary']['total_staff'] == 2


class TestGetLeaderboard:
    """Tests for get_leaderboard method."""

    def test_returns_ranked_list(self):
        """Test returns ranked leaderboard."""
        mock_session = MagicMock(spec=Session)

        mock_staff = [
            MagicMock(id=1, full_name='John', role='admin', initials='JD', is_active=True),
            MagicMock(id=2, full_name='Jane', role='staff', initials='JS', is_active=True),
        ]
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            mock_staff,  # First staff query
            [MagicMock(activity_type='case_completed', response_time_minutes=30) for _ in range(5)],  # John's activities
            [MagicMock(activity_type='case_completed', response_time_minutes=60) for _ in range(3)],  # Jane's activities
        ]

        service = StaffPerformanceService(session=mock_session)
        result = service.get_leaderboard(period='month', limit=10)

        assert isinstance(result, list)

    def test_period_filtering(self):
        """Test period filtering options."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.all.return_value = []

        service = StaffPerformanceService(session=mock_session)

        for period in ['day', 'week', 'month', 'quarter', 'year', 'all']:
            result = service.get_leaderboard(period=period)
            assert isinstance(result, list)

    def test_metric_sorting(self):
        """Test sorting by different metrics."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.all.return_value = []

        service = StaffPerformanceService(session=mock_session)

        for metric in ['points', 'activities', 'response_time', 'cases']:
            result = service.get_leaderboard(metric=metric)
            assert isinstance(result, list)


class TestGetStaffActivities:
    """Tests for get_staff_activities method."""

    def test_returns_activities(self):
        """Test returns activity list."""
        mock_session = MagicMock(spec=Session)
        mock_activities = [
            MagicMock(to_dict=MagicMock(return_value={'id': 1})),
            MagicMock(to_dict=MagicMock(return_value={'id': 2})),
        ]
        mock_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_activities

        service = StaffPerformanceService(session=mock_session)
        result = service.get_staff_activities(staff_id=1)

        assert len(result) == 2


class TestGetRecentTeamActivities:
    """Tests for get_recent_team_activities method."""

    def test_returns_recent_activities(self):
        """Test returns recent team activities."""
        mock_session = MagicMock(spec=Session)

        mock_activity = MagicMock()
        mock_activity.staff_id = 1
        mock_activity.to_dict.return_value = {'id': 1}

        mock_staff = MagicMock()
        mock_staff.full_name = 'John Doe'
        mock_staff.initials = 'JD'

        mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_activity]
        mock_session.query.return_value.filter.return_value.first.return_value = mock_staff

        service = StaffPerformanceService(session=mock_session)
        result = service.get_recent_team_activities()

        assert len(result) == 1
        assert result[0]['staff_name'] == 'John Doe'


class TestGetPerformanceTrend:
    """Tests for get_performance_trend method."""

    def test_returns_daily_trend(self):
        """Test returns daily performance trend."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.all.return_value = []

        service = StaffPerformanceService(session=mock_session)
        result = service.get_performance_trend(days=7)

        assert isinstance(result, list)
        # Should have entries for each day
        assert len(result) >= 7


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary method."""

    def test_returns_summary(self):
        """Test returns comprehensive dashboard summary."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value.count.return_value = 5
        mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = StaffPerformanceService(session=mock_session)

        with patch.object(service, 'get_leaderboard', return_value=[]):
            with patch.object(service, 'get_recent_team_activities', return_value=[]):
                result = service.get_dashboard_summary()

        assert 'today' in result
        assert 'week' in result
        assert 'month' in result
        assert 'team' in result
        assert 'top_performers' in result
        assert 'recent_activities' in result


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_log_staff_activity(self):
        """Test log_staff_activity convenience function."""
        with patch.object(StaffPerformanceService, 'log_activity') as mock_log:
            mock_log.return_value = (True, 'Success', {'id': 1})

            success, message, data = log_staff_activity(
                staff_id=1,
                activity_type='case_completed',
                description='Test'
            )

            assert success == True

    def test_get_staff_leaderboard(self):
        """Test get_staff_leaderboard convenience function."""
        with patch.object(StaffPerformanceService, 'get_leaderboard') as mock_lb:
            mock_lb.return_value = [{'rank': 1, 'name': 'John'}]

            result = get_staff_leaderboard(period='month', limit=10)

            assert len(result) == 1

    def test_get_performance_dashboard(self):
        """Test get_performance_dashboard convenience function."""
        with patch.object(StaffPerformanceService, 'get_dashboard_summary') as mock_dash:
            mock_dash.return_value = {'today': {}, 'week': {}}

            result = get_performance_dashboard()

            assert 'today' in result
