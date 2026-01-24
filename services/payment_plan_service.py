"""
Payment Plan Service
Manage installment payment plans for clients.
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from database import (
    Client,
    PaymentPlan,
    PaymentPlanInstallment,
    PaymentPlanPayment,
    Staff,
    get_db,
)

# Frequency multipliers for calculating installment dates
FREQUENCY_DAYS = {
    "weekly": 7,
    "biweekly": 14,
    "monthly": None,  # Use relativedelta for months
}


class PaymentPlanService:
    """Service for managing payment plans"""

    def __init__(self, db: Session = None):
        self.db = db or get_db()
        self._owns_session = db is None

    def __del__(self):
        if self._owns_session and self.db:
            self.db.close()

    def create_plan(
        self,
        client_id: int,
        total_amount: float,
        num_installments: int = 3,
        down_payment: float = 0,
        start_date: Optional[date] = None,
        frequency: str = "monthly",
        plan_name: Optional[str] = None,
        plan_type: str = "custom",
        payment_method: Optional[str] = None,
        auto_charge: bool = False,
        grace_period_days: int = 5,
        late_fee_amount: float = 0,
        late_fee_percent: float = 0,
        notes: Optional[str] = None,
        staff_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new payment plan with installments.

        Args:
            client_id: Client ID
            total_amount: Total amount to be paid
            num_installments: Number of installments (excluding down payment)
            down_payment: Initial down payment amount
            start_date: When plan starts (default: today)
            frequency: Payment frequency (weekly, biweekly, monthly)
            plan_name: Optional name for the plan
            plan_type: Type of plan (custom, round, prepay, settlement)
            payment_method: Payment method (stripe, manual, check, etc.)
            auto_charge: Whether to auto-charge saved payment method
            grace_period_days: Days before marking late
            late_fee_amount: Fixed late fee amount
            late_fee_percent: Percentage-based late fee
            notes: Optional notes
            staff_id: Staff member creating the plan

        Returns:
            Created plan dictionary
        """
        # Validate client
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {"success": False, "error": "Client not found"}

        if total_amount <= 0:
            return {"success": False, "error": "Total amount must be positive"}

        if num_installments < 1:
            return {"success": False, "error": "Must have at least 1 installment"}

        if down_payment >= total_amount:
            return {
                "success": False,
                "error": "Down payment cannot exceed total amount",
            }

        if frequency not in FREQUENCY_DAYS:
            return {
                "success": False,
                "error": f"Invalid frequency. Use: {list(FREQUENCY_DAYS.keys())}",
            }

        # Calculate installment amount
        remaining_after_down = total_amount - down_payment
        installment_amount = round(remaining_after_down / num_installments, 2)

        # Handle rounding (last installment may differ)
        total_installments = installment_amount * num_installments
        adjustment = round(remaining_after_down - total_installments, 2)

        # Set start date
        if start_date is None:
            start_date = date.today()
        elif isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        # Calculate end date
        end_date = self._calculate_end_date(start_date, num_installments, frequency)

        # Create the plan
        plan = PaymentPlan(
            client_id=client_id,
            created_by_staff_id=staff_id,
            plan_name=plan_name or f"{client.name} - Payment Plan",
            plan_type=plan_type,
            total_amount=total_amount,
            down_payment=down_payment,
            num_installments=num_installments,
            installment_amount=installment_amount,
            installment_frequency=frequency,
            start_date=start_date,
            next_payment_date=(
                start_date
                if down_payment > 0
                else self._get_next_date(start_date, frequency)
            ),
            end_date=end_date,
            amount_paid=0,
            amount_remaining=total_amount,
            installments_completed=0,
            installments_remaining=num_installments + (1 if down_payment > 0 else 0),
            status="pending",
            payment_method=payment_method,
            auto_charge=auto_charge,
            grace_period_days=grace_period_days,
            late_fee_amount=late_fee_amount,
            late_fee_percent=late_fee_percent,
            notes=notes,
        )

        self.db.add(plan)
        self.db.flush()

        # Create installments
        installments = []
        current_date = start_date

        # Down payment (installment 0)
        if down_payment > 0:
            down_installment = PaymentPlanInstallment(
                plan_id=plan.id,
                installment_number=0,
                amount_due=down_payment,
                due_date=start_date,
                status="pending",
            )
            self.db.add(down_installment)
            installments.append(down_installment)
            current_date = self._get_next_date(start_date, frequency)

        # Regular installments
        for i in range(1, num_installments + 1):
            amount = installment_amount
            # Add adjustment to last installment
            if i == num_installments and adjustment != 0:
                amount += adjustment

            installment = PaymentPlanInstallment(
                plan_id=plan.id,
                installment_number=i,
                amount_due=round(amount, 2),
                due_date=current_date,
                status="pending",
            )
            self.db.add(installment)
            installments.append(installment)
            current_date = self._get_next_date(current_date, frequency)

        self.db.commit()
        self.db.refresh(plan)

        return {
            "success": True,
            "plan": plan.to_dict(),
            "installments": [i.to_dict() for i in installments],
        }

    def _get_next_date(self, current_date: date, frequency: str) -> date:
        """Calculate next payment date based on frequency"""
        if frequency == "monthly":
            return current_date + relativedelta(months=1)
        else:
            return current_date + timedelta(days=FREQUENCY_DAYS[frequency])

    def _calculate_end_date(
        self, start_date: date, num_installments: int, frequency: str
    ) -> date:
        """Calculate plan end date"""
        if frequency == "monthly":
            return start_date + relativedelta(months=num_installments)
        else:
            return start_date + timedelta(
                days=FREQUENCY_DAYS[frequency] * num_installments
            )

    def get_plan(self, plan_id: int) -> Optional[Dict[str, Any]]:
        """Get plan with installments"""
        plan = self.db.query(PaymentPlan).filter(PaymentPlan.id == plan_id).first()
        if not plan:
            return None

        installments = (
            self.db.query(PaymentPlanInstallment)
            .filter(PaymentPlanInstallment.plan_id == plan_id)
            .order_by(PaymentPlanInstallment.installment_number)
            .all()
        )

        payments = (
            self.db.query(PaymentPlanPayment)
            .filter(PaymentPlanPayment.plan_id == plan_id)
            .order_by(PaymentPlanPayment.payment_date.desc())
            .all()
        )

        client = self.db.query(Client).filter(Client.id == plan.client_id).first()

        return {
            "plan": plan.to_dict(),
            "client": (
                {"id": client.id, "name": client.name, "email": client.email}
                if client
                else None
            ),
            "installments": [i.to_dict() for i in installments],
            "payments": [p.to_dict() for p in payments],
        }

    def get_client_plans(self, client_id: int) -> List[Dict[str, Any]]:
        """Get all plans for a client"""
        plans = (
            self.db.query(PaymentPlan)
            .filter(PaymentPlan.client_id == client_id)
            .order_by(PaymentPlan.created_at.desc())
            .all()
        )

        result = []
        for plan in plans:
            installments = (
                self.db.query(PaymentPlanInstallment)
                .filter(PaymentPlanInstallment.plan_id == plan.id)
                .order_by(PaymentPlanInstallment.installment_number)
                .all()
            )

            result.append(
                {
                    "plan": plan.to_dict(),
                    "installments": [i.to_dict() for i in installments],
                }
            )

        return result

    def record_payment(
        self,
        plan_id: int,
        amount: float,
        payment_method: str = "manual",
        installment_id: Optional[int] = None,
        reference_number: Optional[str] = None,
        stripe_payment_intent_id: Optional[str] = None,
        staff_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Record a payment against a plan.

        Args:
            plan_id: Payment plan ID
            amount: Amount paid
            payment_method: Method of payment
            installment_id: Specific installment to apply payment to (optional)
            reference_number: Check/transaction reference
            stripe_payment_intent_id: Stripe payment intent ID
            staff_id: Staff member recording payment
            notes: Payment notes

        Returns:
            Payment result dictionary
        """
        plan = self.db.query(PaymentPlan).filter(PaymentPlan.id == plan_id).first()
        if not plan:
            return {"success": False, "error": "Plan not found"}

        if plan.status in ["completed", "cancelled"]:
            return {"success": False, "error": f"Plan is {plan.status}"}

        if amount <= 0:
            return {"success": False, "error": "Amount must be positive"}

        # Create payment record
        payment = PaymentPlanPayment(
            plan_id=plan_id,
            client_id=plan.client_id,
            amount=amount,
            payment_method=payment_method,
            reference_number=reference_number,
            stripe_payment_intent_id=stripe_payment_intent_id,
            received_by_staff_id=staff_id,
            status="completed",
            notes=notes,
        )
        self.db.add(payment)
        self.db.flush()

        # Apply payment to installments
        remaining_amount = amount
        applied_to = []

        if installment_id:
            # Apply to specific installment
            installment = (
                self.db.query(PaymentPlanInstallment)
                .filter(
                    PaymentPlanInstallment.id == installment_id,
                    PaymentPlanInstallment.plan_id == plan_id,
                )
                .first()
            )

            if installment:
                applied, remaining_amount = self._apply_to_installment(
                    installment, remaining_amount, payment.id
                )
                if applied:
                    applied_to.append(installment.to_dict())
        else:
            # Apply to oldest unpaid installments first
            installments = (
                self.db.query(PaymentPlanInstallment)
                .filter(
                    PaymentPlanInstallment.plan_id == plan_id,
                    PaymentPlanInstallment.status.in_(["pending", "partial", "late"]),
                )
                .order_by(PaymentPlanInstallment.due_date)
                .all()
            )

            for installment in installments:
                if remaining_amount <= 0:
                    break

                applied, remaining_amount = self._apply_to_installment(
                    installment, remaining_amount, payment.id
                )
                if applied:
                    applied_to.append(installment.to_dict())

        # Update plan totals
        plan.amount_paid = (plan.amount_paid or 0) + amount
        plan.amount_remaining = plan.total_amount - plan.amount_paid

        # Count completed installments
        completed = (
            self.db.query(func.count(PaymentPlanInstallment.id))
            .filter(
                PaymentPlanInstallment.plan_id == plan_id,
                PaymentPlanInstallment.status == "paid",
            )
            .scalar()
            or 0
        )

        plan.installments_completed = completed
        plan.installments_remaining = (
            plan.num_installments + (1 if plan.down_payment > 0 else 0) - completed
        )

        # Update next payment date
        next_unpaid = (
            self.db.query(PaymentPlanInstallment)
            .filter(
                PaymentPlanInstallment.plan_id == plan_id,
                PaymentPlanInstallment.status.in_(["pending", "partial", "late"]),
            )
            .order_by(PaymentPlanInstallment.due_date)
            .first()
        )

        plan.next_payment_date = next_unpaid.due_date if next_unpaid else None

        # Check if plan is complete
        if plan.amount_remaining <= 0:
            plan.status = "completed"
            plan.completed_at = datetime.utcnow()
        elif plan.status == "pending":
            plan.status = "active"

        self.db.commit()

        return {
            "success": True,
            "payment": payment.to_dict(),
            "applied_to": applied_to,
            "plan": plan.to_dict(),
            "remaining_credit": remaining_amount if remaining_amount > 0 else 0,
        }

    def _apply_to_installment(
        self, installment: PaymentPlanInstallment, amount: float, payment_id: int
    ) -> tuple:
        """Apply payment amount to an installment"""
        amount_needed = installment.amount_due - (installment.amount_paid or 0)

        if amount_needed <= 0:
            return False, amount

        applied = min(amount, amount_needed)
        installment.amount_paid = (installment.amount_paid or 0) + applied
        installment.payment_id = payment_id

        if installment.amount_paid >= installment.amount_due:
            installment.status = "paid"
            installment.paid_date = date.today()
        else:
            installment.status = "partial"

        return True, amount - applied

    def pause_plan(self, plan_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
        """Pause a payment plan"""
        plan = self.db.query(PaymentPlan).filter(PaymentPlan.id == plan_id).first()
        if not plan:
            return {"success": False, "error": "Plan not found"}

        if plan.status in ["completed", "cancelled", "defaulted"]:
            return {"success": False, "error": f"Cannot pause {plan.status} plan"}

        plan.status = "paused"
        plan.paused_at = datetime.utcnow()
        plan.paused_reason = reason

        self.db.commit()

        return {"success": True, "plan": plan.to_dict()}

    def resume_plan(self, plan_id: int) -> Dict[str, Any]:
        """Resume a paused payment plan"""
        plan = self.db.query(PaymentPlan).filter(PaymentPlan.id == plan_id).first()
        if not plan:
            return {"success": False, "error": "Plan not found"}

        if plan.status != "paused":
            return {"success": False, "error": "Plan is not paused"}

        plan.status = "active"
        plan.paused_at = None
        plan.paused_reason = None

        self.db.commit()

        return {"success": True, "plan": plan.to_dict()}

    def cancel_plan(self, plan_id: int, reason: Optional[str] = None) -> Dict[str, Any]:
        """Cancel a payment plan"""
        plan = self.db.query(PaymentPlan).filter(PaymentPlan.id == plan_id).first()
        if not plan:
            return {"success": False, "error": "Plan not found"}

        if plan.status == "completed":
            return {"success": False, "error": "Cannot cancel completed plan"}

        plan.status = "cancelled"
        plan.internal_notes = (
            (plan.internal_notes or "") + f"\nCancelled: {reason}"
            if reason
            else plan.internal_notes
        )

        self.db.commit()

        return {"success": True, "plan": plan.to_dict()}

    def mark_defaulted(
        self, plan_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Mark a plan as defaulted"""
        plan = self.db.query(PaymentPlan).filter(PaymentPlan.id == plan_id).first()
        if not plan:
            return {"success": False, "error": "Plan not found"}

        if plan.status in ["completed", "cancelled"]:
            return {"success": False, "error": f"Cannot default {plan.status} plan"}

        plan.status = "defaulted"
        plan.defaulted_at = datetime.utcnow()
        plan.default_reason = reason

        self.db.commit()

        return {"success": True, "plan": plan.to_dict()}

    def check_late_payments(self) -> Dict[str, Any]:
        """
        Check for late payments and apply late fees.
        Should be run daily by scheduler.
        """
        today = date.today()
        updated_count = 0
        late_fee_applied = 0

        # Find installments that are past due
        pending_installments = (
            self.db.query(PaymentPlanInstallment)
            .filter(
                PaymentPlanInstallment.status.in_(["pending", "partial"]),
                PaymentPlanInstallment.due_date < today,
            )
            .all()
        )

        for installment in pending_installments:
            plan = (
                self.db.query(PaymentPlan)
                .filter(PaymentPlan.id == installment.plan_id)
                .first()
            )

            if not plan or plan.status in [
                "paused",
                "cancelled",
                "completed",
                "defaulted",
            ]:
                continue

            # Check if past grace period
            grace_end = installment.due_date + timedelta(days=plan.grace_period_days)

            if today > grace_end:
                days_late = (today - installment.due_date).days
                installment.is_late = True
                installment.days_late = days_late
                installment.status = "late"

                # Apply late fee if not already applied
                if installment.late_fee_applied == 0:
                    if plan.late_fee_amount > 0:
                        installment.late_fee_applied = plan.late_fee_amount
                        installment.amount_due += plan.late_fee_amount
                        plan.total_amount += plan.late_fee_amount
                        plan.amount_remaining += plan.late_fee_amount
                        late_fee_applied += 1
                    elif plan.late_fee_percent > 0:
                        fee = round(
                            installment.amount_due * (plan.late_fee_percent / 100), 2
                        )
                        installment.late_fee_applied = fee
                        installment.amount_due += fee
                        plan.total_amount += fee
                        plan.amount_remaining += fee
                        late_fee_applied += 1

                updated_count += 1

        self.db.commit()

        return {
            "success": True,
            "updated_count": updated_count,
            "late_fees_applied": late_fee_applied,
        }

    def get_due_soon(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get installments due within specified days"""
        today = date.today()
        end_date = today + timedelta(days=days)

        installments = (
            self.db.query(PaymentPlanInstallment)
            .filter(
                PaymentPlanInstallment.status.in_(["pending", "partial"]),
                PaymentPlanInstallment.due_date >= today,
                PaymentPlanInstallment.due_date <= end_date,
            )
            .order_by(PaymentPlanInstallment.due_date)
            .all()
        )

        result = []
        for inst in installments:
            plan = (
                self.db.query(PaymentPlan)
                .filter(PaymentPlan.id == inst.plan_id)
                .first()
            )
            client = (
                self.db.query(Client).filter(Client.id == plan.client_id).first()
                if plan
                else None
            )

            if plan and plan.status == "active":
                result.append(
                    {
                        "installment": inst.to_dict(),
                        "plan": plan.to_dict(),
                        "client": (
                            {
                                "id": client.id,
                                "name": client.name,
                                "email": client.email,
                            }
                            if client
                            else None
                        ),
                    }
                )

        return result

    def get_overdue(self) -> List[Dict[str, Any]]:
        """Get all overdue installments"""
        today = date.today()

        installments = (
            self.db.query(PaymentPlanInstallment)
            .filter(
                PaymentPlanInstallment.status.in_(["pending", "partial", "late"]),
                PaymentPlanInstallment.due_date < today,
            )
            .order_by(PaymentPlanInstallment.due_date)
            .all()
        )

        result = []
        for inst in installments:
            plan = (
                self.db.query(PaymentPlan)
                .filter(PaymentPlan.id == inst.plan_id)
                .first()
            )
            client = (
                self.db.query(Client).filter(Client.id == plan.client_id).first()
                if plan
                else None
            )

            if plan and plan.status in ["active", "paused"]:
                result.append(
                    {
                        "installment": inst.to_dict(),
                        "plan": plan.to_dict(),
                        "client": (
                            {
                                "id": client.id,
                                "name": client.name,
                                "email": client.email,
                            }
                            if client
                            else None
                        ),
                        "days_overdue": (today - inst.due_date).days,
                    }
                )

        return result

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get dashboard summary of all payment plans"""
        # Count by status
        status_counts = dict(
            self.db.query(PaymentPlan.status, func.count(PaymentPlan.id))
            .group_by(PaymentPlan.status)
            .all()
        )

        # Total amounts
        totals = (
            self.db.query(
                func.sum(PaymentPlan.total_amount),
                func.sum(PaymentPlan.amount_paid),
                func.sum(PaymentPlan.amount_remaining),
            )
            .filter(PaymentPlan.status.in_(["active", "pending", "paused"]))
            .first()
        )

        # Overdue count
        today = date.today()
        overdue_count = (
            self.db.query(func.count(PaymentPlanInstallment.id))
            .filter(
                PaymentPlanInstallment.status.in_(["pending", "partial", "late"]),
                PaymentPlanInstallment.due_date < today,
            )
            .scalar()
            or 0
        )

        # Due this week
        due_this_week = (
            self.db.query(func.count(PaymentPlanInstallment.id))
            .filter(
                PaymentPlanInstallment.status.in_(["pending", "partial"]),
                PaymentPlanInstallment.due_date >= today,
                PaymentPlanInstallment.due_date <= today + timedelta(days=7),
            )
            .scalar()
            or 0
        )

        # Recent plans
        recent_plans = (
            self.db.query(PaymentPlan)
            .order_by(PaymentPlan.created_at.desc())
            .limit(10)
            .all()
        )

        recent_with_clients = []
        for plan in recent_plans:
            client = self.db.query(Client).filter(Client.id == plan.client_id).first()
            data = plan.to_dict()
            data["client_name"] = client.name if client else "Unknown"
            recent_with_clients.append(data)

        return {
            "status_counts": {
                "active": status_counts.get("active", 0),
                "pending": status_counts.get("pending", 0),
                "paused": status_counts.get("paused", 0),
                "completed": status_counts.get("completed", 0),
                "defaulted": status_counts.get("defaulted", 0),
                "cancelled": status_counts.get("cancelled", 0),
            },
            "totals": {
                "total_amount": round(totals[0] or 0, 2),
                "amount_paid": round(totals[1] or 0, 2),
                "amount_remaining": round(totals[2] or 0, 2),
            },
            "overdue_count": overdue_count,
            "due_this_week": due_this_week,
            "recent_plans": recent_with_clients,
        }

    def list_plans(
        self,
        status: Optional[str] = None,
        client_id: Optional[int] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List payment plans with filtering"""
        query = self.db.query(PaymentPlan)

        if status:
            query = query.filter(PaymentPlan.status == status)
        if client_id:
            query = query.filter(PaymentPlan.client_id == client_id)

        total = query.count()
        plans = (
            query.order_by(PaymentPlan.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        result = []
        for plan in plans:
            client = self.db.query(Client).filter(Client.id == plan.client_id).first()
            data = plan.to_dict()
            data["client_name"] = client.name if client else "Unknown"
            data["client_email"] = client.email if client else None
            result.append(data)

        return {
            "plans": result,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    def update_plan(self, plan_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update plan details (limited fields)"""
        plan = self.db.query(PaymentPlan).filter(PaymentPlan.id == plan_id).first()
        if not plan:
            return {"success": False, "error": "Plan not found"}

        allowed_fields = [
            "plan_name",
            "payment_method",
            "auto_charge",
            "grace_period_days",
            "late_fee_amount",
            "late_fee_percent",
            "notes",
            "internal_notes",
        ]

        for field in allowed_fields:
            if field in updates:
                setattr(plan, field, updates[field])

        self.db.commit()
        self.db.refresh(plan)

        return {"success": True, "plan": plan.to_dict()}

    def waive_installment(
        self, installment_id: int, reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Waive an installment (mark as paid without payment)"""
        installment = (
            self.db.query(PaymentPlanInstallment)
            .filter(PaymentPlanInstallment.id == installment_id)
            .first()
        )

        if not installment:
            return {"success": False, "error": "Installment not found"}

        plan = (
            self.db.query(PaymentPlan)
            .filter(PaymentPlan.id == installment.plan_id)
            .first()
        )
        if not plan:
            return {"success": False, "error": "Plan not found"}

        # Mark as waived
        installment.status = "waived"
        installment.notes = reason or "Waived by staff"
        installment.paid_date = date.today()

        # Update plan totals
        plan.amount_remaining -= installment.amount_due
        plan.installments_completed += 1
        plan.installments_remaining -= 1

        # Check if plan is complete
        if plan.installments_remaining <= 0:
            plan.status = "completed"
            plan.completed_at = datetime.utcnow()

        self.db.commit()

        return {
            "success": True,
            "installment": installment.to_dict(),
            "plan": plan.to_dict(),
        }

    def export_plans(
        self,
        status: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Export plans data for CSV"""
        query = self.db.query(PaymentPlan)

        if status:
            query = query.filter(PaymentPlan.status == status)
        if start_date:
            query = query.filter(PaymentPlan.created_at >= start_date)
        if end_date:
            query = query.filter(PaymentPlan.created_at <= end_date)

        plans = query.order_by(PaymentPlan.created_at.desc()).all()

        result = []
        for plan in plans:
            client = self.db.query(Client).filter(Client.id == plan.client_id).first()
            result.append(
                {
                    "plan_id": plan.id,
                    "client_id": plan.client_id,
                    "client_name": client.name if client else "Unknown",
                    "client_email": client.email if client else "",
                    "plan_name": plan.plan_name,
                    "plan_type": plan.plan_type,
                    "status": plan.status,
                    "total_amount": plan.total_amount,
                    "down_payment": plan.down_payment,
                    "num_installments": plan.num_installments,
                    "installment_amount": plan.installment_amount,
                    "frequency": plan.installment_frequency,
                    "amount_paid": plan.amount_paid,
                    "amount_remaining": plan.amount_remaining,
                    "start_date": (
                        plan.start_date.isoformat() if plan.start_date else ""
                    ),
                    "end_date": plan.end_date.isoformat() if plan.end_date else "",
                    "created_at": (
                        plan.created_at.isoformat() if plan.created_at else ""
                    ),
                }
            )

        return result
