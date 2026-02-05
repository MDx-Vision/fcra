"""
Unit tests for Voicemail Drop Service

Tests cover:
- Recording CRUD operations
- Voicemail drop sending
- Provider integrations
- Drop status and history
- Campaign management
- Statistics
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch


class TestVoicemailCategories:
    """Tests for VOICEMAIL_CATEGORIES constant"""

    def test_categories_exist(self):
        """Should have voicemail categories"""
        from services.voicemail_drop_service import VOICEMAIL_CATEGORIES

        assert VOICEMAIL_CATEGORIES is not None
        assert len(VOICEMAIL_CATEGORIES) > 0

    def test_categories_have_keys(self):
        """Should have expected category keys"""
        from services.voicemail_drop_service import VOICEMAIL_CATEGORIES

        keys = [c["key"] for c in VOICEMAIL_CATEGORIES]
        assert "welcome" in keys
        assert "reminder" in keys
        assert "update" in keys
        assert "payment" in keys
        assert "custom" in keys

    def test_categories_have_names(self):
        """Should have names and descriptions"""
        from services.voicemail_drop_service import VOICEMAIL_CATEGORIES

        for category in VOICEMAIL_CATEGORIES:
            assert "name" in category
            assert "description" in category


class TestProviders:
    """Tests for PROVIDERS constant"""

    def test_providers_exist(self):
        """Should have provider configurations"""
        from services.voicemail_drop_service import PROVIDERS

        assert PROVIDERS is not None
        assert "slybroadcast" in PROVIDERS
        assert "dropcowboy" in PROVIDERS
        assert "twilio" in PROVIDERS

    def test_providers_have_config(self):
        """Should have required config fields"""
        from services.voicemail_drop_service import PROVIDERS

        for provider_name, config in PROVIDERS.items():
            assert "name" in config
            assert "api_url" in config
            assert "cost_per_drop_cents" in config


class TestVoicemailDropServiceInit:
    """Tests for VoicemailDropService initialization"""

    def test_creates_instance(self):
        """Should create service instance"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        assert service is not None
        assert service.db == mock_db

    def test_has_default_provider(self):
        """Should have default provider"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        with patch.dict('os.environ', {}, clear=True):
            service = VoicemailDropService(mock_db)

        # Default is slybroadcast when env not set
        assert service.default_provider is not None


class TestRecordingManagement:
    """Tests for recording CRUD operations"""

    def test_create_recording(self):
        """Should create a new recording"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        recording = service.create_recording(
            name="Welcome Message",
            file_path="/path/to/audio.mp3",
            category="welcome",
            description="New client welcome"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_recording_with_all_fields(self):
        """Should create recording with all optional fields"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        recording = service.create_recording(
            name="Test Recording",
            file_path="/path/to/file.mp3",
            category="custom",
            description="Test description",
            file_name="file.mp3",
            file_size_bytes=1024,
            duration_seconds=30,
            format="mp3",
            staff_id=1
        )

        mock_db.add.assert_called_once()

    def test_get_recording(self):
        """Should get recording by ID"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

        service = VoicemailDropService(mock_db)
        result = service.get_recording(1)

        assert result == mock_recording

    def test_get_recording_not_found(self):
        """Should return None for non-existent recording"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VoicemailDropService(mock_db)
        result = service.get_recording(999)

        assert result is None

    def test_get_recordings(self):
        """Should get list of recordings"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recordings = [MagicMock(), MagicMock()]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_recordings

        service = VoicemailDropService(mock_db)
        result = service.get_recordings()

        assert result == mock_recordings

    def test_get_recordings_by_category(self):
        """Should filter recordings by category"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        service.get_recordings(category="welcome")

        # Verify filter was applied
        mock_db.query.return_value.filter.assert_called()

    def test_get_recordings_active_only(self):
        """Should filter active recordings by default"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        service.get_recordings(active_only=True)

        mock_db.query.return_value.filter.assert_called()

    def test_update_recording(self):
        """Should update recording fields"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

        service = VoicemailDropService(mock_db)
        result = service.update_recording(1, name="Updated Name", description="Updated desc")

        assert mock_recording.name == "Updated Name"
        mock_db.commit.assert_called_once()

    def test_update_recording_not_found(self):
        """Should return None for non-existent recording"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VoicemailDropService(mock_db)
        result = service.update_recording(999, name="Test")

        assert result is None

    def test_update_recording_ignores_invalid_fields(self):
        """Should ignore fields not in allowed list"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_recording.file_path = "/original/path.mp3"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

        service = VoicemailDropService(mock_db)
        service.update_recording(1, file_path="/new/path.mp3")

        # file_path should not change (not in allowed_fields)
        assert mock_recording.file_path == "/original/path.mp3"

    def test_delete_recording(self):
        """Should soft delete recording"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_recording.is_system = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

        service = VoicemailDropService(mock_db)
        result = service.delete_recording(1)

        assert result["success"] is True
        assert mock_recording.is_active is False

    def test_delete_recording_not_found(self):
        """Should return error for non-existent recording"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VoicemailDropService(mock_db)
        result = service.delete_recording(999)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_delete_system_recording_fails(self):
        """Should not allow deleting system recordings"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_recording.is_system = True
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

        service = VoicemailDropService(mock_db)
        result = service.delete_recording(1)

        assert result["success"] is False
        assert "system" in result["error"].lower()


