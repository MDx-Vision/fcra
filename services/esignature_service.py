"""
Electronic Signature Service for Brightpath Ascend FCRA Platform
Full ESIGN Act, UETA, and CROA Compliance Implementation

Legal Requirements Met:
1. Intent to Sign - Explicit checkbox + typed name
2. Consent to Electronic Transactions - 3 acknowledgments before signing
3. Attribution - IP, user agent, device fingerprint, email, timestamp
4. Record Retention - Permanent storage, PDF copies, signature certificates

Features:
- Session-based signing flow
- SHA-256 document hashing for tamper-evidence
- Complete 12-action audit trail
- PDF certificate generation
- CROA compliance (Rights Disclosure first, 3-day cancellation)
"""

import base64
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from database import (
    ESIGN_AUDIT_ACTIONS,
    Client,
    CROAComplianceTracker,
    DocumentTemplate,
    ESignatureRequest,
    SessionLocal,
    SignatureAuditLog,
    SignatureSession,
    SignedDocument,
)

logger = logging.getLogger(__name__)

# Configuration
PROVIDER_NAME = "brightpath_esign"
SESSION_EXPIRY_DAYS = 7
SIGNATURE_FOLDER = "static/signatures"
SIGNED_DOCS_FOLDER = "static/signed_documents"
CERTIFICATES_FOLDER = "static/certificates"
CERT_PREFIX = os.environ.get("ESIGN_CERT_PREFIX", "BAG")

# Document types supported
DOCUMENT_TYPES = {
    "client_agreement": "Main Service Agreement",
    "limited_poa": "Limited Power of Attorney",
    "dispute_authorization": "Authorization for Dispute Filing",
    "fee_agreement": "Fee Agreement",
    "rights_disclosure": "Consumer Credit File Rights Disclosure",
    "cancellation_notice": "Right to Cancel Notice",
    "hipaa_authorization": "HIPAA Authorization",
}

# ESIGN Act consent disclosure text
ESIGN_CONSENT_DISCLOSURE = """
<h2>Consent to Use Electronic Signatures and Records</h2>

<p>Before you sign documents electronically, you must consent to the use of electronic signatures and records.
Please read the following disclosure carefully.</p>

<h3>1. Hardware and Software Requirements</h3>
<p>To access, view, and retain electronic records and signatures, you will need:</p>
<ul>
    <li>A computer or mobile device with internet access</li>
    <li>A current web browser (Chrome, Firefox, Safari, or Edge)</li>
    <li>JavaScript enabled</li>
    <li>PDF reader software to view and print documents</li>
    <li>An email account to receive copies of signed documents</li>
</ul>

<h3>2. Right to Paper Copies</h3>
<p>You have the right to receive paper copies of any documents you sign electronically.
To request paper copies, contact us at support@brightpathascend.com or call our office.
There may be a fee of $5.00 per document for paper copies.</p>

<h3>3. Right to Withdraw Consent</h3>
<p>You may withdraw your consent to use electronic signatures at any time by contacting us in writing.
Withdrawal of consent will not affect the legal validity of any documents already signed electronically.
After withdrawal, you will need to sign documents in person with wet ink signatures.</p>

<h3>4. Updating Your Contact Information</h3>
<p>It is your responsibility to keep your email address and contact information current.
You can update your information through your client portal or by contacting our office.</p>

<h3>5. Legal Effect</h3>
<p>By consenting below, you agree that electronic signatures on documents have the same legal
effect as handwritten signatures, in accordance with the Electronic Signatures in Global and
National Commerce Act (ESIGN Act, 15 U.S.C. § 7001) and the Uniform Electronic Transactions Act (UETA).</p>
"""

# Intent statement shown before signing
INTENT_STATEMENT = "I intend this to be my legally binding electronic signature."


def _ensure_folders():
    """Ensure all required storage folders exist."""
    for folder in [SIGNATURE_FOLDER, SIGNED_DOCS_FOLDER, CERTIFICATES_FOLDER]:
        os.makedirs(folder, exist_ok=True)


