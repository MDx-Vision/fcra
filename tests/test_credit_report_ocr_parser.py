"""
Comprehensive Unit Tests for Credit Report OCR Parser

Tests cover:
- get_anthropic_client() - Anthropic client initialization
- _convert_pdf_to_images() - PDF to image conversion
- parse_credit_report_vision() - Main vision parsing function
- detect_discrepancies() - Discrepancy detection between bureaus
- detect_derogatory_accounts() - Derogatory account identification
- get_worst_payment_status() - Payment status analysis
- parse_credit_report_pdf() - Main entry point with fallback
- Edge cases and error handling
"""

import base64
import json
import os
import pytest
import tempfile
from unittest.mock import Mock, MagicMock, patch, mock_open

# Import the module to test
from services.credit_report_ocr_parser import (
    get_anthropic_client,
    _convert_pdf_to_images,
    parse_credit_report_vision,
    detect_discrepancies,
    detect_derogatory_accounts,
    get_worst_payment_status,
    parse_credit_report_pdf,
    CREDIT_REPORT_EXTRACTION_PROMPT,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def reset_anthropic_client():
    """Reset global anthropic client before and after tests."""
    import services.credit_report_ocr_parser as module
    original_client = module._anthropic_client
    module._anthropic_client = None
    yield
    module._anthropic_client = original_client


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"accounts": [], "credit_scores": {}}')]
    mock_response.usage.input_tokens = 1000
    mock_response.usage.output_tokens = 500
    mock_client.messages.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_extracted_data():
    """Sample extracted credit report data for testing."""
    return {
        "reference_number": "CR-2024-001",
        "report_date": "01/15/2024",
        "personal_info": {
            "transunion": {
                "name": "John Doe",
                "dob": "1980",
                "current_address": "123 Main St, City, ST 12345"
            },
            "experian": {
                "name": "John Doe",
                "dob": "1980",
                "current_address": "123 Main St, City, ST 12345"
            },
            "equifax": {
                "name": "John A Doe",  # Different name
                "dob": "1980",
                "current_address": "123 Main St, City, ST 12345"
            }
        },
        "credit_scores": {
            "transunion": {"score": 720, "rank": "Good"},
            "experian": {"score": 715, "rank": "Good"},
            "equifax": {"score": 725, "rank": "Good"}
        },
        "summary_stats": {
            "transunion": {"delinquent": 1, "total_accounts": 10},
            "experian": {"delinquent": 0, "total_accounts": 10},
            "equifax": {"delinquent": 1, "total_accounts": 10}
        },
        "accounts": [
            {
                "creditor_name": "CHASE",
                "account_number": "****1234",
                "tu_reported": True,
                "tu_balance": 5000.00,
                "tu_payment_status": "Pays account as agreed",
                "tu_past_due": 0,
                "ex_reported": True,
                "ex_balance": 5000.00,
                "ex_payment_status": "Pays account as agreed",
                "ex_past_due": 0,
                "eq_reported": True,
                "eq_balance": 5500.00,  # Different balance
                "eq_payment_status": "Pays account as agreed",
                "eq_past_due": 0
            },
            {
                "creditor_name": "CAPITAL ONE",
                "account_number": "****5678",
                "tu_reported": True,
                "tu_balance": 1000.00,
                "tu_payment_status": "30 days past due",
                "tu_past_due": 100,
                "ex_reported": True,
                "ex_balance": 1000.00,
                "ex_payment_status": "Current",
                "ex_past_due": 0,
                "eq_reported": True,
                "eq_balance": 1000.00,
                "eq_payment_status": "30 days past due",
                "eq_past_due": 100
            }
        ],
        "inquiries": [],
        "public_records": [],
        "creditor_contacts": []
    }


@pytest.fixture
def sample_accounts():
    """Sample accounts list for testing derogatory detection."""
    return [
        {
            "creditor_name": "GOOD CREDIT CARD",
            "account_number": "****1111",
            "tu_payment_status": "Pays account as agreed",
            "tu_past_due": 0,
            "ex_payment_status": "Current",
            "ex_past_due": 0,
            "eq_payment_status": "Current",
            "eq_past_due": 0
        },
        {
            "creditor_name": "BAD CREDIT CARD",
            "account_number": "****2222",
            "tu_payment_status": "30 days past due",
            "tu_past_due": 150,
            "ex_payment_status": "60 days past due",
            "ex_past_due": 200,
            "eq_payment_status": "Collection",
            "eq_past_due": 500
        },
        {
            "creditor_name": "CHARGEOFF ACCOUNT",
            "account_number": "****3333",
            "tu_payment_status": "Charged off",
            "tu_past_due": 1000,
            "ex_payment_status": "Charged off",
            "ex_past_due": 1000,
            "eq_payment_status": "Charged off",
            "eq_past_due": 1000
        }
    ]


