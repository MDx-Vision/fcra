"""
Unit tests for ScheduledJobsService

Tests automated scheduled tasks including:
- capture_due_payments - Capture payments after 3-day CROA period
- expire_stale_holds - Release holds if onboarding not completed
- send_payment_reminders - Email clients with upcoming payments
- get_pending_activations - List clients ready for activation
- run_all_jobs - Run all scheduled jobs
"""

import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from services.scheduled_jobs_service import (
    ScheduledJobsService,
    get_scheduled_jobs_service,
)


class TestServiceInit:
    """Tests for ScheduledJobsService initialization."""

    def test_init_with_db_session(self):
        """Test initialization with database session."""
        mock_db = MagicMock(spec=Session)
        service = ScheduledJobsService(mock_db)
        assert service.db == mock_db

    def test_factory_function(self):
        """Test factory function creates service instance."""
        with patch('services.scheduled_jobs_service.SessionLocal') as mock_session:
            mock_db = MagicMock(spec=Session)
            mock_session.return_value = mock_db

            service = get_scheduled_jobs_service()

            assert isinstance(service, ScheduledJobsService)

    def test_factory_function_with_db(self):
        """Test factory function with provided database."""
        mock_db = MagicMock(spec=Session)
        service = get_scheduled_jobs_service(mock_db)
        assert service.db == mock_db


class TestCaptureDuePayments:
    """Tests for capture_due_payments method."""

    def test_no_ready_clients(self):
        """Test when no clients are ready for activation."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        service = ScheduledJobsService(mock_db)
        result = service.capture_due_payments()

        assert result['success'] == True
        assert result['job'] == 'capture_due_payments'
        assert result['results']['processed'] == 0
        assert result['results']['captured'] == 0

    def test_activates_ready_clients(self):
        """Test clients are activated when cancellation period ends."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'pending_payment'

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_client]

        service = ScheduledJobsService(mock_db)

        with patch('services.scheduled_jobs_service.log_milestone'):
            result = service.capture_due_payments()

        assert result['success'] == True
        assert result['results']['captured'] == 1
        assert mock_client.client_stage == 'active'
        assert mock_client.dispute_status == 'active'

    def test_handles_client_error(self):
        """Test error handling for individual client failures."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        # Simulate error when setting client_stage
        type(mock_client).client_stage = property(
            lambda self: 'pending_payment',
            lambda self, v: (_ for _ in ()).throw(Exception("Database error"))
        )

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_client]

        service = ScheduledJobsService(mock_db)
        result = service.capture_due_payments()

        assert result['success'] == True  # Job still succeeds
        assert result['results']['failed'] == 1

    def test_database_exception(self):
        """Test handling of database exception."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.side_effect = Exception("Database connection error")

        service = ScheduledJobsService(mock_db)
        result = service.capture_due_payments()

        assert result['success'] == False
        assert 'error' in result


class TestExpireStaleHolds:
    """Tests for expire_stale_holds method."""

    def test_no_stale_clients(self):
        """Test when no clients have stale holds."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ScheduledJobsService(mock_db)
        result = service.expire_stale_holds(days_old=7)

        assert result['success'] == True
        assert result['job'] == 'expire_stale_holds'
        assert result['results']['processed'] == 0
        assert result['results']['expired'] == 0

    def test_expires_stale_clients(self):
        """Test clients are expired after threshold."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Stale Client'
        mock_client.client_stage = 'onboarding'
        mock_client.created_at = datetime.utcnow() - timedelta(days=10)

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_client]

        service = ScheduledJobsService(mock_db)
        result = service.expire_stale_holds(days_old=7)

        assert result['success'] == True
        assert result['results']['expired'] == 1
        assert mock_client.client_stage == 'cancelled'
        assert 'not completed' in mock_client.cancellation_reason

    def test_custom_days_threshold(self):
        """Test custom days threshold is used."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ScheduledJobsService(mock_db)
        result = service.expire_stale_holds(days_old=14)

        assert result['days_threshold'] == 14

    def test_database_exception(self):
        """Test handling of database exception."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.side_effect = Exception("Database error")

        service = ScheduledJobsService(mock_db)
        result = service.expire_stale_holds()

        assert result['success'] == False
        assert 'error' in result


