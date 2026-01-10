"""
Client Testimonial Service - Collect and manage client reviews

Features:
- Request testimonials via email
- Collect ratings and text reviews
- Approval workflow
- Display approved testimonials
"""

import secrets
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import Session

from database import ClientTestimonial, Client, get_db
from services.email_service import send_email
from services.client_success_service import get_client_success_metrics


def create_testimonial_request(client_id: int) -> Dict[str, Any]:
    """Send a testimonial request to a client"""
    db = get_db()
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        return {'success': False, 'error': 'Client not found'}

    # Check if already has pending request
    existing = db.query(ClientTestimonial).filter(
        ClientTestimonial.client_id == client_id,
        ClientTestimonial.status == 'pending'
    ).first()

    if existing:
        return {'success': False, 'error': 'Client already has pending testimonial request'}

    # Get client success metrics
    metrics = get_client_success_metrics(client_id)

    try:
        token = secrets.token_urlsafe(32)
        testimonial = ClientTestimonial(
            client_id=client_id,
            request_token=token,
            request_sent_at=datetime.utcnow(),
            items_deleted=metrics.get('total_deleted', 0) if metrics else 0,
            score_improvement=metrics.get('score_improvement', 0) if metrics else 0,
            display_name=f"{client.first_name} {client.last_name[0]}." if client.last_name else client.first_name
        )
        db.add(testimonial)
        db.commit()
        db.refresh(testimonial)

        # Send email request
        review_url = f"/review/{token}"
        send_email(
            to_email=client.email,
            subject="Share Your Experience with Brightpath Ascend",
            html_content=f"""
            <h2>Hi {client.first_name},</h2>
            <p>Congratulations on your credit repair progress!</p>
            <p>We'd love to hear about your experience with Brightpath Ascend. Your feedback helps others
            who are considering taking control of their credit.</p>
            <p><a href="{review_url}" style="background: #22c55e; color: white; padding: 12px 24px;
            text-decoration: none; border-radius: 6px; display: inline-block;">Leave a Review</a></p>
            <p>It only takes 2 minutes and your review could help someone else start their journey.</p>
            <p>Thank you for trusting us with your credit repair!</p>
            <p>- The Brightpath Ascend Team</p>
            """
        )

        return {'success': True, 'testimonial_id': testimonial.id, 'token': token}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def submit_testimonial(
    token: str,
    rating: int,
    testimonial_text: str,
    video_url: str = None
) -> Dict[str, Any]:
    """Submit a testimonial via the review link"""
    db = get_db()
    testimonial = db.query(ClientTestimonial).filter(
        ClientTestimonial.request_token == token
    ).first()

    if not testimonial:
        return {'success': False, 'error': 'Invalid or expired review link'}

    if testimonial.submitted_at:
        return {'success': False, 'error': 'Review already submitted'}

    # Validate rating
    if not 1 <= rating <= 5:
        return {'success': False, 'error': 'Rating must be between 1 and 5'}

    try:
        testimonial.rating = rating
        testimonial.testimonial_text = testimonial_text
        testimonial.video_url = video_url
        testimonial.submitted_at = datetime.utcnow()
        testimonial.status = 'pending'  # Needs approval
        db.commit()

        return {'success': True, 'testimonial': testimonial.to_dict()}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_testimonial_by_token(token: str) -> Optional[Dict[str, Any]]:
    """Get testimonial by request token (for review page)"""
    db = get_db()
    testimonial = db.query(ClientTestimonial).filter(
        ClientTestimonial.request_token == token
    ).first()

    if not testimonial:
        return None

    client = db.query(Client).filter(Client.id == testimonial.client_id).first()

    return {
        **testimonial.to_dict(),
        'client_first_name': client.first_name if client else None,
        'already_submitted': testimonial.submitted_at is not None
    }