def _get_base_url():
    """Get the base URL for generating signing links."""
    domain = os.environ.get("REPLIT_DEV_DOMAIN") or os.environ.get("REPL_SLUG_URL", "")
    if domain:
        if not domain.startswith("http"):
            domain = f"https://{domain}"
        return domain
    return ""


def _generate_uuid():
    """Generate a unique, URL-safe UUID."""
    return secrets.token_urlsafe(32)


def _generate_certificate_number():
    """Generate a unique certificate number."""
    timestamp = datetime.utcnow().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"{CERT_PREFIX}-{timestamp}-{random_part}"


def _compute_document_hash(content: str) -> str:
    """Compute SHA-256 hash of document content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _add_business_days(start_date: datetime, num_days: int) -> datetime:
    """
    Add business days to a date (excludes weekends).
    For CROA 3-business-day cancellation period.
    """
    current = start_date
    days_added = 0

    while days_added < num_days:
        current += timedelta(days=1)
        # Monday = 0, Sunday = 6
        if current.weekday() < 5:  # Weekday
            days_added += 1

    # Set to end of day (11:59:59 PM)
    return current.replace(hour=23, minute=59, second=59, microsecond=0)


def _log_audit_action(
    session,
    client_id: int,
    action: str,
    session_id: Optional[int] = None,
    document_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
    details: Optional[Dict] = None,
    raw_request: Optional[Dict] = None,
):
    """Create an audit log entry."""
    action_display = ESIGN_AUDIT_ACTIONS.get(action, action)

    log = SignatureAuditLog(
        session_id=session_id,
        document_id=document_id,
        client_id=client_id,
        action=action,
        action_display=action_display,
        action_details=details,
        ip_address=ip_address,
        user_agent=user_agent,
        device_fingerprint=device_fingerprint,
        raw_request_data=raw_request,
    )
    session.add(log)
    return log


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================


def initiate_signing_session(
    client_id: int,
    documents: List[Dict],
    signer_email: str,
    signer_name: str,
    return_url: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Initiate a new signing session for a client.

    Args:
        client_id: ID of the client
        documents: List of dicts with document_type, document_name, document_html
        signer_email: Email of the signer
        signer_name: Name of the signer
        return_url: URL to redirect after completion
        ip_address: Client's IP address
        user_agent: Client's browser info

    Returns:
        dict with session_uuid, signing_link, expires_at
    """
    db_session = SessionLocal()
    try:
        # Verify client exists
        client = db_session.query(Client).filter(Client.id == client_id).first()
        if not client:
            return {
                "success": False,
                "error": f"Client {client_id} not found",
            }

        _ensure_folders()

        # Create session
        session_uuid = _generate_uuid()
        base_url = _get_base_url()
        signing_link = (
            f"{base_url}/esign/{session_uuid}" if base_url else f"/esign/{session_uuid}"
        )
        expires_at = datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS)

        signing_session = SignatureSession(
            session_uuid=session_uuid,
            client_id=client_id,
            status="pending",
            signer_email=signer_email,
            signer_name=signer_name,
            ip_address=ip_address,
            user_agent=user_agent,
            signing_link=signing_link,
            return_url=return_url,
            expires_at=expires_at,
            consent_disclosure_html=ESIGN_CONSENT_DISCLOSURE,
        )
        db_session.add(signing_session)
        db_session.flush()  # Get session ID

        # Create document records
        for idx, doc in enumerate(documents):
            doc_uuid = _generate_uuid()
            is_croa = doc.get("is_croa_document", False)

            signed_doc = SignedDocument(
                document_uuid=doc_uuid,
                client_id=client_id,
                session_id=signing_session.id,
                template_id=doc.get("template_id"),
                document_name=doc["document_name"],
                document_type=doc.get("document_type", "client_agreement"),
                document_html=doc.get("document_html", ""),
                status="pending",
                is_croa_document=is_croa,
                croa_signing_order=doc.get("croa_signing_order", idx),
            )
            db_session.add(signed_doc)

        # Log audit
        _log_audit_action(
            db_session,
            client_id=client_id,
            action="session_initiated",
            session_id=signing_session.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "documents_count": len(documents),
                "signer_email": signer_email,
            },
        )

        db_session.commit()

        logger.info(
            f"Created signing session {session_uuid} for client {client_id} with {len(documents)} documents"
        )

        return {
            "success": True,
            "session_uuid": session_uuid,
            "session_id": signing_session.id,
            "signing_link": signing_link,
            "expires_at": expires_at.isoformat(),
            "documents_count": len(documents),
        }

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error initiating signing session: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db_session.close()


