"""
Unit tests for ChatService

Tests AI-powered chat support including:
- Conversation lifecycle (start, send, close)
- Message handling
- Escalation detection and workflow
- Rate limiting
- Client context
- Knowledge base
"""

import pytest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session


# =============================================================================
# KNOWLEDGE BASE TESTS
# =============================================================================

class TestKnowledgeBase:
    """Tests for chat knowledge base."""

    def test_company_info_exists(self):
        """Test company info is defined."""
        from services.chat_knowledge_base import COMPANY_INFO
        assert 'Brightpath Ascend Group' in COMPANY_INFO
        assert 'credit restoration' in COMPANY_INFO.lower()

    def test_fcra_basics_exists(self):
        """Test FCRA basics content exists."""
        from services.chat_knowledge_base import FCRA_BASICS
        assert 'FCRA' in FCRA_BASICS
        assert 'Equifax' in FCRA_BASICS
        assert 'Experian' in FCRA_BASICS
        assert 'TransUnion' in FCRA_BASICS

    def test_dispute_process_exists(self):
        """Test dispute process content exists."""
        from services.chat_knowledge_base import DISPUTE_PROCESS
        assert 'ROUND 1' in DISPUTE_PROCESS or 'Round 1' in DISPUTE_PROCESS
        assert 'ROUND 2' in DISPUTE_PROCESS or 'Round 2' in DISPUTE_PROCESS
        assert '30 days' in DISPUTE_PROCESS or '30-45' in DISPUTE_PROCESS

    def test_faq_content_exists(self):
        """Test FAQ content exists."""
        from services.chat_knowledge_base import FAQ_CONTENT
        assert 'Q:' in FAQ_CONTENT
        assert 'A:' in FAQ_CONTENT

    def test_get_full_knowledge_base(self):
        """Test full knowledge base retrieval."""
        from services.chat_knowledge_base import get_full_knowledge_base
        kb = get_full_knowledge_base()
        assert isinstance(kb, str)
        assert len(kb) > 1000  # Should be substantial content
        assert 'Brightpath' in kb
        assert 'FCRA' in kb

    def test_get_system_prompt_basic(self):
        """Test system prompt generation without context."""
        from services.chat_knowledge_base import get_system_prompt
        prompt = get_system_prompt()
        assert 'helpful support assistant' in prompt
        assert 'Brightpath Ascend Group' in prompt
        assert 'GUIDELINES' in prompt

    def test_get_system_prompt_with_context(self):
        """Test system prompt with client context."""
        from services.chat_knowledge_base import get_system_prompt
        context = {
            'client_name': 'John Smith',
            'case_status': 'round_1',
            'client_stage': 'active',
            'dispute_round': 1,
            'days_active': 30,
            'violations_count': 15
        }
        prompt = get_system_prompt(context)
        assert 'John Smith' in prompt
        assert 'CLIENT CONTEXT' in prompt
        assert 'Round 1' in prompt


# =============================================================================
# ESCALATION DETECTION TESTS
# =============================================================================

class TestEscalationDetection:
    """Tests for escalation trigger detection."""

    def test_payment_triggers_escalation(self):
        """Test payment keywords trigger escalation."""
        from services.chat_knowledge_base import check_escalation_needed

        result = check_escalation_needed("I want a refund")
        assert result['should_escalate'] is True
        assert result['reason'] == 'payment_billing'

        result = check_escalation_needed("Cancel my account")
        assert result['should_escalate'] is True

    def test_frustration_triggers_escalation(self):
        """Test frustration keywords trigger escalation."""
        from services.chat_knowledge_base import check_escalation_needed

        result = check_escalation_needed("I'm so frustrated with this")
        assert result['should_escalate'] is True
        assert result['reason'] == 'dissatisfaction'

        result = check_escalation_needed("This is a waste of time")
        assert result['should_escalate'] is True

    def test_legal_triggers_escalation(self):
        """Test legal keywords trigger escalation."""
        from services.chat_knowledge_base import check_escalation_needed

        result = check_escalation_needed("I want to speak to a lawyer")
        assert result['should_escalate'] is True
        assert result['reason'] == 'legal'

        result = check_escalation_needed("I'm going to sue")
        assert result['should_escalate'] is True

    def test_human_request_triggers_escalation(self):
        """Test explicit human requests trigger escalation."""
        from services.chat_knowledge_base import check_escalation_needed

        result = check_escalation_needed("I want to speak to a human")
        assert result['should_escalate'] is True
        assert result['reason'] == 'explicit_request'

        result = check_escalation_needed("Talk to a real person please")
        assert result['should_escalate'] is True

    def test_normal_message_no_escalation(self):
        """Test normal messages don't trigger escalation."""
        from services.chat_knowledge_base import check_escalation_needed

        result = check_escalation_needed("What is my case status?")
        assert result['should_escalate'] is False

        result = check_escalation_needed("How long does the process take?")
        assert result['should_escalate'] is False

        result = check_escalation_needed("Thank you for your help")
        assert result['should_escalate'] is False