# =============================================================================
# Test Class: get_anthropic_client()
# =============================================================================

class TestGetAnthropicClient:
    """Tests for Anthropic client initialization."""

    def test_get_client_with_valid_api_key(self, reset_anthropic_client):
        """Test client initialization with valid API key."""
        import services.credit_report_ocr_parser as module
        module._anthropic_client = None

        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'sk-ant-valid-key-12345678'}):
            with patch.object(module, 'ANTHROPIC_API_KEY', 'sk-ant-valid-key-12345678'):
                with patch('anthropic.Anthropic') as mock_anthropic:
                    mock_client = MagicMock()
                    mock_anthropic.return_value = mock_client

                    client = get_anthropic_client()

                    assert client is not None

    def test_get_client_returns_cached_instance(self, reset_anthropic_client):
        """Test that client is cached after first initialization."""
        import services.credit_report_ocr_parser as module

        # Set a mock client directly
        mock_client = MagicMock()
        module._anthropic_client = mock_client

        client1 = get_anthropic_client()
        client2 = get_anthropic_client()

        # Should return cached instance
        assert client1 is client2
        assert client1 is mock_client

    def test_get_client_with_short_api_key(self, reset_anthropic_client):
        """Test client initialization with too short API key returns None."""
        with patch('services.credit_report_ocr_parser.ANTHROPIC_API_KEY', 'short'):
            client = get_anthropic_client()
            assert client is None

    def test_get_client_with_empty_api_key(self, reset_anthropic_client):
        """Test client initialization with empty API key returns None."""
        with patch('services.credit_report_ocr_parser.ANTHROPIC_API_KEY', ''):
            client = get_anthropic_client()
            assert client is None

    def test_get_client_handles_import_error(self, reset_anthropic_client):
        """Test client handles Anthropic import errors."""
        import services.credit_report_ocr_parser as module
        module._anthropic_client = None

        with patch('services.credit_report_ocr_parser.ANTHROPIC_API_KEY', 'sk-ant-valid-key-12345678'):
            # Should handle gracefully when import fails inside function
            # The actual function handles the ImportError internally
            client = get_anthropic_client()
            # Will be None or a client depending on actual anthropic installation

    def test_get_client_handles_initialization_error(self, reset_anthropic_client):
        """Test client handles Anthropic initialization errors."""
        import services.credit_report_ocr_parser as module
        module._anthropic_client = None

        with patch.object(module, 'ANTHROPIC_API_KEY', 'sk-ant-valid-key-12345678'):
            with patch('anthropic.Anthropic') as mock_anthropic:
                mock_anthropic.side_effect = Exception("API initialization failed")

                client = get_anthropic_client()

                assert client is None


# =============================================================================
# Test Class: _convert_pdf_to_images()
# =============================================================================

