"""
Unit tests for Credit Pull Service
Tests for BaseCreditAdapter implementations and CreditPullService class methods.
"""
import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set TESTING environment variable
os.environ['TESTING'] = 'true'

from services.credit_pull_service import (
    BaseCreditAdapter,
    SmartCreditAdapter,
    IdentityIQAdapter,
    ExperianConnectAdapter,
    CreditPullService,
    PROVIDER_ADAPTERS,
    get_credit_pull_service,
    SERVICE_NAME,
    DISPLAY_NAME,
)


# ============== SmartCreditAdapter Tests ==============


class TestSmartCreditAdapterInit:
    """Tests for SmartCreditAdapter initialization."""

    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        adapter = SmartCreditAdapter(api_key="test_api_key_12345", sandbox=True)
        assert adapter.api_key == "test_api_key_12345"
        assert adapter.sandbox is True
        assert adapter.base_url == SmartCreditAdapter.SANDBOX_BASE_URL

    def test_init_without_api_key_uses_env(self):
        """Test initialization uses environment variable when no key provided."""
        with patch.dict(os.environ, {"SMARTCREDIT_API_KEY": "env_api_key_12345"}):
            adapter = SmartCreditAdapter(sandbox=True)
            assert adapter.api_key == "env_api_key_12345"

    def test_init_production_mode(self):
        """Test initialization in production mode."""
        adapter = SmartCreditAdapter(api_key="prod_key_12345", sandbox=False)
        assert adapter.sandbox is False
        assert adapter.base_url == SmartCreditAdapter.PRODUCTION_BASE_URL

    def test_provider_name(self):
        """Test provider name is correct."""
        adapter = SmartCreditAdapter(api_key="test_key_12345")
        assert adapter.PROVIDER_NAME == "smartcredit"

    def test_is_configured_with_valid_key(self):
        """Test is_configured returns True with valid API key."""
        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        assert adapter.is_configured is True

    def test_is_configured_with_short_key(self):
        """Test is_configured returns False with short API key."""
        adapter = SmartCreditAdapter(api_key="short")
        assert adapter.is_configured is False

    def test_is_configured_with_no_key(self):
        """Test is_configured returns False with no API key."""
        with patch.dict(os.environ, {}, clear=True):
            adapter = SmartCreditAdapter(api_key=None)
            # Remove env var if exists
            if 'SMARTCREDIT_API_KEY' in os.environ:
                del os.environ['SMARTCREDIT_API_KEY']
            adapter.api_key = None
            assert adapter.is_configured is False