# =============================================================================
# CHAT SERVICE INITIALIZATION TESTS
# =============================================================================

class TestChatServiceInit:
    """Tests for ChatService initialization."""

    def test_service_init(self):
        """Test service initializes correctly."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        service = ChatService(mock_db)

        assert service.db == mock_db
        assert service._anthropic_client is None

    def test_rate_limit_defaults(self):
        """Test rate limit defaults are set."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        service = ChatService(mock_db)

        assert service.MAX_MESSAGES_PER_MINUTE > 0
        assert service.MAX_CONVERSATIONS_PER_DAY > 0
        assert service.MAX_TOKENS_PER_CONVERSATION > 0

    def test_ai_model_config(self):
        """Test AI model configuration."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        service = ChatService(mock_db)

        assert 'claude' in service.AI_MODEL.lower()
        assert service.MAX_RESPONSE_TOKENS > 0
        assert 0 <= service.TEMPERATURE <= 1


# =============================================================================
# CONVERSATION LIFECYCLE TESTS
# =============================================================================

class TestConversationLifecycle:
    """Tests for conversation start, close operations."""

    def test_start_conversation_client_not_found(self):
        """Test starting conversation with invalid client."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ChatService(mock_db)
        result = service.start_conversation(client_id=999)

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_start_conversation_rate_limited(self):
        """Test starting conversation when rate limited."""
        from services.chat_service import ChatService
        from database import Client

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock(spec=Client)
        mock_client.id = 1
        mock_client.first_name = "Test"
        mock_client.last_name = "User"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.scalar.return_value = 100  # Many conversations

        service = ChatService(mock_db)
        result = service.start_conversation(client_id=1)

        assert result['success'] is False
        assert 'limit' in result['error'].lower()

    def test_start_conversation_success(self):
        """Test successful conversation start."""
        from services.chat_service import ChatService
        from database import Client, ChatConversation

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock(spec=Client)
        mock_client.id = 1
        mock_client.first_name = "Test"
        mock_client.last_name = "User"
        mock_client.email = "test@example.com"
        mock_client.created_at = datetime.utcnow() - timedelta(days=30)
        mock_client.dispute_status = 'round_1'
        mock_client.client_stage = 'active'
        mock_client.current_round = 1

        # Mock query returns
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value.first.return_value = mock_client
        mock_query.filter.return_value.scalar.return_value = 0  # No rate limit

        # Make conversation be assigned an ID after add
        def mock_add(obj):
            if hasattr(obj, 'id') and obj.id is None:
                obj.id = 1

        mock_db.add.side_effect = mock_add

        service = ChatService(mock_db)
        result = service.start_conversation(client_id=1)

        assert result['success'] is True
        assert 'conversation_id' in result
        assert 'welcome_message' in result

    def test_close_conversation_not_found(self):
        """Test closing non-existent conversation."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ChatService(mock_db)
        result = service.close_conversation(conversation_id=999)

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_close_conversation_unauthorized(self):
        """Test closing conversation by wrong client."""
        from services.chat_service import ChatService
        from database import ChatConversation

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.client_id = 1
        mock_conv.status = 'active'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv

        service = ChatService(mock_db)
        result = service.close_conversation(conversation_id=1, client_id=999)

        assert result['success'] is False
        assert 'unauthorized' in result['error'].lower()

    def test_close_conversation_success(self):
        """Test successful conversation close."""
        from services.chat_service import ChatService
        from database import ChatConversation

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.client_id = 1
        mock_conv.status = 'active'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv

        service = ChatService(mock_db)
        result = service.close_conversation(conversation_id=1, client_id=1)

        assert result['success'] is True
        assert mock_conv.status == 'closed'
        assert mock_conv.ended_at is not None


# =============================================================================
# MESSAGE HANDLING TESTS
# =============================================================================

class TestMessageHandling:
    """Tests for message sending and receiving."""

    def test_send_message_conversation_not_found(self):
        """Test sending message to non-existent conversation."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ChatService(mock_db)
        result = service.send_message(conversation_id=999, message="Hello")

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_send_message_conversation_closed(self):
        """Test sending message to closed conversation."""
        from services.chat_service import ChatService
        from database import ChatConversation

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.status = 'closed'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv

        service = ChatService(mock_db)
        result = service.send_message(conversation_id=1, message="Hello")

        assert result['success'] is False
        assert 'closed' in result['error'].lower()

    def test_send_message_unauthorized(self):
        """Test sending message by wrong client."""
        from services.chat_service import ChatService
        from database import ChatConversation

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.client_id = 1
        mock_conv.status = 'active'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv

        service = ChatService(mock_db)
        result = service.send_message(conversation_id=1, message="Hello", client_id=999)

        assert result['success'] is False
        assert 'unauthorized' in result['error'].lower()

    def test_send_message_triggers_escalation(self):
        """Test message triggering escalation suggestion."""
        from services.chat_service import ChatService
        from database import ChatConversation

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.client_id = 1
        mock_conv.status = 'active'
        mock_conv.total_tokens = 0
        mock_conv.total_messages = 0

        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        service = ChatService(mock_db)
        result = service.send_message(conversation_id=1, message="I want a refund")

        assert result['success'] is True
        assert result.get('escalation_suggested') is True
        assert 'payment_billing' in result.get('escalation_reason', '')