class TestSendDrop:
    """Tests for send_drop method"""

    def test_send_drop_success(self):
        """Should send drop successfully"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_recording.is_active = True
        mock_recording.file_path = "/path/to/audio.mp3"

        mock_client = MagicMock()
        mock_client.phone = "1234567890"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_recording, mock_client
        ]

        service = VoicemailDropService(mock_db)

        with patch.object(service, '_send_to_provider') as mock_send:
            mock_send.return_value = {"success": True, "drop_id": 1}

            result = service.send_drop(
                recording_id=1,
                client_id=1
            )

        assert mock_db.add.called
        assert mock_db.commit.called

    def test_send_drop_recording_not_found(self):
        """Should fail if recording not found"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VoicemailDropService(mock_db)
        result = service.send_drop(recording_id=999, client_id=1)

        assert result["success"] is False
        assert "Recording not found" in result["error"]

    def test_send_drop_inactive_recording(self):
        """Should fail if recording is inactive"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_recording.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording

        service = VoicemailDropService(mock_db)
        result = service.send_drop(recording_id=1, client_id=1)

        assert result["success"] is False
        assert "inactive" in result["error"].lower()

    def test_send_drop_client_not_found(self):
        """Should fail if client not found"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_recording.is_active = True

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_recording, None
        ]

        service = VoicemailDropService(mock_db)
        result = service.send_drop(recording_id=1, client_id=999)

        assert result["success"] is False
        assert "Client not found" in result["error"]

    def test_send_drop_no_phone(self):
        """Should fail if no phone number"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_recording.is_active = True

        mock_client = MagicMock()
        mock_client.phone = None

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_recording, mock_client
        ]

        service = VoicemailDropService(mock_db)
        result = service.send_drop(recording_id=1, client_id=1)

        assert result["success"] is False
        assert "phone" in result["error"].lower()

    def test_send_drop_scheduled(self):
        """Should schedule drop for later"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_recording.is_active = True

        mock_client = MagicMock()
        mock_client.phone = "1234567890"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_recording, mock_client
        ]

        service = VoicemailDropService(mock_db)
        future_time = datetime.utcnow() + timedelta(hours=1)

        result = service.send_drop(
            recording_id=1,
            client_id=1,
            scheduled_at=future_time
        )

        assert result["status"] == "scheduled"
        assert "scheduled_at" in result


class TestCleanPhoneNumber:
    """Tests for _clean_phone_number method"""

    def test_clean_10_digit(self):
        """Should format 10-digit numbers"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        result = service._clean_phone_number("1234567890")

        assert result == "+11234567890"

    def test_clean_11_digit_with_1(self):
        """Should format 11-digit numbers starting with 1"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        result = service._clean_phone_number("11234567890")

        assert result == "+11234567890"

    def test_clean_with_formatting(self):
        """Should strip formatting"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        result = service._clean_phone_number("(123) 456-7890")

        assert result == "+11234567890"

    def test_clean_empty(self):
        """Should return None for empty input"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        result = service._clean_phone_number("")

        assert result is None

    def test_clean_none(self):
        """Should return None for None input"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        result = service._clean_phone_number(None)

        assert result is None

    def test_clean_short_number(self):
        """Should return None for short numbers"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        result = service._clean_phone_number("12345")

        assert result is None


class TestProviderSending:
    """Tests for provider-specific sending"""

    def test_send_mock_provider(self):
        """Should send to mock provider"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        mock_drop = MagicMock()
        mock_recording = MagicMock()

        result = service._send_mock(mock_drop, mock_recording)

        assert result["success"] is True
        assert "mock_" in result["provider_id"]

    def test_send_slybroadcast_no_credentials(self):
        """Should fail without Slybroadcast credentials"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)
        service.slybroadcast_user = None
        service.slybroadcast_pass = None

        mock_drop = MagicMock()
        mock_recording = MagicMock()

        result = service._send_slybroadcast(mock_drop, mock_recording)

        assert result["success"] is False
        assert "credentials" in result["error"].lower()

    def test_send_dropcowboy_no_api_key(self):
        """Should fail without Drop Cowboy API key"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)
        service.dropcowboy_key = None

        mock_drop = MagicMock()
        mock_recording = MagicMock()

        result = service._send_dropcowboy(mock_drop, mock_recording)

        assert result["success"] is False
        assert "API key" in result["error"]

    def test_send_twilio_no_credentials(self):
        """Should fail without Twilio credentials"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)
        service.twilio_sid = None
        service.twilio_token = None

        mock_drop = MagicMock()
        mock_recording = MagicMock()

        result = service._send_twilio(mock_drop, mock_recording)

        assert result["success"] is False
        assert "credentials" in result["error"].lower()


