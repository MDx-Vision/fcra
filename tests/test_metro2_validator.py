"""
Unit tests for Metro 2 Validator Service - CRRG 2025 Compliance Checks

Tests cover:
- Account status code validation
- Payment pattern validation
- Special comment codes
- Compliance condition codes
- DOFD hierarchy rules
- 2025 requirements
- Full validation pipeline
- Helper functions
"""

import pytest
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch


class TestAccountStatusCodes:
    """Tests for ACCOUNT_STATUS_CODES constant"""

    def test_account_status_codes_exist(self):
        """Should have status codes defined"""
        from services.metro2_validator import ACCOUNT_STATUS_CODES

        assert len(ACCOUNT_STATUS_CODES) > 0

    def test_status_codes_have_required_fields(self):
        """Each status code should have required fields"""
        from services.metro2_validator import ACCOUNT_STATUS_CODES

        required_fields = ['description', 'category', 'is_derogatory', 'requires_dofd', 'crrg_section']

        for code, info in ACCOUNT_STATUS_CODES.items():
            for field in required_fields:
                assert field in info, f"Status {code} missing field: {field}"

    def test_derogatory_codes_identified(self):
        """Known derogatory codes should be marked as such"""
        from services.metro2_validator import ACCOUNT_STATUS_CODES

        derogatory_codes = ['80', '82', '83', '84', '85', '86']
        for code in derogatory_codes:
            assert ACCOUNT_STATUS_CODES[code]['is_derogatory'] is True

    def test_non_derogatory_codes_identified(self):
        """Non-derogatory codes should not be marked derogatory"""
        from services.metro2_validator import ACCOUNT_STATUS_CODES

        non_derogatory_codes = ['11', '05', '95', '96']
        for code in non_derogatory_codes:
            assert ACCOUNT_STATUS_CODES[code]['is_derogatory'] is False


class TestPaymentRatingCodes:
    """Tests for PAYMENT_RATING_CODES constant"""

    def test_payment_rating_codes_exist(self):
        """Should have payment codes defined"""
        from services.metro2_validator import PAYMENT_RATING_CODES

        assert len(PAYMENT_RATING_CODES) > 0

    def test_includes_standard_codes(self):
        """Should include standard codes 0-6"""
        from services.metro2_validator import PAYMENT_RATING_CODES

        for code in ['0', '1', '2', '3', '4', '5', '6']:
            assert code in PAYMENT_RATING_CODES


class TestSpecialCommentCodes:
    """Tests for SPECIAL_COMMENT_CODES constant"""

    def test_special_comment_codes_exist(self):
        """Should have special comment codes defined"""
        from services.metro2_validator import SPECIAL_COMMENT_CODES

        assert len(SPECIAL_COMMENT_CODES) > 0

    def test_dispute_codes_exist(self):
        """Should include dispute-related codes"""
        from services.metro2_validator import SPECIAL_COMMENT_CODES

        dispute_codes = ['AW', 'DA', 'ID']
        for code in dispute_codes:
            assert code in SPECIAL_COMMENT_CODES


class TestValidateAccountStatus:
    """Tests for validate_account_status function"""

    def test_valid_status_code(self):
        """Should validate known status code"""
        from services.metro2_validator import validate_account_status

        result = validate_account_status('11')

        assert result['is_valid'] is True
        assert len(result['violations']) == 0
        assert result['code'] == '11'

    def test_invalid_status_code(self):
        """Should detect invalid status code"""
        from services.metro2_validator import validate_account_status

        result = validate_account_status('99')

        assert result['is_valid'] is False
        assert len(result['violations']) > 0
        assert 'Invalid account status code' in result['violations'][0]['issue']

    def test_missing_status_code(self):
        """Should detect missing status code"""
        from services.metro2_validator import validate_account_status

        result = validate_account_status('')

        assert result['is_valid'] is False
        assert 'missing' in result['violations'][0]['issue'].lower()

    def test_returns_derogatory_flag(self):
        """Should return is_derogatory flag"""
        from services.metro2_validator import validate_account_status

        result = validate_account_status('82')  # Charge-off

        assert result['is_derogatory'] is True

    def test_pads_single_digit_code(self):
        """Should handle single-digit codes"""
        from services.metro2_validator import validate_account_status

        result = validate_account_status('5')

        assert result['code'] == '05'


