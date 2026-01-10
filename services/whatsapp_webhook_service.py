"""
WhatsApp Webhook Service

Handles incoming WhatsApp messages from Twilio for:
- Document intake (photos of IDs, credit reports, etc.)
- Keyword commands (STATUS, HELP)
- Auto-replies within 24hr window

NOT a full chat system - for conversations use portal messaging.
"""

import os
import re
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

from database import Client, WhatsAppMessage, ClientUpload


class WhatsAppWebhookService:
    """Service for processing incoming WhatsApp messages"""

    # Keyword commands (case-insensitive)
    KEYWORDS = {
        'STATUS': 'status',
        'HELP': 'help',
        'STOP': 'stop',  # Handled by Twilio, but we track it
    }

    # Document type mapping for common descriptions
    DOCUMENT_HINTS = {
        'id': 'id_document',
        'license': 'drivers_license',
        'dl': 'drivers_license',
        'ssn': 'ssn_card',
        'social': 'ssn_card',
        'utility': 'utility_bill',
        'bill': 'utility_bill',
        'report': 'credit_report',
        'letter': 'cra_response',
        'response': 'cra_response',
    }

    def __init__(self, db):
        self.db = db
        self.twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID', '')
        self.twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN', '')
        self.upload_folder = os.environ.get('UPLOAD_FOLDER', 'static/client_uploads')

    def process_incoming(
        self,
        from_number: str,
        to_number: str,
        body: str,
        message_sid: str,
        profile_name: str = '',
        media_urls: List[str] = None,
        media_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        Process an incoming WhatsApp message.

        Args:
            from_number: Sender's WhatsApp number (whatsapp:+1234567890)
            to_number: Recipient number (our WhatsApp number)
            body: Message text
            message_sid: Twilio message SID
            profile_name: Sender's WhatsApp profile name
            media_urls: List of media attachment URLs
            media_types: List of media content types

        Returns:
            dict with 'success', 'twiml' (optional response), 'message_id'
        """
        media_urls = media_urls or []
        media_types = media_types or []

        # Normalize phone number for lookup
        normalized_phone = self._normalize_phone(from_number)

        # Try to identify the client
        client = self._identify_client(normalized_phone)

        # Create WhatsAppMessage record
        message = WhatsAppMessage(
            client_id=client.id if client else None,
            twilio_sid=message_sid,
            direction='inbound',
            from_number=from_number,
            to_number=to_number,
            body=body,
            has_media=len(media_urls) > 0,
            media_count=len(media_urls),
            media_url=media_urls[0] if media_urls else None,
            media_type=media_types[0] if media_types else None,
            profile_name=profile_name,
            status='received'
        )
        self.db.add(message)
        self.db.commit()

        # Handle unidentified sender
        if not client:
            return self._handle_unidentified_sender(message)

        # Check if client has WhatsApp enabled
        if not client.whatsapp_opt_in:
            # Still process media but don't send auto-replies
            if media_urls:
                self._process_media_attachments(client, message, media_urls, media_types)
            return {'success': True, 'message_id': message.id}

        # Handle media attachments (document intake)
        if media_urls:
            return self._handle_media_message(client, message, media_urls, media_types, body)

        # Handle text message (check for keywords)
        return self._handle_text_message(client, message, body)

    def handle_status_callback(
        self,
        message_sid: str,
        status: str,
        error_code: str = '',
        error_message: str = ''
    ) -> Dict[str, Any]:
        """
        Handle status updates for outbound messages.

        Args:
            message_sid: Twilio message SID
            status: New status (sent, delivered, read, failed)
            error_code: Error code if failed
            error_message: Error message if failed
        """
        message = self.db.query(WhatsAppMessage).filter(
            WhatsAppMessage.twilio_sid == message_sid
        ).first()

        if message:
            message.status = status
            if error_code:
                message.error_code = error_code
            if error_message:
                message.error_message = error_message
            message.updated_at = datetime.utcnow()
            self.db.commit()

        return {'success': True}

    def _identify_client(self, phone: str) -> Optional[Client]:
        """
        Find a client by phone number.

        Searches across multiple phone fields (phone, mobile, phone_2, whatsapp_number).
        """
        if not phone:
            return None

        # Try exact match on whatsapp_number first
        client = self.db.query(Client).filter(
            Client.whatsapp_number == phone
        ).first()
        if client:
            return client

        # Try other phone fields with flexible matching
        phone_variants = self._get_phone_variants(phone)

        for variant in phone_variants:
            client = self.db.query(Client).filter(
                (Client.phone == variant) |
                (Client.mobile == variant) |
                (Client.phone_2 == variant) |
                (Client.whatsapp_number == variant)
            ).first()
            if client:
                return client

        return None

    def _normalize_phone(self, whatsapp_number: str) -> str:
        """
        Normalize WhatsApp number to E.164 format.

        Input: whatsapp:+15551234567
        Output: +15551234567
        """
        if not whatsapp_number:
            return ''

        # Remove whatsapp: prefix
        phone = whatsapp_number.replace('whatsapp:', '')

        # Keep only digits and leading +
        if phone.startswith('+'):
            return '+' + re.sub(r'[^\d]', '', phone[1:])
        return re.sub(r'[^\d]', '', phone)

    def _get_phone_variants(self, phone: str) -> List[str]:
        """
        Generate phone number variants for flexible matching.

        E.g., +15551234567 -> ['+15551234567', '5551234567', '15551234567']
        """
        variants = [phone]

        digits_only = re.sub(r'[^\d]', '', phone)
        if digits_only:
            variants.append(digits_only)

            # Without country code (assuming US +1)
            if digits_only.startswith('1') and len(digits_only) == 11:
                variants.append(digits_only[1:])

            # With + prefix
            if not phone.startswith('+'):
                variants.append('+' + digits_only)

        return variants

    def _handle_unidentified_sender(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """
        Handle messages from unknown senders.

        Returns a TwiML response asking them to log into the portal.
        """
        twiml = self._build_twiml_response(
            "We couldn't find your account. Please log into your portal or contact us for assistance."
        )
        return {
            'success': True,
            'message_id': message.id,
            'twiml': twiml,
            'identified': False
        }

    def _handle_media_message(
        self,
        client: Client,
        message: WhatsAppMessage,
        media_urls: List[str],
        media_types: List[str],
        body: str
    ) -> Dict[str, Any]:
        """
        Handle incoming media attachments (document intake).

        Downloads media from Twilio, creates ClientUpload record.
        """
        uploads = self._process_media_attachments(client, message, media_urls, media_types, body)

        # Send confirmation
        count = len(uploads)
        if count == 1:
            reply = "Got it! We received your document. Our team will review it shortly."
        else:
            reply = f"Got it! We received {count} documents. Our team will review them shortly."

        twiml = self._build_twiml_response(reply)

        return {
            'success': True,
            'message_id': message.id,
            'twiml': twiml,
            'uploads': [u.id for u in uploads]
        }

    def _process_media_attachments(
        self,
        client: Client,
        message: WhatsAppMessage,
        media_urls: List[str],
        media_types: List[str],
        body: str = ''
    ) -> List[ClientUpload]:
        """
        Download and store media attachments.
        """
        uploads = []

        # Try to infer document type from message body
        doc_type = self._infer_document_type(body)

        for i, (url, content_type) in enumerate(zip(media_urls, media_types)):
            try:
                # Download media from Twilio
                media_bytes = self._download_media(url)
                if not media_bytes:
                    continue

                # Determine file extension
                ext = self._get_extension_from_content_type(content_type)

                # Create filename
                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                filename = f"whatsapp_{timestamp}_{i}{ext}"

                # Save file
                client_folder = os.path.join(self.upload_folder, str(client.id))
                os.makedirs(client_folder, exist_ok=True)
                file_path = os.path.join(client_folder, filename)

                with open(file_path, 'wb') as f:
                    f.write(media_bytes)

                # Create ClientUpload record
                upload = ClientUpload(
                    client_id=client.id,
                    category='whatsapp_intake',
                    document_type=doc_type,
                    file_name=filename,
                    file_path=file_path,
                    file_size=len(media_bytes),
                    file_type=content_type,
                    notes=f"Received via WhatsApp. Message: {body[:200]}" if body else "Received via WhatsApp",
                    uploaded_at=datetime.utcnow()
                )
                self.db.add(upload)
                self.db.commit()

                # Link upload to message
                if i == 0:
                    message.upload_id = upload.id
                    message.media_processed = True
                    self.db.commit()

                uploads.append(upload)

            except Exception as e:
                print(f"Error processing WhatsApp media: {e}")
                continue

        return uploads

    def _download_media(self, url: str) -> Optional[bytes]:
        """
        Download media from Twilio with authentication.
        """
        if not self.twilio_account_sid or not self.twilio_auth_token:
            print("Twilio credentials not configured for media download")
            return None

        try:
            response = requests.get(
                url,
                auth=(self.twilio_account_sid, self.twilio_auth_token),
                timeout=30
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            print(f"Error downloading media from Twilio: {e}")
            return None

    def _infer_document_type(self, body: str) -> str:
        """
        Try to infer document type from message text.
        """
        if not body:
            return 'pending_classification'

        body_lower = body.lower()

        for hint, doc_type in self.DOCUMENT_HINTS.items():
            if hint in body_lower:
                return doc_type

        return 'pending_classification'

    def _get_extension_from_content_type(self, content_type: str) -> str:
        """
        Get file extension from MIME type.
        """
        mapping = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        }
        return mapping.get(content_type, '.bin')

    def _handle_text_message(
        self,
        client: Client,
        message: WhatsAppMessage,
        body: str
    ) -> Dict[str, Any]:
        """
        Handle text-only messages (check for keywords).
        """
        body_upper = body.strip().upper()

        # Check for keywords
        if body_upper in self.KEYWORDS:
            keyword = self.KEYWORDS[body_upper]

            if keyword == 'status':
                return self._handle_status_keyword(client, message)
            elif keyword == 'help':
                return self._handle_help_keyword(client, message)
            elif keyword == 'stop':
                # Twilio handles STOP automatically, but we track opt-out
                client.whatsapp_opt_in = False
                self.db.commit()
                return {'success': True, 'message_id': message.id}

        # No keyword match - just acknowledge within 24hr window
        # Don't send unsolicited replies to avoid template requirements
        return {'success': True, 'message_id': message.id}

    def _handle_status_keyword(self, client: Client, message: WhatsAppMessage) -> Dict[str, Any]:
        """
        Handle STATUS keyword - send case status summary.
        """
        # Build status summary
        round_num = client.current_dispute_round or 0
        status = client.dispute_status or 'new'

        status_messages = {
            'new': 'Your case is being set up.',
            'active': f'Your case is active. Currently in Round {round_num}.',
            'waiting_response': f'Round {round_num} disputes sent. Waiting for bureau responses.',
            'complete': 'Your case has been completed.',
        }

        status_text = status_messages.get(status, f'Case status: {status}')

        first_name = client.first_name or client.name.split()[0] if client.name else 'there'
        reply = f"Hi {first_name}! {status_text}\n\nLog into your portal for more details."

        twiml = self._build_twiml_response(reply)

        return {
            'success': True,
            'message_id': message.id,
            'twiml': twiml
        }

    def _handle_help_keyword(self, client: Client, message: WhatsAppMessage) -> Dict[str, Any]:
        """
        Handle HELP keyword - send available commands.
        """
        reply = (
            "Available commands:\n"
            "- STATUS: Get your case status\n"
            "- HELP: Show this message\n"
            "- STOP: Opt out of WhatsApp messages\n\n"
            "You can also send photos of documents anytime!"
        )

        twiml = self._build_twiml_response(reply)

        return {
            'success': True,
            'message_id': message.id,
            'twiml': twiml
        }

    def _build_twiml_response(self, message: str) -> str:
        """
        Build TwiML response for auto-reply.
        """
        # Escape XML special characters
        escaped = (
            message
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;')
        )

        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Message>{escaped}</Message>
</Response>'''


def get_whatsapp_webhook_service(db) -> WhatsAppWebhookService:
    """Factory function to get WhatsAppWebhookService instance."""
    return WhatsAppWebhookService(db)