# =============================================================================
# ESCALATION WORKFLOW TESTS
# =============================================================================

class TestEscalationWorkflow:
    """Tests for escalation to staff."""

    def test_escalate_conversation_not_found(self):
        """Test escalating non-existent conversation."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ChatService(mock_db)
        result = service.escalate_to_staff(conversation_id=999)

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_escalate_already_escalated(self):
        """Test escalating already escalated conversation."""
        from services.chat_service import ChatService
        from database import ChatConversation

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.status = 'escalated'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_conv

        service = ChatService(mock_db)
        result = service.escalate_to_staff(conversation_id=1)

        assert result['success'] is False
        assert 'already escalated' in result['error'].lower()

    def test_escalate_success(self):
        """Test successful escalation."""
        from services.chat_service import ChatService
        from database import ChatConversation, Staff

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.client_id = 1
        mock_conv.status = 'active'
        mock_conv.total_messages = 5

        mock_staff = MagicMock(spec=Staff)
        mock_staff.id = 1
        mock_staff.name = "Test Staff"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ChatConversation:
                mock_query.filter.return_value.first.return_value = mock_conv
            elif model == Staff:
                mock_query.filter.return_value.first.return_value = mock_staff
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = ChatService(mock_db)
        result = service.escalate_to_staff(
            conversation_id=1,
            staff_id=1,
            reason="Payment issue"
        )

        assert result['success'] is True
        assert mock_conv.status == 'escalated'
        assert mock_conv.escalation_reason == "Payment issue"

    def test_get_escalated_conversations(self):
        """Test getting escalated conversations for staff."""
        from services.chat_service import ChatService
        from database import ChatConversation, Client, ChatMessage

        mock_db = MagicMock(spec=Session)

        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.client_id = 1
        mock_conv.status = 'escalated'
        mock_conv.escalated_at = datetime.utcnow() - timedelta(hours=1)
        mock_conv.escalation_reason = "Client request"
        mock_conv.escalated_to_staff_id = None

        mock_client = MagicMock(spec=Client)
        mock_client.id = 1
        mock_client.first_name = "Test"
        mock_client.last_name = "User"
        mock_client.email = "test@example.com"

        mock_msg = MagicMock(spec=ChatMessage)
        mock_msg.content = "I need help"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ChatConversation:
                mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_conv]
            elif model == Client:
                mock_query.filter.return_value.first.return_value = mock_client
            elif model == ChatMessage:
                mock_query.filter.return_value.order_by.return_value.first.return_value = mock_msg
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = ChatService(mock_db)
        result = service.get_escalated_conversations()

        assert result['success'] is True
        assert len(result['conversations']) == 1
        assert result['conversations'][0]['client_name'] == "Test User"


# =============================================================================
# CLIENT CONTEXT TESTS
# =============================================================================

class TestClientContext:
    """Tests for client context gathering."""

    def test_get_context_client_not_found(self):
        """Test getting context for non-existent client."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ChatService(mock_db)
        result = service.get_client_context(client_id=999)

        assert result == {}

    def test_get_context_success(self):
        """Test successful context retrieval."""
        from services.chat_service import ChatService
        from database import Client

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock(spec=Client)
        mock_client.id = 1
        mock_client.first_name = "John"
        mock_client.last_name = "Doe"
        mock_client.created_at = datetime.utcnow() - timedelta(days=45)
        mock_client.dispute_status = 'round_2'
        mock_client.client_stage = 'active'
        mock_client.current_round = 2

        def query_side_effect(model_or_func):
            mock_query = MagicMock()
            if hasattr(model_or_func, '__name__') and model_or_func.__name__ == 'Client':
                mock_query.filter.return_value.first.return_value = mock_client
            else:
                mock_query.filter.return_value.scalar.return_value = 10  # violations/items
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = ChatService(mock_db)
        result = service.get_client_context(client_id=1)

        assert result['client_name'] == 'John Doe'
        assert result['case_status'] == 'round_2'
        assert result['dispute_round'] == 2
        assert result['days_active'] >= 45


