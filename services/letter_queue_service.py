"""
Letter Queue Service - Automated letter suggestion based on escalation triggers

This service monitors dispute items and CRA responses to automatically queue
appropriate advanced letters when trigger conditions are met. Staff can review
and approve suggested letters with one click.

Trigger Types:
- cra_verified: CRA verified disputed item after round 1
- no_cra_response_35_days: No CRA response after 35 days
- collection_disputed: Collection account in dispute
- mortgage_late: Mortgage late payment issue detected
- item_reinserted: Deleted item reinserted without notice
- mov_inadequate: Method of verification received but inadequate
- escalation_stage_change: Dispute escalated to next stage

Letter Types:
- mov_request: Method of Verification Request
- fdcpa_validation: FDCPA Validation Demand
- respa_qwr: RESPA Qualified Written Request
- reg_z_dispute: Reg Z Payment Crediting Dispute
- section_605b_block: §605B Identity Theft Block
- section_623_direct: §623 Direct Furnisher Dispute
- reinsertion_challenge: Reinsertion Challenge Letter
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, cast

from sqlalchemy.orm import Session

LETTER_TYPE_DISPLAY = {
    "mov_request": "Method of Verification Request",
    "fdcpa_validation": "FDCPA Validation Demand",
    "respa_qwr": "RESPA Qualified Written Request",
    "reg_z_dispute": "Reg Z Payment Crediting Dispute",
    "section_605b_block": "§605B Identity Theft Block Request",
    "section_623_direct": "§623 Direct Furnisher Dispute",
    "reinsertion_challenge": "Reinsertion Challenge Letter",
}

TRIGGER_DISPLAY = {
    "cra_verified": "CRA Verified Item After Dispute",
    "no_cra_response_35_days": "No CRA Response After 35 Days",
    "collection_disputed": "Collection Account Disputed",
    "mortgage_late": "Mortgage Late Payment Issue",
    "item_reinserted": "Item Reinserted Without Notice",
    "mov_inadequate": "Inadequate Method of Verification",
    "escalation_stage_change": "Dispute Escalated to Next Stage",
}

TRIGGER_TO_LETTER_MAP = {
    "cra_verified": "mov_request",
    "no_cra_response_35_days": "section_623_direct",
    "collection_disputed": "fdcpa_validation",
    "mortgage_late": "respa_qwr",
    "item_reinserted": "reinsertion_challenge",
    "mov_inadequate": "section_623_direct",
    "escalation_stage_change": "section_623_direct",
}

TRIGGER_PRIORITY = {
    "item_reinserted": "urgent",
    "no_cra_response_35_days": "high",
    "cra_verified": "high",
    "collection_disputed": "high",
    "mortgage_late": "normal",
    "mov_inadequate": "normal",
    "escalation_stage_change": "normal",
}


def queue_letter(
    db: Session,
    client_id: int,
    letter_type: str,
    trigger_type: str,
    trigger_description: str,
    dispute_item_id: Optional[int] = None,
    target_bureau: Optional[str] = None,
    target_creditor: Optional[str] = None,
    target_account: Optional[str] = None,
    letter_data: Optional[Dict] = None,
    priority: str = "normal",
) -> Dict:
    """
    Queue a letter suggestion for staff review

    Returns:
        Dict with success status and queue entry details
    """
    from database import LetterQueue, get_db

    try:
        existing = (
            db.query(LetterQueue)
            .filter_by(
                client_id=client_id,
                letter_type=letter_type,
                trigger_type=trigger_type,
                status="pending",
            )
            .first()
        )

        if existing:
            return {
                "success": False,
                "error": "Similar letter already queued",
                "existing_id": existing.id,
            }

        queue_entry = LetterQueue(
            client_id=client_id,
            dispute_item_id=dispute_item_id,
            letter_type=letter_type,
            trigger_type=trigger_type,
            trigger_description=trigger_description,
            trigger_date=datetime.utcnow(),
            target_bureau=target_bureau,
            target_creditor=target_creditor,
            target_account=target_account,
            letter_data=letter_data or {},
            priority=priority,
            status="pending",
        )

        db.add(queue_entry)
        db.commit()
        db.refresh(queue_entry)

        return {
            "success": True,
            "queue_id": queue_entry.id,
            "letter_type": letter_type,
            "letter_type_display": LETTER_TYPE_DISPLAY.get(letter_type, letter_type),
            "priority": priority,
        }

    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


def check_cra_response_triggers(db: Session, cra_response_id: int) -> List[Dict]:
    """
    Check if a CRA response should trigger letter suggestions

    Triggers checked:
    - CRA verified item → MOV Request
    - Item reinserted → Reinsertion Challenge
    """
    from database import Client, CRAResponse, DisputeItem

    results: List[Dict[str, Any]] = []

    response = db.query(CRAResponse).filter_by(id=cra_response_id).first()
    if not response:
        return results

    client = db.query(Client).filter_by(id=response.client_id).first()
    client_name = client.name if client else "Unknown"

    if response.response_type == "verified":
        dispute_items = (
            db.query(DisputeItem)
            .filter_by(
                client_id=response.client_id,
                bureau=response.bureau,
                status="in_progress",
            )
            .all()
        )

        for item in dispute_items:
            result = queue_letter(
                db=db,
                client_id=int(response.client_id),  # type: ignore[arg-type]
                letter_type="mov_request",
                trigger_type="cra_verified",
                trigger_description=f'{response.bureau} verified {item.creditor_name or "item"} after dispute. Request Method of Verification under §611(a)(6)(B)(iii).',
                dispute_item_id=int(item.id) if item.id else None,  # type: ignore[arg-type]
                target_bureau=str(response.bureau) if response.bureau else None,
                target_creditor=str(item.creditor_name) if item.creditor_name else None,
                target_account=str(item.account_id) if item.account_id else None,
                letter_data={
                    "client_name": client_name,
                    "bureau": response.bureau,
                    "creditor": item.creditor_name,
                    "account": item.account_id,
                    "dispute_round": response.dispute_round,
                    "response_date": (
                        response.response_date.isoformat()
                        if response.response_date
                        else None
                    ),
                },
                priority="high",
            )
            if result.get("success"):
                results.append(result)

    structured_items_list = response.structured_items if response.structured_items else []
    if response.response_type == "reinserted" or (
        structured_items_list
        and any(
            item.get("reinserted")
            for item in structured_items_list
            if isinstance(item, dict)
        )
    ):

        result = queue_letter(
            db=db,
            client_id=int(response.client_id),  # type: ignore[arg-type]
            letter_type="reinsertion_challenge",
            trigger_type="item_reinserted",
            trigger_description=f"Item reinserted by {response.bureau} without proper §611(a)(5)(B) notice. This is a separate FCRA violation.",
            target_bureau=str(response.bureau) if response.bureau else None,
            letter_data={
                "client_name": client_name,
                "bureau": response.bureau,
                "dispute_round": response.dispute_round,
                "response_date": (
                    response.response_date.isoformat()
                    if response.response_date
                    else None
                ),
            },
            priority="urgent",
        )
        if result.get("success"):
            results.append(result)

    return results


def check_no_response_triggers(db: Session, days_threshold: int = 35) -> List[Dict]:
    """
    Check for disputes that haven't received CRA response within threshold

    Default: 35 days (30-day FCRA deadline + 5 day buffer)
    Triggers: §623 Direct Furnisher Dispute
    """
    from database import Client, CRAResponse, DisputeItem

    results: List[Dict[str, Any]] = []
    cutoff_date = datetime.utcnow() - timedelta(days=days_threshold)

    pending_items = (
        db.query(DisputeItem)
        .filter(
            DisputeItem.status == "sent",
            DisputeItem.sent_date != None,
            DisputeItem.sent_date <= cutoff_date.date(),
            DisputeItem.response_date == None,
        )
        .all()
    )

    for item in pending_items:
        has_response = (
            db.query(CRAResponse)
            .filter(
                CRAResponse.client_id == item.client_id,
                CRAResponse.bureau == item.bureau,
                CRAResponse.dispute_round == item.dispute_round,
            )
            .first()
        )

        if not has_response:
            client = db.query(Client).filter_by(id=item.client_id).first()
            client_name = client.name if client else "Unknown"

            days_waiting = (datetime.utcnow().date() - item.sent_date).days

            result = queue_letter(
                db=db,
                client_id=int(item.client_id),  # type: ignore[arg-type]
                letter_type="section_623_direct",
                trigger_type="no_cra_response_35_days",
                trigger_description=f"No response from {item.bureau} after {days_waiting} days. FCRA §611 requires response within 30 days. Escalate to direct furnisher dispute under §623.",
                dispute_item_id=int(item.id) if item.id else None,  # type: ignore[arg-type]
                target_bureau=str(item.bureau) if item.bureau else None,
                target_creditor=str(item.creditor_name) if item.creditor_name else None,
                target_account=str(item.account_id) if item.account_id else None,
                letter_data={
                    "client_name": client_name,
                    "bureau": item.bureau,
                    "creditor": item.creditor_name,
                    "account": item.account_id,
                    "sent_date": item.sent_date.isoformat() if item.sent_date else None,
                    "days_waiting": days_waiting,
                },
                priority="high",
            )
            if result.get("success"):
                results.append(result)

    return results


def check_item_type_triggers(db: Session, dispute_item_id: int) -> List[Dict]:
    """
    Check if a dispute item's type should trigger specific letters

    Triggers:
    - Collection account → FDCPA Validation Demand
    - Mortgage late payment → RESPA QWR
    """
    from database import Client, DisputeItem

    results: List[Dict[str, Any]] = []

    item = db.query(DisputeItem).filter_by(id=dispute_item_id).first()
    if not item:
        return results

    client = db.query(Client).filter_by(id=item.client_id).first()
    client_name = client.name if client else "Unknown"

    if item.item_type == "collection":
        result = queue_letter(
            db=db,
            client_id=int(item.client_id),  # type: ignore[arg-type]
            letter_type="fdcpa_validation",
            trigger_type="collection_disputed",
            trigger_description=f'Collection account from {item.creditor_name or "collector"} disputed. Send FDCPA §1692g validation demand within 30 days of first contact.',
            dispute_item_id=int(item.id) if item.id else None,  # type: ignore[arg-type]
            target_creditor=str(item.creditor_name) if item.creditor_name else None,
            target_account=str(item.account_id) if item.account_id else None,
            letter_data={
                "client_name": client_name,
                "creditor": item.creditor_name,
                "account": item.account_id,
                "bureau": item.bureau,
            },
            priority="high",
        )
        if result.get("success"):
            results.append(result)

    if (
        item.item_type == "late_payment"
        and item.creditor_name
        and any(
            keyword in (item.creditor_name or "").lower()
            for keyword in [
                "mortgage",
                "home loan",
                "fannie",
                "freddie",
                "wells fargo home",
                "bank of america home",
                "chase home",
                "quicken",
                "rocket mortgage",
            ]
        )
    ):
        result = queue_letter(
            db=db,
            client_id=int(item.client_id),  # type: ignore[arg-type]
            letter_type="respa_qwr",
            trigger_type="mortgage_late",
            trigger_description=f"Mortgage late payment disputed on {item.creditor_name}. Send RESPA Qualified Written Request under 12 U.S.C. §2605(e).",
            dispute_item_id=int(item.id) if item.id else None,  # type: ignore[arg-type]
            target_creditor=str(item.creditor_name) if item.creditor_name else None,
            target_account=str(item.account_id) if item.account_id else None,
            letter_data={
                "client_name": client_name,
                "creditor": item.creditor_name,
                "account": item.account_id,
                "bureau": item.bureau,
            },
            priority="normal",
        )
        if result.get("success"):
            results.append(result)

    return results


def check_escalation_triggers(
    db: Session, dispute_item_id: int, new_stage: str
) -> List[Dict]:
    """
    Check if escalation stage change should trigger letters

    Triggers based on new escalation stage:
    - section_623: Queue §623 Direct Furnisher Dispute
    - section_621: Consider CFPB complaint (notification only)
    - section_616_617: Attorney referral notification
    """
    from database import Client, DisputeItem

    results: List[Dict[str, Any]] = []

    item = db.query(DisputeItem).filter_by(id=dispute_item_id).first()
    if not item:
        return results

    client = db.query(Client).filter_by(id=item.client_id).first()
    client_name = client.name if client else "Unknown"

    if new_stage == "section_623" and not item.furnisher_dispute_sent:
        result = queue_letter(
            db=db,
            client_id=int(item.client_id),  # type: ignore[arg-type]
            letter_type="section_623_direct",
            trigger_type="escalation_stage_change",
            trigger_description=f'Dispute escalated to §623. Send direct dispute to furnisher {item.creditor_name or "creditor"} bypassing the CRA.',
            dispute_item_id=int(item.id) if item.id else None,  # type: ignore[arg-type]
            target_creditor=str(item.creditor_name) if item.creditor_name else None,
            target_account=str(item.account_id) if item.account_id else None,
            target_bureau=str(item.bureau) if item.bureau else None,
            letter_data={
                "client_name": client_name,
                "creditor": item.creditor_name,
                "account": item.account_id,
                "bureau": item.bureau,
                "escalation_stage": new_stage,
                "previous_rounds": item.dispute_round,
            },
            priority="normal",
        )
        if result.get("success"):
            results.append(result)

    return results


def get_pending_queue(
    db: Session,
    client_id: Optional[int] = None,
    priority: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    """
    Get pending letter queue entries for staff review
    """
    from database import Client, DisputeItem, LetterQueue

    query = db.query(LetterQueue).filter(LetterQueue.status == "pending")

    if client_id:
        query = query.filter(LetterQueue.client_id == client_id)

    if priority:
        query = query.filter(LetterQueue.priority == priority)

    priority_order = {"urgent": 0, "high": 1, "normal": 2, "low": 3}
    entries = query.order_by(LetterQueue.trigger_date.desc()).limit(limit).all()

    entries = sorted(entries, key=lambda x: priority_order.get(str(x.priority), 2))

    results: List[Dict[str, Any]] = []
    for entry in entries:
        client = db.query(Client).filter_by(id=entry.client_id).first()
        dispute_item = (
            db.query(DisputeItem).filter_by(id=entry.dispute_item_id).first()
            if entry.dispute_item_id
            else None
        )

        results.append(
            {
                "id": entry.id,
                "client_id": entry.client_id,
                "client_name": client.name if client else "Unknown",
                "dispute_item_id": entry.dispute_item_id,
                "letter_type": entry.letter_type,
                "letter_type_display": LETTER_TYPE_DISPLAY.get(
                    str(entry.letter_type), str(entry.letter_type)
                ),
                "trigger_type": entry.trigger_type,
                "trigger_display": TRIGGER_DISPLAY.get(
                    str(entry.trigger_type), str(entry.trigger_type)
                ),
                "trigger_description": entry.trigger_description,
                "trigger_date": (
                    entry.trigger_date.isoformat() if entry.trigger_date else None
                ),
                "target_bureau": entry.target_bureau,
                "target_creditor": entry.target_creditor,
                "target_account": entry.target_account,
                "priority": entry.priority,
                "status": entry.status,
                "letter_data": entry.letter_data or {},
                "created_at": (
                    entry.created_at.isoformat() if entry.created_at else None
                ),
            }
        )

    return results


def get_queue_stats(db: Session) -> Dict:
    """
    Get statistics for the letter queue
    """
    from sqlalchemy import func

    from database import LetterQueue

    total = (
        db.query(func.count(LetterQueue.id))
        .filter(LetterQueue.status == "pending")
        .scalar()
        or 0
    )

    by_priority = {}
    for priority in ["urgent", "high", "normal", "low"]:
        count = (
            db.query(func.count(LetterQueue.id))
            .filter(LetterQueue.status == "pending", LetterQueue.priority == priority)
            .scalar()
            or 0
        )
        by_priority[priority] = count

    by_letter_type = {}
    for letter_type in LETTER_TYPE_DISPLAY.keys():
        count = (
            db.query(func.count(LetterQueue.id))
            .filter(
                LetterQueue.status == "pending", LetterQueue.letter_type == letter_type
            )
            .scalar()
            or 0
        )
        if count > 0:
            by_letter_type[letter_type] = count

    approved_today = (
        db.query(func.count(LetterQueue.id))
        .filter(
            LetterQueue.status == "approved",
            LetterQueue.reviewed_at
            >= datetime.utcnow().replace(hour=0, minute=0, second=0),
        )
        .scalar()
        or 0
    )

    generated_today = (
        db.query(func.count(LetterQueue.id))
        .filter(
            LetterQueue.status == "generated",
            LetterQueue.generated_at
            >= datetime.utcnow().replace(hour=0, minute=0, second=0),
        )
        .scalar()
        or 0
    )

    return {
        "total_pending": total,
        "by_priority": by_priority,
        "by_letter_type": by_letter_type,
        "approved_today": approved_today,
        "generated_today": generated_today,
    }


def approve_queue_entry(
    db: Session, queue_id: int, staff_id: int, notes: Optional[str] = None
) -> Dict:
    """
    Approve a queued letter for generation
    """
    from database import LetterQueue

    entry = db.query(LetterQueue).filter_by(id=queue_id).first()
    if not entry:
        return {"success": False, "error": "Queue entry not found"}

    if entry.status != "pending":
        return {"success": False, "error": f"Entry already {entry.status}"}

    entry.status = "approved"  # type: ignore[assignment]
    entry.reviewed_by_staff_id = staff_id  # type: ignore[assignment]
    entry.reviewed_at = datetime.utcnow()  # type: ignore[assignment]
    entry.action_notes = notes  # type: ignore[assignment]
    entry.updated_at = datetime.utcnow()  # type: ignore[assignment]

    db.commit()

    return {
        "success": True,
        "queue_id": queue_id,
        "status": "approved",
        "letter_type": entry.letter_type,
        "letter_type_display": LETTER_TYPE_DISPLAY.get(
            str(entry.letter_type), str(entry.letter_type)
        ),
    }


def dismiss_queue_entry(db: Session, queue_id: int, staff_id: int, reason: str) -> Dict:
    """
    Dismiss a queued letter suggestion
    """
    from database import LetterQueue

    entry = db.query(LetterQueue).filter_by(id=queue_id).first()
    if not entry:
        return {"success": False, "error": "Queue entry not found"}

    if entry.status != "pending":
        return {"success": False, "error": f"Entry already {entry.status}"}

    entry.status = "dismissed"  # type: ignore[assignment]
    entry.reviewed_by_staff_id = staff_id  # type: ignore[assignment]
    entry.reviewed_at = datetime.utcnow()  # type: ignore[assignment]
    entry.action_notes = reason  # type: ignore[assignment]
    entry.updated_at = datetime.utcnow()  # type: ignore[assignment]

    db.commit()

    return {"success": True, "queue_id": queue_id, "status": "dismissed"}


def bulk_approve(db: Session, queue_ids: List[int], staff_id: int) -> Dict:
    """
    Approve multiple queued letters at once
    """
    from database import LetterQueue

    approved = []
    errors = []

    for queue_id in queue_ids:
        result = approve_queue_entry(db, queue_id, staff_id)
        if result.get("success"):
            approved.append(queue_id)
        else:
            errors.append({"id": queue_id, "error": result.get("error")})

    return {
        "success": len(errors) == 0,
        "approved_count": len(approved),
        "approved_ids": approved,
        "errors": errors,
    }


def run_all_triggers(db: Session) -> Dict:
    """
    Run all trigger checks - typically called by scheduler
    """
    results: Dict[str, Any] = {"no_response_checks": [], "total_queued": 0, "errors": []}

    try:
        no_response_results = check_no_response_triggers(db)
        results["no_response_checks"] = no_response_results
        results["total_queued"] = int(results["total_queued"]) + len(no_response_results)
    except Exception as e:
        cast(List[str], results["errors"]).append(f"No response check error: {str(e)}")

    return results