def get_session_by_uuid(session_uuid: str) -> Dict[str, Any]:
    """Get signing session details by UUID."""
    db_session = SessionLocal()
    try:
        signing_session = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.session_uuid == session_uuid)
            .first()
        )

        if not signing_session:
            return {
                "success": False,
                "error": "Session not found",
            }

        # Check expiration
        if (
            signing_session.expires_at
            and signing_session.expires_at < datetime.utcnow()
        ):
            return {
                "success": False,
                "error": "Session has expired",
                "expired": True,
            }

        # Get documents
        documents = []
        for doc in signing_session.documents:
            documents.append(
                {
                    "document_uuid": doc.document_uuid,
                    "document_name": doc.document_name,
                    "document_type": doc.document_type,
                    "status": doc.status,
                    "is_croa_document": doc.is_croa_document,
                    "croa_signing_order": doc.croa_signing_order,
                }
            )

        # Sort CROA documents by order
        documents.sort(
            key=lambda x: (not x["is_croa_document"], x["croa_signing_order"])
        )

        return {
            "success": True,
            "session": signing_session.to_dict(),
            "documents": documents,
            "consent_disclosure": signing_session.consent_disclosure_html,
        }

    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        db_session.close()


# =============================================================================
# ESIGN ACT CONSENT
# =============================================================================