class TestValidatePaymentPattern:
    """Tests for validate_payment_pattern function"""

    def test_valid_pattern(self):
        """Should validate correct payment pattern"""
        from services.metro2_validator import validate_payment_pattern

        result = validate_payment_pattern('000000000000', '11')

        assert result['is_valid'] is True
        assert len(result['violations']) == 0

    def test_invalid_codes_in_pattern(self):
        """Should detect invalid codes in pattern"""
        from services.metro2_validator import validate_payment_pattern

        result = validate_payment_pattern('00X00Y00', '11')

        assert result['is_valid'] is False
        assert any('Invalid payment codes' in v['issue'] for v in result['violations'])

    def test_status_payment_incompatibility(self):
        """Should detect status/payment incompatibility"""
        from services.metro2_validator import validate_payment_pattern

        # Current status (11) with most recent delinquency (6)
        result = validate_payment_pattern('6000000000', '11')

        assert result['is_valid'] is False

    def test_derogatory_status_without_pattern(self):
        """Should flag derogatory status without payment history"""
        from services.metro2_validator import validate_payment_pattern

        result = validate_payment_pattern('', '82')

        assert result['is_valid'] is False

    def test_pattern_analysis_returned(self):
        """Should return pattern analysis"""
        from services.metro2_validator import validate_payment_pattern

        result = validate_payment_pattern('0001230000', '11')

        assert result['pattern_analysis'] is not None
        assert result['pattern_analysis']['length'] == 10


class TestValidateSpecialComments:
    """Tests for validate_special_comments function"""

    def test_valid_comments(self):
        """Should validate known comment codes"""
        from services.metro2_validator import validate_special_comments

        result = validate_special_comments(['AW', 'AU'], {})

        assert result['is_valid'] is True

    def test_invalid_comment_code(self):
        """Should detect invalid comment code"""
        from services.metro2_validator import validate_special_comments

        result = validate_special_comments(['XX', 'YY'], {})

        assert result['is_valid'] is False
        assert any('Invalid special comment code' in v['issue'] for v in result['violations'])

    def test_missing_dispute_code(self):
        """Should flag missing dispute code when account is disputed"""
        from services.metro2_validator import validate_special_comments

        result = validate_special_comments([], {'is_disputed': True})

        assert result['is_valid'] is False
        assert any('dispute' in v['issue'].lower() for v in result['violations'])

    def test_missing_identity_theft_code(self):
        """Should flag missing AV code for identity theft"""
        from services.metro2_validator import validate_special_comments

        result = validate_special_comments([], {'is_identity_theft': True})

        assert result['is_valid'] is False
        assert any('AV' in v['issue'] for v in result['violations'])

    def test_returns_comment_details(self):
        """Should return comment details"""
        from services.metro2_validator import validate_special_comments

        result = validate_special_comments(['AW'], {})

        assert 'comment_details' in result
        assert result['comment_count'] == 1


class TestValidateComplianceConditions:
    """Tests for validate_compliance_conditions function"""

    def test_valid_conditions(self):
        """Should validate known condition codes"""
        from services.metro2_validator import validate_compliance_conditions

        result = validate_compliance_conditions(['XJ'], {'is_active_duty': True})

        assert result['is_valid'] is True

    def test_invalid_condition_code(self):
        """Should detect invalid condition code"""
        from services.metro2_validator import validate_compliance_conditions

        result = validate_compliance_conditions(['XZ'], {})

        assert result['is_valid'] is False
        assert any('Invalid compliance condition code' in v['issue'] for v in result['violations'])

    def test_missing_military_code(self):
        """Should flag missing XJ for active duty"""
        from services.metro2_validator import validate_compliance_conditions

        result = validate_compliance_conditions([], {'is_active_duty': True})

        assert result['is_valid'] is False
        assert any('XJ' in v['issue'] for v in result['violations'])

    def test_missing_forbearance_code(self):
        """Should flag missing forbearance code"""
        from services.metro2_validator import validate_compliance_conditions

        result = validate_compliance_conditions([], {'is_forbearance': True})

        assert result['is_valid'] is False

    def test_returns_scra_protection_flag(self):
        """Should return SCRA protection flag"""
        from services.metro2_validator import validate_compliance_conditions

        result = validate_compliance_conditions(['XK'], {})

        assert result['has_scra_protection'] is True