def list_testimonials(
    status: str = None,
    min_rating: int = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List testimonials with filters"""
    db = get_db()
    query = db.query(ClientTestimonial).filter(
        ClientTestimonial.submitted_at.isnot(None)
    )

    if status:
        query = query.filter(ClientTestimonial.status == status)
    if min_rating:
        query = query.filter(ClientTestimonial.rating >= min_rating)

    total = query.count()
    testimonials = query.order_by(desc(ClientTestimonial.submitted_at)).offset(offset).limit(limit).all()

    # Add client info
    result = []
    for t in testimonials:
        client = db.query(Client).filter(Client.id == t.client_id).first()
        result.append({
            **t.to_dict(),
            'client_name': f"{client.first_name} {client.last_name}" if client else "Unknown"
        })

    return {
        'testimonials': result,
        'total': total,
        'limit': limit,
        'offset': offset
    }


def approve_testimonial(
    testimonial_id: int,
    staff_id: int,
    show_on_website: bool = False,
    show_in_portal: bool = True
) -> Dict[str, Any]:
    """Approve a testimonial for display"""
    db = get_db()
    testimonial = db.query(ClientTestimonial).filter(
        ClientTestimonial.id == testimonial_id
    ).first()

    if not testimonial:
        return {'success': False, 'error': 'Testimonial not found'}

    try:
        testimonial.status = 'approved'
        testimonial.approved_by_staff_id = staff_id
        testimonial.approved_at = datetime.utcnow()
        testimonial.show_on_website = show_on_website
        testimonial.show_in_portal = show_in_portal
        db.commit()

        return {'success': True, 'testimonial': testimonial.to_dict()}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def reject_testimonial(testimonial_id: int, staff_id: int) -> Dict[str, Any]:
    """Reject a testimonial"""
    db = get_db()
    testimonial = db.query(ClientTestimonial).filter(
        ClientTestimonial.id == testimonial_id
    ).first()

    if not testimonial:
        return {'success': False, 'error': 'Testimonial not found'}

    try:
        testimonial.status = 'rejected'
        testimonial.approved_by_staff_id = staff_id
        testimonial.approved_at = datetime.utcnow()
        db.commit()

        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def feature_testimonial(testimonial_id: int) -> Dict[str, Any]:
    """Mark a testimonial as featured"""
    db = get_db()
    testimonial = db.query(ClientTestimonial).filter(
        ClientTestimonial.id == testimonial_id
    ).first()

    if not testimonial:
        return {'success': False, 'error': 'Testimonial not found'}

    if testimonial.status != 'approved':
        return {'success': False, 'error': 'Only approved testimonials can be featured'}

    try:
        testimonial.status = 'featured'
        db.commit()

        return {'success': True, 'testimonial': testimonial.to_dict()}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def update_display_name(testimonial_id: int, display_name: str) -> Dict[str, Any]:
    """Update how client name is displayed"""
    db = get_db()
    testimonial = db.query(ClientTestimonial).filter(
        ClientTestimonial.id == testimonial_id
    ).first()

    if not testimonial:
        return {'success': False, 'error': 'Testimonial not found'}

    try:
        testimonial.display_name = display_name
        db.commit()

        return {'success': True}
    except Exception as e:
        db.rollback()
        return {'success': False, 'error': str(e)}


def get_public_testimonials(limit: int = 10, featured_only: bool = False) -> List[Dict[str, Any]]:
    """Get testimonials for public display (website)"""
    db = get_db()
    query = db.query(ClientTestimonial).filter(
        ClientTestimonial.show_on_website == True,
        ClientTestimonial.status.in_(['approved', 'featured'])
    )

    if featured_only:
        query = query.filter(ClientTestimonial.status == 'featured')

    testimonials = query.order_by(
        ClientTestimonial.status.desc(),  # Featured first
        desc(ClientTestimonial.rating),
        desc(ClientTestimonial.submitted_at)
    ).limit(limit).all()

    return [{
        'display_name': t.display_name,
        'rating': t.rating,
        'testimonial_text': t.testimonial_text,
        'items_deleted': t.items_deleted,
        'score_improvement': t.score_improvement,
        'submitted_at': t.submitted_at.isoformat() if t.submitted_at else None
    } for t in testimonials]


def get_portal_testimonials(limit: int = 5) -> List[Dict[str, Any]]:
    """Get testimonials for portal display"""
    db = get_db()
    testimonials = db.query(ClientTestimonial).filter(
        ClientTestimonial.show_in_portal == True,
        ClientTestimonial.status.in_(['approved', 'featured'])
    ).order_by(
        ClientTestimonial.status.desc(),
        desc(ClientTestimonial.rating),
        desc(ClientTestimonial.submitted_at)
    ).limit(limit).all()

    return [{
        'display_name': t.display_name,
        'rating': t.rating,
        'testimonial_text': t.testimonial_text,
        'items_deleted': t.items_deleted,
        'score_improvement': t.score_improvement
    } for t in testimonials]


def get_testimonial_stats() -> Dict[str, Any]:
    """Get overall testimonial statistics"""
    db = get_db()

    total = db.query(ClientTestimonial).filter(
        ClientTestimonial.submitted_at.isnot(None)
    ).count()

    pending = db.query(ClientTestimonial).filter(
        ClientTestimonial.status == 'pending'
    ).count()

    approved = db.query(ClientTestimonial).filter(
        ClientTestimonial.status.in_(['approved', 'featured'])
    ).count()

    # Average rating
    from sqlalchemy import func
    avg_rating = db.query(func.avg(ClientTestimonial.rating)).filter(
        ClientTestimonial.submitted_at.isnot(None)
    ).scalar()

    # Rating distribution
    ratings = {}
    for i in range(1, 6):
        count = db.query(ClientTestimonial).filter(
            ClientTestimonial.rating == i,
            ClientTestimonial.submitted_at.isnot(None)
        ).count()
        ratings[str(i)] = count

    return {
        'total': total,
        'pending': pending,
        'approved': approved,
        'average_rating': round(float(avg_rating), 1) if avg_rating else 0,
        'rating_distribution': ratings
    }


def bulk_request_testimonials(client_ids: List[int]) -> Dict[str, Any]:
    """Send testimonial requests to multiple clients"""
    sent = 0
    failed = 0
    errors = []

    for client_id in client_ids:
        result = create_testimonial_request(client_id)
        if result['success']:
            sent += 1
        else:
            failed += 1
            errors.append({'client_id': client_id, 'error': result['error']})

    return {
        'success': True,
        'sent': sent,
        'failed': failed,
        'errors': errors if failed > 0 else None
    }