class TestDropHistory:
    """Tests for drop status and history methods"""

    def test_get_drop(self):
        """Should get drop by ID"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_drop = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_drop

        service = VoicemailDropService(mock_db)
        result = service.get_drop(1)

        assert result == mock_drop

    def test_get_drops(self):
        """Should get list of drops"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_drops = [MagicMock(), MagicMock()]
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_drops

        service = VoicemailDropService(mock_db)
        result = service.get_drops()

        assert result == mock_drops

    def test_get_drops_with_filters(self):
        """Should filter drops"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        service.get_drops(client_id=1, status="sent", provider="twilio")

        # Verify filters were applied
        mock_db.query.return_value.filter.assert_called()

    def test_get_client_drop_history(self):
        """Should get client's drop history"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_drop = MagicMock()
        mock_drop.to_dict.return_value = {"id": 1, "status": "sent"}
        mock_db.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_drop]

        service = VoicemailDropService(mock_db)
        result = service.get_client_drop_history(client_id=1)

        assert isinstance(result, list)

    def test_retry_drop(self):
        """Should retry a failed drop"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_drop = MagicMock()
        mock_drop.status = "failed"
        mock_drop.retry_count = 0
        mock_drop.max_retries = 3
        mock_drop.recording_id = 1

        mock_recording = MagicMock()

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_drop, mock_recording
        ]

        service = VoicemailDropService(mock_db)

        with patch.object(service, '_send_to_provider') as mock_send:
            mock_send.return_value = {"success": True}

            result = service.retry_drop(1)

        assert mock_drop.retry_count == 1

    def test_retry_drop_not_found(self):
        """Should fail for non-existent drop"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VoicemailDropService(mock_db)
        result = service.retry_drop(999)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_retry_drop_wrong_status(self):
        """Should not retry non-failed drops"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_drop = MagicMock()
        mock_drop.status = "sent"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_drop

        service = VoicemailDropService(mock_db)
        result = service.retry_drop(1)

        assert result["success"] is False
        assert "failed or cancelled" in result["error"]

    def test_retry_drop_max_retries(self):
        """Should not retry if max retries exceeded"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_drop = MagicMock()
        mock_drop.status = "failed"
        mock_drop.retry_count = 3
        mock_drop.max_retries = 3
        mock_db.query.return_value.filter.return_value.first.return_value = mock_drop

        service = VoicemailDropService(mock_db)
        result = service.retry_drop(1)

        assert result["success"] is False
        assert "retries exceeded" in result["error"]

    def test_cancel_drop(self):
        """Should cancel pending drop"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_drop = MagicMock()
        mock_drop.status = "pending"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_drop

        service = VoicemailDropService(mock_db)
        result = service.cancel_drop(1)

        assert result["success"] is True
        assert mock_drop.status == "cancelled"

    def test_cancel_drop_wrong_status(self):
        """Should not cancel sent drops"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_drop = MagicMock()
        mock_drop.status = "sent"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_drop

        service = VoicemailDropService(mock_db)
        result = service.cancel_drop(1)

        assert result["success"] is False


