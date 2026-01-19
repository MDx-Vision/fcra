"""
Unit tests for Calendar Sync Service (P33)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from services.calendar_sync_service import CalendarSyncService


class TestCalendarSyncServiceInit:
    """Test service initialization"""

    def test_init_with_db(self):
        """Test initialization with provided db"""
        mock_db = Mock()
        service = CalendarSyncService(db=mock_db)
        assert service.db == mock_db

    @patch('services.calendar_sync_service.get_db')
    def test_init_without_db(self, mock_get_db):
        """Test initialization creates db connection"""
        mock_db = Mock()
        mock_get_db.return_value = mock_db
        service = CalendarSyncService()
        assert service.db == mock_db


class TestGoogleOAuth:
    """Test Google OAuth flow"""

    @patch('services.calendar_sync_service.GOOGLE_CLIENT_ID', 'test-client-id')
    def test_get_google_auth_url(self):
        """Test generating Google auth URL"""
        mock_db = Mock()
        service = CalendarSyncService(db=mock_db)

        url = service.get_google_auth_url(staff_id=1)

        assert 'accounts.google.com' in url
        assert 'client_id=test-client-id' in url
        assert 'state=1' in url
        assert 'calendar' in url.lower()

    @patch('services.calendar_sync_service.GOOGLE_CLIENT_ID', '')
    def test_get_google_auth_url_not_configured(self):
        """Test error when Google not configured"""
        mock_db = Mock()
        service = CalendarSyncService(db=mock_db)

        with pytest.raises(ValueError, match="not configured"):
            service.get_google_auth_url(staff_id=1)

    @patch('services.calendar_sync_service.GOOGLE_CLIENT_ID', 'test-id')
    @patch('services.calendar_sync_service.GOOGLE_CLIENT_SECRET', 'test-secret')
    @patch('requests.post')
    @patch('services.calendar_sync_service.CalendarSyncService._google_list_calendars')
    def test_exchange_google_code_new_integration(self, mock_list_cals, mock_post):
        """Test exchanging Google code for new integration"""
        mock_db = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'access_token': 'test-access-token',
                'refresh_token': 'test-refresh-token',
                'expires_in': 3600
            }
        )
        mock_list_cals.return_value = [
            {'id': 'primary', 'summary': 'My Calendar', 'primary': True}
        ]

        service = CalendarSyncService(db=mock_db)
        result = service.exchange_google_code('auth-code', staff_id=1)

        assert mock_db.add.called
        assert mock_db.commit.called

    @patch('services.calendar_sync_service.GOOGLE_CLIENT_ID', 'test-id')
    @patch('services.calendar_sync_service.GOOGLE_CLIENT_SECRET', 'test-secret')
    @patch('requests.post')
    def test_exchange_google_code_failure(self, mock_post):
        """Test handling Google code exchange failure"""
        mock_db = Mock()
        mock_post.return_value = Mock(
            status_code=400,
            text='Invalid code'
        )

        service = CalendarSyncService(db=mock_db)

        with pytest.raises(Exception, match="Failed to exchange"):
            service.exchange_google_code('bad-code', staff_id=1)


class TestOutlookOAuth:
    """Test Outlook OAuth flow"""

    @patch('services.calendar_sync_service.OUTLOOK_CLIENT_ID', 'test-client-id')
    def test_get_outlook_auth_url(self):
        """Test generating Outlook auth URL"""
        mock_db = Mock()
        service = CalendarSyncService(db=mock_db)

        url = service.get_outlook_auth_url(staff_id=1)

        assert 'login.microsoftonline.com' in url
        assert 'client_id=test-client-id' in url
        assert 'state=1' in url

    @patch('services.calendar_sync_service.OUTLOOK_CLIENT_ID', '')
    def test_get_outlook_auth_url_not_configured(self):
        """Test error when Outlook not configured"""
        mock_db = Mock()
        service = CalendarSyncService(db=mock_db)

        with pytest.raises(ValueError, match="not configured"):
            service.get_outlook_auth_url(staff_id=1)


class TestTokenRefresh:
    """Test token refresh functionality"""

    def test_refresh_tokens_not_expired(self):
        """Test no refresh needed when token valid"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_integration.refresh_token = 'test-refresh'
        mock_integration.token_expires_at = datetime.utcnow() + timedelta(hours=1)

        service = CalendarSyncService(db=mock_db)
        result = service.refresh_tokens(mock_integration)

        assert result is True

    def test_refresh_tokens_no_refresh_token(self):
        """Test failure when no refresh token"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_integration.refresh_token = None

        service = CalendarSyncService(db=mock_db)
        result = service.refresh_tokens(mock_integration)

        assert result is False

    @patch('services.calendar_sync_service.GOOGLE_CLIENT_ID', 'test-id')
    @patch('services.calendar_sync_service.GOOGLE_CLIENT_SECRET', 'test-secret')
    @patch('requests.post')
    def test_refresh_google_tokens(self, mock_post):
        """Test refreshing Google tokens"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_integration.provider = 'google'
        mock_integration.refresh_token = 'test-refresh'
        mock_integration.token_expires_at = datetime.utcnow() - timedelta(hours=1)

        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'access_token': 'new-access-token',
                'expires_in': 3600
            }
        )

        service = CalendarSyncService(db=mock_db)
        result = service.refresh_tokens(mock_integration)

        assert result is True
        assert mock_integration.access_token == 'new-access-token'
        assert mock_db.commit.called


