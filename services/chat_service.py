"""
AI Chat Service for Client Portal

Provides Claude-powered chat support for clients with:
- FCRA knowledge base integration
- Client context awareness
- Conversation history management
- Automatic escalation detection
- Rate limiting
- Staff escalation workflow
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from database import (
    ChatConversation, ChatMessage, Client, Staff,
    Analysis, Violation, DisputeItem
)
from services.chat_knowledge_base import (
    get_system_prompt, check_escalation_needed
)
from services.ai_usage_service import log_ai_usage


class ChatService:
    """Service for managing AI chat conversations with clients"""

    # Rate limiting configuration
    MAX_MESSAGES_PER_MINUTE = int(os.environ.get('CHAT_MAX_MESSAGES_PER_MINUTE', 10))
    MAX_CONVERSATIONS_PER_DAY = int(os.environ.get('CHAT_MAX_CONVERSATIONS_PER_DAY', 5))
    MAX_TOKENS_PER_CONVERSATION = 50000  # Token budget per conversation

    # AI model configuration
    AI_MODEL = "claude-sonnet-4-20250514"
    MAX_RESPONSE_TOKENS = 1000
    TEMPERATURE = 0.7

    def __init__(self, db: Session):
        self.db = db
        self._anthropic_client = None

    @property
    def anthropic_client(self):
        """Lazy load Anthropic client"""
        if self._anthropic_client is None:
            try:
                from anthropic import Anthropic
                self._anthropic_client = Anthropic(
                    api_key=os.environ.get('ANTHROPIC_API_KEY')
                )
            except Exception as e:
                print(f"Error initializing Anthropic client: {e}")
                raise
        return self._anthropic_client

    # =========================================================================
    # CONVERSATION MANAGEMENT
    # =========================================================================

    def start_conversation(self, client_id: int) -> Dict[str, Any]:
        """
        Start a new chat conversation for a client

        Args:
            client_id: The client's database ID

        Returns:
            dict with conversation details or error
        """
        # Verify client exists
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {'success': False, 'error': 'Client not found'}

        # Check rate limit
        rate_check = self._check_conversation_rate_limit(client_id)
        if not rate_check['allowed']:
            return {
                'success': False,
                'error': f"Daily conversation limit reached ({self.MAX_CONVERSATIONS_PER_DAY} per day)"
            }

        # Get client context for the conversation
        context = self.get_client_context(client_id)

        # Create conversation
        conversation = ChatConversation(
            client_id=client_id,
            status='active',
            started_at=datetime.utcnow(),
            client_context=context
        )
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        # Add system message with context
        system_message = ChatMessage(
            conversation_id=conversation.id,
            role='system',
            content=get_system_prompt(context),
            created_at=datetime.utcnow()
        )
        self.db.add(system_message)

        # Add welcome message from assistant
        welcome_msg = self._generate_welcome_message(context)
        assistant_message = ChatMessage(
            conversation_id=conversation.id,
            role='assistant',
            content=welcome_msg,
            created_at=datetime.utcnow()
        )
        self.db.add(assistant_message)

        conversation.total_messages = 1
        self.db.commit()

        return {
            'success': True,
            'conversation_id': conversation.id,
            'welcome_message': welcome_msg,
            'started_at': conversation.started_at.isoformat()
        }

    def send_message(
        self,
        conversation_id: int,
        message: str,
        client_id: int = None
    ) -> Dict[str, Any]:
        """
        Send a message and get AI response

        Args:
            conversation_id: The conversation ID
            message: The user's message
            client_id: Optional client ID for verification

        Returns:
            dict with AI response or error
        """
        # Get conversation
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()

        if not conversation:
            return {'success': False, 'error': 'Conversation not found'}

        if conversation.status != 'active':
            return {'success': False, 'error': f'Conversation is {conversation.status}'}

        # Verify client ownership if provided
        if client_id and conversation.client_id != client_id:
            return {'success': False, 'error': 'Unauthorized'}

        # Check message rate limit
        rate_check = self._check_message_rate_limit(conversation_id)
        if not rate_check['allowed']:
            return {
                'success': False,
                'error': f"Please wait a moment before sending another message"
            }

        # Check token budget
        if conversation.total_tokens >= self.MAX_TOKENS_PER_CONVERSATION:
            return {
                'success': False,
                'error': 'This conversation has reached its limit. Please start a new conversation.'
            }

        # Check for escalation triggers
        escalation = check_escalation_needed(message)

        # Save user message
        user_msg = ChatMessage(
            conversation_id=conversation_id,
            role='user',
            content=message,
            created_at=datetime.utcnow()
        )
        self.db.add(user_msg)

        # Handle escalation if needed
        if escalation['should_escalate']:
            assistant_response = escalation['message']
            assistant_response += "\n\nWould you like me to connect you with our support team now?"

            assistant_msg = ChatMessage(
                conversation_id=conversation_id,
                role='assistant',
                content=assistant_response,
                created_at=datetime.utcnow(),
                extra_data={'escalation_suggested': True, 'reason': escalation['reason']}
            )
            self.db.add(assistant_msg)

            conversation.total_messages += 2
            self.db.commit()

            return {
                'success': True,
                'response': assistant_response,
                'escalation_suggested': True,
                'escalation_reason': escalation['reason']
            }

        # Generate AI response
        try:
            response_data = self._generate_ai_response(conversation, message)

            if not response_data['success']:
                return response_data

            # Save assistant message
            assistant_msg = ChatMessage(
                conversation_id=conversation_id,
                role='assistant',
                content=response_data['response'],
                tokens_used=response_data.get('tokens_used'),
                model_used=self.AI_MODEL,
                created_at=datetime.utcnow()
            )
            self.db.add(assistant_msg)

            # Update conversation stats
            conversation.total_messages += 2
            conversation.total_tokens += response_data.get('tokens_used', 0)
            conversation.updated_at = datetime.utcnow()
            self.db.commit()

            return {
                'success': True,
                'response': response_data['response'],
                'tokens_used': response_data.get('tokens_used')
            }

        except Exception as e:
            self.db.rollback()
            return {'success': False, 'error': f'AI error: {str(e)}'}

    def get_conversation(
        self,
        conversation_id: int,
        client_id: int = None
    ) -> Dict[str, Any]:
        """
        Get a conversation with all messages

        Args:
            conversation_id: The conversation ID
            client_id: Optional client ID for verification

        Returns:
            dict with conversation and messages
        """
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()

        if not conversation:
            return {'success': False, 'error': 'Conversation not found'}

        if client_id and conversation.client_id != client_id:
            return {'success': False, 'error': 'Unauthorized'}

        # Get messages (exclude system messages for client view)
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.role != 'system'
        ).order_by(ChatMessage.created_at.asc()).all()

        return {
            'success': True,
            'conversation': {
                'id': conversation.id,
                'status': conversation.status,
                'started_at': conversation.started_at.isoformat() if conversation.started_at else None,
                'ended_at': conversation.ended_at.isoformat() if conversation.ended_at else None,
                'total_messages': conversation.total_messages,
                'is_escalated': conversation.status == 'escalated'
            },
            'messages': [
                {
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None,
                    'is_staff': msg.staff_id is not None
                }
                for msg in messages
            ]
        }

    def get_client_conversations(
        self,
        client_id: int,
        include_closed: bool = False
    ) -> Dict[str, Any]:
        """
        Get all conversations for a client

        Args:
            client_id: The client's database ID
            include_closed: Whether to include closed conversations

        Returns:
            dict with list of conversations
        """
        query = self.db.query(ChatConversation).filter(
            ChatConversation.client_id == client_id
        )

        if not include_closed:
            query = query.filter(ChatConversation.status.in_(['active', 'escalated']))

        conversations = query.order_by(
            ChatConversation.updated_at.desc()
        ).all()

        return {
            'success': True,
            'conversations': [
                {
                    'id': conv.id,
                    'status': conv.status,
                    'started_at': conv.started_at.isoformat() if conv.started_at else None,
                    'ended_at': conv.ended_at.isoformat() if conv.ended_at else None,
                    'total_messages': conv.total_messages,
                    'last_updated': conv.updated_at.isoformat() if conv.updated_at else None
                }
                for conv in conversations
            ]
        }

    def close_conversation(
        self,
        conversation_id: int,
        client_id: int = None
    ) -> Dict[str, Any]:
        """
        Close a conversation

        Args:
            conversation_id: The conversation ID
            client_id: Optional client ID for verification

        Returns:
            dict with success status
        """
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()

        if not conversation:
            return {'success': False, 'error': 'Conversation not found'}

        if client_id and conversation.client_id != client_id:
            return {'success': False, 'error': 'Unauthorized'}

        if conversation.status == 'closed':
            return {'success': False, 'error': 'Conversation already closed'}

        conversation.status = 'closed'
        conversation.ended_at = datetime.utcnow()
        self.db.commit()

        return {'success': True, 'message': 'Conversation closed'}

    # =========================================================================
    # ESCALATION
    # =========================================================================

    def escalate_to_staff(
        self,
        conversation_id: int,
        staff_id: int = None,
        reason: str = None,
        client_id: int = None
    ) -> Dict[str, Any]:
        """
        Escalate a conversation to staff

        Args:
            conversation_id: The conversation ID
            staff_id: Optional specific staff member to assign
            reason: Reason for escalation
            client_id: Optional client ID for verification

        Returns:
            dict with success status
        """
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()

        if not conversation:
            return {'success': False, 'error': 'Conversation not found'}

        if client_id and conversation.client_id != client_id:
            return {'success': False, 'error': 'Unauthorized'}

        if conversation.status == 'escalated':
            return {'success': False, 'error': 'Already escalated'}

        # Update conversation
        conversation.status = 'escalated'
        conversation.escalated_at = datetime.utcnow()
        conversation.escalation_reason = reason

        if staff_id:
            staff = self.db.query(Staff).filter(Staff.id == staff_id).first()
            if staff:
                conversation.escalated_to_staff_id = staff_id

        # Add system message about escalation
        system_msg = ChatMessage(
            conversation_id=conversation_id,
            role='system',
            content=f"Conversation escalated to staff support. Reason: {reason or 'Client request'}",
            created_at=datetime.utcnow()
        )
        self.db.add(system_msg)

        # Add assistant message for client
        assistant_msg = ChatMessage(
            conversation_id=conversation_id,
            role='assistant',
            content="I've connected you with our support team. A team member will respond shortly. Thank you for your patience!",
            created_at=datetime.utcnow()
        )
        self.db.add(assistant_msg)

        conversation.total_messages += 1
        self.db.commit()

        return {
            'success': True,
            'message': 'Conversation escalated to staff',
            'escalated_at': conversation.escalated_at.isoformat()
        }

    def get_escalated_conversations(
        self,
        staff_id: int = None,
        include_resolved: bool = False
    ) -> Dict[str, Any]:
        """
        Get escalated conversations for staff dashboard

        Args:
            staff_id: Filter by assigned staff (None = all escalated)
            include_resolved: Whether to include resolved escalations

        Returns:
            dict with list of escalated conversations
        """
        query = self.db.query(ChatConversation).filter(
            ChatConversation.status == 'escalated'
        )

        if staff_id:
            query = query.filter(ChatConversation.escalated_to_staff_id == staff_id)

        conversations = query.order_by(
            ChatConversation.escalated_at.desc()
        ).all()

        result = []
        for conv in conversations:
            # Get client info
            client = self.db.query(Client).filter(Client.id == conv.client_id).first()

            # Get last message
            last_msg = self.db.query(ChatMessage).filter(
                ChatMessage.conversation_id == conv.id,
                ChatMessage.role == 'user'
            ).order_by(ChatMessage.created_at.desc()).first()

            result.append({
                'id': conv.id,
                'client_id': conv.client_id,
                'client_name': f"{client.first_name} {client.last_name}" if client else "Unknown",
                'client_email': client.email if client else None,
                'status': conv.status,
                'escalated_at': conv.escalated_at.isoformat() if conv.escalated_at else None,
                'escalation_reason': conv.escalation_reason,
                'waiting_time': self._calculate_waiting_time(conv.escalated_at),
                'last_message': last_msg.content[:100] if last_msg else None,
                'assigned_to': conv.escalated_to_staff_id
            })

        return {'success': True, 'conversations': result}

    def staff_respond(
        self,
        conversation_id: int,
        staff_id: int,
        message: str
    ) -> Dict[str, Any]:
        """
        Add a staff response to an escalated conversation

        Args:
            conversation_id: The conversation ID
            staff_id: The staff member's ID
            message: The response message

        Returns:
            dict with success status
        """
        conversation = self.db.query(ChatConversation).filter(
            ChatConversation.id == conversation_id
        ).first()

        if not conversation:
            return {'success': False, 'error': 'Conversation not found'}

        if conversation.status not in ['escalated', 'active']:
            return {'success': False, 'error': f'Cannot respond to {conversation.status} conversation'}

        # Verify staff exists
        staff = self.db.query(Staff).filter(Staff.id == staff_id).first()
        if not staff:
            return {'success': False, 'error': 'Staff not found'}

        # Add staff message
        staff_msg = ChatMessage(
            conversation_id=conversation_id,
            role='assistant',
            content=message,
            staff_id=staff_id,
            created_at=datetime.utcnow(),
            extra_data={'staff_name': staff.name}
        )
        self.db.add(staff_msg)

        conversation.total_messages += 1
        conversation.updated_at = datetime.utcnow()

        # Assign staff if not already assigned
        if not conversation.escalated_to_staff_id:
            conversation.escalated_to_staff_id = staff_id

        self.db.commit()

        return {
            'success': True,
            'message_id': staff_msg.id,
            'timestamp': staff_msg.created_at.isoformat()
        }

    # =========================================================================
    # CLIENT CONTEXT
    # =========================================================================

    def get_client_context(self, client_id: int) -> Dict[str, Any]:
        """
        Get context about a client for AI personalization

        Args:
            client_id: The client's database ID

        Returns:
            dict with client context information
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {}

        # Calculate days active
        days_active = 0
        if client.created_at:
            days_active = (datetime.utcnow() - client.created_at).days

        context = {
            'client_name': f"{client.first_name or ''} {client.last_name or ''}".strip() or "Client",
            'case_status': client.dispute_status or 'unknown',
            'client_stage': client.client_stage or 'unknown',
            'dispute_round': client.current_dispute_round or 1,
            'days_active': days_active
        }

        # Get violation count
        violations_count = self.db.query(func.count(Violation.id)).filter(
            Violation.client_id == client_id
        ).scalar() or 0
        context['violations_count'] = violations_count

        # Get items removed (if any)
        items_removed = self.db.query(func.count(DisputeItem.id)).filter(
            DisputeItem.client_id == client_id,
            DisputeItem.status == 'deleted'
        ).scalar() or 0
        context['items_removed'] = items_removed

        return context

    # =========================================================================
    # PRIVATE METHODS
    # =========================================================================

    def _generate_ai_response(
        self,
        conversation: ChatConversation,
        user_message: str
    ) -> Dict[str, Any]:
        """Generate AI response using Claude"""

        # Build message history
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.conversation_id == conversation.id
        ).order_by(ChatMessage.created_at.asc()).all()

        # Get system prompt
        system_prompt = None
        api_messages = []

        for msg in messages:
            if msg.role == 'system':
                system_prompt = msg.content
            else:
                api_messages.append({
                    'role': msg.role,
                    'content': msg.content
                })

        # Add current user message
        api_messages.append({
            'role': 'user',
            'content': user_message
        })

        # Call Claude API
        try:
            import time
            start_time = time.time()
            response = self.anthropic_client.messages.create(
                model=self.AI_MODEL,
                max_tokens=self.MAX_RESPONSE_TOKENS,
                temperature=self.TEMPERATURE,
                system=system_prompt or get_system_prompt(conversation.client_context),
                messages=api_messages
            )
            duration_ms = int((time.time() - start_time) * 1000)

            response_text = response.content[0].text
            tokens_used = response.usage.input_tokens + response.usage.output_tokens

            # Log AI usage
            log_ai_usage(
                service="chat_support",
                operation="chat_message",
                model=response.model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                duration_ms=duration_ms,
                client_id=conversation.client_id
            )

            return {
                'success': True,
                'response': response_text,
                'tokens_used': tokens_used
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'AI error: {str(e)}'
            }

    def _generate_welcome_message(self, context: dict) -> str:
        """Generate a personalized welcome message"""
        client_name = context.get('client_name', 'there')

        # Keep it short and friendly
        if context.get('client_stage') == 'active':
            return f"Hi {client_name}! I'm here to help you with any questions about your credit restoration case or the FCRA dispute process. How can I assist you today?"
        else:
            return f"Hi {client_name}! I'm here to help answer your questions about credit restoration and the FCRA dispute process. What would you like to know?"

    def _check_message_rate_limit(self, conversation_id: int) -> Dict[str, bool]:
        """Check if message rate limit is exceeded"""
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)

        recent_messages = self.db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.conversation_id == conversation_id,
            ChatMessage.role == 'user',
            ChatMessage.created_at >= one_minute_ago
        ).scalar() or 0

        return {
            'allowed': recent_messages < self.MAX_MESSAGES_PER_MINUTE,
            'count': recent_messages,
            'limit': self.MAX_MESSAGES_PER_MINUTE
        }

    def _check_conversation_rate_limit(self, client_id: int) -> Dict[str, bool]:
        """Check if conversation rate limit is exceeded"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        today_conversations = self.db.query(func.count(ChatConversation.id)).filter(
            ChatConversation.client_id == client_id,
            ChatConversation.started_at >= today_start
        ).scalar() or 0

        return {
            'allowed': today_conversations < self.MAX_CONVERSATIONS_PER_DAY,
            'count': today_conversations,
            'limit': self.MAX_CONVERSATIONS_PER_DAY
        }

    def _calculate_waiting_time(self, escalated_at: datetime) -> str:
        """Calculate human-readable waiting time"""
        if not escalated_at:
            return "Unknown"

        diff = datetime.utcnow() - escalated_at
        minutes = int(diff.total_seconds() / 60)

        if minutes < 1:
            return "Just now"
        elif minutes < 60:
            return f"{minutes} min"
        elif minutes < 1440:
            hours = minutes // 60
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            days = minutes // 1440
            return f"{days} day{'s' if days > 1 else ''}"


# Convenience function for getting service instance
def get_chat_service(db: Session) -> ChatService:
    """Get a ChatService instance"""
    return ChatService(db)
