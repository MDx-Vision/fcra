"""
Unit Tests for RESPA QWR Service

Tests all functionality of the RESPAQWRService including:
- Service constants and configuration
- Service initialization
- Custom exceptions
- Helper methods
- Business day calculations
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date, timedelta


class TestRESPAQWRConstants:
    """Test service constants"""

    def test_qwr_statuses_defined(self):
        """Verify all QWR statuses are defined"""
        from services.respa_qwr_service import QWR_STATUSES

        assert 'pending' in QWR_STATUSES
        assert 'sent' in QWR_STATUSES
        assert 'awaiting_acknowledgment' in QWR_STATUSES
        assert 'awaiting_response' in QWR_STATUSES
        assert 'response_received' in QWR_STATUSES
        assert 'violation' in QWR_STATUSES
        assert 'escalated' in QWR_STATUSES
        assert 'resolved' in QWR_STATUSES
        assert 'closed' in QWR_STATUSES
        assert len(QWR_STATUSES) >= 9

    def test_qwr_types_defined(self):
        """Verify all QWR types are defined"""
        from services.respa_qwr_service import QWR_TYPES

        assert 'payment_history' in QWR_TYPES
        assert 'escrow_analysis' in QWR_TYPES
        assert 'fee_dispute' in QWR_TYPES
        assert 'payment_application' in QWR_TYPES
        assert 'general_inquiry' in QWR_TYPES
        assert 'loss_mitigation' in QWR_TYPES
        assert 'payoff_request' in QWR_TYPES
        assert len(QWR_TYPES) >= 7

    def test_violation_types_defined(self):
        """Verify all violation types are defined"""
        from services.respa_qwr_service import VIOLATION_TYPES

        assert 'no_acknowledgment' in VIOLATION_TYPES
        assert 'no_response' in VIOLATION_TYPES
        assert 'inadequate_response' in VIOLATION_TYPES
        assert 'continued_fees' in VIOLATION_TYPES
        assert 'retaliation' in VIOLATION_TYPES
        assert 'false_information' in VIOLATION_TYPES
        assert len(VIOLATION_TYPES) >= 6

    def test_response_types_defined(self):
        """Verify all response types are defined"""
        from services.respa_qwr_service import RESPONSE_TYPES

        assert 'complete' in RESPONSE_TYPES
        assert 'partial' in RESPONSE_TYPES
        assert 'inadequate' in RESPONSE_TYPES
        assert 'denied' in RESPONSE_TYPES
        assert 'no_response' in RESPONSE_TYPES
        assert len(RESPONSE_TYPES) >= 5

    def test_resolution_types_defined(self):
        """Verify all resolution types are defined"""
        from services.respa_qwr_service import RESOLUTION_TYPES

        assert 'corrected' in RESOLUTION_TYPES
        assert 'denied' in RESOLUTION_TYPES
        assert 'partial_correction' in RESOLUTION_TYPES
        assert 'escalated' in RESOLUTION_TYPES
        assert 'litigation' in RESOLUTION_TYPES
        assert 'settled' in RESOLUTION_TYPES
        assert len(RESOLUTION_TYPES) >= 6

    def test_loan_types_defined(self):
        """Verify loan types are defined"""
        from services.respa_qwr_service import LOAN_TYPES

        assert 'conventional' in LOAN_TYPES
        assert 'fha' in LOAN_TYPES
        assert 'va' in LOAN_TYPES
        assert 'usda' in LOAN_TYPES
        assert len(LOAN_TYPES) >= 4

    def test_send_methods_defined(self):
        """Verify send methods are defined"""
        from services.respa_qwr_service import SEND_METHODS

        assert 'certified_mail' in SEND_METHODS
        assert 'regular_mail' in SEND_METHODS
        assert 'fax' in SEND_METHODS
        assert 'email' in SEND_METHODS
        assert len(SEND_METHODS) >= 4

    def test_major_servicers_defined(self):
        """Verify major servicers list is defined"""
        from services.respa_qwr_service import MAJOR_SERVICERS

        assert isinstance(MAJOR_SERVICERS, list)
        assert len(MAJOR_SERVICERS) >= 10
        assert 'Wells Fargo Home Mortgage' in MAJOR_SERVICERS
        assert 'Chase Home Lending' in MAJOR_SERVICERS

    def test_qwr_statuses_have_descriptions(self):
        """Each status has a description"""
        from services.respa_qwr_service import QWR_STATUSES

        for status, description in QWR_STATUSES.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_qwr_types_have_descriptions(self):
        """Each QWR type has a description"""
        from services.respa_qwr_service import QWR_TYPES

        for qwr_type, description in QWR_TYPES.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_violation_types_have_descriptions(self):
        """Each violation type has a description"""
        from services.respa_qwr_service import VIOLATION_TYPES

        for vtype, description in VIOLATION_TYPES.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_pending_status_description(self):
        """Pending status has correct description"""
        from services.respa_qwr_service import QWR_STATUSES

        assert 'Pending' in QWR_STATUSES['pending']

    def test_violation_status_description(self):
        """Violation status has correct description"""
        from services.respa_qwr_service import QWR_STATUSES

        assert 'Violation' in QWR_STATUSES['violation']


class TestRESPAQWRServiceInit:
    """Test service initialization"""

    def test_init_without_session(self):
        """Service initializes without session"""
        from services.respa_qwr_service import RESPAQWRService

        service = RESPAQWRService()
        assert service._session is None
        assert service._owns_session is True

    def test_init_with_session(self):
        """Service initializes with provided session"""
        from services.respa_qwr_service import RESPAQWRService

        mock_session = MagicMock()
        service = RESPAQWRService(session=mock_session)
        assert service._session is mock_session
        assert service._owns_session is False

    def test_context_manager(self):
        """Service works as context manager"""
        from services.respa_qwr_service import RESPAQWRService

        mock_session = MagicMock()
        with RESPAQWRService(session=mock_session) as service:
            assert service._session is mock_session

    def test_context_manager_factory(self):
        """Context manager factory function works"""
        from services.respa_qwr_service import get_respa_qwr_service

        mock_session = MagicMock()
        service = get_respa_qwr_service(mock_session)
        assert service._session is mock_session

    def test_context_manager_exit_closes_session(self):
        """Context manager closes session on exit if owned"""
        from services.respa_qwr_service import RESPAQWRService

        mock_session = MagicMock()
        service = RESPAQWRService()
        service._session = mock_session
        service._owns_session = True
        service.__exit__(None, None, None)
        mock_session.close.assert_called_once()

    def test_context_manager_exit_no_close_if_not_owned(self):
        """Context manager does not close session if not owned"""
        from services.respa_qwr_service import RESPAQWRService

        mock_session = MagicMock()
        service = RESPAQWRService(session=mock_session)
        service.__exit__(None, None, None)
        mock_session.close.assert_not_called()

    def test_enter_returns_self(self):
        """Context manager enter returns self"""
        from services.respa_qwr_service import RESPAQWRService

        service = RESPAQWRService()
        result = service.__enter__()
        assert result is service


class TestRESPAQWRServiceError:
    """Test custom exception"""

    def test_error_has_message(self):
        """Error contains message"""
        from services.respa_qwr_service import RESPAQWRServiceError

        error = RESPAQWRServiceError("Test error", "TEST_CODE")
        assert error.message == "Test error"
        assert error.error_code == "TEST_CODE"

    def test_error_has_details(self):
        """Error contains optional details"""
        from services.respa_qwr_service import RESPAQWRServiceError

        error = RESPAQWRServiceError("Test", "CODE", {"key": "value"})
        assert error.details == {"key": "value"}

    def test_error_default_details(self):
        """Error has empty details by default"""
        from services.respa_qwr_service import RESPAQWRServiceError

        error = RESPAQWRServiceError("Test", "CODE")
        assert error.details == {}

    def test_error_str_representation(self):
        """Error has string representation"""
        from services.respa_qwr_service import RESPAQWRServiceError

        error = RESPAQWRServiceError("Test error", "TEST_CODE")
        assert str(error) == "Test error"

    def test_error_is_exception(self):
        """Error is an Exception subclass"""
        from services.respa_qwr_service import RESPAQWRServiceError

        error = RESPAQWRServiceError("Test", "CODE")
        assert isinstance(error, Exception)

    def test_error_can_be_raised(self):
        """Error can be raised and caught"""
        from services.respa_qwr_service import RESPAQWRServiceError

        with pytest.raises(RESPAQWRServiceError) as exc_info:
            raise RESPAQWRServiceError("Raised error", "RAISE_TEST")

        assert exc_info.value.message == "Raised error"
        assert exc_info.value.error_code == "RAISE_TEST"


class TestHelperMethods:
    """Test helper methods"""

    def test_success_response_format(self):
        """Success response has correct format"""
        from services.respa_qwr_service import RESPAQWRService

        service = RESPAQWRService()
        result = service._success_response({'key': 'value'}, 'Success message')

        assert result['success'] is True
        assert 'message' in result

    def test_success_response_without_message(self):
        """Success response works without message"""
        from services.respa_qwr_service import RESPAQWRService

        service = RESPAQWRService()
        result = service._success_response({'key': 'value'})

        assert result['success'] is True

    def test_error_response_format(self):
        """Error response has correct format"""
        from services.respa_qwr_service import RESPAQWRService

        service = RESPAQWRService()
        result = service._error_response('Error message', 'ERR_CODE', {'detail': 'info'})

        assert result['success'] is False
        assert result['error'] == 'Error message'
        assert result['error_code'] == 'ERR_CODE'

    def test_error_response_without_details(self):
        """Error response works without details"""
        from services.respa_qwr_service import RESPAQWRService

        service = RESPAQWRService()
        result = service._error_response('Error message', 'ERR_CODE')

        assert result['success'] is False
        assert result['error'] == 'Error message'


class TestBusinessDayCalculations:
    """Test business day calculations"""

    def test_add_business_days_basic(self):
        """Basic business day addition works"""
        from services.respa_qwr_service import add_business_days

        # Start from a Monday
        start = date(2026, 2, 2)  # Monday
        result = add_business_days(start, 5)

        # 5 business days from Monday = next Monday
        assert result == date(2026, 2, 9)

    def test_add_business_days_skips_weekend(self):
        """Business day calculation skips weekends"""
        from services.respa_qwr_service import add_business_days

        # Start from a Friday
        start = date(2026, 2, 6)  # Friday
        result = add_business_days(start, 1)

        # 1 business day from Friday = Monday
        assert result == date(2026, 2, 9)

    def test_add_business_days_30_days(self):
        """30 business days calculation works (RESPA deadline)"""
        from services.respa_qwr_service import add_business_days

        start = date(2026, 2, 2)  # Monday
        result = add_business_days(start, 30)

        # Should be 6 weeks later (30 business days = 6 weeks)
        assert result == date(2026, 3, 16)

    def test_add_business_days_45_days(self):
        """45 business days calculation works (extended deadline)"""
        from services.respa_qwr_service import add_business_days

        start = date(2026, 2, 2)  # Monday
        result = add_business_days(start, 45)

        # Should be 9 weeks later
        assert result == date(2026, 4, 6)


class TestValidStatusTransitions:
    """Test valid status values"""

    def test_all_statuses_are_strings(self):
        """All status keys are strings"""
        from services.respa_qwr_service import QWR_STATUSES

        for status in QWR_STATUSES.keys():
            assert isinstance(status, str)

    def test_workflow_statuses_exist(self):
        """Key workflow statuses exist"""
        from services.respa_qwr_service import QWR_STATUSES

        workflow_statuses = ['pending', 'sent', 'awaiting_acknowledgment',
                            'awaiting_response', 'response_received',
                            'violation', 'escalated', 'resolved', 'closed']
        for status in workflow_statuses:
            assert status in QWR_STATUSES


class TestQWRTypes:
    """Test QWR type definitions"""

    def test_respa_section_6_qwr_types(self):
        """RESPA Section 6 QWR types are defined"""
        from services.respa_qwr_service import QWR_TYPES

        assert 'payment_history' in QWR_TYPES
        assert 'escrow_analysis' in QWR_TYPES
        assert 'fee_dispute' in QWR_TYPES

    def test_payment_history_type(self):
        """Payment history type has description"""
        from services.respa_qwr_service import QWR_TYPES

        assert 'Payment History' in QWR_TYPES['payment_history']

    def test_escrow_analysis_type(self):
        """Escrow analysis type has description"""
        from services.respa_qwr_service import QWR_TYPES

        assert 'Escrow' in QWR_TYPES['escrow_analysis']

    def test_fee_dispute_type(self):
        """Fee dispute type has description"""
        from services.respa_qwr_service import QWR_TYPES

        assert 'Fee' in QWR_TYPES['fee_dispute']


class TestViolationTypes:
    """Test violation type definitions"""

    def test_no_acknowledgment_violation(self):
        """No acknowledgment violation is defined"""
        from services.respa_qwr_service import VIOLATION_TYPES

        assert 'no_acknowledgment' in VIOLATION_TYPES
        assert '5 business days' in VIOLATION_TYPES['no_acknowledgment']

    def test_no_response_violation(self):
        """No response violation is defined"""
        from services.respa_qwr_service import VIOLATION_TYPES

        assert 'no_response' in VIOLATION_TYPES
        assert '30 business days' in VIOLATION_TYPES['no_response']

    def test_continued_fees_violation(self):
        """Continued fees violation is defined"""
        from services.respa_qwr_service import VIOLATION_TYPES

        assert 'continued_fees' in VIOLATION_TYPES
        assert 'RESPA' in VIOLATION_TYPES['continued_fees']


class TestServicerList:
    """Test major servicers list"""

    def test_major_servicers_is_list(self):
        """Major servicers is a list"""
        from services.respa_qwr_service import MAJOR_SERVICERS

        assert isinstance(MAJOR_SERVICERS, list)

    def test_major_servicers_not_empty(self):
        """Major servicers list is not empty"""
        from services.respa_qwr_service import MAJOR_SERVICERS

        assert len(MAJOR_SERVICERS) > 0

    def test_major_servicers_includes_wells_fargo(self):
        """Wells Fargo is in major servicers"""
        from services.respa_qwr_service import MAJOR_SERVICERS

        assert 'Wells Fargo Home Mortgage' in MAJOR_SERVICERS

    def test_major_servicers_includes_chase(self):
        """Chase is in major servicers"""
        from services.respa_qwr_service import MAJOR_SERVICERS

        assert 'Chase Home Lending' in MAJOR_SERVICERS

    def test_major_servicers_includes_mr_cooper(self):
        """Mr. Cooper is in major servicers"""
        from services.respa_qwr_service import MAJOR_SERVICERS

        assert 'Mr. Cooper (Nationstar)' in MAJOR_SERVICERS

    def test_major_servicers_includes_pennymac(self):
        """Pennymac is in major servicers"""
        from services.respa_qwr_service import MAJOR_SERVICERS

        assert 'Pennymac' in MAJOR_SERVICERS
