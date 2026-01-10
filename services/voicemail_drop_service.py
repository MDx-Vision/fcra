"""
Voicemail Drop Service

Manages ringless voicemail drops for automated client outreach.
Supports multiple providers: Slybroadcast, Drop Cowboy, Twilio.
"""

import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from database import (
    SessionLocal,
    VoicemailRecording,
    VoicemailDrop,
    VoicemailCampaign,
    Client,
    Staff
)


# Voicemail categories
VOICEMAIL_CATEGORIES = [
    {'key': 'welcome', 'name': 'Welcome', 'description': 'New client welcome messages'},
    {'key': 'reminder', 'name': 'Reminder', 'description': 'Document and action reminders'},
    {'key': 'update', 'name': 'Case Update', 'description': 'Case status updates'},
    {'key': 'follow_up', 'name': 'Follow Up', 'description': 'Follow-up messages'},
    {'key': 'payment', 'name': 'Payment', 'description': 'Payment reminders'},
    {'key': 'custom', 'name': 'Custom', 'description': 'Custom messages'},
]

# Provider configurations
PROVIDERS = {
    'slybroadcast': {
        'name': 'Slybroadcast',
        'api_url': 'https://www.slybroadcast.com/api/',
        'cost_per_drop_cents': 3,  # $0.03 per drop
    },
    'dropcowboy': {
        'name': 'Drop Cowboy',
        'api_url': 'https://api.dropcowboy.com/v1/',
        'cost_per_drop_cents': 4,  # $0.04 per drop
    },
    'twilio': {
        'name': 'Twilio',
        'api_url': 'https://api.twilio.com/2010-04-01/',
        'cost_per_drop_cents': 5,  # Variable, ~$0.05 per drop
    },
}


