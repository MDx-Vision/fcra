"""
FCRA Statute of Limitations Calculator

FCRA § 1681p provides the statute of limitations for FCRA claims:
- 2 years from the date of discovery of the violation, OR
- 5 years from the date the violation occurred
Whichever is EARLIER applies.

This applies to both willful and negligent violations.
Federal FCRA SOL applies nationwide (no state variations for FCRA itself).
"""

from datetime import date, datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any
from dateutil.relativedelta import relativedelta


DISCOVERY_PERIOD_YEARS = 2
OCCURRENCE_PERIOD_YEARS = 5

WARNING_LEVELS = {
    'critical': 30,
    'warning': 90,
    'caution': 180
}


def calculate_sol(
    violation_date: date,
    discovery_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Calculate the Statute of Limitations expiration date for an FCRA claim.
    
    FCRA § 1681p: The earlier of:
    - 2 years from date of discovery
    - 5 years from date the violation occurred
    
    Args:
        violation_date: The date the violation occurred
        discovery_date: The date the violation was discovered (optional)
                       If not provided, defaults to violation_date
    
    Returns:
        Dictionary with SOL calculation details
    """
    if not violation_date:
        return {
            'error': 'Violation date is required',
            'expiration_date': None,
            'remaining_days': None,
            'is_expired': None,
            'warning_level': None
        }
    
    if isinstance(violation_date, datetime):
        violation_date = violation_date.date()
    if discovery_date and isinstance(discovery_date, datetime):
        discovery_date = discovery_date.date()
    
    if not discovery_date:
        discovery_date = violation_date
    
    occurrence_expiration = violation_date + relativedelta(years=OCCURRENCE_PERIOD_YEARS)
    
    discovery_expiration = discovery_date + relativedelta(years=DISCOVERY_PERIOD_YEARS)
    
    if occurrence_expiration <= discovery_expiration:
        expiration_date = occurrence_expiration
        limiting_factor = 'occurrence'
    else:
        expiration_date = discovery_expiration
        limiting_factor = 'discovery'
    
    today = date.today()
    remaining_days = (expiration_date - today).days
    is_expired = remaining_days < 0
    warning_level = get_sol_warning_level(remaining_days)
    
    return {
        'violation_date': violation_date.isoformat() if violation_date else None,
        'discovery_date': discovery_date.isoformat() if discovery_date else None,
        'expiration_date': expiration_date.isoformat(),
        'expiration_date_formatted': expiration_date.strftime('%B %d, %Y'),
        'remaining_days': remaining_days,
        'is_expired': is_expired,
        'warning_level': warning_level,
        'limiting_factor': limiting_factor,
        'occurrence_expiration': occurrence_expiration.isoformat(),
        'discovery_expiration': discovery_expiration.isoformat()
    }


def get_remaining_days(
    violation_date: date,
    discovery_date: Optional[date] = None
) -> int:
    """
    Get the number of days remaining until the SOL expires.
    
    Args:
        violation_date: The date the violation occurred
        discovery_date: The date the violation was discovered (optional)
    
    Returns:
        Number of days remaining (negative if expired)
    """
    result = calculate_sol(violation_date, discovery_date)
    return result.get('remaining_days', 0)


def is_expired(
    violation_date: date,
    discovery_date: Optional[date] = None
) -> bool:
    """
    Check if the SOL for a claim has expired.
    
    Args:
        violation_date: The date the violation occurred
        discovery_date: The date the violation was discovered (optional)
    
    Returns:
        True if the claim has expired, False otherwise
    """
    result = calculate_sol(violation_date, discovery_date)
    return result.get('is_expired', True)


def get_sol_warning_level(remaining_days: int) -> str:
    """
    Get the warning level based on days remaining until SOL expiration.
    
    Warning levels:
    - 'expired': Already expired (negative days)
    - 'critical': Less than 30 days remaining
    - 'warning': Less than 90 days remaining
    - 'caution': Less than 180 days remaining
    - 'ok': 180+ days remaining
    
    Args:
        remaining_days: Number of days until expiration
    
    Returns:
        Warning level string
    """
    if remaining_days is None:
        return 'unknown'
    
    if remaining_days < 0:
        return 'expired'
    elif remaining_days < WARNING_LEVELS['critical']:
        return 'critical'
    elif remaining_days < WARNING_LEVELS['warning']:
        return 'warning'
    elif remaining_days < WARNING_LEVELS['caution']:
        return 'caution'
    else:
        return 'ok'


def get_violations_with_sol_status(db_session, client_id: Optional[int] = None) -> List[Dict]:
    """
    Get all violations with their SOL status.
    
    Args:
        db_session: Database session
        client_id: Optional client ID to filter by
    
    Returns:
        List of violations with SOL status
    """
    from database import Violation, Client, Analysis
    
    query = db_session.query(Violation, Client, Analysis).join(
        Client, Violation.client_id == Client.id
    ).join(
        Analysis, Violation.analysis_id == Analysis.id
    )
    
    if client_id:
        query = query.filter(Violation.client_id == client_id)
    
    results = []
    for violation, client, analysis in query.all():
        sol_info = calculate_sol(
            violation.violation_date or violation.created_at.date(),
            violation.discovery_date
        )
        
        results.append({
            'violation_id': violation.id,
            'client_id': client.id,
            'client_name': client.name,
            'analysis_id': analysis.id,
            'bureau': violation.bureau,
            'account_name': violation.account_name,
            'fcra_section': violation.fcra_section,
            'violation_type': violation.violation_type,
            'is_willful': violation.is_willful,
            'violation_date': violation.violation_date,
            'discovery_date': violation.discovery_date,
            'sol_warning_sent': violation.sol_warning_sent,
            **sol_info
        })
    
    return results


def get_upcoming_expirations(db_session, days: int = 90) -> List[Dict]:
    """
    Get all violations with SOL expiring within the specified number of days.
    
    Args:
        db_session: Database session
        days: Number of days to look ahead (default 90)
    
    Returns:
        List of violations expiring soon, sorted by remaining days
    """
    all_violations = get_violations_with_sol_status(db_session)
    
    upcoming = [
        v for v in all_violations
        if v.get('remaining_days') is not None 
        and 0 <= v['remaining_days'] <= days
    ]
    
    return sorted(upcoming, key=lambda x: x.get('remaining_days', 999))


def get_expired_claims(db_session) -> List[Dict]:
    """
    Get all violations with expired SOL.
    
    Args:
        db_session: Database session
    
    Returns:
        List of expired violations
    """
    all_violations = get_violations_with_sol_status(db_session)
    
    return [v for v in all_violations if v.get('is_expired', False)]


def get_sol_statistics(db_session) -> Dict[str, Any]:
    """
    Get statistics about SOL status across all violations.
    
    Args:
        db_session: Database session
    
    Returns:
        Dictionary with SOL statistics
    """
    all_violations = get_violations_with_sol_status(db_session)
    
    stats = {
        'total': len(all_violations),
        'expired': 0,
        'critical': 0,
        'warning': 0,
        'caution': 0,
        'ok': 0,
        'unknown': 0,
        'expiring_30_days': 0,
        'expiring_60_days': 0,
        'expiring_90_days': 0
    }
    
    for v in all_violations:
        level = v.get('warning_level', 'unknown')
        stats[level] = stats.get(level, 0) + 1
        
        remaining = v.get('remaining_days')
        if remaining is not None and remaining >= 0:
            if remaining <= 30:
                stats['expiring_30_days'] += 1
            if remaining <= 60:
                stats['expiring_60_days'] += 1
            if remaining <= 90:
                stats['expiring_90_days'] += 1
    
    return stats


def check_sol_deadlines(db_session) -> Dict[str, Any]:
    """
    Check all violations for approaching SOL deadlines and create alerts.
    This function should be run periodically (e.g., daily).
    
    Creates CaseDeadline entries for SOL warnings and marks
    sol_warning_sent on violations when alerts are triggered.
    
    Args:
        db_session: Database session
    
    Returns:
        Dictionary with results of the check
    """
    from database import Violation, CaseDeadline, Client
    from datetime import datetime
    
    violations_needing_warning = get_upcoming_expirations(db_session, days=90)
    
    alerts_created = 0
    alerts_skipped = 0
    errors = []
    
    for v_data in violations_needing_warning:
        try:
            violation = db_session.query(Violation).get(v_data['violation_id'])
            if not violation:
                continue
            
            if violation.sol_warning_sent:
                alerts_skipped += 1
                continue
            
            case_query = db_session.query(CaseDeadline).filter(
                CaseDeadline.client_id == v_data['client_id'],
                CaseDeadline.deadline_type == 'sol_expiration',
            )
            
            existing = case_query.first()
            if not existing:
                client = db_session.query(Client).get(v_data['client_id'])
                
                exp_date_str = v_data.get('expiration_date')
                if exp_date_str:
                    exp_date = datetime.fromisoformat(exp_date_str).date()
                else:
                    continue
                
                deadline = CaseDeadline(
                    client_id=v_data['client_id'],
                    deadline_type='sol_expiration',
                    bureau=v_data.get('bureau'),
                    start_date=date.today(),
                    deadline_date=exp_date,
                    days_allowed=v_data.get('remaining_days', 0),
                    status='active'
                )
                db_session.add(deadline)
                
                violation.sol_warning_sent = True
                alerts_created += 1
            else:
                violation.sol_warning_sent = True
                alerts_skipped += 1
                
        except Exception as e:
            errors.append(f"Error processing violation {v_data.get('violation_id')}: {str(e)}")
    
    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        errors.append(f"Database commit error: {str(e)}")
    
    return {
        'violations_checked': len(violations_needing_warning),
        'alerts_created': alerts_created,
        'alerts_skipped': alerts_skipped,
        'errors': errors
    }


def update_violation_sol_dates(
    db_session,
    violation_id: int,
    violation_date: Optional[date] = None,
    discovery_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Update the SOL-related dates for a violation and recalculate expiration.
    
    Args:
        db_session: Database session
        violation_id: ID of the violation to update
        violation_date: New violation date (optional)
        discovery_date: New discovery date (optional)
    
    Returns:
        Updated SOL calculation
    """
    from database import Violation
    
    violation = db_session.query(Violation).get(violation_id)
    if not violation:
        return {'error': 'Violation not found'}
    
    if violation_date:
        if isinstance(violation_date, str):
            violation_date = datetime.fromisoformat(violation_date).date()
        violation.violation_date = violation_date
    
    if discovery_date:
        if isinstance(discovery_date, str):
            discovery_date = datetime.fromisoformat(discovery_date).date()
        violation.discovery_date = discovery_date
    
    v_date = violation.violation_date or violation.created_at.date()
    sol_info = calculate_sol(v_date, violation.discovery_date)
    
    if sol_info.get('expiration_date'):
        violation.sol_expiration_date = datetime.fromisoformat(
            sol_info['expiration_date']
        ).date()
    
    try:
        db_session.commit()
        return {
            'success': True,
            'violation_id': violation_id,
            **sol_info
        }
    except Exception as e:
        db_session.rollback()
        return {'error': str(e)}


def format_sol_for_display(sol_data: Dict) -> Dict:
    """
    Format SOL data for frontend display.
    
    Args:
        sol_data: SOL calculation data
    
    Returns:
        Formatted data for display
    """
    remaining = sol_data.get('remaining_days', 0)
    level = sol_data.get('warning_level', 'unknown')
    
    level_colors = {
        'expired': '#ef4444',
        'critical': '#ef4444',
        'warning': '#f97316',
        'caution': '#eab308',
        'ok': '#22c55e',
        'unknown': '#6b7280'
    }
    
    level_labels = {
        'expired': 'EXPIRED',
        'critical': 'CRITICAL',
        'warning': 'WARNING',
        'caution': 'CAUTION',
        'ok': 'OK',
        'unknown': 'UNKNOWN'
    }
    
    if remaining is not None and remaining >= 0:
        if remaining == 0:
            remaining_text = 'Expires today'
        elif remaining == 1:
            remaining_text = '1 day remaining'
        else:
            remaining_text = f'{remaining} days remaining'
    elif remaining is not None:
        remaining_text = f'Expired {abs(remaining)} days ago'
    else:
        remaining_text = 'Unknown'
    
    return {
        **sol_data,
        'color': level_colors.get(level, '#6b7280'),
        'level_label': level_labels.get(level, 'UNKNOWN'),
        'remaining_text': remaining_text
    }
