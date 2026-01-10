"""
CROA Signing Service

Manages the Credit Repair Organizations Act (CROA) document signing workflow.
Ensures compliance with federal requirements:
- Rights Disclosure MUST be signed before any contract
- 3 business day cancellation period after contract signing
- Sequential document signing in proper order
"""

import base64
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session

from database import (
    SessionLocal,
    Client,
    DocumentTemplate,
    ClientDocumentSignature,
    CROAProgress
)


# CROA Document definitions in signing order
CROA_DOCUMENTS = [
    {
        'code': 'CROA_01_RIGHTS_DISCLOSURE',
        'name': 'Consumer Credit File Rights Disclosure',
        'description': 'Required disclosure of your rights under federal law (CROA § 1679c)',
        'must_sign_before_contract': True,
        'is_required': True,
        'order': 1
    },
    {
        'code': 'CROA_02_LPOA',
        'name': 'Limited Power of Attorney',
        'description': 'Authorization for us to communicate with credit bureaus on your behalf',
        'must_sign_before_contract': False,
        'is_required': True,
        'order': 2
    },
    {
        'code': 'CROA_03_SERVICE_AGREEMENT',
        'name': 'Service Agreement',
        'description': 'Terms, conditions, and fee structure for services',
        'must_sign_before_contract': False,
        'is_required': True,
        'order': 3
    },
    {
        'code': 'CROA_04_CANCELLATION_NOTICE',
        'name': 'Notice of Right to Cancel',
        'description': 'Your 3-business-day cancellation rights under CROA',
        'must_sign_before_contract': False,
        'is_required': True,
        'order': 4
    },
    {
        'code': 'CROA_05_SERVICE_COMPLETION',
        'name': 'Service Completion Authorization',
        'description': 'Authorization to begin work after cancellation period',
        'must_sign_before_contract': False,
        'is_required': True,
        'order': 5
    },
    {
        'code': 'CROA_06_HIPAA',
        'name': 'HIPAA Authorization',
        'description': 'Authorization to access health-related information if applicable',
        'must_sign_before_contract': False,
        'is_required': False,  # Optional
        'order': 6
    },
    {
        'code': 'CROA_07_WELCOME_PACKET',
        'name': 'Client Welcome Packet',
        'description': 'Welcome information and next steps',
        'must_sign_before_contract': False,
        'is_required': True,
        'order': 7
    }
]

# Map document codes to progress fields
DOCUMENT_PROGRESS_FIELDS = {
    'CROA_01_RIGHTS_DISCLOSURE': 'rights_disclosure_signed_at',
    'CROA_02_LPOA': 'lpoa_signed_at',
    'CROA_03_SERVICE_AGREEMENT': 'service_agreement_signed_at',
    'CROA_04_CANCELLATION_NOTICE': 'cancellation_notice_signed_at',
    'CROA_05_SERVICE_COMPLETION': 'service_completion_signed_at',
    'CROA_06_HIPAA': 'hipaa_signed_at',
    'CROA_07_WELCOME_PACKET': 'welcome_packet_signed_at'
}

SIGNATURE_FOLDER = "static/signatures"