# =============================================================================
# GET CONVERSATION TESTS
# =============================================================================

class TestGetConversation:
    """Tests for retrieving conversation details."""

    def test_get_conversation_not_found(self):
        """Test getting non-existent conversation."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ChatService(mock_db)
        result = service.get_conversation(conversation_id=999)

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_conversation_success(self):
        """Test successful conversation retrieval."""
        from services.chat_service import ChatService
        from database import ChatConversation, ChatMessage

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.client_id = 1
        mock_conv.status = 'active'
        mock_conv.started_at = datetime.utcnow()
        mock_conv.ended_at = None
        mock_conv.total_messages = 5

        mock_msg = MagicMock(spec=ChatMessage)
        mock_msg.id = 1
        mock_msg.role = 'user'
        mock_msg.content = 'Hello'
        mock_msg.created_at = datetime.utcnow()
        mock_msg.staff_id = None

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ChatConversation:
                mock_query.filter.return_value.first.return_value = mock_conv
            elif model == ChatMessage:
                mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_msg]
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = ChatService(mock_db)
        result = service.get_conversation(conversation_id=1)

        assert result['success'] is True
        assert result['conversation']['id'] == 1
        assert len(result['messages']) == 1


# =============================================================================
# CLIENT CONVERSATIONS LIST TESTS
# =============================================================================

class TestClientConversations:
    """Tests for listing client conversations."""

    def test_get_client_conversations_empty(self):
        """Test getting conversations when none exist."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []

        service = ChatService(mock_db)
        result = service.get_client_conversations(client_id=1)

        assert result['success'] is True
        assert result['conversations'] == []

    def test_get_client_conversations_success(self):
        """Test successful retrieval of client conversations."""
        from services.chat_service import ChatService
        from database import ChatConversation

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.status = 'active'
        mock_conv.started_at = datetime.utcnow()
        mock_conv.ended_at = None
        mock_conv.total_messages = 10
        mock_conv.updated_at = datetime.utcnow()

        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_conv]

        service = ChatService(mock_db)
        result = service.get_client_conversations(client_id=1)

        assert result['success'] is True
        assert len(result['conversations']) == 1


# =============================================================================
# STAFF RESPONSE TESTS
# =============================================================================

class TestStaffResponse:
    """Tests for staff responding to escalated chats."""

    def test_staff_respond_conversation_not_found(self):
        """Test staff responding to non-existent conversation."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = ChatService(mock_db)
        result = service.staff_respond(conversation_id=999, staff_id=1, message="Hello")

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_staff_respond_staff_not_found(self):
        """Test staff responding when staff doesn't exist."""
        from services.chat_service import ChatService
        from database import ChatConversation, Staff

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.status = 'escalated'

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ChatConversation:
                mock_query.filter.return_value.first.return_value = mock_conv
            elif model == Staff:
                mock_query.filter.return_value.first.return_value = None
            return mock_query

        mock_db.query.side_effect = query_side_effect

        service = ChatService(mock_db)
        result = service.staff_respond(conversation_id=1, staff_id=999, message="Hello")

        assert result['success'] is False
        assert 'staff' in result['error'].lower()

    def test_staff_respond_success(self):
        """Test successful staff response."""
        from services.chat_service import ChatService
        from database import ChatConversation, Staff

        mock_db = MagicMock(spec=Session)
        mock_conv = MagicMock(spec=ChatConversation)
        mock_conv.id = 1
        mock_conv.status = 'escalated'
        mock_conv.total_messages = 5
        mock_conv.escalated_to_staff_id = None

        mock_staff = MagicMock(spec=Staff)
        mock_staff.id = 1
        mock_staff.name = "Test Staff"

        def query_side_effect(model):
            mock_query = MagicMock()
            if model == ChatConversation:
                mock_query.filter.return_value.first.return_value = mock_conv
            elif model == Staff:
                mock_query.filter.return_value.first.return_value = mock_staff
            return mock_query

        mock_db.query.side_effect = query_side_effect

        # Mock message id assignment
        def mock_add(obj):
            if hasattr(obj, 'id') and obj.id is None:
                obj.id = 100
            if hasattr(obj, 'created_at') and obj.created_at is None:
                obj.created_at = datetime.utcnow()

        mock_db.add.side_effect = mock_add

        service = ChatService(mock_db)
        result = service.staff_respond(
            conversation_id=1,
            staff_id=1,
            message="How can I help you?"
        )

        assert result['success'] is True
        assert 'message_id' in result