def submit_esign_consent(
    session_uuid: str,
    hardware_software_acknowledged: bool,
    paper_copy_right_acknowledged: bool,
    consent_withdrawal_acknowledged: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Submit ESIGN Act consent with 3 required acknowledgments.

    Args:
        session_uuid: Session UUID
        hardware_software_acknowledged: Acknowledges tech requirements
        paper_copy_right_acknowledged: Acknowledges right to paper copies
        consent_withdrawal_acknowledged: Acknowledges right to withdraw consent
        ip_address: Client's IP
        user_agent: Client's browser
        device_fingerprint: Browser fingerprint

    Returns:
        dict with success status
    """
    db_session = SessionLocal()
    try:
        signing_session = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.session_uuid == session_uuid)
            .first()
        )

        if not signing_session:
            return {"success": False, "error": "Session not found"}

        if (
            signing_session.expires_at
            and signing_session.expires_at < datetime.utcnow()
        ):
            return {"success": False, "error": "Session has expired"}

        # All 3 acknowledgments required
        if not all(
            [
                hardware_software_acknowledged,
                paper_copy_right_acknowledged,
                consent_withdrawal_acknowledged,
            ]
        ):
            return {
                "success": False,
                "error": "All three acknowledgments are required",
            }

        # Update session
        now = datetime.utcnow()
        signing_session.esign_consent_given = True
        signing_session.esign_consent_timestamp = now
        signing_session.hardware_software_acknowledged = True
        signing_session.paper_copy_right_acknowledged = True
        signing_session.consent_withdrawal_acknowledged = True
        signing_session.consent_at = now
        signing_session.status = "consent_given"
        signing_session.ip_address = ip_address or signing_session.ip_address
        signing_session.user_agent = user_agent or signing_session.user_agent
        signing_session.device_fingerprint = device_fingerprint

        # Log audit
        _log_audit_action(
            db_session,
            client_id=signing_session.client_id,
            action="esign_consent_given",
            session_id=signing_session.id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            details={
                "hardware_software_acknowledged": True,
                "paper_copy_right_acknowledged": True,
                "consent_withdrawal_acknowledged": True,
            },
        )

        db_session.commit()

        logger.info(f"ESIGN consent recorded for session {session_uuid}")

        return {
            "success": True,
            "consent_timestamp": now.isoformat(),
        }

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error submitting consent: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


# =============================================================================
# DOCUMENT REVIEW & SIGNING
# =============================================================================


def get_document_for_review(session_uuid: str, document_uuid: str) -> Dict[str, Any]:
    """Get a document for review before signing."""
    db_session = SessionLocal()
    try:
        signing_session = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.session_uuid == session_uuid)
            .first()
        )

        if not signing_session:
            return {"success": False, "error": "Session not found"}

        if not signing_session.esign_consent_given:
            return {
                "success": False,
                "error": "ESIGN consent required before reviewing documents",
            }

        document = (
            db_session.query(SignedDocument)
            .filter(
                SignedDocument.document_uuid == document_uuid,
                SignedDocument.session_id == signing_session.id,
            )
            .first()
        )

        if not document:
            return {"success": False, "error": "Document not found"}

        # Check CROA signing order
        if document.is_croa_document:
            # Find any unsigned CROA documents with lower order
            unsigned_prior = (
                db_session.query(SignedDocument)
                .filter(
                    SignedDocument.session_id == signing_session.id,
                    SignedDocument.is_croa_document == True,
                    SignedDocument.croa_signing_order < document.croa_signing_order,
                    SignedDocument.status != "signed",
                )
                .first()
            )

            if unsigned_prior:
                return {
                    "success": False,
                    "error": f"You must sign '{unsigned_prior.document_name}' first",
                    "required_document": unsigned_prior.document_uuid,
                }

        # Mark as presented
        if not document.document_presented_at:
            document.document_presented_at = datetime.utcnow()

        _log_audit_action(
            db_session,
            client_id=signing_session.client_id,
            action="document_reviewed",
            session_id=signing_session.id,
            document_id=document.id,
            details={"document_name": document.document_name},
        )

        db_session.commit()

        return {
            "success": True,
            "document": {
                "document_uuid": document.document_uuid,
                "document_name": document.document_name,
                "document_type": document.document_type,
                "document_html": document.document_html,
                "is_croa_document": document.is_croa_document,
                "status": document.status,
            },
            "intent_statement": INTENT_STATEMENT,
        }

    except Exception as e:
        logger.error(f"Error getting document: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def record_document_review_progress(
    session_uuid: str,
    document_uuid: str,
    scroll_percentage: int,
    review_duration_seconds: int,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Record scroll progress and review duration for a document."""
    db_session = SessionLocal()
    try:
        signing_session = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.session_uuid == session_uuid)
            .first()
        )

        if not signing_session:
            return {"success": False, "error": "Session not found"}

        document = (
            db_session.query(SignedDocument)
            .filter(
                SignedDocument.document_uuid == document_uuid,
                SignedDocument.session_id == signing_session.id,
            )
            .first()
        )

        if not document:
            return {"success": False, "error": "Document not found"}

        # Update progress
        document.scroll_percentage = max(
            document.scroll_percentage or 0, scroll_percentage
        )
        document.review_duration_seconds = max(
            document.review_duration_seconds or 0, review_duration_seconds
        )

        if scroll_percentage >= 95:
            document.scrolled_to_bottom = True

        if not document.review_started_at:
            document.review_started_at = datetime.utcnow()

        # Log scroll action periodically (every 25%)
        if scroll_percentage in [25, 50, 75, 100]:
            _log_audit_action(
                db_session,
                client_id=signing_session.client_id,
                action="document_scrolled",
                session_id=signing_session.id,
                document_id=document.id,
                ip_address=ip_address,
                details={
                    "scroll_percentage": scroll_percentage,
                    "review_duration": review_duration_seconds,
                },
            )

        db_session.commit()

        return {
            "success": True,
            "scrolled_to_bottom": document.scrolled_to_bottom,
            "review_duration_seconds": document.review_duration_seconds,
        }

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error recording progress: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def sign_document(
    session_uuid: str,
    document_uuid: str,
    signature_type: str,  # 'typed' or 'drawn'
    signature_value: str,  # Typed name or base64 image
    intent_confirmed: bool,
    typed_name: str,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_fingerprint: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Sign a document with full legal compliance.

    Args:
        session_uuid: Session UUID
        document_uuid: Document UUID
        signature_type: 'typed' or 'drawn'
        signature_value: Typed name or base64 signature image
        intent_confirmed: Must be True (checkbox checked)
        typed_name: Typed name for verification
        ip_address: Signer's IP
        user_agent: Signer's browser
        device_fingerprint: Browser fingerprint

    Returns:
        dict with certificate_number, signature details
    """
    db_session = SessionLocal()
    try:
        signing_session = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.session_uuid == session_uuid)
            .first()
        )

        if not signing_session:
            return {"success": False, "error": "Session not found"}

        if not signing_session.esign_consent_given:
            return {"success": False, "error": "ESIGN consent required before signing"}

        document = (
            db_session.query(SignedDocument)
            .filter(
                SignedDocument.document_uuid == document_uuid,
                SignedDocument.session_id == signing_session.id,
            )
            .first()
        )

        if not document:
            return {"success": False, "error": "Document not found"}

        if document.status == "signed":
            return {"success": False, "error": "Document already signed"}

        # Verify intent confirmed
        if not intent_confirmed:
            return {"success": False, "error": "You must confirm your intent to sign"}

        # Verify typed name matches
        if typed_name.strip().lower() != signing_session.signer_name.strip().lower():
            return {
                "success": False,
                "error": f"Typed name must match: {signing_session.signer_name}",
            }

        # CROA signing order check
        if document.is_croa_document:
            unsigned_prior = (
                db_session.query(SignedDocument)
                .filter(
                    SignedDocument.session_id == signing_session.id,
                    SignedDocument.is_croa_document == True,
                    SignedDocument.croa_signing_order < document.croa_signing_order,
                    SignedDocument.status != "signed",
                )
                .first()
            )

            if unsigned_prior:
                return {
                    "success": False,
                    "error": f"You must sign '{unsigned_prior.document_name}' first",
                }

        _ensure_folders()
        now = datetime.utcnow()

        # Compute document hash for tamper-evidence
        doc_hash = _compute_document_hash(document.document_html or "")

        # Generate certificate number
        cert_number = _generate_certificate_number()

        # Save signature image if drawn
        signature_image_path = None
        if signature_type == "drawn" and signature_value:
            if signature_value.startswith("data:image"):
                _, signature_value = signature_value.split(",", 1)
            try:
                signature_bytes = base64.b64decode(signature_value)
                timestamp = now.strftime("%Y%m%d_%H%M%S")
                filename = f"sig_{document.client_id}_{document.id}_{timestamp}.png"
                signature_image_path = os.path.join(SIGNATURE_FOLDER, filename)
                with open(signature_image_path, "wb") as f:
                    f.write(signature_bytes)
            except Exception as e:
                logger.warning(f"Could not save signature image: {e}")

        # Update document record
        document.signature_type = signature_type
        document.signature_value = (
            signature_value if signature_type == "typed" else typed_name
        )
        document.signature_image_path = signature_image_path
        document.intent_checkbox_checked = True
        document.intent_statement = INTENT_STATEMENT
        document.signer_name = typing_name = signing_session.signer_name
        document.signer_email = signing_session.signer_email
        document.signer_ip = ip_address
        document.signer_user_agent = user_agent
        document.signature_timestamp = now
        document.document_hash_sha256 = doc_hash
        document.certificate_number = cert_number
        document.status = "signed"
        document.updated_at = now

        # Log audit actions
        _log_audit_action(
            db_session,
            client_id=signing_session.client_id,
            action="intent_confirmed",
            session_id=signing_session.id,
            document_id=document.id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            details={"intent_statement": INTENT_STATEMENT},
        )

        _log_audit_action(
            db_session,
            client_id=signing_session.client_id,
            action="document_signed",
            session_id=signing_session.id,
            document_id=document.id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            details={
                "document_name": document.document_name,
                "signature_type": signature_type,
                "certificate_number": cert_number,
                "document_hash": doc_hash,
            },
        )

        # Update session status
        signing_session.status = "in_progress"

        # Handle CROA compliance
        if document.is_croa_document and document.document_type == "rights_disclosure":
            # Get or create CROA tracker
            croa_tracker = (
                db_session.query(CROAComplianceTracker)
                .filter(CROAComplianceTracker.client_id == signing_session.client_id)
                .first()
            )

            if not croa_tracker:
                croa_tracker = CROAComplianceTracker(
                    client_id=signing_session.client_id,
                    session_id=signing_session.id,
                )
                db_session.add(croa_tracker)

            croa_tracker.rights_disclosure_signed = True
            croa_tracker.rights_disclosure_signed_at = now
            croa_tracker.rights_disclosure_document_id = document.id

        # Check if contract was signed (starts cancellation period)
        if document.is_croa_document and document.document_type == "client_agreement":
            croa_tracker = (
                db_session.query(CROAComplianceTracker)
                .filter(CROAComplianceTracker.client_id == signing_session.client_id)
                .first()
            )

            if croa_tracker:
                croa_tracker.contract_package_signed = True
                croa_tracker.contract_package_signed_at = now
                croa_tracker.cancellation_period_start = now
                croa_tracker.cancellation_period_end = _add_business_days(now, 3)

        db_session.commit()

        logger.info(f"Document {document_uuid} signed with certificate {cert_number}")

        return {
            "success": True,
            "certificate_number": cert_number,
            "signature_timestamp": now.isoformat(),
            "document_hash": doc_hash,
            "signer_name": signing_session.signer_name,
        }

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error signing document: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def complete_signing_session(
    session_uuid: str,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Complete a signing session after all documents are signed."""
    db_session = SessionLocal()
    try:
        signing_session = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.session_uuid == session_uuid)
            .first()
        )

        if not signing_session:
            return {"success": False, "error": "Session not found"}

        # Check all documents are signed
        unsigned_docs = (
            db_session.query(SignedDocument)
            .filter(
                SignedDocument.session_id == signing_session.id,
                SignedDocument.status != "signed",
            )
            .all()
        )

        if unsigned_docs:
            return {
                "success": False,
                "error": f"{len(unsigned_docs)} document(s) still need to be signed",
                "unsigned_documents": [d.document_name for d in unsigned_docs],
            }

        now = datetime.utcnow()
        signing_session.status = "completed"
        signing_session.completed_at = now

        _log_audit_action(
            db_session,
            client_id=signing_session.client_id,
            action="session_completed",
            session_id=signing_session.id,
            ip_address=ip_address,
            details={
                "documents_signed": len(signing_session.documents),
                "total_duration_seconds": int(
                    (now - signing_session.initiated_at).total_seconds()
                ),
            },
        )

        db_session.commit()

        logger.info(f"Signing session {session_uuid} completed")

        return {
            "success": True,
            "completed_at": now.isoformat(),
            "documents_signed": len(signing_session.documents),
            "return_url": signing_session.return_url,
        }

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error completing session: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


