"""
Badge Service - Client gamification and progress badges

Features:
- Award badges for achievements
- Track badge progress
- Display badges in portal
- Notify clients of new badges
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from database import BadgeDefinition, Client, ClientBadge, get_db

# Default badge definitions
DEFAULT_BADGES = [
    {
        "badge_type": "first_login",
        "name": "Getting Started",
        "description": "Logged into the portal for the first time",
        "icon": "🚀",
        "color": "blue",
        "trigger_type": "event",
        "trigger_event": "first_login",
        "sort_order": 1,
    },
    {
        "badge_type": "documents_complete",
        "name": "Paperwork Pro",
        "description": "Uploaded all required identity documents",
        "icon": "📄",
        "color": "green",
        "trigger_type": "event",
        "trigger_event": "documents_complete",
        "sort_order": 2,
    },
    {
        "badge_type": "agreements_signed",
        "name": "Official Client",
        "description": "Signed all CROA agreements",
        "icon": "✍️",
        "color": "purple",
        "trigger_type": "event",
        "trigger_event": "agreements_signed",
        "sort_order": 3,
    },
    {
        "badge_type": "first_deletion",
        "name": "First Victory",
        "description": "Got your first negative item deleted",
        "icon": "🎯",
        "color": "yellow",
        "trigger_type": "threshold",
        "trigger_event": "deletion_confirmed",
        "trigger_threshold": 1,
        "sort_order": 10,
    },
    {
        "badge_type": "five_deletions",
        "name": "On a Roll",
        "description": "Got 5 negative items deleted",
        "icon": "⭐",
        "color": "yellow",
        "trigger_type": "threshold",
        "trigger_event": "deletion_confirmed",
        "trigger_threshold": 5,
        "sort_order": 11,
    },
    {
        "badge_type": "ten_deletions",
        "name": "Double Digits",
        "description": "Got 10 negative items deleted",
        "icon": "🌟",
        "color": "orange",
        "trigger_type": "threshold",
        "trigger_event": "deletion_confirmed",
        "trigger_threshold": 10,
        "sort_order": 12,
    },
    {
        "badge_type": "twenty_deletions",
        "name": "Credit Champion",
        "description": "Got 20 negative items deleted",
        "icon": "🏆",
        "color": "gold",
        "trigger_type": "threshold",
        "trigger_event": "deletion_confirmed",
        "trigger_threshold": 20,
        "sort_order": 13,
    },
    {
        "badge_type": "score_up_25",
        "name": "Score Climber",
        "description": "Improved your credit score by 25+ points",
        "icon": "📈",
        "color": "green",
        "trigger_type": "threshold",
        "trigger_event": "score_improved",
        "trigger_threshold": 25,
        "sort_order": 20,
    },
    {
        "badge_type": "score_up_50",
        "name": "Major Improvement",
        "description": "Improved your credit score by 50+ points",
        "icon": "📊",
        "color": "green",
        "trigger_type": "threshold",
        "trigger_event": "score_improved",
        "trigger_threshold": 50,
        "sort_order": 21,
    },
    {
        "badge_type": "score_up_100",
        "name": "Credit Transformation",
        "description": "Improved your credit score by 100+ points",
        "icon": "🎉",
        "color": "gold",
        "trigger_type": "threshold",
        "trigger_event": "score_improved",
        "trigger_threshold": 100,
        "sort_order": 22,
    },
    {
        "badge_type": "round_1_complete",
        "name": "Round 1 Complete",
        "description": "Finished your first dispute round",
        "icon": "1️⃣",
        "color": "blue",
        "trigger_type": "event",
        "trigger_event": "round_complete",
        "sort_order": 30,
    },
    {
        "badge_type": "round_2_complete",
        "name": "Persistence Pays",
        "description": "Finished your second dispute round",
        "icon": "2️⃣",
        "color": "blue",
        "trigger_type": "event",
        "trigger_event": "round_complete",
        "sort_order": 31,
    },
    {
        "badge_type": "round_3_complete",
        "name": "Going the Distance",
        "description": "Finished your third dispute round",
        "icon": "3️⃣",
        "color": "purple",
        "trigger_type": "event",
        "trigger_event": "round_complete",
        "sort_order": 32,
    },
    {
        "badge_type": "case_complete",
        "name": "Mission Accomplished",
        "description": "Completed your credit repair case",
        "icon": "🏁",
        "color": "gold",
        "trigger_type": "event",
        "trigger_event": "case_complete",
        "sort_order": 40,
    },
    {
        "badge_type": "referred_friend",
        "name": "Sharing is Caring",
        "description": "Referred a friend to Brightpath Ascend",
        "icon": "🤝",
        "color": "teal",
        "trigger_type": "event",
        "trigger_event": "referral_signup",
        "sort_order": 50,
    },
    {
        "badge_type": "left_review",
        "name": "Voice of Experience",
        "description": "Left a testimonial to help others",
        "icon": "💬",
        "color": "pink",
        "trigger_type": "event",
        "trigger_event": "testimonial_submitted",
        "sort_order": 51,
    },
]


def seed_badge_definitions() -> Dict[str, Any]:
    """Create default badge definitions if they don't exist"""
    db = get_db()
    created = 0

    for badge in DEFAULT_BADGES:
        existing = (
            db.query(BadgeDefinition)
            .filter(BadgeDefinition.badge_type == badge["badge_type"])
            .first()
        )

        if not existing:
            definition = BadgeDefinition(**badge)
            db.add(definition)
            created += 1

    db.commit()
    return {"success": True, "created": created}