class TestSmartCreditAdapterTestConnection:
    """Tests for SmartCreditAdapter test_connection method."""

    def test_test_connection_not_configured(self):
        """Test connection fails when not configured."""
        adapter = SmartCreditAdapter(api_key="short")
        result = adapter.test_connection()
        assert result is False

    @patch('services.credit_pull_service.requests.get')
    def test_test_connection_success_200(self, mock_get):
        """Test connection succeeds with 200 status."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.test_connection()

        assert result is True
        mock_get.assert_called_once()

    @patch('services.credit_pull_service.requests.get')
    def test_test_connection_success_201(self, mock_get):
        """Test connection succeeds with 201 status."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_get.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.test_connection()

        assert result is True

    @patch('services.credit_pull_service.requests.get')
    def test_test_connection_success_401(self, mock_get):
        """Test connection succeeds with 401 (API reachable but auth failed)."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.test_connection()

        assert result is True

    @patch('services.credit_pull_service.requests.get')
    def test_test_connection_failure_500(self, mock_get):
        """Test connection fails with 500 status."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.test_connection()

        assert result is False

    @patch('services.credit_pull_service.requests.get')
    def test_test_connection_request_exception(self, mock_get):
        """Test connection handles request exception."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection error")

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.test_connection()

        assert result is False


class TestSmartCreditAdapterRequestReport:
    """Tests for SmartCreditAdapter request_report method."""

    def test_request_report_not_configured(self):
        """Test request fails when not configured."""
        adapter = SmartCreditAdapter(api_key="short")
        result = adapter.request_report(ssn_last4="1234", dob="1990-01-15")

        assert result["success"] is False
        assert result["request_id"] is None
        assert "not configured" in result["error"]

    @patch('services.credit_pull_service.requests.post')
    def test_request_report_success(self, mock_post):
        """Test successful report request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "request_id": "req_123456",
            "status": "pending"
        }
        mock_post.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.request_report(ssn_last4="1234", dob="1990-01-15")

        assert result["success"] is True
        assert result["request_id"] == "req_123456"
        assert result["status"] == "pending"
        assert result["error"] is None

    @patch('services.credit_pull_service.requests.post')
    def test_request_report_with_full_ssn(self, mock_post):
        """Test report request with full SSN."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "req_789", "status": "processing"}
        mock_post.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.request_report(
            ssn_last4="1234",
            dob="1990-01-15",
            full_ssn="123-45-6789"
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert "ssn" in call_args.kwargs["json"]

    @patch('services.credit_pull_service.requests.post')
    def test_request_report_with_address(self, mock_post):
        """Test report request with address information."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"request_id": "req_456"}
        mock_post.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        address = {"street": "123 Main St", "city": "Test City", "state": "CA", "zip": "90210"}
        result = adapter.request_report(
            ssn_last4="1234",
            dob="1990-01-15",
            address=address
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert "address" in call_args.kwargs["json"]

    @patch('services.credit_pull_service.requests.post')
    def test_request_report_api_error(self, mock_post):
        """Test report request handles API error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request - Invalid SSN format"
        mock_post.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.request_report(ssn_last4="1234", dob="1990-01-15")

        assert result["success"] is False
        assert "API error: 400" in result["error"]

    @patch('services.credit_pull_service.requests.post')
    def test_request_report_network_error(self, mock_post):
        """Test report request handles network error."""
        import requests
        mock_post.side_effect = requests.RequestException("Network timeout")

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.request_report(ssn_last4="1234", dob="1990-01-15")

        assert result["success"] is False
        assert "Network error" in result["error"]


class TestSmartCreditAdapterGetStatus:
    """Tests for SmartCreditAdapter get_status method."""

    def test_get_status_not_configured(self):
        """Test get_status fails when not configured."""
        adapter = SmartCreditAdapter(api_key="short")
        result = adapter.get_status("req_123")

        assert result["success"] is False
        assert "not configured" in result["error"]

    @patch('services.credit_pull_service.requests.get')
    def test_get_status_pending(self, mock_get):
        """Test get_status for pending report."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "pending"}
        mock_get.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.get_status("req_123")

        assert result["success"] is True
        assert result["status"] == "pending"
        assert result["scores"] is None
        assert result["report_ready"] is False

    @patch('services.credit_pull_service.requests.get')
    def test_get_status_complete_with_scores(self, mock_get):
        """Test get_status for completed report with scores."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "complete",
            "experian_score": 720,
            "equifax_score": 715,
            "transunion_score": 710
        }
        mock_get.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.get_status("req_123")

        assert result["success"] is True
        assert result["status"] == "complete"
        assert result["scores"]["experian"] == 720
        assert result["scores"]["equifax"] == 715
        assert result["scores"]["transunion"] == 710
        assert result["report_ready"] is True

    @patch('services.credit_pull_service.requests.get')
    def test_get_status_api_error(self, mock_get):
        """Test get_status handles API error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.get_status("req_invalid")

        assert result["success"] is False
        assert "API error: 404" in result["error"]


class TestSmartCreditAdapterGetReport:
    """Tests for SmartCreditAdapter get_report method."""

    def test_get_report_not_configured(self):
        """Test get_report fails when not configured."""
        adapter = SmartCreditAdapter(api_key="short")
        result = adapter.get_report("req_123")

        assert result["success"] is False
        assert "not configured" in result["error"]

    @patch('services.credit_pull_service.requests.get')
    def test_get_report_success(self, mock_get):
        """Test successful get_report."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"tradelines": [], "inquiries": []}
        mock_get.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.get_report("req_123")

        assert result["success"] is True
        assert result["raw_data"] is not None
        assert result["error"] is None

    @patch('services.credit_pull_service.requests.get')
    def test_get_report_api_error(self, mock_get):
        """Test get_report handles API error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.get_report("req_123")

        assert result["success"] is False
        assert "API error: 500" in result["error"]


class TestSmartCreditAdapterParseReport:
    """Tests for SmartCreditAdapter parse_report method."""

    def test_parse_report_no_data(self):
        """Test parse_report with no data."""
        adapter = SmartCreditAdapter(api_key="test_key_12345")
        result = adapter.parse_report(None)

        assert result["success"] is False
        assert "No data to parse" in result["error"]

    def test_parse_report_success(self):
        """Test successful report parsing."""
        adapter = SmartCreditAdapter(api_key="test_key_12345")
        raw_data = {
            "report_date": "2024-01-15",
            "consumer_name": "John Doe",
            "addresses": [{"street": "123 Main St"}],
            "employers": [{"name": "Test Corp"}],
            "experian_score": 720,
            "equifax_score": 715,
            "transunion_score": 710,
            "tradelines": [
                {
                    "creditor_name": "Test Bank",
                    "account_number_masked": "****1234",
                    "account_type": "Credit Card",
                    "balance": 1500,
                    "credit_limit": 5000,
                    "payment_status": "Current",
                    "date_opened": "2020-01-01",
                    "date_closed": None,
                    "bureaus": ["experian", "equifax"]
                }
            ],
            "inquiries": [
                {
                    "creditor_name": "Auto Dealer",
                    "inquiry_date": "2024-01-10",
                    "inquiry_type": "Hard",
                    "bureau": "experian"
                }
            ],
            "public_records": [],
            "collections": []
        }

        result = adapter.parse_report(raw_data)

        assert result["success"] is True
        assert result["parsed_data"]["provider"] == "smartcredit"
        assert result["parsed_data"]["scores"]["experian"] == 720
        assert len(result["parsed_data"]["tradelines"]) == 1
        assert result["parsed_data"]["tradelines"][0]["creditor"] == "Test Bank"

    def test_parse_report_with_collections(self):
        """Test parsing report with collections."""
        adapter = SmartCreditAdapter(api_key="test_key_12345")
        raw_data = {
            "report_date": "2024-01-15",
            "collections": [
                {
                    "creditor_name": "Collection Agency",
                    "original_creditor": "Medical Center",
                    "account_number_masked": "****5678",
                    "balance": 500,
                    "date_reported": "2023-06-01",
                    "status": "Open"
                }
            ]
        }

        result = adapter.parse_report(raw_data)

        assert result["success"] is True
        assert len(result["parsed_data"]["collections"]) == 1
        assert result["parsed_data"]["collections"][0]["original_creditor"] == "Medical Center"


# ============== IdentityIQAdapter Tests ==============


class TestIdentityIQAdapterInit:
    """Tests for IdentityIQAdapter initialization."""

    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        adapter = IdentityIQAdapter(api_key="test_api_key_12345", sandbox=True)
        assert adapter.api_key == "test_api_key_12345"
        assert adapter.sandbox is True

    def test_provider_name(self):
        """Test provider name is correct."""
        adapter = IdentityIQAdapter(api_key="test_key_12345")
        assert adapter.PROVIDER_NAME == "identityiq"

    def test_get_headers(self):
        """Test headers include API key and secret."""
        with patch.dict(os.environ, {"IDENTITYIQ_API_SECRET": "test_secret"}):
            adapter = IdentityIQAdapter(api_key="test_api_key_12345")
            headers = adapter._get_headers()

            assert headers["X-Api-Key"] == "test_api_key_12345"
            assert headers["Content-Type"] == "application/json"


class TestIdentityIQAdapterTestConnection:
    """Tests for IdentityIQAdapter test_connection method."""

    @patch('services.credit_pull_service.requests.get')
    def test_test_connection_success(self, mock_get):
        """Test successful connection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        adapter = IdentityIQAdapter(api_key="valid_api_key_12345")
        result = adapter.test_connection()

        assert result is True

    @patch('services.credit_pull_service.requests.get')
    def test_test_connection_failure(self, mock_get):
        """Test failed connection."""
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.return_value = mock_response

        adapter = IdentityIQAdapter(api_key="valid_api_key_12345")
        result = adapter.test_connection()

        assert result is False


class TestIdentityIQAdapterRequestReport:
    """Tests for IdentityIQAdapter request_report method."""

    @patch('services.credit_pull_service.requests.post')
    def test_request_report_success(self, mock_post):
        """Test successful report request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "transaction_id": "txn_123456",
            "status": "pending"
        }
        mock_post.return_value = mock_response

        adapter = IdentityIQAdapter(api_key="valid_api_key_12345")
        result = adapter.request_report(
            ssn_last4="1234",
            dob="1990-01-15",
            first_name="John",
            last_name="Doe"
        )

        assert result["success"] is True
        assert result["request_id"] == "txn_123456"


