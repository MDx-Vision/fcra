"""
Unit tests for Bulk Campaign Service - Email/SMS blasts to multiple clients

Tests cover:
- Campaign creation and validation
- Recipient management
- Campaign sending
- Scheduling and cancellation
- Statistics and processing
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


class TestCreateCampaign:
    """Tests for create_campaign function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_creates_email_campaign(self, mock_get_db):
        """Should create email campaign with content"""
        from services.bulk_campaign_service import create_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.to_dict.return_value = {'id': 1, 'name': 'Test'}
        mock_db.add = Mock()
        mock_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        result = create_campaign(
            name='Test Campaign',
            channel='email',
            created_by_staff_id=1,
            email_content='Hello {{first_name}}',
            email_subject='Test Subject'
        )

        assert result['success'] is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    @patch('services.bulk_campaign_service.get_db')
    def test_creates_sms_campaign(self, mock_get_db):
        """Should create SMS campaign with content"""
        from services.bulk_campaign_service import create_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        result = create_campaign(
            name='SMS Campaign',
            channel='sms',
            created_by_staff_id=1,
            sms_content='Hi {{first_name}}'
        )

        assert result['success'] is True
        mock_db.commit.assert_called()

    def test_fails_invalid_channel(self):
        """Should fail with invalid channel"""
        from services.bulk_campaign_service import create_campaign

        result = create_campaign(
            name='Test',
            channel='invalid',
            created_by_staff_id=1
        )

        assert result['success'] is False
        assert 'Invalid channel' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_fails_email_without_content(self, mock_get_db):
        """Should fail if email campaign has no content"""
        from services.bulk_campaign_service import create_campaign

        result = create_campaign(
            name='Test',
            channel='email',
            created_by_staff_id=1
        )

        assert result['success'] is False
        assert 'Email content' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_fails_sms_without_content(self, mock_get_db):
        """Should fail if SMS campaign has no content"""
        from services.bulk_campaign_service import create_campaign

        result = create_campaign(
            name='Test',
            channel='sms',
            created_by_staff_id=1
        )

        assert result['success'] is False
        assert 'SMS content' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_handles_exception(self, mock_get_db):
        """Should handle database exceptions"""
        from services.bulk_campaign_service import create_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.add.side_effect = Exception('DB Error')

        result = create_campaign(
            name='Test',
            channel='email',
            created_by_staff_id=1,
            email_content='Test'
        )

        assert result['success'] is False
        mock_db.rollback.assert_called_once()


class TestGetCampaign:
    """Tests for get_campaign function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_returns_campaign(self, mock_get_db):
        """Should return campaign dict when found"""
        from services.bulk_campaign_service import get_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.to_dict.return_value = {'id': 1, 'name': 'Test'}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = get_campaign(campaign_id=1)

        assert result is not None
        assert result['id'] == 1

    @patch('services.bulk_campaign_service.get_db')
    def test_returns_none_not_found(self, mock_get_db):
        """Should return None when not found"""
        from services.bulk_campaign_service import get_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_campaign(campaign_id=999)

        assert result is None


class TestListCampaigns:
    """Tests for list_campaigns function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_returns_paginated_list(self, mock_get_db):
        """Should return paginated campaigns"""
        from services.bulk_campaign_service import list_campaigns

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_query = mock_db.query.return_value
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = list_campaigns()

        assert 'campaigns' in result
        assert 'total' in result
        assert 'limit' in result
        assert 'offset' in result

    @patch('services.bulk_campaign_service.get_db')
    def test_filters_by_status(self, mock_get_db):
        """Should filter by status"""
        from services.bulk_campaign_service import list_campaigns

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_query = mock_db.query.return_value
        mock_filtered = mock_query.filter.return_value
        mock_filtered.count.return_value = 0
        mock_filtered.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        list_campaigns(status='draft')

        mock_query.filter.assert_called()


