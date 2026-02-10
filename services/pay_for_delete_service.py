"""
Pay-for-Delete Negotiation Service
Handles P4D negotiations with collection agencies including:
- CRUD operations for negotiations
- Offer letter generation
- Status tracking through negotiation lifecycle
- Payment and deletion verification
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import Client, PayForDeleteNegotiation, get_db

# P4D Negotiation Statuses
P4D_STATUSES = {
    "pending": "Pending - Not yet contacted",
    "offered": "Offer Sent - Awaiting response",
    "countered": "Counter Received - Review needed",
    "negotiating": "Active Negotiation",
    "agreed": "Agreement Reached - Pending payment",
    "payment_pending": "Payment Sent - Awaiting confirmation",
    "paid": "Payment Confirmed - Awaiting deletion",
    "awaiting_deletion": "Paid - Waiting for deletion",
    "deleted": "Successfully Deleted",
    "failed": "Negotiation Failed",
    "cancelled": "Cancelled",
}

# Common collection agencies with P4D success rates
COMMON_COLLECTORS = [
    {
        "name": "Portfolio Recovery Associates",
        "p4d_friendly": True,
        "typical_accept": 40,
    },
    {"name": "Midland Credit Management", "p4d_friendly": True, "typical_accept": 35},
    {"name": "LVNV Funding", "p4d_friendly": True, "typical_accept": 30},
    {"name": "Cavalry SPV", "p4d_friendly": True, "typical_accept": 40},
    {"name": "Enhanced Recovery Company", "p4d_friendly": True, "typical_accept": 35},
    {"name": "Credit Collection Services", "p4d_friendly": True, "typical_accept": 50},
    {"name": "IC System", "p4d_friendly": False, "typical_accept": None},
    {"name": "First Premier Bank", "p4d_friendly": False, "typical_accept": None},
]


class PayForDeleteService:
    """Service for managing pay-for-delete negotiations"""

    def __init__(self, session=None):
        self.session = session or get_db()
        self._owns_session = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._owns_session:
            self.session.close()

    def close(self):
        """Close the database session if we own it"""
        if self._owns_session:
            self.session.close()

    # =========================================================================
    # CRUD Operations
    # =========================================================================

    def create_negotiation(
        self,
        client_id: int,
        collector_name: str,
        original_balance: float,
        current_balance: Optional[float] = None,
        account_number: Optional[str] = None,
        original_creditor: Optional[str] = None,
        collector_address: Optional[str] = None,
        collector_phone: Optional[str] = None,
        collector_email: Optional[str] = None,
        dispute_item_id: Optional[int] = None,
        assigned_staff_id: Optional[int] = None,
        notes: Optional[str] = None,
    ) -> PayForDeleteNegotiation:
        """Create a new pay-for-delete negotiation"""
        negotiation = PayForDeleteNegotiation(
            client_id=client_id,
            collector_name=collector_name,
            original_balance=original_balance,
            current_balance=current_balance or original_balance,
            account_number=account_number,
            original_creditor=original_creditor,
            collector_address=collector_address,
            collector_phone=collector_phone,
            collector_email=collector_email,
            dispute_item_id=dispute_item_id,
            assigned_staff_id=assigned_staff_id,
            notes=notes,
            status="pending",
        )
        self.session.add(negotiation)
        self.session.commit()
        return negotiation

    def get_negotiation(self, negotiation_id: int) -> Optional[PayForDeleteNegotiation]:
        """Get a negotiation by ID"""
        return (
            self.session.query(PayForDeleteNegotiation)
            .filter_by(id=negotiation_id)
            .first()
        )

    def get_client_negotiations(self, client_id: int) -> List[PayForDeleteNegotiation]:
        """Get all negotiations for a client"""
        return (
            self.session.query(PayForDeleteNegotiation)
            .filter_by(client_id=client_id)
            .order_by(PayForDeleteNegotiation.created_at.desc())
            .all()
        )

    def get_negotiations_by_status(self, status: str) -> List[PayForDeleteNegotiation]:
        """Get all negotiations with a specific status"""
        return (
            self.session.query(PayForDeleteNegotiation)
            .filter_by(status=status)
            .order_by(PayForDeleteNegotiation.updated_at.desc())
            .all()
        )

    def get_all_negotiations(
        self,
        status: Optional[str] = None,
        client_id: Optional[int] = None,
        assigned_staff_id: Optional[int] = None,
    ) -> List[PayForDeleteNegotiation]:
        """Get all negotiations with optional filtering"""
        query = self.session.query(PayForDeleteNegotiation)

        if status:
            query = query.filter(PayForDeleteNegotiation.status == status)
        if client_id:
            query = query.filter(PayForDeleteNegotiation.client_id == client_id)
        if assigned_staff_id:
            query = query.filter(
                PayForDeleteNegotiation.assigned_staff_id == assigned_staff_id
            )

        return query.order_by(PayForDeleteNegotiation.updated_at.desc()).all()

    def update_negotiation(
        self, negotiation_id: int, **kwargs
    ) -> Optional[PayForDeleteNegotiation]:
        """Update a negotiation with provided fields"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return None

        for key, value in kwargs.items():
            if hasattr(negotiation, key):
                setattr(negotiation, key, value)

        self.session.commit()
        return negotiation

    def delete_negotiation(self, negotiation_id: int) -> bool:
        """Delete a negotiation"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return False

        self.session.delete(negotiation)
        self.session.commit()
        return True

    # =========================================================================
    # Status Transitions
    # =========================================================================

    def make_offer(
        self,
        negotiation_id: int,
        offer_amount: float,
        offer_percent: Optional[float] = None,
    ) -> Optional[PayForDeleteNegotiation]:
        """Record an initial offer being made"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return None

        if offer_percent is None and negotiation.original_balance:
            offer_percent = (offer_amount / negotiation.original_balance) * 100

        negotiation.initial_offer_amount = offer_amount
        negotiation.initial_offer_percent = offer_percent
        negotiation.initial_offer_date = datetime.utcnow()
        negotiation.status = "offered"
        negotiation.last_contact_date = datetime.utcnow()

        self.session.commit()
        return negotiation

    def record_counter_offer(
        self,
        negotiation_id: int,
        counter_amount: float,
    ) -> Optional[PayForDeleteNegotiation]:
        """Record a counter offer from the collector"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return None

        negotiation.counter_offer_amount = counter_amount
        negotiation.counter_offer_date = datetime.utcnow()
        negotiation.status = "countered"
        negotiation.last_contact_date = datetime.utcnow()

        self.session.commit()
        return negotiation

    def make_counter_offer(
        self,
        negotiation_id: int,
        our_counter_amount: float,
    ) -> Optional[PayForDeleteNegotiation]:
        """Record our counter to their counter offer"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return None

        negotiation.our_counter_amount = our_counter_amount
        negotiation.our_counter_date = datetime.utcnow()
        negotiation.status = "negotiating"
        negotiation.last_contact_date = datetime.utcnow()

        self.session.commit()
        return negotiation

    def accept_agreement(
        self,
        negotiation_id: int,
        agreed_amount: float,
        payment_deadline: Optional[datetime] = None,
        deletion_deadline: Optional[datetime] = None,
        agreement_in_writing: bool = False,
        agreement_signed_by: Optional[str] = None,
    ) -> Optional[PayForDeleteNegotiation]:
        """Record an accepted agreement"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return None

        agreed_percent = None
        if negotiation.original_balance:
            agreed_percent = (agreed_amount / negotiation.original_balance) * 100

        negotiation.agreed_amount = agreed_amount
        negotiation.agreed_percent = agreed_percent
        negotiation.agreement_date = datetime.utcnow()
        negotiation.status = "agreed"

        if payment_deadline:
            negotiation.payment_deadline = (
                payment_deadline.date()
                if isinstance(payment_deadline, datetime)
                else payment_deadline
            )
        if deletion_deadline:
            negotiation.deletion_deadline = (
                deletion_deadline.date()
                if isinstance(deletion_deadline, datetime)
                else deletion_deadline
            )

        negotiation.agreement_in_writing = agreement_in_writing
        negotiation.agreement_signed_by = agreement_signed_by
        negotiation.last_contact_date = datetime.utcnow()

        self.session.commit()
        return negotiation

    def record_payment(
        self,
        negotiation_id: int,
        payment_amount: float,
        payment_method: str,
        payment_confirmation: Optional[str] = None,
    ) -> Optional[PayForDeleteNegotiation]:
        """Record that payment has been made"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return None

        negotiation.payment_amount = payment_amount
        negotiation.payment_date = datetime.utcnow()
        negotiation.payment_method = payment_method
        negotiation.payment_confirmation = payment_confirmation
        negotiation.status = "paid"
        negotiation.last_contact_date = datetime.utcnow()

        self.session.commit()
        return negotiation

    def verify_deletion(
        self,
        negotiation_id: int,
        verified_bureau: str,
    ) -> Optional[PayForDeleteNegotiation]:
        """Record that deletion has been verified on credit report"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return None

        negotiation.deletion_verified = True
        negotiation.deletion_verified_date = datetime.utcnow()
        negotiation.deletion_verified_bureau = verified_bureau
        negotiation.status = "deleted"

        self.session.commit()
        return negotiation

    def mark_failed(
        self,
        negotiation_id: int,
        reason: str,
    ) -> Optional[PayForDeleteNegotiation]:
        """Mark a negotiation as failed"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return None

        negotiation.status = "failed"
        negotiation.failure_reason = reason

        self.session.commit()
        return negotiation

    def cancel_negotiation(
        self,
        negotiation_id: int,
        reason: Optional[str] = None,
    ) -> Optional[PayForDeleteNegotiation]:
        """Cancel a negotiation"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return None

        negotiation.status = "cancelled"
        if reason:
            negotiation.failure_reason = reason

        self.session.commit()
        return negotiation

    # =========================================================================
    # Statistics
    # =========================================================================

    def get_statistics(self) -> Dict[str, Any]:
        """Get overall P4D statistics"""
        all_negotiations = self.session.query(PayForDeleteNegotiation).all()

        stats = {
            "total": len(all_negotiations),
            "by_status": {},
            "success_rate": 0,
            "total_saved": 0,
            "avg_settlement_percent": 0,
        }

        # Count by status
        for status in P4D_STATUSES.keys():
            count = len([n for n in all_negotiations if n.status == status])
            stats["by_status"][status] = count

        # Calculate success rate and savings
        completed = [n for n in all_negotiations if n.status == "deleted"]
        failed = [n for n in all_negotiations if n.status == "failed"]

        if completed or failed:
            stats["success_rate"] = (
                len(completed) / (len(completed) + len(failed)) * 100
            )

        # Calculate total saved
        for n in completed:
            if n.original_balance and n.agreed_amount:
                stats["total_saved"] += n.original_balance - n.agreed_amount

        # Average settlement percentage
        settlement_percents = [n.agreed_percent for n in completed if n.agreed_percent]
        if settlement_percents:
            stats["avg_settlement_percent"] = sum(settlement_percents) / len(
                settlement_percents
            )

        return stats

    def get_pending_follow_ups(self) -> List[PayForDeleteNegotiation]:
        """Get negotiations that need follow-up"""
        today = datetime.utcnow().date()
        return (
            self.session.query(PayForDeleteNegotiation)
            .filter(
                PayForDeleteNegotiation.next_follow_up_date <= today,
                PayForDeleteNegotiation.status.notin_(
                    ["deleted", "failed", "cancelled"]
                ),
            )
            .order_by(PayForDeleteNegotiation.next_follow_up_date)
            .all()
        )

    def get_awaiting_deletion(self) -> List[PayForDeleteNegotiation]:
        """Get paid negotiations awaiting deletion verification"""
        return (
            self.session.query(PayForDeleteNegotiation)
            .filter(PayForDeleteNegotiation.status.in_(["paid", "awaiting_deletion"]))
            .order_by(PayForDeleteNegotiation.payment_date)
            .all()
        )

    # =========================================================================
    # Letter Generation
    # =========================================================================

    def generate_offer_letter(
        self,
        negotiation_id: int,
        offer_amount: Optional[float] = None,
    ) -> Dict[str, str]:
        """Generate a pay-for-delete offer letter"""
        negotiation = self.get_negotiation(negotiation_id)
        if not negotiation:
            return {"error": "Negotiation not found"}

        client = self.session.query(Client).filter_by(id=negotiation.client_id).first()
        if not client:
            return {"error": "Client not found"}

        # Use provided amount or calculate suggested offer
        if offer_amount is None:
            offer_amount = negotiation.initial_offer_amount
        if offer_amount is None and negotiation.current_balance:
            # Suggest 30% of current balance as starting point
            offer_amount = negotiation.current_balance * 0.30

        offer_percent = 0
        if negotiation.original_balance and offer_amount:
            offer_percent = (offer_amount / negotiation.original_balance) * 100

        # Build client address
        client_address = ""
        if client.address_street:
            client_address = client.address_street
            if client.address_city and client.address_state and client.address_zip:
                client_address += f"\n{client.address_city}, {client.address_state} {client.address_zip}"

        letter_content = f"""
{client.name or f"{client.first_name} {client.last_name}"}
{client_address}