class TestIdentityIQAdapterGetStatus:
    """Tests for IdentityIQAdapter get_status method."""

    @patch('services.credit_pull_service.requests.get')
    def test_get_status_complete(self, mock_get):
        """Test get_status for completed report."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "complete",
            "scores": {"EX": 720, "EQ": 715, "TU": 710}
        }
        mock_get.return_value = mock_response

        adapter = IdentityIQAdapter(api_key="valid_api_key_12345")
        result = adapter.get_status("txn_123")

        assert result["success"] is True
        assert result["status"] == "complete"
        assert result["scores"]["experian"] == 720


class TestIdentityIQAdapterParseReport:
    """Tests for IdentityIQAdapter parse_report method."""

    def test_parse_report_success(self):
        """Test successful report parsing."""
        adapter = IdentityIQAdapter(api_key="test_key_12345")
        raw_data = {
            "pull_date": "2024-01-15",
            "consumer": {
                "name": "John Doe",
                "addresses": [],
                "employers": []
            },
            "scores": {"EX": 720, "EQ": 715, "TU": 710},
            "trade_lines": [
                {
                    "subscriber_name": "Test Bank",
                    "account_number": "****1234",
                    "type": "Revolving",
                    "current_balance": 1500,
                    "high_credit": 5000,
                    "payment_pattern": "Current",
                    "open_date": "2020-01-01",
                    "close_date": None,
                    "bureaus": ["EX"]
                }
            ]
        }

        result = adapter.parse_report(raw_data)

        assert result["success"] is True
        assert result["parsed_data"]["provider"] == "identityiq"
        assert result["parsed_data"]["scores"]["experian"] == 720


# ============== ExperianConnectAdapter Tests ==============


class TestExperianConnectAdapterInit:
    """Tests for ExperianConnectAdapter initialization."""

    def test_init_with_api_key(self):
        """Test initialization with provided API key."""
        adapter = ExperianConnectAdapter(api_key="test_api_key_12345", sandbox=True)
        assert adapter.api_key == "test_api_key_12345"

    def test_provider_name(self):
        """Test provider name is correct."""
        adapter = ExperianConnectAdapter(api_key="test_key_12345")
        assert adapter.PROVIDER_NAME == "experian_connect"

    def test_is_configured_with_client_credentials(self):
        """Test is_configured with OAuth client credentials."""
        with patch.dict(os.environ, {
            "EXPERIAN_CLIENT_ID": "client_id_12345",
            "EXPERIAN_CLIENT_SECRET": "client_secret_12345"
        }):
            adapter = ExperianConnectAdapter(api_key=None)
            adapter.api_key = None
            adapter.client_id = "client_id_12345"
            adapter.client_secret = "client_secret_12345"
            assert adapter.is_configured is True


class TestExperianConnectAdapterGetAccessToken:
    """Tests for ExperianConnectAdapter OAuth token handling."""

    @patch('services.credit_pull_service.requests.post')
    def test_get_access_token_success(self, mock_post):
        """Test successful token retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "expires_in": 3600
        }
        mock_post.return_value = mock_response

        adapter = ExperianConnectAdapter(api_key=None, sandbox=True)
        adapter.client_id = "test_client_id"
        adapter.client_secret = "test_client_secret"

        token = adapter._get_access_token()

        assert token == "new_access_token"
        assert adapter._access_token == "new_access_token"

    def test_get_access_token_uses_cached_token(self):
        """Test cached token is used when not expired."""
        adapter = ExperianConnectAdapter(api_key=None)
        adapter._access_token = "cached_token"
        adapter._token_expires_at = datetime.utcnow().timestamp() + 3600

        token = adapter._get_access_token()

        assert token == "cached_token"


