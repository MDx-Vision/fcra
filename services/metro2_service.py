"""
Metro2 Service for FCRA Litigation Platform.
Detects Metro2 format violations in credit reporting data.
Metro2 is the standard format used by data furnishers to report to credit bureaus.
"""
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


PAYMENT_STATUS_CODES = {
    '0': {'description': 'Current', 'is_derogatory': False},
    '1': {'description': '30-59 days past due', 'is_derogatory': True},
    '2': {'description': '60-89 days past due', 'is_derogatory': True},
    '3': {'description': '90-119 days past due', 'is_derogatory': True},
    '4': {'description': '120-149 days past due', 'is_derogatory': True},
    '5': {'description': '150-179 days past due', 'is_derogatory': True},
    '6': {'description': '180+ days past due', 'is_derogatory': True},
    '7': {'description': 'Bankruptcy', 'is_derogatory': True},
    '8': {'description': 'Foreclosure/Repossession', 'is_derogatory': True},
    '9': {'description': 'Collection/Charge-off', 'is_derogatory': True},
}

REVOLVING_STATUS_CODES = {
    'R0': {'description': 'Current', 'is_derogatory': False},
    'R1': {'description': '30-59 days past due', 'is_derogatory': True},
    'R2': {'description': '60-89 days past due', 'is_derogatory': True},
    'R3': {'description': '90-119 days past due', 'is_derogatory': True},
    'R4': {'description': '120-149 days past due', 'is_derogatory': True},
    'R5': {'description': '150-179 days past due', 'is_derogatory': True},
    'R6': {'description': '180+ days past due', 'is_derogatory': True},
    'R7': {'description': 'Bankruptcy', 'is_derogatory': True},
    'R8': {'description': 'Foreclosure/Repossession', 'is_derogatory': True},
    'R9': {'description': 'Collection/Charge-off', 'is_derogatory': True},
}

PAYMENT_HISTORY_CODES = {
    '0': 'Current/As agreed',
    '1': '30 days late',
    '2': '60 days late',
    '3': '90 days late',
    '4': '120 days late',
    '5': '150 days late',
    '6': '180+ days late',
    '7': 'Bankruptcy',
    '8': 'Foreclosure/Repossession',
    '9': 'Collection/Charge-off',
    'B': 'No data available for period',
    'C': 'Current - account paid satisfactorily',
    'D': 'No payment history maintained',
    'E': 'Account has zero balance and current',
    'G': 'Collection',
    'H': 'Foreclosure completed',
    'J': 'Deferred payment',
    'K': 'Repossession',
    'L': 'Charge-off',
    'X': 'Unknown',
    '-': 'Not reported/No data',
}

ACCOUNT_TYPES = {
    'installment': {'has_credit_limit': False, 'uses_high_credit': True},
    'revolving': {'has_credit_limit': True, 'uses_high_credit': False},
    'mortgage': {'has_credit_limit': False, 'uses_high_credit': True},
    'open': {'has_credit_limit': True, 'uses_high_credit': True},
    'collection': {'has_credit_limit': False, 'uses_high_credit': True},
    'line_of_credit': {'has_credit_limit': True, 'uses_high_credit': False},
    'auto': {'has_credit_limit': False, 'uses_high_credit': True},
    'student_loan': {'has_credit_limit': False, 'uses_high_credit': True},
}

VIOLATION_SEVERITY = {
    'INVALID_STATUS_CODE': 'high',
    'BALANCE_EXCEEDS_LIMIT': 'medium',
    'INVALID_DATE_SEQUENCE': 'high',
    'MISSING_DOFD': 'high',
    'FUTURE_DATE': 'high',
    'STALE_REPORTING': 'medium',
    'REAGING': 'high',
    'BALANCE_ON_CLOSED': 'medium',
    'DUPLICATE_REPORTING': 'high',
    'INVALID_PAYMENT_HISTORY': 'medium',
    'MISSING_ORIGINAL_CREDITOR': 'high',
    'SOL_EXPIRED': 'high',
    'DOFD_MISMATCH': 'high',
    'JUNK_DEBT_BUYER': 'medium',
}

FCRA_SECTIONS = {
    'INVALID_STATUS_CODE': '§ 623(a)(1)(A)',
    'BALANCE_EXCEEDS_LIMIT': '§ 623(a)(1)(A)',
    'INVALID_DATE_SEQUENCE': '§ 623(a)(1)(A)',
    'MISSING_DOFD': '§ 623(a)(6)',
    'FUTURE_DATE': '§ 623(a)(1)(A)',
    'STALE_REPORTING': '§ 623(a)(2)',
    'REAGING': '§ 623(a)(6)',
    'BALANCE_ON_CLOSED': '§ 623(a)(1)(A)',
    'DUPLICATE_REPORTING': '§ 623(a)(1)(B)',
    'INVALID_PAYMENT_HISTORY': '§ 623(a)(1)(A)',
    'MISSING_ORIGINAL_CREDITOR': '§ 623(a)(1)(A)',
    'SOL_EXPIRED': '§ 605(a)',
    'DOFD_MISMATCH': '§ 623(a)(6)',
    'JUNK_DEBT_BUYER': '§ 623(a)(1)(A)',
}

FCRA_DESCRIPTIONS = {
    '§ 623(a)(1)(A)': 'Duty to provide accurate information',
    '§ 623(a)(1)(B)': 'Duty to refrain from reporting incomplete information',
    '§ 623(a)(2)': 'Duty to correct and update information',
    '§ 623(a)(6)': 'Duties regarding date of first delinquency',
    '§ 605(a)': 'Information excluded from consumer reports',
    '§ 611': 'Dispute procedures',
}

