"""
Affiliate Service for Brightpath Ascend FCRA Platform

Manages affiliates, referrals, commissions, and payouts.
Supports two-level affiliate structure with parent/sub-affiliate relationships.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import Affiliate, AffiliatePayout, Client, Commission, SessionLocal

# Affiliate status options
AFFILIATE_STATUSES = {
    "pending": "Pending Approval",
    "active": "Active",
    "suspended": "Suspended",
    "inactive": "Inactive",
}

# Commission trigger types
COMMISSION_TRIGGERS = {
    "signup": "Client Signup",
    "payment": "Payment Received",
    "subscription": "Subscription Started",
    "milestone": "Milestone Reached",
}

# Payout methods
PAYOUT_METHODS = {
    "paypal": "PayPal",
    "bank_transfer": "Bank Transfer",
    "check": "Check",
    "venmo": "Venmo",
    "zelle": "Zelle",
}

# Payout statuses
PAYOUT_STATUSES = {
    "pending": "Pending",
    "processing": "Processing",
    "completed": "Completed",
    "failed": "Failed",
}


def generate_affiliate_code(name: str) -> str:
    """Generate a unique affiliate code based on name"""
    prefix = "".join(c for c in name.upper() if c.isalpha())[:3]
    if len(prefix) < 3:
        prefix = prefix.ljust(3, "X")
    suffix = uuid.uuid4().hex[:5].upper()
    return f"{prefix}{suffix}"


class AffiliateService:
    """Service for managing affiliates and commissions"""

    @staticmethod
    def create_affiliate(
        name: str,
        email: str,
        phone: str = None,
        company_name: str = None,
        affiliate_code: str = None,
        parent_affiliate_id: int = None,
        commission_rate_1: float = 0.10,
        commission_rate_2: float = 0.05,
        payout_method: str = None,
        payout_details: dict = None,
        session=None,
    ) -> Dict[str, Any]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            existing = session.query(Affiliate).filter(Affiliate.email == email).first()
            if existing:
                return {
                    "success": False,
                    "error": f"Affiliate with email '{email}' already exists",
                }

            if not affiliate_code:
                affiliate_code = generate_affiliate_code(name)

            code_exists = (
                session.query(Affiliate)
                .filter(Affiliate.affiliate_code == affiliate_code)
                .first()
            )
            if code_exists:
                affiliate_code = generate_affiliate_code(name)

            if parent_affiliate_id:
                parent = (
                    session.query(Affiliate)
                    .filter(Affiliate.id == parent_affiliate_id)
                    .first()
                )
                if not parent:
                    return {"success": False, "error": "Parent affiliate not found"}

            affiliate = Affiliate(
                name=name,
                email=email,
                phone=phone,
                company_name=company_name,
                affiliate_code=affiliate_code,
                parent_affiliate_id=parent_affiliate_id,
                commission_rate_1=commission_rate_1,
                commission_rate_2=commission_rate_2,
                status="pending",
                payout_method=payout_method,
                payout_details=payout_details or {},
            )

            session.add(affiliate)
            session.commit()
            session.refresh(affiliate)

            return {
                "success": True,
                "affiliate_id": affiliate.id,
                "affiliate_code": affiliate.affiliate_code,
                "message": f"Affiliate '{name}' created successfully",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def update_affiliate(
        affiliate_id: int,
        name: str = None,
        phone: str = None,
        company_name: str = None,
        commission_rate_1: float = None,
        commission_rate_2: float = None,
        status: str = None,
        payout_method: str = None,
        payout_details: dict = None,
        session=None,
    ) -> Dict[str, Any]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            affiliate = (
                session.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
            )
            if not affiliate:
                return {"success": False, "error": "Affiliate not found"}

            if name is not None:
                affiliate.name = name
            if phone is not None:
                affiliate.phone = phone
            if company_name is not None:
                affiliate.company_name = company_name
            if commission_rate_1 is not None:
                affiliate.commission_rate_1 = commission_rate_1
            if commission_rate_2 is not None:
                affiliate.commission_rate_2 = commission_rate_2
            if status is not None:
                affiliate.status = status
            if payout_method is not None:
                affiliate.payout_method = payout_method
            if payout_details is not None:
                affiliate.payout_details = payout_details

            affiliate.updated_at = datetime.utcnow()
            session.commit()
            return {
                "success": True,
                "message": f"Affiliate '{affiliate.name}' updated successfully",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_affiliate(
        affiliate_id: int = None,
        affiliate_code: str = None,
        email: str = None,
        session=None,
    ) -> Optional[Dict[str, Any]]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            query = session.query(Affiliate)
            if affiliate_id:
                affiliate = query.filter(Affiliate.id == affiliate_id).first()
            elif affiliate_code:
                affiliate = query.filter(
                    Affiliate.affiliate_code == affiliate_code
                ).first()
            elif email:
                affiliate = query.filter(Affiliate.email == email).first()
            else:
                return None

            if not affiliate:
                return None

            sub_count = (
                session.query(Affiliate)
                .filter(Affiliate.parent_affiliate_id == affiliate.id)
                .count()
            )

            return {
                "id": affiliate.id,
                "name": affiliate.name,
                "email": affiliate.email,
                "phone": affiliate.phone,
                "company_name": affiliate.company_name,
                "affiliate_code": affiliate.affiliate_code,
                "parent_affiliate_id": affiliate.parent_affiliate_id,
                "commission_rate_1": affiliate.commission_rate_1,
                "commission_rate_2": affiliate.commission_rate_2,
                "status": affiliate.status,
                "status_label": AFFILIATE_STATUSES.get(
                    affiliate.status, affiliate.status
                ),
                "payout_method": affiliate.payout_method,
                "payout_details": affiliate.payout_details,
                "total_referrals": affiliate.total_referrals,
                "total_earnings": affiliate.total_earnings,
                "pending_earnings": affiliate.pending_earnings,
                "paid_out": affiliate.paid_out,
                "sub_affiliates_count": sub_count,
                "created_at": (
                    affiliate.created_at.isoformat() if affiliate.created_at else None
                ),
                "updated_at": (
                    affiliate.updated_at.isoformat() if affiliate.updated_at else None
                ),
            }
        finally:
            if close_session:
                session.close()

    @staticmethod
    def list_affiliates(
        status: str = None,
        parent_id: int = None,
        search: str = None,
        include_stats: bool = True,
        session=None,
    ) -> List[Dict[str, Any]]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            query = session.query(Affiliate)
            if status:
                query = query.filter(Affiliate.status == status)
            if parent_id is not None:
                if parent_id == 0:
                    query = query.filter(Affiliate.parent_affiliate_id == None)
                else:
                    query = query.filter(Affiliate.parent_affiliate_id == parent_id)
            if search:
                pattern = f"%{search}%"
                query = query.filter(
                    (Affiliate.name.ilike(pattern))
                    | (Affiliate.email.ilike(pattern))
                    | (Affiliate.company_name.ilike(pattern))
                    | (Affiliate.affiliate_code.ilike(pattern))
                )

            affiliates = query.order_by(Affiliate.created_at.desc()).all()
            results = []
            for a in affiliates:
                data = {
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
                    "status_label": AFFILIATE_STATUSES.get(a.status, a.status),
                    "total_referrals": a.total_referrals,
                    "total_earnings": a.total_earnings,
                    "pending_earnings": a.pending_earnings,
                    "paid_out": a.paid_out,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                if include_stats:
                    data["sub_affiliates_count"] = (
                        session.query(Affiliate)
                        .filter(Affiliate.parent_affiliate_id == a.id)
                        .count()
                    )
                results.append(data)
            return results
        finally:
            if close_session:
                session.close()

    @staticmethod
    def delete_affiliate(affiliate_id: int, session=None) -> Dict[str, Any]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            affiliate = (
                session.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
            )
            if not affiliate:
                return {"success": False, "error": "Affiliate not found"}
            if affiliate.total_referrals > 0:
                return {
                    "success": False,
                    "error": "Cannot delete affiliate with existing referrals",
                }
            sub_count = (
                session.query(Affiliate)
                .filter(Affiliate.parent_affiliate_id == affiliate_id)
                .count()
            )
            if sub_count > 0:
                return {
                    "success": False,
                    "error": "Cannot delete affiliate with sub-affiliates",
                }

            name = affiliate.name
            session.delete(affiliate)
            session.commit()
            return {"success": True, "message": f"Affiliate '{name}' deleted"}

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def record_referral(
        affiliate_code: str,
        client_id: int,
        trigger_type: str = "signup",
        trigger_amount: float = 0.0,
        session=None,
    ) -> Dict[str, Any]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            affiliate = (
                session.query(Affiliate)
                .filter(Affiliate.affiliate_code == affiliate_code)
                .first()
            )
            if not affiliate:
                return {"success": False, "error": "Affiliate code not found"}
            if affiliate.status != "active":
                return {"success": False, "error": "Affiliate is not active"}

            client = session.query(Client).filter(Client.id == client_id).first()
            if not client:
                return {"success": False, "error": "Client not found"}

            commissions_created = []
            rate_1 = affiliate.commission_rate_1
            amount_1 = trigger_amount * rate_1

            commission_1 = Commission(
                affiliate_id=affiliate.id,
                client_id=client_id,
                level=1,
                trigger_type=trigger_type,
                trigger_amount=trigger_amount,
                commission_rate=rate_1,
                commission_amount=amount_1,
                status="pending",
            )
            session.add(commission_1)
            affiliate.total_referrals += 1
            affiliate.pending_earnings += amount_1
            affiliate.total_earnings += amount_1
            commissions_created.append(
                {"affiliate_id": affiliate.id, "level": 1, "amount": amount_1}
            )

            if affiliate.parent_affiliate_id:
                parent = (
                    session.query(Affiliate)
                    .filter(Affiliate.id == affiliate.parent_affiliate_id)
                    .first()
                )
                if parent and parent.status == "active":
                    rate_2 = parent.commission_rate_2
                    amount_2 = trigger_amount * rate_2
                    commission_2 = Commission(
                        affiliate_id=parent.id,
                        client_id=client_id,
                        level=2,
                        trigger_type=trigger_type,
                        trigger_amount=trigger_amount,
                        commission_rate=rate_2,
                        commission_amount=amount_2,
                        status="pending",
                    )
                    session.add(commission_2)
                    parent.pending_earnings += amount_2
                    parent.total_earnings += amount_2
                    commissions_created.append(
                        {"affiliate_id": parent.id, "level": 2, "amount": amount_2}
                    )

            session.commit()
            return {
                "success": True,
                "affiliate_id": affiliate.id,
                "commissions": commissions_created,
                "message": f"Referral recorded, {len(commissions_created)} commission(s) created",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_commissions(
        affiliate_id: int = None,
        client_id: int = None,
        status: str = None,
        trigger_type: str = None,
        session=None,
    ) -> List[Dict[str, Any]]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            query = session.query(Commission)
            if affiliate_id:
                query = query.filter(Commission.affiliate_id == affiliate_id)
            if client_id:
                query = query.filter(Commission.client_id == client_id)
            if status:
                query = query.filter(Commission.status == status)
            if trigger_type:
                query = query.filter(Commission.trigger_type == trigger_type)

            commissions = query.order_by(Commission.created_at.desc()).all()
            return [
                {
                    "id": c.id,
                    "affiliate_id": c.affiliate_id,
                    "client_id": c.client_id,
                    "level": c.level,
                    "trigger_type": c.trigger_type,
                    "trigger_type_label": COMMISSION_TRIGGERS.get(
                        c.trigger_type, c.trigger_type
                    ),
                    "trigger_amount": c.trigger_amount,
                    "commission_rate": c.commission_rate,
                    "commission_amount": c.commission_amount,
                    "status": c.status,
                    "paid_at": c.paid_at.isoformat() if c.paid_at else None,
                    "payout_id": c.payout_id,
                    "notes": c.notes,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in commissions
            ]
        finally:
            if close_session:
                session.close()

    @staticmethod
    def create_payout(
        affiliate_id: int,
        amount: float,
        payout_method: str = None,
        payout_reference: str = None,
        commission_ids: List[int] = None,
        notes: str = None,
        processed_by_id: int = None,
        session=None,
    ) -> Dict[str, Any]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            affiliate = (
                session.query(Affiliate).filter(Affiliate.id == affiliate_id).first()
            )
            if not affiliate:
                return {"success": False, "error": "Affiliate not found"}
            if amount > affiliate.pending_earnings:
                return {
                    "success": False,
                    "error": f"Amount exceeds pending earnings (${affiliate.pending_earnings:.2f})",
                }

            payout = AffiliatePayout(
                affiliate_id=affiliate_id,
                amount=amount,
                payout_method=payout_method or affiliate.payout_method,
                payout_reference=payout_reference,
                status="pending",
                commission_ids=commission_ids or [],
                notes=notes,
                processed_by_id=processed_by_id,
            )
            session.add(payout)
            session.commit()
            session.refresh(payout)
            return {
                "success": True,
                "payout_id": payout.id,
                "message": f"Payout of ${amount:.2f} created for {affiliate.name}",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def process_payout(
        payout_id: int,
        payout_reference: str = None,
        processed_by_id: int = None,
        session=None,
    ) -> Dict[str, Any]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            payout = (
                session.query(AffiliatePayout)
                .filter(AffiliatePayout.id == payout_id)
                .first()
            )
            if not payout:
                return {"success": False, "error": "Payout not found"}
            if payout.status == "completed":
                return {"success": False, "error": "Payout already completed"}

            affiliate = (
                session.query(Affiliate)
                .filter(Affiliate.id == payout.affiliate_id)
                .first()
            )
            if not affiliate:
                return {"success": False, "error": "Affiliate not found"}

            payout.status = "completed"
            payout.processed_at = datetime.utcnow()
            if payout_reference:
                payout.payout_reference = payout_reference
            if processed_by_id:
                payout.processed_by_id = processed_by_id

            affiliate.pending_earnings -= payout.amount
            affiliate.paid_out += payout.amount

            if payout.commission_ids:
                for cid in payout.commission_ids:
                    commission = (
                        session.query(Commission).filter(Commission.id == cid).first()
                    )
                    if commission:
                        commission.status = "paid"
                        commission.paid_at = datetime.utcnow()
                        commission.payout_id = payout.id

            session.commit()
            return {
                "success": True,
                "message": f"Payout of ${payout.amount:.2f} processed successfully",
            }

        except Exception as e:
            session.rollback()
            return {"success": False, "error": str(e)}
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_payouts(
        affiliate_id: int = None, status: str = None, session=None
    ) -> List[Dict[str, Any]]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            query = session.query(AffiliatePayout)
            if affiliate_id:
                query = query.filter(AffiliatePayout.affiliate_id == affiliate_id)
            if status:
                query = query.filter(AffiliatePayout.status == status)

            payouts = query.order_by(AffiliatePayout.created_at.desc()).all()
            return [
                {
                    "id": p.id,
                    "affiliate_id": p.affiliate_id,
                    "amount": p.amount,
                    "payout_method": p.payout_method,
                    "payout_method_label": PAYOUT_METHODS.get(
                        p.payout_method, p.payout_method
                    ),
                    "payout_reference": p.payout_reference,
                    "status": p.status,
                    "status_label": PAYOUT_STATUSES.get(p.status, p.status),
                    "commission_ids": p.commission_ids,
                    "notes": p.notes,
                    "processed_by_id": p.processed_by_id,
                    "processed_at": (
                        p.processed_at.isoformat() if p.processed_at else None
                    ),
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in payouts
            ]
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_affiliate_stats(affiliate_id: int = None, session=None) -> Dict[str, Any]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            if affiliate_id:
                affiliate = (
                    session.query(Affiliate)
                    .filter(Affiliate.id == affiliate_id)
                    .first()
                )
                if not affiliate:
                    return {"error": "Affiliate not found"}

                commissions = (
                    session.query(Commission)
                    .filter(Commission.affiliate_id == affiliate_id)
                    .all()
                )
                pending = sum(
                    c.commission_amount for c in commissions if c.status == "pending"
                )
                paid = sum(
                    c.commission_amount for c in commissions if c.status == "paid"
                )

                sub_affiliates = (
                    session.query(Affiliate)
                    .filter(Affiliate.parent_affiliate_id == affiliate_id)
                    .all()
                )

                return {
                    "affiliate_id": affiliate_id,
                    "total_referrals": affiliate.total_referrals,
                    "total_earnings": affiliate.total_earnings,
                    "pending_earnings": pending,
                    "paid_out": paid,
                    "commission_count": len(commissions),
                    "pending_commission_count": len(
                        [c for c in commissions if c.status == "pending"]
                    ),
                    "sub_affiliates": [
                        {
                            "id": s.id,
                            "name": s.name,
                            "total_referrals": s.total_referrals,
                            "total_earnings": s.total_earnings,
                        }
                        for s in sub_affiliates
                    ],
                }
            else:
                total = session.query(Affiliate).count()
                active = (
                    session.query(Affiliate)
                    .filter(Affiliate.status == "active")
                    .count()
                )
                pending_aff = (
                    session.query(Affiliate)
                    .filter(Affiliate.status == "pending")
                    .count()
                )
                total_comm = session.query(Commission).count()
                pending_comm = (
                    session.query(Commission)
                    .filter(Commission.status == "pending")
                    .count()
                )

                all_affiliates = session.query(Affiliate).all()
                total_earnings = sum(a.total_earnings for a in all_affiliates)
                total_pending = sum(a.pending_earnings for a in all_affiliates)
                total_paid = sum(a.paid_out for a in all_affiliates)
                total_referrals = sum(a.total_referrals for a in all_affiliates)

                return {
                    "total_affiliates": total,
                    "active_affiliates": active,
                    "pending_affiliates": pending_aff,
                    "total_commissions": total_comm,
                    "pending_commissions": pending_comm,
                    "total_referrals": total_referrals,
                    "total_earnings": total_earnings,
                    "total_pending": total_pending,
                    "total_paid": total_paid,
                }
        finally:
            if close_session:
                session.close()

    @staticmethod
    def get_dashboard_data(session=None) -> Dict[str, Any]:
        close_session = False
        if session is None:
            session = SessionLocal()
            close_session = True

        try:
            stats = AffiliateService.get_affiliate_stats(session=session)
            top_affiliates = (
                session.query(Affiliate)
                .filter(Affiliate.status == "active")
                .order_by(Affiliate.total_referrals.desc())
                .limit(5)
                .all()
            )
            recent_payouts = (
                session.query(AffiliatePayout)
                .order_by(AffiliatePayout.created_at.desc())
                .limit(5)
                .all()
            )
            pending_count = (
                session.query(AffiliatePayout)
                .filter(AffiliatePayout.status == "pending")
                .count()
            )

            return {
                "stats": stats,
                "top_affiliates": [
                    {
                        "id": a.id,
                        "name": a.name,
                        "affiliate_code": a.affiliate_code,
                        "total_referrals": a.total_referrals,
                        "total_earnings": a.total_earnings,
                    }
                    for a in top_affiliates
                ],
                "recent_payouts": [
                    {
                        "id": p.id,
                        "affiliate_id": p.affiliate_id,
                        "amount": p.amount,
                        "status": p.status,
                        "created_at": (
                            p.created_at.isoformat() if p.created_at else None
                        ),
                    }
                    for p in recent_payouts
                ],
                "pending_payout_count": pending_count,
            }
        finally:
            if close_session:
                session.close()


def get_affiliate_by_code(code: str) -> Optional[Dict]:
    return AffiliateService.get_affiliate(affiliate_code=code)


def record_client_referral(
    affiliate_code: str, client_id: int, amount: float = 0
) -> Dict:
    return AffiliateService.record_referral(
        affiliate_code=affiliate_code,
        client_id=client_id,
        trigger_type="signup",
        trigger_amount=amount,
    )