class TestExperianConnectAdapterTestConnection:
    """Tests for ExperianConnectAdapter test_connection method."""

    @patch.object(ExperianConnectAdapter, '_get_access_token')
    def test_test_connection_success(self, mock_get_token):
        """Test successful connection."""
        mock_get_token.return_value = "valid_token"

        adapter = ExperianConnectAdapter(api_key="valid_api_key_12345")
        result = adapter.test_connection()

        assert result is True

    @patch.object(ExperianConnectAdapter, '_get_access_token')
    def test_test_connection_no_token(self, mock_get_token):
        """Test failed connection when token cannot be obtained."""
        mock_get_token.return_value = None

        adapter = ExperianConnectAdapter(api_key="valid_api_key_12345")
        result = adapter.test_connection()

        assert result is False


class TestExperianConnectAdapterRequestReport:
    """Tests for ExperianConnectAdapter request_report method."""

    @patch.object(ExperianConnectAdapter, '_get_access_token')
    @patch('services.credit_pull_service.requests.post')
    def test_request_report_success(self, mock_post, mock_get_token):
        """Test successful report request."""
        mock_get_token.return_value = "valid_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "reportId": "exp_123",
            "creditProfile": {"riskModel": {"score": 720}}
        }
        mock_post.return_value = mock_response

        adapter = ExperianConnectAdapter(api_key="valid_api_key_12345")
        result = adapter.request_report(
            ssn_last4="1234",
            dob="1990-01-15",
            first_name="John",
            last_name="Doe"
        )

        assert result["success"] is True
        assert result["request_id"] == "exp_123"


