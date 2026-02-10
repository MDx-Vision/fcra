"""
RESPA Qualified Written Request (QWR) Service

Manages QWR submissions to mortgage servicers under RESPA §6.
Tracks the complete lifecycle from request to resolution/violation.

Key RESPA §6 Requirements:
- 5 business days: Servicer must acknowledge receipt
- 30 business days: Servicer must provide substantive response
- 45 business days: Response deadline with extension notice
- Prohibited from charging fees during dispute resolution

QWR Types Supported:
- Payment history requests
- Escrow analysis requests
- Fee dispute/challenge
- Payment application disputes
- General account inquiries
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class RESPAQWRServiceError(Exception):
    """Custom exception for RESPA QWR service errors"""

    def __init__(self, message: str, error_code: str, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# QWR status workflow
QWR_STATUSES = {
    "pending": "Pending - Not yet sent",
    "sent": "Sent - Awaiting delivery confirmation",
    "awaiting_acknowledgment": "Awaiting Acknowledgment - 5 business day deadline",
    "awaiting_response": "Awaiting Response - 30 business day deadline",
    "response_received": "Response Received - Under review",
    "violation": "RESPA Violation - Deadline missed",
    "escalated": "Escalated - Filed with CFPB/AG/Attorney",
    "resolved": "Resolved - Issues addressed",
    "closed": "Closed - Case complete",
}

# QWR types
QWR_TYPES = {
    "payment_history": "Payment History Request - Full loan payment record",
    "escrow_analysis": "Escrow Analysis Request - Escrow account review",
    "fee_dispute": "Fee Dispute - Challenge improper fees",
    "payment_application": "Payment Application Dispute - How payments were applied",
    "general_inquiry": "General Inquiry - Account information request",
    "loss_mitigation": "Loss Mitigation - Loan modification or workout options",
    "payoff_request": "Payoff Statement Request - Current balance for payoff",
}

# Violation types
VIOLATION_TYPES = {
    "no_acknowledgment": "No Acknowledgment - Failed to respond within 5 business days",
    "no_response": "No Substantive Response - Failed to respond within 30 business days",
    "inadequate_response": "Inadequate Response - Did not address all issues",
    "continued_fees": "Continued Fees During Dispute - Prohibited under RESPA",
    "retaliation": "Retaliation - Adverse action for filing QWR",
    "false_information": "False Information - Servicer provided inaccurate info",
}

# Response types
RESPONSE_TYPES = {
    "complete": "Complete Response - All requests addressed",
    "partial": "Partial Response - Some issues unaddressed",
    "inadequate": "Inadequate Response - Does not comply with RESPA",
    "denied": "Denied - Servicer disputes the issues",
    "no_response": "No Response - Deadline passed without response",
}

# Resolution types
RESOLUTION_TYPES = {
    "corrected": "Fully Corrected - All issues resolved",
    "denied": "Denied - Servicer refused correction",
    "partial_correction": "Partial Correction - Some issues resolved",
    "escalated": "Escalated - Sent to regulator/attorney",
    "litigation": "Litigation - Lawsuit filed",
    "settled": "Settled - Monetary/account resolution reached",
}

# Loan types
LOAN_TYPES = ["conventional", "fha", "va", "usda", "jumbo", "heloc", "reverse"]

# Letter send methods
SEND_METHODS = ["certified_mail", "regular_mail", "fax", "email", "overnight"]

# Common mortgage servicers
MAJOR_SERVICERS = [
    "Wells Fargo Home Mortgage",
    "Chase Home Lending",
    "Bank of America Home Loans",
    "Mr. Cooper (Nationstar)",
    "Pennymac",
    "Freedom Mortgage",
    "LoanCare",
    "PHH Mortgage",
    "Cenlar FSB",
    "Flagstar Bank",
    "NewRez LLC",
    "Shellpoint Mortgage",
    "Specialized Loan Servicing",
    "Carrington Mortgage",
    "Dovenmuehle Mortgage",
]


def add_business_days(start_date: date, num_days: int) -> date:
    """Add business days to a date (excludes weekends)"""
    current = start_date
    days_added = 0
    while days_added < num_days:
        current += timedelta(days=1)
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            days_added += 1
    return current


class RESPAQWRService:
    """Service for managing RESPA Qualified Written Requests"""

    def __init__(self, session: Session = None):
        """Initialize with optional database session"""
        self._session = session
        self._owns_session = session is None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._owns_session and self._session:
            self._session.close()

    @property
    def session(self) -> Session:
        """Get or create database session"""
        if self._session is None:
            from database import get_db

            self._session = next(get_db())
        return self._session

    def _success_response(
        self, data: Dict[str, Any], message: str = None
    ) -> Dict[str, Any]:
        """Format success response"""
        response = {"success": True, **data}
        if message:
            response["message"] = message
        return response

    def _error_response(
        self, message: str, error_code: str, details: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Format error response"""
        response = {
            "success": False,
            "error": message,
            "error_code": error_code,
        }
        if details:
            response["details"] = details
        return response

    # ========== QWR CRUD Operations ==========

    def create_qwr_request(
        self,
        client_id: int,
        servicer_name: str,
        qwr_type: str,
        request_reason: str,
        loan_number: str = None,
        property_address: str = None,
        servicer_address: str = None,
        servicer_phone: str = None,
        servicer_email: str = None,
        original_lender: str = None,
        original_loan_amount: float = None,
        current_principal_balance: float = None,
        loan_type: str = None,
        specific_issues: List[str] = None,
        documents_requested: List[str] = None,
        disputed_fees: List[Dict] = None,
        disputed_payments: List[Dict] = None,
        escrow_shortage_dispute: bool = False,
        payment_misapplication_dispute: bool = False,
        dispute_item_id: int = None,
        assigned_staff_id: int = None,
        notes: str = None,
    ) -> Dict[str, Any]:
        """Create a new QWR request"""
        try:
            from database import Client, RESPAQWRRequest

            # Validate client exists
            client = self.session.query(Client).filter(Client.id == client_id).first()
            if not client:
                return self._error_response(
                    f"Client {client_id} not found", "CLIENT_NOT_FOUND"
                )

            # Validate QWR type
            if qwr_type not in QWR_TYPES:
                return self._error_response(
                    f"Invalid QWR type: {qwr_type}",
                    "INVALID_QWR_TYPE",
                    {"valid_types": list(QWR_TYPES.keys())},
                )

            # Create the QWR request
            qwr = RESPAQWRRequest(
                client_id=client_id,
                dispute_item_id=dispute_item_id,
                servicer_name=servicer_name,
                servicer_address=servicer_address,
                servicer_phone=servicer_phone,
                servicer_email=servicer_email,
                loan_number=loan_number,
                property_address=property_address,
                original_lender=original_lender,
                original_loan_amount=original_loan_amount,
                current_principal_balance=current_principal_balance,
                loan_type=loan_type,
                qwr_type=qwr_type,
                request_reason=request_reason,
                specific_issues=specific_issues or [],
                documents_requested=documents_requested or [],
                disputed_fees=disputed_fees or [],
                disputed_payments=disputed_payments or [],
                escrow_shortage_dispute=escrow_shortage_dispute,
                payment_misapplication_dispute=payment_misapplication_dispute,
                assigned_staff_id=assigned_staff_id,
                notes=notes,
                status="pending",
            )

            self.session.add(qwr)
            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Created QWR request {qwr.id} for client {client_id}")

            return self._success_response(
                {"qwr_id": qwr.id, "qwr": self._serialize_qwr(qwr)},
                f"QWR request created for {servicer_name}",
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error creating QWR request: {str(e)}")
            return self._error_response(str(e), "CREATE_ERROR")

    def get_qwr_request(self, qwr_id: int) -> Dict[str, Any]:
        """Get a single QWR request by ID"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            return self._success_response({"qwr": self._serialize_qwr(qwr)})

        except Exception as e:
            logger.error(f"Error getting QWR request: {str(e)}")
            return self._error_response(str(e), "GET_ERROR")

    def list_qwr_requests(
        self,
        client_id: int = None,
        status: str = None,
        qwr_type: str = None,
        has_violation: bool = None,
        assigned_staff_id: int = None,
        servicer_name: str = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List QWR requests with optional filters"""
        try:
            from database import RESPAQWRRequest

            query = self.session.query(RESPAQWRRequest)

            if client_id:
                query = query.filter(RESPAQWRRequest.client_id == client_id)
            if status:
                query = query.filter(RESPAQWRRequest.status == status)
            if qwr_type:
                query = query.filter(RESPAQWRRequest.qwr_type == qwr_type)
            if has_violation is not None:
                query = query.filter(
                    RESPAQWRRequest.respa_violation_flagged == has_violation
                )
            if assigned_staff_id:
                query = query.filter(
                    RESPAQWRRequest.assigned_staff_id == assigned_staff_id
                )
            if servicer_name:
                query = query.filter(
                    RESPAQWRRequest.servicer_name.ilike(f"%{servicer_name}%")
                )

            total = query.count()
            qwrs = (
                query.order_by(RESPAQWRRequest.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            return self._success_response(
                {
                    "qwr_requests": [self._serialize_qwr(q) for q in qwrs],
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
            )

        except Exception as e:
            logger.error(f"Error listing QWR requests: {str(e)}")
            return self._error_response(str(e), "LIST_ERROR")

    def update_qwr_request(self, qwr_id: int, **updates) -> Dict[str, Any]:
        """Update a QWR request"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            # Update allowed fields
            allowed_fields = [
                "servicer_name",
                "servicer_address",
                "servicer_phone",
                "servicer_email",
                "loan_number",
                "property_address",
                "original_lender",
                "original_loan_amount",
                "current_principal_balance",
                "loan_type",
                "qwr_type",
                "request_reason",
                "specific_issues",
                "documents_requested",
                "disputed_fees",
                "disputed_payments",
                "escrow_shortage_dispute",
                "payment_misapplication_dispute",
                "assigned_staff_id",
                "notes",
            ]

            for field in allowed_fields:
                if field in updates:
                    setattr(qwr, field, updates[field])

            qwr.updated_at = datetime.utcnow()
            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Updated QWR request {qwr_id}")

            return self._success_response(
                {"qwr": self._serialize_qwr(qwr)}, "QWR request updated"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating QWR request: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def delete_qwr_request(self, qwr_id: int) -> Dict[str, Any]:
        """Delete a QWR request (only if pending)"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            if qwr.status != "pending":
                return self._error_response(
                    "Can only delete pending QWR requests",
                    "CANNOT_DELETE",
                    {"current_status": qwr.status},
                )

            self.session.delete(qwr)
            self.session.commit()

            logger.info(f"Deleted QWR request {qwr_id}")

            return self._success_response({}, "QWR request deleted")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting QWR request: {str(e)}")
            return self._error_response(str(e), "DELETE_ERROR")

    # ========== QWR Workflow Operations ==========

    def mark_sent(
        self,
        qwr_id: int,
        send_method: str,
        sent_at: datetime = None,
        tracking_number: str = None,
    ) -> Dict[str, Any]:
        """Mark a QWR as sent"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            if send_method not in SEND_METHODS:
                return self._error_response(
                    f"Invalid send method: {send_method}",
                    "INVALID_SEND_METHOD",
                    {"valid_methods": SEND_METHODS},
                )

            qwr.letter_sent_at = sent_at or datetime.utcnow()
            qwr.letter_sent_method = send_method
            qwr.tracking_number = tracking_number
            qwr.status = "sent"

            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Marked QWR {qwr_id} as sent via {send_method}")

            return self._success_response(
                {"qwr": self._serialize_qwr(qwr)},
                f"QWR marked as sent via {send_method}",
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error marking QWR sent: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def confirm_delivery(
        self,
        qwr_id: int,
        delivery_date: date = None,
    ) -> Dict[str, Any]:
        """Confirm delivery and calculate RESPA deadlines"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            delivery = delivery_date or date.today()
            qwr.delivery_confirmed = True
            qwr.delivery_date = delivery

            # Calculate RESPA deadlines
            qwr.acknowledgment_deadline = add_business_days(delivery, 5)
            qwr.response_deadline = add_business_days(delivery, 30)

            qwr.status = "awaiting_acknowledgment"

            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Confirmed delivery for QWR {qwr_id}, deadlines set")

            return self._success_response(
                {
                    "qwr": self._serialize_qwr(qwr),
                    "acknowledgment_deadline": qwr.acknowledgment_deadline.isoformat(),
                    "response_deadline": qwr.response_deadline.isoformat(),
                },
                "Delivery confirmed, RESPA deadlines calculated",
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error confirming delivery: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def record_acknowledgment(
        self,
        qwr_id: int,
        acknowledgment_date: datetime = None,
        document_path: str = None,
    ) -> Dict[str, Any]:
        """Record acknowledgment received from servicer"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            ack_date = acknowledgment_date or datetime.utcnow()
            qwr.acknowledgment_received = True
            qwr.acknowledgment_date = ack_date
            qwr.acknowledgment_document_path = document_path

            # Check if acknowledgment was timely
            timely = True
            if (
                qwr.acknowledgment_deadline
                and ack_date.date() > qwr.acknowledgment_deadline
            ):
                timely = False
                # Flag violation for late acknowledgment
                qwr.respa_violation_flagged = True
                qwr.violation_type = "no_acknowledgment"
                qwr.violation_date = qwr.acknowledgment_deadline
                qwr.violation_notes = f"Acknowledgment received {ack_date.date()}, deadline was {qwr.acknowledgment_deadline}"

            qwr.status = "awaiting_response"

            self.session.commit()
            self.session.refresh(qwr)

            message = "Acknowledgment recorded"
            if not timely:
                message += " - RESPA violation flagged for late acknowledgment"

            logger.info(f"Recorded acknowledgment for QWR {qwr_id}, timely: {timely}")

            return self._success_response(
                {
                    "qwr": self._serialize_qwr(qwr),
                    "timely": timely,
                },
                message,
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording acknowledgment: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def record_extension_notice(
        self,
        qwr_id: int,
        extended_deadline: date = None,
    ) -> Dict[str, Any]:
        """Record that servicer sent extension notice (extends deadline to 45 days)"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            qwr.extension_notice_received = True

            # Calculate 45-day deadline if not provided
            if extended_deadline:
                qwr.extended_deadline = extended_deadline
            elif qwr.delivery_date:
                qwr.extended_deadline = add_business_days(qwr.delivery_date, 45)

            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Recorded extension notice for QWR {qwr_id}")

            return self._success_response(
                {
                    "qwr": self._serialize_qwr(qwr),
                    "extended_deadline": (
                        qwr.extended_deadline.isoformat()
                        if qwr.extended_deadline
                        else None
                    ),
                },
                "Extension notice recorded - deadline extended to 45 business days",
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording extension notice: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def record_response(
        self,
        qwr_id: int,
        response_type: str,
        response_received_at: datetime = None,
        response_document_path: str = None,
        payment_history_received: bool = False,
        escrow_analysis_received: bool = False,
        fee_breakdown_received: bool = False,
        payment_application_records_received: bool = False,
        loan_modification_docs_received: bool = False,
        documents_received: List[str] = None,
        notes: str = None,
    ) -> Dict[str, Any]:
        """Record response received from servicer"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            if response_type not in RESPONSE_TYPES:
                return self._error_response(
                    f"Invalid response type: {response_type}",
                    "INVALID_RESPONSE_TYPE",
                    {"valid_types": list(RESPONSE_TYPES.keys())},
                )

            response_date = response_received_at or datetime.utcnow()
            qwr.response_received = True
            qwr.response_received_at = response_date
            qwr.response_type = response_type
            qwr.response_document_path = response_document_path

            # Track documents received
            qwr.payment_history_received = payment_history_received
            qwr.escrow_analysis_received = escrow_analysis_received
            qwr.fee_breakdown_received = fee_breakdown_received
            qwr.payment_application_records_received = (
                payment_application_records_received
            )
            qwr.loan_modification_docs_received = loan_modification_docs_received
            qwr.documents_received = documents_received or []

            if notes:
                qwr.notes = (qwr.notes or "") + f"\n[{response_date}] {notes}"

            # Check if response was timely
            effective_deadline = qwr.extended_deadline or qwr.response_deadline
            timely = True
            if effective_deadline and response_date.date() > effective_deadline:
                timely = False
                # Flag violation for late response
                if not qwr.respa_violation_flagged:
                    qwr.respa_violation_flagged = True
                    qwr.violation_type = "no_response"
                    qwr.violation_date = effective_deadline
                    qwr.violation_notes = f"Response received {response_date.date()}, deadline was {effective_deadline}"

            # Check for inadequate response
            if response_type == "inadequate":
                qwr.respa_violation_flagged = True
                qwr.violation_type = "inadequate_response"
                qwr.violation_notes = f"Response marked as inadequate: {notes}"

            qwr.status = (
                "response_received" if not qwr.respa_violation_flagged else "violation"
            )

            self.session.commit()
            self.session.refresh(qwr)

            message = f"Response recorded as {response_type}"
            if not timely:
                message += " - RESPA violation flagged for late response"

            logger.info(
                f"Recorded response for QWR {qwr_id}, type: {response_type}, timely: {timely}"
            )

            return self._success_response(
                {
                    "qwr": self._serialize_qwr(qwr),
                    "timely": timely,
                },
                message,
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording response: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def flag_violation(
        self,
        qwr_id: int,
        violation_type: str,
        violation_notes: str = None,
        actual_damages: float = None,
        statutory_damages: float = None,
    ) -> Dict[str, Any]:
        """Flag a RESPA violation"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            if violation_type not in VIOLATION_TYPES:
                return self._error_response(
                    f"Invalid violation type: {violation_type}",
                    "INVALID_VIOLATION_TYPE",
                    {"valid_types": list(VIOLATION_TYPES.keys())},
                )

            qwr.respa_violation_flagged = True
            qwr.violation_type = violation_type
            qwr.violation_date = date.today()
            qwr.violation_notes = violation_notes

            if actual_damages is not None:
                qwr.actual_damages = actual_damages
            if statutory_damages is not None:
                qwr.statutory_damages = statutory_damages

            qwr.status = "violation"

            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Flagged RESPA violation for QWR {qwr_id}: {violation_type}")

            return self._success_response(
                {"qwr": self._serialize_qwr(qwr)},
                f"RESPA violation flagged: {VIOLATION_TYPES[violation_type]}",
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error flagging violation: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def record_resolution(
        self,
        qwr_id: int,
        resolution_type: str,
        resolution_notes: str = None,
        amount_refunded: float = None,
        fees_waived: float = None,
        account_corrected: bool = False,
    ) -> Dict[str, Any]:
        """Record resolution of the QWR"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            if resolution_type not in RESOLUTION_TYPES:
                return self._error_response(
                    f"Invalid resolution type: {resolution_type}",
                    "INVALID_RESOLUTION_TYPE",
                    {"valid_types": list(RESOLUTION_TYPES.keys())},
                )

            qwr.resolution_received = True
            qwr.resolution_date = datetime.utcnow()
            qwr.resolution_type = resolution_type
            qwr.resolution_notes = resolution_notes
            qwr.amount_refunded = amount_refunded
            qwr.fees_waived = fees_waived
            qwr.account_corrected = account_corrected

            qwr.status = "resolved"

            self.session.commit()
            self.session.refresh(qwr)

            total_recovery = (amount_refunded or 0) + (fees_waived or 0)
            logger.info(
                f"Recorded resolution for QWR {qwr_id}: {resolution_type}, recovery: ${total_recovery}"
            )

            return self._success_response(
                {
                    "qwr": self._serialize_qwr(qwr),
                    "total_recovery": total_recovery,
                },
                f"Resolution recorded: {RESOLUTION_TYPES[resolution_type]}",
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error recording resolution: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def close_qwr(
        self,
        qwr_id: int,
        reason: str = None,
    ) -> Dict[str, Any]:
        """Close a QWR request"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            qwr.status = "closed"
            qwr.closed_at = datetime.utcnow()
            qwr.closed_reason = reason

            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Closed QWR {qwr_id}: {reason}")

            return self._success_response(
                {"qwr": self._serialize_qwr(qwr)}, "QWR request closed"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error closing QWR: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    # ========== Escalation Operations ==========

    def escalate_to_cfpb(
        self,
        qwr_id: int,
        cfpb_complaint_id: str = None,
    ) -> Dict[str, Any]:
        """Escalate QWR to CFPB"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            qwr.escalated_to_cfpb = True
            qwr.cfpb_complaint_id = cfpb_complaint_id
            qwr.status = "escalated"

            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Escalated QWR {qwr_id} to CFPB: {cfpb_complaint_id}")

            return self._success_response(
                {"qwr": self._serialize_qwr(qwr)}, "Escalated to CFPB"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error escalating to CFPB: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def escalate_to_state_ag(
        self,
        qwr_id: int,
        state_ag_complaint_id: int = None,
    ) -> Dict[str, Any]:
        """Escalate QWR to State Attorney General"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            qwr.escalated_to_state_ag = True
            qwr.state_ag_complaint_id = state_ag_complaint_id
            qwr.status = "escalated"

            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Escalated QWR {qwr_id} to State AG")

            return self._success_response(
                {"qwr": self._serialize_qwr(qwr)}, "Escalated to State Attorney General"
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error escalating to State AG: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    def escalate_to_attorney(
        self,
        qwr_id: int,
        attorney_referral_id: int = None,
    ) -> Dict[str, Any]:
        """Escalate QWR to attorney for litigation"""
        try:
            from database import RESPAQWRRequest

            qwr = (
                self.session.query(RESPAQWRRequest)
                .filter(RESPAQWRRequest.id == qwr_id)
                .first()
            )

            if not qwr:
                return self._error_response(
                    f"QWR request {qwr_id} not found", "QWR_NOT_FOUND"
                )

            qwr.escalated_to_attorney = True
            qwr.attorney_referral_id = attorney_referral_id
            qwr.status = "escalated"

            self.session.commit()
            self.session.refresh(qwr)

            logger.info(f"Escalated QWR {qwr_id} to attorney")

            return self._success_response(
                {"qwr": self._serialize_qwr(qwr)},
                "Escalated to attorney for potential litigation",
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error escalating to attorney: {str(e)}")
            return self._error_response(str(e), "UPDATE_ERROR")

    # ========== Monitoring & Statistics ==========

    def check_deadlines(self) -> Dict[str, Any]:
        """Check for QWRs with approaching or missed deadlines"""
        try:
            from database import RESPAQWRRequest

            today = date.today()
            results = {
                "acknowledgment_overdue": [],
                "acknowledgment_due_soon": [],
                "response_overdue": [],
                "response_due_soon": [],
            }

            # Find overdue acknowledgments
            ack_overdue = (
                self.session.query(RESPAQWRRequest)
                .filter(
                    and_(
                        RESPAQWRRequest.status == "awaiting_acknowledgment",
                        RESPAQWRRequest.acknowledgment_deadline < today,
                        RESPAQWRRequest.acknowledgment_received == False,
                    )
                )
                .all()
            )
            results["acknowledgment_overdue"] = [
                self._serialize_qwr(q) for q in ack_overdue
            ]

            # Find acknowledgments due within 2 days
            soon = today + timedelta(days=2)
            ack_due_soon = (
                self.session.query(RESPAQWRRequest)
                .filter(
                    and_(
                        RESPAQWRRequest.status == "awaiting_acknowledgment",
                        RESPAQWRRequest.acknowledgment_deadline >= today,
                        RESPAQWRRequest.acknowledgment_deadline <= soon,
                        RESPAQWRRequest.acknowledgment_received == False,
                    )
                )
                .all()
            )
            results["acknowledgment_due_soon"] = [
                self._serialize_qwr(q) for q in ack_due_soon
            ]

            # Find overdue responses
            resp_overdue = (
                self.session.query(RESPAQWRRequest)
                .filter(
                    and_(
                        RESPAQWRRequest.status == "awaiting_response",
                        or_(
                            and_(
                                RESPAQWRRequest.extended_deadline.isnot(None),
                                RESPAQWRRequest.extended_deadline < today,
                            ),
                            and_(
                                RESPAQWRRequest.extended_deadline.is_(None),
                                RESPAQWRRequest.response_deadline < today,
                            ),
                        ),
                        RESPAQWRRequest.response_received == False,
                    )
                )
                .all()
            )
            results["response_overdue"] = [self._serialize_qwr(q) for q in resp_overdue]

            # Find responses due within 5 days
            soon_5 = today + timedelta(days=5)
            resp_due_soon = (
                self.session.query(RESPAQWRRequest)
                .filter(
                    and_(
                        RESPAQWRRequest.status == "awaiting_response",
                        or_(
                            and_(
                                RESPAQWRRequest.extended_deadline.isnot(None),
                                RESPAQWRRequest.extended_deadline >= today,
                                RESPAQWRRequest.extended_deadline <= soon_5,
                            ),
                            and_(
                                RESPAQWRRequest.extended_deadline.is_(None),
                                RESPAQWRRequest.response_deadline >= today,
                                RESPAQWRRequest.response_deadline <= soon_5,
                            ),
                        ),
                        RESPAQWRRequest.response_received == False,
                    )
                )
                .all()
            )
            results["response_due_soon"] = [
                self._serialize_qwr(q) for q in resp_due_soon
            ]

            return self._success_response(
                {
                    "deadlines": results,
                    "counts": {
                        "acknowledgment_overdue": len(
                            results["acknowledgment_overdue"]
                        ),
                        "acknowledgment_due_soon": len(
                            results["acknowledgment_due_soon"]
                        ),
                        "response_overdue": len(results["response_overdue"]),
                        "response_due_soon": len(results["response_due_soon"]),
                    },
                }
            )

        except Exception as e:
            logger.error(f"Error checking deadlines: {str(e)}")
            return self._error_response(str(e), "DEADLINE_CHECK_ERROR")

    def auto_flag_violations(self) -> Dict[str, Any]:
        """Automatically flag RESPA violations for missed deadlines"""
        try:
            from database import RESPAQWRRequest

            today = date.today()
            flagged = []

            # Find missed acknowledgment deadlines
            ack_violations = (
                self.session.query(RESPAQWRRequest)
                .filter(
                    and_(
                        RESPAQWRRequest.status == "awaiting_acknowledgment",
                        RESPAQWRRequest.acknowledgment_deadline < today,
                        RESPAQWRRequest.acknowledgment_received == False,
                        RESPAQWRRequest.respa_violation_flagged == False,
                    )
                )
                .all()
            )

            for qwr in ack_violations:
                qwr.respa_violation_flagged = True
                qwr.violation_type = "no_acknowledgment"
                qwr.violation_date = qwr.acknowledgment_deadline
                qwr.violation_notes = (
                    f"Auto-flagged: No acknowledgment by {qwr.acknowledgment_deadline}"
                )
                qwr.status = "violation"
                flagged.append({"qwr_id": qwr.id, "violation": "no_acknowledgment"})

            # Find missed response deadlines
            resp_violations = (
                self.session.query(RESPAQWRRequest)
                .filter(
                    and_(
                        RESPAQWRRequest.status == "awaiting_response",
                        RESPAQWRRequest.response_received == False,
                        RESPAQWRRequest.respa_violation_flagged == False,
                        or_(
                            and_(
                                RESPAQWRRequest.extended_deadline.isnot(None),
                                RESPAQWRRequest.extended_deadline < today,
                            ),
                            and_(
                                RESPAQWRRequest.extended_deadline.is_(None),
                                RESPAQWRRequest.response_deadline < today,
                            ),
                        ),
                    )
                )
                .all()
            )

            for qwr in resp_violations:
                effective_deadline = qwr.extended_deadline or qwr.response_deadline
                qwr.respa_violation_flagged = True
                qwr.violation_type = "no_response"
                qwr.violation_date = effective_deadline
                qwr.violation_notes = (
                    f"Auto-flagged: No response by {effective_deadline}"
                )
                qwr.status = "violation"
                flagged.append({"qwr_id": qwr.id, "violation": "no_response"})

            self.session.commit()

            logger.info(f"Auto-flagged {len(flagged)} RESPA violations")

            return self._success_response(
                {
                    "violations_flagged": flagged,
                    "count": len(flagged),
                },
                f"Auto-flagged {len(flagged)} RESPA violations",
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error auto-flagging violations: {str(e)}")
            return self._error_response(str(e), "AUTO_FLAG_ERROR")

    def get_statistics(self, client_id: int = None) -> Dict[str, Any]:
        """Get QWR statistics"""
        try:
            from database import RESPAQWRRequest

            query = self.session.query(RESPAQWRRequest)
            if client_id:
                query = query.filter(RESPAQWRRequest.client_id == client_id)

            # Status counts
            status_counts = {}
            for status in QWR_STATUSES.keys():
                count = query.filter(RESPAQWRRequest.status == status).count()
                status_counts[status] = count

            # QWR type counts
            type_counts = {}
            for qwr_type in QWR_TYPES.keys():
                count = query.filter(RESPAQWRRequest.qwr_type == qwr_type).count()
                type_counts[qwr_type] = count

            # Violation counts
            violations = query.filter(
                RESPAQWRRequest.respa_violation_flagged == True
            ).count()

            # Resolution stats
            resolved = query.filter(RESPAQWRRequest.resolution_received == True).all()
            total_refunded = sum(q.amount_refunded or 0 for q in resolved)
            total_fees_waived = sum(q.fees_waived or 0 for q in resolved)

            # Top servicers
            servicer_counts = (
                self.session.query(
                    RESPAQWRRequest.servicer_name,
                    func.count(RESPAQWRRequest.id).label("count"),
                )
                .group_by(RESPAQWRRequest.servicer_name)
                .order_by(func.count(RESPAQWRRequest.id).desc())
                .limit(10)
                .all()
            )

            return self._success_response(
                {
                    "total": query.count(),
                    "by_status": status_counts,
                    "by_type": type_counts,
                    "violations": violations,
                    "resolutions": len(resolved),
                    "total_refunded": total_refunded,
                    "total_fees_waived": total_fees_waived,
                    "total_recovery": total_refunded + total_fees_waived,
                    "top_servicers": [
                        {"name": s[0], "count": s[1]} for s in servicer_counts
                    ],
                }
            )

        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return self._error_response(str(e), "STATS_ERROR")

    # ========== Serialization ==========

    def _serialize_qwr(self, qwr) -> Dict[str, Any]:
        """Serialize a QWR request to dict"""
        return {
            "id": qwr.id,
            "client_id": qwr.client_id,
            "dispute_item_id": qwr.dispute_item_id,
            "servicer_name": qwr.servicer_name,
            "servicer_address": qwr.servicer_address,
            "servicer_phone": qwr.servicer_phone,
            "servicer_email": qwr.servicer_email,
            "loan_number": qwr.loan_number,
            "property_address": qwr.property_address,
            "original_lender": qwr.original_lender,
            "original_loan_amount": qwr.original_loan_amount,
            "current_principal_balance": qwr.current_principal_balance,
            "loan_type": qwr.loan_type,
            "qwr_type": qwr.qwr_type,
            "qwr_type_description": QWR_TYPES.get(qwr.qwr_type, ""),
            "request_reason": qwr.request_reason,
            "specific_issues": qwr.specific_issues or [],
            "documents_requested": qwr.documents_requested or [],
            "letter_sent_at": (
                qwr.letter_sent_at.isoformat() if qwr.letter_sent_at else None
            ),
            "letter_sent_method": qwr.letter_sent_method,
            "tracking_number": qwr.tracking_number,
            "delivery_confirmed": qwr.delivery_confirmed,
            "delivery_date": (
                qwr.delivery_date.isoformat() if qwr.delivery_date else None
            ),
            "acknowledgment_deadline": (
                qwr.acknowledgment_deadline.isoformat()
                if qwr.acknowledgment_deadline
                else None
            ),
            "response_deadline": (
                qwr.response_deadline.isoformat() if qwr.response_deadline else None
            ),
            "extended_deadline": (
                qwr.extended_deadline.isoformat() if qwr.extended_deadline else None
            ),
            "extension_notice_received": qwr.extension_notice_received,
            "acknowledgment_received": qwr.acknowledgment_received,
            "acknowledgment_date": (
                qwr.acknowledgment_date.isoformat() if qwr.acknowledgment_date else None
            ),
            "response_received": qwr.response_received,
            "response_received_at": (
                qwr.response_received_at.isoformat()
                if qwr.response_received_at
                else None
            ),
            "response_type": qwr.response_type,
            "payment_history_received": qwr.payment_history_received,
            "escrow_analysis_received": qwr.escrow_analysis_received,
            "fee_breakdown_received": qwr.fee_breakdown_received,
            "payment_application_records_received": qwr.payment_application_records_received,
            "loan_modification_docs_received": qwr.loan_modification_docs_received,
            "documents_received": qwr.documents_received or [],
            "respa_violation_flagged": qwr.respa_violation_flagged,
            "violation_type": qwr.violation_type,
            "violation_type_description": (
                VIOLATION_TYPES.get(qwr.violation_type, "")
                if qwr.violation_type
                else None
            ),
            "violation_notes": qwr.violation_notes,
            "violation_date": (
                qwr.violation_date.isoformat() if qwr.violation_date else None
            ),
            "actual_damages": qwr.actual_damages,
            "statutory_damages": qwr.statutory_damages,
            "attorney_fees": qwr.attorney_fees,
            "class_action_potential": qwr.class_action_potential,
            "disputed_fees": qwr.disputed_fees or [],
            "disputed_payments": qwr.disputed_payments or [],
            "escrow_shortage_dispute": qwr.escrow_shortage_dispute,
            "payment_misapplication_dispute": qwr.payment_misapplication_dispute,
            "resolution_received": qwr.resolution_received,
            "resolution_date": (
                qwr.resolution_date.isoformat() if qwr.resolution_date else None
            ),
            "resolution_type": qwr.resolution_type,
            "resolution_notes": qwr.resolution_notes,
            "amount_refunded": qwr.amount_refunded,
            "fees_waived": qwr.fees_waived,
            "account_corrected": qwr.account_corrected,
            "status": qwr.status,
            "status_description": QWR_STATUSES.get(qwr.status, ""),
            "closed_at": qwr.closed_at.isoformat() if qwr.closed_at else None,
            "closed_reason": qwr.closed_reason,
            "escalated_to_cfpb": qwr.escalated_to_cfpb,
            "cfpb_complaint_id": qwr.cfpb_complaint_id,
            "escalated_to_state_ag": qwr.escalated_to_state_ag,
            "state_ag_complaint_id": qwr.state_ag_complaint_id,
            "escalated_to_attorney": qwr.escalated_to_attorney,
            "attorney_referral_id": qwr.attorney_referral_id,
            "assigned_staff_id": qwr.assigned_staff_id,
            "notes": qwr.notes,
            "created_at": qwr.created_at.isoformat() if qwr.created_at else None,
            "updated_at": (
                qwr.updated_at.isoformat()
                if hasattr(qwr, "updated_at") and qwr.updated_at
                else None
            ),
        }


def get_respa_qwr_service(session: Session = None) -> RESPAQWRService:
    """Factory function to get RESPAQWRService instance"""
    return RESPAQWRService(session=session)
