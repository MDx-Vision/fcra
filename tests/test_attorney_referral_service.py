"""
Unit Tests for Attorney Referral Handoff Service

Tests all functionality of the AttorneyReferralService including:
- Service constants and configuration
- Service initialization
- Custom exceptions
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestAttorneyReferralConstants:
    """Test service constants"""

    def test_referral_statuses_defined(self):
        """Verify all referral statuses are defined"""
        from services.attorney_referral_service import REFERRAL_STATUSES

        assert 'pending' in REFERRAL_STATUSES
        assert 'contacted' in REFERRAL_STATUSES
        assert 'accepted' in REFERRAL_STATUSES
        assert 'declined' in REFERRAL_STATUSES
        assert 'intake' in REFERRAL_STATUSES
        assert 'filed' in REFERRAL_STATUSES
        assert 'settled' in REFERRAL_STATUSES
        assert 'won' in REFERRAL_STATUSES
        assert 'lost' in REFERRAL_STATUSES
        assert len(REFERRAL_STATUSES) >= 10

    def test_violation_types_defined(self):
        """Verify all violation types are defined"""
        from services.attorney_referral_service import VIOLATION_TYPES

        assert 'failure_to_investigate' in VIOLATION_TYPES
        assert 'inaccurate_reporting' in VIOLATION_TYPES
        assert 'failure_to_correct' in VIOLATION_TYPES
        assert 'reinsertion' in VIOLATION_TYPES
        assert 'willful_noncompliance' in VIOLATION_TYPES
        assert 'negligent_noncompliance' in VIOLATION_TYPES
        assert len(VIOLATION_TYPES) >= 6

    def test_fee_arrangements_defined(self):
        """Verify all fee arrangements are defined"""
        from services.attorney_referral_service import FEE_ARRANGEMENTS

        assert 'contingency' in FEE_ARRANGEMENTS
        assert 'hourly' in FEE_ARRANGEMENTS
        assert 'hybrid' in FEE_ARRANGEMENTS
        assert 'flat' in FEE_ARRANGEMENTS

    def test_practice_areas_defined(self):
        """Verify practice areas include FCRA"""
        from services.attorney_referral_service import PRACTICE_AREAS

        assert 'FCRA' in PRACTICE_AREAS
        assert 'FDCPA' in PRACTICE_AREAS
        assert len(PRACTICE_AREAS) >= 5

    def test_referral_statuses_have_descriptions(self):
        """Each status has a description"""
        from services.attorney_referral_service import REFERRAL_STATUSES

        for status, description in REFERRAL_STATUSES.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_violation_types_have_descriptions(self):
        """Each violation type has a description"""
        from services.attorney_referral_service import VIOLATION_TYPES

        for vtype, description in VIOLATION_TYPES.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_fee_arrangements_have_descriptions(self):
        """Each fee arrangement has a description"""
        from services.attorney_referral_service import FEE_ARRANGEMENTS

        for fee_type, description in FEE_ARRANGEMENTS.items():
            assert isinstance(description, str)
            assert len(description) > 0

    def test_referral_status_pending_description(self):
        """Pending status has correct description"""
        from services.attorney_referral_service import REFERRAL_STATUSES

        assert 'Pending' in REFERRAL_STATUSES['pending']

    def test_referral_status_filed_description(self):
        """Filed status has correct description"""
        from services.attorney_referral_service import REFERRAL_STATUSES

        assert 'filed' in REFERRAL_STATUSES['filed'].lower() or 'Filed' in REFERRAL_STATUSES['filed']

    def test_referral_status_settled_description(self):
        """Settled status has correct description"""
        from services.attorney_referral_service import REFERRAL_STATUSES

        assert 'ettl' in REFERRAL_STATUSES['settled'].lower()


class TestAttorneyReferralServiceInit:
    """Test service initialization"""

    def test_init_without_session(self):
        """Service initializes without session"""
        from services.attorney_referral_service import AttorneyReferralService

        service = AttorneyReferralService()
        assert service._session is None
        assert service._owns_session is True

    def test_init_with_session(self):
        """Service initializes with provided session"""
        from services.attorney_referral_service import AttorneyReferralService

        mock_session = MagicMock()
        service = AttorneyReferralService(session=mock_session)
        assert service._session is mock_session
        assert service._owns_session is False

    def test_context_manager(self):
        """Service works as context manager"""
        from services.attorney_referral_service import AttorneyReferralService

        mock_session = MagicMock()
        with AttorneyReferralService(session=mock_session) as service:
            assert service._session is mock_session

    def test_context_manager_factory(self):
        """Context manager factory function works"""
        from services.attorney_referral_service import get_attorney_referral_service

        mock_session = MagicMock()
        service = get_attorney_referral_service(mock_session)
        assert service._session is mock_session

    def test_context_manager_exit_closes_session(self):
        """Context manager closes session on exit if owned"""
        from services.attorney_referral_service import AttorneyReferralService

        mock_session = MagicMock()
        service = AttorneyReferralService()
        service._session = mock_session
        service._owns_session = True
        service.__exit__(None, None, None)
        mock_session.close.assert_called_once()

    def test_context_manager_exit_no_close_if_not_owned(self):
        """Context manager does not close session if not owned"""
        from services.attorney_referral_service import AttorneyReferralService

        mock_session = MagicMock()
        service = AttorneyReferralService(session=mock_session)
        service.__exit__(None, None, None)
        mock_session.close.assert_not_called()

    def test_enter_returns_self(self):
        """Context manager enter returns self"""
        from services.attorney_referral_service import AttorneyReferralService

        service = AttorneyReferralService()
        result = service.__enter__()
        assert result is service


class TestAttorneyReferralServiceError:
    """Test custom exception"""

    def test_error_has_message(self):
        """Error contains message"""
        from services.attorney_referral_service import AttorneyReferralServiceError

        error = AttorneyReferralServiceError("Test error", "TEST_CODE")
        assert error.message == "Test error"
        assert error.error_code == "TEST_CODE"

    def test_error_has_details(self):
        """Error contains optional details"""
        from services.attorney_referral_service import AttorneyReferralServiceError

        error = AttorneyReferralServiceError("Test", "CODE", {"key": "value"})
        assert error.details == {"key": "value"}

    def test_error_default_details(self):
        """Error has empty details by default"""
        from services.attorney_referral_service import AttorneyReferralServiceError

        error = AttorneyReferralServiceError("Test", "CODE")
        assert error.details == {}

    def test_error_str_representation(self):
        """Error has string representation"""
        from services.attorney_referral_service import AttorneyReferralServiceError

        error = AttorneyReferralServiceError("Test error", "TEST_CODE")
        assert str(error) == "Test error"

    def test_error_is_exception(self):
        """Error is an Exception subclass"""
        from services.attorney_referral_service import AttorneyReferralServiceError

        error = AttorneyReferralServiceError("Test", "CODE")
        assert isinstance(error, Exception)

    def test_error_can_be_raised(self):
        """Error can be raised and caught"""
        from services.attorney_referral_service import AttorneyReferralServiceError

        with pytest.raises(AttorneyReferralServiceError) as exc_info:
            raise AttorneyReferralServiceError("Raised error", "RAISE_TEST")

        assert exc_info.value.message == "Raised error"
        assert exc_info.value.error_code == "RAISE_TEST"


class TestHelperMethods:
    """Test helper methods"""

    def test_success_response_format(self):
        """Success response has correct format"""
        from services.attorney_referral_service import AttorneyReferralService

        service = AttorneyReferralService()
        result = service._success_response({'key': 'value'}, 'Success message')

        assert result['success'] is True
        assert 'message' in result

    def test_success_response_without_message(self):
        """Success response works without message"""
        from services.attorney_referral_service import AttorneyReferralService

        service = AttorneyReferralService()
        result = service._success_response({'key': 'value'})

        assert result['success'] is True

    def test_error_response_format(self):
        """Error response has correct format"""
        from services.attorney_referral_service import AttorneyReferralService

        service = AttorneyReferralService()
        result = service._error_response('Error message', 'ERR_CODE', {'detail': 'info'})

        assert result['success'] is False
        assert result['error'] == 'Error message'
        assert result['error_code'] == 'ERR_CODE'

    def test_error_response_without_details(self):
        """Error response works without details"""
        from services.attorney_referral_service import AttorneyReferralService

        service = AttorneyReferralService()
        result = service._error_response('Error message', 'ERR_CODE')

        assert result['success'] is False
        assert result['error'] == 'Error message'


class TestValidStatusTransitions:
    """Test valid status values"""

    def test_all_statuses_are_strings(self):
        """All status keys are strings"""
        from services.attorney_referral_service import REFERRAL_STATUSES

        for status in REFERRAL_STATUSES.keys():
            assert isinstance(status, str)

    def test_workflow_statuses_exist(self):
        """Key workflow statuses exist"""
        from services.attorney_referral_service import REFERRAL_STATUSES

        workflow_statuses = ['pending', 'contacted', 'accepted', 'declined',
                            'intake', 'filed', 'settled', 'won', 'lost', 'closed']
        for status in workflow_statuses:
            assert status in REFERRAL_STATUSES

    def test_retainer_signed_status_exists(self):
        """Retainer signed status exists"""
        from services.attorney_referral_service import REFERRAL_STATUSES

        assert 'retainer_signed' in REFERRAL_STATUSES


class TestViolationTypes:
    """Test violation type definitions"""

    def test_fcra_section_611_violations(self):
        """Section 611 violations are defined"""
        from services.attorney_referral_service import VIOLATION_TYPES

        # Section 611 covers investigation procedures
        assert 'failure_to_investigate' in VIOLATION_TYPES
        assert 'failure_to_correct' in VIOLATION_TYPES
        assert 'reinsertion' in VIOLATION_TYPES

    def test_fcra_section_616_617_violations(self):
        """Sections 616/617 violations are defined"""
        from services.attorney_referral_service import VIOLATION_TYPES

        # Section 616 - willful, Section 617 - negligent
        assert 'willful_noncompliance' in VIOLATION_TYPES
        assert 'negligent_noncompliance' in VIOLATION_TYPES

    def test_fcra_section_623_violations(self):
        """Section 623 violations are defined"""
        from services.attorney_referral_service import VIOLATION_TYPES

        # Section 623 covers furnisher requirements
        assert 'inaccurate_reporting' in VIOLATION_TYPES


class TestFeeArrangements:
    """Test fee arrangement definitions"""

    def test_contingency_fee_structure(self):
        """Contingency fee structure is defined"""
        from services.attorney_referral_service import FEE_ARRANGEMENTS

        assert 'contingency' in FEE_ARRANGEMENTS
        assert 'contingency' in FEE_ARRANGEMENTS['contingency'].lower() or 'no fee' in FEE_ARRANGEMENTS['contingency'].lower()

    def test_hourly_fee_structure(self):
        """Hourly fee structure is defined"""
        from services.attorney_referral_service import FEE_ARRANGEMENTS

        assert 'hourly' in FEE_ARRANGEMENTS
        assert 'hour' in FEE_ARRANGEMENTS['hourly'].lower()

    def test_hybrid_fee_structure(self):
        """Hybrid fee structure is defined"""
        from services.attorney_referral_service import FEE_ARRANGEMENTS

        assert 'hybrid' in FEE_ARRANGEMENTS


class TestPracticeAreas:
    """Test practice area definitions"""

    def test_consumer_protection_laws(self):
        """Consumer protection practice areas are defined"""
        from services.attorney_referral_service import PRACTICE_AREAS

        consumer_laws = ['FCRA', 'FDCPA', 'TCPA']
        for law in consumer_laws:
            assert law in PRACTICE_AREAS

    def test_practice_areas_is_list(self):
        """Practice areas is a list"""
        from services.attorney_referral_service import PRACTICE_AREAS

        assert isinstance(PRACTICE_AREAS, list)

    def test_practice_areas_not_empty(self):
        """Practice areas list is not empty"""
        from services.attorney_referral_service import PRACTICE_AREAS

        assert len(PRACTICE_AREAS) > 0