class TestExperianConnectAdapterGetStatus:
    """Tests for ExperianConnectAdapter get_status method."""

    def test_get_status_returns_complete(self):
        """Test get_status always returns complete for Experian."""
        adapter = ExperianConnectAdapter(api_key="test_key_12345")
        result = adapter.get_status("req_123")

        assert result["success"] is True
        assert result["status"] == "complete"
        assert result["report_ready"] is True


class TestExperianConnectAdapterParseReport:
    """Tests for ExperianConnectAdapter parse_report method."""

    def test_parse_report_success(self):
        """Test successful report parsing."""
        adapter = ExperianConnectAdapter(api_key="test_key_12345")
        raw_data = {
            "creditProfile": {
                "riskModel": {"score": 720},
                "tradeline": [
                    {
                        "subscriberName": "Test Bank",
                        "accountNumber": "****1234",
                        "accountType": "Credit Card",
                        "balance": 1500,
                        "creditLimit": 5000,
                        "paymentStatus": "Current",
                        "openDate": "2020-01-01",
                        "closeDate": None
                    }
                ],
                "inquiry": [
                    {
                        "subscriberName": "Auto Dealer",
                        "inquiryDate": "2024-01-10",
                        "inquiryType": "Hard"
                    }
                ]
            }
        }

        result = adapter.parse_report(raw_data)

        assert result["success"] is True
        assert result["parsed_data"]["provider"] == "experian_connect"
        assert result["parsed_data"]["scores"]["experian"] == 720


# ============== CreditPullService Tests ==============


class TestCreditPullServiceInit:
    """Tests for CreditPullService initialization."""

    def test_init_default_provider(self):
        """Test initialization with default provider."""
        service = CreditPullService()
        assert service.provider_name == "smartcredit"
        assert service.sandbox is True

    def test_init_custom_provider(self):
        """Test initialization with custom provider."""
        service = CreditPullService(provider="identityiq")
        assert service.provider_name == "identityiq"
        assert isinstance(service.adapter, IdentityIQAdapter)

    def test_init_production_mode(self):
        """Test initialization in production mode."""
        service = CreditPullService(sandbox=False)
        assert service.sandbox is False

    def test_init_with_api_key(self):
        """Test initialization with API key."""
        service = CreditPullService(api_key="custom_api_key_12345")
        assert service.adapter.api_key == "custom_api_key_12345"


