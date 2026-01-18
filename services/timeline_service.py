"""
Timeline Service for Client Journey Tracking

Manages timeline events that visualize a client's journey from signup
through dispute resolution. Provides methods to create, retrieve, and
display timeline events in the client portal.
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from database import SessionLocal, Client, TimelineEvent


# Define event types with their icons and categories
EVENT_TYPES = {
    # Onboarding events
    'signup': {
        'title': 'Account Created',
        'icon': 'user-plus',
        'category': 'onboarding',
        'is_milestone': True
    },
    'personal_info_completed': {
        'title': 'Personal Information Completed',
        'icon': 'user',
        'category': 'onboarding',
        'is_milestone': False
    },
    'documents_uploaded': {
        'title': 'Documents Uploaded',
        'icon': 'file-upload',
        'category': 'onboarding',
        'is_milestone': False
    },
    'id_verified': {
        'title': 'Identity Verified',
        'icon': 'id-card',
        'category': 'onboarding',
        'is_milestone': True
    },
    'agreement_signed': {
        'title': 'Service Agreement Signed',
        'icon': 'file-signature',
        'category': 'onboarding',
        'is_milestone': True
    },
    'payment_completed': {
        'title': 'Payment Completed',
        'icon': 'credit-card',
        'category': 'onboarding',
        'is_milestone': True
    },
    'onboarding_complete': {
        'title': 'Onboarding Complete',
        'icon': 'check-circle',
        'category': 'onboarding',
        'is_milestone': True
    },

    # Document events
    'document_uploaded': {
        'title': 'Document Uploaded',
        'icon': 'file-upload',
        'category': 'documents',
        'is_milestone': False
    },
    'credit_report_uploaded': {
        'title': 'Credit Report Uploaded',
        'icon': 'file-alt',
        'category': 'documents',
        'is_milestone': True
    },
    'cra_response_received': {
        'title': 'CRA Response Received',
        'icon': 'envelope-open',
        'category': 'documents',
        'is_milestone': True
    },

    # Analysis events
    'analysis_started': {
        'title': 'Credit Report Analysis Started',
        'icon': 'search',
        'category': 'analysis',
        'is_milestone': False
    },
    'analysis_complete': {
        'title': 'Credit Report Analysis Complete',
        'icon': 'chart-bar',
        'category': 'analysis',
        'is_milestone': True
    },
    'violations_found': {
        'title': 'FCRA Violations Found',
        'icon': 'exclamation-triangle',
        'category': 'analysis',
        'is_milestone': True
    },

    # Dispute events
    'dispute_letters_generated': {
        'title': 'Dispute Letters Generated',
        'icon': 'file-alt',
        'category': 'disputes',
        'is_milestone': True
    },
    'dispute_sent': {
        'title': 'Dispute Letter Sent',
        'icon': 'paper-plane',
        'category': 'disputes',
        'is_milestone': True
    },
    'dispute_delivered': {
        'title': 'Dispute Letter Delivered',
        'icon': 'check',
        'category': 'disputes',
        'is_milestone': False
    },
    'response_deadline': {
        'title': 'Response Deadline',
        'icon': 'clock',
        'category': 'disputes',
        'is_milestone': False
    },

    # Response events
    'response_received': {
        'title': 'Bureau Response Received',
        'icon': 'envelope-open',
        'category': 'responses',
        'is_milestone': True
    },
    'item_deleted': {
        'title': 'Negative Item Deleted',
        'icon': 'trash-alt',
        'category': 'responses',
        'is_milestone': True
    },
    'item_updated': {
        'title': 'Item Updated by Bureau',
        'icon': 'edit',
        'category': 'responses',
        'is_milestone': False
    },
    'item_verified': {
        'title': 'Item Verified by Bureau',
        'icon': 'check-circle',
        'category': 'responses',
        'is_milestone': False
    },

    # Status changes
    'status_changed': {
        'title': 'Status Updated',
        'icon': 'sync',
        'category': 'status',
        'is_milestone': False
    },
    'round_started': {
        'title': 'New Dispute Round Started',
        'icon': 'redo',
        'category': 'status',
        'is_milestone': True
    },
    'round_completed': {
        'title': 'Dispute Round Completed',
        'icon': 'flag-checkered',
        'category': 'status',
        'is_milestone': True
    },

    # Communication events
    'message_sent': {
        'title': 'Message Sent',
        'icon': 'comment',
        'category': 'communication',
        'is_milestone': False
    },
    'call_scheduled': {
        'title': 'Call Scheduled',
        'icon': 'phone',
        'category': 'communication',
        'is_milestone': False
    },
    'call_completed': {
        'title': 'Consultation Call Completed',
        'icon': 'phone-alt',
        'category': 'communication',
        'is_milestone': False
    },

    # Completion events
    'case_resolved': {
        'title': 'Case Resolved',
        'icon': 'trophy',
        'category': 'completion',
        'is_milestone': True
    },
    'settlement_reached': {
        'title': 'Settlement Reached',
        'icon': 'handshake',
        'category': 'completion',
        'is_milestone': True
    }
}


class TimelineService:
    """Service for managing client timeline events"""

    def __init__(self, db: Session):
        self.db = db

    def create_event(
        self,
        client_id: int,
        event_type: str,
        title: str = None,
        description: str = None,
        icon: str = None,
        category: str = None,
        related_type: str = None,
        related_id: int = None,
        metadata: dict = None,
        is_milestone: bool = None,
        event_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Create a new timeline event for a client.

        Args:
            client_id: ID of the client
            event_type: Type of event (see EVENT_TYPES)
            title: Custom title (or use default from EVENT_TYPES)
            description: Optional detailed description
            icon: Font Awesome icon class (or use default)
            category: Event category (or use default)
            related_type: Type of related entity (e.g., 'dispute_letter')
            related_id: ID of the related entity
            metadata: Additional event data as dict
            is_milestone: Whether this is a major event
            event_date: When the event occurred (defaults to now)

        Returns:
            dict with success status and event details
        """
        # Validate client exists
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {'success': False, 'error': 'Client not found'}

        # Get defaults from EVENT_TYPES if available
        event_config = EVENT_TYPES.get(event_type, {})

        event = TimelineEvent(
            client_id=client_id,
            event_type=event_type,
            event_category=category or event_config.get('category', 'general'),
            title=title or event_config.get('title', event_type.replace('_', ' ').title()),
            description=description,
            icon=icon or event_config.get('icon', 'circle'),
            related_type=related_type,
            related_id=related_id,
            metadata_json=metadata,
            is_milestone=is_milestone if is_milestone is not None else event_config.get('is_milestone', False),
            is_visible=True,
            event_date=event_date or datetime.utcnow()
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return {
            'success': True,
            'event_id': event.id,
            'event_type': event.event_type,
            'title': event.title,
            'created_at': event.created_at.isoformat()
        }

    def get_timeline(
        self,
        client_id: int,
        limit: int = 50,
        offset: int = 0,
        category: str = None,
        milestones_only: bool = False
    ) -> Dict[str, Any]:
        """
        Get timeline events for a client.

        Args:
            client_id: ID of the client
            limit: Maximum number of events to return
            offset: Number of events to skip
            category: Filter by category (onboarding, documents, disputes, etc.)
            milestones_only: Only return milestone events

        Returns:
            dict with events list and metadata
        """
        query = self.db.query(TimelineEvent).filter(
            TimelineEvent.client_id == client_id,
            TimelineEvent.is_visible == True
        )

        if category:
            query = query.filter(TimelineEvent.event_category == category)

        if milestones_only:
            query = query.filter(TimelineEvent.is_milestone == True)

        total = query.count()
        events = query.order_by(desc(TimelineEvent.event_date)).offset(offset).limit(limit).all()

        return {
            'success': True,
            'client_id': client_id,
            'total': total,
            'events': [self._event_to_dict(e) for e in events]
        }

    def get_recent_events(self, client_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Get most recent timeline events for a client."""
        events = self.db.query(TimelineEvent).filter(
            TimelineEvent.client_id == client_id,
            TimelineEvent.is_visible == True
        ).order_by(desc(TimelineEvent.event_date)).limit(limit).all()

        return [self._event_to_dict(e) for e in events]

    def get_milestones(self, client_id: int) -> List[Dict[str, Any]]:
        """Get all milestone events for a client."""
        events = self.db.query(TimelineEvent).filter(
            TimelineEvent.client_id == client_id,
            TimelineEvent.is_milestone == True,
            TimelineEvent.is_visible == True
        ).order_by(TimelineEvent.event_date).all()

        return [self._event_to_dict(e) for e in events]

    def get_progress_summary(self, client_id: int) -> Dict[str, Any]:
        """
        Get a summary of client progress through their journey.

        Returns:
            dict with progress stats and current stage
        """
        events = self.db.query(TimelineEvent).filter(
            TimelineEvent.client_id == client_id
        ).all()

        if not events:
            return {
                'success': True,
                'client_id': client_id,
                'total_events': 0,
                'milestones_completed': 0,
                'current_stage': 'signup',
                'stages': self._get_stage_progress([])
            }

        milestones = [e for e in events if e.is_milestone]
        event_types = {e.event_type for e in events}

        # Determine current stage based on completed events
        current_stage = self._determine_stage(event_types)

        return {
            'success': True,
            'client_id': client_id,
            'total_events': len(events),
            'milestones_completed': len(milestones),
            'current_stage': current_stage,
            'first_event': min(e.event_date for e in events).isoformat() if events else None,
            'last_event': max(e.event_date for e in events).isoformat() if events else None,
            'stages': self._get_stage_progress(event_types)
        }

    def _determine_stage(self, event_types: set) -> str:
        """Determine current stage based on completed events."""
        if 'case_resolved' in event_types or 'settlement_reached' in event_types:
            return 'completed'
        if 'response_received' in event_types:
            return 'awaiting_response'
        if 'dispute_sent' in event_types:
            return 'disputes_sent'
        if 'analysis_complete' in event_types:
            return 'analysis_complete'
        if 'credit_report_uploaded' in event_types:
            return 'report_uploaded'
        if 'onboarding_complete' in event_types:
            return 'onboarded'
        if 'signup' in event_types:
            return 'onboarding'
        return 'signup'

    def _get_stage_progress(self, event_types: set) -> List[Dict[str, Any]]:
        """Get stage progress with completion status."""
        stages = [
            {'key': 'signup', 'name': 'Account Created', 'check_event': 'signup'},
            {'key': 'onboarding', 'name': 'Onboarding', 'check_event': 'onboarding_complete'},
            {'key': 'report_uploaded', 'name': 'Credit Report Uploaded', 'check_event': 'credit_report_uploaded'},
            {'key': 'analysis_complete', 'name': 'Analysis Complete', 'check_event': 'analysis_complete'},
            {'key': 'disputes_sent', 'name': 'Disputes Sent', 'check_event': 'dispute_sent'},
            {'key': 'awaiting_response', 'name': 'Awaiting Response', 'check_event': 'response_received'},
            {'key': 'completed', 'name': 'Case Resolved', 'check_event': 'case_resolved'}
        ]

        for stage in stages:
            stage['completed'] = stage['check_event'] in event_types
            del stage['check_event']

        return stages

    def _event_to_dict(self, event: TimelineEvent) -> Dict[str, Any]:
        """Convert TimelineEvent to dictionary."""
        return {
            'id': event.id,
            'event_type': event.event_type,
            'category': event.event_category,
            'title': event.title,
            'description': event.description,
            'icon': event.icon,
            'is_milestone': event.is_milestone,
            'related_type': event.related_type,
            'related_id': event.related_id,
            'metadata': event.metadata_json,
            'event_date': event.event_date.isoformat() if event.event_date else None,
            'created_at': event.created_at.isoformat() if event.created_at else None
        }

    def hide_event(self, event_id: int) -> Dict[str, Any]:
        """Hide a timeline event from display."""
        event = self.db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
        if not event:
            return {'success': False, 'error': 'Event not found'}

        event.is_visible = False
        self.db.commit()

        return {'success': True, 'event_id': event_id}

    def delete_event(self, event_id: int) -> Dict[str, Any]:
        """Delete a timeline event."""
        event = self.db.query(TimelineEvent).filter(TimelineEvent.id == event_id).first()
        if not event:
            return {'success': False, 'error': 'Event not found'}

        self.db.delete(event)
        self.db.commit()

        return {'success': True, 'event_id': event_id}

    def backfill_events(self, client_id: int) -> Dict[str, Any]:
        """
        Backfill timeline events from existing client data.
        Useful for clients created before timeline feature.

        Returns:
            dict with number of events created
        """
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {'success': False, 'error': 'Client not found'}

        events_created = 0

        # Check if signup event already exists
        existing = self.db.query(TimelineEvent).filter(
            TimelineEvent.client_id == client_id,
            TimelineEvent.event_type == 'signup'
        ).first()

        if not existing and client.created_at:
            self.create_event(
                client_id=client_id,
                event_type='signup',
                event_date=client.created_at
            )
            events_created += 1

        # Check for agreement signed
        if client.agreement_signed:
            existing = self.db.query(TimelineEvent).filter(
                TimelineEvent.client_id == client_id,
                TimelineEvent.event_type == 'agreement_signed'
            ).first()
            if not existing:
                self.create_event(
                    client_id=client_id,
                    event_type='agreement_signed',
                    event_date=getattr(client, 'agreement_signed_at', None) or client.updated_at or datetime.utcnow()
                )
                events_created += 1

        # Check for payment completed
        if client.payment_status in ['paid', 'completed', 'active']:
            existing = self.db.query(TimelineEvent).filter(
                TimelineEvent.client_id == client_id,
                TimelineEvent.event_type == 'payment_completed'
            ).first()
            if not existing:
                self.create_event(
                    client_id=client_id,
                    event_type='payment_completed'
                )
                events_created += 1

        return {
            'success': True,
            'client_id': client_id,
            'events_created': events_created
        }


def get_timeline_service(db: Session = None) -> TimelineService:
    """Factory function to get TimelineService instance."""
    if db is None:
        db = SessionLocal()
    return TimelineService(db)


# Helper functions for creating events from other services

def log_signup_event(db: Session, client_id: int) -> None:
    """Log a signup event for a client."""
    service = TimelineService(db)
    service.create_event(client_id=client_id, event_type='signup')


def log_document_uploaded(db: Session, client_id: int, document_type: str, document_id: int = None) -> None:
    """Log a document upload event."""
    service = TimelineService(db)

    # Determine event type based on document
    if document_type in ['credit_report', 'credit_report_pdf']:
        event_type = 'credit_report_uploaded'
    elif document_type in ['cra_response', 'bureau_response']:
        event_type = 'cra_response_received'
    else:
        event_type = 'document_uploaded'

    service.create_event(
        client_id=client_id,
        event_type=event_type,
        description=f"Uploaded: {document_type.replace('_', ' ').title()}",
        related_type='client_upload',
        related_id=document_id
    )


def log_analysis_complete(db: Session, client_id: int, analysis_id: int, violations_count: int = 0) -> None:
    """Log analysis completion event."""
    service = TimelineService(db)
    service.create_event(
        client_id=client_id,
        event_type='analysis_complete',
        description=f"Found {violations_count} potential violations" if violations_count else None,
        related_type='analysis',
        related_id=analysis_id,
        metadata={'violations_count': violations_count}
    )


def log_dispute_sent(db: Session, client_id: int, bureau: str, letter_id: int = None, round_number: int = 1) -> None:
    """Log dispute letter sent event."""
    service = TimelineService(db)
    service.create_event(
        client_id=client_id,
        event_type='dispute_sent',
        title=f"Dispute Sent to {bureau}",
        description=f"Round {round_number} dispute letter sent via certified mail",
        related_type='dispute_letter',
        related_id=letter_id,
        metadata={'bureau': bureau, 'round': round_number}
    )


def log_response_received(db: Session, client_id: int, bureau: str, response_id: int = None) -> None:
    """Log bureau response received event."""
    service = TimelineService(db)
    service.create_event(
        client_id=client_id,
        event_type='response_received',
        title=f"Response from {bureau}",
        related_type='cra_response',
        related_id=response_id,
        metadata={'bureau': bureau}
    )


def log_status_changed(db: Session, client_id: int, old_status: str, new_status: str) -> None:
    """Log status change event."""
    service = TimelineService(db)
    service.create_event(
        client_id=client_id,
        event_type='status_changed',
        title=f"Status: {new_status.replace('_', ' ').title()}",
        description=f"Changed from {old_status.replace('_', ' ').title()}" if old_status else None,
        metadata={'old_status': old_status, 'new_status': new_status}
    )


def log_milestone(db: Session, client_id: int, event_type: str, title: str, description: str = None) -> None:
    """Log a milestone event for a client.

    Generic function for logging important milestones in the client journey.

    Args:
        db: Database session
        client_id: Client ID
        event_type: Type of milestone event (e.g., 'case_activated', 'round_complete')
        title: Display title for the event
        description: Optional description
    """
    service = TimelineService(db)
    service.create_event(
        client_id=client_id,
        event_type=event_type,
        title=title,
        description=description
    )