# =============================================================================
# RATE LIMITING TESTS
# =============================================================================

class TestRateLimiting:
    """Tests for rate limiting functionality."""

    def test_message_rate_limit_not_exceeded(self):
        """Test message rate limit when not exceeded."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 2

        service = ChatService(mock_db)
        result = service._check_message_rate_limit(conversation_id=1)

        assert result['allowed'] is True

    def test_message_rate_limit_exceeded(self):
        """Test message rate limit when exceeded."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 100

        service = ChatService(mock_db)
        result = service._check_message_rate_limit(conversation_id=1)

        assert result['allowed'] is False

    def test_conversation_rate_limit_not_exceeded(self):
        """Test conversation rate limit when not exceeded."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 1

        service = ChatService(mock_db)
        result = service._check_conversation_rate_limit(client_id=1)

        assert result['allowed'] is True

    def test_conversation_rate_limit_exceeded(self):
        """Test conversation rate limit when exceeded."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 100

        service = ChatService(mock_db)
        result = service._check_conversation_rate_limit(client_id=1)

        assert result['allowed'] is False


# =============================================================================
# HELPER METHOD TESTS
# =============================================================================

class TestHelperMethods:
    """Tests for helper methods."""

    def test_calculate_waiting_time_just_now(self):
        """Test waiting time calculation for recent escalation."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        service = ChatService(mock_db)

        result = service._calculate_waiting_time(datetime.utcnow())
        assert 'Just now' in result or 'min' in result

    def test_calculate_waiting_time_hours(self):
        """Test waiting time calculation for hours."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        service = ChatService(mock_db)

        two_hours_ago = datetime.utcnow() - timedelta(hours=2)
        result = service._calculate_waiting_time(two_hours_ago)
        assert 'hour' in result

    def test_calculate_waiting_time_days(self):
        """Test waiting time calculation for days."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        service = ChatService(mock_db)

        two_days_ago = datetime.utcnow() - timedelta(days=2)
        result = service._calculate_waiting_time(two_days_ago)
        assert 'day' in result

    def test_calculate_waiting_time_none(self):
        """Test waiting time calculation with None."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        service = ChatService(mock_db)

        result = service._calculate_waiting_time(None)
        assert 'Unknown' in result

    def test_generate_welcome_message_active(self):
        """Test welcome message for active client."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        service = ChatService(mock_db)

        context = {
            'client_name': 'John',
            'client_stage': 'active'
        }
        result = service._generate_welcome_message(context)

        assert 'John' in result
        assert 'credit restoration' in result.lower() or 'case' in result.lower()

    def test_generate_welcome_message_non_active(self):
        """Test welcome message for non-active client."""
        from services.chat_service import ChatService

        mock_db = MagicMock(spec=Session)
        service = ChatService(mock_db)

        context = {
            'client_name': 'Jane',
            'client_stage': 'onboarding'
        }
        result = service._generate_welcome_message(context)

        assert 'Jane' in result


# =============================================================================
# GET CHAT SERVICE FUNCTION TESTS
# =============================================================================

class TestGetChatService:
    """Tests for convenience function."""

    def test_get_chat_service(self):
        """Test get_chat_service convenience function."""
        from services.chat_service import get_chat_service, ChatService

        mock_db = MagicMock(spec=Session)
        service = get_chat_service(mock_db)

        assert isinstance(service, ChatService)
        assert service.db == mock_db