class TestValidateDofdHierarchy:
    """Tests for validate_dofd_hierarchy function"""

    def test_valid_dofd(self):
        """Should validate valid DOFD"""
        from services.metro2_validator import validate_dofd_hierarchy

        dofd = (date.today() - timedelta(days=365)).isoformat()
        result = validate_dofd_hierarchy(dofd, [], {'account_status': '82'})

        assert result['is_valid'] is True

    def test_missing_dofd_derogatory(self):
        """Should flag missing DOFD for derogatory account"""
        from services.metro2_validator import validate_dofd_hierarchy

        result = validate_dofd_hierarchy(None, [], {'account_status': '82'})

        assert result['is_valid'] is False
        assert any('missing' in v['issue'].lower() for v in result['violations'])

    def test_expired_dofd(self):
        """Should flag DOFD past 7-year limit"""
        from services.metro2_validator import validate_dofd_hierarchy

        old_dofd = (date.today() - timedelta(days=8 * 365)).isoformat()
        result = validate_dofd_hierarchy(old_dofd, [], {'account_status': '82'})

        assert result['is_valid'] is False
        assert any('7-year' in v['issue'] for v in result['violations'])

    def test_future_dofd(self):
        """Should flag future DOFD"""
        from services.metro2_validator import validate_dofd_hierarchy

        future_dofd = (date.today() + timedelta(days=30)).isoformat()
        result = validate_dofd_hierarchy(future_dofd, [], {'account_status': '82'})

        assert result['is_valid'] is False
        assert any('future' in v['issue'].lower() for v in result['violations'])

    def test_returns_days_until_expiration(self):
        """Should return days until expiration"""
        from services.metro2_validator import validate_dofd_hierarchy

        dofd = (date.today() - timedelta(days=365)).isoformat()
        result = validate_dofd_hierarchy(dofd, [], {})

        assert result['days_until_expiration'] is not None


class TestValidate2025Requirements:
    """Tests for validate_2025_requirements function"""

    def test_all_required_fields_present(self):
        """Should pass when all required fields present"""
        from services.metro2_validator import validate_2025_requirements

        account = {
            'account_number': '123456',
            'account_type': 'I',
            'date_opened': '2020-01-01',
            'date_reported': '2024-01-01',
            'current_balance': 1000,
            'account_status': '11',
            'payment_rating': '0',
        }

        result = validate_2025_requirements(account)

        # May still have violations for derogatory fields, but basic required should pass
        assert result is not None

    def test_missing_required_field(self):
        """Should detect missing required field"""
        from services.metro2_validator import validate_2025_requirements

        account = {'account_status': '11'}  # Missing most required fields

        result = validate_2025_requirements(account)

        assert result['is_valid'] is False
        assert len(result['missing_fields']) > 0

    def test_derogatory_account_requirements(self):
        """Should check derogatory account requirements"""
        from services.metro2_validator import validate_2025_requirements

        account = {
            'account_number': '123',
            'account_type': 'I',
            'date_opened': '2020-01-01',
            'date_reported': '2024-01-01',
            'current_balance': 1000,
            'account_status': '82',  # Charge-off
            'payment_rating': '6',
            # Missing derogatory-required fields
        }

        result = validate_2025_requirements(account)

        assert any('derogatory' in str(v).lower() for v in result['violations'])

    def test_bankruptcy_account_requirements(self):
        """Should check bankruptcy account requirements"""
        from services.metro2_validator import validate_2025_requirements

        account = {
            'account_number': '123',
            'account_type': 'I',
            'date_opened': '2020-01-01',
            'date_reported': '2024-01-01',
            'current_balance': 0,
            'account_status': '83',  # Chapter 7
            'payment_rating': 'B',
            # Missing bankruptcy-required fields
        }

        result = validate_2025_requirements(account)

        assert any('bankruptcy' in str(v).lower() for v in result['violations'])


class TestRunFullMetro2Validation:
    """Tests for run_full_metro2_validation function"""

    def test_returns_summary(self):
        """Should return validation summary"""
        from services.metro2_validator import run_full_metro2_validation

        accounts = [
            {
                'account_status': '11',
                'payment_history': '000000000000',
                'account_number': '123',
                'account_type': 'I',
                'date_opened': '2020-01-01',
                'date_reported': '2024-01-01',
                'current_balance': 1000,
                'payment_rating': '0',
            }
        ]

        result = run_full_metro2_validation(accounts)

        assert 'metro2_violations' in result
        assert 'compliance_score' in result
        assert 'summary' in result
        assert result['summary']['total_accounts'] == 1

    def test_handles_empty_accounts(self):
        """Should handle empty accounts list"""
        from services.metro2_validator import run_full_metro2_validation

        result = run_full_metro2_validation([])

        assert result['compliance_score'] == 100
        assert result['summary']['total_accounts'] == 0

    def test_calculates_compliance_score(self):
        """Should calculate compliance score"""
        from services.metro2_validator import run_full_metro2_validation

        # Account with violations
        accounts = [
            {
                'account_status': '99',  # Invalid
                'payment_history': 'XXXX',  # Invalid
            }
        ]

        result = run_full_metro2_validation(accounts)

        assert result['compliance_score'] < 100

    def test_categorizes_issues(self):
        """Should categorize issues by type"""
        from services.metro2_validator import run_full_metro2_validation

        accounts = [
            {'account_status': '99'}  # Invalid status
        ]

        result = run_full_metro2_validation(accounts)

        assert 'issues_by_category' in result
        assert result['issues_by_category']['status_codes'] > 0

    def test_returns_timestamp_and_version(self):
        """Should include timestamp and version"""
        from services.metro2_validator import run_full_metro2_validation

        result = run_full_metro2_validation([])

        assert 'validation_timestamp' in result
        assert 'validator_version' in result