STATE_SOL_PERIODS = {
    'AL': 6, 'AK': 3, 'AZ': 6, 'AR': 5, 'CA': 4, 'CO': 6, 'CT': 6, 'DE': 3,
    'FL': 5, 'GA': 6, 'HI': 6, 'ID': 5, 'IL': 5, 'IN': 6, 'IA': 5, 'KS': 5,
    'KY': 5, 'LA': 3, 'ME': 6, 'MD': 3, 'MA': 6, 'MI': 6, 'MN': 6, 'MS': 3,
    'MO': 5, 'MT': 5, 'NE': 5, 'NV': 6, 'NH': 3, 'NJ': 6, 'NM': 6, 'NY': 6,
    'NC': 3, 'ND': 6, 'OH': 6, 'OK': 5, 'OR': 6, 'PA': 4, 'RI': 10, 'SC': 3,
    'SD': 6, 'TN': 6, 'TX': 4, 'UT': 6, 'VT': 6, 'VA': 5, 'WA': 6, 'WV': 10,
    'WI': 6, 'WY': 8, 'DC': 3
}


def _parse_date(date_value: Any) -> Optional[date]:
    """Parse a date from various formats into a date object."""
    if date_value is None:
        return None
    if isinstance(date_value, date):
        return date_value
    if isinstance(date_value, datetime):
        return date_value.date()
    if isinstance(date_value, str):
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d', '%m/%Y', '%Y%m%d']:
            try:
                return datetime.strptime(date_value, fmt).date()
            except ValueError:
                continue
    return None


def _parse_amount(amount_value: Any) -> Optional[float]:
    """Parse an amount from various formats into a float."""
    if amount_value is None:
        return None
    if isinstance(amount_value, (int, float)):
        return float(amount_value)
    if isinstance(amount_value, str):
        cleaned = amount_value.replace('$', '').replace(',', '').strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def _is_derogatory_status(status: str) -> bool:
    """Check if a payment status code indicates derogatory status."""
    if status in PAYMENT_STATUS_CODES:
        return PAYMENT_STATUS_CODES[status]['is_derogatory']
    if status.upper() in REVOLVING_STATUS_CODES:
        return REVOLVING_STATUS_CODES[status.upper()]['is_derogatory']
    derogatory_chars = ['1', '2', '3', '4', '5', '6', '7', '8', '9', 'G', 'H', 'K', 'L']
    return any(char in status for char in derogatory_chars)


def _get_status_description(status: str) -> str:
    """Get the description for a payment status code."""
    if status in PAYMENT_STATUS_CODES:
        return PAYMENT_STATUS_CODES[status]['description']
    if status.upper() in REVOLVING_STATUS_CODES:
        return REVOLVING_STATUS_CODES[status.upper()]['description']
    return f"Unknown status code: {status}"


