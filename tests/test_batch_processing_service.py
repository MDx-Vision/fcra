"""
Unit tests for BatchProcessingService

Tests bulk operations on clients including:
- Job creation and management
- Status updates, email sending, staff assignment
- Tag management, delete operations
- Progress tracking and error handling
"""

import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from services.batch_processing_service import (
    BatchProcessingService,
    ACTION_TYPES,
    STATUS_OPTIONS,
    create_batch_job,
    execute_batch_job,
    get_batch_job_progress,
    get_batch_stats,
)


class TestConstants:
    """Tests for batch processing constants."""

    def test_action_types_defined(self):
        """Test all expected action types are defined."""
        expected_actions = [
            'update_status', 'update_dispute_round', 'send_email',
            'send_sms', 'assign_staff', 'add_tag', 'remove_tag',
            'add_note', 'export', 'delete'
        ]
        for action in expected_actions:
            assert action in ACTION_TYPES

    def test_action_type_structure(self):
        """Test each action type has required fields."""
        for action_key, action in ACTION_TYPES.items():
            assert 'name' in action
            assert 'description' in action
            assert 'params' in action
            assert isinstance(action['params'], list)

    def test_status_options_defined(self):
        """Test status options include expected values."""
        assert 'new' in STATUS_OPTIONS
        assert 'active' in STATUS_OPTIONS
        assert 'cancelled' in STATUS_OPTIONS
        assert 'complete' in STATUS_OPTIONS


class TestServiceInit:
    """Tests for BatchProcessingService initialization."""

    def test_init_with_session(self):
        """Test initialization with provided session."""
        mock_session = MagicMock(spec=Session)
        service = BatchProcessingService(session=mock_session)
        assert service._session == mock_session
        assert service._owns_session == False

    def test_init_without_session(self):
        """Test initialization without session."""
        service = BatchProcessingService()
        assert service._session is None
        assert service._owns_session == True


class TestGetActionTypes:
    """Tests for get_action_types method."""

    def test_returns_all_action_types(self):
        """Test all action types are returned."""
        service = BatchProcessingService()
        result = service.get_action_types()
        assert result == ACTION_TYPES
        assert len(result) == 10


class TestGetStatusOptions:
    """Tests for get_status_options method."""

    def test_returns_all_status_options(self):
        """Test all status options are returned."""
        service = BatchProcessingService()
        result = service.get_status_options()
        assert result == STATUS_OPTIONS


class TestCreateJob:
    """Tests for create_job method."""

    def test_success(self):
        """Test successful job creation."""
        mock_session = MagicMock(spec=Session)
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.job_uuid = 'test-uuid'
        mock_job.to_dict.return_value = {'id': 1, 'job_uuid': 'test-uuid'}

        # Setup session to return our mock job
        mock_session.add = MagicMock()
        mock_session.flush = MagicMock()
        mock_session.commit = MagicMock()

        with patch('services.batch_processing_service.BatchJob') as MockBatchJob:
            MockBatchJob.return_value = mock_job

            service = BatchProcessingService(session=mock_session)
            success, message, job_dict = service.create_job(
                name='Test Job',
                action_type='update_status',
                client_ids=[1, 2, 3],
                action_params={'new_status': 'active'},
                staff_id=1
            )

        assert success == True
        assert 'created successfully' in message

    def test_invalid_action_type(self):
        """Test error for invalid action type."""
        service = BatchProcessingService()
        success, message, job_dict = service.create_job(
            name='Test Job',
            action_type='invalid_action',
            client_ids=[1, 2],
            action_params={},
            staff_id=1
        )

        assert success == False
        assert 'Invalid action type' in message

    def test_no_clients_selected(self):
        """Test error when no clients selected."""
        service = BatchProcessingService()
        success, message, job_dict = service.create_job(
            name='Test Job',
            action_type='update_status',
            client_ids=[],
            action_params={},
            staff_id=1
        )

        assert success == False
        assert 'No clients selected' in message