{datetime.now().strftime("%B %d, %Y")}

{negotiation.collector_name}
{negotiation.collector_address or "[COLLECTOR ADDRESS]"}

RE: Pay-for-Delete Settlement Offer
Account Number: {negotiation.account_number or "[ACCOUNT NUMBER]"}
Original Creditor: {negotiation.original_creditor or "[ORIGINAL CREDITOR]"}
Current Balance: ${negotiation.current_balance:,.2f}

To Whom It May Concern:

I am writing to propose a settlement of the above-referenced account. I am prepared to pay ${offer_amount:,.2f} ({offer_percent:.0f}% of the original balance) as full and final settlement of this debt.

SETTLEMENT TERMS:

In exchange for my payment, I require the following:

1. FULL DELETION: You will request deletion of this account from all three major credit bureaus (Equifax, Experian, and TransUnion) within 30 days of receiving payment.

2. WRITTEN AGREEMENT: Before I submit payment, I require a signed letter on your company letterhead confirming:
   - The settlement amount of ${offer_amount:,.2f}
   - That this payment constitutes full satisfaction of the debt
   - Your commitment to delete (not update) this account from all credit bureaus

3. PAYMENT METHOD: Upon receipt of your signed agreement, I will submit payment via [certified check/money order].

4. NO FURTHER COLLECTION: You will cease all collection activity and will not sell or transfer this account.

This offer is contingent upon receiving a written agreement. I will not submit payment without written confirmation of the deletion agreement.

Please respond in writing within 15 days. This offer expires 30 days from the date of this letter.

I look forward to resolving this matter.

Sincerely,

______________________________
{client.name or f"{client.first_name} {client.last_name}"}
"""

        return {
            "content": letter_content.strip(),
            "client_name": client.name or f"{client.first_name} {client.last_name}",
            "collector_name": negotiation.collector_name,
            "offer_amount": offer_amount,
            "offer_percent": offer_percent,
            "account_number": negotiation.account_number,
        }


# Factory function
def get_pay_for_delete_service(session=None) -> PayForDeleteService:
    """Factory function to get PayForDeleteService instance"""
    return PayForDeleteService(session)


# Export common collectors for UI
def get_common_collectors() -> List[Dict[str, Any]]:
    """Get list of common collectors with P4D info"""
    return COMMON_COLLECTORS


# Export status definitions for UI
def get_p4d_statuses() -> Dict[str, str]:
    """Get P4D status definitions"""
    return P4D_STATUSES
