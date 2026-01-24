"""
SendCertifiedMail.com SFTP Integration Service
Handles batch upload of dispute letters via SFTP
"""

import csv
import io
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import paramiko  # type: ignore[import-untyped]
from sqlalchemy.orm import Session

# Import from existing codebase
from database import CaseDeadline, DisputeLetter, LetterBatch

# Bureau address lookup dictionary
BUREAU_ADDRESSES = {
    "Equifax": {
        "name": "Equifax Information Services LLC",
        "address1": "P.O. Box 740256",
        "city": "Atlanta",
        "state": "GA",
        "zip": "30374-0256",
    },
    "Experian": {
        "name": "Experian",
        "address1": "P.O. Box 4500",
        "city": "Allen",
        "state": "TX",
        "zip": "75013",
    },
    "TransUnion": {
        "name": "TransUnion LLC",
        "address1": "Consumer Dispute Center",
        "address2": "P.O. Box 2000",
        "city": "Chester",
        "state": "PA",
        "zip": "19016",
    },
}


def get_sftp_connection():
    """Establish SFTP connection to SendCertifiedMail.com"""
    host = os.environ.get("SENDCERTIFIED_SFTP_HOST")
    username = os.environ.get("SENDCERTIFIED_SFTP_USERNAME")
    password = os.environ.get("SENDCERTIFIED_SFTP_PASSWORD")
    port = int(os.environ.get("SENDCERTIFIED_SFTP_PORT", 22))

    if not all([host, username, password]):
        raise ValueError(
            "Missing SendCertified SFTP credentials in environment variables"
        )

    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    return sftp, transport


def upload_batch(letters: List[Dict]) -> Dict:
    """
    Upload batch of letters to SendCertifiedMail.com via SFTP

    Args:
        letters: List of dicts with keys: letter_id, recipient_name, address1,
                 address2, city, state, zip, pdf_path, tracking_number

    Returns:
        Dict with batch_id, letter_count, timestamp
    """
    if not letters:
        raise ValueError("No letters provided for batch upload")

    batch_id = f"BATCH_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.utcnow().isoformat()

    # Create CSV manifest
    csv_buffer = io.StringIO()
    csv_writer = csv.DictWriter(
        csv_buffer,
        fieldnames=[
            "letter_id",
            "recipient_name",
            "address1",
            "address2",
            "city",
            "state",
            "zip",
            "pdf_filename",
            "tracking_number",
        ],
    )
    csv_writer.writeheader()

    for letter in letters:
        csv_writer.writerow(
            {
                "letter_id": letter.get("letter_id"),
                "recipient_name": letter.get("recipient_name"),
                "address1": letter.get("address1"),
                "address2": letter.get("address2", ""),
                "city": letter.get("city"),
                "state": letter.get("state"),
                "zip": letter.get("zip"),
                "pdf_filename": os.path.basename(letter.get("pdf_path") or ""),
                "tracking_number": letter.get("tracking_number", ""),
            }
        )

    csv_content = csv_buffer.getvalue()

    # Upload to SFTP
    sftp, transport = None, None
    try:
        sftp, transport = get_sftp_connection()

        # Create batch directory
        batch_dir = f"/uploads/{batch_id}"
        try:
            sftp.mkdir(batch_dir)
        except IOError:
            pass  # Directory might already exist

        # Upload CSV manifest
        csv_path = f"{batch_dir}/manifest.csv"
        sftp.putfo(io.BytesIO(csv_content.encode("utf-8")), csv_path)

        # Upload PDF files
        for letter in letters:
            pdf_path = letter.get("pdf_path")
            if pdf_path and os.path.exists(pdf_path):
                remote_pdf_path = f"{batch_dir}/{os.path.basename(pdf_path)}"
                sftp.put(pdf_path, remote_pdf_path)

        return {
            "batch_id": batch_id,
            "letter_count": len(letters),
            "timestamp": timestamp,
            "status": "uploaded",
        }

    finally:
        if sftp:
            sftp.close()
        if transport:
            transport.close()