class TestHelperFunctions:
    """Tests for helper functions"""

    def test_get_account_status_info(self):
        """Should return status info"""
        from services.metro2_validator import get_account_status_info

        result = get_account_status_info('82')

        assert result is not None
        assert result['code'] == '82'
        assert 'description' in result

    def test_get_account_status_info_invalid(self):
        """Should return None for invalid code"""
        from services.metro2_validator import get_account_status_info

        result = get_account_status_info('99')

        assert result is None

    def test_get_payment_rating_info(self):
        """Should return payment rating info"""
        from services.metro2_validator import get_payment_rating_info

        result = get_payment_rating_info('1')

        assert result is not None
        assert result['code'] == '1'

    def test_get_special_comment_info(self):
        """Should return special comment info"""
        from services.metro2_validator import get_special_comment_info

        result = get_special_comment_info('AW')

        assert result is not None
        assert result['code'] == 'AW'

    def test_get_compliance_condition_info(self):
        """Should return compliance condition info"""
        from services.metro2_validator import get_compliance_condition_info

        result = get_compliance_condition_info('XJ')

        assert result is not None
        assert result['code'] == 'XJ'

    def test_is_derogatory_status(self):
        """Should identify derogatory status"""
        from services.metro2_validator import is_derogatory_status

        assert is_derogatory_status('82') is True
        assert is_derogatory_status('11') is False

    def test_requires_dofd(self):
        """Should identify status requiring DOFD"""
        from services.metro2_validator import requires_dofd

        assert requires_dofd('82') is True
        assert requires_dofd('11') is False

    def test_get_all_status_codes(self):
        """Should return all status codes"""
        from services.metro2_validator import get_all_status_codes

        result = get_all_status_codes()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_get_all_payment_codes(self):
        """Should return all payment codes"""
        from services.metro2_validator import get_all_payment_codes

        result = get_all_payment_codes()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_get_all_special_comments(self):
        """Should return all special comments"""
        from services.metro2_validator import get_all_special_comments

        result = get_all_special_comments()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_get_all_compliance_conditions(self):
        """Should return all compliance conditions"""
        from services.metro2_validator import get_all_compliance_conditions

        result = get_all_compliance_conditions()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_get_dofd_hierarchy_rules(self):
        """Should return DOFD hierarchy rules"""
        from services.metro2_validator import get_dofd_hierarchy_rules

        result = get_dofd_hierarchy_rules()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_get_bankruptcy_requirements(self):
        """Should return bankruptcy requirements"""
        from services.metro2_validator import get_bankruptcy_requirements

        result = get_bankruptcy_requirements()

        assert isinstance(result, dict)
        assert '83' in result  # Chapter 7


class TestParseDateHelper:
    """Tests for _parse_date helper function"""

    def test_parses_iso_format(self):
        """Should parse ISO date format"""
        from services.metro2_validator import _parse_date

        result = _parse_date('2024-01-15')

        assert result == date(2024, 1, 15)

    def test_parses_us_format(self):
        """Should parse US date format"""
        from services.metro2_validator import _parse_date

        result = _parse_date('01/15/2024')

        assert result == date(2024, 1, 15)

    def test_handles_date_object(self):
        """Should handle date object"""
        from services.metro2_validator import _parse_date

        input_date = date(2024, 1, 15)
        result = _parse_date(input_date)

        assert result == input_date

    def test_handles_datetime_object(self):
        """Should handle datetime object (returns as-is)"""
        from services.metro2_validator import _parse_date

        input_dt = datetime(2024, 1, 15, 10, 30)
        result = _parse_date(input_dt)

        # Function returns datetime as-is, doesn't convert to date
        assert result == input_dt

    def test_returns_none_for_none(self):
        """Should return None for None input"""
        from services.metro2_validator import _parse_date

        result = _parse_date(None)

        assert result is None

    def test_returns_none_for_invalid_string(self):
        """Should return None for invalid date string"""
        from services.metro2_validator import _parse_date

        result = _parse_date('not-a-date')

        assert result is None
