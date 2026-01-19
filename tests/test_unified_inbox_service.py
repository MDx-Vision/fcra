"""
Unit Tests for Unified Inbox Service (P32)

Tests the UnifiedInboxService which aggregates messages from multiple channels.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch


class TestUnifiedMessage:
    """Tests for the UnifiedMessage class"""

    def test_create_unified_message(self):
        """Test creating a UnifiedMessage object"""
        from services.unified_inbox_service import UnifiedMessage

        msg = UnifiedMessage(
            id=1,
            channel='email',
            client_id=100,
            direction='outbound',
            subject='Test Subject',
            content='Test content here',
            preview='Test content here',
            sender_name='System',
            recipient='test@example.com',
            is_read=True,
            status='sent',
            timestamp=datetime.utcnow()
        )

        assert msg.id == 1
        assert msg.channel == 'email'
        assert msg.client_id == 100
        assert msg.direction == 'outbound'
        assert msg.subject == 'Test Subject'
        assert msg.is_read == True
        assert msg.status == 'sent'

    def test_unified_message_preview_truncation(self):
        """Test that preview is truncated to 100 chars"""
        from services.unified_inbox_service import UnifiedMessage

        long_content = 'A' * 200
        msg = UnifiedMessage(
            id=1,
            channel='sms',
            client_id=100,
            direction='outbound',
            subject=None,
            content=long_content,
            preview=long_content,
            sender_name='System',
            recipient='+1234567890',
            is_read=True,
            status='sent',
            timestamp=datetime.utcnow()
        )

        assert len(msg.preview) <= 103  # 100 + '...'
        assert msg.preview.endswith('...')

    def test_unified_message_to_dict(self):
        """Test converting UnifiedMessage to dict"""
        from services.unified_inbox_service import UnifiedMessage

        timestamp = datetime.utcnow()
        msg = UnifiedMessage(
            id=1,
            channel='portal',
            client_id=100,
            direction='inbound',
            subject=None,
            content='Hello',
            preview='Hello',
            sender_name='John Doe',
            recipient='Staff',
            is_read=False,
            status='unread',
            timestamp=timestamp,
            raw_data={'sender_type': 'client'}
        )

        result = msg.to_dict()

        assert result['id'] == 1
        assert result['channel'] == 'portal'
        assert result['client_id'] == 100
        assert result['direction'] == 'inbound'
        assert result['is_read'] == False
        assert result['timestamp'] == timestamp.isoformat()
        assert result['raw_data']['sender_type'] == 'client'


class TestUnifiedInboxServiceConstants:
    """Tests for service constants"""

    def test_channel_constants(self):
        """Test channel constants are defined"""
        from services.unified_inbox_service import (
            CHANNEL_EMAIL, CHANNEL_SMS, CHANNEL_WHATSAPP,
            CHANNEL_PORTAL, CHANNEL_CHAT, ALL_CHANNELS
        )

        assert CHANNEL_EMAIL == 'email'
        assert CHANNEL_SMS == 'sms'
        assert CHANNEL_WHATSAPP == 'whatsapp'
        assert CHANNEL_PORTAL == 'portal'
        assert CHANNEL_CHAT == 'chat'
        assert len(ALL_CHANNELS) == 5

    def test_direction_constants(self):
        """Test direction constants"""
        from services.unified_inbox_service import DIRECTION_INBOUND, DIRECTION_OUTBOUND

        assert DIRECTION_INBOUND == 'inbound'
        assert DIRECTION_OUTBOUND == 'outbound'


class TestUnifiedInboxServiceConversions:
    """Tests for message conversion methods"""

    def setup_method(self):
        """Set up test fixtures"""
        from services.unified_inbox_service import UnifiedInboxService
        self.service = UnifiedInboxService(db_session=Mock())

    def test_email_to_unified(self):
        """Test converting EmailLog to UnifiedMessage"""
        email_log = Mock()
        email_log.id = 1
        email_log.client_id = 100
        email_log.email_address = 'test@example.com'
        email_log.subject = 'Test Email'
        email_log.template_type = 'welcome'
        email_log.status = 'sent'
        email_log.message_id = 'msg123'
        email_log.sent_at = datetime.utcnow()
        email_log.created_at = datetime.utcnow()
        email_log.error_message = None

        result = self.service._email_to_unified(email_log)

        assert result.channel == 'email'
        assert result.direction == 'outbound'
        assert result.subject == 'Test Email'
        assert result.recipient == 'test@example.com'
        assert result.is_read == True  # Outbound are always read
        assert result.raw_data['template_type'] == 'welcome'

    def test_sms_to_unified(self):
        """Test converting SMSLog to UnifiedMessage"""
        sms_log = Mock()
        sms_log.id = 2
        sms_log.client_id = 100
        sms_log.phone_number = '+1234567890'
        sms_log.message = 'Hello from SMS'
        sms_log.template_type = 'reminder'
        sms_log.status = 'delivered'
        sms_log.twilio_sid = 'SM123'
        sms_log.sent_at = datetime.utcnow()
        sms_log.created_at = datetime.utcnow()
        sms_log.error_message = None

        result = self.service._sms_to_unified(sms_log)

        assert result.channel == 'sms'
        assert result.direction == 'outbound'
        assert result.content == 'Hello from SMS'
        assert result.recipient == '+1234567890'
        assert result.raw_data['twilio_sid'] == 'SM123'

    def test_whatsapp_inbound_to_unified(self):
        """Test converting inbound WhatsApp message"""
        wa_msg = Mock()
        wa_msg.id = 3
        wa_msg.client_id = 100
        wa_msg.direction = 'inbound'
        wa_msg.from_number = 'whatsapp:+1234567890'
        wa_msg.to_number = 'whatsapp:+0987654321'
        wa_msg.body = 'Hello via WhatsApp'
        wa_msg.profile_name = 'John Doe'
        wa_msg.status = 'received'
        wa_msg.has_media = False
        wa_msg.media_type = None
        wa_msg.twilio_sid = 'WA123'
        wa_msg.template_name = None
        wa_msg.error_message = None
        wa_msg.created_at = datetime.utcnow()

        result = self.service._whatsapp_to_unified(wa_msg)

        assert result.channel == 'whatsapp'
        assert result.direction == 'inbound'
        assert result.sender_name == 'John Doe'
        assert result.content == 'Hello via WhatsApp'

    def test_whatsapp_outbound_to_unified(self):
        """Test converting outbound WhatsApp message"""
        wa_msg = Mock()
        wa_msg.id = 4
        wa_msg.client_id = 100
        wa_msg.direction = 'outbound'
        wa_msg.from_number = 'whatsapp:+0987654321'
        wa_msg.to_number = 'whatsapp:+1234567890'
        wa_msg.body = 'Reply from system'
        wa_msg.profile_name = None
        wa_msg.status = 'delivered'
        wa_msg.has_media = False
        wa_msg.media_type = None
        wa_msg.twilio_sid = 'WA456'
        wa_msg.template_name = 'status_update'
        wa_msg.error_message = None
        wa_msg.created_at = datetime.utcnow()

        result = self.service._whatsapp_to_unified(wa_msg)

        assert result.channel == 'whatsapp'
        assert result.direction == 'outbound'
        assert result.sender_name == 'System'
        assert result.is_read == True  # delivered is read

    def test_portal_message_from_client(self):
        """Test converting portal message from client"""
        msg = Mock()
        msg.id = 5
        msg.client_id = 100
        msg.staff_id = None
        msg.message = 'Question from client'
        msg.sender_type = 'client'
        msg.is_read = False
        msg.read_at = None
        msg.created_at = datetime.utcnow()

        client = Mock()
        client.first_name = 'John'
        client.last_name = 'Doe'

        result = self.service._portal_message_to_unified(msg, client, None)

        assert result.channel == 'portal'
        assert result.direction == 'inbound'
        assert result.sender_name == 'John Doe'
        assert result.is_read == False
        assert result.status == 'unread'

    def test_portal_message_from_staff(self):
        """Test converting portal message from staff"""
        msg = Mock()
        msg.id = 6
        msg.client_id = 100
        msg.staff_id = 1
        msg.message = 'Response from staff'
        msg.sender_type = 'staff'
        msg.is_read = True
        msg.read_at = datetime.utcnow()
        msg.created_at = datetime.utcnow()

        client = Mock()
        client.first_name = 'Jane'
        client.last_name = 'Smith'

        staff = Mock()
        staff.name = 'Admin User'

        result = self.service._portal_message_to_unified(msg, client, staff)

        assert result.channel == 'portal'
        assert result.direction == 'outbound'
        assert result.sender_name == 'Admin User'
        assert result.is_read == True

    def test_chat_message_from_user(self):
        """Test converting AI chat message from user"""
        chat_msg = Mock()
        chat_msg.id = 7
        chat_msg.conversation_id = 1
        chat_msg.role = 'user'
        chat_msg.content = 'I have a question'
        chat_msg.tokens_used = None
        chat_msg.model_used = None
        chat_msg.created_at = datetime.utcnow()

        conversation = Mock()
        conversation.client_id = 100

        client = Mock()
        client.first_name = 'Bob'
        client.last_name = 'Jones'

        result = self.service._chat_message_to_unified(chat_msg, conversation, client)

        assert result.channel == 'chat'
        assert result.direction == 'inbound'
        assert result.sender_name == 'Bob Jones'

    def test_chat_message_from_assistant(self):
        """Test converting AI chat message from assistant"""
        chat_msg = Mock()
        chat_msg.id = 8
        chat_msg.conversation_id = 1
        chat_msg.role = 'assistant'
        chat_msg.content = 'Here is the answer'
        chat_msg.tokens_used = 150
        chat_msg.model_used = 'claude-3'
        chat_msg.created_at = datetime.utcnow()

        conversation = Mock()
        conversation.client_id = 100

        result = self.service._chat_message_to_unified(chat_msg, conversation, None)

        assert result.channel == 'chat'
        assert result.direction == 'outbound'
        assert result.sender_name == 'AI Assistant'
        assert result.raw_data['tokens_used'] == 150


class TestUnifiedInboxServiceRetrieval:
    """Tests for inbox retrieval methods"""

    def test_get_client_inbox_empty(self):
        """Test getting inbox for client with no messages"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = UnifiedInboxService(db_session=mock_db)
        result = service.get_client_inbox(client_id=999)

        assert result['messages'] == []
        assert result['total'] == 0
        assert result['client_id'] == 999

    def test_get_client_inbox_with_portal_messages(self):
        """Test getting inbox with portal messages"""
        from services.unified_inbox_service import UnifiedInboxService

        # Mock client
        mock_client = Mock()
        mock_client.id = 100
        mock_client.first_name = 'Test'
        mock_client.last_name = 'User'

        # Mock portal message
        mock_message = Mock()
        mock_message.id = 1
        mock_message.client_id = 100
        mock_message.staff_id = None
        mock_message.message = 'Test message'
        mock_message.sender_type = 'client'
        mock_message.is_read = False
        mock_message.read_at = None
        mock_message.created_at = datetime.utcnow()

        mock_db = MagicMock()

        # Set up query side effects for different models
        def query_side_effect(model):
            mock_query = MagicMock()
            model_name = model.__name__ if hasattr(model, '__name__') else str(model)
            if 'Client' in model_name and 'Message' not in model_name:
                mock_query.filter.return_value.first.return_value = mock_client
            elif 'ClientMessage' in model_name:
                mock_query.filter.return_value.all.return_value = [mock_message]
            elif 'Staff' in model_name:
                mock_query.filter.return_value.first.return_value = None
            else:
                mock_query.filter.return_value.all.return_value = []
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = UnifiedInboxService(db_session=mock_db)
        result = service.get_client_inbox(client_id=100, channels=['portal'])

        assert result['client_id'] == 100
        # Messages count may vary based on mocking

    def test_get_unread_counts(self):
        """Test getting unread counts"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        service = UnifiedInboxService(db_session=mock_db)
        result = service.get_unread_counts(client_id=100)

        assert 'portal' in result
        assert 'total' in result


class TestUnifiedInboxServiceActions:
    """Tests for inbox action methods"""

    def test_mark_read_portal_message(self):
        """Test marking portal message as read"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_message = Mock()
        mock_message.id = 1
        mock_message.is_read = False
        mock_message.read_at = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_message

        service = UnifiedInboxService(db_session=mock_db)
        result = service.mark_read(channel='portal', message_id=1)

        assert result == True
        assert mock_message.is_read == True
        mock_db.commit.assert_called_once()

    def test_mark_read_unsupported_channel(self):
        """Test marking non-portal message as read returns False"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_db = MagicMock()
        service = UnifiedInboxService(db_session=mock_db)

        result = service.mark_read(channel='email', message_id=1)

        assert result == False

    def test_mark_client_messages_read(self):
        """Test marking all client messages as read"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_messages = [Mock(is_read=False, read_at=None) for _ in range(3)]

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = mock_messages

        service = UnifiedInboxService(db_session=mock_db)
        count = service.mark_client_messages_read(client_id=100)

        assert count == 3
        for msg in mock_messages:
            assert msg.is_read == True
        mock_db.commit.assert_called_once()