class TestCreditPullServiceSetProvider:
    """Tests for CreditPullService set_provider method."""

    def test_set_provider_success(self):
        """Test successful provider switch."""
        service = CreditPullService(provider="smartcredit")
        result = service.set_provider("identityiq")

        assert result is True
        assert service.provider_name == "identityiq"
        assert isinstance(service.adapter, IdentityIQAdapter)

    def test_set_provider_unknown_provider(self):
        """Test set_provider with unknown provider."""
        service = CreditPullService()
        result = service.set_provider("unknown_provider")

        assert result is False
        assert service.provider_name == "smartcredit"

    def test_set_provider_with_api_key(self):
        """Test set_provider with custom API key."""
        service = CreditPullService()
        service.set_provider("experian_connect", api_key="custom_key_12345")

        assert service.adapter.api_key == "custom_key_12345"


class TestCreditPullServiceIsConfigured:
    """Tests for CreditPullService is_configured property."""

    def test_is_configured_true(self):
        """Test is_configured returns True when adapter is configured."""
        service = CreditPullService(api_key="valid_api_key_12345")
        assert service.is_configured is True

    def test_is_configured_false_no_adapter(self):
        """Test is_configured returns False when no adapter."""
        service = CreditPullService()
        del service.adapter
        assert service.is_configured is False


class TestCreditPullServiceTestConnection:
    """Tests for CreditPullService test_connection method."""

    @patch.object(SmartCreditAdapter, 'test_connection')
    @patch('services.credit_pull_service.SessionLocal')
    def test_test_connection_success(self, mock_session, mock_adapter_test):
        """Test successful connection test."""
        mock_adapter_test.return_value = True
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        service = CreditPullService(api_key="valid_api_key_12345")
        result = service.test_connection()

        assert result is True
        mock_adapter_test.assert_called_once()

    def test_test_connection_no_adapter(self):
        """Test test_connection fails with no adapter."""
        service = CreditPullService()
        del service.adapter
        result = service.test_connection()

        assert result is False