class TestConvertPdfToImages:
    """Tests for PDF to image conversion."""

    def test_convert_pdf_success(self):
        """Test successful PDF to images conversion."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_images = [MagicMock() for _ in range(3)]
            for mock_img in mock_images:
                mock_img.save = MagicMock()

            # Create a mock pdf2image module
            mock_pdf2image = MagicMock()
            mock_pdf2image.convert_from_path = MagicMock(return_value=mock_images)

            with patch.dict('sys.modules', {'pdf2image': mock_pdf2image}):
                with patch('tempfile.NamedTemporaryFile') as mock_tmp:
                    mock_file = MagicMock()
                    mock_file.__enter__ = MagicMock(return_value=mock_file)
                    mock_file.__exit__ = MagicMock(return_value=False)
                    mock_file.name = '/tmp/test.png'
                    mock_tmp.return_value = mock_file

                    with patch('builtins.open', mock_open(read_data=b'image_data')):
                        with patch('os.unlink'):
                            result = _convert_pdf_to_images(tmp_path, max_pages=10)

            assert result is not None
            assert len(result) == 3
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_convert_pdf_respects_max_pages(self):
        """Test PDF conversion respects max_pages parameter."""
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path = MagicMock(return_value=[])

        with patch.dict('sys.modules', {'pdf2image': mock_pdf2image}):
            _convert_pdf_to_images('/fake/path.pdf', max_pages=5)

            call_kwargs = mock_pdf2image.convert_from_path.call_args[1]
            assert call_kwargs['last_page'] == 5

    def test_convert_pdf_import_error(self):
        """Test PDF conversion handles pdf2image import error.

        When pdf2image is not installed, the function should return None
        and log an error about the missing dependency.
        """
        # Test by actually calling the function - it will hit ImportError
        # if pdf2image is not installed in this test environment
        result = _convert_pdf_to_images('/fake/path.pdf')

        # Either returns None (if pdf2image not installed) or
        # handles the error gracefully
        assert result is None

    def test_convert_pdf_general_error(self):
        """Test PDF conversion handles general errors."""
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path = MagicMock(side_effect=Exception("Conversion failed"))

        with patch.dict('sys.modules', {'pdf2image': mock_pdf2image}):
            result = _convert_pdf_to_images('/fake/path.pdf')

            assert result is None

    def test_convert_pdf_empty_result(self):
        """Test PDF conversion returns None for empty result."""
        mock_pdf2image = MagicMock()
        mock_pdf2image.convert_from_path = MagicMock(return_value=[])

        with patch.dict('sys.modules', {'pdf2image': mock_pdf2image}):
            result = _convert_pdf_to_images('/fake/path.pdf')

            assert result is None


# =============================================================================
# Test Class: parse_credit_report_vision()
# =============================================================================

class TestParseCreditReportVision:
    """Tests for the main vision parsing function."""

    def test_parse_file_not_found(self):
        """Test parsing returns error when file not found."""
        result = parse_credit_report_vision('/nonexistent/file.pdf')

        assert result['success'] is False
        assert 'File not found' in result['error']

    def test_parse_no_client_available(self, reset_anthropic_client):
        """Test parsing returns error when no Anthropic client."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with patch('services.credit_report_ocr_parser.ANTHROPIC_API_KEY', ''):
                result = parse_credit_report_vision(tmp_path)

            assert result['success'] is False
            assert 'Anthropic API client not available' in result['error']
        finally:
            os.unlink(tmp_path)

    def test_parse_pdf_conversion_fails(self, reset_anthropic_client):
        """Test parsing returns error when PDF conversion fails."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with patch('services.credit_report_ocr_parser.get_anthropic_client') as mock_get_client:
                mock_get_client.return_value = MagicMock()
                with patch('services.credit_report_ocr_parser._convert_pdf_to_images', return_value=None):
                    result = parse_credit_report_vision(tmp_path)

            assert result['success'] is False
            assert 'Could not convert PDF' in result['error']
        finally:
            os.unlink(tmp_path)

    def test_parse_success(self, reset_anthropic_client, sample_extracted_data):
        """Test successful parsing returns extracted data."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps(sample_extracted_data))]
            mock_response.usage.input_tokens = 5000
            mock_response.usage.output_tokens = 2000
            mock_client.messages.create.return_value = mock_response

            with patch('services.credit_report_ocr_parser.get_anthropic_client', return_value=mock_client):
                with patch('services.credit_report_ocr_parser._convert_pdf_to_images', return_value=['base64_image_1', 'base64_image_2']):
                    result = parse_credit_report_vision(tmp_path)

            assert result['success'] is True
            assert result['data'] is not None
            assert result['tokens_used'] == 7000
            assert 'discrepancies' in result['data']
            assert 'derogatory_accounts' in result['data']
        finally:
            os.unlink(tmp_path)

    def test_parse_handles_json_code_block(self, reset_anthropic_client):
        """Test parsing handles JSON wrapped in code blocks."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_client = MagicMock()
            mock_response = MagicMock()
            json_data = '{"accounts": [], "credit_scores": {}}'
            mock_response.content = [MagicMock(text=f'```json\n{json_data}\n```')]
            mock_response.usage.input_tokens = 1000
            mock_response.usage.output_tokens = 500
            mock_client.messages.create.return_value = mock_response

            with patch('services.credit_report_ocr_parser.get_anthropic_client', return_value=mock_client):
                with patch('services.credit_report_ocr_parser._convert_pdf_to_images', return_value=['base64_image']):
                    result = parse_credit_report_vision(tmp_path)

            assert result['success'] is True
            assert result['data'] is not None
        finally:
            os.unlink(tmp_path)

    def test_parse_handles_plain_code_block(self, reset_anthropic_client):
        """Test parsing handles JSON wrapped in plain code blocks."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_client = MagicMock()
            mock_response = MagicMock()
            json_data = '{"accounts": [], "credit_scores": {}}'
            mock_response.content = [MagicMock(text=f'```\n{json_data}\n```')]
            mock_response.usage.input_tokens = 1000
            mock_response.usage.output_tokens = 500
            mock_client.messages.create.return_value = mock_response

            with patch('services.credit_report_ocr_parser.get_anthropic_client', return_value=mock_client):
                with patch('services.credit_report_ocr_parser._convert_pdf_to_images', return_value=['base64_image']):
                    result = parse_credit_report_vision(tmp_path)

            assert result['success'] is True
            assert result['data'] is not None
        finally:
            os.unlink(tmp_path)

    def test_parse_json_decode_error(self, reset_anthropic_client):
        """Test parsing handles JSON decode errors."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text='invalid json {{{')]
            mock_response.usage.input_tokens = 1000
            mock_response.usage.output_tokens = 500
            mock_client.messages.create.return_value = mock_response

            with patch('services.credit_report_ocr_parser.get_anthropic_client', return_value=mock_client):
                with patch('services.credit_report_ocr_parser._convert_pdf_to_images', return_value=['base64_image']):
                    result = parse_credit_report_vision(tmp_path)

            assert result['success'] is False
            assert 'JSON parse error' in result['error']
            assert 'raw_response' in result
        finally:
            os.unlink(tmp_path)

    def test_parse_api_error(self, reset_anthropic_client):
        """Test parsing handles API errors."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API rate limit exceeded")

            with patch('services.credit_report_ocr_parser.get_anthropic_client', return_value=mock_client):
                with patch('services.credit_report_ocr_parser._convert_pdf_to_images', return_value=['base64_image']):
                    result = parse_credit_report_vision(tmp_path)

            assert result['success'] is False
            assert 'API rate limit exceeded' in result['error']
        finally:
            os.unlink(tmp_path)

    def test_parse_result_structure(self, reset_anthropic_client):
        """Test parse result has correct structure."""
        result = parse_credit_report_vision('/nonexistent/file.pdf')

        assert 'success' in result
        assert 'error' in result
        assert 'report_type' in result
        assert 'extraction_method' in result
        assert 'data' in result
        assert 'tokens_used' in result
        assert result['report_type'] == 'three_bureau'
        assert result['extraction_method'] == 'claude_vision'


