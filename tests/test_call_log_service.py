"""
Unit tests for CallLogService
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, date, timedelta
from services.call_log_service import CallLogService, get_call_log_service


class TestCallLogServiceConstants:
    """Test service constants and configuration"""

    def test_valid_directions(self):
        """Test valid call directions"""
        assert 'inbound' in CallLogService.DIRECTIONS
        assert 'outbound' in CallLogService.DIRECTIONS
        assert len(CallLogService.DIRECTIONS) == 2

    def test_valid_statuses(self):
        """Test valid call statuses"""
        expected = ['completed', 'missed', 'voicemail', 'no_answer', 'busy', 'cancelled']
        for status in expected:
            assert status in CallLogService.STATUSES

    def test_valid_outcomes(self):
        """Test valid call outcomes"""
        expected_outcomes = [
            'scheduled_appointment', 'left_message', 'follow_up_needed',
            'resolved', 'information_provided', 'document_requested',
            'payment_discussed', 'case_update', 'complaint', 'other'
        ]
        for outcome in expected_outcomes:
            assert outcome in CallLogService.OUTCOMES


class TestCallLogServiceInit:
    """Test service initialization"""

    def test_init_with_db(self):
        """Test service initialization with database session"""
        mock_db = MagicMock()
        service = CallLogService(mock_db)
        assert service.db == mock_db

    def test_factory_function(self):
        """Test factory function creates service"""
        mock_db = MagicMock()
        service = get_call_log_service(mock_db)
        assert isinstance(service, CallLogService)
        assert service.db == mock_db


class TestCreateCallLog:
    """Test call log creation"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    def test_create_call_log_invalid_direction(self):
        """Test create with invalid direction"""
        result = self.service.create_call_log(
            staff_id=1,
            direction='invalid',
            call_started_at=datetime.now()
        )
        assert result['success'] is False
        assert 'Invalid direction' in result['error']

    def test_create_call_log_invalid_status(self):
        """Test create with invalid status"""
        result = self.service.create_call_log(
            staff_id=1,
            direction='outbound',
            call_started_at=datetime.now(),
            status='invalid_status'
        )
        assert result['success'] is False
        assert 'Invalid status' in result['error']

    @patch('database.Staff')
    def test_create_call_log_staff_not_found(self, mock_staff_class):
        """Test create with non-existent staff"""
        self.mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = self.service.create_call_log(
            staff_id=999,
            direction='outbound',
            call_started_at=datetime.now()
        )
        assert result['success'] is False
        assert 'Staff member not found' in result['error']

    @patch('database.Client')
    @patch('database.Staff')
    def test_create_call_log_client_not_found(self, mock_staff_class, mock_client_class):
        """Test create with non-existent client"""
        # Staff found
        mock_staff = MagicMock()
        # Client not found
        def query_side_effect(model):
            mock_query = MagicMock()
            if model == mock_staff_class:
                mock_query.filter_by.return_value.first.return_value = mock_staff
            else:
                mock_query.filter_by.return_value.first.return_value = None
            return mock_query

        self.mock_db.query.side_effect = query_side_effect

        result = self.service.create_call_log(
            staff_id=1,
            direction='outbound',
            call_started_at=datetime.now(),
            client_id=999
        )
        assert result['success'] is False
        assert 'Client not found' in result['error']

    @patch('database.CallLog')
    @patch('database.Staff')
    def test_create_call_log_success(self, mock_staff_class, mock_call_log_class):
        """Test successful call log creation"""
        mock_staff = MagicMock()
        mock_staff.id = 1
        mock_staff.name = 'Test Staff'

        mock_call_log = MagicMock()
        mock_call_log.id = 1
        mock_call_log.client = None
        mock_call_log.staff = mock_staff
        mock_call_log.direction = 'outbound'
        mock_call_log.phone_number = '555-1234'
        mock_call_log.call_started_at = datetime.now()
        mock_call_log.call_ended_at = None
        mock_call_log.duration_seconds = 300
        mock_call_log.status = 'completed'
        mock_call_log.outcome = None
        mock_call_log.subject = 'Test call'
        mock_call_log.notes = None
        mock_call_log.follow_up_required = False
        mock_call_log.follow_up_date = None
        mock_call_log.follow_up_notes = None
        mock_call_log.recording_url = None
        mock_call_log.recording_duration = None
        mock_call_log.created_at = datetime.now()
        mock_call_log.updated_at = datetime.now()

        mock_call_log_class.return_value = mock_call_log
        self.mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        result = self.service.create_call_log(
            staff_id=1,
            direction='outbound',
            call_started_at=datetime.now(),
            phone_number='555-1234',
            subject='Test call',
            duration_seconds=300
        )

        assert result['success'] is True
        assert result['call_log_id'] == 1
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @patch('database.CallLog')
    @patch('database.Staff')
    def test_create_call_log_calculates_duration(self, mock_staff_class, mock_call_log_class):
        """Test duration is calculated from start/end times"""
        mock_staff = MagicMock()
        self.mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        mock_call_log = MagicMock()
        mock_call_log.id = 1
        mock_call_log.client = None
        mock_call_log.staff = mock_staff
        mock_call_log.direction = 'outbound'
        mock_call_log.phone_number = None
        mock_call_log.call_started_at = datetime.now()
        mock_call_log.call_ended_at = None
        mock_call_log.duration_seconds = 300
        mock_call_log.status = 'completed'
        mock_call_log.outcome = None
        mock_call_log.subject = None
        mock_call_log.notes = None
        mock_call_log.follow_up_required = False
        mock_call_log.follow_up_date = None
        mock_call_log.follow_up_notes = None
        mock_call_log.recording_url = None
        mock_call_log.recording_duration = None
        mock_call_log.created_at = datetime.now()
        mock_call_log.updated_at = datetime.now()

        mock_call_log_class.return_value = mock_call_log

        start = datetime(2024, 1, 1, 10, 0, 0)
        end = datetime(2024, 1, 1, 10, 5, 0)  # 5 minutes later

        result = self.service.create_call_log(
            staff_id=1,
            direction='outbound',
            call_started_at=start,
            call_ended_at=end
        )

        # Check that CallLog was created with calculated duration
        call_args = mock_call_log_class.call_args
        assert call_args.kwargs.get('duration_seconds') == 300  # 5 minutes


