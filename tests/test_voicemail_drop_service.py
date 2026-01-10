"""
Unit tests for VoicemailDropService
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from services.voicemail_drop_service import (
    VoicemailDropService,
    VOICEMAIL_CATEGORIES,
    PROVIDERS,
    get_voicemail_drop_service,
)


class TestVoicemailCategories:
    """Test voicemail categories configuration"""

    def test_has_required_categories(self):
        """Should have standard voicemail categories"""
        keys = [c['key'] for c in VOICEMAIL_CATEGORIES]
        assert 'welcome' in keys
        assert 'reminder' in keys
        assert 'update' in keys
        assert 'follow_up' in keys
        assert 'payment' in keys
        assert 'custom' in keys

    def test_categories_have_required_fields(self):
        """Each category should have key, name, description"""
        for cat in VOICEMAIL_CATEGORIES:
            assert 'key' in cat
            assert 'name' in cat
            assert 'description' in cat


class TestProviders:
    """Test provider configurations"""

    def test_has_supported_providers(self):
        """Should have main voicemail drop providers"""
        assert 'slybroadcast' in PROVIDERS
        assert 'dropcowboy' in PROVIDERS
        assert 'twilio' in PROVIDERS

    def test_providers_have_required_fields(self):
        """Each provider should have name, api_url, cost"""
        for key, provider in PROVIDERS.items():
            assert 'name' in provider
            assert 'api_url' in provider
            assert 'cost_per_drop_cents' in provider

    def test_provider_costs_are_reasonable(self):
        """Provider costs should be in expected range (1-10 cents)"""
        for key, provider in PROVIDERS.items():
            cost = provider['cost_per_drop_cents']
            assert 1 <= cost <= 10, f"Provider {key} cost {cost} cents is out of range"


class TestVoicemailDropServiceRecordings:
    """Test recording management"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database"""
        return VoicemailDropService(mock_db)

    def test_create_recording(self, service, mock_db):
        """Should create a recording with all fields"""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_recording(
            name="Test Recording",
            file_path="/static/voicemail/test.mp3",
            category="welcome",
            description="Test description",
            file_name="test.mp3",
            file_size_bytes=1024,
            duration_seconds=30,
            format="mp3",
            staff_id=1
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_recording_not_found(self, service, mock_db):
        """Should return None for non-existent recording"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_recording(999)
        assert result is None

    def test_get_recordings_with_filters(self, service, mock_db):
        """Should filter recordings by category and active status"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = service.get_recordings(category='welcome', active_only=True, limit=50)

        assert mock_db.query.called
        assert mock_query.filter.called

    def test_update_recording(self, service, mock_db):
        """Should update allowed fields"""
        mock_recording = MagicMock()
        mock_recording.is_system = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

        result = service.update_recording(1, name="New Name", category="reminder")

        assert mock_recording.name == "New Name"
        assert mock_recording.category == "reminder"
        mock_db.commit.assert_called()

    def test_delete_recording_soft_delete(self, service, mock_db):
        """Should soft delete (deactivate) recording"""
        mock_recording = MagicMock()
        mock_recording.is_system = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

        result = service.delete_recording(1)

        assert result['success'] is True
        assert mock_recording.is_active is False

    def test_delete_system_recording_fails(self, service, mock_db):
        """Should not delete system recordings"""
        mock_recording = MagicMock()
        mock_recording.is_system = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

        result = service.delete_recording(1)

        assert result['success'] is False
        assert 'system' in result['error'].lower()


class TestVoicemailDropServiceSending:
    """Test voicemail drop sending"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = MagicMock()
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database"""
        svc = VoicemailDropService(mock_db)
        svc.default_provider = 'mock'  # Use mock provider
        return svc

    def test_send_drop_validates_recording(self, service, mock_db):
        """Should fail if recording not found"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.send_drop(recording_id=999, client_id=1)

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_send_drop_validates_client(self, service, mock_db):
        """Should fail if client not found"""
        mock_recording = MagicMock()
        mock_recording.is_active = True

        def query_side_effect(model):
            mock = MagicMock()
            if hasattr(model, '__tablename__') and model.__tablename__ == 'voicemail_recordings':
                mock.filter.return_value.first.return_value = mock_recording
            else:
                mock.filter.return_value.first.return_value = None
            return mock

        mock_db.query.side_effect = query_side_effect

        result = service.send_drop(recording_id=1, client_id=999)

        assert result['success'] is False

    def test_send_drop_validates_phone(self, service, mock_db):
        """Should fail if no phone number"""
        mock_recording = MagicMock()
        mock_recording.is_active = True
        mock_client = MagicMock()
        mock_client.phone = None

        def query_side_effect(model):
            mock = MagicMock()
            if hasattr(model, '__tablename__'):
                if 'recording' in model.__tablename__:
                    mock.filter.return_value.first.return_value = mock_recording
                else:
                    mock.filter.return_value.first.return_value = mock_client
            return mock

        mock_db.query.side_effect = query_side_effect

        result = service.send_drop(recording_id=1, client_id=1)

        assert result['success'] is False
        assert 'phone' in result['error'].lower()

    def test_send_drop_schedules_future(self, service, mock_db):
        """Should schedule drop for future time"""
        mock_recording = MagicMock()
        mock_recording.is_active = True
        mock_client = MagicMock()
        mock_client.phone = "5551234567"
        mock_client.id = 1

        from database import VoicemailRecording, Client

        def query_side_effect(model):
            mock = MagicMock()
            if model == VoicemailRecording:
                mock.filter.return_value.first.return_value = mock_recording
            elif model == Client:
                mock.filter.return_value.first.return_value = mock_client
            return mock

        mock_db.query.side_effect = query_side_effect
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        future_time = datetime.utcnow() + timedelta(hours=1)
        result = service.send_drop(
            recording_id=1,
            client_id=1,
            scheduled_at=future_time
        )

        assert result['status'] == 'scheduled'


class TestVoicemailDropServicePhoneValidation:
    """Test phone number cleaning and validation"""

    @pytest.fixture
    def service(self):
        """Create service with mock database"""
        return VoicemailDropService(MagicMock())

    def test_clean_10_digit_phone(self, service):
        """Should add +1 to 10 digit US numbers"""
        result = service._clean_phone_number("5551234567")
        assert result == "+15551234567"

    def test_clean_11_digit_phone(self, service):
        """Should format 11 digit numbers starting with 1"""
        result = service._clean_phone_number("15551234567")
        assert result == "+15551234567"

    def test_clean_phone_with_formatting(self, service):
        """Should strip non-digits"""
        result = service._clean_phone_number("(555) 123-4567")
        assert result == "+15551234567"

    def test_clean_empty_phone(self, service):
        """Should return None for empty phone"""
        result = service._clean_phone_number("")
        assert result is None

    def test_clean_none_phone(self, service):
        """Should return None for None phone"""
        result = service._clean_phone_number(None)
        assert result is None


class TestVoicemailDropServiceStatus:
    """Test drop status management"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database"""
        return VoicemailDropService(mock_db)

    def test_get_drop_not_found(self, service, mock_db):
        """Should return None for non-existent drop"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_drop(999)
        assert result is None

    def test_get_drops_with_filters(self, service, mock_db):
        """Should filter drops correctly"""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        result = service.get_drops(
            client_id=1,
            status='sent',
            provider='slybroadcast',
            limit=50
        )

        assert mock_db.query.called

    def test_retry_drop_validates_status(self, service, mock_db):
        """Should only retry failed/cancelled drops"""
        mock_drop = MagicMock()
        mock_drop.status = 'sent'  # Not failed
        mock_db.query.return_value.filter.return_value.first.return_value = mock_drop

        result = service.retry_drop(1)

        assert result['success'] is False
        assert 'failed' in result['error'].lower() or 'cancelled' in result['error'].lower()

    def test_cancel_drop_validates_status(self, service, mock_db):
        """Should only cancel pending/scheduled drops"""
        mock_drop = MagicMock()
        mock_drop.status = 'sent'  # Already sent
        mock_db.query.return_value.filter.return_value.first.return_value = mock_drop

        result = service.cancel_drop(1)

        assert result['success'] is False


class TestVoicemailDropServiceCampaigns:
    """Test campaign management"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return MagicMock()

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database"""
        return VoicemailDropService(mock_db)

    def test_create_campaign(self, service, mock_db):
        """Should create campaign with all fields"""
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        result = service.create_campaign(
            name="Test Campaign",
            recording_id=1,
            description="Test",
            target_type="manual",
            staff_id=1
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_campaign_not_found(self, service, mock_db):
        """Should return None for non-existent campaign"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_campaign(999)
        assert result is None

    def test_add_targets_validates_draft_status(self, service, mock_db):
        """Should only add targets to draft campaigns"""
        mock_campaign = MagicMock()
        mock_campaign.status = 'in_progress'  # Not draft
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = service.add_targets_to_campaign(1, [1, 2, 3])

        assert result['success'] is False
        assert 'draft' in result['error'].lower()

    def test_start_campaign_validates_targets(self, service, mock_db):
        """Should not start campaign with no targets"""
        mock_campaign = MagicMock()
        mock_campaign.status = 'draft'
        mock_campaign.total_drops = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = service.start_campaign(1)

        assert result['success'] is False
        assert 'target' in result['error'].lower()

    def test_pause_campaign_validates_status(self, service, mock_db):
        """Should only pause in-progress campaigns"""
        mock_campaign = MagicMock()
        mock_campaign.status = 'draft'  # Not in progress
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = service.pause_campaign(1)

        assert result['success'] is False
        assert 'in-progress' in result['error'].lower() or 'in_progress' in result['error'].lower()


class TestVoicemailDropServiceStatistics:
    """Test statistics methods"""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        db = MagicMock()
        # Set up scalar returns for count queries
        db.query.return_value.filter.return_value.scalar.return_value = 0
        db.query.return_value.group_by.return_value.all.return_value = []
        return db

    @pytest.fixture
    def service(self, mock_db):
        """Create service with mock database"""
        return VoicemailDropService(mock_db)

    def test_get_stats_returns_required_fields(self, service, mock_db):
        """Should return all required stat fields"""
        # Mock the scalar calls
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10
        mock_db.query.return_value.scalar.return_value = 100
        mock_db.query.return_value.group_by.return_value.all.return_value = [
            ('sent', 50), ('failed', 10), ('pending', 5)
        ]

        stats = service.get_stats()

        assert 'total_recordings' in stats
        assert 'total_drops' in stats
        assert 'drops_by_status' in stats
        assert 'sent_count' in stats
        assert 'failed_count' in stats
        assert 'pending_count' in stats
        assert 'total_cost_cents' in stats
        assert 'total_cost_dollars' in stats
        assert 'active_campaigns' in stats
        assert 'recent_drops_24h' in stats

    def test_get_recording_stats_not_found(self, service, mock_db):
        """Should return error for non-existent recording"""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_recording_stats(999)

        assert 'error' in result


class TestMockProvider:
    """Test mock provider for testing"""

    @pytest.fixture
    def service(self):
        """Create service with mock database"""
        return VoicemailDropService(MagicMock())

    def test_mock_provider_returns_success(self, service):
        """Mock provider should return success"""
        mock_drop = MagicMock()
        mock_recording = MagicMock()

        result = service._send_mock(mock_drop, mock_recording)

        assert result['success'] is True
        assert 'provider_id' in result
        assert result['provider_id'].startswith('mock_')


class TestFactoryFunction:
    """Test factory function"""

    def test_get_voicemail_drop_service_creates_instance(self):
        """Should create service instance"""
        with patch('services.voicemail_drop_service.SessionLocal') as mock_session:
            mock_session.return_value = MagicMock()
            service = get_voicemail_drop_service()
            assert isinstance(service, VoicemailDropService)

    def test_get_voicemail_drop_service_uses_provided_db(self):
        """Should use provided database session"""
        mock_db = MagicMock()
        service = get_voicemail_drop_service(db=mock_db)
        assert service.db == mock_db