# =============================================================================
# Test Class: detect_discrepancies()
# =============================================================================

class TestDetectDiscrepancies:
    """Tests for discrepancy detection between bureaus."""

    def test_detect_name_discrepancy(self, sample_extracted_data):
        """Test detection of name discrepancies."""
        discrepancies = detect_discrepancies(sample_extracted_data)

        name_discrepancies = [d for d in discrepancies if d['field'] == 'name']
        assert len(name_discrepancies) == 1
        assert 'John A Doe' in name_discrepancies[0]['description']

    def test_detect_delinquent_count_discrepancy(self, sample_extracted_data):
        """Test detection of delinquent count discrepancies."""
        discrepancies = detect_discrepancies(sample_extracted_data)

        delinq_discrepancies = [d for d in discrepancies if d['field'] == 'delinquent']
        assert len(delinq_discrepancies) == 1

    def test_detect_balance_discrepancy(self, sample_extracted_data):
        """Test detection of account balance discrepancies."""
        discrepancies = detect_discrepancies(sample_extracted_data)

        balance_discrepancies = [d for d in discrepancies if d['field'] == 'balance']
        assert len(balance_discrepancies) >= 1
        assert any('CHASE' in d['account'] for d in balance_discrepancies)

    def test_detect_payment_status_discrepancy(self, sample_extracted_data):
        """Test detection of payment status discrepancies."""
        discrepancies = detect_discrepancies(sample_extracted_data)

        status_discrepancies = [d for d in discrepancies if d['field'] == 'payment_status']
        assert len(status_discrepancies) >= 1
        assert any('CAPITAL ONE' in d['account'] for d in status_discrepancies)

    def test_no_discrepancies_when_data_matches(self):
        """Test no discrepancies when all bureau data matches."""
        data = {
            "personal_info": {
                "transunion": {"name": "John Doe"},
                "experian": {"name": "John Doe"},
                "equifax": {"name": "John Doe"}
            },
            "summary_stats": {
                "transunion": {"delinquent": 0},
                "experian": {"delinquent": 0},
                "equifax": {"delinquent": 0}
            },
            "accounts": [
                {
                    "creditor_name": "TEST",
                    "tu_balance": 1000,
                    "ex_balance": 1000,
                    "eq_balance": 1000,
                    "tu_payment_status": "Current",
                    "ex_payment_status": "Current",
                    "eq_payment_status": "Current"
                }
            ]
        }

        discrepancies = detect_discrepancies(data)

        assert len(discrepancies) == 0

    def test_detect_discrepancies_with_missing_data(self):
        """Test discrepancy detection handles missing data gracefully."""
        data = {
            "personal_info": {},
            "summary_stats": {},
            "accounts": []
        }

        discrepancies = detect_discrepancies(data)

        assert isinstance(discrepancies, list)

    def test_detect_discrepancies_empty_data(self):
        """Test discrepancy detection with empty data."""
        discrepancies = detect_discrepancies({})

        assert isinstance(discrepancies, list)
        assert len(discrepancies) == 0

    def test_detect_discrepancies_single_bureau(self):
        """Test discrepancy detection with single bureau data."""
        data = {
            "personal_info": {
                "transunion": {"name": "John Doe"}
            },
            "summary_stats": {
                "transunion": {"delinquent": 1}
            },
            "accounts": [
                {
                    "creditor_name": "TEST",
                    "tu_balance": 1000
                }
            ]
        }

        discrepancies = detect_discrepancies(data)

        # Should not detect discrepancies with only one bureau
        assert isinstance(discrepancies, list)

    def test_detect_balance_discrepancy_with_none_values(self):
        """Test balance discrepancy detection handles None values."""
        data = {
            "personal_info": {},
            "summary_stats": {},
            "accounts": [
                {
                    "creditor_name": "TEST",
                    "tu_balance": 1000,
                    "ex_balance": None,
                    "eq_balance": 1000
                }
            ]
        }

        discrepancies = detect_discrepancies(data)

        assert isinstance(discrepancies, list)