class TestCreditPullServiceRequestCreditReport:
    """Tests for CreditPullService request_credit_report method."""

    @patch('services.credit_pull_service.SessionLocal')
    @patch.object(SmartCreditAdapter, 'request_report')
    def test_request_credit_report_success(self, mock_request, mock_session):
        """Test successful credit report request."""
        mock_db = Mock()
        mock_session.return_value = mock_db

        mock_client = Mock()
        mock_client.id = 1
        mock_client.first_name = "John"
        mock_client.last_name = "Doe"
        mock_client.address_street = "123 Main St"
        mock_client.address_city = "Test City"
        mock_client.address_state = "CA"
        mock_client.address_zip = "90210"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        mock_request.return_value = {
            "success": True,
            "request_id": "req_123",
            "status": "pending",
            "error": None
        }

        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 100))

        service = CreditPullService(api_key="valid_api_key_12345")
        result = service.request_credit_report(
            client_id=1,
            ssn_last4="1234",
            dob="1990-01-15"
        )

        assert result["success"] is True
        assert result["request_id"] == 100
        assert result["external_id"] == "req_123"

    @patch('services.credit_pull_service.SessionLocal')
    def test_request_credit_report_client_not_found(self, mock_session):
        """Test request fails when client not found."""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        service = CreditPullService(api_key="valid_api_key_12345")
        result = service.request_credit_report(
            client_id=999,
            ssn_last4="1234",
            dob="1990-01-15"
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_request_credit_report_no_adapter(self):
        """Test request fails with no adapter."""
        service = CreditPullService()
        del service.adapter
        result = service.request_credit_report(
            client_id=1,
            ssn_last4="1234",
            dob="1990-01-15"
        )

        assert result["success"] is False
        assert "No credit provider configured" in result["error"]


class TestCreditPullServiceGetReportStatus:
    """Tests for CreditPullService get_report_status method."""

    @patch('services.credit_pull_service.SessionLocal')
    def test_get_report_status_not_found(self, mock_session):
        """Test get_report_status when request not found."""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        service = CreditPullService()
        result = service.get_report_status(request_id=999)

        assert result["success"] is False
        assert result["status"] == "not_found"

    @patch('services.credit_pull_service.SessionLocal')
    def test_get_report_status_complete(self, mock_session):
        """Test get_report_status for complete request."""
        mock_db = Mock()
        mock_session.return_value = mock_db

        mock_pull_request = Mock()
        mock_pull_request.status = "complete"
        mock_pull_request.score_experian = 720
        mock_pull_request.score_equifax = 715
        mock_pull_request.score_transunion = 710
        mock_pull_request.raw_response_path = "/path/to/report"
        mock_pull_request.parsed_data = {"tradelines": []}
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_pull_request

        service = CreditPullService()
        result = service.get_report_status(request_id=1)

        assert result["success"] is True
        assert result["status"] == "complete"
        assert result["scores"]["experian"] == 720


class TestCreditPullServiceGetParsedReport:
    """Tests for CreditPullService get_parsed_report method."""

    @patch('services.credit_pull_service.SessionLocal')
    def test_get_parsed_report_not_found(self, mock_session):
        """Test get_parsed_report when request not found."""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        service = CreditPullService()
        result = service.get_parsed_report(request_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.credit_pull_service.SessionLocal')
    def test_get_parsed_report_cached(self, mock_session):
        """Test get_parsed_report returns cached data."""
        mock_db = Mock()
        mock_session.return_value = mock_db

        mock_pull_request = Mock()
        mock_pull_request.parsed_data = {"tradelines": [], "scores": {}}
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_pull_request

        service = CreditPullService()
        result = service.get_parsed_report(request_id=1)

        assert result["success"] is True
        assert result["parsed_data"] is not None


class TestCreditPullServiceParseCreditReport:
    """Tests for CreditPullService parse_credit_report method."""

    def test_parse_credit_report_success(self):
        """Test successful report parsing."""
        service = CreditPullService(api_key="test_key_12345")
        raw_data = {
            "report_date": "2024-01-15",
            "experian_score": 720,
            "tradelines": []
        }

        result = service.parse_credit_report(raw_data)

        assert result["success"] is True

    def test_parse_credit_report_no_adapter(self):
        """Test parsing fails with no adapter."""
        service = CreditPullService()
        del service.adapter

        result = service.parse_credit_report({"data": "test"})

        assert result["success"] is False
        assert "No adapter configured" in result["error"]


class TestCreditPullServiceGetClientPulls:
    """Tests for CreditPullService get_client_pulls method."""

    @patch('services.credit_pull_service.SessionLocal')
    def test_get_client_pulls_success(self, mock_session):
        """Test successful retrieval of client pulls."""
        mock_db = Mock()
        mock_session.return_value = mock_db

        mock_pull = Mock()
        mock_pull.id = 1
        mock_pull.provider = "smartcredit"
        mock_pull.status = "complete"
        mock_pull.report_type = "tri-merge"
        mock_pull.score_experian = 720
        mock_pull.score_equifax = 715
        mock_pull.score_transunion = 710
        mock_pull.pulled_at = datetime.utcnow()
        mock_pull.created_at = datetime.utcnow()
        mock_pull.error_message = None

        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [mock_pull]

        service = CreditPullService()
        result = service.get_client_pulls(client_id=1)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["scores"]["experian"] == 720


class TestCreditPullServiceGetAvailableProviders:
    """Tests for CreditPullService get_available_providers method."""

    def test_get_available_providers(self):
        """Test retrieval of available providers."""
        service = CreditPullService()
        providers = service.get_available_providers()

        assert len(providers) == 3
        provider_names = [p["name"] for p in providers]
        assert "smartcredit" in provider_names
        assert "identityiq" in provider_names
        assert "experian_connect" in provider_names


class TestCreditPullServiceGetRequiredEnvVars:
    """Tests for CreditPullService _get_required_env_vars method."""

    def test_get_required_env_vars_smartcredit(self):
        """Test required env vars for SmartCredit."""
        service = CreditPullService()
        env_vars = service._get_required_env_vars("smartcredit")

        assert "SMARTCREDIT_API_KEY" in env_vars

    def test_get_required_env_vars_identityiq(self):
        """Test required env vars for IdentityIQ."""
        service = CreditPullService()
        env_vars = service._get_required_env_vars("identityiq")

        assert "IDENTITYIQ_API_KEY" in env_vars
        assert "IDENTITYIQ_API_SECRET" in env_vars

    def test_get_required_env_vars_experian(self):
        """Test required env vars for Experian Connect."""
        service = CreditPullService()
        env_vars = service._get_required_env_vars("experian_connect")

        assert "EXPERIAN_CLIENT_ID" in env_vars
        assert "EXPERIAN_CLIENT_SECRET" in env_vars
        assert "EXPERIAN_SUBSCRIBER_CODE" in env_vars

    def test_get_required_env_vars_unknown(self):
        """Test required env vars for unknown provider."""
        service = CreditPullService()
        env_vars = service._get_required_env_vars("unknown_provider")

        assert env_vars == []


# ============== Factory Function Tests ==============


class TestFactoryFunction:
    """Tests for get_credit_pull_service factory function."""

    def test_get_credit_pull_service_default(self):
        """Test factory returns CreditPullService instance."""
        service = get_credit_pull_service()
        assert isinstance(service, CreditPullService)
        assert service.provider_name == "smartcredit"

    def test_get_credit_pull_service_custom_provider(self):
        """Test factory with custom provider."""
        service = get_credit_pull_service(provider="identityiq")
        assert service.provider_name == "identityiq"

    def test_get_credit_pull_service_production_mode(self):
        """Test factory in production mode."""
        service = get_credit_pull_service(sandbox=False)
        assert service.sandbox is False


# ============== Provider Registry Tests ==============


class TestProviderRegistry:
    """Tests for PROVIDER_ADAPTERS registry."""

    def test_provider_adapters_contains_all_providers(self):
        """Test all providers are registered."""
        assert "smartcredit" in PROVIDER_ADAPTERS
        assert "identityiq" in PROVIDER_ADAPTERS
        assert "experian_connect" in PROVIDER_ADAPTERS

    def test_provider_adapters_classes_correct(self):
        """Test registered adapter classes are correct."""
        assert PROVIDER_ADAPTERS["smartcredit"] == SmartCreditAdapter
        assert PROVIDER_ADAPTERS["identityiq"] == IdentityIQAdapter
        assert PROVIDER_ADAPTERS["experian_connect"] == ExperianConnectAdapter


# ============== Constants Tests ==============


class TestConstants:
    """Tests for module constants."""

    def test_service_name(self):
        """Test SERVICE_NAME constant."""
        assert SERVICE_NAME == "credit_pull"

    def test_display_name(self):
        """Test DISPLAY_NAME constant."""
        assert DISPLAY_NAME == "Credit Pull Service"


# ============== Edge Cases Tests ==============


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_adapter_sandbox_urls_defined(self):
        """Test all adapters have sandbox URLs defined."""
        for adapter_class in PROVIDER_ADAPTERS.values():
            assert adapter_class.SANDBOX_BASE_URL != ""

    def test_adapter_production_urls_defined(self):
        """Test all adapters have production URLs defined."""
        for adapter_class in PROVIDER_ADAPTERS.values():
            assert adapter_class.PRODUCTION_BASE_URL != ""

    def test_smartcredit_headers_include_authorization(self):
        """Test SmartCredit headers include Authorization."""
        adapter = SmartCreditAdapter(api_key="test_key_12345")
        headers = adapter._get_headers()

        assert "Authorization" in headers
        assert headers["Authorization"].startswith("Bearer ")

    @patch('services.credit_pull_service.requests.get')
    def test_smartcredit_get_report_network_error(self, mock_get):
        """Test get_report handles network errors."""
        import requests
        mock_get.side_effect = requests.RequestException("Timeout")

        adapter = SmartCreditAdapter(api_key="valid_api_key_12345")
        result = adapter.get_report("req_123")

        assert result["success"] is False
        assert "Network error" in result["error"]

    @patch('services.credit_pull_service.requests.get')
    def test_identityiq_get_status_network_error(self, mock_get):
        """Test IdentityIQ get_status handles network errors."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection refused")

        adapter = IdentityIQAdapter(api_key="valid_api_key_12345")
        result = adapter.get_status("txn_123")

        assert result["success"] is False
        assert "Network error" in result["error"]

    def test_parse_report_exception_handling(self):
        """Test parse_report handles exceptions gracefully."""
        adapter = SmartCreditAdapter(api_key="test_key_12345")
        # Pass data that will cause an exception during parsing
        raw_data = Mock()
        raw_data.get.side_effect = Exception("Unexpected error")

        result = adapter.parse_report(raw_data)

        assert result["success"] is False
        assert "Parse error" in result["error"]
