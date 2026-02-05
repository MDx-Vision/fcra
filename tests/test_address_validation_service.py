"""
Unit tests for Address Validation Service - USPS API integration

Tests cover:
- AddressValidationService initialization
- Address validation logic
- Response parsing
- Address formatting
- Singleton management
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock


class TestValidatedAddressDataclass:
    """Tests for ValidatedAddress dataclass"""

    def test_validated_address_creation(self):
        """Should create ValidatedAddress with all fields"""
        from services.address_validation_service import ValidatedAddress

        addr = ValidatedAddress(
            street="123 MAIN ST",
            street2="APT 4",
            city="NEW YORK",
            state="NY",
            zip5="10001",
            zip4="1234",
            is_valid=True,
            error_message="",
            return_text="",
            was_corrected=False,
            original={"street": "123 Main St", "city": "New York", "state": "NY", "zip_code": "10001", "street2": ""}
        )

        assert addr.street == "123 MAIN ST"
        assert addr.zip5 == "10001"
        assert addr.is_valid is True

    def test_validated_address_all_fields(self):
        """Should have all required fields"""
        from services.address_validation_service import ValidatedAddress

        addr = ValidatedAddress(
            street="", street2="", city="", state="", zip5="", zip4="",
            is_valid=False, error_message="", return_text="", was_corrected=False, original={}
        )

        assert hasattr(addr, 'street')
        assert hasattr(addr, 'street2')
        assert hasattr(addr, 'city')
        assert hasattr(addr, 'state')
        assert hasattr(addr, 'zip5')
        assert hasattr(addr, 'zip4')
        assert hasattr(addr, 'is_valid')
        assert hasattr(addr, 'error_message')


class TestAddressValidationServiceInit:
    """Tests for AddressValidationService initialization"""

    def test_init_creates_instance(self):
        """Should create instance"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService()

        assert service is not None

    def test_init_with_credentials(self):
        """Should store credentials"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService(client_id="test_id", client_secret="test_secret")

        assert service.client_id == "test_id"
        assert service.client_secret == "test_secret"

    def test_init_is_configured_with_credentials(self):
        """Should be configured when credentials provided"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService(client_id="test", client_secret="test")

        assert service.is_configured is True

    @patch('services.address_validation_service.USPS_CLIENT_ID', '')
    @patch('services.address_validation_service.USPS_CLIENT_SECRET', '')
    def test_init_not_configured_without_credentials(self):
        """Should not be configured without credentials"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService(client_id=None, client_secret=None)

        assert service.is_configured is False

    def test_init_token_is_none(self):
        """Should start with no token"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService()

        assert service._access_token is None
        assert service._token_expires_at is None


class TestGetAccessToken:
    """Tests for _get_access_token method"""

    def test_returns_cached_token(self):
        """Should return cached token if valid"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService()
        service._access_token = "cached_token"
        service._token_expires_at = datetime.now() + timedelta(hours=1)

        token = service._get_access_token()

        assert token == "cached_token"

    @patch('services.address_validation_service.requests.post')
    @patch('services.address_validation_service.log_api_call')
    def test_requests_new_token(self, mock_log, mock_post):
        """Should request new token when no cached token"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService(client_id="test", client_secret="test")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "new_token", "expires_in": 3600}
        mock_post.return_value = mock_response

        token = service._get_access_token()

        assert token == "new_token"
        mock_post.assert_called_once()

    @patch('services.address_validation_service.requests.post')
    def test_returns_none_on_error(self, mock_post):
        """Should return None on request error"""
        from services.address_validation_service import AddressValidationService
        import requests

        service = AddressValidationService(client_id="test", client_secret="test")
        mock_post.side_effect = requests.RequestException("Error")

        token = service._get_access_token()

        assert token is None


class TestValidateAddress:
    """Tests for validate_address method"""

    @patch('services.address_validation_service.USPS_CLIENT_ID', '')
    @patch('services.address_validation_service.USPS_CLIENT_SECRET', '')
    def test_returns_as_is_when_not_configured(self):
        """Should return address as-is when not configured"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService(client_id=None, client_secret=None)

        result = service.validate_address(
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001"
        )

        assert result.street == "123 Main St"
        assert result.is_valid is True
        assert "not configured" in result.error_message

    def test_returns_validated_address(self):
        """Should return ValidatedAddress object"""
        from services.address_validation_service import AddressValidationService, ValidatedAddress

        service = AddressValidationService(client_id="", client_secret="")

        result = service.validate_address(
            street="123 Main St",
            city="New York",
            state="NY"
        )

        assert isinstance(result, ValidatedAddress)

    def test_preserves_original_data(self):
        """Should preserve original input"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService(client_id="", client_secret="")

        result = service.validate_address(
            street="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            street2="Apt 4"
        )

        assert result.original['street'] == "123 Main St"
        assert result.original['city'] == "New York"


