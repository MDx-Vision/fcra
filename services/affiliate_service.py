"""
Affiliate Commission Service - Two-Level Commission System

Handles affiliate referral tracking, commission calculations, and payout processing.
"""

import random
import string
from datetime import datetime

from database import Affiliate, Client, Commission, get_db


def generate_affiliate_code(name: str = None) -> str:
    """Generate a unique affiliate code"""
    if name:
        prefix = "".join(c.upper() for c in name[:3] if c.isalpha())
        if len(prefix) < 3:
            prefix = prefix + "X" * (3 - len(prefix))
    else:
        prefix = "".join(random.choices(string.ascii_uppercase, k=3))

    suffix = "".join(random.choices(string.digits, k=5))
    code = f"{prefix}{suffix}"

    session = get_db()
    try:
        existing = (
            session.query(Affiliate).filter(Affiliate.affiliate_code == code).first()
        )
        if existing:
            return generate_affiliate_code(name)
        return code
    finally:
        session.close()


def validate_affiliate_code(code: str) -> dict:
    """Validate if an affiliate code exists and is active"""
    if not code:
        return {"valid": False, "message": "No code provided"}

    session = get_db()
    try:
        affiliate = (
            session.query(Affiliate)
            .filter(Affiliate.affiliate_code == code.upper().strip())
            .first()
        )

        if not affiliate:
            return {"valid": False, "message": "Invalid affiliate code"}

        if affiliate.status != "active":
            return {"valid": False, "message": "Affiliate is not currently active"}

        return {
            "valid": True,
            "affiliate_id": affiliate.id,
            "affiliate_name": affiliate.name,
            "message": "Valid affiliate code",
        }
    finally:
        session.close()