def get_badge_definitions(active_only: bool = True) -> List[Dict[str, Any]]:
    """Get all badge definitions"""
    db = get_db()
    query = db.query(BadgeDefinition)

    if active_only:
        query = query.filter(BadgeDefinition.is_active == True)

    badges = query.order_by(BadgeDefinition.sort_order).all()
    return [b.to_dict() for b in badges]


def award_badge(
    client_id: int, badge_type: str, achievement_value: int = None
) -> Dict[str, Any]:
    """Award a badge to a client"""
    db = get_db()

    # Check if badge type exists
    definition = (
        db.query(BadgeDefinition)
        .filter(
            BadgeDefinition.badge_type == badge_type, BadgeDefinition.is_active == True
        )
        .first()
    )

    if not definition:
        return {"success": False, "error": f"Badge type not found: {badge_type}"}

    # Check if client already has this badge
    existing = (
        db.query(ClientBadge)
        .filter(
            ClientBadge.client_id == client_id, ClientBadge.badge_type == badge_type
        )
        .first()
    )

    if existing:
        return {
            "success": False,
            "error": "Client already has this badge",
            "already_awarded": True,
        }

    try:
        badge = ClientBadge(
            client_id=client_id,
            badge_type=badge_type,
            achievement_value=achievement_value,
        )
        db.add(badge)
        db.commit()
        db.refresh(badge)

        return {
            "success": True,
            "badge": {
                "badge_type": badge_type,
                "name": definition.name,
                "description": definition.description,
                "icon": definition.icon,
                "color": definition.color,
                "earned_at": badge.earned_at.isoformat(),
            },
        }
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


def get_client_badges(client_id: int) -> List[Dict[str, Any]]:
    """Get all badges earned by a client"""
    db = get_db()
    badges = (
        db.query(ClientBadge)
        .filter(ClientBadge.client_id == client_id)
        .order_by(ClientBadge.earned_at.desc())
        .all()
    )

    result = []
    for badge in badges:
        definition = (
            db.query(BadgeDefinition)
            .filter(BadgeDefinition.badge_type == badge.badge_type)
            .first()
        )

        if definition:
            result.append(
                {
                    "badge_type": badge.badge_type,
                    "name": definition.name,
                    "description": definition.description,
                    "icon": definition.icon,
                    "color": definition.color,
                    "achievement_value": badge.achievement_value,
                    "earned_at": (
                        badge.earned_at.isoformat() if badge.earned_at else None
                    ),
                    "notified": badge.notified,
                }
            )

    return result


def get_unnotified_badges(client_id: int) -> List[Dict[str, Any]]:
    """Get badges that haven't been shown to client yet"""
    db = get_db()
    badges = (
        db.query(ClientBadge)
        .filter(ClientBadge.client_id == client_id, ClientBadge.notified == False)
        .all()
    )

    result = []
    for badge in badges:
        definition = (
            db.query(BadgeDefinition)
            .filter(BadgeDefinition.badge_type == badge.badge_type)
            .first()
        )

        if definition:
            result.append(
                {
                    "badge_type": badge.badge_type,
                    "name": definition.name,
                    "description": definition.description,
                    "icon": definition.icon,
                    "color": definition.color,
                }
            )

    return result