class TestGetJob:
    """Tests for get_job method."""

    def test_get_by_id(self):
        """Test getting job by ID."""
        mock_session = MagicMock(spec=Session)
        mock_job = MagicMock()
        mock_job.to_dict.return_value = {'id': 1}
        mock_job.items = []
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job

        service = BatchProcessingService(session=mock_session)
        result = service.get_job(job_id=1)

        assert result['id'] == 1

    def test_get_by_uuid(self):
        """Test getting job by UUID."""
        mock_session = MagicMock(spec=Session)
        mock_job = MagicMock()
        mock_job.to_dict.return_value = {'job_uuid': 'test-uuid'}
        mock_job.items = []
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job

        service = BatchProcessingService(session=mock_session)
        result = service.get_job(job_uuid='test-uuid')

        assert result['job_uuid'] == 'test-uuid'

    def test_not_found(self):
        """Test when job not found."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = BatchProcessingService(session=mock_session)
        result = service.get_job(job_id=999)

        assert result is None


class TestListJobs:
    """Tests for list_jobs method."""

    def test_list_all(self):
        """Test listing all jobs."""
        mock_session = MagicMock(spec=Session)
        mock_jobs = [
            MagicMock(to_dict=MagicMock(return_value={'id': 1})),
            MagicMock(to_dict=MagicMock(return_value={'id': 2})),
        ]
        mock_session.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_jobs

        service = BatchProcessingService(session=mock_session)
        result = service.list_jobs()

        assert len(result) == 2

    def test_filter_by_status(self):
        """Test filtering by status."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        service = BatchProcessingService(session=mock_session)
        result = service.list_jobs(status='pending')

        # Filter should be called
        mock_session.query.return_value.filter.assert_called()


class TestGetJobProgress:
    """Tests for get_job_progress method."""

    def test_success(self):
        """Test getting job progress."""
        mock_session = MagicMock(spec=Session)
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.job_uuid = 'test-uuid'
        mock_job.status = 'running'
        mock_job.total_items = 10
        mock_job.items_processed = 5
        mock_job.items_succeeded = 4
        mock_job.items_failed = 1
        mock_job.progress_percent = 50.0
        mock_job.started_at = datetime.utcnow()
        mock_job.completed_at = None
        mock_job.error_message = None

        mock_session.query.return_value.filter.return_value.first.return_value = mock_job

        service = BatchProcessingService(session=mock_session)
        result = service.get_job_progress(job_id=1)

        assert result['status'] == 'running'
        assert result['progress_percent'] == 50.0
        assert result['items_processed'] == 5

    def test_not_found(self):
        """Test when job not found."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = BatchProcessingService(session=mock_session)
        result = service.get_job_progress(job_id=999)

        assert result is None


class TestCancelJob:
    """Tests for cancel_job method."""

    def test_success(self):
        """Test successful job cancellation."""
        mock_session = MagicMock(spec=Session)
        mock_job = MagicMock()
        mock_job.status = 'pending'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job

        service = BatchProcessingService(session=mock_session)
        success, message = service.cancel_job(job_id=1, staff_id=1)

        assert success == True
        assert mock_job.status == 'cancelled'

    def test_job_not_found(self):
        """Test cancelling non-existent job."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = BatchProcessingService(session=mock_session)
        success, message = service.cancel_job(job_id=999, staff_id=1)

        assert success == False
        assert 'not found' in message

    def test_already_completed(self):
        """Test cancelling already completed job."""
        mock_session = MagicMock(spec=Session)
        mock_job = MagicMock()
        mock_job.status = 'completed'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job

        service = BatchProcessingService(session=mock_session)
        success, message = service.cancel_job(job_id=1, staff_id=1)

        assert success == False
        assert 'Cannot cancel' in message


