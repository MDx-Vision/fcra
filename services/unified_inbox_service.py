"""
Unified Inbox Service (P32)

Aggregates messages from multiple channels into a single inbox view:
- Email (EmailLog)
- SMS (SMSLog)
- WhatsApp (WhatsAppMessage)
- Portal Messages (ClientMessage)
- AI Chat (ChatMessage/ChatConversation)

Created: 2026-01-19
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import joinedload

# Channel constants
CHANNEL_EMAIL = "email"
CHANNEL_SMS = "sms"
CHANNEL_WHATSAPP = "whatsapp"
CHANNEL_PORTAL = "portal"
CHANNEL_CHAT = "chat"

ALL_CHANNELS = [
    CHANNEL_EMAIL,
    CHANNEL_SMS,
    CHANNEL_WHATSAPP,
    CHANNEL_PORTAL,
    CHANNEL_CHAT,
]

# Direction constants
DIRECTION_INBOUND = "inbound"
DIRECTION_OUTBOUND = "outbound"


class UnifiedMessage:
    """
    Normalized message object that represents a message from any channel.
    This is a virtual/computed object, not stored in database.
    """

    def __init__(
        self,
        id: int,
        channel: str,
        client_id: Optional[int],
        direction: str,
        subject: Optional[str],
        content: str,
        preview: str,
        sender_name: Optional[str],
        recipient: Optional[str],
        is_read: bool,
        status: str,
        timestamp: datetime,
        raw_data: Dict[str, Any] = None,
    ):
        self.id = id
        self.channel = channel
        self.client_id = client_id
        self.direction = direction
        self.subject = subject
        self.content = content
        self.preview = preview[:100] + "..." if len(preview) > 100 else preview
        self.sender_name = sender_name
        self.recipient = recipient
        self.is_read = is_read
        self.status = status
        self.timestamp = timestamp
        self.raw_data = raw_data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "channel": self.channel,
            "client_id": self.client_id,
            "direction": self.direction,
            "subject": self.subject,
            "content": self.content,
            "preview": self.preview,
            "sender_name": self.sender_name,
            "recipient": self.recipient,
            "is_read": self.is_read,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "raw_data": self.raw_data,
        }


class UnifiedInboxService:
    """
    Service for aggregating and managing messages across all channels.
    """

    def __init__(self, db_session=None):
        """Initialize with optional database session."""
        self.db = db_session

    def _get_db(self):
        """Get database session, creating one if needed."""
        if self.db:
            return self.db
        from database import get_db

        return get_db()

    # =========================================================================
    # MESSAGE CONVERSION HELPERS
    # =========================================================================

    def _email_to_unified(self, email_log, client=None) -> UnifiedMessage:
        """Convert EmailLog to UnifiedMessage."""
        return UnifiedMessage(
            id=email_log.id,
            channel=CHANNEL_EMAIL,
            client_id=email_log.client_id,
            direction=DIRECTION_OUTBOUND,  # EmailLog is always outbound
            subject=email_log.subject,
            content=email_log.subject,  # We don't store email body in EmailLog
            preview=email_log.subject or "No subject",
            sender_name="System",
            recipient=email_log.email_address,
            is_read=True,  # Outbound emails are "read" by definition
            status=email_log.status or "sent",
            timestamp=email_log.sent_at or email_log.created_at,
            raw_data={
                "template_type": email_log.template_type,
                "message_id": email_log.message_id,
                "error_message": email_log.error_message,
            },
        )

    def _sms_to_unified(self, sms_log, client=None) -> UnifiedMessage:
        """Convert SMSLog to UnifiedMessage."""
        return UnifiedMessage(
            id=sms_log.id,
            channel=CHANNEL_SMS,
            client_id=sms_log.client_id,
            direction=DIRECTION_OUTBOUND,  # SMSLog is always outbound
            subject=None,
            content=sms_log.message,
            preview=sms_log.message or "No message",
            sender_name="System",
            recipient=sms_log.phone_number,
            is_read=True,  # Outbound SMS are "read" by definition
            status=sms_log.status or "sent",
            timestamp=sms_log.sent_at or sms_log.created_at,
            raw_data={
                "template_type": sms_log.template_type,
                "twilio_sid": sms_log.twilio_sid,
                "error_message": sms_log.error_message,
            },
        )

    def _whatsapp_to_unified(self, wa_msg, client=None) -> UnifiedMessage:
        """Convert WhatsAppMessage to UnifiedMessage."""
        direction = wa_msg.direction or DIRECTION_OUTBOUND

        return UnifiedMessage(
            id=wa_msg.id,
            channel=CHANNEL_WHATSAPP,
            client_id=wa_msg.client_id,
            direction=direction,
            subject=None,
            content=wa_msg.body or "",
            preview=(
                wa_msg.body or "Media message" if wa_msg.has_media else "No message"
            ),
            sender_name=(
                wa_msg.profile_name if direction == DIRECTION_INBOUND else "System"
            ),
            recipient=(
                wa_msg.to_number
                if direction == DIRECTION_OUTBOUND
                else wa_msg.from_number
            ),
            is_read=wa_msg.status in ["delivered", "read"],
            status=wa_msg.status or "sent",
            timestamp=wa_msg.created_at,
            raw_data={
                "twilio_sid": wa_msg.twilio_sid,
                "has_media": wa_msg.has_media,
                "media_type": wa_msg.media_type,
                "template_name": wa_msg.template_name,
                "error_message": wa_msg.error_message,
            },
        )

    def _portal_message_to_unified(
        self, msg, client=None, staff=None
    ) -> UnifiedMessage:
        """Convert ClientMessage (portal) to UnifiedMessage."""
        is_from_client = msg.sender_type == "client"

        # Get names
        client_name = None
        staff_name = None
        if client:
            client_name = (
                f"{client.first_name or ''} {client.last_name or ''}".strip()
                or "Client"
            )
        if staff:
            staff_name = staff.name or "Staff"

        return UnifiedMessage(
            id=msg.id,
            channel=CHANNEL_PORTAL,
            client_id=msg.client_id,
            direction=DIRECTION_INBOUND if is_from_client else DIRECTION_OUTBOUND,
            subject=None,
            content=msg.message,
            preview=msg.message or "No message",
            sender_name=client_name if is_from_client else staff_name,
            recipient=staff_name if is_from_client else client_name,
            is_read=msg.is_read,
            status="read" if msg.is_read else "unread",
            timestamp=msg.created_at,
            raw_data={
                "sender_type": msg.sender_type,
                "staff_id": msg.staff_id,
                "read_at": msg.read_at.isoformat() if msg.read_at else None,
            },
        )

    def _chat_message_to_unified(
        self, chat_msg, conversation=None, client=None
    ) -> UnifiedMessage:
        """Convert ChatMessage to UnifiedMessage."""
        is_from_client = chat_msg.role == "user"

        client_name = None
        if client:
            client_name = (
                f"{client.first_name or ''} {client.last_name or ''}".strip()
                or "Client"
            )

        return UnifiedMessage(
            id=chat_msg.id,
            channel=CHANNEL_CHAT,
            client_id=conversation.client_id if conversation else None,
            direction=DIRECTION_INBOUND if is_from_client else DIRECTION_OUTBOUND,
            subject=None,
            content=chat_msg.content,
            preview=chat_msg.content or "No message",
            sender_name=client_name if is_from_client else "AI Assistant",
            recipient="AI Assistant" if is_from_client else client_name,
            is_read=True,  # Chat messages are always "read"
            status="delivered",
            timestamp=chat_msg.created_at,
            raw_data={
                "role": chat_msg.role,
                "conversation_id": chat_msg.conversation_id,
                "tokens_used": chat_msg.tokens_used,
                "model_used": chat_msg.model_used,
            },
        )

    # =========================================================================
    # INBOX RETRIEVAL METHODS
    # =========================================================================

    def get_client_inbox(
        self,
        client_id: int,
        channels: List[str] = None,
        direction: str = None,
        is_read: bool = None,
        search_query: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get all messages for a specific client across all channels.

        Args:
            client_id: The client ID to get messages for
            channels: List of channels to include (default: all)
            direction: Filter by direction ('inbound' or 'outbound')
            is_read: Filter by read status
            search_query: Search in message content
            limit: Maximum messages to return
            offset: Offset for pagination

        Returns:
            Dict with 'messages', 'total', 'unread_count', 'channels'
        """
        from database import (
            ChatConversation,
            ChatMessage,
            Client,
            ClientMessage,
            EmailLog,
            SMSLog,
            Staff,
            WhatsAppMessage,
        )

        db = self._get_db()
        channels = channels or ALL_CHANNELS
        messages = []

        # Get client info
        client = db.query(Client).filter(Client.id == client_id).first()

        # Collect messages from each channel
        if CHANNEL_EMAIL in channels:
            query = db.query(EmailLog).filter(EmailLog.client_id == client_id)
            if search_query:
                query = query.filter(EmailLog.subject.ilike(f"%{search_query}%"))
            for email in query.all():
                messages.append(self._email_to_unified(email, client))

        if CHANNEL_SMS in channels:
            query = db.query(SMSLog).filter(SMSLog.client_id == client_id)
            if search_query:
                query = query.filter(SMSLog.message.ilike(f"%{search_query}%"))
            for sms in query.all():
                messages.append(self._sms_to_unified(sms, client))

        if CHANNEL_WHATSAPP in channels:
            query = db.query(WhatsAppMessage).filter(
                WhatsAppMessage.client_id == client_id
            )
            if search_query:
                query = query.filter(WhatsAppMessage.body.ilike(f"%{search_query}%"))
            if direction:
                query = query.filter(WhatsAppMessage.direction == direction)
            for wa in query.all():
                messages.append(self._whatsapp_to_unified(wa, client))

        if CHANNEL_PORTAL in channels:
            query = db.query(ClientMessage).filter(ClientMessage.client_id == client_id)
            if search_query:
                query = query.filter(ClientMessage.message.ilike(f"%{search_query}%"))
            if direction == DIRECTION_INBOUND:
                query = query.filter(ClientMessage.sender_type == "client")
            elif direction == DIRECTION_OUTBOUND:
                query = query.filter(ClientMessage.sender_type == "staff")
            if is_read is not None:
                query = query.filter(ClientMessage.is_read == is_read)
            for msg in query.all():
                staff = (
                    db.query(Staff).filter(Staff.id == msg.staff_id).first()
                    if msg.staff_id
                    else None
                )
                messages.append(self._portal_message_to_unified(msg, client, staff))

        if CHANNEL_CHAT in channels:
            # Get chat messages through conversations
            conversations = (
                db.query(ChatConversation)
                .filter(ChatConversation.client_id == client_id)
                .all()
            )

            for conv in conversations:
                chat_query = db.query(ChatMessage).filter(
                    ChatMessage.conversation_id == conv.id
                )
                if search_query:
                    chat_query = chat_query.filter(
                        ChatMessage.content.ilike(f"%{search_query}%")
                    )
                if direction == DIRECTION_INBOUND:
                    chat_query = chat_query.filter(ChatMessage.role == "user")
                elif direction == DIRECTION_OUTBOUND:
                    chat_query = chat_query.filter(ChatMessage.role == "assistant")

                for chat_msg in chat_query.all():
                    messages.append(
                        self._chat_message_to_unified(chat_msg, conv, client)
                    )

        # Filter by direction if specified (for channels that don't have direction field)
        if direction:
            messages = [m for m in messages if m.direction == direction]

        # Filter by read status
        if is_read is not None:
            messages = [m for m in messages if m.is_read == is_read]

        # Sort by timestamp (newest first)
        messages.sort(key=lambda m: m.timestamp or datetime.min, reverse=True)

        # Calculate unread count
        unread_count = sum(1 for m in messages if not m.is_read)

        # Get channel counts
        channel_counts = {}
        for ch in ALL_CHANNELS:
            channel_counts[ch] = sum(1 for m in messages if m.channel == ch)

        total = len(messages)

        # Apply pagination
        messages = messages[offset : offset + limit]

        return {
            "messages": [m.to_dict() for m in messages],
            "total": total,
            "unread_count": unread_count,
            "channels": channel_counts,
            "client_id": client_id,
            "client_name": (
                f"{client.first_name or ''} {client.last_name or ''}".strip()
                if client
                else None
            ),
        }

    def get_staff_inbox(
        self,
        staff_id: int = None,
        channels: List[str] = None,
        is_read: bool = None,
        search_query: str = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get inbox for staff member (messages from their assigned clients).
        If staff_id is None, returns all messages (for admin view).

        Args:
            staff_id: Optional staff ID to filter by assigned clients
            channels: List of channels to include
            is_read: Filter by read status
            search_query: Search query
            limit: Max results
            offset: Pagination offset

        Returns:
            Dict with messages grouped by client
        """
        from database import (
            ChatConversation,
            ChatMessage,
            Client,
            ClientMessage,
            EmailLog,
            SMSLog,
            Staff,
            WhatsAppMessage,
        )

        db = self._get_db()
        channels = channels or ALL_CHANNELS

        # Get clients (optionally filtered by assigned staff)
        client_query = db.query(Client)
        if staff_id:
            client_query = client_query.filter(Client.assigned_to == staff_id)

        clients = client_query.all()
        client_ids = [c.id for c in clients]

        all_messages = []

        # Collect messages from all clients
        for client in clients:
            result = self.get_client_inbox(
                client_id=client.id,
                channels=channels,
                is_read=is_read,
                search_query=search_query,
                limit=1000,  # Get all for aggregation
                offset=0,
            )
            for msg_dict in result["messages"]:
                msg_dict["client_name"] = result["client_name"]
                all_messages.append(msg_dict)

        # Sort by timestamp
        all_messages.sort(key=lambda m: m.get("timestamp", ""), reverse=True)

        # Calculate stats
        unread_count = sum(1 for m in all_messages if not m.get("is_read"))

        # Channel counts
        channel_counts = {}
        for ch in ALL_CHANNELS:
            channel_counts[ch] = sum(1 for m in all_messages if m.get("channel") == ch)

        total = len(all_messages)

        # Apply pagination
        messages = all_messages[offset : offset + limit]

        return {
            "messages": messages,
            "total": total,
            "unread_count": unread_count,
            "channels": channel_counts,
            "client_count": len(clients),
        }

    def search_messages(
        self,
        query: str,
        client_id: int = None,
        channels: List[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search messages across all channels.

        Args:
            query: Search query string
            client_id: Optional client ID filter
            channels: Optional channel filter
            limit: Max results

        Returns:
            List of matching messages
        """
        if client_id:
            result = self.get_client_inbox(
                client_id=client_id, channels=channels, search_query=query, limit=limit
            )
            return result["messages"]
        else:
            result = self.get_staff_inbox(
                channels=channels, search_query=query, limit=limit
            )
            return result["messages"]

    def get_unread_counts(
        self, client_id: int = None, staff_id: int = None
    ) -> Dict[str, int]:
        """
        Get unread message counts by channel.

        Args:
            client_id: Filter by client
            staff_id: Filter by staff's assigned clients

        Returns:
            Dict mapping channel names to unread counts
        """
        from database import Client, ClientMessage

        db = self._get_db()
        counts = {ch: 0 for ch in ALL_CHANNELS}

        # Portal messages are the main ones with read tracking
        query = db.query(ClientMessage).filter(ClientMessage.is_read == False)

        if client_id:
            query = query.filter(ClientMessage.client_id == client_id)
        elif staff_id:
            # Get clients assigned to this staff
            client_ids = (
                db.query(Client.id).filter(Client.assigned_to == staff_id).all()
            )
            client_ids = [c[0] for c in client_ids]
            query = query.filter(ClientMessage.client_id.in_(client_ids))

        counts[CHANNEL_PORTAL] = query.count()

        # Total
        counts["total"] = sum(counts.values())

        return counts

    def mark_read(
        self, channel: str, message_id: int, read_by_staff_id: int = None
    ) -> bool:
        """
        Mark a message as read.

        Args:
            channel: Message channel
            message_id: Message ID
            read_by_staff_id: Staff who read the message

        Returns:
            True if successful
        """
        from database import ClientMessage

        db = self._get_db()

        if channel == CHANNEL_PORTAL:
            msg = db.query(ClientMessage).filter(ClientMessage.id == message_id).first()
            if msg:
                msg.is_read = True
                msg.read_at = datetime.utcnow()
                db.commit()
                return True

        # Other channels don't have read tracking in their models
        return False

    def mark_client_messages_read(
        self, client_id: int, channel: str = None, read_by_staff_id: int = None
    ) -> int:
        """
        Mark all messages from a client as read.

        Args:
            client_id: Client ID
            channel: Optional channel filter
            read_by_staff_id: Staff who read the messages

        Returns:
            Number of messages marked as read
        """
        from database import ClientMessage

        db = self._get_db()
        count = 0

        if channel is None or channel == CHANNEL_PORTAL:
            query = db.query(ClientMessage).filter(
                ClientMessage.client_id == client_id,
                ClientMessage.is_read == False,
                ClientMessage.sender_type
                == "client",  # Only mark client messages as read
            )

            messages = query.all()
            for msg in messages:
                msg.is_read = True
                msg.read_at = datetime.utcnow()
                count += 1

            db.commit()

        return count

    # =========================================================================
    # CONVERSATION THREAD VIEW
    # =========================================================================

    def get_conversation_thread(
        self, client_id: int, include_channels: List[str] = None, limit: int = 100
    ) -> Dict[str, Any]:
        """
        Get a threaded conversation view for a client.
        Messages are ordered chronologically for a chat-like display.

        Args:
            client_id: Client ID
            include_channels: Channels to include (default: portal and chat)
            limit: Max messages

        Returns:
            Dict with thread messages and metadata
        """
        # Default to conversational channels
        include_channels = include_channels or [
            CHANNEL_PORTAL,
            CHANNEL_CHAT,
            CHANNEL_SMS,
        ]

        result = self.get_client_inbox(
            client_id=client_id, channels=include_channels, limit=limit
        )

        # Reverse for chronological order (oldest first for thread view)
        messages = list(reversed(result["messages"]))

        return {
            "thread": messages,
            "total": result["total"],
            "unread_count": result["unread_count"],
            "client_id": client_id,
            "client_name": result.get("client_name"),
        }

    # =========================================================================
    # DASHBOARD STATISTICS
    # =========================================================================

    def get_dashboard_stats(
        self, staff_id: int = None, days: int = 7
    ) -> Dict[str, Any]:
        """
        Get inbox dashboard statistics.

        Args:
            staff_id: Optional staff filter
            days: Number of days to look back

        Returns:
            Dict with various statistics
        """
        from database import (
            ChatConversation,
            Client,
            ClientMessage,
            EmailLog,
            SMSLog,
            WhatsAppMessage,
        )

        db = self._get_db()
        since = datetime.utcnow() - timedelta(days=days)

        # Build client filter
        client_filter = None
        if staff_id:
            client_ids = (
                db.query(Client.id).filter(Client.assigned_to == staff_id).all()
            )
            client_ids = [c[0] for c in client_ids]
            client_filter = lambda q, model: q.filter(model.client_id.in_(client_ids))

        # Count by channel
        def count_with_filter(model, date_field):
            q = db.query(func.count(model.id)).filter(date_field >= since)
            if client_filter and hasattr(model, "client_id"):
                q = client_filter(q, model)
            return q.scalar() or 0

        email_count = count_with_filter(EmailLog, EmailLog.created_at)
        sms_count = count_with_filter(SMSLog, SMSLog.created_at)
        whatsapp_count = count_with_filter(WhatsAppMessage, WhatsAppMessage.created_at)
        portal_count = count_with_filter(ClientMessage, ClientMessage.created_at)

        # Unread portal messages
        unread_query = db.query(func.count(ClientMessage.id)).filter(
            ClientMessage.is_read == False, ClientMessage.sender_type == "client"
        )
        if client_filter:
            unread_query = client_filter(unread_query, ClientMessage)
        unread_count = unread_query.scalar() or 0

        # Active conversations (chat)
        active_chats_query = db.query(func.count(ChatConversation.id)).filter(
            ChatConversation.status == "active"
        )
        if client_filter:
            active_chats_query = client_filter(active_chats_query, ChatConversation)
        active_chats = active_chats_query.scalar() or 0

        # Total messages
        total_messages = email_count + sms_count + whatsapp_count + portal_count

        return {
            "total_messages": total_messages,
            "unread_count": unread_count,
            "active_chats": active_chats,
            "by_channel": {
                CHANNEL_EMAIL: email_count,
                CHANNEL_SMS: sms_count,
                CHANNEL_WHATSAPP: whatsapp_count,
                CHANNEL_PORTAL: portal_count,
            },
            "period_days": days,
        }

    # =========================================================================
    # REPLY / SEND MESSAGE
    # =========================================================================

    def send_reply(
        self,
        client_id: int,
        channel: str,
        content: str,
        staff_id: int,
        subject: str = None,
    ) -> Dict[str, Any]:
        """
        Send a reply to a client through the specified channel.

        Args:
            client_id: Client to send to
            channel: Channel to use
            content: Message content
            staff_id: Staff sending the message
            subject: Optional subject (for email)

        Returns:
            Dict with result status and message info
        """
        from database import Client, ClientMessage

        db = self._get_db()
        client = db.query(Client).filter(Client.id == client_id).first()

        if not client:
            return {"success": False, "error": "Client not found"}

        if channel == CHANNEL_PORTAL:
            # Create portal message
            msg = ClientMessage(
                client_id=client_id,
                staff_id=staff_id,
                message=content,
                sender_type="staff",
                is_read=False,
            )
            db.add(msg)
            db.commit()
            db.refresh(msg)

            return {"success": True, "channel": channel, "message_id": msg.id}

        elif channel == CHANNEL_EMAIL:
            # Use email service
            from services.email_service import send_email

            result = send_email(
                to_email=client.email,
                subject=subject or "Message from Brightpath Ascend",
                html_content=f"<p>{content}</p>",
                template_type="custom_reply",
            )

            return {
                "success": result.get("success", False),
                "channel": channel,
                "error": result.get("error"),
            }

        elif channel == CHANNEL_SMS:
            # Use SMS service
            from services.sms_service import send_sms

            if not client.phone:
                return {"success": False, "error": "Client has no phone number"}

            result = send_sms(
                phone_number=client.phone, message=content, client_id=client_id
            )

            return {
                "success": result.get("success", False),
                "channel": channel,
                "error": result.get("error"),
            }

        else:
            return {"success": False, "error": f"Unsupported channel: {channel}"}


# =========================================================================
# HELPER FUNCTIONS
# =========================================================================


def get_unified_inbox_service(db=None) -> UnifiedInboxService:
    """Factory function to create UnifiedInboxService instance."""
    return UnifiedInboxService(db_session=db)