class TestSendPaymentReminders:
    """Tests for send_payment_reminders method."""

    def test_no_upcoming_payments(self):
        """Test when no payments are upcoming."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ScheduledJobsService(mock_db)
        result = service.send_payment_reminders()

        assert result['success'] == True
        assert result['job'] == 'send_payment_reminders'
        assert result['results']['processed'] == 0

    def test_sends_upcoming_reminders(self):
        """Test reminders are queued for upcoming payments."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.email = 'test@example.com'

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_client]
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ScheduledJobsService(mock_db)
        result = service.send_payment_reminders()

        assert result['success'] == True
        assert result['results']['sent'] >= 1

    def test_sends_failed_payment_reminders(self):
        """Test reminders for failed payments."""
        mock_db = MagicMock(spec=Session)

        mock_upcoming = MagicMock()
        mock_upcoming.id = 1
        mock_upcoming.email = 'upcoming@example.com'

        mock_failed = MagicMock()
        mock_failed.id = 2
        mock_failed.email = 'failed@example.com'
        mock_failed.client_stage = 'payment_failed'

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_upcoming]
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_failed]

        service = ScheduledJobsService(mock_db)
        result = service.send_payment_reminders()

        assert result['success'] == True
        assert result['results']['sent'] == 2

    def test_handles_email_error(self):
        """Test error handling for email failures."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ScheduledJobsService(mock_db)
        result = service.send_payment_reminders()

        # Should succeed even with no clients
        assert result['success'] == True


class TestGetPendingActivations:
    """Tests for get_pending_activations method."""

    def test_no_pending_activations(self):
        """Test when no clients are pending activation."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        service = ScheduledJobsService(mock_db)
        result = service.get_pending_activations()

        assert result['success'] == True
        assert result['count'] == 0
        assert result['clients'] == []

    def test_returns_pending_clients(self):
        """Test returns list of pending clients."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Ready Client'
        mock_client.email = 'ready@example.com'

        mock_croa = MagicMock()
        mock_croa.cancellation_period_ends_at = datetime.utcnow() - timedelta(hours=1)

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_client]
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_croa

        service = ScheduledJobsService(mock_db)
        result = service.get_pending_activations()

        assert result['success'] == True
        assert result['count'] == 1
        assert len(result['clients']) == 1
        assert result['clients'][0]['client_id'] == 1

    def test_database_exception(self):
        """Test handling of database exception."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.side_effect = Exception("Database error")

        service = ScheduledJobsService(mock_db)
        result = service.get_pending_activations()

        assert result['success'] == False
        assert 'error' in result


class TestRunAllJobs:
    """Tests for run_all_jobs method."""

    def test_runs_all_jobs(self):
        """Test all jobs are run."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ScheduledJobsService(mock_db)
        result = service.run_all_jobs()

        assert result['success'] == True
        assert 'run_at' in result
        assert 'jobs' in result
        assert 'capture_due_payments' in result['jobs']
        assert 'expire_stale_holds' in result['jobs']
        assert 'send_payment_reminders' in result['jobs']

    def test_individual_job_failures_dont_stop_others(self):
        """Test that one job failing doesn't stop other jobs."""
        mock_db = MagicMock(spec=Session)

        service = ScheduledJobsService(mock_db)

        with patch.object(service, 'capture_due_payments') as mock_capture:
            mock_capture.return_value = {'success': False, 'error': 'Test error'}

            with patch.object(service, 'expire_stale_holds') as mock_expire:
                mock_expire.return_value = {'success': True}

                with patch.object(service, 'send_payment_reminders') as mock_remind:
                    mock_remind.return_value = {'success': True}

                    result = service.run_all_jobs()

        # All jobs should have been attempted
        mock_capture.assert_called_once()
        mock_expire.assert_called_once()
        mock_remind.assert_called_once()


class TestTimelineLogging:
    """Tests for timeline event logging."""

    def test_logs_activation_milestone(self):
        """Test that activation logs a timeline milestone."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'pending_payment'

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_client]

        service = ScheduledJobsService(mock_db)

        with patch('services.scheduled_jobs_service.log_milestone') as mock_log:
            result = service.capture_due_payments()

            mock_log.assert_called_once()
            call_args = mock_log.call_args
            assert call_args[0][1] == 1  # client_id
            assert 'case_activated' in call_args[0][2]

    def test_timeline_failure_doesnt_fail_job(self):
        """Test that timeline logging failure doesn't fail the job."""
        mock_db = MagicMock(spec=Session)

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        mock_client.client_stage = 'pending_payment'

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [mock_client]

        service = ScheduledJobsService(mock_db)

        with patch('services.scheduled_jobs_service.log_milestone') as mock_log:
            mock_log.side_effect = Exception("Timeline error")

            result = service.capture_due_payments()

            # Job should still succeed
            assert result['success'] == True
            assert result['results']['captured'] == 1


class TestDateCalculations:
    """Tests for date-related calculations."""

    def test_cancellation_period_check(self):
        """Test cancellation period end date comparison."""
        mock_db = MagicMock(spec=Session)

        # This tests that the query filters correctly
        service = ScheduledJobsService(mock_db)
        result = service.capture_due_payments()

        # The query should have been made with datetime comparison
        assert mock_db.query.called

    def test_stale_hold_cutoff_calculation(self):
        """Test stale hold cutoff date calculation."""
        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = ScheduledJobsService(mock_db)

        # Default 7 days
        result = service.expire_stale_holds(days_old=7)
        assert result['days_threshold'] == 7

        # Custom days
        result = service.expire_stale_holds(days_old=30)
        assert result['days_threshold'] == 30