class TestUpdateCallLog:
    """Test call log updates"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    @patch('database.CallLog')
    def test_update_call_log_not_found(self, mock_call_log_class):
        """Test update with non-existent call log"""
        self.mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = self.service.update_call_log(999, notes='Updated notes')
        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('database.CallLog')
    def test_update_call_log_success(self, mock_call_log_class):
        """Test successful call log update"""
        mock_call_log = MagicMock()
        mock_call_log.id = 1
        mock_call_log.client = None
        mock_call_log.staff = MagicMock(name='Test')
        mock_call_log.direction = 'outbound'
        mock_call_log.phone_number = '555-1234'
        mock_call_log.call_started_at = datetime.now()
        mock_call_log.call_ended_at = None
        mock_call_log.duration_seconds = 300
        mock_call_log.status = 'completed'
        mock_call_log.outcome = None
        mock_call_log.subject = 'Test'
        mock_call_log.notes = 'Updated notes'
        mock_call_log.follow_up_required = False
        mock_call_log.follow_up_date = None
        mock_call_log.follow_up_notes = None
        mock_call_log.recording_url = None
        mock_call_log.recording_duration = None
        mock_call_log.created_at = datetime.now()
        mock_call_log.updated_at = datetime.now()

        self.mock_db.query.return_value.filter_by.return_value.first.return_value = mock_call_log

        result = self.service.update_call_log(1, notes='Updated notes')
        assert result['success'] is True
        self.mock_db.commit.assert_called_once()


class TestDeleteCallLog:
    """Test call log deletion"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    @patch('database.CallLog')
    def test_delete_call_log_not_found(self, mock_call_log_class):
        """Test delete with non-existent call log"""
        self.mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = self.service.delete_call_log(999)
        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('database.CallLog')
    def test_delete_call_log_success(self, mock_call_log_class):
        """Test successful call log deletion"""
        mock_call_log = MagicMock()
        self.mock_db.query.return_value.filter_by.return_value.first.return_value = mock_call_log

        result = self.service.delete_call_log(1)
        assert result['success'] is True
        self.mock_db.delete.assert_called_once_with(mock_call_log)
        self.mock_db.commit.assert_called_once()