def mark_badges_notified(
    client_id: int, badge_types: List[str] = None
) -> Dict[str, Any]:
    """Mark badges as notified (shown to client)"""
    db = get_db()

    query = db.query(ClientBadge).filter(
        ClientBadge.client_id == client_id, ClientBadge.notified == False
    )

    if badge_types:
        query = query.filter(ClientBadge.badge_type.in_(badge_types))

    try:
        badges = query.all()
        for badge in badges:
            badge.notified = True
            badge.notified_at = datetime.utcnow()
        db.commit()

        return {"success": True, "marked": len(badges)}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


def check_and_award_badges(
    client_id: int, event_type: str, value: int = None
) -> List[Dict[str, Any]]:
    """Check if client qualifies for any badges based on event"""
    db = get_db()
    awarded = []

    # Get badge definitions that match this event
    definitions = (
        db.query(BadgeDefinition)
        .filter(
            BadgeDefinition.is_active == True,
            BadgeDefinition.trigger_event == event_type,
        )
        .all()
    )

    for definition in definitions:
        # Check if already has badge
        existing = (
            db.query(ClientBadge)
            .filter(
                ClientBadge.client_id == client_id,
                ClientBadge.badge_type == definition.badge_type,
            )
            .first()
        )

        if existing:
            continue

        # Check threshold if applicable
        if definition.trigger_type == "threshold":
            if value is None or value < definition.trigger_threshold:
                continue

        # Award the badge
        result = award_badge(client_id, definition.badge_type, value)
        if result["success"]:
            awarded.append(result["badge"])

    return awarded


def get_badge_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    """Get clients with the most badges"""
    db = get_db()

    results = (
        db.query(ClientBadge.client_id, func.count(ClientBadge.id).label("badge_count"))
        .group_by(ClientBadge.client_id)
        .order_by(func.count(ClientBadge.id).desc())
        .limit(limit)
        .all()
    )

    leaderboard = []
    for client_id, badge_count in results:
        client = db.query(Client).filter(Client.id == client_id).first()
        if client:
            leaderboard.append(
                {
                    "client_id": client_id,
                    "display_name": (
                        f"{client.first_name} {client.last_name[0]}."
                        if client.last_name
                        else client.first_name
                    ),
                    "badge_count": badge_count,
                }
            )

    return leaderboard


def get_badge_stats() -> Dict[str, Any]:
    """Get overall badge statistics"""
    db = get_db()

    total_awarded = db.query(ClientBadge).count()
    clients_with_badges = db.query(
        func.count(func.distinct(ClientBadge.client_id))
    ).scalar()

    # Most common badges
    popular = (
        db.query(ClientBadge.badge_type, func.count(ClientBadge.id).label("count"))
        .group_by(ClientBadge.badge_type)
        .order_by(func.count(ClientBadge.id).desc())
        .limit(5)
        .all()
    )

    # Rarest badges
    rare = (
        db.query(ClientBadge.badge_type, func.count(ClientBadge.id).label("count"))
        .group_by(ClientBadge.badge_type)
        .order_by(func.count(ClientBadge.id))
        .limit(5)
        .all()
    )

    return {
        "total_awarded": total_awarded,
        "clients_with_badges": clients_with_badges,
        "most_common": [{"badge_type": b, "count": c} for b, c in popular],
        "rarest": [{"badge_type": b, "count": c} for b, c in rare],
    }


def get_next_badges(client_id: int) -> List[Dict[str, Any]]:
    """Get badges the client is close to earning"""
    db = get_db()
    earned_types = [
        b.badge_type
        for b in db.query(ClientBadge).filter(ClientBadge.client_id == client_id).all()
    ]

    # Get all threshold-based badges not yet earned
    next_badges = []
    definitions = (
        db.query(BadgeDefinition)
        .filter(
            BadgeDefinition.is_active == True,
            BadgeDefinition.trigger_type == "threshold",
            ~BadgeDefinition.badge_type.in_(earned_types) if earned_types else True,
        )
        .order_by(BadgeDefinition.trigger_threshold)
        .limit(3)
        .all()
    )

    for d in definitions:
        next_badges.append(
            {
                "badge_type": d.badge_type,
                "name": d.name,
                "description": d.description,
                "icon": d.icon,
                "threshold": d.trigger_threshold,
                "trigger_event": d.trigger_event,
            }
        )

    return next_badges


def revoke_badge(client_id: int, badge_type: str) -> Dict[str, Any]:
    """Revoke a badge from a client (admin action)"""
    db = get_db()
    badge = (
        db.query(ClientBadge)
        .filter(
            ClientBadge.client_id == client_id, ClientBadge.badge_type == badge_type
        )
        .first()
    )

    if not badge:
        return {"success": False, "error": "Badge not found"}

    try:
        db.delete(badge)
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