class TestIntegrationManagement:
    """Test integration CRUD operations"""

    def test_get_integration(self):
        """Test getting active integration"""
        mock_db = Mock()
        mock_integration = Mock()
        # Chain filter_by calls (staff_id, is_active, then provider)
        mock_query = Mock()
        mock_query.filter_by.return_value = mock_query
        mock_query.first.return_value = mock_integration
        mock_db.query.return_value = mock_query

        service = CalendarSyncService(db=mock_db)
        result = service.get_integration(staff_id=1, provider='google')

        assert result == mock_integration

    def test_get_integrations(self):
        """Test getting all integrations"""
        mock_db = Mock()
        mock_integrations = [Mock(), Mock()]
        mock_db.query.return_value.filter_by.return_value.all.return_value = mock_integrations

        service = CalendarSyncService(db=mock_db)
        result = service.get_integrations(staff_id=1)

        assert result == mock_integrations

    def test_disconnect_success(self):
        """Test disconnecting integration"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_integration

        service = CalendarSyncService(db=mock_db)
        result = service.disconnect(integration_id=1, staff_id=1)

        assert result is True
        assert mock_integration.is_active is False
        assert mock_integration.access_token is None
        assert mock_db.commit.called

    def test_disconnect_not_found(self):
        """Test disconnecting non-existent integration"""
        mock_db = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        service = CalendarSyncService(db=mock_db)
        result = service.disconnect(integration_id=999, staff_id=1)

        assert result is False

    def test_set_calendar(self):
        """Test setting calendar for integration"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_integration

        service = CalendarSyncService(db=mock_db)
        result = service.set_calendar(
            integration_id=1,
            staff_id=1,
            calendar_id='cal-123',
            calendar_name='My Calendar'
        )

        assert result is True
        assert mock_integration.calendar_id == 'cal-123'
        assert mock_integration.calendar_name == 'My Calendar'


class TestListCalendars:
    """Test listing calendars"""

    @patch('requests.get')
    def test_google_list_calendars(self, mock_get):
        """Test listing Google calendars"""
        mock_db = Mock()
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'items': [
                    {'id': 'primary', 'summary': 'Primary', 'primary': True},
                    {'id': 'cal-2', 'summary': 'Work', 'primary': False}
                ]
            }
        )

        service = CalendarSyncService(db=mock_db)
        result = service._google_list_calendars('test-token')

        assert len(result) == 2
        assert result[0]['id'] == 'primary'
        assert result[0]['primary'] is True

    @patch('requests.get')
    def test_outlook_list_calendars(self, mock_get):
        """Test listing Outlook calendars"""
        mock_db = Mock()
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {
                'value': [
                    {'id': 'cal-1', 'name': 'Calendar', 'isDefaultCalendar': True},
                    {'id': 'cal-2', 'name': 'Work', 'isDefaultCalendar': False}
                ]
            }
        )

        service = CalendarSyncService(db=mock_db)
        result = service._outlook_list_calendars('test-token')

        assert len(result) == 2
        assert result[0]['name'] == 'Calendar'
        assert result[0]['isDefaultCalendar'] is True