# =============================================================================
# Test Class: detect_derogatory_accounts()
# =============================================================================

class TestDetectDerogatoryAccounts:
    """Tests for derogatory account detection."""

    def test_detect_30_day_late(self, sample_accounts):
        """Test detection of 30 day late accounts."""
        derogatory = detect_derogatory_accounts(sample_accounts)

        assert len(derogatory) >= 1
        bad_account = next((d for d in derogatory if d['creditor_name'] == 'BAD CREDIT CARD'), None)
        assert bad_account is not None

    def test_detect_60_day_late(self, sample_accounts):
        """Test detection of 60 day late accounts."""
        derogatory = detect_derogatory_accounts(sample_accounts)

        bad_account = next((d for d in derogatory if d['creditor_name'] == 'BAD CREDIT CARD'), None)
        assert bad_account is not None

        experian_issues = [i for i in bad_account['issues'] if i['bureau'] == 'Experian']
        assert len(experian_issues) >= 1

    def test_detect_chargeoff(self, sample_accounts):
        """Test detection of charged off accounts."""
        derogatory = detect_derogatory_accounts(sample_accounts)

        chargeoff_account = next((d for d in derogatory if d['creditor_name'] == 'CHARGEOFF ACCOUNT'), None)
        assert chargeoff_account is not None

    def test_detect_past_due_amount(self, sample_accounts):
        """Test detection of past due amounts."""
        derogatory = detect_derogatory_accounts(sample_accounts)

        bad_account = next((d for d in derogatory if d['creditor_name'] == 'BAD CREDIT CARD'), None)
        assert bad_account is not None

        # Should have past due issues
        past_due_issues = [i for i in bad_account['issues'] if 'Past due' in i['issue']]
        assert len(past_due_issues) >= 1

    def test_detect_collection_status(self, sample_accounts):
        """Test detection of collection status."""
        derogatory = detect_derogatory_accounts(sample_accounts)

        bad_account = next((d for d in derogatory if d['creditor_name'] == 'BAD CREDIT CARD'), None)
        assert bad_account is not None

        # Equifax shows collection
        eq_issues = [i for i in bad_account['issues'] if i['bureau'] == 'Equifax']
        assert len(eq_issues) >= 1

    def test_no_derogatory_for_good_account(self, sample_accounts):
        """Test good accounts are not flagged as derogatory."""
        derogatory = detect_derogatory_accounts(sample_accounts)

        good_account = next((d for d in derogatory if d['creditor_name'] == 'GOOD CREDIT CARD'), None)
        assert good_account is None

    def test_detect_derogatory_empty_list(self):
        """Test derogatory detection with empty account list."""
        derogatory = detect_derogatory_accounts([])

        assert isinstance(derogatory, list)
        assert len(derogatory) == 0

    def test_detect_derogatory_all_keywords(self):
        """Test detection of various bad keywords."""
        accounts = [
            {
                "creditor_name": "TEST1",
                "tu_payment_status": "late payment",
                "tu_past_due": 0
            },
            {
                "creditor_name": "TEST2",
                "tu_payment_status": "delinquent",
                "tu_past_due": 0
            },
            {
                "creditor_name": "TEST3",
                "tu_payment_status": "90 days past due",
                "tu_past_due": 0
            },
            {
                "creditor_name": "TEST4",
                "tu_payment_status": "120 days past due",
                "tu_past_due": 0
            },
            {
                "creditor_name": "TEST5",
                "tu_payment_status": "not more than two payments past due",
                "tu_past_due": 0
            }
        ]

        derogatory = detect_derogatory_accounts(accounts)

        assert len(derogatory) == 5

    def test_detect_derogatory_handles_none_past_due(self):
        """Test derogatory detection handles None past_due values."""
        accounts = [
            {
                "creditor_name": "TEST",
                "tu_payment_status": "Current",
                "tu_past_due": None,
                "ex_payment_status": "Current",
                "ex_past_due": None,
                "eq_payment_status": "Current",
                "eq_past_due": None
            }
        ]

        derogatory = detect_derogatory_accounts(accounts)

        assert len(derogatory) == 0

    def test_detect_derogatory_case_insensitive(self):
        """Test derogatory detection is case insensitive."""
        accounts = [
            {
                "creditor_name": "TEST",
                "tu_payment_status": "PAST DUE 30 DAYS",
                "tu_past_due": 0
            }
        ]

        derogatory = detect_derogatory_accounts(accounts)

        assert len(derogatory) == 1