# =============================================================================
# VERIFICATION & AUDIT
# =============================================================================


def verify_document_integrity(document_uuid: str) -> Dict[str, Any]:
    """Verify a signed document hasn't been tampered with."""
    db_session = SessionLocal()
    try:
        document = (
            db_session.query(SignedDocument)
            .filter(SignedDocument.document_uuid == document_uuid)
            .first()
        )

        if not document:
            return {"success": False, "error": "Document not found"}

        if document.status != "signed":
            return {"success": False, "error": "Document has not been signed"}

        is_valid = document.verify_integrity()

        return {
            "success": True,
            "document_uuid": document_uuid,
            "certificate_number": document.certificate_number,
            "integrity_valid": is_valid,
            "original_hash": document.document_hash_sha256,
            "signature_timestamp": (
                document.signature_timestamp.isoformat()
                if document.signature_timestamp
                else None
            ),
            "signer_name": document.signer_name,
        }

    except Exception as e:
        logger.error(f"Error verifying document: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def get_session_audit_trail(session_uuid: str) -> Dict[str, Any]:
    """Get complete audit trail for a signing session."""
    db_session = SessionLocal()
    try:
        signing_session = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.session_uuid == session_uuid)
            .first()
        )

        if not signing_session:
            return {"success": False, "error": "Session not found"}

        audit_logs = (
            db_session.query(SignatureAuditLog)
            .filter(SignatureAuditLog.session_id == signing_session.id)
            .order_by(SignatureAuditLog.timestamp)
            .all()
        )

        return {
            "success": True,
            "session_uuid": session_uuid,
            "audit_trail": [log.to_dict() for log in audit_logs],
            "total_actions": len(audit_logs),
        }

    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