class TestFreeBusy:
    """Test free/busy checking"""

    @patch('requests.post')
    def test_google_get_free_busy(self, mock_post):
        """Test getting Google free/busy"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_integration.access_token = 'test-token'
        mock_integration.calendar_id = 'primary'

        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {
                'calendars': {
                    'primary': {
                        'busy': [
                            {'start': '2026-01-20T10:00:00Z', 'end': '2026-01-20T11:00:00Z'}
                        ]
                    }
                }
            }
        )

        service = CalendarSyncService(db=mock_db)
        result = service._google_get_free_busy(
            mock_integration,
            datetime(2026, 1, 20, 0, 0),
            datetime(2026, 1, 21, 0, 0)
        )

        assert len(result) == 1
        assert result[0]['provider'] == 'google'

    def test_is_time_available_no_conflicts(self):
        """Test availability check with no conflicts"""
        mock_db = Mock()
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        service = CalendarSyncService(db=mock_db)
        result = service.is_time_available(
            staff_id=1,
            start_time=datetime(2026, 1, 20, 10, 0),
            end_time=datetime(2026, 1, 20, 11, 0)
        )

        assert result is True


class TestEventSync:
    """Test event sync functionality"""

    @patch('services.calendar_sync_service.CalendarSyncService.refresh_tokens')
    @patch('services.calendar_sync_service.CalendarSyncService.get_integration')
    @patch('services.calendar_sync_service.CalendarSyncService._google_create_event')
    def test_sync_booking_to_google(self, mock_create, mock_get_int, mock_refresh):
        """Test syncing booking to Google Calendar"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_integration.provider = 'google'
        mock_integration.sync_enabled = True
        mock_integration.id = 1

        mock_get_int.return_value = mock_integration
        mock_refresh.return_value = True
        mock_create.return_value = 'event-123'

        # Create mock booking
        mock_booking = Mock()
        mock_booking.id = 1
        mock_booking.booking_type = 'qa_call'
        mock_booking.notes = 'Test notes'
        mock_booking.slot = Mock()
        mock_booking.slot.staff_id = 1
        mock_booking.slot.slot_date = datetime(2026, 1, 20).date()
        mock_booking.slot.slot_time = datetime(2026, 1, 20, 10, 0).time()
        mock_booking.slot.duration_minutes = 15
        mock_booking.client = Mock()
        mock_booking.client.full_name = 'John Doe'
        mock_booking.client.email = 'john@example.com'

        service = CalendarSyncService(db=mock_db)
        result = service.sync_booking_to_calendar(mock_booking)

        assert mock_create.called
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_sync_booking_no_integration(self):
        """Test sync with no calendar integration"""
        mock_db = Mock()

        mock_booking = Mock()
        mock_booking.slot = Mock()
        mock_booking.slot.staff_id = 1

        with patch.object(CalendarSyncService, 'get_integration', return_value=None):
            service = CalendarSyncService(db=mock_db)
            result = service.sync_booking_to_calendar(mock_booking)

        assert result is None

    @patch('services.calendar_sync_service.CalendarSyncService.refresh_tokens')
    @patch('requests.delete')
    def test_delete_calendar_event(self, mock_delete, mock_refresh):
        """Test deleting calendar event"""
        mock_db = Mock()
        mock_event = Mock()
        mock_event.external_event_id = 'event-123'
        mock_event.integration = Mock()
        mock_event.integration.provider = 'google'
        mock_event.integration.calendar_id = 'primary'
        mock_event.integration.access_token = 'test-token'

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_event
        mock_refresh.return_value = True
        mock_delete.return_value = Mock(status_code=204)

        service = CalendarSyncService(db=mock_db)
        result = service.delete_calendar_event(booking_id=1)

        assert result is True
        assert mock_delete.called

    def test_delete_calendar_event_not_found(self):
        """Test deleting non-existent event"""
        mock_db = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        service = CalendarSyncService(db=mock_db)
        result = service.delete_calendar_event(booking_id=999)

        assert result is True  # Nothing to delete is success