def detect_metro2_violations(tradeline_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Detect Metro2 format violations in tradeline data.
    
    Args:
        tradeline_data: Dictionary containing tradeline information:
            - creditor_name: Name of the creditor
            - account_number: Account number (may be partial)
            - date_opened: Date account was opened
            - date_reported: Date of last report to bureau
            - current_balance: Current balance amount
            - high_credit: High credit/original loan amount
            - credit_limit: Credit limit (for revolving accounts)
            - payment_status: Current payment status (0-9 or R1-R9)
            - payment_history: String of monthly payment codes
            - date_of_last_activity: Date of last account activity
            - date_of_first_delinquency: DOFD for derogatory accounts
            - original_creditor: Original creditor (for collections)
            - account_type: Type of account (installment, revolving, etc.)
            - account_status: Open/Closed status
            - bureau: Which bureau reported this (optional)
            - previous_dofd: Previous date of first delinquency (for reaging detection)
    
    Returns:
        List of violation dictionaries containing:
            - violation_type: Type of violation code
            - description: Human-readable description
            - fcra_section: Applicable FCRA section
            - severity: high/medium/low
            - evidence: Supporting evidence for the violation
    """
    violations = []
    today = date.today()
    
    creditor_name = tradeline_data.get('creditor_name', 'Unknown Creditor')
    account_number = tradeline_data.get('account_number', '')
    date_opened = _parse_date(tradeline_data.get('date_opened'))
    date_reported = _parse_date(tradeline_data.get('date_reported'))
    current_balance = _parse_amount(tradeline_data.get('current_balance'))
    high_credit = _parse_amount(tradeline_data.get('high_credit'))
    credit_limit = _parse_amount(tradeline_data.get('credit_limit'))
    payment_status = str(tradeline_data.get('payment_status', '')).strip()
    payment_history = tradeline_data.get('payment_history', '')
    date_of_last_activity = _parse_date(tradeline_data.get('date_of_last_activity'))
    date_of_first_delinquency = _parse_date(tradeline_data.get('date_of_first_delinquency'))
    original_creditor = tradeline_data.get('original_creditor')
    account_type = tradeline_data.get('account_type', '').lower()
    account_status = tradeline_data.get('account_status', '').lower()
    previous_dofd = _parse_date(tradeline_data.get('previous_dofd'))
    
    status_violation = _check_invalid_status_code(payment_status, payment_history, creditor_name, account_number)
    if status_violation:
        violations.append(status_violation)
    
    balance_violation = _check_balance_exceeds_limit(
        current_balance, credit_limit, high_credit, account_type, creditor_name, account_number
    )
    if balance_violation:
        violations.append(balance_violation)
    
    date_seq_violation = _check_invalid_date_sequence(
        date_opened, date_of_last_activity, date_reported, creditor_name, account_number
    )
    if date_seq_violation:
        violations.append(date_seq_violation)
    
    dofd_violation = _check_missing_dofd(
        payment_status, date_of_first_delinquency, creditor_name, account_number
    )
    if dofd_violation:
        violations.append(dofd_violation)
    
    future_violations = _check_future_dates(
        date_opened, date_reported, date_of_last_activity, date_of_first_delinquency,
        today, creditor_name, account_number
    )
    violations.extend(future_violations)
    
    stale_violation = _check_stale_reporting(
        date_reported, today, creditor_name, account_number
    )
    if stale_violation:
        violations.append(stale_violation)
    
    reaging_violation = _check_reaging(
        date_of_first_delinquency, previous_dofd, creditor_name, account_number
    )
    if reaging_violation:
        violations.append(reaging_violation)
    
    closed_balance_violation = _check_balance_on_closed(
        account_status, current_balance, creditor_name, account_number
    )
    if closed_balance_violation:
        violations.append(closed_balance_violation)
    
    history_violation = _check_invalid_payment_history(
        payment_history, date_opened, today, creditor_name, account_number
    )
    if history_violation:
        violations.append(history_violation)
    
    logger.info(f"Detected {len(violations)} Metro2 violations for {creditor_name} (Account: {account_number})")
    return violations


def _check_invalid_status_code(
    payment_status: str, 
    payment_history: str, 
    creditor_name: str,
    account_number: str
) -> Optional[Dict[str, Any]]:
    """Check if payment status matches payment history."""
    if not payment_status or not payment_history:
        return None
    
    recent_history = payment_history[:12] if len(payment_history) >= 12 else payment_history
    if not recent_history:
        return None
    
    most_recent = recent_history[0] if recent_history else ''
    
    status_num = payment_status[-1] if payment_status else ''
    
    if status_num.isdigit() and most_recent.isdigit():
        if status_num != most_recent:
            if int(status_num) > 0 and most_recent == '0':
                return {
                    'violation_type': 'INVALID_STATUS_CODE',
                    'description': f"Payment status code '{payment_status}' ({_get_status_description(payment_status)}) "
                                   f"conflicts with payment history showing current status. The current payment status "
                                   f"indicates delinquency but the most recent payment history shows the account is current.",
                    'fcra_section': FCRA_SECTIONS['INVALID_STATUS_CODE'],
                    'severity': VIOLATION_SEVERITY['INVALID_STATUS_CODE'],
                    'evidence': {
                        'creditor_name': creditor_name,
                        'account_number': account_number,
                        'payment_status': payment_status,
                        'payment_history': payment_history[:24],
                        'most_recent_history': most_recent,
                        'status_description': _get_status_description(payment_status),
                        'metro2_field': 'Payment Rating / Payment History Profile',
                    }
                }
    return None


def _check_balance_exceeds_limit(
    current_balance: Optional[float],
    credit_limit: Optional[float],
    high_credit: Optional[float],
    account_type: str,
    creditor_name: str,
    account_number: str
) -> Optional[Dict[str, Any]]:
    """Check if current balance exceeds credit limit (for revolving accounts)."""
    if account_type not in ['revolving', 'line_of_credit', 'open']:
        return None
    
    if current_balance is None or current_balance <= 0:
        return None
    
    limit_to_check = credit_limit if credit_limit and credit_limit > 0 else high_credit
    
    if limit_to_check is None or limit_to_check <= 0:
        return None
    
    overage_percent = ((current_balance - limit_to_check) / limit_to_check) * 100
    
    if current_balance > limit_to_check and overage_percent > 5:
        return {
            'violation_type': 'BALANCE_EXCEEDS_LIMIT',
            'description': f"Current balance (${current_balance:,.2f}) exceeds credit limit (${limit_to_check:,.2f}) "
                           f"by {overage_percent:.1f}% without explanation. Metro2 format requires accurate balance "
                           f"reporting relative to credit limits.",
            'fcra_section': FCRA_SECTIONS['BALANCE_EXCEEDS_LIMIT'],
            'severity': VIOLATION_SEVERITY['BALANCE_EXCEEDS_LIMIT'],
            'evidence': {
                'creditor_name': creditor_name,
                'account_number': account_number,
                'current_balance': current_balance,
                'credit_limit': limit_to_check,
                'overage_amount': current_balance - limit_to_check,
                'overage_percent': round(overage_percent, 1),
                'account_type': account_type,
                'metro2_field': 'Current Balance / Credit Limit',
            }
        }
    return None


def _check_invalid_date_sequence(
    date_opened: Optional[date],
    date_of_last_activity: Optional[date],
    date_reported: Optional[date],
    creditor_name: str,
    account_number: str
) -> Optional[Dict[str, Any]]:
    """Check for invalid date sequences."""
    if not date_opened:
        return None
    
    if date_of_last_activity and date_of_last_activity < date_opened:
        return {
            'violation_type': 'INVALID_DATE_SEQUENCE',
            'description': f"Date of last activity ({date_of_last_activity}) is before date opened ({date_opened}). "
                           f"This is logically impossible and indicates a Metro2 format violation.",
            'fcra_section': FCRA_SECTIONS['INVALID_DATE_SEQUENCE'],
            'severity': VIOLATION_SEVERITY['INVALID_DATE_SEQUENCE'],
            'evidence': {
                'creditor_name': creditor_name,
                'account_number': account_number,
                'date_opened': str(date_opened),
                'date_of_last_activity': str(date_of_last_activity),
                'date_reported': str(date_reported) if date_reported else None,
                'metro2_field': 'Date Opened / Date of Last Activity',
            }
        }
    return None


def _check_missing_dofd(
    payment_status: str,
    date_of_first_delinquency: Optional[date],
    creditor_name: str,
    account_number: str
) -> Optional[Dict[str, Any]]:
    """Check for missing date of first delinquency on derogatory accounts."""
    if not _is_derogatory_status(payment_status):
        return None
    
    if date_of_first_delinquency is None:
        return {
            'violation_type': 'MISSING_DOFD',
            'description': f"Account shows derogatory status ({_get_status_description(payment_status)}) but "
                           f"date of first delinquency is not reported. Per FCRA § 623(a)(6), furnishers must report "
                           f"the DOFD for any account placed for collection, charged-off, or subject to similar action.",
            'fcra_section': FCRA_SECTIONS['MISSING_DOFD'],
            'severity': VIOLATION_SEVERITY['MISSING_DOFD'],
            'evidence': {
                'creditor_name': creditor_name,
                'account_number': account_number,
                'payment_status': payment_status,
                'status_description': _get_status_description(payment_status),
                'date_of_first_delinquency': None,
                'metro2_field': 'Date of First Delinquency',
            }
        }
    return None


def _check_future_dates(
    date_opened: Optional[date],
    date_reported: Optional[date],
    date_of_last_activity: Optional[date],
    date_of_first_delinquency: Optional[date],
    today: date,
    creditor_name: str,
    account_number: str
) -> List[Dict[str, Any]]:
    """Check for any future dates."""
    violations = []
    
    date_fields = [
        ('date_opened', date_opened, 'Date Opened'),
        ('date_reported', date_reported, 'Date Reported'),
        ('date_of_last_activity', date_of_last_activity, 'Date of Last Activity'),
        ('date_of_first_delinquency', date_of_first_delinquency, 'Date of First Delinquency'),
    ]
    
    for field_name, field_value, field_display in date_fields:
        if field_value and field_value > today:
            violations.append({
                'violation_type': 'FUTURE_DATE',
                'description': f"{field_display} ({field_value}) is in the future. Credit reporting cannot include "
                               f"dates that have not yet occurred.",
                'fcra_section': FCRA_SECTIONS['FUTURE_DATE'],
                'severity': VIOLATION_SEVERITY['FUTURE_DATE'],
                'evidence': {
                    'creditor_name': creditor_name,
                    'account_number': account_number,
                    'field_name': field_name,
                    'field_value': str(field_value),
                    'current_date': str(today),
                    'days_in_future': (field_value - today).days,
                    'metro2_field': field_display,
                }
            })
    
    return violations


def _check_stale_reporting(
    date_reported: Optional[date],
    today: date,
    creditor_name: str,
    account_number: str
) -> Optional[Dict[str, Any]]:
    """Check if account reporting is stale (>90 days old)."""
    if not date_reported:
        return None
    
    days_since_report = (today - date_reported).days
    
    if days_since_report > 90:
        return {
            'violation_type': 'STALE_REPORTING',
            'description': f"Account has not been updated in {days_since_report} days (last reported: {date_reported}). "
                           f"Data furnishers have an ongoing duty to report complete and accurate information, "
                           f"and stale data may not reflect the current account status.",
            'fcra_section': FCRA_SECTIONS['STALE_REPORTING'],
            'severity': VIOLATION_SEVERITY['STALE_REPORTING'],
            'evidence': {
                'creditor_name': creditor_name,
                'account_number': account_number,
                'date_reported': str(date_reported),
                'current_date': str(today),
                'days_since_report': days_since_report,
                'metro2_field': 'Date Reported',
            }
        }
    return None


def _check_reaging(
    date_of_first_delinquency: Optional[date],
    previous_dofd: Optional[date],
    creditor_name: str,
    account_number: str
) -> Optional[Dict[str, Any]]:
    """Check for re-aging of date of first delinquency."""
    if not date_of_first_delinquency or not previous_dofd:
        return None
    
    if date_of_first_delinquency > previous_dofd:
        days_reaged = (date_of_first_delinquency - previous_dofd).days
        return {
            'violation_type': 'REAGING',
            'description': f"Date of first delinquency has been changed from {previous_dofd} to a more recent date "
                           f"({date_of_first_delinquency}), effectively re-aging the account by {days_reaged} days. "
                           f"This is a serious FCRA violation that artificially extends the 7-year reporting period.",
            'fcra_section': FCRA_SECTIONS['REAGING'],
            'severity': VIOLATION_SEVERITY['REAGING'],
            'evidence': {
                'creditor_name': creditor_name,
                'account_number': account_number,
                'previous_dofd': str(previous_dofd),
                'current_dofd': str(date_of_first_delinquency),
                'days_reaged': days_reaged,
                'metro2_field': 'Date of First Delinquency',
            }
        }
    return None


def _check_balance_on_closed(
    account_status: str,
    current_balance: Optional[float],
    creditor_name: str,
    account_number: str
) -> Optional[Dict[str, Any]]:
    """Check for balance showing on closed account."""
    closed_indicators = ['closed', 'paid', 'settled', 'transferred']
    is_closed = any(indicator in account_status.lower() for indicator in closed_indicators)
    
    if not is_closed:
        return None
    
    if current_balance and current_balance > 0:
        return {
            'violation_type': 'BALANCE_ON_CLOSED',
            'description': f"Account is marked as '{account_status}' but shows a balance of ${current_balance:,.2f}. "
                           f"Closed accounts paid in full should reflect a zero balance.",
            'fcra_section': FCRA_SECTIONS['BALANCE_ON_CLOSED'],
            'severity': VIOLATION_SEVERITY['BALANCE_ON_CLOSED'],
            'evidence': {
                'creditor_name': creditor_name,
                'account_number': account_number,
                'account_status': account_status,
                'current_balance': current_balance,
                'metro2_field': 'Account Status / Current Balance',
            }
        }
    return None


def _check_invalid_payment_history(
    payment_history: str,
    date_opened: Optional[date],
    today: date,
    creditor_name: str,
    account_number: str
) -> Optional[Dict[str, Any]]:
    """Check if payment history length matches account age."""
    if not payment_history or not date_opened:
        return None
    
    history_length = len(payment_history.replace(' ', '').replace('-', ''))
    
    months_since_opened = (today.year - date_opened.year) * 12 + (today.month - date_opened.month)
    
    if history_length > months_since_opened + 6:
        return {
            'violation_type': 'INVALID_PAYMENT_HISTORY',
            'description': f"Payment history contains {history_length} months of data, but account was only opened "
                           f"{months_since_opened} months ago (on {date_opened}). Payment history cannot exceed "
                           f"the account's actual age.",
            'fcra_section': FCRA_SECTIONS['INVALID_PAYMENT_HISTORY'],
            'severity': VIOLATION_SEVERITY['INVALID_PAYMENT_HISTORY'],
            'evidence': {
                'creditor_name': creditor_name,
                'account_number': account_number,
                'payment_history_length': history_length,
                'account_age_months': months_since_opened,
                'date_opened': str(date_opened),
                'metro2_field': 'Payment History Profile',
            }
        }
    return None


def analyze_collection_account(collection_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Perform specific analysis for collection accounts.
    
    Args:
        collection_data: Dictionary containing collection account information:
            - creditor_name: Name of the collection agency
            - account_number: Collection account number
            - original_creditor: Name of original creditor
            - original_account_number: Original account number
            - original_dofd: Original date of first delinquency
            - collection_dofd: DOFD reported by collection agency
            - date_opened: Date collection account opened
            - original_balance: Original debt amount
            - current_balance: Current amount claimed
            - last_payment_date: Date of last payment
            - state: State for statute of limitations
            - account_type: Type of original account
            - is_sold_debt: Whether debt was sold to debt buyer
            - purchase_date: Date debt was purchased
    
    Returns:
        List of collection-specific violation dictionaries
    """
    violations = []
    today = date.today()
    
    creditor_name = collection_data.get('creditor_name', 'Unknown Collection Agency')
    account_number = collection_data.get('account_number', '')
    original_creditor = collection_data.get('original_creditor')
    original_dofd = _parse_date(collection_data.get('original_dofd'))
    collection_dofd = _parse_date(collection_data.get('collection_dofd'))
    date_opened = _parse_date(collection_data.get('date_opened'))
    last_payment_date = _parse_date(collection_data.get('last_payment_date'))
    state = collection_data.get('state', '').upper()
    is_sold_debt = collection_data.get('is_sold_debt', False)
    
    if not original_creditor or original_creditor.strip() == '':
        violations.append({
            'violation_type': 'MISSING_ORIGINAL_CREDITOR',
            'description': f"Collection account does not report the original creditor. Metro2 format requires "
                           f"collection agencies to identify the original creditor from whom the debt originated.",
            'fcra_section': FCRA_SECTIONS['MISSING_ORIGINAL_CREDITOR'],
            'severity': VIOLATION_SEVERITY['MISSING_ORIGINAL_CREDITOR'],
            'evidence': {
                'creditor_name': creditor_name,
                'account_number': account_number,
                'original_creditor': original_creditor,
                'metro2_field': 'Original Creditor Name',
            }
        })
    
    if original_dofd and collection_dofd:
        if collection_dofd != original_dofd:
            days_diff = abs((collection_dofd - original_dofd).days)
            if days_diff > 30:
                violations.append({
                    'violation_type': 'DOFD_MISMATCH',
                    'description': f"Collection agency reports date of first delinquency as {collection_dofd}, "
                                   f"which differs from the original DOFD of {original_dofd} by {days_diff} days. "
                                   f"The DOFD must remain consistent with the original creditor's records.",
                    'fcra_section': FCRA_SECTIONS['DOFD_MISMATCH'],
                    'severity': VIOLATION_SEVERITY['DOFD_MISMATCH'],
                    'evidence': {
                        'creditor_name': creditor_name,
                        'account_number': account_number,
                        'original_creditor': original_creditor,
                        'original_dofd': str(original_dofd),
                        'collection_dofd': str(collection_dofd),
                        'days_difference': days_diff,
                        'metro2_field': 'Date of First Delinquency',
                    }
                })
    
    sol_date = last_payment_date or original_dofd or collection_dofd
    if sol_date and state in STATE_SOL_PERIODS:
        sol_years = STATE_SOL_PERIODS[state]
        sol_expiration = date(sol_date.year + sol_years, sol_date.month, sol_date.day)
        
        if today > sol_expiration:
            violations.append({
                'violation_type': 'SOL_EXPIRED',
                'description': f"This appears to be zombie debt - the {sol_years}-year statute of limitations "
                               f"for {state} expired on {sol_expiration}. While expired debt can still be reported "
                               f"within the 7-year FCRA period, attempting to collect may violate state law.",
                'fcra_section': FCRA_SECTIONS['SOL_EXPIRED'],
                'severity': VIOLATION_SEVERITY['SOL_EXPIRED'],
                'evidence': {
                    'creditor_name': creditor_name,
                    'account_number': account_number,
                    'state': state,
                    'sol_years': sol_years,
                    'last_activity_date': str(sol_date),
                    'sol_expiration': str(sol_expiration),
                    'years_expired': round((today - sol_expiration).days / 365, 1),
                    'metro2_field': 'Collection Account Status',
                }
            })
    
    if is_sold_debt:
        violations.append({
            'violation_type': 'JUNK_DEBT_BUYER',
            'description': f"This debt has been sold to a debt buyer. Junk debt buyers often lack proper documentation "
                           f"to verify the debt. Request complete verification including the original signed agreement, "
                           f"full payment history, and chain of title documentation.",
            'fcra_section': FCRA_SECTIONS['JUNK_DEBT_BUYER'],
            'severity': VIOLATION_SEVERITY['JUNK_DEBT_BUYER'],
            'evidence': {
                'creditor_name': creditor_name,
                'account_number': account_number,
                'original_creditor': original_creditor,
                'is_sold_debt': True,
                'verification_requirements': [
                    'Original signed credit agreement',
                    'Complete payment history from original creditor',
                    'Chain of title/assignment documentation',
                    'Calculation of amount claimed',
                ],
                'metro2_field': 'Account Type / Creditor Classification',
            }
        })
    
    base_violations = detect_metro2_violations(collection_data)
    violations.extend(base_violations)
    
    logger.info(f"Analyzed collection account {creditor_name}: {len(violations)} violations found")
    return violations


def calculate_violation_damages(violations: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate potential damages based on detected violations.
    
    Args:
        violations: List of violation dictionaries from detect_metro2_violations
    
    Returns:
        Dictionary containing:
            - damage_range_low: Low end of potential damages
            - damage_range_high: High end of potential damages
            - per_violation_breakdown: Damages breakdown by violation type
            - willful_violations: Count of likely willful violations
            - negligent_violations: Count of likely negligent violations
            - total_violations: Total number of violations
    """
    if not violations:
        return {
            'damage_range_low': 0,
            'damage_range_high': 0,
            'per_violation_breakdown': [],
            'willful_violations': 0,
            'negligent_violations': 0,
            'total_violations': 0,
            'notes': 'No violations detected'
        }
    
    willful_types = {'REAGING', 'MISSING_DOFD', 'DOFD_MISMATCH', 'SOL_EXPIRED', 'DUPLICATE_REPORTING'}
    
    violation_damages = {
        'INVALID_STATUS_CODE': {'low': 100, 'high': 500},
        'BALANCE_EXCEEDS_LIMIT': {'low': 100, 'high': 300},
        'INVALID_DATE_SEQUENCE': {'low': 200, 'high': 750},
        'MISSING_DOFD': {'low': 500, 'high': 1000},
        'FUTURE_DATE': {'low': 200, 'high': 750},
        'STALE_REPORTING': {'low': 100, 'high': 300},
        'REAGING': {'low': 750, 'high': 1000},
        'BALANCE_ON_CLOSED': {'low': 100, 'high': 500},
        'DUPLICATE_REPORTING': {'low': 500, 'high': 1000},
        'INVALID_PAYMENT_HISTORY': {'low': 100, 'high': 500},
        'MISSING_ORIGINAL_CREDITOR': {'low': 300, 'high': 750},
        'SOL_EXPIRED': {'low': 500, 'high': 1000},
        'DOFD_MISMATCH': {'low': 500, 'high': 1000},
        'JUNK_DEBT_BUYER': {'low': 200, 'high': 500},
    }
    
    total_low = 0
    total_high = 0
    willful_count = 0
    negligent_count = 0
    breakdown = []
    
    for violation in violations:
        v_type = violation.get('violation_type', '')
        severity = violation.get('severity', 'low')
        
        damages = violation_damages.get(v_type, {'low': 100, 'high': 500})
        
        if v_type in willful_types or severity == 'high':
            damages['low'] = int(damages['low'] * 1.5)
            damages['high'] = int(damages['high'] * 1.5)
            willful_count += 1
        else:
            negligent_count += 1
        
        total_low += damages['low']
        total_high += damages['high']
        
        breakdown.append({
            'violation_type': v_type,
            'creditor_name': violation.get('evidence', {}).get('creditor_name', 'Unknown'),
            'fcra_section': violation.get('fcra_section', ''),
            'damage_low': damages['low'],
            'damage_high': damages['high'],
            'is_willful': v_type in willful_types,
            'severity': severity,
        })
    
    return {
        'damage_range_low': total_low,
        'damage_range_high': total_high,
        'damage_range_low_formatted': f"${total_low:,.2f}",
        'damage_range_high_formatted': f"${total_high:,.2f}",
        'per_violation_breakdown': breakdown,
        'willful_violations': willful_count,
        'negligent_violations': negligent_count,
        'total_violations': len(violations),
        'average_per_violation': round((total_low + total_high) / 2 / len(violations), 2) if violations else 0,
        'notes': _generate_damage_notes(willful_count, negligent_count, total_high),
    }


def _generate_damage_notes(willful_count: int, negligent_count: int, total_high: float) -> str:
    """Generate notes explaining the damage calculation."""
    notes = []
    
    if willful_count > 0:
        notes.append(f"Found {willful_count} violation(s) likely to be considered willful, "
                     f"which may allow for statutory damages of $100-$1,000 per violation under 15 U.S.C. § 1681n.")
    
    if negligent_count > 0:
        notes.append(f"Found {negligent_count} violation(s) that may be considered negligent, "
                     f"allowing for actual damages under 15 U.S.C. § 1681o.")
    
    if total_high >= 5000:
        notes.append("Total potential damages exceed $5,000 threshold that may make this case "
                     "attractive for FCRA litigation.")
    
    if willful_count >= 3:
        notes.append("Pattern of willful violations may support punitive damages claim.")
    
    return " ".join(notes) if notes else "Standard violation damages apply."


def generate_metro2_dispute_points(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate specific dispute language for each Metro2 violation.
    
    Args:
        violations: List of violation dictionaries
    
    Returns:
        List of dispute point dictionaries containing:
            - violation_type: Type of violation
            - dispute_header: Header text for dispute letter
            - dispute_body: Body text explaining the violation
            - fcra_citation: Full FCRA citation with explanation
            - metro2_reference: Reference to Metro2 format requirements
            - requested_action: Specific action requested
            - evidence_points: Bullet points of evidence
    """
    dispute_points = []
    
    for violation in violations:
        v_type = violation.get('violation_type', '')
        description = violation.get('description', '')
        fcra_section = violation.get('fcra_section', '')
        evidence = violation.get('evidence', {})
        
        dispute_point = _build_dispute_point(v_type, description, fcra_section, evidence)
        dispute_points.append(dispute_point)
    
    logger.info(f"Generated {len(dispute_points)} dispute points")
    return dispute_points


def _build_dispute_point(
    violation_type: str,
    description: str,
    fcra_section: str,
    evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """Build a complete dispute point for a violation."""
    
    creditor_name = evidence.get('creditor_name', 'the creditor')
    account_number = evidence.get('account_number', 'the referenced account')
    metro2_field = evidence.get('metro2_field', 'Account Information')
    
    templates = {
        'INVALID_STATUS_CODE': {
            'header': 'Payment Status Code Inaccuracy',
            'body': f"The account from {creditor_name} displays a payment status code that is inconsistent "
                    f"with the payment history profile. Specifically, {description}",
            'metro2_ref': "Metro2 Format Guide Section 6.6 - Payment Rating and Payment History Profile "
                          "must be consistent and accurately reflect account status.",
            'action': "Immediately correct the payment status code to accurately reflect the payment history, "
                      "or provide documentary evidence supporting the current status code.",
        },
        'BALANCE_EXCEEDS_LIMIT': {
            'header': 'Balance/Credit Limit Reporting Error',
            'body': f"The account from {creditor_name} reports a current balance that exceeds the credit limit "
                    f"without proper explanation or account indicator. {description}",
            'metro2_ref': "Metro2 Format Guide Section 6.2 - Current Balance and Credit Limit/High Credit "
                          "fields must be accurately reported and logically consistent.",
            'action': "Correct the balance or credit limit to reflect accurate figures, "
                      "or provide documentation explaining the reported over-limit balance.",
        },
        'INVALID_DATE_SEQUENCE': {
            'header': 'Impossible Date Sequence Error',
            'body': f"The account from {creditor_name} contains logically impossible date sequences. {description}",
            'metro2_ref': "Metro2 Format Guide Section 5.0 - All date fields must be logically consistent "
                          "and represent actual account history.",
            'action': "Correct all date fields to reflect accurate, logically consistent dates "
                      "supported by documentary evidence.",
        },
        'MISSING_DOFD': {
            'header': 'Missing Date of First Delinquency',
            'body': f"The account from {creditor_name} reports derogatory status but fails to include "
                    f"the required Date of First Delinquency. {description}",
            'metro2_ref': "Metro2 Format Guide Section 6.11 - Date of First Delinquency is REQUIRED "
                          "for accounts reporting derogatory payment status.",
            'action': "Immediately add the accurate Date of First Delinquency as required by FCRA § 623(a)(6), "
                      "or remove the derogatory status if DOFD cannot be determined.",
        },
        'FUTURE_DATE': {
            'header': 'Future Date Reporting Error',
            'body': f"The account from {creditor_name} contains dates that are in the future, which is impossible. "
                    f"{description}",
            'metro2_ref': "Metro2 Format Guide - All date fields must represent past or present dates; "
                          "future dates are invalid in credit reporting.",
            'action': "Immediately correct all future dates to accurate past dates "
                      "supported by documentary evidence.",
        },
        'STALE_REPORTING': {
            'header': 'Stale/Outdated Account Information',
            'body': f"The account from {creditor_name} has not been updated in an unreasonable time period. "
                    f"{description}",
            'metro2_ref': "Metro2 Format Guide Section 3.0 - Data furnishers should update accounts monthly "
                          "to ensure accuracy and completeness of consumer credit information.",
            'action': "Update this account with current, accurate information, "
                      "or confirm the account status and provide explanation for the reporting delay.",
        },
        'REAGING': {
            'header': 'Illegal Re-aging of Account',
            'body': f"The account from {creditor_name} shows evidence of illegal re-aging - the Date of First "
                    f"Delinquency has been changed to a more recent date. {description}",
            'metro2_ref': "Metro2 Format Guide Section 6.11 - Date of First Delinquency must remain static "
                          "and reflect the original delinquency date. Re-aging is a serious violation.",
            'action': "Immediately restore the original Date of First Delinquency and correct the reporting period, "
                      "or delete this tradeline if the correct DOFD cannot be determined.",
        },
        'BALANCE_ON_CLOSED': {
            'header': 'Balance Shown on Closed Account',
            'body': f"The account from {creditor_name} is reported as closed but shows a remaining balance. "
                    f"{description}",
            'metro2_ref': "Metro2 Format Guide Section 6.2 and 6.5 - Account Status and Current Balance "
                          "must be consistent. Closed/paid accounts should reflect zero balance.",
            'action': "Correct the balance to zero if account is paid and closed, "
                      "or correct the account status if a balance remains.",
        },
        'DUPLICATE_REPORTING': {
            'header': 'Duplicate Account Reporting',
            'body': f"The account from {creditor_name} appears to be reported multiple times or by entities "
                    f"without proper authority. {description}",
            'metro2_ref': "Metro2 Format Guide Section 4.0 - Each account should be reported only once "
                          "by the entity with current ownership or servicing rights.",
            'action': "Remove duplicate tradelines and ensure only the current account holder reports this debt.",
        },
        'INVALID_PAYMENT_HISTORY': {
            'header': 'Payment History Length Inconsistency',
            'body': f"The account from {creditor_name} shows payment history that is inconsistent with the "
                    f"account age. {description}",
            'metro2_ref': "Metro2 Format Guide Section 6.6 - Payment History Profile length should not exceed "
                          "the actual account age in months.",
            'action': "Correct the payment history profile to accurately reflect the account's actual age.",
        },
        'MISSING_ORIGINAL_CREDITOR': {
            'header': 'Missing Original Creditor Information',
            'body': f"The collection account from {creditor_name} fails to report the original creditor "
                    f"from whom the debt originated. {description}",
            'metro2_ref': "Metro2 Format Guide Section 6.4 - Collection agencies must report the "
                          "Original Creditor Name field for all purchased or placed accounts.",
            'action': "Add the complete original creditor name, or delete this tradeline if the original "
                      "creditor cannot be verified.",
        },
        'SOL_EXPIRED': {
            'header': 'Statute of Limitations Expired - Zombie Debt',
            'body': f"The collection account from {creditor_name} represents debt where the statute of "
                    f"limitations has expired. {description}",
            'metro2_ref': "While this debt may still appear within the FCRA 7-year reporting period, "
                          "collection activity on time-barred debt may violate state consumer protection laws.",
            'action': "Verify the last payment date and state statute of limitations. If the debt is time-barred, "
                      "update account status accordingly and cease collection activity.",
        },
        'DOFD_MISMATCH': {
            'header': 'Date of First Delinquency Mismatch',
            'body': f"The collection account from {creditor_name} reports a Date of First Delinquency that "
                    f"differs from the original creditor's records. {description}",
            'metro2_ref': "Metro2 Format Guide Section 6.11 and FCRA § 623(a)(6) - The DOFD must be "
                          "transferred accurately from the original creditor and remain unchanged.",
            'action': "Correct the Date of First Delinquency to match the original creditor's records, "
                      "or provide documentation proving the reported date is accurate.",
        },
        'JUNK_DEBT_BUYER': {
            'header': 'Debt Buyer Verification Required',
            'body': f"The account from {creditor_name} was purchased from the original creditor. "
                    f"{description} Complete verification documentation is required.",
            'metro2_ref': "Metro2 Format Guide Section 4.0 - Entities reporting purchased debt must maintain "
                          "and be able to provide complete documentation of the debt and chain of title.",
            'action': "Provide complete verification documentation including: original signed agreement, "
                      "complete payment history, and chain of title from original creditor through current owner.",
        },
    }
    
    default_template = {
        'header': 'Metro2 Format Violation',
        'body': description,
        'metro2_ref': "Metro2 Format Guide requires accurate and complete credit reporting.",
        'action': "Investigate and correct this inaccuracy, or provide documentary evidence "
                  "supporting the current reporting.",
    }
    
    template = templates.get(violation_type, default_template)
    
    evidence_points = []
    for key, value in evidence.items():
        if value is not None and key not in ['creditor_name', 'account_number', 'metro2_field']:
            formatted_key = key.replace('_', ' ').title()
            if isinstance(value, (int, float)) and 'amount' in key.lower() or 'balance' in key.lower():
                evidence_points.append(f"{formatted_key}: ${value:,.2f}")
            else:
                evidence_points.append(f"{formatted_key}: {value}")
    
    fcra_description = FCRA_DESCRIPTIONS.get(fcra_section, 'Fair Credit Reporting Act requirement')
    
    return {
        'violation_type': violation_type,
        'dispute_header': template['header'],
        'dispute_body': template['body'],
        'fcra_citation': f"{fcra_section} - {fcra_description}",
        'metro2_reference': template['metro2_ref'],
        'requested_action': template['action'],
        'evidence_points': evidence_points,
        'creditor_name': creditor_name,
        'account_number': account_number,
        'severity': VIOLATION_SEVERITY.get(violation_type, 'medium'),
    }


def check_duplicate_reporting(
    tradelines: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Check for duplicate reporting across multiple tradelines.
    
    Args:
        tradelines: List of all tradelines to check for duplicates
    
    Returns:
        List of duplicate reporting violations
    """
    violations = []
    
    account_map = {}
    
    for tradeline in tradelines:
        original_creditor = tradeline.get('original_creditor', '').lower().strip()
        account_number = tradeline.get('account_number', '').replace('X', '').replace('*', '')[-4:]
        creditor_name = tradeline.get('creditor_name', '')
        high_credit = _parse_amount(tradeline.get('high_credit'))
        
        if not account_number or len(account_number) < 4:
            continue
        
        key = f"{original_creditor}_{account_number}_{high_credit}"
        
        if key in account_map:
            existing = account_map[key]
            
            if existing['creditor_name'].lower() != creditor_name.lower():
                violations.append({
                    'violation_type': 'DUPLICATE_REPORTING',
                    'description': f"The same account appears to be reported by both {existing['creditor_name']} "
                                   f"and {creditor_name}. Only one entity should report this account.",
                    'fcra_section': FCRA_SECTIONS['DUPLICATE_REPORTING'],
                    'severity': VIOLATION_SEVERITY['DUPLICATE_REPORTING'],
                    'evidence': {
                        'first_reporter': existing['creditor_name'],
                        'second_reporter': creditor_name,
                        'account_number': account_number,
                        'original_creditor': original_creditor or 'Not specified',
                        'high_credit': high_credit,
                        'metro2_field': 'Account Identification',
                    }
                })
        else:
            account_map[key] = {
                'creditor_name': creditor_name,
                'tradeline': tradeline,
            }
    
    logger.info(f"Duplicate check: Found {len(violations)} duplicate reporting violations")
    return violations


def get_payment_status_info(status_code: str) -> Dict[str, Any]:
    """
    Get information about a payment status code.
    
    Args:
        status_code: The payment status code (0-9 or R0-R9)
    
    Returns:
        Dictionary with status information
    """
    if status_code in PAYMENT_STATUS_CODES:
        return PAYMENT_STATUS_CODES[status_code]
    if status_code.upper() in REVOLVING_STATUS_CODES:
        return REVOLVING_STATUS_CODES[status_code.upper()]
    return {
        'description': f'Unknown status code: {status_code}',
        'is_derogatory': False
    }


def get_state_sol_period(state: str) -> Optional[int]:
    """
    Get the statute of limitations period for a state.
    
    Args:
        state: Two-letter state code
    
    Returns:
        Number of years for SOL, or None if unknown
    """
    return STATE_SOL_PERIODS.get(state.upper())