class TestCampaigns:
    """Tests for campaign management"""

    def test_create_campaign(self):
        """Should create a campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        campaign = service.create_campaign(
            name="Test Campaign",
            recording_id=1,
            target_type="manual",
            description="Test description"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_get_campaign(self):
        """Should get campaign by ID"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        service = VoicemailDropService(mock_db)
        result = service.get_campaign(1)

        assert result == mock_campaign

    def test_get_campaigns(self):
        """Should get list of campaigns"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaigns = [MagicMock(), MagicMock()]
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = mock_campaigns

        service = VoicemailDropService(mock_db)
        result = service.get_campaigns()

        assert result == mock_campaigns

    def test_get_campaigns_by_status(self):
        """Should filter campaigns by status"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        service = VoicemailDropService(mock_db)

        service.get_campaigns(status="in_progress")

        mock_db.query.return_value.filter.assert_called()

    def test_add_targets_to_campaign(self):
        """Should add targets to draft campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign.status = "draft"
        mock_campaign.recording_id = 1

        mock_client = MagicMock()
        mock_client.phone = "1234567890"

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_campaign, mock_client
        ]

        service = VoicemailDropService(mock_db)
        result = service.add_targets_to_campaign(1, [1])

        assert result["success"] is True
        assert result["added"] == 1

    def test_add_targets_campaign_not_found(self):
        """Should fail for non-existent campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VoicemailDropService(mock_db)
        result = service.add_targets_to_campaign(999, [1])

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_add_targets_non_draft_campaign(self):
        """Should not add targets to non-draft campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign.status = "in_progress"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        service = VoicemailDropService(mock_db)
        result = service.add_targets_to_campaign(1, [1])

        assert result["success"] is False
        assert "draft" in result["error"]

    def test_start_campaign(self):
        """Should start a draft campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign.status = "draft"
        mock_campaign.total_drops = 2
        mock_campaign.recording_id = 1

        mock_recording = MagicMock()

        mock_drop1 = MagicMock()
        mock_drop2 = MagicMock()

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_campaign, mock_recording
        ]
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_drop1, mock_drop2]

        service = VoicemailDropService(mock_db)

        with patch.object(service, '_send_to_provider') as mock_send:
            mock_send.return_value = {"success": True}

            result = service.start_campaign(1)

        assert result["success"] is True

    def test_start_campaign_not_found(self):
        """Should fail for non-existent campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VoicemailDropService(mock_db)
        result = service.start_campaign(999)

        assert result["success"] is False

    def test_start_campaign_wrong_status(self):
        """Should not start non-draft campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign.status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        service = VoicemailDropService(mock_db)
        result = service.start_campaign(1)

        assert result["success"] is False
        assert "draft" in result["error"]

    def test_start_campaign_no_targets(self):
        """Should fail if campaign has no targets"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign.status = "draft"
        mock_campaign.total_drops = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        service = VoicemailDropService(mock_db)
        result = service.start_campaign(1)

        assert result["success"] is False
        assert "no targets" in result["error"]

    def test_pause_campaign(self):
        """Should pause in-progress campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign.status = "in_progress"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        service = VoicemailDropService(mock_db)
        result = service.pause_campaign(1)

        assert result["success"] is True
        assert mock_campaign.status == "paused"

    def test_pause_campaign_wrong_status(self):
        """Should not pause non-in-progress campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign.status = "draft"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        service = VoicemailDropService(mock_db)
        result = service.pause_campaign(1)

        assert result["success"] is False

    def test_cancel_campaign(self):
        """Should cancel campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign.status = "draft"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        service = VoicemailDropService(mock_db)
        result = service.cancel_campaign(1)

        assert result["success"] is True
        assert mock_campaign.status == "cancelled"

    def test_cancel_completed_campaign_fails(self):
        """Should not cancel completed campaign"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_campaign = MagicMock()
        mock_campaign.status = "completed"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        service = VoicemailDropService(mock_db)
        result = service.cancel_campaign(1)

        assert result["success"] is False


class TestStatistics:
    """Tests for statistics methods"""

    def test_get_stats(self):
        """Should get overall statistics"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10
        mock_db.query.return_value.scalar.return_value = 100
        mock_db.query.return_value.group_by.return_value.all.return_value = [
            ("sent", 50),
            ("failed", 10),
            ("pending", 40)
        ]

        service = VoicemailDropService(mock_db)
        result = service.get_stats()

        assert "total_recordings" in result
        assert "total_drops" in result
        assert "drops_by_status" in result
        assert "total_cost_dollars" in result

    def test_get_recording_stats(self):
        """Should get stats for specific recording"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_recording = MagicMock()
        mock_recording.name = "Test Recording"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_recording
        mock_db.query.return_value.filter.return_value.scalar.return_value = 10

        service = VoicemailDropService(mock_db)
        result = service.get_recording_stats(1)

        assert "recording_id" in result
        assert "name" in result
        assert "total_uses" in result
        assert "success_rate" in result

    def test_get_recording_stats_not_found(self):
        """Should return error for non-existent recording"""
        from services.voicemail_drop_service import VoicemailDropService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = VoicemailDropService(mock_db)
        result = service.get_recording_stats(999)

        assert "error" in result


class TestFactoryFunction:
    """Tests for get_voicemail_drop_service factory"""

    def test_creates_service_with_db(self):
        """Should create service with provided db"""
        from services.voicemail_drop_service import get_voicemail_drop_service, VoicemailDropService

        mock_db = MagicMock()
        service = get_voicemail_drop_service(mock_db)

        assert isinstance(service, VoicemailDropService)
        assert service.db == mock_db

    @patch('services.voicemail_drop_service.SessionLocal')
    def test_creates_service_without_db(self, mock_session):
        """Should create service with new session if db not provided"""
        from services.voicemail_drop_service import get_voicemail_drop_service, VoicemailDropService

        mock_session.return_value = MagicMock()
        service = get_voicemail_drop_service()

        assert isinstance(service, VoicemailDropService)
        mock_session.assert_called_once()