# =============================================================================
# CROA COMPLIANCE
# =============================================================================


def get_croa_compliance_status(client_id: int) -> Dict[str, Any]:
    """Get CROA compliance status for a client."""
    db_session = SessionLocal()
    try:
        tracker = (
            db_session.query(CROAComplianceTracker)
            .filter(CROAComplianceTracker.client_id == client_id)
            .first()
        )

        if not tracker:
            return {
                "success": True,
                "has_tracker": False,
                "rights_disclosure_signed": False,
                "contract_signed": False,
                "work_can_begin": False,
            }

        now = datetime.utcnow()

        # Check if cancellation period is complete
        cancellation_complete = False
        if tracker.cancellation_period_end:
            cancellation_complete = now > tracker.cancellation_period_end
            if cancellation_complete and not tracker.cancellation_period_complete:
                tracker.cancellation_period_complete = True
                tracker.work_can_begin = True
                db_session.commit()

        # Calculate remaining time
        remaining_hours = 0
        if tracker.cancellation_period_end and not cancellation_complete:
            remaining = tracker.cancellation_period_end - now
            remaining_hours = max(0, remaining.total_seconds() / 3600)

        return {
            "success": True,
            "has_tracker": True,
            "rights_disclosure_signed": tracker.rights_disclosure_signed,
            "rights_disclosure_signed_at": (
                tracker.rights_disclosure_signed_at.isoformat()
                if tracker.rights_disclosure_signed_at
                else None
            ),
            "contract_signed": tracker.contract_package_signed,
            "contract_signed_at": (
                tracker.contract_package_signed_at.isoformat()
                if tracker.contract_package_signed_at
                else None
            ),
            "cancellation_period_start": (
                tracker.cancellation_period_start.isoformat()
                if tracker.cancellation_period_start
                else None
            ),
            "cancellation_period_end": (
                tracker.cancellation_period_end.isoformat()
                if tracker.cancellation_period_end
                else None
            ),
            "cancellation_period_complete": tracker.cancellation_period_complete
            or cancellation_complete,
            "remaining_cancellation_hours": round(remaining_hours, 1),
            "client_cancelled": tracker.client_cancelled,
            "cancellation_waived": tracker.cancellation_waived,
            "work_can_begin": tracker.work_can_begin,
        }

    except Exception as e:
        logger.error(f"Error getting CROA status: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def cancel_service_during_croa_period(
    client_id: int,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel service during CROA 3-business-day cancellation period."""
    db_session = SessionLocal()
    try:
        tracker = (
            db_session.query(CROAComplianceTracker)
            .filter(CROAComplianceTracker.client_id == client_id)
            .first()
        )

        if not tracker:
            return {"success": False, "error": "No CROA tracker found for client"}

        now = datetime.utcnow()

        # Check if still within cancellation period
        if tracker.cancellation_period_end and now > tracker.cancellation_period_end:
            return {"success": False, "error": "Cancellation period has ended"}

        if tracker.client_cancelled:
            return {"success": False, "error": "Service has already been cancelled"}

        tracker.client_cancelled = True
        tracker.client_cancelled_at = now
        tracker.cancellation_reason = reason
        tracker.work_can_begin = False

        db_session.commit()

        logger.info(f"Client {client_id} cancelled during CROA period")

        return {
            "success": True,
            "cancelled_at": now.isoformat(),
            "reason": reason,
        }

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error cancelling service: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def waive_cancellation_period(
    client_id: int,
    waiver_signature: str,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Waive CROA cancellation period to begin work immediately."""
    db_session = SessionLocal()
    try:
        tracker = (
            db_session.query(CROAComplianceTracker)
            .filter(CROAComplianceTracker.client_id == client_id)
            .first()
        )

        if not tracker:
            return {"success": False, "error": "No CROA tracker found for client"}

        if tracker.client_cancelled:
            return {"success": False, "error": "Service has been cancelled"}

        now = datetime.utcnow()

        tracker.cancellation_waived = True
        tracker.cancellation_waived_at = now
        tracker.work_can_begin = True

        db_session.commit()

        logger.info(f"Client {client_id} waived cancellation period")

        return {
            "success": True,
            "waived_at": now.isoformat(),
            "work_can_begin": True,
        }

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error waiving cancellation: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


# =============================================================================
# CLIENT HISTORY & MANAGEMENT
# =============================================================================


def get_client_signing_history(client_id: int) -> Dict[str, Any]:
    """Get all signing sessions and documents for a client."""
    db_session = SessionLocal()
    try:
        sessions = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.client_id == client_id)
            .order_by(SignatureSession.created_at.desc())
            .all()
        )

        session_list = []
        for session in sessions:
            documents = [
                {
                    "document_uuid": doc.document_uuid,
                    "document_name": doc.document_name,
                    "status": doc.status,
                    "certificate_number": doc.certificate_number,
                    "signature_timestamp": (
                        doc.signature_timestamp.isoformat()
                        if doc.signature_timestamp
                        else None
                    ),
                }
                for doc in session.documents
            ]

            session_list.append(
                {
                    "session_uuid": session.session_uuid,
                    "status": session.status,
                    "initiated_at": (
                        session.initiated_at.isoformat()
                        if session.initiated_at
                        else None
                    ),
                    "completed_at": (
                        session.completed_at.isoformat()
                        if session.completed_at
                        else None
                    ),
                    "documents": documents,
                }
            )

        return {
            "success": True,
            "client_id": client_id,
            "sessions": session_list,
            "total_sessions": len(session_list),
        }

    except Exception as e:
        logger.error(f"Error getting signing history: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def cancel_signing_session(
    session_uuid: str,
    reason: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> Dict[str, Any]:
    """Cancel a pending signing session."""
    db_session = SessionLocal()
    try:
        signing_session = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.session_uuid == session_uuid)
            .first()
        )

        if not signing_session:
            return {"success": False, "error": "Session not found"}

        if signing_session.status == "completed":
            return {"success": False, "error": "Cannot cancel a completed session"}

        signing_session.status = "cancelled"
        signing_session.updated_at = datetime.utcnow()

        _log_audit_action(
            db_session,
            client_id=signing_session.client_id,
            action="session_cancelled",
            session_id=signing_session.id,
            ip_address=ip_address,
            details={"reason": reason},
        )

        db_session.commit()

        return {"success": True}

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error cancelling session: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