class TestGoogleEventCreation:
    """Test Google event creation"""

    @patch('requests.post')
    def test_google_create_event_success(self, mock_post):
        """Test creating Google event"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_integration.access_token = 'test-token'
        mock_integration.calendar_id = 'primary'

        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: {'id': 'event-123'}
        )

        service = CalendarSyncService(db=mock_db)
        result = service._google_create_event(
            mock_integration,
            'Test Event',
            'Description',
            datetime(2026, 1, 20, 10, 0),
            datetime(2026, 1, 20, 11, 0)
        )

        assert result == 'event-123'

    @patch('requests.post')
    def test_google_create_event_failure(self, mock_post):
        """Test Google event creation failure"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_integration.access_token = 'test-token'
        mock_integration.calendar_id = 'primary'

        mock_post.return_value = Mock(
            status_code=400,
            text='Error creating event'
        )

        service = CalendarSyncService(db=mock_db)

        with pytest.raises(Exception, match="Google event creation failed"):
            service._google_create_event(
                mock_integration,
                'Test Event',
                'Description',
                datetime(2026, 1, 20, 10, 0),
                datetime(2026, 1, 20, 11, 0)
            )


class TestOutlookEventCreation:
    """Test Outlook event creation"""

    @patch('requests.post')
    def test_outlook_create_event_success(self, mock_post):
        """Test creating Outlook event"""
        mock_db = Mock()
        mock_integration = Mock()
        mock_integration.access_token = 'test-token'
        mock_integration.calendar_id = 'cal-123'

        mock_post.return_value = Mock(
            status_code=201,
            json=lambda: {'id': 'event-456'}
        )

        service = CalendarSyncService(db=mock_db)
        result = service._outlook_create_event(
            mock_integration,
            'Test Event',
            'Description',
            datetime(2026, 1, 20, 10, 0),
            datetime(2026, 1, 20, 11, 0)
        )

        assert result == 'event-456'


class TestSyncStats:
    """Test sync statistics"""

    def test_get_sync_stats(self):
        """Test getting sync stats"""
        mock_db = Mock()
        mock_integrations = [
            Mock(
                provider='google',
                is_active=True,
                calendar_name='My Calendar',
                last_sync_at=datetime(2026, 1, 19, 10, 0),
                last_sync_status='success',
                sync_enabled=True
            ),
            Mock(
                provider='outlook',
                is_active=False,
                calendar_name=None,
                last_sync_at=None,
                last_sync_status=None,
                sync_enabled=False
            )
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = mock_integrations

        service = CalendarSyncService(db=mock_db)
        stats = service.get_sync_stats(staff_id=1)

        assert stats['total_integrations'] == 2
        assert stats['active_integrations'] == 1
        assert 'google' in stats['providers']
        assert stats['providers']['google']['connected'] is True

    def test_update_sync_status(self):
        """Test updating sync status"""
        mock_db = Mock()
        mock_integration = Mock()

        service = CalendarSyncService(db=mock_db)
        service.update_sync_status(
            mock_integration,
            status='success',
            error=None
        )

        assert mock_integration.last_sync_status == 'success'
        assert mock_integration.last_sync_error is None
        assert mock_db.commit.called


class TestSingletonInstance:
    """Test singleton pattern"""

    @patch('services.calendar_sync_service.get_db')
    def test_get_calendar_service(self, mock_get_db):
        """Test getting singleton service instance"""
        from services.calendar_sync_service import get_calendar_service

        mock_db = Mock()
        mock_get_db.return_value = mock_db

        # Reset singleton
        import services.calendar_sync_service as module
        module._calendar_service = None

        service1 = get_calendar_service()
        service2 = get_calendar_service()

        # Should be same instance
        assert service1 is service2
