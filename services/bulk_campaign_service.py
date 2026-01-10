"""
Bulk Campaign Service - One-time email/SMS blasts to multiple clients

Features:
- Create campaigns with email/SMS content
- Target clients by status, tags, or manual selection
- Schedule or send immediately
- Track delivery and engagement
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from database import (
    BulkCampaign, BulkCampaignRecipient, Client, ClientTag,
    EmailTemplate, SMSTemplate, get_db
)
from services.email_service import send_email
from services.sms_service import send_sms


def create_campaign(
    name: str,
    channel: str,
    created_by_staff_id: int,
    description: str = None,
    email_template_id: int = None,
    sms_template_id: int = None,
    email_subject: str = None,
    email_content: str = None,
    sms_content: str = None,
    target_type: str = 'manual',
    target_filters: Dict = None,
    scheduled_at: datetime = None
) -> Dict[str, Any]:
    """Create a new bulk campaign"""
    db = get_db()

    # Validate channel
    if channel not in ['email', 'sms', 'both']:
        return {'success': False, 'error': 'Invalid channel. Use email, sms, or both'}

    # Validate content
    if channel in ['email', 'both']:
        if not email_template_id and not email_content:
            return {'success': False, 'error': 'Email content or template required for email campaigns'}

    if channel in ['sms', 'both']:
        if not sms_template_id and not sms_content:
            return {'success': False, 'error': 'SMS content or template required for SMS campaigns'}

    try:
        campaign = BulkCampaign(
            name=name,
            description=description,
            channel=channel,
            email_template_id=email_template_id,
            sms_template_id=sms_template_id,
            email_subject=email_subject,
            email_content=email_content,
            sms_content=sms_content,
            target_type=target_type,
            target_filters=target_filters or {},
            status='draft' if scheduled_at else 'draft',
            scheduled_at=scheduled_at,
            created_by_staff_id=created_by_staff_id
        )
        db.add(campaign)
        db.commit()
        db.refresh(campaign)

        return {'success': True, 'campaign': campaign.to_dict()}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_campaign(campaign_id: int) -> Optional[Dict[str, Any]]:
    """Get campaign by ID"""
    db = get_db()
    campaign = db.query(BulkCampaign).filter(BulkCampaign.id == campaign_id).first()
    if campaign:
        return campaign.to_dict()
    return None


def list_campaigns(
    status: str = None,
    channel: str = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List campaigns with optional filters"""
    db = get_db()
    query = db.query(BulkCampaign)

    if status:
        query = query.filter(BulkCampaign.status == status)
    if channel:
        query = query.filter(BulkCampaign.channel == channel)

    total = query.count()
    campaigns = query.order_by(BulkCampaign.created_at.desc()).offset(offset).limit(limit).all()

    return {
        'campaigns': [c.to_dict() for c in campaigns],
        'total': total,
        'limit': limit,
        'offset': offset
    }


def add_recipients(campaign_id: int, client_ids: List[int]) -> Dict[str, Any]:
    """Add recipients to a campaign manually"""
    db = get_db()
    campaign = db.query(BulkCampaign).filter(BulkCampaign.id == campaign_id).first()

    if not campaign:
        return {'success': False, 'error': 'Campaign not found'}

    if campaign.status not in ['draft', 'scheduled']:
        return {'success': False, 'error': 'Cannot add recipients to campaign in progress'}

    added = 0
    skipped = 0

    try:
        for client_id in client_ids:
            # Check if already added
            existing = db.query(BulkCampaignRecipient).filter(
                BulkCampaignRecipient.campaign_id == campaign_id,
                BulkCampaignRecipient.client_id == client_id
            ).first()

            if existing:
                skipped += 1
                continue

            recipient = BulkCampaignRecipient(
                campaign_id=campaign_id,
                client_id=client_id,
                email_status='pending' if campaign.channel in ['email', 'both'] else None,
                sms_status='pending' if campaign.channel in ['sms', 'both'] else None
            )
            db.add(recipient)
            added += 1

        # Update total count
        campaign.total_recipients = db.query(BulkCampaignRecipient).filter(
            BulkCampaignRecipient.campaign_id == campaign_id
        ).count()

        db.commit()
        return {'success': True, 'added': added, 'skipped': skipped, 'total': campaign.total_recipients}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def add_recipients_by_filter(campaign_id: int, filters: Dict) -> Dict[str, Any]:
    """Add recipients based on filter criteria"""
    db = get_db()
    campaign = db.query(BulkCampaign).filter(BulkCampaign.id == campaign_id).first()

    if not campaign:
        return {'success': False, 'error': 'Campaign not found'}

    # Build query based on filters
    query = db.query(Client)

    # Status filter
    if filters.get('status'):
        statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
        query = query.filter(Client.dispute_status.in_(statuses))

    # Tag filter
    if filters.get('tags'):
        tag_ids = filters['tags']
        query = query.join(ClientTag).filter(ClientTag.tag_id.in_(tag_ids))

    # Opt-in filters
    if campaign.channel in ['email', 'both']:
        query = query.filter(Client.email_opt_in == True)
    if campaign.channel in ['sms', 'both']:
        query = query.filter(Client.sms_opt_in == True)

    # Get client IDs
    client_ids = [c.id for c in query.all()]

    return add_recipients(campaign_id, client_ids)