class TestAddRecipients:
    """Tests for add_recipients function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_campaign_not_found(self, mock_get_db):
        """Should fail if campaign not found"""
        from services.bulk_campaign_service import add_recipients

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = add_recipients(campaign_id=999, client_ids=[1, 2])

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_fails_campaign_in_progress(self, mock_get_db):
        """Should fail if campaign is in progress"""
        from services.bulk_campaign_service import add_recipients

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'sending'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = add_recipients(campaign_id=1, client_ids=[1])

        assert result['success'] is False
        assert 'in progress' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_adds_recipients(self, mock_get_db):
        """Should add recipients successfully"""
        from services.bulk_campaign_service import add_recipients

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'draft'
        mock_campaign.channel = 'email'

        # First call returns campaign, subsequent calls return None (no existing recipient)
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_campaign,  # Campaign lookup
            None,  # No existing recipient
        ]
        mock_db.query.return_value.filter.return_value.count.return_value = 1

        result = add_recipients(campaign_id=1, client_ids=[1])

        assert result['success'] is True
        assert result['added'] >= 0


class TestRemoveRecipient:
    """Tests for remove_recipient function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_recipient_not_found(self, mock_get_db):
        """Should fail if recipient not found"""
        from services.bulk_campaign_service import remove_recipient

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = remove_recipient(campaign_id=1, client_id=999)

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_removes_recipient(self, mock_get_db):
        """Should remove recipient successfully"""
        from services.bulk_campaign_service import remove_recipient

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_recipient = Mock()
        mock_campaign = Mock()

        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_recipient,
            mock_campaign,
        ]
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = remove_recipient(campaign_id=1, client_id=1)

        assert result['success'] is True
        mock_db.delete.assert_called_once_with(mock_recipient)


class TestGetRecipients:
    """Tests for get_recipients function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_returns_paginated_recipients(self, mock_get_db):
        """Should return paginated recipients with client info"""
        from services.bulk_campaign_service import get_recipients

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_query = mock_db.query.return_value.filter.return_value
        mock_query.count.return_value = 0
        mock_query.offset.return_value.limit.return_value.all.return_value = []

        result = get_recipients(campaign_id=1)

        assert 'recipients' in result
        assert 'total' in result
        assert 'limit' in result
        assert 'offset' in result


class TestSendCampaign:
    """Tests for send_campaign function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_campaign_not_found(self, mock_get_db):
        """Should fail if campaign not found"""
        from services.bulk_campaign_service import send_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = send_campaign(campaign_id=999)

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_fails_wrong_status(self, mock_get_db):
        """Should fail if campaign not draft/scheduled"""
        from services.bulk_campaign_service import send_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'completed'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = send_campaign(campaign_id=1)

        assert result['success'] is False
        assert 'Cannot send' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_fails_no_recipients(self, mock_get_db):
        """Should fail if no recipients"""
        from services.bulk_campaign_service import send_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'draft'
        mock_campaign.total_recipients = 0
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = send_campaign(campaign_id=1)

        assert result['success'] is False
        assert 'No recipients' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_sends_email_campaign(self, mock_get_db):
        """Should successfully complete email campaign send"""
        from services.bulk_campaign_service import send_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'draft'
        mock_campaign.total_recipients = 1
        mock_campaign.channel = 'email'
        mock_campaign.email_template_id = None
        mock_campaign.sms_template_id = None
        mock_campaign.email_subject = 'Test'
        mock_campaign.email_content = 'Hello'
        mock_campaign.sms_content = None

        # Empty recipients list for simpler test - just verify campaign status changes
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = send_campaign(campaign_id=1)

        # Verifies campaign completes (even with 0 actual sends)
        assert result['success'] is True
        assert mock_campaign.status == 'completed'
        mock_db.commit.assert_called()


class TestScheduleCampaign:
    """Tests for schedule_campaign function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_campaign_not_found(self, mock_get_db):
        """Should fail if campaign not found"""
        from services.bulk_campaign_service import schedule_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = schedule_campaign(campaign_id=999, scheduled_at=datetime.utcnow())

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_fails_non_draft(self, mock_get_db):
        """Should fail if not a draft campaign"""
        from services.bulk_campaign_service import schedule_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'sending'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = schedule_campaign(campaign_id=1, scheduled_at=datetime.utcnow())

        assert result['success'] is False
        assert 'draft' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_schedules_successfully(self, mock_get_db):
        """Should schedule campaign"""
        from services.bulk_campaign_service import schedule_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'draft'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        result = schedule_campaign(campaign_id=1, scheduled_at=scheduled_time)

        assert result['success'] is True
        assert 'scheduled_at' in result


class TestCancelCampaign:
    """Tests for cancel_campaign function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_campaign_not_found(self, mock_get_db):
        """Should fail if campaign not found"""
        from services.bulk_campaign_service import cancel_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = cancel_campaign(campaign_id=999)

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_fails_in_progress(self, mock_get_db):
        """Should fail if campaign is in progress"""
        from services.bulk_campaign_service import cancel_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'sending'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = cancel_campaign(campaign_id=1)

        assert result['success'] is False
        assert 'Cannot cancel' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_cancels_successfully(self, mock_get_db):
        """Should cancel campaign"""
        from services.bulk_campaign_service import cancel_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'scheduled'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = cancel_campaign(campaign_id=1)

        assert result['success'] is True
        assert mock_campaign.status == 'cancelled'