def regenerate_signing_link(session_uuid: str) -> Dict[str, Any]:
    """Regenerate signing link for an expired session."""
    db_session = SessionLocal()
    try:
        signing_session = (
            db_session.query(SignatureSession)
            .filter(SignatureSession.session_uuid == session_uuid)
            .first()
        )

        if not signing_session:
            return {"success": False, "error": "Session not found"}

        if signing_session.status == "completed":
            return {"success": False, "error": "Session already completed"}

        # Generate new UUID and link
        new_uuid = _generate_uuid()
        base_url = _get_base_url()
        new_link = f"{base_url}/esign/{new_uuid}" if base_url else f"/esign/{new_uuid}"
        new_expires = datetime.utcnow() + timedelta(days=SESSION_EXPIRY_DAYS)

        signing_session.session_uuid = new_uuid
        signing_session.signing_link = new_link
        signing_session.expires_at = new_expires
        signing_session.updated_at = datetime.utcnow()

        _log_audit_action(
            db_session,
            client_id=signing_session.client_id,
            action="link_regenerated",
            session_id=signing_session.id,
            details={
                "new_uuid": new_uuid,
                "expires_at": new_expires.isoformat(),
            },
        )

        db_session.commit()

        return {
            "success": True,
            "session_uuid": new_uuid,
            "signing_link": new_link,
            "expires_at": new_expires.isoformat(),
        }

    except Exception as e:
        db_session.rollback()
        logger.error(f"Error regenerating link: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db_session.close()


# =============================================================================
# DOCUMENT TYPES HELPER
# =============================================================================


def list_document_types() -> Dict[str, str]:
    """Get list of supported document types."""
    return DOCUMENT_TYPES.copy()


def get_esign_consent_disclosure() -> str:
    """Get the ESIGN Act consent disclosure HTML."""
    return ESIGN_CONSENT_DISCLOSURE