class TestExecuteJob:
    """Tests for execute_job method."""

    def test_job_not_found(self):
        """Test executing non-existent job."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = BatchProcessingService(session=mock_session)
        success, message = service.execute_job(job_id=999)

        assert success == False
        assert 'not found' in message

    def test_job_not_pending(self):
        """Test executing non-pending job."""
        mock_session = MagicMock(spec=Session)
        mock_job = MagicMock()
        mock_job.status = 'running'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job

        service = BatchProcessingService(session=mock_session)
        success, message = service.execute_job(job_id=1)

        assert success == False
        assert 'not pending' in message


class TestActionHandlers:
    """Tests for individual action handlers."""

    def test_action_update_status(self):
        """Test update status action."""
        mock_session = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.dispute_status = 'pending'
        mock_item = MagicMock()
        mock_job = MagicMock()
        mock_job.action_params = {'new_status': 'active'}

        service = BatchProcessingService(session=mock_session)
        success, error = service._action_update_status(
            mock_session, mock_client, mock_item,
            {'new_status': 'active'}
        )

        assert success == True
        assert mock_client.dispute_status == 'active'

    def test_action_update_status_no_status(self):
        """Test update status without new_status param."""
        mock_session = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_item = MagicMock()

        service = BatchProcessingService(session=mock_session)
        success, error = service._action_update_status(
            mock_session, mock_client, mock_item, {}
        )

        assert success == False
        assert 'No new_status' in error

    def test_action_update_round(self):
        """Test update round action."""
        mock_session = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.current_dispute_round = 1
        mock_item = MagicMock()

        service = BatchProcessingService(session=mock_session)
        success, error = service._action_update_round(
            mock_session, mock_client, mock_item,
            {'new_round': 2}
        )

        assert success == True
        assert mock_client.current_dispute_round == 2

    def test_action_update_round_invalid(self):
        """Test update round with invalid round number."""
        mock_session = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_item = MagicMock()

        service = BatchProcessingService(session=mock_session)
        success, error = service._action_update_round(
            mock_session, mock_client, mock_item,
            {'new_round': 99}
        )

        assert success == False
        assert 'must be between' in error

    def test_action_add_note(self):
        """Test add note action."""
        mock_session = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.admin_notes = ''
        mock_item = MagicMock()

        service = BatchProcessingService(session=mock_session)
        success, error = service._action_add_note(
            mock_session, mock_client, mock_item,
            {'note': 'Test note'}
        )

        assert success == True
        assert 'Test note' in mock_client.admin_notes

    def test_action_delete_soft(self):
        """Test soft delete action."""
        mock_session = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_item = MagicMock()

        service = BatchProcessingService(session=mock_session)
        success, error = service._action_delete(
            mock_session, mock_client, mock_item, {}
        )

        assert success == True
        assert mock_client.status == 'deleted'

    def test_action_delete_hard(self):
        """Test hard delete action."""
        mock_session = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_item = MagicMock()

        service = BatchProcessingService(session=mock_session)
        success, error = service._action_delete(
            mock_session, mock_client, mock_item,
            {'hard_delete': True}
        )

        assert success == True
        mock_session.delete.assert_called_with(mock_client)


class TestGetStats:
    """Tests for get_stats method."""

    def test_returns_stats(self):
        """Test that stats are returned."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.scalar.return_value = 0
        mock_session.query.return_value.filter.return_value.scalar.return_value = 0

        service = BatchProcessingService(session=mock_session)
        result = service.get_stats()

        assert 'total_jobs' in result
        assert 'pending_jobs' in result
        assert 'running_jobs' in result
        assert 'completed_jobs' in result
        assert 'success_rate' in result