class TestGetCallLog:
    """Test getting individual call logs"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    @patch('database.CallLog')
    def test_get_call_log_not_found(self, mock_call_log_class):
        """Test get with non-existent call log"""
        self.mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = self.service.get_call_log(999)
        assert result is None

    @patch('database.CallLog')
    def test_get_call_log_success(self, mock_call_log_class):
        """Test successful call log retrieval"""
        mock_call_log = MagicMock()
        mock_call_log.id = 1
        mock_call_log.client = None
        mock_call_log.staff = MagicMock(name='Test')
        mock_call_log.staff.name = 'Test Staff'
        mock_call_log.direction = 'outbound'
        mock_call_log.phone_number = '555-1234'
        mock_call_log.call_started_at = datetime.now()
        mock_call_log.call_ended_at = None
        mock_call_log.duration_seconds = 300
        mock_call_log.status = 'completed'
        mock_call_log.outcome = 'resolved'
        mock_call_log.subject = 'Test call'
        mock_call_log.notes = 'Test notes'
        mock_call_log.follow_up_required = False
        mock_call_log.follow_up_date = None
        mock_call_log.follow_up_notes = None
        mock_call_log.recording_url = None
        mock_call_log.recording_duration = None
        mock_call_log.created_at = datetime.now()
        mock_call_log.updated_at = datetime.now()

        self.mock_db.query.return_value.filter_by.return_value.first.return_value = mock_call_log

        result = self.service.get_call_log(1)
        assert result is not None
        assert result['id'] == 1
        assert result['direction'] == 'outbound'
        assert result['status'] == 'completed'


class TestGetCallLogs:
    """Test listing call logs with filters"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    @patch('services.call_log_service.desc')
    def test_get_call_logs_empty(self, mock_desc):
        """Test get call logs with no results"""
        mock_query = MagicMock()
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        result = self.service.get_call_logs()
        assert result['call_logs'] == []
        assert result['total'] == 0

    @patch('services.call_log_service.desc')
    def test_get_call_logs_with_filters(self, mock_desc):
        """Test get call logs with various filters"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        result = self.service.get_call_logs(
            client_id=1,
            staff_id=1,
            direction='outbound',
            status='completed',
            date_from=date.today() - timedelta(days=7),
            date_to=date.today()
        )

        assert result['total'] == 0
        # Verify filters were applied
        assert mock_query.filter.called


class TestGetClientCallHistory:
    """Test getting call history for a client"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    @patch('services.call_log_service.desc')
    def test_get_client_call_history(self, mock_desc):
        """Test getting client call history"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.limit.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        result = self.service.get_client_call_history(client_id=1)
        assert isinstance(result, list)


class TestGetStaffCallActivity:
    """Test staff call activity statistics"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    @patch('database.CallLog')
    def test_get_staff_call_activity_empty(self, mock_call_log_class):
        """Test staff activity with no calls"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        result = self.service.get_staff_call_activity(staff_id=1)

        assert result['staff_id'] == 1
        assert result['total_calls'] == 0
        assert result['inbound'] == 0
        assert result['outbound'] == 0

    @patch('database.CallLog')
    def test_get_staff_call_activity_with_calls(self, mock_call_log_class):
        """Test staff activity with calls"""
        mock_call1 = MagicMock()
        mock_call1.direction = 'inbound'
        mock_call1.status = 'completed'
        mock_call1.duration_seconds = 300
        mock_call1.outcome = 'resolved'

        mock_call2 = MagicMock()
        mock_call2.direction = 'outbound'
        mock_call2.status = 'completed'
        mock_call2.duration_seconds = 600
        mock_call2.outcome = 'follow_up_needed'

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_call1, mock_call2]
        self.mock_db.query.return_value = mock_query

        result = self.service.get_staff_call_activity(staff_id=1)

        assert result['total_calls'] == 2
        assert result['inbound'] == 1
        assert result['outbound'] == 1
        assert result['total_duration_seconds'] == 900


class TestPendingFollowUps:
    """Test pending follow-up functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    @patch('database.CallLog')
    def test_get_pending_follow_ups_empty(self, mock_call_log_class):
        """Test getting pending follow-ups with none"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        self.mock_db.query.return_value = mock_query

        result = self.service.get_pending_follow_ups()
        assert result == []

    @patch('database.CallLog')
    def test_mark_follow_up_complete_not_found(self, mock_call_log_class):
        """Test marking follow-up complete with non-existent call"""
        self.mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = self.service.mark_follow_up_complete(999)
        assert result['success'] is False

    @patch('database.CallLog')
    def test_mark_follow_up_complete_success(self, mock_call_log_class):
        """Test successfully marking follow-up complete"""
        mock_call_log = MagicMock()
        mock_call_log.follow_up_required = True
        self.mock_db.query.return_value.filter_by.return_value.first.return_value = mock_call_log

        result = self.service.mark_follow_up_complete(1)
        assert result['success'] is True
        assert mock_call_log.follow_up_required is False
        self.mock_db.commit.assert_called_once()


class TestCallStatistics:
    """Test call statistics"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    @patch('database.CallLog')
    def test_get_call_statistics_empty(self, mock_call_log_class):
        """Test statistics with no calls"""
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        self.mock_db.query.return_value = mock_query

        result = self.service.get_call_statistics()

        assert result['total_calls'] == 0
        assert result['inbound'] == 0
        assert result['outbound'] == 0
        assert 'period' in result

    @patch('database.CallLog')
    def test_get_call_statistics_with_calls(self, mock_call_log_class):
        """Test statistics with calls"""
        mock_call1 = MagicMock()
        mock_call1.direction = 'inbound'
        mock_call1.status = 'completed'
        mock_call1.duration_seconds = 300
        mock_call1.follow_up_required = False
        mock_call1.call_started_at = datetime.now()

        mock_call2 = MagicMock()
        mock_call2.direction = 'outbound'
        mock_call2.status = 'missed'
        mock_call2.duration_seconds = 0
        mock_call2.follow_up_required = True
        mock_call2.call_started_at = datetime.now()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_call1, mock_call2]
        self.mock_db.query.return_value = mock_query

        result = self.service.get_call_statistics()

        assert result['total_calls'] == 2
        assert result['inbound'] == 1
        assert result['outbound'] == 1
        assert result['by_status']['completed'] == 1
        assert result['by_status']['missed'] == 1
        assert result['pending_follow_ups'] == 1


class TestDurationFormatting:
    """Test duration formatting helper"""

    def setup_method(self):
        """Setup for each test"""
        self.mock_db = MagicMock()
        self.service = CallLogService(self.mock_db)

    def test_format_duration_seconds(self):
        """Test formatting seconds only"""
        assert self.service._format_duration(45) == "0:45"

    def test_format_duration_minutes(self):
        """Test formatting minutes and seconds"""
        assert self.service._format_duration(125) == "2:05"

    def test_format_duration_hours(self):
        """Test formatting hours, minutes, and seconds"""
        assert self.service._format_duration(3725) == "1:02:05"

    def test_format_duration_zero(self):
        """Test formatting zero duration"""
        assert self.service._format_duration(0) == "0:00"