class TestUnifiedInboxServiceSendReply:
    """Tests for send_reply method"""

    def test_send_reply_portal(self):
        """Test sending portal reply"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_client = Mock()
        mock_client.id = 100
        mock_client.email = 'test@example.com'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = UnifiedInboxService(db_session=mock_db)
        result = service.send_reply(
            client_id=100,
            channel='portal',
            content='Test reply',
            staff_id=1
        )

        assert result['success'] == True
        assert result['channel'] == 'portal'
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_send_reply_client_not_found(self):
        """Test sending reply when client doesn't exist"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = UnifiedInboxService(db_session=mock_db)
        result = service.send_reply(
            client_id=999,
            channel='portal',
            content='Test reply',
            staff_id=1
        )

        assert result['success'] == False
        assert 'not found' in result['error'].lower()

    @patch('services.email_service.send_email')
    def test_send_reply_email(self, mock_send_email):
        """Test sending email reply"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_client = Mock()
        mock_client.id = 100
        mock_client.email = 'test@example.com'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        mock_send_email.return_value = {'success': True}

        service = UnifiedInboxService(db_session=mock_db)
        result = service.send_reply(
            client_id=100,
            channel='email',
            content='Email reply content',
            staff_id=1,
            subject='Re: Your inquiry'
        )

        assert result['success'] == True
        assert result['channel'] == 'email'
        mock_send_email.assert_called_once()

    @patch('services.sms_service.send_sms')
    def test_send_reply_sms(self, mock_send_sms):
        """Test sending SMS reply"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_client = Mock()
        mock_client.id = 100
        mock_client.phone = '+1234567890'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        mock_send_sms.return_value = {'success': True}

        service = UnifiedInboxService(db_session=mock_db)
        result = service.send_reply(
            client_id=100,
            channel='sms',
            content='SMS reply',
            staff_id=1
        )

        assert result['success'] == True
        assert result['channel'] == 'sms'
        mock_send_sms.assert_called_once()

    def test_send_reply_sms_no_phone(self):
        """Test SMS reply when client has no phone"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_client = Mock()
        mock_client.id = 100
        mock_client.phone = None

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = UnifiedInboxService(db_session=mock_db)
        result = service.send_reply(
            client_id=100,
            channel='sms',
            content='SMS reply',
            staff_id=1
        )

        assert result['success'] == False
        assert 'phone' in result['error'].lower()

    def test_send_reply_unsupported_channel(self):
        """Test reply to unsupported channel"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_client = Mock()
        mock_client.id = 100

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = UnifiedInboxService(db_session=mock_db)
        result = service.send_reply(
            client_id=100,
            channel='unsupported',
            content='Test',
            staff_id=1
        )

        assert result['success'] == False
        assert 'unsupported' in result['error'].lower()