class TestDeleteCampaign:
    """Tests for delete_campaign function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_campaign_not_found(self, mock_get_db):
        """Should fail if campaign not found"""
        from services.bulk_campaign_service import delete_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = delete_campaign(campaign_id=999)

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_fails_while_sending(self, mock_get_db):
        """Should fail if campaign is sending"""
        from services.bulk_campaign_service import delete_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'sending'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = delete_campaign(campaign_id=1)

        assert result['success'] is False
        assert 'Cannot delete' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_deletes_successfully(self, mock_get_db):
        """Should delete campaign and recipients"""
        from services.bulk_campaign_service import delete_campaign

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.status = 'draft'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        result = delete_campaign(campaign_id=1)

        assert result['success'] is True
        mock_db.delete.assert_called_once_with(mock_campaign)


class TestGetCampaignStats:
    """Tests for get_campaign_stats function"""

    @patch('services.bulk_campaign_service.get_db')
    def test_campaign_not_found(self, mock_get_db):
        """Should fail if campaign not found"""
        from services.bulk_campaign_service import get_campaign_stats

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_campaign_stats(campaign_id=999)

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.bulk_campaign_service.get_db')
    def test_returns_stats(self, mock_get_db):
        """Should return campaign statistics"""
        from services.bulk_campaign_service import get_campaign_stats

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.channel = 'email'
        mock_campaign.to_dict.return_value = {'id': 1}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_campaign_stats(campaign_id=1)

        assert 'campaign' in result
        assert 'email_stats' in result


class TestProcessScheduledCampaigns:
    """Tests for process_scheduled_campaigns function"""

    @patch('services.bulk_campaign_service.send_campaign')
    @patch('services.bulk_campaign_service.get_db')
    def test_processes_due_campaigns(self, mock_get_db, mock_send):
        """Should process all due scheduled campaigns"""
        from services.bulk_campaign_service import process_scheduled_campaigns

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.id = 1
        mock_campaign.name = 'Test Campaign'
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_campaign]
        mock_send.return_value = {'success': True, 'sent': 5, 'failed': 0}

        result = process_scheduled_campaigns()

        assert 'processed' in result
        assert result['processed'] == 1
        mock_send.assert_called_once_with(1)

    @patch('services.bulk_campaign_service.get_db')
    def test_returns_empty_when_none_due(self, mock_get_db):
        """Should return empty when no campaigns due"""
        from services.bulk_campaign_service import process_scheduled_campaigns

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = process_scheduled_campaigns()

        assert result['processed'] == 0
        assert result['results'] == []


class TestAddRecipientsByFilter:
    """Tests for add_recipients_by_filter function"""

    @patch('services.bulk_campaign_service.add_recipients')
    @patch('services.bulk_campaign_service.get_db')
    def test_campaign_not_found(self, mock_get_db, mock_add):
        """Should fail if campaign not found"""
        from services.bulk_campaign_service import add_recipients_by_filter

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = add_recipients_by_filter(campaign_id=999, filters={})

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.bulk_campaign_service.add_recipients')
    @patch('services.bulk_campaign_service.get_db')
    def test_filters_by_status(self, mock_get_db, mock_add):
        """Should filter clients by status"""
        from services.bulk_campaign_service import add_recipients_by_filter

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_campaign = Mock()
        mock_campaign.channel = 'email'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_campaign

        # Setup client query chain
        mock_client_query = mock_db.query.return_value
        mock_client_query.filter.return_value.all.return_value = []
        mock_add.return_value = {'success': True, 'added': 0}

        result = add_recipients_by_filter(
            campaign_id=1,
            filters={'status': 'active'}
        )

        # Should call add_recipients with filtered client IDs
        mock_add.assert_called()