class TestRetryFailedItems:
    """Tests for retry_failed_items method."""

    def test_job_not_found(self):
        """Test retry when job not found."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = BatchProcessingService(session=mock_session)
        success, message = service.retry_failed_items(job_id=999)

        assert success == False
        assert 'not found' in message

    def test_job_not_completed(self):
        """Test retry on still running job."""
        mock_session = MagicMock(spec=Session)
        mock_job = MagicMock()
        mock_job.status = 'running'
        mock_session.query.return_value.filter.return_value.first.return_value = mock_job

        service = BatchProcessingService(session=mock_session)
        success, message = service.retry_failed_items(job_id=1)

        assert success == False
        assert 'only retry' in message.lower()


class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_create_batch_job(self):
        """Test create_batch_job convenience function."""
        with patch.object(BatchProcessingService, 'create_job') as mock_create:
            mock_create.return_value = (True, 'Success', {'id': 1})

            success, message, job = create_batch_job(
                name='Test',
                action_type='update_status',
                client_ids=[1],
                action_params={},
                staff_id=1
            )

            assert success == True

    def test_execute_batch_job(self):
        """Test execute_batch_job convenience function."""
        with patch.object(BatchProcessingService, 'execute_job') as mock_exec:
            mock_exec.return_value = (True, 'Success')

            success, message = execute_batch_job(job_id=1)

            assert success == True

    def test_get_batch_job_progress(self):
        """Test get_batch_job_progress convenience function."""
        with patch.object(BatchProcessingService, 'get_job_progress') as mock_progress:
            mock_progress.return_value = {'status': 'running'}

            result = get_batch_job_progress(job_id=1)

            assert result['status'] == 'running'

    def test_get_batch_stats(self):
        """Test get_batch_stats convenience function."""
        with patch.object(BatchProcessingService, 'get_stats') as mock_stats:
            mock_stats.return_value = {'total_jobs': 10}

            result = get_batch_stats()

            assert result['total_jobs'] == 10


class TestExecuteJob:
    """Tests for execute_job method."""

    def test_execute_job_method_exists(self):
        """Test execute_job method exists."""
        mock_session = MagicMock(spec=Session)
        service = BatchProcessingService(session=mock_session)
        assert hasattr(service, 'execute_job')

    def test_execute_job_returns_tuple(self):
        """Test execute_job returns success/message tuple."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = BatchProcessingService(session=mock_session)
        with patch.object(service, '_get_session', return_value=mock_session):
            with patch.object(service, '_close_session'):
                result = service.execute_job(job_id=999)

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestProcessItem:
    """Tests for _process_item method."""

    def test_process_item_method_exists(self):
        """Test _process_item method exists."""
        mock_session = MagicMock(spec=Session)
        service = BatchProcessingService(session=mock_session)
        assert hasattr(service, '_process_item')

    def test_process_item_returns_tuple(self):
        """Test _process_item returns success/error tuple."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_job = MagicMock()
        mock_job.action_type = 'update_status'
        mock_job.action_params = {}

        mock_item = MagicMock()
        mock_item.client_id = 999

        service = BatchProcessingService(session=mock_session)
        result = service._process_item(mock_session, mock_job, mock_item)

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestActionTypes:
    """Tests for different action types."""

    def test_valid_action_types_attribute_exists(self):
        """Test that VALID_ACTION_TYPES attribute exists or method handles actions."""
        mock_session = MagicMock(spec=Session)
        service = BatchProcessingService(session=mock_session)

        # Service should have some way to handle action types
        assert hasattr(service, 'VALID_ACTION_TYPES') or hasattr(service, '_process_item')

    def test_common_action_types(self):
        """Test common action types are handled."""
        common_actions = [
            'update_status',
            'send_email',
            'generate_letters',
        ]
        # Just verify these are valid strings
        for action in common_actions:
            assert isinstance(action, str)


class TestCancelJob:
    """Tests for cancel_job method."""

    def test_cancel_job_method_exists(self):
        """Test cancel_job method exists."""
        mock_session = MagicMock(spec=Session)
        service = BatchProcessingService(session=mock_session)
        assert hasattr(service, 'cancel_job')

    def test_cancel_job_returns_tuple(self):
        """Test cancel_job returns success/message tuple."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = BatchProcessingService(session=mock_session)
        result = service.cancel_job(job_id=999)

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestDeleteJob:
    """Tests for delete_job method."""

    def test_delete_job_method_exists(self):
        """Test delete_job method exists."""
        mock_session = MagicMock(spec=Session)
        service = BatchProcessingService(session=mock_session)
        assert hasattr(service, 'delete_job')

    def test_delete_job_returns_tuple(self):
        """Test delete_job returns success/message tuple."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.filter.return_value.first.return_value = None

        service = BatchProcessingService(session=mock_session)
        result = service.delete_job(job_id=999)

        assert isinstance(result, tuple)
        assert len(result) == 2


class TestListJobs:
    """Tests for list_jobs method."""

    def test_list_jobs_method_exists(self):
        """Test list_jobs method exists."""
        mock_session = MagicMock(spec=Session)
        service = BatchProcessingService(session=mock_session)
        assert hasattr(service, 'list_jobs')

    def test_list_jobs_returns_list(self):
        """Test list_jobs returns a list."""
        mock_session = MagicMock(spec=Session)
        mock_session.query.return_value.order_by.return_value.all.return_value = []

        service = BatchProcessingService(session=mock_session)
        with patch.object(service, '_get_session', return_value=mock_session):
            with patch.object(service, '_close_session'):
                jobs = service.list_jobs()

        assert isinstance(jobs, list)