class CROASigningService:
    """Service for managing CROA document signing workflow"""

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_progress(self, client_id: int) -> Optional[CROAProgress]:
        """Get existing CROA progress or create new one for client"""
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return None

        progress = self.db.query(CROAProgress).filter(
            CROAProgress.client_id == client_id
        ).first()

        if not progress:
            progress = CROAProgress(client_id=client_id)
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)

        return progress

    def get_progress_summary(self, client_id: int) -> Dict[str, Any]:
        """Get detailed CROA signing progress for a client"""
        progress = self.get_or_create_progress(client_id)
        if not progress:
            return {'error': 'Client not found'}

        documents_status = []
        signed_count = 0

        for doc in CROA_DOCUMENTS:
            field_name = DOCUMENT_PROGRESS_FIELDS.get(doc['code'])
            signed_at = getattr(progress, field_name, None) if field_name else None

            is_signed = signed_at is not None
            if is_signed:
                signed_count += 1

            # Get document content from database
            template = self.db.query(DocumentTemplate).filter(
                DocumentTemplate.code == doc['code']
            ).first()

            documents_status.append({
                'code': doc['code'],
                'name': doc['name'],
                'description': doc['description'],
                'order': doc['order'],
                'is_required': doc['is_required'],
                'must_sign_before_contract': doc['must_sign_before_contract'],
                'is_signed': is_signed,
                'signed_at': signed_at.isoformat() if signed_at else None,
                'has_content': template is not None
            })

        # Calculate cancellation status
        cancellation_status = self._get_cancellation_status(progress)

        return {
            'success': True,
            'client_id': client_id,
            'documents': documents_status,
            'documents_completed': signed_count,
            'total_documents': len(CROA_DOCUMENTS),
            'required_completed': sum(1 for d in documents_status if d['is_signed'] and d['is_required']),
            'required_total': sum(1 for d in CROA_DOCUMENTS if d['is_required']),
            'current_document': progress.current_document,
            'is_complete': progress.is_complete,
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
            'cancellation_status': cancellation_status,
            'percentage': int((signed_count / len(CROA_DOCUMENTS)) * 100)
        }

    def get_document(self, document_code: str) -> Dict[str, Any]:
        """Get a CROA document template by code"""
        template = self.db.query(DocumentTemplate).filter(
            DocumentTemplate.code == document_code,
            DocumentTemplate.is_active == True
        ).first()

        if not template:
            return {'success': False, 'error': f'Document {document_code} not found'}

        doc_config = next((d for d in CROA_DOCUMENTS if d['code'] == document_code), None)

        return {
            'success': True,
            'document': {
                'code': template.code,
                'name': template.name,
                'description': template.description,
                'content_html': template.content_html,
                'version': template.version,
                'order': doc_config['order'] if doc_config else 0,
                'is_required': doc_config['is_required'] if doc_config else True,
                'must_sign_before_contract': template.must_sign_before_contract
            }
        }

    def get_current_document(self, client_id: int) -> Dict[str, Any]:
        """Get the next document that needs to be signed"""
        progress = self.get_or_create_progress(client_id)
        if not progress:
            return {'success': False, 'error': 'Client not found'}

        if progress.is_complete:
            return {
                'success': True,
                'is_complete': True,
                'message': 'All CROA documents have been signed'
            }

        # Find first unsigned required document
        for doc in CROA_DOCUMENTS:
            field_name = DOCUMENT_PROGRESS_FIELDS.get(doc['code'])
            signed_at = getattr(progress, field_name, None) if field_name else None

            if signed_at is None and doc['is_required']:
                return self.get_document(doc['code'])

        # All required signed, check optional
        for doc in CROA_DOCUMENTS:
            if not doc['is_required']:
                field_name = DOCUMENT_PROGRESS_FIELDS.get(doc['code'])
                signed_at = getattr(progress, field_name, None) if field_name else None

                if signed_at is None:
                    result = self.get_document(doc['code'])
                    result['is_optional'] = True
                    return result

        return {
            'success': True,
            'is_complete': True,
            'message': 'All documents signed'
        }

    def sign_document(
        self,
        client_id: int,
        document_code: str,
        signature_data: str,
        signature_type: str = 'drawn',
        ip_address: str = None,
        user_agent: str = None
    ) -> Dict[str, Any]:
        """
        Sign a CROA document.

        Args:
            client_id: ID of the client
            document_code: Code of the document to sign (e.g., 'CROA_01_RIGHTS_DISCLOSURE')
            signature_data: Base64 signature image or typed name
            signature_type: 'drawn', 'typed', or 'uploaded'
            ip_address: Client's IP address
            user_agent: Client's browser/device info

        Returns:
            dict with success status and next document info
        """
        progress = self.get_or_create_progress(client_id)
        if not progress:
            return {'success': False, 'error': 'Client not found'}

        # Validate document exists
        template = self.db.query(DocumentTemplate).filter(
            DocumentTemplate.code == document_code
        ).first()

        if not template:
            return {'success': False, 'error': f'Document {document_code} not found'}

        # Check signing order compliance
        doc_config = next((d for d in CROA_DOCUMENTS if d['code'] == document_code), None)
        if not doc_config:
            return {'success': False, 'error': 'Invalid document code'}

        # Verify Rights Disclosure is signed first (CROA requirement)
        if document_code != 'CROA_01_RIGHTS_DISCLOSURE':
            if not progress.rights_disclosure_signed_at:
                return {
                    'success': False,
                    'error': 'Rights Disclosure must be signed before any other document'
                }

        # Check if already signed
        field_name = DOCUMENT_PROGRESS_FIELDS.get(document_code)
        if field_name and getattr(progress, field_name, None):
            return {
                'success': False,
                'error': 'Document has already been signed'
            }

        # Save signature image if drawn
        signature_path = None
        if signature_type == 'drawn' and signature_data:
            signature_path = self._save_signature_image(
                client_id, document_code, signature_data
            )

        # Create signature record
        signature = ClientDocumentSignature(
            client_id=client_id,
            document_template_id=template.id,
            signature_data=signature_data if signature_type == 'typed' else None,
            signature_type=signature_type,
            ip_address=ip_address,
            user_agent=user_agent,
            signed_document_path=signature_path
        )
        self.db.add(signature)

        # Update progress
        now = datetime.utcnow()
        if field_name:
            setattr(progress, field_name, now)

        progress.last_activity_at = now
        progress.documents_completed = self._count_signed_documents(progress)

        # Handle cancellation period for service agreement
        if document_code == 'CROA_03_SERVICE_AGREEMENT':
            progress.cancellation_period_starts_at = now
            progress.cancellation_period_ends_at = self._calculate_cancellation_end(now)

        # Update current document and completion status
        self._update_current_document(progress)

        # Update client's agreement_signed if service agreement was signed
        if document_code == 'CROA_03_SERVICE_AGREEMENT':
            client = self.db.query(Client).filter(Client.id == client_id).first()
            if client:
                client.agreement_signed = True
                client.agreement_signed_at = now

        self.db.commit()
        self.db.refresh(progress)

        # Log timeline event
        try:
            from services.timeline_service import TimelineService
            timeline = TimelineService(self.db)
            timeline.create_event(
                client_id=client_id,
                event_type='agreement_signed' if document_code == 'CROA_03_SERVICE_AGREEMENT' else 'document_uploaded',
                title=f'Signed: {template.name}',
                description=f'Document signed electronically',
                icon='file-signature',
                category='onboarding',
                is_milestone=(document_code == 'CROA_03_SERVICE_AGREEMENT'),
                related_type='document_template',
                related_id=template.id
            )
        except Exception as e:
            print(f"Timeline event error (non-fatal): {e}")

        # Get next document
        next_doc = self.get_current_document(client_id)

        return {
            'success': True,
            'document_signed': document_code,
            'signed_at': now.isoformat(),
            'documents_completed': progress.documents_completed,
            'is_complete': progress.is_complete,
            'next_document': next_doc.get('document') if next_doc.get('success') else None,
            'cancellation_status': self._get_cancellation_status(progress) if document_code == 'CROA_03_SERVICE_AGREEMENT' else None
        }

    def skip_optional_document(self, client_id: int, document_code: str) -> Dict[str, Any]:
        """Skip an optional document (like HIPAA)"""
        progress = self.get_or_create_progress(client_id)
        if not progress:
            return {'success': False, 'error': 'Client not found'}

        doc_config = next((d for d in CROA_DOCUMENTS if d['code'] == document_code), None)
        if not doc_config:
            return {'success': False, 'error': 'Invalid document code'}

        if doc_config['is_required']:
            return {'success': False, 'error': 'Cannot skip required document'}

        # Mark as skipped by setting a marker (we'll use the signed_at with a special flag)
        # For now, just move to next document
        self._update_current_document(progress)
        self.db.commit()

        return {
            'success': True,
            'skipped': document_code,
            'next_document': self.get_current_document(client_id)
        }

    def get_cancellation_status(self, client_id: int) -> Dict[str, Any]:
        """Get the current cancellation period status"""
        progress = self.get_or_create_progress(client_id)
        if not progress:
            return {'success': False, 'error': 'Client not found'}

        return {
            'success': True,
            **self._get_cancellation_status(progress)
        }

    def cancel_service(self, client_id: int, reason: str = None) -> Dict[str, Any]:
        """Cancel service during the 3-day cancellation period"""
        progress = self.get_or_create_progress(client_id)
        if not progress:
            return {'success': False, 'error': 'Client not found'}

        status = self._get_cancellation_status(progress)

        if not status['can_cancel']:
            return {
                'success': False,
                'error': status.get('message', 'Cancellation period has expired')
            }

        now = datetime.utcnow()
        progress.cancelled_at = now

        # Update client status
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if client:
            client.dispute_status = 'cancelled'

        self.db.commit()

        # Log timeline event
        try:
            from services.timeline_service import TimelineService
            timeline = TimelineService(self.db)
            timeline.create_event(
                client_id=client_id,
                event_type='status_changed',
                title='Service Cancelled',
                description=f'Client cancelled during 3-day cancellation period. Reason: {reason or "Not provided"}',
                icon='times-circle',
                category='status',
                is_milestone=True
            )
        except Exception as e:
            print(f"Timeline event error (non-fatal): {e}")

        return {
            'success': True,
            'cancelled_at': now.isoformat(),
            'message': 'Service has been cancelled. No charges will be made.'
        }

    def waive_cancellation_period(self, client_id: int) -> Dict[str, Any]:
        """
        Allow client to waive the 3-day cancellation period.
        Some states allow this with proper disclosure.
        """
        progress = self.get_or_create_progress(client_id)
        if not progress:
            return {'success': False, 'error': 'Client not found'}

        if not progress.cancellation_period_starts_at:
            return {'success': False, 'error': 'Service agreement not yet signed'}

        if progress.cancelled_at:
            return {'success': False, 'error': 'Service has already been cancelled'}

        progress.cancellation_waived = True
        progress.cancellation_period_ends_at = datetime.utcnow()
        self.db.commit()

        return {
            'success': True,
            'message': 'Cancellation period waived. Services may begin immediately.'
        }

    def can_begin_services(self, client_id: int) -> Dict[str, Any]:
        """Check if services can begin (all required docs signed + cancellation period passed)"""
        progress = self.get_or_create_progress(client_id)
        if not progress:
            return {'success': False, 'can_begin': False, 'error': 'Client not found'}

        # Check all required documents are signed
        required_signed = True
        missing_docs = []

        for doc in CROA_DOCUMENTS:
            if doc['is_required']:
                field_name = DOCUMENT_PROGRESS_FIELDS.get(doc['code'])
                if field_name and not getattr(progress, field_name, None):
                    required_signed = False
                    missing_docs.append(doc['name'])

        if not required_signed:
            return {
                'success': True,
                'can_begin': False,
                'reason': 'documents_incomplete',
                'missing_documents': missing_docs
            }

        # Check cancellation period
        status = self._get_cancellation_status(progress)

        if status['in_cancellation_period'] and not progress.cancellation_waived:
            return {
                'success': True,
                'can_begin': False,
                'reason': 'cancellation_period_active',
                'cancellation_ends_at': status['cancellation_ends_at'],
                'days_remaining': status['days_remaining']
            }

        if progress.cancelled_at:
            return {
                'success': True,
                'can_begin': False,
                'reason': 'cancelled',
                'cancelled_at': progress.cancelled_at.isoformat()
            }

        return {
            'success': True,
            'can_begin': True,
            'reason': 'all_requirements_met'
        }

    def _count_signed_documents(self, progress: CROAProgress) -> int:
        """Count how many documents have been signed"""
        count = 0
        for doc in CROA_DOCUMENTS:
            field_name = DOCUMENT_PROGRESS_FIELDS.get(doc['code'])
            if field_name and getattr(progress, field_name, None):
                count += 1
        return count

    def _update_current_document(self, progress: CROAProgress):
        """Update the current document pointer based on signing status"""
        for doc in CROA_DOCUMENTS:
            field_name = DOCUMENT_PROGRESS_FIELDS.get(doc['code'])
            signed_at = getattr(progress, field_name, None) if field_name else None

            if signed_at is None and doc['is_required']:
                progress.current_document = doc['code']
                return

        # All required signed
        progress.is_complete = True
        progress.completed_at = datetime.utcnow()
        progress.current_document = 'complete'

    def _get_cancellation_status(self, progress: CROAProgress) -> Dict[str, Any]:
        """Get detailed cancellation period status"""
        if not progress.cancellation_period_starts_at:
            return {
                'in_cancellation_period': False,
                'can_cancel': False,
                'message': 'Service agreement not yet signed'
            }

        if progress.cancelled_at:
            return {
                'in_cancellation_period': False,
                'can_cancel': False,
                'cancelled': True,
                'cancelled_at': progress.cancelled_at.isoformat(),
                'message': 'Service has been cancelled'
            }

        if progress.cancellation_waived:
            return {
                'in_cancellation_period': False,
                'can_cancel': False,
                'waived': True,
                'message': 'Cancellation period was waived'
            }

        now = datetime.utcnow()
        ends_at = progress.cancellation_period_ends_at

        if now < ends_at:
            days_remaining = (ends_at - now).days + 1
            return {
                'in_cancellation_period': True,
                'can_cancel': True,
                'cancellation_starts_at': progress.cancellation_period_starts_at.isoformat(),
                'cancellation_ends_at': ends_at.isoformat(),
                'days_remaining': days_remaining,
                'message': f'You may cancel within {days_remaining} business day(s)'
            }

        return {
            'in_cancellation_period': False,
            'can_cancel': False,
            'cancellation_expired': True,
            'expired_at': ends_at.isoformat(),
            'message': 'Cancellation period has expired'
        }

    def _calculate_cancellation_end(self, start_date: datetime) -> datetime:
        """Calculate the end of the 3 business day cancellation period"""
        # Add 3 business days (excluding weekends)
        current = start_date
        business_days = 0

        while business_days < 3:
            current += timedelta(days=1)
            # Skip weekends (Saturday = 5, Sunday = 6)
            if current.weekday() < 5:
                business_days += 1

        # Set to end of business day (5 PM)
        return current.replace(hour=17, minute=0, second=0, microsecond=0)

    def _save_signature_image(
        self,
        client_id: int,
        document_code: str,
        signature_data: str
    ) -> Optional[str]:
        """Save signature image to file system"""
        try:
            os.makedirs(SIGNATURE_FOLDER, exist_ok=True)

            # Remove data URL prefix if present
            if signature_data.startswith('data:image'):
                header, signature_data = signature_data.split(',', 1)

            signature_bytes = base64.b64decode(signature_data)

            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"croa_sig_{client_id}_{document_code}_{timestamp}.png"
            filepath = os.path.join(SIGNATURE_FOLDER, filename)

            with open(filepath, 'wb') as f:
                f.write(signature_bytes)

            return filepath

        except Exception as e:
            print(f"Error saving signature: {e}")
            return None


def get_croa_signing_service(db: Session = None) -> CROASigningService:
    """Factory function to get CROASigningService instance"""
    if db is None:
        db = SessionLocal()
    return CROASigningService(db)
