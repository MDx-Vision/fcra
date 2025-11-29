"""
Metro 2® Field Validation Module with 2025 Compliance Checks
This module provides comprehensive Metro 2® format validation per CRRG 2025 standards.
Used by AI analysis to detect Metro 2® format violations in credit reports.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
import re
import logging

logger = logging.getLogger(__name__)

ACCOUNT_STATUS_CODES = {
    '05': {
        'description': 'Account transferred to another office',
        'category': 'transferred',
        'is_derogatory': False,
        'requires_dofd': False,
        'crrg_section': '4.2.1'
    },
    '11': {
        'description': 'Current',
        'category': 'current',
        'is_derogatory': False,
        'requires_dofd': False,
        'crrg_section': '4.2.2'
    },
    '13': {
        'description': 'Paid or closed account/zero balance (was derogatory)',
        'category': 'closed_derogatory',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.3'
    },
    '61': {
        'description': 'Paid in full; was a collection account',
        'category': 'paid_collection',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.4'
    },
    '62': {
        'description': 'Paid in full; was a charge-off',
        'category': 'paid_chargeoff',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.5'
    },
    '63': {
        'description': 'Paid in full; was a foreclosure',
        'category': 'paid_foreclosure',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.6'
    },
    '64': {
        'description': 'Paid in full; was a repossession',
        'category': 'paid_repo',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.7'
    },
    '65': {
        'description': 'Paid in full; voluntary surrender',
        'category': 'paid_surrender',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.8'
    },
    '71': {
        'description': 'Purchased by another company',
        'category': 'purchased',
        'is_derogatory': False,
        'requires_dofd': False,
        'crrg_section': '4.2.9'
    },
    '78': {
        'description': 'Foreclosure proceeding started',
        'category': 'foreclosure_started',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.10'
    },
    '80': {
        'description': 'Placed for collection',
        'category': 'collection',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.11'
    },
    '82': {
        'description': 'Charge-off',
        'category': 'chargeoff',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.12'
    },
    '83': {
        'description': 'Bankruptcy Chapter 7',
        'category': 'bankruptcy',
        'is_derogatory': True,
        'requires_dofd': True,
        'bankruptcy_chapter': '7',
        'crrg_section': '4.2.13'
    },
    '84': {
        'description': 'Bankruptcy Chapter 11',
        'category': 'bankruptcy',
        'is_derogatory': True,
        'requires_dofd': True,
        'bankruptcy_chapter': '11',
        'crrg_section': '4.2.14'
    },
    '85': {
        'description': 'Bankruptcy Chapter 12',
        'category': 'bankruptcy',
        'is_derogatory': True,
        'requires_dofd': True,
        'bankruptcy_chapter': '12',
        'crrg_section': '4.2.15'
    },
    '86': {
        'description': 'Bankruptcy Chapter 13',
        'category': 'bankruptcy',
        'is_derogatory': True,
        'requires_dofd': True,
        'bankruptcy_chapter': '13',
        'crrg_section': '4.2.16'
    },
    '87': {
        'description': 'Bankruptcy withdrawn',
        'category': 'bankruptcy_withdrawn',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.17'
    },
    '88': {
        'description': 'Claim filed with government for insured portion of balance',
        'category': 'government_claim',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.18'
    },
    '89': {
        'description': 'Deed in lieu of foreclosure',
        'category': 'deed_in_lieu',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.19'
    },
    '93': {
        'description': 'Account assigned to internal or external collections',
        'category': 'assigned',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.20'
    },
    '94': {
        'description': 'Sold',
        'category': 'sold',
        'is_derogatory': False,
        'requires_dofd': False,
        'crrg_section': '4.2.21'
    },
    '95': {
        'description': 'Account closed at credit grantor\'s request',
        'category': 'closed_grantor',
        'is_derogatory': False,
        'requires_dofd': False,
        'crrg_section': '4.2.22'
    },
    '96': {
        'description': 'Account closed at consumer\'s request',
        'category': 'closed_consumer',
        'is_derogatory': False,
        'requires_dofd': False,
        'crrg_section': '4.2.23'
    },
    '97': {
        'description': 'Unpaid balance reported as loss by credit grantor',
        'category': 'loss',
        'is_derogatory': True,
        'requires_dofd': True,
        'crrg_section': '4.2.24'
    }
}

PAYMENT_RATING_CODES = {
    '0': {
        'description': 'Too new to rate/approved but not used',
        'is_derogatory': False,
        'days_past_due': 0,
        'crrg_section': '5.1.1'
    },
    '': {
        'description': 'Too new to rate/approved but not used',
        'is_derogatory': False,
        'days_past_due': 0,
        'crrg_section': '5.1.1'
    },
    '1': {
        'description': '30-59 days past due',
        'is_derogatory': True,
        'days_past_due': 30,
        'crrg_section': '5.1.2'
    },
    '2': {
        'description': '60-89 days past due',
        'is_derogatory': True,
        'days_past_due': 60,
        'crrg_section': '5.1.3'
    },
    '3': {
        'description': '90-119 days past due',
        'is_derogatory': True,
        'days_past_due': 90,
        'crrg_section': '5.1.4'
    },
    '4': {
        'description': '120-149 days past due',
        'is_derogatory': True,
        'days_past_due': 120,
        'crrg_section': '5.1.5'
    },
    '5': {
        'description': '150-179 days past due',
        'is_derogatory': True,
        'days_past_due': 150,
        'crrg_section': '5.1.6'
    },
    '6': {
        'description': '180+ days past due',
        'is_derogatory': True,
        'days_past_due': 180,
        'crrg_section': '5.1.7'
    },
    'B': {
        'description': 'No payment history available before DOFD',
        'is_derogatory': False,
        'days_past_due': None,
        'special': True,
        'crrg_section': '5.1.8'
    },
    'D': {
        'description': 'No payment history required for this account',
        'is_derogatory': False,
        'days_past_due': None,
        'special': True,
        'crrg_section': '5.1.9'
    },
    'E': {
        'description': 'Zero balance and current',
        'is_derogatory': False,
        'days_past_due': 0,
        'crrg_section': '5.1.10'
    }
}

SPECIAL_COMMENT_CODES = {
    'AC': {
        'description': 'Account closed at consumer\'s request',
        'category': 'closure',
        'consumer_favorable': True,
        'crrg_section': '6.1.1'
    },
    'AM': {
        'description': 'Account acquired from another creditor',
        'category': 'acquisition',
        'consumer_favorable': None,
        'crrg_section': '6.1.2'
    },
    'AU': {
        'description': 'Authorized user',
        'category': 'account_type',
        'consumer_favorable': None,
        'crrg_section': '6.1.3'
    },
    'AV': {
        'description': 'Affected by verified account of identity theft',
        'category': 'fraud',
        'consumer_favorable': True,
        'crrg_section': '6.1.4'
    },
    'AW': {
        'description': 'Account information disputed by consumer under FCRA',
        'category': 'dispute',
        'consumer_favorable': True,
        'crrg_section': '6.1.5'
    },
    'B': {
        'description': 'Closed by consumer',
        'category': 'closure',
        'consumer_favorable': True,
        'crrg_section': '6.1.6'
    },
    'BL': {
        'description': 'Delinquent due to billing dispute',
        'category': 'dispute',
        'consumer_favorable': True,
        'crrg_section': '6.1.7'
    },
    'CH': {
        'description': 'Paid through insurance',
        'category': 'payment',
        'consumer_favorable': True,
        'crrg_section': '6.1.8'
    },
    'CL': {
        'description': 'Credit line closed; not available',
        'category': 'closure',
        'consumer_favorable': None,
        'crrg_section': '6.1.9'
    },
    'CN': {
        'description': 'Account closed; may be opened',
        'category': 'closure',
        'consumer_favorable': None,
        'crrg_section': '6.1.10'
    },
    'CO': {
        'description': 'Account closed; all tradelines transferred',
        'category': 'closure',
        'consumer_favorable': None,
        'crrg_section': '6.1.11'
    },
    'CP': {
        'description': 'Account closed; new account number',
        'category': 'closure',
        'consumer_favorable': None,
        'crrg_section': '6.1.12'
    },
    'CS': {
        'description': 'Child support',
        'category': 'account_type',
        'consumer_favorable': None,
        'crrg_section': '6.1.13'
    },
    'DA': {
        'description': 'Account in dispute under Fair Credit Reporting Act',
        'category': 'dispute',
        'consumer_favorable': True,
        'crrg_section': '6.1.14'
    },
    'DF': {
        'description': 'Account in forbearance',
        'category': 'forbearance',
        'consumer_favorable': True,
        'crrg_section': '6.1.15'
    },
    'DL': {
        'description': 'Deferment - student loan',
        'category': 'deferment',
        'consumer_favorable': True,
        'crrg_section': '6.1.16'
    },
    'EP': {
        'description': 'Account legally paid in full for less than full balance',
        'category': 'settlement',
        'consumer_favorable': False,
        'crrg_section': '6.1.17'
    },
    'IA': {
        'description': 'Recalled for further review',
        'category': 'review',
        'consumer_favorable': None,
        'crrg_section': '6.1.18'
    },
    'IC': {
        'description': 'Inactive account',
        'category': 'status',
        'consumer_favorable': None,
        'crrg_section': '6.1.19'
    },
    'ID': {
        'description': 'Account information disputed by consumer (completeness)',
        'category': 'dispute',
        'consumer_favorable': True,
        'crrg_section': '6.1.20'
    },
    'M': {
        'description': 'Maker',
        'category': 'account_type',
        'consumer_favorable': None,
        'crrg_section': '6.1.21'
    },
    'PD': {
        'description': 'Payment deferred',
        'category': 'deferment',
        'consumer_favorable': True,
        'crrg_section': '6.1.22'
    },
    'PL': {
        'description': 'Paid by co-maker',
        'category': 'payment',
        'consumer_favorable': None,
        'crrg_section': '6.1.23'
    },
    'PM': {
        'description': 'Paid by dealer',
        'category': 'payment',
        'consumer_favorable': None,
        'crrg_section': '6.1.24'
    },
    'PN': {
        'description': 'Paid by primary servicemember on non-military account',
        'category': 'payment',
        'consumer_favorable': None,
        'crrg_section': '6.1.25'
    },
    'Q': {
        'description': 'Joint account',
        'category': 'account_type',
        'consumer_favorable': None,
        'crrg_section': '6.1.26'
    },
    'RA': {
        'description': 'Dispute resolved; consumer disagrees',
        'category': 'dispute',
        'consumer_favorable': False,
        'crrg_section': '6.1.27'
    },
    'RB': {
        'description': 'Dispute resolved; consumer agrees',
        'category': 'dispute',
        'consumer_favorable': True,
        'crrg_section': '6.1.28'
    },
    'S': {
        'description': 'Co-signer',
        'category': 'account_type',
        'consumer_favorable': None,
        'crrg_section': '6.1.29'
    },
    'SP': {
        'description': 'Settled, payment not less than full balance',
        'category': 'settlement',
        'consumer_favorable': True,
        'crrg_section': '6.1.30'
    },
    'V': {
        'description': 'Voluntary surrender',
        'category': 'surrender',
        'consumer_favorable': False,
        'crrg_section': '6.1.31'
    }
}

COMPLIANCE_CONDITION_CODES = {
    'XA': {
        'description': 'Account in disaster (natural/declared disaster)',
        'category': 'disaster',
        'consumer_protection': True,
        'crrg_section': '7.1.1',
        '2025_enhanced': True,
        'requires_end_date': True
    },
    'XB': {
        'description': 'Account in pandemic relief program',
        'category': 'disaster',
        'consumer_protection': True,
        'crrg_section': '7.1.2',
        '2025_enhanced': True,
        'requires_end_date': True
    },
    'XC': {
        'description': 'Account affected by natural disaster - hardship',
        'category': 'disaster',
        'consumer_protection': True,
        'crrg_section': '7.1.3',
        '2025_enhanced': True
    },
    'XD': {
        'description': 'Account affected by civil emergency',
        'category': 'disaster',
        'consumer_protection': True,
        'crrg_section': '7.1.4',
        '2025_enhanced': True
    },
    'XE': {
        'description': 'Account affected by government shutdown',
        'category': 'disaster',
        'consumer_protection': True,
        'crrg_section': '7.1.5',
        '2025_enhanced': True
    },
    'XF': {
        'description': 'Account in forbearance due to COVID-19',
        'category': 'forbearance',
        'consumer_protection': True,
        'crrg_section': '7.1.6',
        '2025_enhanced': True
    },
    'XG': {
        'description': 'Account in CARES Act forbearance',
        'category': 'forbearance',
        'consumer_protection': True,
        'crrg_section': '7.1.7',
        '2025_enhanced': True
    },
    'XH': {
        'description': 'Account in disaster relief modification program',
        'category': 'disaster',
        'consumer_protection': True,
        'crrg_section': '7.1.8',
        '2025_enhanced': True
    },
    'XJ': {
        'description': 'Military active duty',
        'category': 'military',
        'consumer_protection': True,
        'crrg_section': '7.1.9',
        'scra_protected': True,
        '2025_enhanced': True
    },
    'XK': {
        'description': 'SCRA - Servicemembers Civil Relief Act benefits',
        'category': 'military',
        'consumer_protection': True,
        'crrg_section': '7.1.10',
        'scra_protected': True,
        '2025_enhanced': True
    },
    'XL': {
        'description': 'Military Lending Act (MLA) covered borrower',
        'category': 'military',
        'consumer_protection': True,
        'crrg_section': '7.1.11',
        'mla_protected': True,
        '2025_enhanced': True
    },
    'XM': {
        'description': 'Account in forbearance - general',
        'category': 'forbearance',
        'consumer_protection': True,
        'crrg_section': '7.1.12',
        '2025_enhanced': True
    },
    'XN': {
        'description': 'Account in deferment',
        'category': 'deferment',
        'consumer_protection': True,
        'crrg_section': '7.1.13',
        '2025_enhanced': True
    },
    'XO': {
        'description': 'Account in loss mitigation program',
        'category': 'loss_mitigation',
        'consumer_protection': True,
        'crrg_section': '7.1.14',
        '2025_enhanced': True
    },
    'XP': {
        'description': 'Account in partial payment agreement',
        'category': 'payment_plan',
        'consumer_protection': True,
        'crrg_section': '7.1.15',
        '2025_enhanced': True
    },
    'XQ': {
        'description': 'Account in modification/workout program',
        'category': 'modification',
        'consumer_protection': True,
        'crrg_section': '7.1.16',
        '2025_enhanced': True
    },
    'XR': {
        'description': 'Account in repayment plan',
        'category': 'repayment',
        'consumer_protection': True,
        'crrg_section': '7.1.17',
        '2025_enhanced': True
    }
}

COMPLIANCE_2025_REQUIREMENTS = {
    'bankruptcy_notation': {
        'description': 'Enhanced bankruptcy notation requirements for 2025',
        'requirements': [
            'Correct status code (83-87) must be used',
            'Discharge date must be reported when applicable',
            'Proper disposition notation required',
            'Trustee payment tracking for Chapter 13'
        ],
        'effective_date': '2025-01-01',
        'crrg_section': '9.1'
    },
    'disaster_codes': {
        'description': 'Updated disaster code handling for 2025',
        'requirements': [
            'XA-XH codes must include start/end dates',
            'Cannot report delinquency during active accommodation',
            'Documentation of disaster declaration required'
        ],
        'effective_date': '2025-01-01',
        'crrg_section': '9.2'
    },
    'scra_military': {
        'description': 'Enhanced SCRA active duty requirements',
        'requirements': [
            'XJ/XK/XL codes must include deployment dates',
            'Interest rate caps enforced (6% max)',
            'Cannot report negative during active duty protection',
            'MLA protections for covered borrowers'
        ],
        'effective_date': '2025-01-01',
        'crrg_section': '9.3'
    },
    'forbearance_reporting': {
        'description': 'Post-COVID forbearance/deferral reporting',
        'requirements': [
            'XM/XN/XR codes required for forbearance accounts',
            'Cannot show delinquent during approved forbearance',
            'End of forbearance date must be documented',
            'Transition reporting requirements'
        ],
        'effective_date': '2025-01-01',
        'crrg_section': '9.4'
    },
    'medical_debt': {
        'description': 'Medical debt reporting updates for 2025',
        'requirements': [
            'Medical collections under $500 should not be reported',
            'Paid medical debt must be removed within 7 days',
            'Medical debt in payment plan cannot be reported to collections',
            'Veterans medical debt protections'
        ],
        'effective_date': '2024-04-01',
        'crrg_section': '9.5'
    },
    'student_loan': {
        'description': 'Student loan reporting requirements',
        'requirements': [
            'IDR plan status must be accurately reflected',
            'Forbearance periods must use correct codes',
            'Rehabilitation agreements must be tracked'
        ],
        'effective_date': '2025-01-01',
        'crrg_section': '9.6'
    }
}

DOFD_HIERARCHY_RULES = {
    'delinquency_30': {
        'triggers_dofd': False,
        'minimum_days_late': 30,
        'crrg_section': '8.1.1'
    },
    'delinquency_60': {
        'triggers_dofd': False,
        'minimum_days_late': 60,
        'crrg_section': '8.1.2'
    },
    'delinquency_90': {
        'triggers_dofd': False,
        'minimum_days_late': 90,
        'crrg_section': '8.1.3'
    },
    'delinquency_120': {
        'triggers_dofd': False,
        'minimum_days_late': 120,
        'crrg_section': '8.1.4'
    },
    'delinquency_180': {
        'triggers_dofd': True,
        'minimum_days_late': 180,
        'crrg_section': '8.1.5',
        'rule': 'DOFD should be set when account reaches 180 days delinquent if not previously set'
    },
    'chargeoff': {
        'triggers_dofd': True,
        'status_code': '82',
        'crrg_section': '8.1.6',
        'rule': 'DOFD must be set at or before charge-off'
    },
    'collection': {
        'triggers_dofd': True,
        'status_code': '80',
        'crrg_section': '8.1.7',
        'rule': 'DOFD from original creditor must be carried forward to collection'
    },
    'sold_account': {
        'triggers_dofd': True,
        'status_code': '94',
        'crrg_section': '8.1.8',
        'rule': 'DOFD must be preserved when account is sold'
    },
    'bankruptcy': {
        'triggers_dofd': True,
        'status_codes': ['83', '84', '85', '86'],
        'crrg_section': '8.1.9',
        'rule': 'Bankruptcy filing date becomes relevant but original DOFD should be preserved'
    }
}

STATUS_PAYMENT_COMPATIBILITY = {
    '11': ['0', '', 'E'],
    '05': ['0', '', 'B', 'D', 'E'],
    '13': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '61': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '62': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '63': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '64': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '65': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '71': ['0', '', 'B', 'D', 'E', '1', '2', '3', '4', '5', '6'],
    '78': ['1', '2', '3', '4', '5', '6', 'B', 'D'],
    '80': ['1', '2', '3', '4', '5', '6', 'B', 'D'],
    '82': ['1', '2', '3', '4', '5', '6', 'B', 'D'],
    '83': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '84': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '85': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '86': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '87': ['0', '', '1', '2', '3', '4', '5', '6', 'B', 'D'],
    '88': ['1', '2', '3', '4', '5', '6', 'B', 'D'],
    '89': ['1', '2', '3', '4', '5', '6', 'B', 'D'],
    '93': ['1', '2', '3', '4', '5', '6', 'B', 'D'],
    '94': ['0', '', 'B', 'D', 'E', '1', '2', '3', '4', '5', '6'],
    '95': ['0', '', 'B', 'D', 'E'],
    '96': ['0', '', 'B', 'D', 'E'],
    '97': ['1', '2', '3', '4', '5', '6', 'B', 'D']
}

BANKRUPTCY_REQUIREMENTS_2025 = {
    '83': {
        'chapter': '7',
        'max_reporting_years': 10,
        'requires_filing_date': True,
        'requires_discharge_date': False,
        'requires_case_number': True,
        'crrg_section': '9.1.1'
    },
    '84': {
        'chapter': '11',
        'max_reporting_years': 7,
        'requires_filing_date': True,
        'requires_discharge_date': True,
        'requires_case_number': True,
        'crrg_section': '9.1.2'
    },
    '85': {
        'chapter': '12',
        'max_reporting_years': 7,
        'requires_filing_date': True,
        'requires_discharge_date': True,
        'requires_case_number': True,
        'crrg_section': '9.1.3'
    },
    '86': {
        'chapter': '13',
        'max_reporting_years': 7,
        'requires_filing_date': True,
        'requires_discharge_date': True,
        'requires_case_number': True,
        'requires_trustee_payment_tracking': True,
        'crrg_section': '9.1.4'
    }
}

REQUIRED_2025_FIELDS = {
    'all_accounts': [
        'account_number',
        'account_type',
        'date_opened',
        'date_reported',
        'current_balance',
        'account_status',
        'payment_rating'
    ],
    'derogatory_accounts': [
        'date_of_first_delinquency',
        'date_closed',
        'amount_past_due'
    ],
    'collection_accounts': [
        'original_creditor_name',
        'date_of_first_delinquency',
        'original_amount'
    ],
    'bankruptcy_accounts': [
        'bankruptcy_filing_date',
        'bankruptcy_case_number',
        'court_location'
    ],
    'military_accounts': [
        'active_duty_indicator',
        'scra_benefit_date'
    ],
    'forbearance_accounts': [
        'forbearance_start_date',
        'forbearance_end_date',
        'forbearance_type'
    ]
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
        date_value = date_value.strip()
        if not date_value:
            return None
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d', '%m/%Y', '%Y%m%d', '%Y%m']:
            try:
                return datetime.strptime(date_value, fmt).date()
            except ValueError:
                continue
    return None


def validate_account_status(status_code: str) -> dict:
    """
    Validate account status code and return violations.
    
    Args:
        status_code: The Metro 2 account status code (Field 17A)
        
    Returns:
        Dictionary containing validation results and any violations
    """
    violations = []
    status_code = str(status_code).strip().zfill(2) if status_code else ''
    
    if not status_code:
        violations.append({
            'violation_type': 'Metro 2 Account Status Violation',
            'code': '',
            'field': 'Account Status (Field 17A)',
            'issue': 'Account status code is missing or blank',
            'crrg_reference': 'CRRG Section 4.1',
            'recommended_action': 'Account status code is required for all tradelines',
            'severity': 'high'
        })
        return {
            'is_valid': False,
            'violations': violations,
            'status_info': None
        }
    
    if status_code not in ACCOUNT_STATUS_CODES:
        violations.append({
            'violation_type': 'Metro 2 Account Status Violation',
            'code': status_code,
            'field': 'Account Status (Field 17A)',
            'issue': f'Invalid account status code "{status_code}" - not a recognized Metro 2 code',
            'crrg_reference': 'CRRG Section 4.1',
            'recommended_action': 'Use only valid Metro 2 account status codes (05, 11, 13, 61-97)',
            'severity': 'high'
        })
        return {
            'is_valid': False,
            'violations': violations,
            'status_info': None
        }
    
    status_info = ACCOUNT_STATUS_CODES[status_code]
    return {
        'is_valid': True,
        'violations': [],
        'status_info': status_info,
        'code': status_code,
        'description': status_info['description'],
        'is_derogatory': status_info['is_derogatory'],
        'requires_dofd': status_info['requires_dofd']
    }


def validate_payment_pattern(pattern: str, status: str) -> dict:
    """
    Validate payment history pattern matches account status.
    
    Args:
        pattern: Payment history pattern string (e.g., "000000111222")
        status: Account status code
        
    Returns:
        Dictionary containing validation results and any violations
    """
    violations = []
    status = str(status).strip().zfill(2) if status else ''
    pattern = str(pattern).strip() if pattern else ''
    
    if not pattern:
        if status and status in ACCOUNT_STATUS_CODES:
            status_info = ACCOUNT_STATUS_CODES[status]
            if status_info.get('is_derogatory', False):
                violations.append({
                    'violation_type': 'Metro 2 Payment Pattern Violation',
                    'code': status,
                    'field': 'Payment History Profile',
                    'issue': 'Derogatory account status with no payment history pattern',
                    'crrg_reference': 'CRRG Section 5.2',
                    'recommended_action': 'Payment history must be provided for derogatory accounts',
                    'severity': 'medium'
                })
        return {
            'is_valid': len(violations) == 0,
            'violations': violations,
            'pattern_analysis': None
        }
    
    valid_codes = set(PAYMENT_RATING_CODES.keys())
    invalid_codes = []
    for i, code in enumerate(pattern):
        if code not in valid_codes:
            invalid_codes.append({'position': i + 1, 'code': code})
    
    if invalid_codes:
        violations.append({
            'violation_type': 'Metro 2 Payment Pattern Violation',
            'code': '',
            'field': 'Payment History Profile',
            'issue': f'Invalid payment codes in pattern: {invalid_codes}',
            'crrg_reference': 'CRRG Section 5.1',
            'recommended_action': 'Use only valid payment rating codes (0-6, B, D, E, blank)',
            'severity': 'high'
        })
    
    if status and status in STATUS_PAYMENT_COMPATIBILITY:
        compatible_codes = STATUS_PAYMENT_COMPATIBILITY[status]
        most_recent = pattern[0] if pattern else ''
        
        if most_recent and most_recent not in compatible_codes:
            status_desc = ACCOUNT_STATUS_CODES.get(status, {}).get('description', 'Unknown')
            payment_desc = PAYMENT_RATING_CODES.get(most_recent, {}).get('description', 'Unknown')
            
            violations.append({
                'violation_type': 'Metro 2 Payment Pattern Violation',
                'code': status,
                'field': 'Payment History vs Account Status',
                'issue': f'Account status "{status}" ({status_desc}) is incompatible with payment rating "{most_recent}" ({payment_desc})',
                'crrg_reference': 'CRRG Section 5.3',
                'recommended_action': 'Payment history must be consistent with account status',
                'severity': 'high'
            })
    
    if status == '11' and pattern:
        derogatory_in_history = [c for c in pattern[:12] if c in ['1', '2', '3', '4', '5', '6']]
        if derogatory_in_history:
            violations.append({
                'violation_type': 'Metro 2 Payment Pattern Violation',
                'code': status,
                'field': 'Payment History Pattern',
                'issue': f'Current (11) status with recent derogatory payment history: {derogatory_in_history}',
                'crrg_reference': 'CRRG Section 5.4',
                'recommended_action': 'Verify if account has been brought current and status is accurate',
                'severity': 'medium'
            })
    
    if status in ['80', '82', '97']:
        all_current = all(c in ['0', '', 'E'] for c in pattern[:6] if c)
        if all_current:
            status_desc = ACCOUNT_STATUS_CODES.get(status, {}).get('description', 'Unknown')
            violations.append({
                'violation_type': 'Metro 2 Payment Pattern Violation',
                'code': status,
                'field': 'Payment History Pattern',
                'issue': f'{status_desc} status ({status}) but payment history shows all current (0s)',
                'crrg_reference': 'CRRG Section 5.5',
                'recommended_action': 'Status and payment history must be consistent',
                'severity': 'high'
            })
    
    pattern_analysis = {
        'length': len(pattern),
        'most_recent': pattern[0] if pattern else None,
        'derogatory_count': sum(1 for c in pattern if c in ['1', '2', '3', '4', '5', '6']),
        'current_count': sum(1 for c in pattern if c in ['0', 'E']),
        'special_codes': [c for c in pattern if c in ['B', 'D']]
    }
    
    return {
        'is_valid': len(violations) == 0,
        'violations': violations,
        'pattern_analysis': pattern_analysis
    }


def validate_special_comments(comments: list, account_data: dict) -> dict:
    """
    Check for missing or improper special comments.
    
    Args:
        comments: List of special comment codes on the account
        account_data: Dictionary containing account information
        
    Returns:
        Dictionary containing validation results and any violations
    """
    violations = []
    comments = comments or []
    comments = [str(c).strip().upper() for c in comments if c]
    
    for comment in comments:
        if comment and comment not in SPECIAL_COMMENT_CODES:
            violations.append({
                'violation_type': 'Metro 2 Special Comment Violation',
                'code': comment,
                'field': 'Special Comment Code',
                'issue': f'Invalid special comment code "{comment}"',
                'crrg_reference': 'CRRG Section 6.1',
                'recommended_action': 'Use only valid Metro 2 special comment codes',
                'severity': 'medium'
            })
    
    account_status = str(account_data.get('account_status', '')).strip().zfill(2)
    ecoa_code = str(account_data.get('ecoa_code', '')).strip().upper()
    is_disputed = account_data.get('is_disputed', False)
    is_identity_theft = account_data.get('is_identity_theft', False)
    is_closed_by_consumer = account_data.get('is_closed_by_consumer', False)
    is_authorized_user = account_data.get('is_authorized_user', False)
    
    if is_disputed and 'AW' not in comments and 'DA' not in comments and 'ID' not in comments:
        violations.append({
            'violation_type': 'Metro 2 Special Comment Violation',
            'code': '',
            'field': 'Special Comment Code',
            'issue': 'Account is in dispute but missing dispute comment code (AW, DA, or ID)',
            'crrg_reference': 'CRRG Section 6.2',
            'recommended_action': 'Add AW, DA, or ID special comment for disputed accounts',
            'severity': 'high'
        })
    
    if is_identity_theft and 'AV' not in comments:
        violations.append({
            'violation_type': 'Metro 2 Special Comment Violation',
            'code': '',
            'field': 'Special Comment Code',
            'issue': 'Identity theft verified but missing AV comment code',
            'crrg_reference': 'CRRG Section 6.3',
            'recommended_action': 'Add AV special comment for verified identity theft accounts',
            'severity': 'high'
        })
    
    if (is_closed_by_consumer or account_status == '96') and 'AC' not in comments and 'B' not in comments:
        violations.append({
            'violation_type': 'Metro 2 Special Comment Violation',
            'code': '',
            'field': 'Special Comment Code',
            'issue': 'Account closed by consumer but missing AC or B comment code',
            'crrg_reference': 'CRRG Section 6.4',
            'recommended_action': 'Add AC or B special comment when consumer closes account',
            'severity': 'low'
        })
    
    if is_authorized_user and 'AU' not in comments:
        violations.append({
            'violation_type': 'Metro 2 Special Comment Violation',
            'code': '',
            'field': 'Special Comment Code',
            'issue': 'Authorized user account missing AU comment code',
            'crrg_reference': 'CRRG Section 6.5',
            'recommended_action': 'Add AU special comment for authorized user accounts',
            'severity': 'medium'
        })
    
    comment_details = []
    for comment in comments:
        if comment in SPECIAL_COMMENT_CODES:
            comment_details.append({
                'code': comment,
                **SPECIAL_COMMENT_CODES[comment]
            })
    
    return {
        'is_valid': len(violations) == 0,
        'violations': violations,
        'comment_details': comment_details,
        'comment_count': len(comments)
    }


def validate_compliance_conditions(conditions: list, account_data: dict) -> dict:
    """
    Validate XA-XR compliance condition codes are properly applied.
    
    Args:
        conditions: List of compliance condition codes on the account
        account_data: Dictionary containing account information
        
    Returns:
        Dictionary containing validation results and any violations
    """
    violations = []
    conditions = conditions or []
    conditions = [str(c).strip().upper() for c in conditions if c]
    
    for condition in conditions:
        if condition and condition not in COMPLIANCE_CONDITION_CODES:
            violations.append({
                'violation_type': 'Metro 2 Compliance Condition Violation',
                'code': condition,
                'field': 'Compliance Condition Code',
                'issue': f'Invalid compliance condition code "{condition}"',
                'crrg_reference': 'CRRG Section 7.1',
                'recommended_action': 'Use only valid Metro 2 compliance condition codes (XA-XR)',
                'severity': 'medium'
            })
    
    is_military = account_data.get('is_military', False)
    is_active_duty = account_data.get('is_active_duty', False)
    is_forbearance = account_data.get('is_forbearance', False)
    is_disaster_affected = account_data.get('is_disaster_affected', False)
    scra_benefits = account_data.get('scra_benefits', False)
    forbearance_type = account_data.get('forbearance_type', '')
    
    if is_active_duty and 'XJ' not in conditions:
        violations.append({
            'violation_type': 'Metro 2 Compliance Condition Violation',
            'code': '',
            'field': 'Compliance Condition Code',
            'issue': 'Military active duty consumer missing XJ compliance condition code',
            'crrg_reference': 'CRRG Section 7.2 (2025 Enhanced)',
            'recommended_action': 'Add XJ condition code for active duty servicemembers',
            'severity': 'high'
        })
    
    if scra_benefits and 'XK' not in conditions:
        violations.append({
            'violation_type': 'Metro 2 Compliance Condition Violation',
            'code': '',
            'field': 'Compliance Condition Code',
            'issue': 'SCRA benefits active but missing XK compliance condition code',
            'crrg_reference': 'CRRG Section 7.3 (2025 Enhanced)',
            'recommended_action': 'Add XK condition code when SCRA benefits are in effect',
            'severity': 'high'
        })
    
    if is_forbearance:
        forbearance_codes = ['XF', 'XG', 'XM', 'XN', 'XO', 'XP', 'XQ', 'XR']
        has_forbearance_code = any(c in conditions for c in forbearance_codes)
        if not has_forbearance_code:
            violations.append({
                'violation_type': 'Metro 2 Compliance Condition Violation',
                'code': '',
                'field': 'Compliance Condition Code',
                'issue': 'Account in forbearance but missing appropriate compliance condition code',
                'crrg_reference': 'CRRG Section 7.4 (2025 Enhanced)',
                'recommended_action': 'Add appropriate forbearance condition code (XF, XG, XM, XN, XO, XP, XQ, or XR)',
                'severity': 'high'
            })
    
    if is_disaster_affected:
        disaster_codes = ['XA', 'XB', 'XC', 'XD', 'XE', 'XH']
        has_disaster_code = any(c in conditions for c in disaster_codes)
        if not has_disaster_code:
            violations.append({
                'violation_type': 'Metro 2 Compliance Condition Violation',
                'code': '',
                'field': 'Compliance Condition Code',
                'issue': 'Account affected by disaster but missing disaster compliance condition code',
                'crrg_reference': 'CRRG Section 7.5 (2025 Enhanced)',
                'recommended_action': 'Add appropriate disaster condition code (XA-XE or XH)',
                'severity': 'high'
            })
    
    for condition in conditions:
        if condition in COMPLIANCE_CONDITION_CODES:
            cond_info = COMPLIANCE_CONDITION_CODES[condition]
            if cond_info.get('requires_end_date', False):
                if not account_data.get('compliance_end_date'):
                    violations.append({
                        'violation_type': 'Metro 2 Compliance Condition Violation',
                        'code': condition,
                        'field': 'Compliance Condition End Date',
                        'issue': f'Condition code {condition} requires an end date but none provided',
                        'crrg_reference': 'CRRG Section 7.6',
                        'recommended_action': 'Provide end date for time-limited compliance conditions',
                        'severity': 'medium'
                    })
    
    condition_details = []
    for condition in conditions:
        if condition in COMPLIANCE_CONDITION_CODES:
            condition_details.append({
                'code': condition,
                **COMPLIANCE_CONDITION_CODES[condition]
            })
    
    return {
        'is_valid': len(violations) == 0,
        'violations': violations,
        'condition_details': condition_details,
        'has_2025_enhanced': any(
            COMPLIANCE_CONDITION_CODES.get(c, {}).get('2025_enhanced', False) 
            for c in conditions
        ),
        'has_scra_protection': any(
            COMPLIANCE_CONDITION_CODES.get(c, {}).get('scra_protected', False)
            for c in conditions
        )
    }


def validate_dofd_hierarchy(dofd: str, status_changes: list, account_data: dict = None) -> dict:
    """
    Check DOFD follows CRRG 2025 hierarchy rules.
    
    Args:
        dofd: Date of First Delinquency (string or date)
        status_changes: List of status change events with dates
        account_data: Optional dictionary containing additional account information
        
    Returns:
        Dictionary containing validation results and any violations
    """
    violations = []
    account_data = account_data or {}
    
    dofd_date = _parse_date(dofd)
    account_status = str(account_data.get('account_status', '')).strip().zfill(2)
    original_creditor_dofd = _parse_date(account_data.get('original_creditor_dofd'))
    is_collection = account_data.get('is_collection', False) or account_status == '80'
    is_sold = account_data.get('is_sold', False) or account_status == '94'
    is_chargeoff = account_status == '82'
    is_derogatory = account_status in ACCOUNT_STATUS_CODES and ACCOUNT_STATUS_CODES.get(account_status, {}).get('is_derogatory', False)
    
    if is_derogatory and not dofd_date:
        violations.append({
            'violation_type': 'Metro 2 DOFD Violation',
            'code': account_status,
            'field': 'Date of First Delinquency',
            'issue': 'Derogatory account status but DOFD is missing',
            'crrg_reference': 'CRRG Section 8.2',
            'recommended_action': 'DOFD is required for all derogatory accounts per FCRA § 623(a)(6)',
            'severity': 'high'
        })
    
    if (is_collection or is_sold) and original_creditor_dofd:
        if dofd_date and dofd_date != original_creditor_dofd:
            if dofd_date > original_creditor_dofd:
                violations.append({
                    'violation_type': 'Metro 2 DOFD Violation',
                    'code': account_status,
                    'field': 'Date of First Delinquency',
                    'issue': f'Collection/sold account DOFD ({dofd_date}) differs from original creditor DOFD ({original_creditor_dofd}) - possible re-aging',
                    'crrg_reference': 'CRRG Section 8.3',
                    'recommended_action': 'DOFD must be preserved from original creditor and cannot be re-aged',
                    'severity': 'high'
                })
    
    if dofd_date:
        today = date.today()
        seven_year_limit = dofd_date + timedelta(days=7*365 + 180)
        
        if today > seven_year_limit:
            violations.append({
                'violation_type': 'Metro 2 DOFD Violation',
                'code': account_status,
                'field': 'Date of First Delinquency',
                'issue': f'DOFD ({dofd_date}) indicates account is past 7-year reporting limit',
                'crrg_reference': 'CRRG Section 8.4 / FCRA § 605(a)',
                'recommended_action': 'Account should be removed from credit report as it exceeds 7-year limit',
                'severity': 'high'
            })
        
        date_opened = _parse_date(account_data.get('date_opened'))
        if date_opened and dofd_date < date_opened:
            violations.append({
                'violation_type': 'Metro 2 DOFD Violation',
                'code': account_status,
                'field': 'Date of First Delinquency',
                'issue': f'DOFD ({dofd_date}) is before account open date ({date_opened})',
                'crrg_reference': 'CRRG Section 8.5',
                'recommended_action': 'DOFD cannot precede account open date',
                'severity': 'high'
            })
        
        if dofd_date > today:
            violations.append({
                'violation_type': 'Metro 2 DOFD Violation',
                'code': account_status,
                'field': 'Date of First Delinquency',
                'issue': f'DOFD ({dofd_date}) is in the future',
                'crrg_reference': 'CRRG Section 8.6',
                'recommended_action': 'DOFD cannot be a future date',
                'severity': 'high'
            })
    
    if status_changes:
        previous_dofd = None
        for change in sorted(status_changes, key=lambda x: _parse_date(x.get('date')) or date.min):
            change_dofd = _parse_date(change.get('dofd'))
            if previous_dofd and change_dofd:
                if change_dofd > previous_dofd:
                    violations.append({
                        'violation_type': 'Metro 2 DOFD Violation',
                        'code': change.get('status', ''),
                        'field': 'Date of First Delinquency',
                        'issue': f'DOFD changed from {previous_dofd} to {change_dofd} - re-aging detected',
                        'crrg_reference': 'CRRG Section 8.7',
                        'recommended_action': 'DOFD can only move earlier, never later (no re-aging)',
                        'severity': 'high'
                    })
            if change_dofd:
                previous_dofd = change_dofd
    
    return {
        'is_valid': len(violations) == 0,
        'violations': violations,
        'dofd_date': str(dofd_date) if dofd_date else None,
        'is_within_reporting_period': dofd_date and (date.today() <= dofd_date + timedelta(days=7*365 + 180)) if dofd_date else None,
        'days_until_expiration': (dofd_date + timedelta(days=7*365 + 180) - date.today()).days if dofd_date else None
    }


def validate_2025_requirements(account_data: dict) -> dict:
    """
    Check 2025-specific Metro 2 format requirements.
    
    Args:
        account_data: Dictionary containing account information
        
    Returns:
        Dictionary containing validation results and any violations
    """
    violations = []
    account_status = str(account_data.get('account_status', '')).strip().zfill(2)
    
    for field in REQUIRED_2025_FIELDS['all_accounts']:
        if field not in account_data or account_data.get(field) is None or account_data.get(field) == '':
            violations.append({
                'violation_type': 'Metro 2 2025 Compliance Violation',
                'code': '',
                'field': field,
                'issue': f'Required field "{field}" is missing or blank',
                'crrg_reference': 'CRRG 2025 Section 10.1',
                'recommended_action': f'Provide value for required field: {field}',
                'severity': 'medium'
            })
    
    is_derogatory = account_status in ACCOUNT_STATUS_CODES and ACCOUNT_STATUS_CODES.get(account_status, {}).get('is_derogatory', False)
    if is_derogatory:
        for field in REQUIRED_2025_FIELDS['derogatory_accounts']:
            if field not in account_data or account_data.get(field) is None or account_data.get(field) == '':
                violations.append({
                    'violation_type': 'Metro 2 2025 Compliance Violation',
                    'code': account_status,
                    'field': field,
                    'issue': f'Derogatory account missing required field "{field}"',
                    'crrg_reference': 'CRRG 2025 Section 10.2',
                    'recommended_action': f'Provide value for derogatory account field: {field}',
                    'severity': 'high'
                })
    
    is_collection = account_data.get('is_collection', False) or account_status == '80'
    if is_collection:
        for field in REQUIRED_2025_FIELDS['collection_accounts']:
            if field not in account_data or account_data.get(field) is None or account_data.get(field) == '':
                violations.append({
                    'violation_type': 'Metro 2 2025 Compliance Violation',
                    'code': account_status,
                    'field': field,
                    'issue': f'Collection account missing required field "{field}"',
                    'crrg_reference': 'CRRG 2025 Section 10.3',
                    'recommended_action': f'Provide value for collection account field: {field}',
                    'severity': 'high'
                })
    
    is_bankruptcy = account_status in ['83', '84', '85', '86']
    if is_bankruptcy:
        bankruptcy_reqs = BANKRUPTCY_REQUIREMENTS_2025.get(account_status, {})
        for field in REQUIRED_2025_FIELDS['bankruptcy_accounts']:
            if field not in account_data or account_data.get(field) is None or account_data.get(field) == '':
                violations.append({
                    'violation_type': 'Metro 2 2025 Bankruptcy Compliance Violation',
                    'code': account_status,
                    'field': field,
                    'issue': f'Bankruptcy Chapter {bankruptcy_reqs.get("chapter", "?")} account missing required field "{field}"',
                    'crrg_reference': bankruptcy_reqs.get('crrg_section', 'CRRG 2025 Section 9.1'),
                    'recommended_action': f'Provide value for bankruptcy account field: {field}',
                    'severity': 'high'
                })
        
        if account_status == '86':
            if not account_data.get('trustee_payment_tracking'):
                violations.append({
                    'violation_type': 'Metro 2 2025 Bankruptcy Compliance Violation',
                    'code': '86',
                    'field': 'Trustee Payment Tracking',
                    'issue': 'Chapter 13 bankruptcy requires trustee payment tracking per 2025 requirements',
                    'crrg_reference': 'CRRG 2025 Section 9.1.4',
                    'recommended_action': 'Enable trustee payment tracking for Chapter 13 accounts',
                    'severity': 'medium'
                })
    
    is_military = account_data.get('is_military', False) or account_data.get('is_active_duty', False)
    if is_military:
        for field in REQUIRED_2025_FIELDS['military_accounts']:
            if field not in account_data or account_data.get(field) is None or account_data.get(field) == '':
                violations.append({
                    'violation_type': 'Metro 2 2025 Military Compliance Violation',
                    'code': '',
                    'field': field,
                    'issue': f'Military/SCRA account missing required field "{field}"',
                    'crrg_reference': 'CRRG 2025 Section 7.9-7.11',
                    'recommended_action': f'Provide value for military account field: {field}',
                    'severity': 'high'
                })
    
    is_forbearance = account_data.get('is_forbearance', False)
    if is_forbearance:
        for field in REQUIRED_2025_FIELDS['forbearance_accounts']:
            if field not in account_data or account_data.get(field) is None or account_data.get(field) == '':
                violations.append({
                    'violation_type': 'Metro 2 2025 Forbearance Compliance Violation',
                    'code': '',
                    'field': field,
                    'issue': f'Forbearance account missing required field "{field}"',
                    'crrg_reference': 'CRRG 2025 Section 7.12-7.17',
                    'recommended_action': f'Provide value for forbearance account field: {field}',
                    'severity': 'high'
                })
    
    conditions = account_data.get('compliance_conditions', [])
    if conditions:
        for condition in conditions:
            if condition in COMPLIANCE_CONDITION_CODES:
                cond_info = COMPLIANCE_CONDITION_CODES[condition]
                if cond_info.get('2025_enhanced', False):
                    if not account_data.get('condition_effective_date'):
                        violations.append({
                            'violation_type': 'Metro 2 2025 Compliance Condition Violation',
                            'code': condition,
                            'field': 'Condition Effective Date',
                            'issue': f'2025 enhanced condition {condition} requires effective date',
                            'crrg_reference': cond_info.get('crrg_section', 'CRRG 2025'),
                            'recommended_action': 'Provide effective date for 2025 enhanced compliance conditions',
                            'severity': 'medium'
                        })
    
    return {
        'is_valid': len(violations) == 0,
        'violations': violations,
        '2025_compliant': len(violations) == 0,
        'missing_fields': [v['field'] for v in violations if 'missing' in v['issue'].lower()]
    }


def run_full_metro2_validation(accounts: list) -> dict:
    """
    Run all Metro 2 validations on a list of extracted accounts.
    
    Args:
        accounts: List of account dictionaries containing tradeline data
        
    Returns:
        Comprehensive validation results with all violations and compliance score
    """
    all_violations = []
    issues_by_category = {
        'status_codes': 0,
        'payment_patterns': 0,
        'special_comments': 0,
        'compliance_conditions': 0,
        'dofd': 0,
        '2025_requirements': 0
    }
    
    accounts = accounts or []
    total_accounts = len(accounts)
    accounts_with_violations = 0
    
    for idx, account in enumerate(accounts):
        account_violations = []
        account_name = account.get('creditor_name', account.get('account_name', f'Account {idx + 1}'))
        account_number = account.get('account_number', 'Unknown')
        
        status_result = validate_account_status(account.get('account_status', account.get('status_code', '')))
        if not status_result['is_valid']:
            for v in status_result['violations']:
                v['account_name'] = account_name
                v['account_number'] = account_number
                account_violations.append(v)
                issues_by_category['status_codes'] += 1
        
        pattern_result = validate_payment_pattern(
            account.get('payment_history', account.get('payment_pattern', '')),
            account.get('account_status', account.get('status_code', ''))
        )
        if not pattern_result['is_valid']:
            for v in pattern_result['violations']:
                v['account_name'] = account_name
                v['account_number'] = account_number
                account_violations.append(v)
                issues_by_category['payment_patterns'] += 1
        
        comments_result = validate_special_comments(
            account.get('special_comments', account.get('remarks', [])),
            account
        )
        if not comments_result['is_valid']:
            for v in comments_result['violations']:
                v['account_name'] = account_name
                v['account_number'] = account_number
                account_violations.append(v)
                issues_by_category['special_comments'] += 1
        
        conditions_result = validate_compliance_conditions(
            account.get('compliance_conditions', []),
            account
        )
        if not conditions_result['is_valid']:
            for v in conditions_result['violations']:
                v['account_name'] = account_name
                v['account_number'] = account_number
                account_violations.append(v)
                issues_by_category['compliance_conditions'] += 1
        
        dofd_result = validate_dofd_hierarchy(
            account.get('date_of_first_delinquency', account.get('dofd', '')),
            account.get('status_changes', []),
            account
        )
        if not dofd_result['is_valid']:
            for v in dofd_result['violations']:
                v['account_name'] = account_name
                v['account_number'] = account_number
                account_violations.append(v)
                issues_by_category['dofd'] += 1
        
        requirements_result = validate_2025_requirements(account)
        if not requirements_result['is_valid']:
            for v in requirements_result['violations']:
                v['account_name'] = account_name
                v['account_number'] = account_number
                account_violations.append(v)
                issues_by_category['2025_requirements'] += 1
        
        if account_violations:
            accounts_with_violations += 1
            all_violations.extend(account_violations)
    
    total_violations = len(all_violations)
    high_severity = sum(1 for v in all_violations if v.get('severity') == 'high')
    medium_severity = sum(1 for v in all_violations if v.get('severity') == 'medium')
    low_severity = sum(1 for v in all_violations if v.get('severity') == 'low')
    
    if total_accounts == 0:
        compliance_score = 100
    else:
        base_score = 100
        high_penalty = high_severity * 10
        medium_penalty = medium_severity * 5
        low_penalty = low_severity * 2
        total_penalty = high_penalty + medium_penalty + low_penalty
        
        max_penalty = total_accounts * 30
        penalty_ratio = min(total_penalty / max_penalty, 1.0) if max_penalty > 0 else 0
        compliance_score = max(0, int(base_score - (penalty_ratio * 100)))
    
    is_2025_compliant = issues_by_category['2025_requirements'] == 0 and high_severity == 0
    
    logger.info(f"Metro 2 validation complete: {total_violations} violations found across {total_accounts} accounts")
    
    return {
        'metro2_violations': all_violations,
        'compliance_score': compliance_score,
        '2025_compliant': is_2025_compliant,
        'issues_by_category': issues_by_category,
        'summary': {
            'total_accounts': total_accounts,
            'accounts_with_violations': accounts_with_violations,
            'total_violations': total_violations,
            'high_severity': high_severity,
            'medium_severity': medium_severity,
            'low_severity': low_severity
        },
        'validation_timestamp': datetime.utcnow().isoformat(),
        'validator_version': '2025.1.0'
    }


def get_account_status_info(status_code: str) -> Optional[dict]:
    """Get detailed information about an account status code."""
    status_code = str(status_code).strip().zfill(2) if status_code else ''
    if status_code in ACCOUNT_STATUS_CODES:
        return {
            'code': status_code,
            **ACCOUNT_STATUS_CODES[status_code]
        }
    return None


def get_payment_rating_info(rating_code: str) -> Optional[dict]:
    """Get detailed information about a payment rating code."""
    rating_code = str(rating_code).strip() if rating_code else ''
    if rating_code in PAYMENT_RATING_CODES:
        return {
            'code': rating_code,
            **PAYMENT_RATING_CODES[rating_code]
        }
    return None


def get_special_comment_info(comment_code: str) -> Optional[dict]:
    """Get detailed information about a special comment code."""
    comment_code = str(comment_code).strip().upper() if comment_code else ''
    if comment_code in SPECIAL_COMMENT_CODES:
        return {
            'code': comment_code,
            **SPECIAL_COMMENT_CODES[comment_code]
        }
    return None


def get_compliance_condition_info(condition_code: str) -> Optional[dict]:
    """Get detailed information about a compliance condition code."""
    condition_code = str(condition_code).strip().upper() if condition_code else ''
    if condition_code in COMPLIANCE_CONDITION_CODES:
        return {
            'code': condition_code,
            **COMPLIANCE_CONDITION_CODES[condition_code]
        }
    return None


def is_derogatory_status(status_code: str) -> bool:
    """Check if a status code indicates derogatory status."""
    status_code = str(status_code).strip().zfill(2) if status_code else ''
    if status_code in ACCOUNT_STATUS_CODES:
        return ACCOUNT_STATUS_CODES[status_code].get('is_derogatory', False)
    return False


def requires_dofd(status_code: str) -> bool:
    """Check if a status code requires DOFD."""
    status_code = str(status_code).strip().zfill(2) if status_code else ''
    if status_code in ACCOUNT_STATUS_CODES:
        return ACCOUNT_STATUS_CODES[status_code].get('requires_dofd', False)
    return False


def get_all_status_codes() -> dict:
    """Return all account status codes with their definitions."""
    return ACCOUNT_STATUS_CODES.copy()


def get_all_payment_codes() -> dict:
    """Return all payment rating codes with their definitions."""
    return PAYMENT_RATING_CODES.copy()


def get_all_special_comments() -> dict:
    """Return all special comment codes with their definitions."""
    return SPECIAL_COMMENT_CODES.copy()


def get_all_compliance_conditions() -> dict:
    """Return all compliance condition codes with their definitions."""
    return COMPLIANCE_CONDITION_CODES.copy()


def get_dofd_hierarchy_rules() -> dict:
    """Return all DOFD hierarchy rules."""
    return DOFD_HIERARCHY_RULES.copy()


def get_bankruptcy_requirements() -> dict:
    """Return 2025 bankruptcy reporting requirements."""
    return BANKRUPTCY_REQUIREMENTS_2025.copy()