class VoicemailDropService:
    """Service for managing voicemail recordings and drops"""

    def __init__(self, db: Session):
        self.db = db
        self.default_provider = os.getenv('VOICEMAIL_PROVIDER', 'slybroadcast')
        self.slybroadcast_user = os.getenv('SLYBROADCAST_USER')
        self.slybroadcast_pass = os.getenv('SLYBROADCAST_PASS')
        self.dropcowboy_key = os.getenv('DROPCOWBOY_API_KEY')
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')

    # ==================== RECORDING MANAGEMENT ====================

    def create_recording(
        self,
        name: str,
        file_path: str,
        category: str = 'custom',
        description: str = None,
        file_name: str = None,
        file_size_bytes: int = None,
        duration_seconds: int = None,
        format: str = 'mp3',
        staff_id: int = None
    ) -> VoicemailRecording:
        """Create a new voicemail recording"""
        recording = VoicemailRecording(
            name=name,
            description=description,
            category=category,
            file_path=file_path,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            duration_seconds=duration_seconds,
            format=format,
            is_active=True,
            is_system=False,
            created_by_staff_id=staff_id
        )
        self.db.add(recording)
        self.db.commit()
        self.db.refresh(recording)
        return recording

    def get_recording(self, recording_id: int) -> Optional[VoicemailRecording]:
        """Get a recording by ID"""
        return self.db.query(VoicemailRecording).filter(
            VoicemailRecording.id == recording_id
        ).first()

    def get_recordings(
        self,
        category: str = None,
        active_only: bool = True,
        limit: int = 100
    ) -> List[VoicemailRecording]:
        """Get all recordings with optional filters"""
        query = self.db.query(VoicemailRecording)

        if active_only:
            query = query.filter(VoicemailRecording.is_active == True)

        if category:
            query = query.filter(VoicemailRecording.category == category)

        return query.order_by(VoicemailRecording.created_at.desc()).limit(limit).all()

    def update_recording(
        self,
        recording_id: int,
        **kwargs
    ) -> Optional[VoicemailRecording]:
        """Update a recording"""
        recording = self.get_recording(recording_id)
        if not recording:
            return None

        allowed_fields = ['name', 'description', 'category', 'is_active']
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(recording, field, value)

        recording.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(recording)
        return recording

    def delete_recording(self, recording_id: int) -> Dict[str, Any]:
        """Soft delete a recording (set inactive)"""
        recording = self.get_recording(recording_id)
        if not recording:
            return {'success': False, 'error': 'Recording not found'}

        if recording.is_system:
            return {'success': False, 'error': 'Cannot delete system recordings'}

        recording.is_active = False
        recording.updated_at = datetime.utcnow()
        self.db.commit()

        return {'success': True, 'message': 'Recording deactivated'}

    # ==================== VOICEMAIL DROP SENDING ====================

    def send_drop(
        self,
        recording_id: int,
        client_id: int,
        phone_number: str = None,
        trigger_type: str = 'manual',
        trigger_event: str = None,
        scheduled_at: datetime = None,
        staff_id: int = None,
        provider: str = None
    ) -> Dict[str, Any]:
        """Send a voicemail drop to a client"""

        # Validate recording
        recording = self.get_recording(recording_id)
        if not recording:
            return {'success': False, 'error': 'Recording not found'}

        if not recording.is_active:
            return {'success': False, 'error': 'Recording is inactive'}

        # Validate client
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {'success': False, 'error': 'Client not found'}

        # Get phone number
        if not phone_number:
            phone_number = client.phone

        if not phone_number:
            return {'success': False, 'error': 'No phone number available'}

        # Clean phone number
        phone_number = self._clean_phone_number(phone_number)
        if not phone_number:
            return {'success': False, 'error': 'Invalid phone number'}

        # Use default provider if not specified
        provider = provider or self.default_provider

        # Create drop record
        drop = VoicemailDrop(
            recording_id=recording_id,
            client_id=client_id,
            phone_number=phone_number,
            trigger_type=trigger_type,
            trigger_event=trigger_event,
            status='pending',
            provider=provider,
            scheduled_at=scheduled_at,
            initiated_by_staff_id=staff_id,
            cost_cents=PROVIDERS.get(provider, {}).get('cost_per_drop_cents', 0)
        )
        self.db.add(drop)
        self.db.commit()
        self.db.refresh(drop)

        # If scheduled for later, don't send now
        if scheduled_at and scheduled_at > datetime.utcnow():
            return {
                'success': True,
                'drop_id': drop.id,
                'status': 'scheduled',
                'scheduled_at': scheduled_at.isoformat()
            }

        # Send immediately
        result = self._send_to_provider(drop, recording)

        return result

    def _send_to_provider(self, drop: VoicemailDrop, recording: VoicemailRecording) -> Dict[str, Any]:
        """Send drop to the configured provider"""

        drop.queued_at = datetime.utcnow()

        try:
            if drop.provider == 'slybroadcast':
                result = self._send_slybroadcast(drop, recording)
            elif drop.provider == 'dropcowboy':
                result = self._send_dropcowboy(drop, recording)
            elif drop.provider == 'twilio':
                result = self._send_twilio(drop, recording)
            else:
                # Mock provider for testing
                result = self._send_mock(drop, recording)

            if result.get('success'):
                drop.status = 'sent'
                drop.sent_at = datetime.utcnow()
                drop.provider_id = result.get('provider_id')
                drop.provider_response = result.get('response')

                # Update recording usage
                recording.use_count = (recording.use_count or 0) + 1
                recording.last_used_at = datetime.utcnow()
            else:
                drop.status = 'failed'
                drop.error_code = result.get('error_code')
                drop.error_message = result.get('error')

            self.db.commit()
            self.db.refresh(drop)

            return {
                'success': result.get('success', False),
                'drop_id': drop.id,
                'status': drop.status,
                'provider_id': drop.provider_id,
                'error': result.get('error')
            }

        except Exception as e:
            drop.status = 'failed'
            drop.error_message = str(e)
            self.db.commit()

            return {
                'success': False,
                'drop_id': drop.id,
                'status': 'failed',
                'error': str(e)
            }

    def _send_slybroadcast(self, drop: VoicemailDrop, recording: VoicemailRecording) -> Dict[str, Any]:
        """Send via Slybroadcast API"""
        if not self.slybroadcast_user or not self.slybroadcast_pass:
            return {'success': False, 'error': 'Slybroadcast credentials not configured'}

        try:
            # Slybroadcast API call
            url = PROVIDERS['slybroadcast']['api_url'] + 'vmb.php'
            data = {
                'c_uid': self.slybroadcast_user,
                'c_password': self.slybroadcast_pass,
                'c_phone': drop.phone_number,
                'c_url': recording.file_path,  # URL to audio file
                'c_callerID': os.getenv('VOICEMAIL_CALLER_ID', ''),
            }

            response = requests.post(url, data=data, timeout=30)
            result = response.json() if response.headers.get('content-type', '').startswith('application/json') else {'response': response.text}

            if response.status_code == 200 and result.get('status') == 'OK':
                return {
                    'success': True,
                    'provider_id': result.get('session_id'),
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'error': result.get('message', 'Unknown error'),
                    'error_code': result.get('error_code'),
                    'response': result
                }

        except requests.RequestException as e:
            return {'success': False, 'error': f'API request failed: {str(e)}'}

    def _send_dropcowboy(self, drop: VoicemailDrop, recording: VoicemailRecording) -> Dict[str, Any]:
        """Send via Drop Cowboy API"""
        if not self.dropcowboy_key:
            return {'success': False, 'error': 'Drop Cowboy API key not configured'}

        try:
            url = PROVIDERS['dropcowboy']['api_url'] + 'drops'
            headers = {
                'Authorization': f'Bearer {self.dropcowboy_key}',
                'Content-Type': 'application/json'
            }
            data = {
                'phone_number': drop.phone_number,
                'audio_url': recording.file_path,
            }

            response = requests.post(url, json=data, headers=headers, timeout=30)
            result = response.json()

            if response.status_code in [200, 201] and result.get('id'):
                return {
                    'success': True,
                    'provider_id': result.get('id'),
                    'response': result
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'response': result
                }

        except requests.RequestException as e:
            return {'success': False, 'error': f'API request failed: {str(e)}'}

    def _send_twilio(self, drop: VoicemailDrop, recording: VoicemailRecording) -> Dict[str, Any]:
        """Send via Twilio (using Answering Machine Detection)"""
        if not self.twilio_sid or not self.twilio_token:
            return {'success': False, 'error': 'Twilio credentials not configured'}

        try:
            from twilio.rest import Client as TwilioClient

            client = TwilioClient(self.twilio_sid, self.twilio_token)

            # Create call with AMD (Answering Machine Detection)
            call = client.calls.create(
                to=drop.phone_number,
                from_=os.getenv('TWILIO_PHONE_NUMBER'),
                url=recording.file_path,  # TwiML URL or hosted audio
                machine_detection='DetectMessageEnd',
                machine_detection_timeout=30
            )

            return {
                'success': True,
                'provider_id': call.sid,
                'response': {'sid': call.sid, 'status': call.status}
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _send_mock(self, drop: VoicemailDrop, recording: VoicemailRecording) -> Dict[str, Any]:
        """Mock provider for testing"""
        import uuid
        return {
            'success': True,
            'provider_id': f'mock_{uuid.uuid4().hex[:12]}',
            'response': {'status': 'mocked', 'message': 'Mock drop sent'}
        }

    def _clean_phone_number(self, phone: str) -> Optional[str]:
        """Clean and validate phone number"""
        if not phone:
            return None

        # Remove non-digits
        digits = ''.join(c for c in phone if c.isdigit())

        # Handle US numbers
        if len(digits) == 10:
            return f'+1{digits}'
        elif len(digits) == 11 and digits.startswith('1'):
            return f'+{digits}'
        elif len(digits) > 10:
            return f'+{digits}'

        return None

    # ==================== DROP STATUS & HISTORY ====================

    def get_drop(self, drop_id: int) -> Optional[VoicemailDrop]:
        """Get a drop by ID"""
        return self.db.query(VoicemailDrop).filter(VoicemailDrop.id == drop_id).first()

    def get_drops(
        self,
        client_id: int = None,
        recording_id: int = None,
        status: str = None,
        provider: str = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[VoicemailDrop]:
        """Get drops with optional filters"""
        query = self.db.query(VoicemailDrop)

        if client_id:
            query = query.filter(VoicemailDrop.client_id == client_id)
        if recording_id:
            query = query.filter(VoicemailDrop.recording_id == recording_id)
        if status:
            query = query.filter(VoicemailDrop.status == status)
        if provider:
            query = query.filter(VoicemailDrop.provider == provider)

        return query.order_by(VoicemailDrop.created_at.desc()).offset(offset).limit(limit).all()

    def get_client_drop_history(self, client_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Get voicemail drop history for a client"""
        drops = self.get_drops(client_id=client_id, limit=limit)
        return [drop.to_dict() for drop in drops]

    def retry_drop(self, drop_id: int) -> Dict[str, Any]:
        """Retry a failed drop"""
        drop = self.get_drop(drop_id)
        if not drop:
            return {'success': False, 'error': 'Drop not found'}

        if drop.status not in ['failed', 'cancelled']:
            return {'success': False, 'error': 'Can only retry failed or cancelled drops'}

        if drop.retry_count >= drop.max_retries:
            return {'success': False, 'error': 'Max retries exceeded'}

        recording = self.get_recording(drop.recording_id)
        if not recording:
            return {'success': False, 'error': 'Recording not found'}

        # Reset for retry
        drop.retry_count += 1
        drop.status = 'pending'
        drop.error_code = None
        drop.error_message = None
        self.db.commit()

        # Attempt send
        return self._send_to_provider(drop, recording)

    def cancel_drop(self, drop_id: int) -> Dict[str, Any]:
        """Cancel a pending or scheduled drop"""
        drop = self.get_drop(drop_id)
        if not drop:
            return {'success': False, 'error': 'Drop not found'}

        if drop.status not in ['pending', 'scheduled']:
            return {'success': False, 'error': 'Can only cancel pending or scheduled drops'}

        drop.status = 'cancelled'
        drop.updated_at = datetime.utcnow()
        self.db.commit()

        return {'success': True, 'message': 'Drop cancelled'}

    # ==================== CAMPAIGNS ====================

    def create_campaign(
        self,
        name: str,
        recording_id: int,
        target_type: str = 'manual',
        target_filters: Dict = None,
        description: str = None,
        scheduled_at: datetime = None,
        send_window_start: str = None,
        send_window_end: str = None,
        send_days: List[str] = None,
        staff_id: int = None
    ) -> VoicemailCampaign:
        """Create a new voicemail campaign"""
        campaign = VoicemailCampaign(
            name=name,
            description=description,
            recording_id=recording_id,
            target_type=target_type,
            target_filters=target_filters,
            status='draft',
            scheduled_at=scheduled_at,
            send_window_start=send_window_start,
            send_window_end=send_window_end,
            send_days=send_days,
            created_by_staff_id=staff_id
        )
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        return campaign

    def get_campaign(self, campaign_id: int) -> Optional[VoicemailCampaign]:
        """Get a campaign by ID"""
        return self.db.query(VoicemailCampaign).filter(
            VoicemailCampaign.id == campaign_id
        ).first()

    def get_campaigns(
        self,
        status: str = None,
        limit: int = 50
    ) -> List[VoicemailCampaign]:
        """Get all campaigns"""
        query = self.db.query(VoicemailCampaign)

        if status:
            query = query.filter(VoicemailCampaign.status == status)

        return query.order_by(VoicemailCampaign.created_at.desc()).limit(limit).all()

    def add_targets_to_campaign(
        self,
        campaign_id: int,
        client_ids: List[int]
    ) -> Dict[str, Any]:
        """Add target clients to a campaign"""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return {'success': False, 'error': 'Campaign not found'}

        if campaign.status != 'draft':
            return {'success': False, 'error': 'Can only add targets to draft campaigns'}

        added = 0
        for client_id in client_ids:
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if client and client.phone:
                drop = VoicemailDrop(
                    recording_id=campaign.recording_id,
                    client_id=client_id,
                    phone_number=self._clean_phone_number(client.phone),
                    trigger_type='campaign',
                    campaign_id=campaign_id,
                    status='pending',
                    provider=self.default_provider
                )
                self.db.add(drop)
                added += 1

        campaign.target_count = added
        campaign.total_drops = added
        self.db.commit()

        return {'success': True, 'added': added}

    def start_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Start a campaign"""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return {'success': False, 'error': 'Campaign not found'}

        if campaign.status != 'draft':
            return {'success': False, 'error': 'Can only start draft campaigns'}

        if campaign.total_drops == 0:
            return {'success': False, 'error': 'Campaign has no targets'}

        recording = self.get_recording(campaign.recording_id)
        if not recording:
            return {'success': False, 'error': 'Recording not found'}

        campaign.status = 'in_progress'
        campaign.started_at = datetime.utcnow()
        self.db.commit()

        # Process drops
        drops = self.db.query(VoicemailDrop).filter(
            VoicemailDrop.campaign_id == campaign_id,
            VoicemailDrop.status == 'pending'
        ).all()

        sent = 0
        failed = 0

        for drop in drops:
            result = self._send_to_provider(drop, recording)
            if result.get('success'):
                sent += 1
            else:
                failed += 1

        campaign.sent_count = sent
        campaign.failed_count = failed

        if sent + failed >= campaign.total_drops:
            campaign.status = 'completed'
            campaign.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(campaign)

        return {
            'success': True,
            'campaign_id': campaign_id,
            'sent': sent,
            'failed': failed,
            'status': campaign.status
        }

    def pause_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Pause an in-progress campaign"""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return {'success': False, 'error': 'Campaign not found'}

        if campaign.status != 'in_progress':
            return {'success': False, 'error': 'Can only pause in-progress campaigns'}

        campaign.status = 'paused'
        self.db.commit()

        return {'success': True, 'message': 'Campaign paused'}

    def cancel_campaign(self, campaign_id: int) -> Dict[str, Any]:
        """Cancel a campaign and all pending drops"""
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            return {'success': False, 'error': 'Campaign not found'}

        if campaign.status in ['completed', 'cancelled']:
            return {'success': False, 'error': 'Campaign already finished'}

        # Cancel all pending drops
        self.db.query(VoicemailDrop).filter(
            VoicemailDrop.campaign_id == campaign_id,
            VoicemailDrop.status == 'pending'
        ).update({'status': 'cancelled'})

        campaign.status = 'cancelled'
        self.db.commit()

        return {'success': True, 'message': 'Campaign cancelled'}

    # ==================== STATISTICS ====================

    def get_stats(self) -> Dict[str, Any]:
        """Get overall voicemail drop statistics"""
        total_recordings = self.db.query(func.count(VoicemailRecording.id)).filter(
            VoicemailRecording.is_active == True
        ).scalar()

        total_drops = self.db.query(func.count(VoicemailDrop.id)).scalar()

        drops_by_status = self.db.query(
            VoicemailDrop.status,
            func.count(VoicemailDrop.id)
        ).group_by(VoicemailDrop.status).all()

        status_counts = {status: count for status, count in drops_by_status}

        total_cost = self.db.query(func.sum(VoicemailDrop.cost_cents)).filter(
            VoicemailDrop.status.in_(['sent', 'delivered'])
        ).scalar() or 0

        active_campaigns = self.db.query(func.count(VoicemailCampaign.id)).filter(
            VoicemailCampaign.status == 'in_progress'
        ).scalar()

        # Recent drops (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_drops = self.db.query(func.count(VoicemailDrop.id)).filter(
            VoicemailDrop.created_at >= yesterday
        ).scalar()

        return {
            'total_recordings': total_recordings,
            'total_drops': total_drops,
            'drops_by_status': status_counts,
            'sent_count': status_counts.get('sent', 0) + status_counts.get('delivered', 0),
            'failed_count': status_counts.get('failed', 0),
            'pending_count': status_counts.get('pending', 0),
            'total_cost_cents': total_cost,
            'total_cost_dollars': total_cost / 100,
            'active_campaigns': active_campaigns,
            'recent_drops_24h': recent_drops
        }

    def get_recording_stats(self, recording_id: int) -> Dict[str, Any]:
        """Get stats for a specific recording"""
        recording = self.get_recording(recording_id)
        if not recording:
            return {'error': 'Recording not found'}

        total_uses = self.db.query(func.count(VoicemailDrop.id)).filter(
            VoicemailDrop.recording_id == recording_id
        ).scalar()

        successful = self.db.query(func.count(VoicemailDrop.id)).filter(
            VoicemailDrop.recording_id == recording_id,
            VoicemailDrop.status.in_(['sent', 'delivered'])
        ).scalar()

        failed = self.db.query(func.count(VoicemailDrop.id)).filter(
            VoicemailDrop.recording_id == recording_id,
            VoicemailDrop.status == 'failed'
        ).scalar()

        return {
            'recording_id': recording_id,
            'name': recording.name,
            'total_uses': total_uses,
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / total_uses * 100) if total_uses > 0 else 0
        }


# Factory function
def get_voicemail_drop_service(db: Session = None) -> VoicemailDropService:
    """Get VoicemailDropService instance"""
    if db is None:
        db = SessionLocal()
    return VoicemailDropService(db)