def remove_recipient(campaign_id: int, client_id: int) -> Dict[str, Any]:
    """Remove a recipient from a campaign"""
    db = get_db()
    recipient = db.query(BulkCampaignRecipient).filter(
        BulkCampaignRecipient.campaign_id == campaign_id,
        BulkCampaignRecipient.client_id == client_id
    ).first()

    if not recipient:
        return {'success': False, 'error': 'Recipient not found'}

    try:
        db.delete(recipient)

        # Update total count
        campaign = db.query(BulkCampaign).filter(BulkCampaign.id == campaign_id).first()
        campaign.total_recipients = db.query(BulkCampaignRecipient).filter(
            BulkCampaignRecipient.campaign_id == campaign_id
        ).count()

        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_recipients(campaign_id: int, status: str = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """Get recipients for a campaign"""
    db = get_db()
    query = db.query(BulkCampaignRecipient).filter(
        BulkCampaignRecipient.campaign_id == campaign_id
    )

    if status:
        query = query.filter(
            or_(
                BulkCampaignRecipient.email_status == status,
                BulkCampaignRecipient.sms_status == status
            )
        )

    total = query.count()
    recipients = query.offset(offset).limit(limit).all()

    # Join with client data
    result = []
    for r in recipients:
        client = db.query(Client).filter(Client.id == r.client_id).first()
        result.append({
            **r.to_dict(),
            'client_name': f"{client.first_name} {client.last_name}" if client else "Unknown",
            'client_email': client.email if client else None,
            'client_phone': client.phone if client else None
        })

    return {
        'recipients': result,
        'total': total,
        'limit': limit,
        'offset': offset
    }


def send_campaign(campaign_id: int) -> Dict[str, Any]:
    """Send a campaign immediately"""
    db = get_db()
    campaign = db.query(BulkCampaign).filter(BulkCampaign.id == campaign_id).first()

    if not campaign:
        return {'success': False, 'error': 'Campaign not found'}

    if campaign.status not in ['draft', 'scheduled']:
        return {'success': False, 'error': f'Cannot send campaign with status: {campaign.status}'}

    if campaign.total_recipients == 0:
        return {'success': False, 'error': 'No recipients in campaign'}

    # Get email template if using one
    email_template = None
    if campaign.email_template_id:
        email_template = db.query(EmailTemplate).filter(
            EmailTemplate.id == campaign.email_template_id
        ).first()

    # Get SMS template if using one
    sms_template = None
    if campaign.sms_template_id:
        sms_template = db.query(SMSTemplate).filter(
            SMSTemplate.id == campaign.sms_template_id
        ).first()

    # Update campaign status
    campaign.status = 'sending'
    campaign.started_at = datetime.utcnow()
    db.commit()

    sent = 0
    failed = 0

    # Process recipients
    recipients = db.query(BulkCampaignRecipient).filter(
        BulkCampaignRecipient.campaign_id == campaign_id
    ).all()

    for recipient in recipients:
        client = db.query(Client).filter(Client.id == recipient.client_id).first()
        if not client:
            continue

        # Prepare personalized content
        variables = {
            'client_name': f"{client.first_name} {client.last_name}",
            'first_name': client.first_name,
            'last_name': client.last_name,
            'email': client.email,
        }

        # Send email
        if campaign.channel in ['email', 'both'] and client.email:
            try:
                subject = campaign.email_subject or (email_template.subject if email_template else 'Message from Brightpath Ascend')
                content = campaign.email_content or (email_template.html_content if email_template else '')

                # Replace variables
                for key, value in variables.items():
                    subject = subject.replace(f'{{{{{key}}}}}', str(value or ''))
                    content = content.replace(f'{{{{{key}}}}}', str(value or ''))

                send_email(
                    to_email=client.email,
                    subject=subject,
                    html_content=content
                )
                recipient.email_status = 'sent'
                recipient.email_sent_at = datetime.utcnow()
                sent += 1
            except Exception as e:
                recipient.email_status = 'failed'
                recipient.email_error = str(e)
                failed += 1

        # Send SMS
        if campaign.channel in ['sms', 'both'] and client.phone and client.sms_opt_in:
            try:
                content = campaign.sms_content or (sms_template.message if sms_template else '')

                # Replace variables
                for key, value in variables.items():
                    content = content.replace(f'{{{{{key}}}}}', str(value or ''))

                send_sms(
                    to_phone=client.phone,
                    message=content
                )
                recipient.sms_status = 'sent'
                recipient.sms_sent_at = datetime.utcnow()
                if campaign.channel == 'sms':
                    sent += 1
            except Exception as e:
                recipient.sms_status = 'failed'
                recipient.sms_error = str(e)
                if campaign.channel == 'sms':
                    failed += 1

        db.commit()

    # Update campaign stats
    campaign.status = 'completed'
    campaign.completed_at = datetime.utcnow()
    campaign.sent_count = sent
    campaign.failed_count = failed
    db.commit()

    return {
        'success': True,
        'sent': sent,
        'failed': failed,
        'total': campaign.total_recipients
    }


def schedule_campaign(campaign_id: int, scheduled_at: datetime) -> Dict[str, Any]:
    """Schedule a campaign for later"""
    db = get_db()
    campaign = db.query(BulkCampaign).filter(BulkCampaign.id == campaign_id).first()

    if not campaign:
        return {'success': False, 'error': 'Campaign not found'}

    if campaign.status not in ['draft']:
        return {'success': False, 'error': 'Can only schedule draft campaigns'}

    try:
        campaign.scheduled_at = scheduled_at
        campaign.status = 'scheduled'
        db.commit()
        return {'success': True, 'scheduled_at': scheduled_at.isoformat()}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def cancel_campaign(campaign_id: int) -> Dict[str, Any]:
    """Cancel a scheduled campaign"""
    db = get_db()
    campaign = db.query(BulkCampaign).filter(BulkCampaign.id == campaign_id).first()

    if not campaign:
        return {'success': False, 'error': 'Campaign not found'}

    if campaign.status not in ['draft', 'scheduled']:
        return {'success': False, 'error': 'Cannot cancel campaign in progress or completed'}

    try:
        campaign.status = 'cancelled'
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def delete_campaign(campaign_id: int) -> Dict[str, Any]:
    """Delete a campaign and its recipients"""
    db = get_db()
    campaign = db.query(BulkCampaign).filter(BulkCampaign.id == campaign_id).first()

    if not campaign:
        return {'success': False, 'error': 'Campaign not found'}

    if campaign.status == 'sending':
        return {'success': False, 'error': 'Cannot delete campaign while sending'}

    try:
        # Delete recipients first
        db.query(BulkCampaignRecipient).filter(
            BulkCampaignRecipient.campaign_id == campaign_id
        ).delete()

        # Delete campaign
        db.delete(campaign)
        db.commit()
        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_campaign_stats(campaign_id: int) -> Dict[str, Any]:
    """Get detailed stats for a campaign"""
    db = get_db()
    campaign = db.query(BulkCampaign).filter(BulkCampaign.id == campaign_id).first()

    if not campaign:
        return {'success': False, 'error': 'Campaign not found'}

    # Get recipient status breakdown
    recipients = db.query(BulkCampaignRecipient).filter(
        BulkCampaignRecipient.campaign_id == campaign_id
    ).all()

    email_stats = {'pending': 0, 'sent': 0, 'delivered': 0, 'opened': 0, 'clicked': 0, 'failed': 0}
    sms_stats = {'pending': 0, 'sent': 0, 'delivered': 0, 'failed': 0}

    for r in recipients:
        if r.email_status:
            email_stats[r.email_status] = email_stats.get(r.email_status, 0) + 1
        if r.sms_status:
            sms_stats[r.sms_status] = sms_stats.get(r.sms_status, 0) + 1

    return {
        'campaign': campaign.to_dict(),
        'email_stats': email_stats if campaign.channel in ['email', 'both'] else None,
        'sms_stats': sms_stats if campaign.channel in ['sms', 'both'] else None
    }


def process_scheduled_campaigns() -> Dict[str, Any]:
    """Process all scheduled campaigns that are due (called by cron)"""
    db = get_db()
    now = datetime.utcnow()

    campaigns = db.query(BulkCampaign).filter(
        BulkCampaign.status == 'scheduled',
        BulkCampaign.scheduled_at <= now
    ).all()

    results = []
    for campaign in campaigns:
        result = send_campaign(campaign.id)
        results.append({
            'campaign_id': campaign.id,
            'name': campaign.name,
            **result
        })

    return {'processed': len(results), 'results': results}