def send_letter_batch(db: Session, letter_ids: List[int]) -> Dict:
    """
    Send batch of dispute letters via SendCertifiedMail.com

    Args:
        db: Database session
        letter_ids: List of DisputeLetter IDs to send

    Returns:
        Dict with batch_id, letter_count, cost_cents, deadline_ids
    """
    from database import Client  # Import here to avoid circular imports

    # Query letters
    letters = db.query(DisputeLetter).filter(DisputeLetter.id.in_(letter_ids)).all()

    if not letters:
        raise ValueError("No letters found with provided IDs")

    # Prepare batch data
    batch_letters = []
    for letter in letters:
        # Get bureau address
        bureau_name: str = (
            str(letter.bureau) if letter.bureau else "Equifax"
        )  # Default to Equifax if not specified
        bureau_info = BUREAU_ADDRESSES.get(bureau_name)

        if not bureau_info:
            continue  # Skip if bureau not found

        batch_letters.append(
            {
                "letter_id": letter.id,
                "recipient_name": bureau_info["name"],
                "address1": bureau_info["address1"],
                "address2": bureau_info.get("address2", ""),
                "city": bureau_info["city"],
                "state": bureau_info["state"],
                "zip": bureau_info["zip"],
                "pdf_path": letter.file_path or "",
                "tracking_number": f"SCM{letter.id:06d}",
            }
        )

    # Upload batch
    result = upload_batch(batch_letters)
    batch_id = result["batch_id"]

    # Calculate cost (SendCertified: $11.00 per letter - includes printing, certified mail, and return receipt electronic)
    cost_per_letter_cents = 1100
    total_cost_cents = len(batch_letters) * cost_per_letter_cents

    # Create LetterBatch record
    letter_batch = LetterBatch(
        batch_id=batch_id,
        letter_count=len(batch_letters),
        cost_cents=total_cost_cents,
        status="uploaded",
        uploaded_at=datetime.utcnow(),
    )
    db.add(letter_batch)

    # Update letters as sent
    now = datetime.utcnow()
    deadline_ids = []

    for letter in letters:
        if letter.id in [bl["letter_id"] for bl in batch_letters]:
            letter.sent_via_letterstream = True  # type: ignore[assignment]
            letter.sent_at = now  # type: ignore[assignment]
            letter.tracking_number = f"SCM{letter.id:06d}"

            # Create 30-day response deadline
            deadline = CaseDeadline(
                client_id=letter.client_id,
                deadline_type="cra_response",
                deadline_date=now + timedelta(days=30),
                description=f"{letter.bureau} Response Deadline - Round {letter.round_number or 1}",
                status="pending",
                related_bureau=letter.bureau,
                round_number=letter.round_number or 1,
            )
            db.add(deadline)
            db.flush()  # Get deadline ID
            deadline_ids.append(deadline.id)

    db.commit()

    return {
        "batch_id": batch_id,
        "letter_count": len(batch_letters),
        "cost_cents": total_cost_cents,
        "deadline_ids": deadline_ids,
        "sent_at": now.isoformat(),
    }


def check_tracking(batch_id: str) -> Dict:
    """
    Check tracking status for a batch from SendCertifiedMail.com

    Args:
        batch_id: The batch ID to check

    Returns:
        Dict with tracking updates for each letter in batch
    """
    sftp, transport = None, None
    try:
        sftp, transport = get_sftp_connection()

        # Download tracking file if it exists
        tracking_path = f"/tracking/{batch_id}_tracking.csv"

        try:
            tracking_file = io.BytesIO()
            sftp.getfo(tracking_path, tracking_file)
            tracking_file.seek(0)

            # Parse tracking CSV
            csv_reader = csv.DictReader(
                io.TextIOWrapper(tracking_file, encoding="utf-8")
            )
            tracking_data = list(csv_reader)

            return {
                "batch_id": batch_id,
                "tracking_available": True,
                "tracking_data": tracking_data,
                "retrieved_at": datetime.utcnow().isoformat(),
            }

        except IOError:
            # Tracking file not yet available
            return {
                "batch_id": batch_id,
                "tracking_available": False,
                "message": "Tracking data not yet available",
                "retrieved_at": datetime.utcnow().isoformat(),
            }

    finally:
        if sftp:
            sftp.close()
        if transport:
            transport.close()


def update_batch_status(db: Session, batch_id: str) -> Optional[LetterBatch]:
    """
    Update batch status based on tracking data

    Args:
        db: Database session
        batch_id: The batch ID to update

    Returns:
        Updated LetterBatch object or None
    """
    batch = db.query(LetterBatch).filter_by(batch_id=batch_id).first()

    if not batch:
        return None

    # Check tracking
    tracking_result = check_tracking(batch_id)

    if tracking_result.get("tracking_available"):
        batch.status = "complete"  # type: ignore[assignment]
        batch.tracking_received_at = datetime.utcnow()  # type: ignore[assignment]
        db.commit()

    return batch


def get_bureau_address(bureau_name: str) -> Dict:
    """
    Get mailing address for a credit bureau

    Args:
        bureau_name: Name of bureau (Equifax, Experian, or TransUnion)

    Returns:
        Dict with address fields
    """
    return BUREAU_ADDRESSES.get(bureau_name, BUREAU_ADDRESSES["Equifax"])