class TestParseResponse:
    """Tests for _parse_response method"""

    def test_parses_address_data(self):
        """Should parse address from response"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService()

        data = {
            "address": {
                "streetAddress": "123 MAIN ST",
                "city": "NEW YORK",
                "state": "NY",
                "ZIPCode": "10001",
                "ZIPPlus4": "5678"
            },
            "additionalInfo": {"DPVConfirmation": "Y"}
        }
        original = {"street": "123 main", "street2": "", "city": "new york", "state": "ny", "zip_code": "10001"}

        result = service._parse_response(data, original)

        assert result.street == "123 MAIN ST"
        assert result.city == "NEW YORK"

    def test_handles_empty_response(self):
        """Should handle empty/malformed response"""
        from services.address_validation_service import AddressValidationService

        service = AddressValidationService()

        original = {"street": "123 Main", "street2": "", "city": "NY", "state": "NY", "zip_code": "10001"}

        result = service._parse_response({}, original)

        assert result.is_valid is True or result.is_valid is False  # Should not crash


class TestFormatFullAddress:
    """Tests for format_full_address method"""

    def test_formats_basic_address(self):
        """Should format basic address"""
        from services.address_validation_service import AddressValidationService, ValidatedAddress

        service = AddressValidationService()

        addr = ValidatedAddress(
            street="123 MAIN ST", street2="", city="NEW YORK", state="NY",
            zip5="10001", zip4="", is_valid=True, error_message="",
            return_text="", was_corrected=False, original={}
        )

        result = service.format_full_address(addr)

        assert "123 MAIN ST" in result
        assert "NEW YORK" in result
        assert "NY" in result

    def test_includes_street2(self):
        """Should include street2 when present"""
        from services.address_validation_service import AddressValidationService, ValidatedAddress

        service = AddressValidationService()

        addr = ValidatedAddress(
            street="123 MAIN ST", street2="APT 4", city="NEW YORK", state="NY",
            zip5="10001", zip4="", is_valid=True, error_message="",
            return_text="", was_corrected=False, original={}
        )

        result = service.format_full_address(addr)

        assert "APT 4" in result

    def test_includes_zip4(self):
        """Should format ZIP+4 when present"""
        from services.address_validation_service import AddressValidationService, ValidatedAddress

        service = AddressValidationService()

        addr = ValidatedAddress(
            street="123 MAIN ST", street2="", city="NEW YORK", state="NY",
            zip5="10001", zip4="5678", is_valid=True, error_message="",
            return_text="", was_corrected=False, original={}
        )

        result = service.format_full_address(addr)

        assert "10001-5678" in result


class TestCompareAddresses:
    """Tests for compare_addresses method"""

    def test_detects_no_corrections(self):
        """Should detect when no corrections made"""
        from services.address_validation_service import AddressValidationService, ValidatedAddress

        service = AddressValidationService()

        addr = ValidatedAddress(
            street="123 MAIN ST", street2="", city="NEW YORK", state="NY",
            zip5="10001", zip4="", is_valid=True, error_message="",
            return_text="", was_corrected=False,
            original={"street": "123 MAIN ST", "street2": "", "city": "NEW YORK", "state": "NY", "zip_code": "10001"}
        )

        result = service.compare_addresses(addr)

        assert result['was_corrected'] is False

    def test_detects_corrections(self):
        """Should detect when corrections made"""
        from services.address_validation_service import AddressValidationService, ValidatedAddress

        service = AddressValidationService()

        addr = ValidatedAddress(
            street="123 MAIN STREET", street2="", city="NEW YORK", state="NY",
            zip5="10001", zip4="", is_valid=True, error_message="",
            return_text="", was_corrected=True,
            original={"street": "123 main st", "street2": "", "city": "new york", "state": "ny", "zip_code": "10001"}
        )

        result = service.compare_addresses(addr)

        assert 'corrections' in result
        assert 'formatted_address' in result


class TestSingletonInstance:
    """Tests for singleton instance management"""

    def test_get_service_returns_instance(self):
        """Should return AddressValidationService instance"""
        from services.address_validation_service import get_address_validation_service, AddressValidationService

        import services.address_validation_service as module
        module._service_instance = None

        service = get_address_validation_service()

        assert isinstance(service, AddressValidationService)

    def test_get_service_returns_same_instance(self):
        """Should return same instance"""
        from services.address_validation_service import get_address_validation_service

        import services.address_validation_service as module
        module._service_instance = None

        service1 = get_address_validation_service()
        service2 = get_address_validation_service()

        assert service1 is service2


class TestValidateClientAddress:
    """Tests for validate_client_address convenience function"""

    @patch('services.address_validation_service.get_address_validation_service')
    def test_returns_tuple(self, mock_get_service):
        """Should return tuple of (is_valid, result_dict)"""
        from services.address_validation_service import validate_client_address, ValidatedAddress

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_validated = ValidatedAddress(
            street="123 MAIN ST", street2="", city="NEW YORK", state="NY",
            zip5="10001", zip4="", is_valid=True, error_message="",
            return_text="", was_corrected=False, original={}
        )
        mock_service.validate_address.return_value = mock_validated
        mock_service.compare_addresses.return_value = {
            "was_corrected": False, "corrections": [], "is_valid": True,
            "error_message": "", "formatted_address": ""
        }

        is_valid, result = validate_client_address(
            street="123 Main St", city="New York", state="NY"
        )

        assert isinstance(is_valid, bool)
        assert isinstance(result, dict)

    @patch('services.address_validation_service.get_address_validation_service')
    def test_includes_validated_address(self, mock_get_service):
        """Should include validated_address in result"""
        from services.address_validation_service import validate_client_address, ValidatedAddress

        mock_service = Mock()
        mock_get_service.return_value = mock_service

        mock_validated = ValidatedAddress(
            street="123 MAIN ST", street2="", city="NEW YORK", state="NY",
            zip5="10001", zip4="5678", is_valid=True, error_message="",
            return_text="", was_corrected=False, original={}
        )
        mock_service.validate_address.return_value = mock_validated
        mock_service.compare_addresses.return_value = {
            "was_corrected": False, "corrections": [], "is_valid": True,
            "error_message": "", "formatted_address": ""
        }

        is_valid, result = validate_client_address(
            street="123 Main St", city="New York", state="NY"
        )

        assert 'validated_address' in result
        assert result['validated_address']['street'] == "123 MAIN ST"