def process_referral(client_id: int, affiliate_code: str) -> dict:
    """Link a client to an affiliate via referral code"""
    if not affiliate_code:
        return {"success": False, "message": "No affiliate code provided"}

    session = get_db()
    try:
        affiliate = (
            session.query(Affiliate)
            .filter(
                Affiliate.affiliate_code == affiliate_code.upper().strip(),
                Affiliate.status == "active",
            )
            .first()
        )

        if not affiliate:
            return {"success": False, "message": "Invalid or inactive affiliate code"}

        client = session.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {"success": False, "message": "Client not found"}

        if client.referred_by_affiliate_id:
            return {
                "success": False,
                "message": "Client already has an affiliate referral",
            }

        client.referred_by_affiliate_id = affiliate.id

        affiliate.total_referrals = (affiliate.total_referrals or 0) + 1

        session.commit()

        return {
            "success": True,
            "affiliate_id": affiliate.id,
            "affiliate_name": affiliate.name,
            "message": f"Client linked to affiliate {affiliate.name}",
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error processing referral: {str(e)}"}
    finally:
        session.close()


def calculate_commission(client_id: int, trigger_type: str, amount: float) -> dict:
    """
    Calculate and create commission records for two-level affiliate system.

    Two-level logic:
    - Level 1 (Direct): Affiliate who directly referred the client gets commission_rate_1 (default 10%)
    - Level 2 (Parent): Parent of the referring affiliate gets commission_rate_2 (default 5%)
    """
    if not amount or amount <= 0:
        return {"success": False, "message": "Invalid amount"}

    session = get_db()
    try:
        client = session.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {"success": False, "message": "Client not found"}

        if not client.referred_by_affiliate_id:
            return {"success": False, "message": "Client has no affiliate referral"}

        affiliate = (
            session.query(Affiliate)
            .filter(Affiliate.id == client.referred_by_affiliate_id)
            .first()
        )

        if not affiliate:
            return {"success": False, "message": "Referring affiliate not found"}

        if affiliate.status != "active":
            return {"success": False, "message": "Referring affiliate is not active"}

        commissions_created = []

        level_1_rate = affiliate.commission_rate_1 or 0.10
        level_1_amount = round(amount * level_1_rate, 2)

        commission_1 = Commission(
            affiliate_id=affiliate.id,
            client_id=client_id,
            level=1,
            trigger_type=trigger_type,
            trigger_amount=amount,
            commission_rate=level_1_rate,
            commission_amount=level_1_amount,
            status="pending",
            notes=f"Level 1 commission from {trigger_type}: ${amount:.2f} x {level_1_rate*100:.0f}%",
        )
        session.add(commission_1)

        affiliate.total_earnings = (affiliate.total_earnings or 0) + level_1_amount
        affiliate.pending_earnings = (affiliate.pending_earnings or 0) + level_1_amount

        commissions_created.append(
            {
                "level": 1,
                "affiliate_id": affiliate.id,
                "affiliate_name": affiliate.name,
                "rate": level_1_rate,
                "amount": level_1_amount,
            }
        )

        if affiliate.parent_affiliate_id:
            parent = (
                session.query(Affiliate)
                .filter(
                    Affiliate.id == affiliate.parent_affiliate_id,
                    Affiliate.status == "active",
                )
                .first()
            )

            if parent:
                level_2_rate = parent.commission_rate_2 or 0.05
                level_2_amount = round(amount * level_2_rate, 2)

                commission_2 = Commission(
                    affiliate_id=parent.id,
                    client_id=client_id,
                    level=2,
                    trigger_type=trigger_type,
                    trigger_amount=amount,
                    commission_rate=level_2_rate,
                    commission_amount=level_2_amount,
                    status="pending",
                    notes=f"Level 2 commission via {affiliate.name} from {trigger_type}: ${amount:.2f} x {level_2_rate*100:.0f}%",
                )
                session.add(commission_2)

                parent.total_earnings = (parent.total_earnings or 0) + level_2_amount
                parent.pending_earnings = (
                    parent.pending_earnings or 0
                ) + level_2_amount

                commissions_created.append(
                    {
                        "level": 2,
                        "affiliate_id": parent.id,
                        "affiliate_name": parent.name,
                        "rate": level_2_rate,
                        "amount": level_2_amount,
                    }
                )

        session.commit()

        return {
            "success": True,
            "message": f"Created {len(commissions_created)} commission record(s)",
            "commissions": commissions_created,
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error calculating commission: {str(e)}"}
    finally:
        session.close()


def get_affiliate_stats(affiliate_id: int) -> dict:
    """Get comprehensive performance metrics for an affiliate"""
    session = get_db()
    try:
        affiliate = (
            session.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
        )
        if not affiliate:
            return {"success": False, "message": "Affiliate not found"}

        referred_clients = (
            session.query(Client)
            .filter(Client.referred_by_affiliate_id == affiliate_id)
            .all()
        )

        converted_clients = [c for c in referred_clients if c.payment_status == "paid"]
        conversion_rate = (
            (len(converted_clients) / len(referred_clients) * 100)
            if referred_clients
            else 0
        )

        level_1_commissions = (
            session.query(Commission)
            .filter(Commission.affiliate_id == affiliate_id, Commission.level == 1)
            .all()
        )

        level_2_commissions = (
            session.query(Commission)
            .filter(Commission.affiliate_id == affiliate_id, Commission.level == 2)
            .all()
        )

        pending_commissions = (
            session.query(Commission)
            .filter(
                Commission.affiliate_id == affiliate_id, Commission.status == "pending"
            )
            .all()
        )

        paid_commissions = (
            session.query(Commission)
            .filter(
                Commission.affiliate_id == affiliate_id, Commission.status == "paid"
            )
            .all()
        )

        sub_affiliates = (
            session.query(Affiliate)
            .filter(Affiliate.parent_affiliate_id == affiliate_id)
            .all()
        )

        return {
            "success": True,
            "affiliate_id": affiliate_id,
            "affiliate_name": affiliate.name,
            "affiliate_code": affiliate.affiliate_code,
            "status": affiliate.status,
            "total_referrals": affiliate.total_referrals or 0,
            "converted_referrals": len(converted_clients),
            "conversion_rate": round(conversion_rate, 1),
            "level_1_count": len(level_1_commissions),
            "level_1_earnings": sum(c.commission_amount for c in level_1_commissions),
            "level_2_count": len(level_2_commissions),
            "level_2_earnings": sum(c.commission_amount for c in level_2_commissions),
            "total_earnings": affiliate.total_earnings or 0,
            "pending_earnings": affiliate.pending_earnings or 0,
            "paid_out": affiliate.paid_out or 0,
            "pending_commissions": len(pending_commissions),
            "paid_commissions": len(paid_commissions),
            "sub_affiliates": len(sub_affiliates),
            "parent_affiliate_id": affiliate.parent_affiliate_id,
            "commission_rate_1": affiliate.commission_rate_1 or 0.10,
            "commission_rate_2": affiliate.commission_rate_2 or 0.05,
            "payout_method": affiliate.payout_method,
            "created_at": (
                affiliate.created_at.isoformat() if affiliate.created_at else None
            ),
        }
    finally:
        session.close()


def process_payout(
    affiliate_id: int, amount: float, payout_method: str = None, notes: str = None
) -> dict:
    """Process a payout to an affiliate, marking commissions as paid"""
    if not amount or amount <= 0:
        return {"success": False, "message": "Invalid payout amount"}

    session = get_db()
    try:
        affiliate = (
            session.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
        )
        if not affiliate:
            return {"success": False, "message": "Affiliate not found"}

        if (affiliate.pending_earnings or 0) < amount:
            return {
                "success": False,
                "message": f"Insufficient pending earnings. Available: ${affiliate.pending_earnings:.2f}",
            }

        payout_id = int(datetime.utcnow().timestamp())

        pending_commissions = (
            session.query(Commission)
            .filter(
                Commission.affiliate_id == affiliate_id, Commission.status == "pending"
            )
            .order_by(Commission.created_at)
            .all()
        )

        remaining = amount
        commissions_paid = 0

        for commission in pending_commissions:
            if remaining <= 0:
                break

            if commission.commission_amount <= remaining:
                commission.status = "paid"
                commission.paid_at = datetime.utcnow()
                commission.payout_id = payout_id
                if notes:
                    commission.notes = (commission.notes or "") + f" | Payout: {notes}"

                remaining -= commission.commission_amount
                commissions_paid += 1

        affiliate.pending_earnings = (affiliate.pending_earnings or 0) - amount
        affiliate.paid_out = (affiliate.paid_out or 0) + amount

        session.commit()

        return {
            "success": True,
            "message": f"Payout of ${amount:.2f} processed successfully",
            "payout_id": payout_id,
            "commissions_paid": commissions_paid,
            "remaining_pending": affiliate.pending_earnings,
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error processing payout: {str(e)}"}
    finally:
        session.close()


def get_commission_history(affiliate_id: int, limit: int = 50) -> list:
    """Get commission history for an affiliate"""
    session = get_db()
    try:
        commissions = (
            session.query(Commission)
            .filter(Commission.affiliate_id == affiliate_id)
            .order_by(Commission.created_at.desc())
            .limit(limit)
            .all()
        )

        result = []
        for c in commissions:
            client = session.query(Client).filter(Client.id == c.client_id).first()
            client_name = (
                f"{client.first_name or ''} {client.last_name or ''}".strip()
                if client
                else "Unknown"
            )

            result.append(
                {
                    "id": c.id,
                    "client_id": c.client_id,
                    "client_name": client_name,
                    "level": c.level,
                    "trigger_type": c.trigger_type,
                    "trigger_amount": c.trigger_amount,
                    "commission_rate": c.commission_rate,
                    "commission_amount": c.commission_amount,
                    "status": c.status,
                    "paid_at": c.paid_at.isoformat() if c.paid_at else None,
                    "payout_id": c.payout_id,
                    "notes": c.notes,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
            )

        return result
    finally:
        session.close()


def get_referral_tree(affiliate_id: int) -> dict:
    """Get the referral tree for an affiliate (sub-affiliates and their stats)"""
    session = get_db()
    try:
        affiliate = (
            session.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
        )
        if not affiliate:
            return {"success": False, "message": "Affiliate not found"}

        sub_affiliates = (
            session.query(Affiliate)
            .filter(Affiliate.parent_affiliate_id == affiliate_id)
            .all()
        )

        tree = {
            "affiliate_id": affiliate.id,
            "name": affiliate.name,
            "affiliate_code": affiliate.affiliate_code,
            "total_referrals": affiliate.total_referrals or 0,
            "total_earnings": affiliate.total_earnings or 0,
            "children": [],
        }

        for sub in sub_affiliates:
            tree["children"].append(
                {
                    "affiliate_id": sub.id,
                    "name": sub.name,
                    "affiliate_code": sub.affiliate_code,
                    "total_referrals": sub.total_referrals or 0,
                    "total_earnings": sub.total_earnings or 0,
                    "status": sub.status,
                    "created_at": (
                        sub.created_at.isoformat() if sub.created_at else None
                    ),
                }
            )

        return {"success": True, "tree": tree}
    finally:
        session.close()


def create_affiliate(
    name: str,
    email: str,
    phone: str = None,
    company_name: str = None,
    parent_affiliate_id: int = None,
    commission_rate_1: float = 0.10,
    commission_rate_2: float = 0.05,
    payout_method: str = None,
    payout_details: dict = None,
    status: str = "pending",
) -> dict:
    """Create a new affiliate"""
    session = get_db()
    try:
        existing = (
            session.query(Affiliate)
            .filter(Affiliate.email == email.lower().strip())
            .first()
        )
        if existing:
            return {
                "success": False,
                "message": "An affiliate with this email already exists",
            }

        affiliate_code = generate_affiliate_code(name)

        if parent_affiliate_id:
            parent = (
                session.query(Affiliate)
                .filter(Affiliate.id == parent_affiliate_id)
                .first()
            )
            if not parent:
                return {"success": False, "message": "Parent affiliate not found"}

        affiliate = Affiliate(
            name=name.strip(),
            email=email.lower().strip(),
            phone=phone,
            company_name=company_name,
            affiliate_code=affiliate_code,
            parent_affiliate_id=parent_affiliate_id,
            commission_rate_1=commission_rate_1,
            commission_rate_2=commission_rate_2,
            payout_method=payout_method,
            payout_details=payout_details,
            status=status,
            total_referrals=0,
            total_earnings=0.0,
            pending_earnings=0.0,
            paid_out=0.0,
        )

        session.add(affiliate)
        session.commit()

        return {
            "success": True,
            "message": "Affiliate created successfully",
            "affiliate_id": affiliate.id,
            "affiliate_code": affiliate.affiliate_code,
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error creating affiliate: {str(e)}"}
    finally:
        session.close()


def update_affiliate(affiliate_id: int, **kwargs) -> dict:
    """Update affiliate information"""
    session = get_db()
    try:
        affiliate = (
            session.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
        )
        if not affiliate:
            return {"success": False, "message": "Affiliate not found"}

        allowed_fields = [
            "name",
            "email",
            "phone",
            "company_name",
            "parent_affiliate_id",
            "commission_rate_1",
            "commission_rate_2",
            "status",
            "payout_method",
            "payout_details",
        ]

        for key, value in kwargs.items():
            if key in allowed_fields and value is not None:
                setattr(affiliate, key, value)

        affiliate.updated_at = datetime.utcnow()
        session.commit()

        return {
            "success": True,
            "message": "Affiliate updated successfully",
            "affiliate_id": affiliate.id,
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "message": f"Error updating affiliate: {str(e)}"}
    finally:
        session.close()


def get_all_affiliates(status: str = None, limit: int = 100) -> list:
    """Get all affiliates with optional status filter"""
    session = get_db()
    try:
        query = session.query(Affiliate)

        if status:
            query = query.filter(Affiliate.status == status)

        affiliates = query.order_by(Affiliate.created_at.desc()).limit(limit).all()

        result = []
        for a in affiliates:
            referred_clients = (
                session.query(Client)
                .filter(Client.referred_by_affiliate_id == a.id)
                .count()
            )

            result.append(
                {
                    "id": a.id,
                    "name": a.name,
                    "email": a.email,
                    "phone": a.phone,
                    "company_name": a.company_name,
                    "affiliate_code": a.affiliate_code,
                    "parent_affiliate_id": a.parent_affiliate_id,
                    "commission_rate_1": a.commission_rate_1,
                    "commission_rate_2": a.commission_rate_2,
                    "status": a.status,
                    "payout_method": a.payout_method,
                    "total_referrals": a.total_referrals or 0,
                    "actual_referrals": referred_clients,
                    "total_earnings": a.total_earnings or 0,
                    "pending_earnings": a.pending_earnings or 0,
                    "paid_out": a.paid_out or 0,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
            )

        return result
    finally:
        session.close()


def get_affiliate_by_id(affiliate_id: int) -> dict:
    """Get a single affiliate by ID"""
    session = get_db()
    try:
        affiliate = (
            session.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
        )
        if not affiliate:
            return None

        parent = None
        if affiliate.parent_affiliate_id:
            parent_affiliate = (
                session.query(Affiliate)
                .filter(Affiliate.id == affiliate.parent_affiliate_id)
                .first()
            )
            if parent_affiliate:
                parent = {
                    "id": parent_affiliate.id,
                    "name": parent_affiliate.name,
                    "affiliate_code": parent_affiliate.affiliate_code,
                }

        return {
            "id": affiliate.id,
            "user_id": affiliate.user_id,
            "name": affiliate.name,
            "email": affiliate.email,
            "phone": affiliate.phone,
            "company_name": affiliate.company_name,
            "affiliate_code": affiliate.affiliate_code,
            "parent_affiliate_id": affiliate.parent_affiliate_id,
            "parent": parent,
            "commission_rate_1": affiliate.commission_rate_1,
            "commission_rate_2": affiliate.commission_rate_2,
            "status": affiliate.status,
            "payout_method": affiliate.payout_method,
            "payout_details": affiliate.payout_details,
            "total_referrals": affiliate.total_referrals or 0,
            "total_earnings": affiliate.total_earnings or 0,
            "pending_earnings": affiliate.pending_earnings or 0,
            "paid_out": affiliate.paid_out or 0,
            "created_at": (
                affiliate.created_at.isoformat() if affiliate.created_at else None
            ),
            "updated_at": (
                affiliate.updated_at.isoformat() if affiliate.updated_at else None
            ),
        }
    finally:
        session.close()


def apply_for_affiliate(
    name: str,
    email: str,
    phone: str = None,
    company_name: str = None,
    payout_method: str = None,
    payout_details: dict = None,
    referrer_code: str = None,
) -> dict:
    """Public endpoint for affiliate application"""
    parent_affiliate_id = None

    if referrer_code:
        session = get_db()
        try:
            parent = (
                session.query(Affiliate)
                .filter(
                    Affiliate.affiliate_code == referrer_code.upper().strip(),
                    Affiliate.status == "active",
                )
                .first()
            )
            if parent:
                parent_affiliate_id = parent.id
        finally:
            session.close()

    return create_affiliate(
        name=name,
        email=email,
        phone=phone,
        company_name=company_name,
        parent_affiliate_id=parent_affiliate_id,
        payout_method=payout_method,
        payout_details=payout_details,
        status="pending",
    )


def get_dashboard_stats() -> dict:
    """Get summary stats for the affiliate dashboard"""
    session = get_db()
    try:
        total_affiliates = session.query(Affiliate).count()
        active_affiliates = (
            session.query(Affiliate).filter(Affiliate.status == "active").count()
        )
        pending_affiliates = (
            session.query(Affiliate).filter(Affiliate.status == "pending").count()
        )

        all_affiliates = session.query(Affiliate).all()
        total_pending_payouts = sum(a.pending_earnings or 0 for a in all_affiliates)
        total_paid = sum(a.paid_out or 0 for a in all_affiliates)
        total_earnings = sum(a.total_earnings or 0 for a in all_affiliates)

        total_referrals = (
            session.query(Client)
            .filter(Client.referred_by_affiliate_id.isnot(None))
            .count()
        )

        pending_commissions = (
            session.query(Commission).filter(Commission.status == "pending").count()
        )

        return {
            "total_affiliates": total_affiliates,
            "active_affiliates": active_affiliates,
            "pending_affiliates": pending_affiliates,
            "total_referrals": total_referrals,
            "total_pending_payouts": total_pending_payouts,
            "total_paid": total_paid,
            "total_earnings": total_earnings,
            "pending_commissions": pending_commissions,
        }
    finally:
        session.close()