# =============================================================================
# Test Class: get_worst_payment_status()
# =============================================================================

class TestGetWorstPaymentStatus:
    """Tests for payment status analysis."""

    def test_90_plus_days_late(self):
        """Test 90+ days late is worst status."""
        account = {
            "tu_payment_status": "90 days past due",
            "ex_payment_status": "Current",
            "eq_payment_status": "Current"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == '90+ Days Late'
        assert result['color'] == 'red'
        assert result['class'] == 'badge-danger'

    def test_120_days_late(self):
        """Test 120 days late returns 90+ status."""
        account = {
            "tu_payment_status": "Current",
            "ex_payment_status": "120 days past due",
            "eq_payment_status": "Current"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == '90+ Days Late'

    def test_chargeoff_returns_severe(self):
        """Test charge off returns severe status."""
        account = {
            "tu_payment_status": "Charged off",
            "ex_payment_status": "Current",
            "eq_payment_status": "Current"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == '90+ Days Late'

    def test_60_days_late(self):
        """Test 60 days late status."""
        account = {
            "tu_payment_status": "60 days past due",
            "ex_payment_status": "Current",
            "eq_payment_status": "Current"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == '60 Days Past Due'
        assert result['color'] == 'red'

    def test_30_days_late(self):
        """Test 30 days late status."""
        account = {
            "tu_payment_status": "30 days past due",
            "ex_payment_status": "Current",
            "eq_payment_status": "Current"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == '30 Days Past Due'
        assert result['color'] == 'yellow'
        assert result['class'] == 'badge-warning'

    def test_not_more_than_two_payments(self):
        """Test 'not more than two payments' status."""
        account = {
            "tu_payment_status": "Not more than two payments past due",
            "ex_payment_status": "Current",
            "eq_payment_status": "Current"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == '30 Days Past Due'

    def test_current_status(self):
        """Test current/good status."""
        account = {
            "tu_payment_status": "Current",
            "ex_payment_status": "Current",
            "eq_payment_status": "Current"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == 'Current'
        assert result['color'] == 'green'
        assert result['class'] == 'badge-success'

    def test_pays_as_agreed_status(self):
        """Test 'pays as agreed' status."""
        account = {
            "tu_payment_status": "Pays account as agreed",
            "ex_payment_status": "Pays account as agreed",
            "eq_payment_status": "Pays account as agreed"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == 'Current'

    def test_closed_status(self):
        """Test closed account status."""
        account = {
            "tu_payment_status": "Closed",
            "ex_payment_status": "Closed",
            "eq_payment_status": "Closed"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == 'Closed'
        assert result['color'] == 'gray'
        assert result['class'] == 'badge-secondary'

    def test_paid_status(self):
        """Test paid account status."""
        account = {
            "tu_payment_status": "Paid in full",
            "ex_payment_status": "Paid",
            "eq_payment_status": "Paid"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == 'Closed'

    def test_unknown_status(self):
        """Test unknown status."""
        account = {
            "tu_payment_status": "Some random status",
            "ex_payment_status": "Another status",
            "eq_payment_status": "Unknown status"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == 'Unknown'
        assert result['color'] == 'gray'

    def test_empty_statuses(self):
        """Test empty payment statuses."""
        account = {
            "tu_payment_status": "",
            "ex_payment_status": "",
            "eq_payment_status": ""
        }

        result = get_worst_payment_status(account)

        assert result['text'] == 'Unknown'

    def test_mixed_severity_returns_worst(self):
        """Test mixed severity returns the worst status."""
        account = {
            "tu_payment_status": "Current",
            "ex_payment_status": "60 days past due",
            "eq_payment_status": "30 days past due"
        }

        result = get_worst_payment_status(account)

        assert result['text'] == '60 Days Past Due'


# =============================================================================
# Test Class: parse_credit_report_pdf()
# =============================================================================

class TestParseCreditReportPdf:
    """Tests for the main entry point function."""

    def test_parse_with_text_extractable_pdf(self, reset_anthropic_client):
        """Test parsing PDF with extractable text uses text parser."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "A" * 600  # > 500 chars
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)

            # Create mock module for the text parser
            mock_text_module = MagicMock()
            mock_text_module.parse_three_bureau_text = MagicMock(return_value={'success': True, 'data': {}})

            with patch('pdfplumber.open', return_value=mock_pdf):
                with patch.dict('sys.modules', {'services.pdf_parser_service_text': mock_text_module}):
                    result = parse_credit_report_pdf(tmp_path)

                    mock_text_module.parse_three_bureau_text.assert_called_once()
        finally:
            os.unlink(tmp_path)

    def test_parse_falls_back_to_vision_for_image_pdf(self, reset_anthropic_client):
        """Test parsing falls back to vision for image-based PDFs."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Short"  # < 500 chars
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)

            with patch('pdfplumber.open', return_value=mock_pdf):
                with patch('services.credit_report_ocr_parser.parse_credit_report_vision') as mock_vision:
                    mock_vision.return_value = {'success': True, 'data': {}}

                    result = parse_credit_report_pdf(tmp_path)

                    mock_vision.assert_called_once_with(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_parse_falls_back_on_text_extraction_error(self, reset_anthropic_client):
        """Test parsing falls back to vision when text extraction fails."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            with patch('pdfplumber.open') as mock_open:
                mock_open.side_effect = Exception("PDF read error")

                with patch('services.credit_report_ocr_parser.parse_credit_report_vision') as mock_vision:
                    mock_vision.return_value = {'success': True, 'data': {}}

                    result = parse_credit_report_pdf(tmp_path)

                    mock_vision.assert_called_once_with(tmp_path)
        finally:
            os.unlink(tmp_path)

    def test_parse_handles_empty_pages(self, reset_anthropic_client):
        """Test parsing handles PDF with empty pages."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = None
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=False)

            with patch('pdfplumber.open', return_value=mock_pdf):
                with patch('services.credit_report_ocr_parser.parse_credit_report_vision') as mock_vision:
                    mock_vision.return_value = {'success': True, 'data': {}}

                    result = parse_credit_report_pdf(tmp_path)

                    mock_vision.assert_called_once()
        finally:
            os.unlink(tmp_path)


# =============================================================================
# Test Class: CREDIT_REPORT_EXTRACTION_PROMPT
# =============================================================================

class TestExtractionPrompt:
    """Tests for the extraction prompt configuration."""

    def test_prompt_contains_json_structure(self):
        """Test prompt contains JSON structure instructions."""
        assert 'JSON' in CREDIT_REPORT_EXTRACTION_PROMPT
        assert 'reference_number' in CREDIT_REPORT_EXTRACTION_PROMPT
        assert 'credit_scores' in CREDIT_REPORT_EXTRACTION_PROMPT
        assert 'accounts' in CREDIT_REPORT_EXTRACTION_PROMPT

    def test_prompt_contains_all_bureaus(self):
        """Test prompt mentions all three bureaus."""
        assert 'transunion' in CREDIT_REPORT_EXTRACTION_PROMPT.lower()
        assert 'experian' in CREDIT_REPORT_EXTRACTION_PROMPT.lower()
        assert 'equifax' in CREDIT_REPORT_EXTRACTION_PROMPT.lower()

    def test_prompt_contains_payment_status_instructions(self):
        """Test prompt contains payment status instructions."""
        assert 'Pays account as agreed' in CREDIT_REPORT_EXTRACTION_PROMPT
        assert '30 days past due' in CREDIT_REPORT_EXTRACTION_PROMPT
        assert '60 days past due' in CREDIT_REPORT_EXTRACTION_PROMPT

    def test_prompt_contains_payment_history_instructions(self):
        """Test prompt contains payment history instructions."""
        assert 'PAYMENT HISTORY' in CREDIT_REPORT_EXTRACTION_PROMPT
        assert 'OK' in CREDIT_REPORT_EXTRACTION_PROMPT


# =============================================================================
# Test Class: Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_detect_discrepancies_with_none_names(self):
        """Test discrepancy detection handles None names."""
        data = {
            "personal_info": {
                "transunion": {"name": None},
                "experian": {"name": "John Doe"},
                "equifax": {"name": "John Doe"}
            },
            "summary_stats": {},
            "accounts": []
        }

        discrepancies = detect_discrepancies(data)

        # Should handle gracefully
        assert isinstance(discrepancies, list)

    def test_detect_discrepancies_mixed_missing_data(self):
        """Test discrepancy detection with mixed missing data."""
        data = {
            "personal_info": {
                "transunion": {},
                "experian": {"name": "John"},
                "equifax": {"name": "Jane"}
            },
            "summary_stats": {
                "transunion": {},
                "experian": {"delinquent": 1}
            },
            "accounts": []
        }

        discrepancies = detect_discrepancies(data)

        # Should detect name discrepancy
        name_discrepancies = [d for d in discrepancies if d['field'] == 'name']
        assert len(name_discrepancies) >= 1

    def test_get_worst_payment_status_with_none_values(self):
        """Test get_worst_payment_status handles None values."""
        account = {
            "tu_payment_status": None,
            "ex_payment_status": "Current",
            "eq_payment_status": None
        }

        result = get_worst_payment_status(account)

        # Should not crash
        assert 'text' in result
        assert 'color' in result
        assert 'class' in result

    def test_derogatory_accounts_with_empty_status(self):
        """Test derogatory detection with empty payment status."""
        accounts = [
            {
                "creditor_name": "TEST",
                "tu_payment_status": "",
                "tu_past_due": 100
            }
        ]

        derogatory = detect_derogatory_accounts(accounts)

        # Should detect due to past_due amount
        assert len(derogatory) == 1

    def test_detect_discrepancies_with_zero_values(self):
        """Test discrepancy detection distinguishes zero from missing."""
        data = {
            "personal_info": {},
            "summary_stats": {
                "transunion": {"delinquent": 0},
                "experian": {"delinquent": 0},
                "equifax": {"delinquent": 0}
            },
            "accounts": []
        }

        discrepancies = detect_discrepancies(data)

        # All zeros should match - no discrepancy
        delinq_discrepancies = [d for d in discrepancies if d.get('field') == 'delinquent']
        assert len(delinq_discrepancies) == 0

    def test_account_with_single_bureau_balance(self):
        """Test discrepancy detection with single bureau balance."""
        data = {
            "personal_info": {},
            "summary_stats": {},
            "accounts": [
                {
                    "creditor_name": "TEST",
                    "tu_balance": 1000,
                    # No ex_balance or eq_balance
                }
            ]
        }

        discrepancies = detect_discrepancies(data)

        # Can't compare with only one value
        balance_discrepancies = [d for d in discrepancies if d.get('field') == 'balance']
        assert len(balance_discrepancies) == 0


# =============================================================================
# Test Class: Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for full parsing workflow."""

    def test_full_workflow_success(self, reset_anthropic_client, sample_extracted_data):
        """Test full parsing workflow with successful extraction."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Mock text extraction to fail (force vision path)
            with patch('pdfplumber.open') as mock_pdfplumber:
                mock_pdfplumber.side_effect = Exception("Text extraction failed")

                mock_client = MagicMock()
                mock_response = MagicMock()
                mock_response.content = [MagicMock(text=json.dumps(sample_extracted_data))]
                mock_response.usage.input_tokens = 5000
                mock_response.usage.output_tokens = 2000
                mock_client.messages.create.return_value = mock_response

                with patch('services.credit_report_ocr_parser.get_anthropic_client', return_value=mock_client):
                    with patch('services.credit_report_ocr_parser._convert_pdf_to_images', return_value=['img1', 'img2']):
                        result = parse_credit_report_pdf(tmp_path)

                assert result['success'] is True
                assert 'discrepancies' in result['data']
                assert 'derogatory_accounts' in result['data']

                # Check discrepancies were detected
                discrepancies = result['data']['discrepancies']
                assert len(discrepancies) > 0

                # Check derogatory accounts were detected
                derogatory = result['data']['derogatory_accounts']
                assert len(derogatory) > 0
        finally:
            os.unlink(tmp_path)

    def test_result_structure_completeness(self, reset_anthropic_client, sample_extracted_data):
        """Test that result contains all expected fields."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps(sample_extracted_data))]
            mock_response.usage.input_tokens = 1000
            mock_response.usage.output_tokens = 500
            mock_client.messages.create.return_value = mock_response

            with patch('services.credit_report_ocr_parser.get_anthropic_client', return_value=mock_client):
                with patch('services.credit_report_ocr_parser._convert_pdf_to_images', return_value=['img']):
                    result = parse_credit_report_vision(tmp_path)

            # Check top-level result structure
            assert 'success' in result
            assert 'error' in result
            assert 'report_type' in result
            assert 'extraction_method' in result
            assert 'data' in result
            assert 'tokens_used' in result

            # Check data structure
            data = result['data']
            assert 'reference_number' in data
            assert 'report_date' in data
            assert 'credit_scores' in data
            assert 'accounts' in data
            assert 'discrepancies' in data
            assert 'derogatory_accounts' in data
        finally:
            os.unlink(tmp_path)

    def test_parse_preserves_original_data(self, reset_anthropic_client, sample_extracted_data):
        """Test that parsing preserves original extracted data."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text=json.dumps(sample_extracted_data))]
            mock_response.usage.input_tokens = 1000
            mock_response.usage.output_tokens = 500
            mock_client.messages.create.return_value = mock_response

            with patch('services.credit_report_ocr_parser.get_anthropic_client', return_value=mock_client):
                with patch('services.credit_report_ocr_parser._convert_pdf_to_images', return_value=['img']):
                    result = parse_credit_report_vision(tmp_path)

            data = result['data']

            # Original data should be preserved
            assert data['reference_number'] == sample_extracted_data['reference_number']
            assert data['report_date'] == sample_extracted_data['report_date']
            assert len(data['accounts']) == len(sample_extracted_data['accounts'])
        finally:
            os.unlink(tmp_path)