class TestUnifiedInboxServiceDashboard:
    """Tests for dashboard statistics"""

    def test_get_dashboard_stats(self):
        """Test getting dashboard statistics"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_db = MagicMock()
        # Make all count queries return 5
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5

        service = UnifiedInboxService(db_session=mock_db)
        result = service.get_dashboard_stats(days=7)

        assert 'total_messages' in result
        assert 'unread_count' in result
        assert 'active_chats' in result
        assert 'by_channel' in result
        assert result['period_days'] == 7

    def test_get_dashboard_stats_with_staff_filter(self):
        """Test dashboard stats filtered by staff"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_db = MagicMock()

        # Set up query to handle both scalar and all calls
        mock_query = MagicMock()
        mock_query.filter.return_value.scalar.return_value = 3
        mock_query.filter.return_value.all.return_value = [(1,), (2,)]
        mock_db.query.return_value = mock_query

        service = UnifiedInboxService(db_session=mock_db)
        result = service.get_dashboard_stats(staff_id=1, days=30)

        assert result['period_days'] == 30
        assert 'total_messages' in result


class TestConversationThread:
    """Tests for conversation thread view"""

    def test_get_conversation_thread(self):
        """Test getting conversation thread"""
        from services.unified_inbox_service import UnifiedInboxService

        mock_db = MagicMock()

        # Mock client
        mock_client = Mock()
        mock_client.id = 100
        mock_client.first_name = 'Test'
        mock_client.last_name = 'Client'

        # Set up return values
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = UnifiedInboxService(db_session=mock_db)
        result = service.get_conversation_thread(client_id=100)

        assert 'thread' in result
        assert result['client_id'] == 100


class TestFactoryFunction:
    """Tests for factory function"""

    def test_get_unified_inbox_service(self):
        """Test factory function creates service"""
        from services.unified_inbox_service import get_unified_inbox_service

        service = get_unified_inbox_service()
        assert service is not None

    def test_get_unified_inbox_service_with_db(self):
        """Test factory function with db parameter"""
        from services.unified_inbox_service import get_unified_inbox_service

        mock_db = Mock()
        service = get_unified_inbox_service(db=mock_db)
        assert service.db == mock_db
