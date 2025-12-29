"""
Unit Tests for Affiliate Service.
Tests for affiliate management, referral processing, commission calculation,
payout processing, and two-level commission system.
Covers all main functions with mocked database interactions.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.affiliate_service import (
    generate_affiliate_code,
    validate_affiliate_code,
    process_referral,
    calculate_commission,
    get_affiliate_stats,
    process_payout,
    get_commission_history,
    get_referral_tree,
    create_affiliate,
    update_affiliate,
    get_all_affiliates,
    get_affiliate_by_id,
    apply_for_affiliate,
    get_dashboard_stats,
)


# ============== Fixtures ==============


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock()
    db.query.return_value = db
    db.filter.return_value = db
    db.filter_by.return_value = db
    db.first.return_value = None
    db.all.return_value = []
    db.count.return_value = 0
    db.order_by.return_value = db
    db.limit.return_value = db
    db.desc.return_value = db
    return db


@pytest.fixture
def mock_affiliate():
    """Create a mock Affiliate."""
    affiliate = Mock()
    affiliate.id = 1
    affiliate.user_id = 100
    affiliate.name = "Test Affiliate"
    affiliate.email = "affiliate@test.com"
    affiliate.phone = "555-1234"
    affiliate.company_name = "Test Company"
    affiliate.affiliate_code = "TES12345"
    affiliate.parent_affiliate_id = None
    affiliate.commission_rate_1 = 0.10
    affiliate.commission_rate_2 = 0.05
    affiliate.status = "active"
    affiliate.payout_method = "paypal"
    affiliate.payout_details = {"email": "affiliate@test.com"}
    affiliate.total_referrals = 5
    affiliate.total_earnings = 500.0
    affiliate.pending_earnings = 100.0
    affiliate.paid_out = 400.0
    affiliate.created_at = datetime(2024, 1, 1)
    affiliate.updated_at = datetime(2024, 1, 15)
    return affiliate


@pytest.fixture
def mock_client():
    """Create a mock Client."""
    client = Mock()
    client.id = 1
    client.first_name = "Test"
    client.last_name = "Client"
    client.email = "client@test.com"
    client.referred_by_affiliate_id = None
    client.payment_status = "pending"
    return client


@pytest.fixture
def mock_commission():
    """Create a mock Commission."""
    commission = Mock()
    commission.id = 1
    commission.affiliate_id = 1
    commission.client_id = 1
    commission.level = 1
    commission.trigger_type = "signup"
    commission.trigger_amount = 299.00
    commission.commission_rate = 0.10
    commission.commission_amount = 29.90
    commission.status = "pending"
    commission.paid_at = None
    commission.payout_id = None
    commission.notes = "Test commission"
    commission.created_at = datetime(2024, 1, 1)
    return commission


# ============== generate_affiliate_code Tests ==============


class TestGenerateAffiliateCode:
    """Tests for generate_affiliate_code function."""

    @patch('services.affiliate_service.get_db')
    def test_generate_code_with_name(self, mock_get_db):
        """Test code generation with a name."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        code = generate_affiliate_code("John")

        assert code.startswith("JOH")
        assert len(code) == 8
        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_generate_code_with_short_name(self, mock_get_db):
        """Test code generation with short name pads with X."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        code = generate_affiliate_code("Jo")

        assert code.startswith("JO")
        assert len(code) == 8
        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_generate_code_with_single_char_name(self, mock_get_db):
        """Test code generation with single char name pads with XX."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        code = generate_affiliate_code("A")

        assert code.startswith("A")
        assert len(code) == 8
        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_generate_code_without_name(self, mock_get_db):
        """Test code generation without name uses random letters."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        code = generate_affiliate_code()

        assert len(code) == 8
        assert code[:3].isalpha()
        assert code[3:].isdigit()
        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_generate_code_with_none_name(self, mock_get_db):
        """Test code generation with None name uses random letters."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        code = generate_affiliate_code(None)

        assert len(code) == 8
        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_generate_code_regenerates_on_collision(self, mock_get_db):
        """Test code generation retries on collision."""
        mock_session = Mock()
        existing_affiliate = Mock()
        # First call returns existing, second returns None
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            existing_affiliate,
            None
        ]
        mock_get_db.return_value = mock_session

        code = generate_affiliate_code("Test")

        assert len(code) == 8
        assert mock_session.close.call_count == 2

    @patch('services.affiliate_service.get_db')
    def test_generate_code_strips_non_alpha(self, mock_get_db):
        """Test code generation strips non-alphabetic characters from first 3 chars."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        # "J0h" (first 3 chars) -> filter alpha -> "JH" -> pad -> "JHX"
        code = generate_affiliate_code("J0hn123")

        assert code.startswith("JHX")
        assert len(code) == 8


# ============== validate_affiliate_code Tests ==============


class TestValidateAffiliateCode:
    """Tests for validate_affiliate_code function."""

    @patch('services.affiliate_service.get_db')
    def test_validate_empty_code(self, mock_get_db):
        """Test validation with empty code."""
        result = validate_affiliate_code("")

        assert result["valid"] is False
        assert result["message"] == "No code provided"
        mock_get_db.assert_not_called()

    @patch('services.affiliate_service.get_db')
    def test_validate_none_code(self, mock_get_db):
        """Test validation with None code."""
        result = validate_affiliate_code(None)

        assert result["valid"] is False
        assert result["message"] == "No code provided"

    @patch('services.affiliate_service.get_db')
    def test_validate_invalid_code(self, mock_get_db):
        """Test validation with non-existent code."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = validate_affiliate_code("INVALID123")

        assert result["valid"] is False
        assert result["message"] == "Invalid affiliate code"
        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_validate_inactive_affiliate(self, mock_get_db, mock_affiliate):
        """Test validation with inactive affiliate."""
        mock_affiliate.status = "inactive"
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = validate_affiliate_code("TES12345")

        assert result["valid"] is False
        assert result["message"] == "Affiliate is not currently active"

    @patch('services.affiliate_service.get_db')
    def test_validate_pending_affiliate(self, mock_get_db, mock_affiliate):
        """Test validation with pending affiliate."""
        mock_affiliate.status = "pending"
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = validate_affiliate_code("TES12345")

        assert result["valid"] is False
        assert result["message"] == "Affiliate is not currently active"

    @patch('services.affiliate_service.get_db')
    def test_validate_active_affiliate(self, mock_get_db, mock_affiliate):
        """Test validation with active affiliate."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = validate_affiliate_code("TES12345")

        assert result["valid"] is True
        assert result["affiliate_id"] == 1
        assert result["affiliate_name"] == "Test Affiliate"
        assert result["message"] == "Valid affiliate code"

    @patch('services.affiliate_service.get_db')
    def test_validate_code_case_insensitive(self, mock_get_db, mock_affiliate):
        """Test validation is case insensitive."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = validate_affiliate_code("  tes12345  ")

        assert result["valid"] is True


# ============== process_referral Tests ==============


class TestProcessReferral:
    """Tests for process_referral function."""

    @patch('services.affiliate_service.get_db')
    def test_process_referral_no_code(self, mock_get_db):
        """Test referral processing with no code."""
        result = process_referral(1, "")

        assert result["success"] is False
        assert result["message"] == "No affiliate code provided"

    @patch('services.affiliate_service.get_db')
    def test_process_referral_none_code(self, mock_get_db):
        """Test referral processing with None code."""
        result = process_referral(1, None)

        assert result["success"] is False
        assert result["message"] == "No affiliate code provided"

    @patch('services.affiliate_service.get_db')
    def test_process_referral_invalid_affiliate(self, mock_get_db):
        """Test referral with invalid affiliate code."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = process_referral(1, "INVALID123")

        assert result["success"] is False
        assert result["message"] == "Invalid or inactive affiliate code"

    @patch('services.affiliate_service.get_db')
    def test_process_referral_client_not_found(self, mock_get_db, mock_affiliate):
        """Test referral when client not found."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate,  # affiliate lookup
            None,  # client lookup
        ]
        mock_get_db.return_value = mock_session

        result = process_referral(999, "TES12345")

        assert result["success"] is False
        assert result["message"] == "Client not found"

    @patch('services.affiliate_service.get_db')
    def test_process_referral_client_already_referred(self, mock_get_db, mock_affiliate, mock_client):
        """Test referral when client already has a referral."""
        mock_client.referred_by_affiliate_id = 2  # Already referred
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate,
            mock_client,
        ]
        mock_get_db.return_value = mock_session

        result = process_referral(1, "TES12345")

        assert result["success"] is False
        assert result["message"] == "Client already has an affiliate referral"

    @patch('services.affiliate_service.get_db')
    def test_process_referral_success(self, mock_get_db, mock_affiliate, mock_client):
        """Test successful referral processing."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate,
            mock_client,
        ]
        mock_get_db.return_value = mock_session

        result = process_referral(1, "TES12345")

        assert result["success"] is True
        assert result["affiliate_id"] == 1
        assert result["affiliate_name"] == "Test Affiliate"
        assert mock_client.referred_by_affiliate_id == 1
        assert mock_affiliate.total_referrals == 6  # Was 5
        mock_session.commit.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_process_referral_increments_null_referrals(self, mock_get_db, mock_affiliate, mock_client):
        """Test referral increments from None total_referrals."""
        mock_affiliate.total_referrals = None
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate,
            mock_client,
        ]
        mock_get_db.return_value = mock_session

        result = process_referral(1, "TES12345")

        assert result["success"] is True
        assert mock_affiliate.total_referrals == 1

    @patch('services.affiliate_service.get_db')
    def test_process_referral_exception_rollback(self, mock_get_db, mock_affiliate, mock_client):
        """Test referral rollback on exception."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate,
            mock_client,
        ]
        mock_session.commit.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_session

        result = process_referral(1, "TES12345")

        assert result["success"] is False
        assert "Error processing referral" in result["message"]
        mock_session.rollback.assert_called_once()


# ============== calculate_commission Tests ==============


class TestCalculateCommission:
    """Tests for calculate_commission function."""

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_invalid_amount_zero(self, mock_get_db):
        """Test commission calculation with zero amount."""
        result = calculate_commission(1, "signup", 0)

        assert result["success"] is False
        assert result["message"] == "Invalid amount"

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_invalid_amount_negative(self, mock_get_db):
        """Test commission calculation with negative amount."""
        result = calculate_commission(1, "signup", -100)

        assert result["success"] is False
        assert result["message"] == "Invalid amount"

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_invalid_amount_none(self, mock_get_db):
        """Test commission calculation with None amount."""
        result = calculate_commission(1, "signup", None)

        assert result["success"] is False
        assert result["message"] == "Invalid amount"

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_client_not_found(self, mock_get_db):
        """Test commission calculation when client not found."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = calculate_commission(999, "signup", 299.00)

        assert result["success"] is False
        assert result["message"] == "Client not found"

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_no_referral(self, mock_get_db, mock_client):
        """Test commission calculation when client has no referral."""
        mock_client.referred_by_affiliate_id = None
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client
        mock_get_db.return_value = mock_session

        result = calculate_commission(1, "signup", 299.00)

        assert result["success"] is False
        assert result["message"] == "Client has no affiliate referral"

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_affiliate_not_found(self, mock_get_db, mock_client):
        """Test commission calculation when affiliate not found."""
        mock_client.referred_by_affiliate_id = 1
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            None,  # affiliate not found
        ]
        mock_get_db.return_value = mock_session

        result = calculate_commission(1, "signup", 299.00)

        assert result["success"] is False
        assert result["message"] == "Referring affiliate not found"

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_affiliate_inactive(self, mock_get_db, mock_client, mock_affiliate):
        """Test commission calculation when affiliate is inactive."""
        mock_client.referred_by_affiliate_id = 1
        mock_affiliate.status = "inactive"
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            mock_affiliate,
        ]
        mock_get_db.return_value = mock_session

        result = calculate_commission(1, "signup", 299.00)

        assert result["success"] is False
        assert result["message"] == "Referring affiliate is not active"

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_level_1_only(self, mock_get_db, mock_client, mock_affiliate):
        """Test commission calculation for level 1 only (no parent)."""
        mock_client.referred_by_affiliate_id = 1
        mock_affiliate.parent_affiliate_id = None
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            mock_affiliate,
        ]
        mock_get_db.return_value = mock_session

        result = calculate_commission(1, "signup", 100.00)

        assert result["success"] is True
        assert len(result["commissions"]) == 1
        assert result["commissions"][0]["level"] == 1
        assert result["commissions"][0]["rate"] == 0.10
        assert result["commissions"][0]["amount"] == 10.00
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_level_1_and_2(self, mock_get_db, mock_client, mock_affiliate):
        """Test commission calculation for both levels."""
        mock_client.referred_by_affiliate_id = 1
        mock_affiliate.parent_affiliate_id = 2

        parent_affiliate = Mock()
        parent_affiliate.id = 2
        parent_affiliate.name = "Parent Affiliate"
        parent_affiliate.commission_rate_2 = 0.05
        parent_affiliate.status = "active"
        parent_affiliate.total_earnings = 200.0
        parent_affiliate.pending_earnings = 50.0

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            mock_affiliate,
            parent_affiliate,  # Parent lookup
        ]
        mock_get_db.return_value = mock_session

        result = calculate_commission(1, "signup", 100.00)

        assert result["success"] is True
        assert len(result["commissions"]) == 2
        # Level 1
        assert result["commissions"][0]["level"] == 1
        assert result["commissions"][0]["amount"] == 10.00
        # Level 2
        assert result["commissions"][1]["level"] == 2
        assert result["commissions"][1]["amount"] == 5.00
        assert mock_session.add.call_count == 2

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_parent_inactive(self, mock_get_db, mock_client, mock_affiliate):
        """Test commission calculation when parent is inactive."""
        mock_client.referred_by_affiliate_id = 1
        mock_affiliate.parent_affiliate_id = 2

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            mock_affiliate,
            None,  # Parent not found (inactive filter)
        ]
        mock_get_db.return_value = mock_session

        result = calculate_commission(1, "signup", 100.00)

        assert result["success"] is True
        assert len(result["commissions"]) == 1  # Only level 1

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_uses_default_rates(self, mock_get_db, mock_client, mock_affiliate):
        """Test commission uses default rates when None."""
        mock_client.referred_by_affiliate_id = 1
        mock_affiliate.commission_rate_1 = None
        mock_affiliate.parent_affiliate_id = None
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            mock_affiliate,
        ]
        mock_get_db.return_value = mock_session

        result = calculate_commission(1, "signup", 100.00)

        assert result["success"] is True
        assert result["commissions"][0]["rate"] == 0.10  # Default

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_updates_earnings(self, mock_get_db, mock_client, mock_affiliate):
        """Test commission updates affiliate earnings."""
        mock_client.referred_by_affiliate_id = 1
        mock_affiliate.parent_affiliate_id = None
        mock_affiliate.total_earnings = 100.0
        mock_affiliate.pending_earnings = 50.0
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            mock_affiliate,
        ]
        mock_get_db.return_value = mock_session

        result = calculate_commission(1, "signup", 100.00)

        assert result["success"] is True
        assert mock_affiliate.total_earnings == 110.0  # +10
        assert mock_affiliate.pending_earnings == 60.0  # +10

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_exception_rollback(self, mock_get_db, mock_client, mock_affiliate):
        """Test commission rollback on exception."""
        mock_client.referred_by_affiliate_id = 1
        mock_affiliate.parent_affiliate_id = None
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            mock_affiliate,
        ]
        mock_session.commit.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_session

        result = calculate_commission(1, "signup", 100.00)

        assert result["success"] is False
        assert "Error calculating commission" in result["message"]
        mock_session.rollback.assert_called_once()


# ============== get_affiliate_stats Tests ==============


class TestGetAffiliateStats:
    """Tests for get_affiliate_stats function."""

    @patch('services.affiliate_service.get_db')
    def test_get_stats_affiliate_not_found(self, mock_get_db):
        """Test getting stats when affiliate not found."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = get_affiliate_stats(999)

        assert result["success"] is False
        assert result["message"] == "Affiliate not found"

    @patch('services.affiliate_service.get_db')
    def test_get_stats_success(self, mock_get_db, mock_affiliate):
        """Test successful stats retrieval."""
        mock_client = Mock()
        mock_client.payment_status = "paid"

        mock_commission_1 = Mock()
        mock_commission_1.commission_amount = 10.0

        mock_commission_2 = Mock()
        mock_commission_2.commission_amount = 5.0

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_client],  # referred_clients
            [mock_commission_1],  # level_1_commissions
            [mock_commission_2],  # level_2_commissions
            [mock_commission_1],  # pending_commissions
            [],  # paid_commissions
            [],  # sub_affiliates
        ]
        mock_get_db.return_value = mock_session

        result = get_affiliate_stats(1)

        assert result["success"] is True
        assert result["affiliate_id"] == 1
        assert result["affiliate_name"] == "Test Affiliate"
        assert result["status"] == "active"
        assert result["total_referrals"] == 5
        assert result["converted_referrals"] == 1
        assert result["conversion_rate"] == 100.0
        assert result["level_1_count"] == 1
        assert result["level_1_earnings"] == 10.0
        assert result["level_2_count"] == 1
        assert result["level_2_earnings"] == 5.0

    @patch('services.affiliate_service.get_db')
    def test_get_stats_zero_referrals(self, mock_get_db, mock_affiliate):
        """Test stats with zero referrals (no division by zero)."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        result = get_affiliate_stats(1)

        assert result["success"] is True
        assert result["conversion_rate"] == 0

    @patch('services.affiliate_service.get_db')
    def test_get_stats_null_earnings(self, mock_get_db, mock_affiliate):
        """Test stats handles null earnings."""
        mock_affiliate.total_earnings = None
        mock_affiliate.pending_earnings = None
        mock_affiliate.paid_out = None
        mock_affiliate.total_referrals = None

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        result = get_affiliate_stats(1)

        assert result["success"] is True
        assert result["total_referrals"] == 0
        assert result["total_earnings"] == 0
        assert result["pending_earnings"] == 0
        assert result["paid_out"] == 0


# ============== process_payout Tests ==============


class TestProcessPayout:
    """Tests for process_payout function."""

    @patch('services.affiliate_service.get_db')
    def test_process_payout_invalid_amount_zero(self, mock_get_db):
        """Test payout with zero amount."""
        result = process_payout(1, 0)

        assert result["success"] is False
        assert result["message"] == "Invalid payout amount"

    @patch('services.affiliate_service.get_db')
    def test_process_payout_invalid_amount_negative(self, mock_get_db):
        """Test payout with negative amount."""
        result = process_payout(1, -100)

        assert result["success"] is False
        assert result["message"] == "Invalid payout amount"

    @patch('services.affiliate_service.get_db')
    def test_process_payout_invalid_amount_none(self, mock_get_db):
        """Test payout with None amount."""
        result = process_payout(1, None)

        assert result["success"] is False
        assert result["message"] == "Invalid payout amount"

    @patch('services.affiliate_service.get_db')
    def test_process_payout_affiliate_not_found(self, mock_get_db):
        """Test payout when affiliate not found."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = process_payout(999, 100)

        assert result["success"] is False
        assert result["message"] == "Affiliate not found"

    @patch('services.affiliate_service.get_db')
    def test_process_payout_insufficient_earnings(self, mock_get_db, mock_affiliate):
        """Test payout with insufficient pending earnings."""
        mock_affiliate.pending_earnings = 50.0
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = process_payout(1, 100)

        assert result["success"] is False
        assert "Insufficient pending earnings" in result["message"]

    @patch('services.affiliate_service.get_db')
    def test_process_payout_success(self, mock_get_db, mock_affiliate, mock_commission):
        """Test successful payout processing."""
        mock_affiliate.pending_earnings = 100.0
        mock_affiliate.paid_out = 0.0
        mock_commission.commission_amount = 30.0
        mock_commission.status = "pending"
        mock_commission.notes = "Original note"

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_commission]
        mock_get_db.return_value = mock_session

        result = process_payout(1, 50, payout_method="paypal", notes="Payout note")

        assert result["success"] is True
        assert "Payout of $50.00" in result["message"]
        assert result["commissions_paid"] == 1
        assert mock_affiliate.pending_earnings == 50.0  # 100 - 50
        assert mock_affiliate.paid_out == 50.0  # 0 + 50
        mock_session.commit.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_process_payout_marks_commissions_paid(self, mock_get_db, mock_affiliate):
        """Test payout marks commissions as paid."""
        mock_affiliate.pending_earnings = 100.0
        mock_affiliate.paid_out = 0.0

        commission1 = Mock()
        commission1.commission_amount = 30.0
        commission1.status = "pending"
        commission1.notes = None

        commission2 = Mock()
        commission2.commission_amount = 20.0
        commission2.status = "pending"
        commission2.notes = "Existing note"

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [commission1, commission2]
        mock_get_db.return_value = mock_session

        result = process_payout(1, 50, notes="Test payout")

        assert result["success"] is True
        assert result["commissions_paid"] == 2
        assert commission1.status == "paid"
        assert commission2.status == "paid"
        assert commission1.paid_at is not None
        assert commission2.paid_at is not None

    @patch('services.affiliate_service.get_db')
    def test_process_payout_partial_commissions(self, mock_get_db, mock_affiliate):
        """Test payout only pays commissions up to amount."""
        mock_affiliate.pending_earnings = 100.0
        mock_affiliate.paid_out = 0.0

        commission1 = Mock()
        commission1.commission_amount = 30.0
        commission1.status = "pending"
        commission1.notes = None

        commission2 = Mock()
        commission2.commission_amount = 50.0
        commission2.status = "pending"
        commission2.notes = None

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [commission1, commission2]
        mock_get_db.return_value = mock_session

        result = process_payout(1, 30)

        assert result["success"] is True
        assert result["commissions_paid"] == 1  # Only first one fits
        assert commission1.status == "paid"
        assert commission2.status == "pending"

    @patch('services.affiliate_service.get_db')
    def test_process_payout_exception_rollback(self, mock_get_db, mock_affiliate):
        """Test payout rollback on exception."""
        mock_affiliate.pending_earnings = 100.0
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_session.commit.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_session

        result = process_payout(1, 50)

        assert result["success"] is False
        assert "Error processing payout" in result["message"]
        mock_session.rollback.assert_called_once()


# ============== get_commission_history Tests ==============


class TestGetCommissionHistory:
    """Tests for get_commission_history function."""

    @patch('services.affiliate_service.get_db')
    def test_get_history_empty(self, mock_get_db):
        """Test getting empty commission history."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        result = get_commission_history(1)

        assert result == []

    @patch('services.affiliate_service.get_db')
    def test_get_history_with_commissions(self, mock_get_db, mock_commission, mock_client):
        """Test getting commission history with records."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_commission]
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client
        mock_get_db.return_value = mock_session

        result = get_commission_history(1)

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["client_name"] == "Test Client"
        assert result[0]["level"] == 1
        assert result[0]["commission_amount"] == 29.90

    @patch('services.affiliate_service.get_db')
    def test_get_history_client_not_found(self, mock_get_db, mock_commission):
        """Test getting history when client is not found."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_commission]
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = get_commission_history(1)

        assert len(result) == 1
        assert result[0]["client_name"] == "Unknown"

    @patch('services.affiliate_service.get_db')
    def test_get_history_custom_limit(self, mock_get_db):
        """Test getting history with custom limit."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        get_commission_history(1, limit=10)

        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_with(10)

    @patch('services.affiliate_service.get_db')
    def test_get_history_paid_commission(self, mock_get_db, mock_commission, mock_client):
        """Test getting history with paid commission."""
        mock_commission.status = "paid"
        mock_commission.paid_at = datetime(2024, 2, 1)
        mock_commission.payout_id = 12345

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_commission]
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client
        mock_get_db.return_value = mock_session

        result = get_commission_history(1)

        assert result[0]["status"] == "paid"
        assert result[0]["paid_at"] is not None
        assert result[0]["payout_id"] == 12345


# ============== get_referral_tree Tests ==============


class TestGetReferralTree:
    """Tests for get_referral_tree function."""

    @patch('services.affiliate_service.get_db')
    def test_get_tree_affiliate_not_found(self, mock_get_db):
        """Test getting tree when affiliate not found."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = get_referral_tree(999)

        assert result["success"] is False
        assert result["message"] == "Affiliate not found"

    @patch('services.affiliate_service.get_db')
    def test_get_tree_no_children(self, mock_get_db, mock_affiliate):
        """Test getting tree with no sub-affiliates."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        result = get_referral_tree(1)

        assert result["success"] is True
        assert result["tree"]["affiliate_id"] == 1
        assert result["tree"]["name"] == "Test Affiliate"
        assert result["tree"]["children"] == []

    @patch('services.affiliate_service.get_db')
    def test_get_tree_with_children(self, mock_get_db, mock_affiliate):
        """Test getting tree with sub-affiliates."""
        sub_affiliate = Mock()
        sub_affiliate.id = 2
        sub_affiliate.name = "Sub Affiliate"
        sub_affiliate.affiliate_code = "SUB12345"
        sub_affiliate.total_referrals = 2
        sub_affiliate.total_earnings = 100.0
        sub_affiliate.status = "active"
        sub_affiliate.created_at = datetime(2024, 2, 1)

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.all.return_value = [sub_affiliate]
        mock_get_db.return_value = mock_session

        result = get_referral_tree(1)

        assert result["success"] is True
        assert len(result["tree"]["children"]) == 1
        assert result["tree"]["children"][0]["name"] == "Sub Affiliate"
        assert result["tree"]["children"][0]["status"] == "active"


# ============== create_affiliate Tests ==============


class TestCreateAffiliate:
    """Tests for create_affiliate function."""

    @patch('services.affiliate_service.get_db')
    @patch('services.affiliate_service.generate_affiliate_code')
    def test_create_affiliate_email_exists(self, mock_gen_code, mock_get_db):
        """Test creating affiliate when email exists."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = Mock()  # Existing
        mock_get_db.return_value = mock_session

        result = create_affiliate("Test", "existing@test.com")

        assert result["success"] is False
        assert "email already exists" in result["message"]

    @patch('services.affiliate_service.get_db')
    @patch('services.affiliate_service.generate_affiliate_code')
    def test_create_affiliate_invalid_parent(self, mock_gen_code, mock_get_db):
        """Test creating affiliate with invalid parent."""
        mock_gen_code.return_value = "TES12345"
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            None,  # No existing email
            None,  # Parent not found
        ]
        mock_get_db.return_value = mock_session

        result = create_affiliate("Test", "test@test.com", parent_affiliate_id=999)

        assert result["success"] is False
        assert result["message"] == "Parent affiliate not found"

    @patch('services.affiliate_service.get_db')
    @patch('services.affiliate_service.generate_affiliate_code')
    def test_create_affiliate_success(self, mock_gen_code, mock_get_db):
        """Test successful affiliate creation."""
        mock_gen_code.return_value = "TES12345"
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        # Mock the added affiliate to get ID after commit
        def set_id(affiliate):
            affiliate.id = 1
        mock_session.add.side_effect = set_id

        result = create_affiliate(
            name="Test Affiliate",
            email="test@test.com",
            phone="555-1234",
            company_name="Test Co",
            payout_method="paypal"
        )

        assert result["success"] is True
        assert result["affiliate_code"] == "TES12345"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('services.affiliate_service.get_db')
    @patch('services.affiliate_service.generate_affiliate_code')
    def test_create_affiliate_with_parent(self, mock_gen_code, mock_get_db):
        """Test creating affiliate with parent."""
        mock_gen_code.return_value = "TES12345"
        parent = Mock()
        parent.id = 1
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            None,  # No existing email
            parent,  # Parent found
        ]
        mock_get_db.return_value = mock_session

        result = create_affiliate(
            name="Sub Affiliate",
            email="sub@test.com",
            parent_affiliate_id=1
        )

        assert result["success"] is True
        mock_session.commit.assert_called_once()

    @patch('services.affiliate_service.get_db')
    @patch('services.affiliate_service.generate_affiliate_code')
    def test_create_affiliate_exception(self, mock_gen_code, mock_get_db):
        """Test affiliate creation exception handling."""
        mock_gen_code.return_value = "TES12345"
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.commit.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_session

        result = create_affiliate("Test", "test@test.com")

        assert result["success"] is False
        assert "Error creating affiliate" in result["message"]
        mock_session.rollback.assert_called_once()

    @patch('services.affiliate_service.get_db')
    @patch('services.affiliate_service.generate_affiliate_code')
    def test_create_affiliate_normalizes_email(self, mock_gen_code, mock_get_db):
        """Test affiliate creation normalizes email."""
        mock_gen_code.return_value = "TES12345"
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = create_affiliate("Test", "  TEST@Test.com  ")

        assert result["success"] is True
        # Verify the email was lowercased and stripped in the filter call
        mock_session.query.return_value.filter.assert_called()


# ============== update_affiliate Tests ==============


class TestUpdateAffiliate:
    """Tests for update_affiliate function."""

    @patch('services.affiliate_service.get_db')
    def test_update_affiliate_not_found(self, mock_get_db):
        """Test updating non-existent affiliate."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = update_affiliate(999, name="New Name")

        assert result["success"] is False
        assert result["message"] == "Affiliate not found"

    @patch('services.affiliate_service.get_db')
    def test_update_affiliate_success(self, mock_get_db, mock_affiliate):
        """Test successful affiliate update."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = update_affiliate(1, name="Updated Name", phone="555-9999")

        assert result["success"] is True
        assert mock_affiliate.name == "Updated Name"
        assert mock_affiliate.phone == "555-9999"
        mock_session.commit.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_update_affiliate_ignores_unknown_fields(self, mock_get_db, mock_affiliate):
        """Test update ignores unknown fields."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = update_affiliate(1, unknown_field="value", name="Valid")

        assert result["success"] is True
        assert mock_affiliate.name == "Valid"
        assert not hasattr(mock_affiliate, "unknown_field") or mock_affiliate.unknown_field != "value"

    @patch('services.affiliate_service.get_db')
    def test_update_affiliate_ignores_none_values(self, mock_get_db, mock_affiliate):
        """Test update ignores None values."""
        original_name = mock_affiliate.name
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = update_affiliate(1, name=None, phone="555-9999")

        assert result["success"] is True
        assert mock_affiliate.name == original_name  # Unchanged
        assert mock_affiliate.phone == "555-9999"  # Changed

    @patch('services.affiliate_service.get_db')
    def test_update_affiliate_exception(self, mock_get_db, mock_affiliate):
        """Test affiliate update exception handling."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.commit.side_effect = Exception("DB error")
        mock_get_db.return_value = mock_session

        result = update_affiliate(1, name="New Name")

        assert result["success"] is False
        assert "Error updating affiliate" in result["message"]
        mock_session.rollback.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_update_affiliate_sets_updated_at(self, mock_get_db, mock_affiliate):
        """Test update sets updated_at timestamp."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = update_affiliate(1, name="New Name")

        assert result["success"] is True
        assert mock_affiliate.updated_at is not None


# ============== get_all_affiliates Tests ==============


class TestGetAllAffiliates:
    """Tests for get_all_affiliates function."""

    @patch('services.affiliate_service.get_db')
    def test_get_all_empty(self, mock_get_db):
        """Test getting all affiliates when none exist."""
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        result = get_all_affiliates()

        assert result == []

    @patch('services.affiliate_service.get_db')
    def test_get_all_with_affiliates(self, mock_get_db, mock_affiliate):
        """Test getting all affiliates."""
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_affiliate]
        mock_session.query.return_value.filter.return_value.count.return_value = 3
        mock_get_db.return_value = mock_session

        result = get_all_affiliates()

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["name"] == "Test Affiliate"
        assert result[0]["actual_referrals"] == 3

    @patch('services.affiliate_service.get_db')
    def test_get_all_with_status_filter(self, mock_get_db, mock_affiliate):
        """Test getting affiliates with status filter."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_affiliate]
        mock_session.query.return_value.filter.return_value.count.return_value = 3
        mock_get_db.return_value = mock_session

        result = get_all_affiliates(status="active")

        assert len(result) == 1
        mock_session.query.return_value.filter.assert_called()

    @patch('services.affiliate_service.get_db')
    def test_get_all_custom_limit(self, mock_get_db):
        """Test getting affiliates with custom limit."""
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        get_all_affiliates(limit=10)

        mock_session.query.return_value.order_by.return_value.limit.assert_called_with(10)


# ============== get_affiliate_by_id Tests ==============


class TestGetAffiliateById:
    """Tests for get_affiliate_by_id function."""

    @patch('services.affiliate_service.get_db')
    def test_get_by_id_not_found(self, mock_get_db):
        """Test getting affiliate that doesn't exist."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        result = get_affiliate_by_id(999)

        assert result is None

    @patch('services.affiliate_service.get_db')
    def test_get_by_id_success(self, mock_get_db, mock_affiliate):
        """Test getting affiliate by ID."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        result = get_affiliate_by_id(1)

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "Test Affiliate"
        assert result["email"] == "affiliate@test.com"
        assert result["parent"] is None

    @patch('services.affiliate_service.get_db')
    def test_get_by_id_with_parent(self, mock_get_db, mock_affiliate):
        """Test getting affiliate with parent."""
        mock_affiliate.parent_affiliate_id = 2

        parent = Mock()
        parent.id = 2
        parent.name = "Parent Affiliate"
        parent.affiliate_code = "PAR12345"

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate,
            parent,
        ]
        mock_get_db.return_value = mock_session

        result = get_affiliate_by_id(1)

        assert result is not None
        assert result["parent"]["id"] == 2
        assert result["parent"]["name"] == "Parent Affiliate"

    @patch('services.affiliate_service.get_db')
    def test_get_by_id_parent_not_found(self, mock_get_db, mock_affiliate):
        """Test getting affiliate when parent not found."""
        mock_affiliate.parent_affiliate_id = 2

        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate,
            None,  # Parent not found
        ]
        mock_get_db.return_value = mock_session

        result = get_affiliate_by_id(1)

        assert result is not None
        assert result["parent"] is None


# ============== apply_for_affiliate Tests ==============


class TestApplyForAffiliate:
    """Tests for apply_for_affiliate function."""

    @patch('services.affiliate_service.create_affiliate')
    @patch('services.affiliate_service.get_db')
    def test_apply_without_referrer(self, mock_get_db, mock_create):
        """Test affiliate application without referrer code."""
        mock_create.return_value = {"success": True, "affiliate_id": 1}

        result = apply_for_affiliate(
            name="New Affiliate",
            email="new@test.com",
            phone="555-1234"
        )

        assert result["success"] is True
        mock_create.assert_called_once()
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["parent_affiliate_id"] is None
        assert call_kwargs["status"] == "pending"

    @patch('services.affiliate_service.create_affiliate')
    @patch('services.affiliate_service.get_db')
    def test_apply_with_valid_referrer(self, mock_get_db, mock_create):
        """Test affiliate application with valid referrer code."""
        parent = Mock()
        parent.id = 1
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = parent
        mock_get_db.return_value = mock_session
        mock_create.return_value = {"success": True, "affiliate_id": 2}

        result = apply_for_affiliate(
            name="New Affiliate",
            email="new@test.com",
            referrer_code="PAR12345"
        )

        assert result["success"] is True
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["parent_affiliate_id"] == 1

    @patch('services.affiliate_service.create_affiliate')
    @patch('services.affiliate_service.get_db')
    def test_apply_with_invalid_referrer(self, mock_get_db, mock_create):
        """Test affiliate application with invalid referrer code."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session
        mock_create.return_value = {"success": True, "affiliate_id": 2}

        result = apply_for_affiliate(
            name="New Affiliate",
            email="new@test.com",
            referrer_code="INVALID123"
        )

        assert result["success"] is True
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["parent_affiliate_id"] is None

    @patch('services.affiliate_service.create_affiliate')
    @patch('services.affiliate_service.get_db')
    def test_apply_with_inactive_referrer(self, mock_get_db, mock_create):
        """Test affiliate application with inactive referrer."""
        mock_session = Mock()
        # Filter for active status returns None
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session
        mock_create.return_value = {"success": True, "affiliate_id": 2}

        result = apply_for_affiliate(
            name="New Affiliate",
            email="new@test.com",
            referrer_code="INACTIVE"
        )

        assert result["success"] is True
        call_kwargs = mock_create.call_args[1]
        assert call_kwargs["parent_affiliate_id"] is None


# ============== get_dashboard_stats Tests ==============


class TestGetDashboardStats:
    """Tests for get_dashboard_stats function."""

    @patch('services.affiliate_service.get_db')
    def test_get_dashboard_stats_empty(self, mock_get_db):
        """Test dashboard stats with no data."""
        mock_session = Mock()
        mock_session.query.return_value.count.return_value = 0
        mock_session.query.return_value.filter.return_value.count.return_value = 0
        mock_session.query.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        result = get_dashboard_stats()

        assert result["total_affiliates"] == 0
        assert result["active_affiliates"] == 0
        assert result["pending_affiliates"] == 0
        assert result["total_referrals"] == 0
        assert result["total_pending_payouts"] == 0
        assert result["total_paid"] == 0
        assert result["total_earnings"] == 0
        assert result["pending_commissions"] == 0

    @patch('services.affiliate_service.get_db')
    def test_get_dashboard_stats_with_data(self, mock_get_db, mock_affiliate):
        """Test dashboard stats with data."""
        mock_affiliate2 = Mock()
        mock_affiliate2.pending_earnings = 50.0
        mock_affiliate2.paid_out = 200.0
        mock_affiliate2.total_earnings = 250.0

        mock_session = Mock()
        mock_session.query.return_value.count.return_value = 10
        mock_session.query.return_value.filter.return_value.count.side_effect = [5, 3, 25, 15]
        mock_session.query.return_value.all.return_value = [mock_affiliate, mock_affiliate2]
        mock_get_db.return_value = mock_session

        result = get_dashboard_stats()

        assert result["total_affiliates"] == 10
        assert result["active_affiliates"] == 5
        assert result["pending_affiliates"] == 3
        assert result["total_referrals"] == 25
        assert result["pending_commissions"] == 15
        assert result["total_pending_payouts"] == 150.0  # 100 + 50
        assert result["total_paid"] == 600.0  # 400 + 200
        assert result["total_earnings"] == 750.0  # 500 + 250

    @patch('services.affiliate_service.get_db')
    def test_get_dashboard_stats_handles_null_values(self, mock_get_db):
        """Test dashboard stats handles null earnings values."""
        mock_affiliate = Mock()
        mock_affiliate.pending_earnings = None
        mock_affiliate.paid_out = None
        mock_affiliate.total_earnings = None

        mock_session = Mock()
        mock_session.query.return_value.count.return_value = 1
        mock_session.query.return_value.filter.return_value.count.return_value = 0
        mock_session.query.return_value.all.return_value = [mock_affiliate]
        mock_get_db.return_value = mock_session

        result = get_dashboard_stats()

        assert result["total_pending_payouts"] == 0
        assert result["total_paid"] == 0
        assert result["total_earnings"] == 0


# ============== Edge Cases and Error Handling ==============


class TestEdgeCases:
    """Test edge cases and error handling."""

    @patch('services.affiliate_service.get_db')
    def test_validate_code_closes_session(self, mock_get_db, mock_affiliate):
        """Test validate_affiliate_code closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_get_db.return_value = mock_session

        validate_affiliate_code("TES12345")

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_process_referral_closes_session(self, mock_get_db, mock_affiliate, mock_client):
        """Test process_referral closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate,
            mock_client,
        ]
        mock_get_db.return_value = mock_session

        process_referral(1, "TES12345")

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_calculate_commission_closes_session(self, mock_get_db, mock_client, mock_affiliate):
        """Test calculate_commission closes database session."""
        mock_client.referred_by_affiliate_id = 1
        mock_affiliate.parent_affiliate_id = None
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            mock_affiliate,
        ]
        mock_get_db.return_value = mock_session

        calculate_commission(1, "signup", 100.00)

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_get_affiliate_stats_closes_session(self, mock_get_db, mock_affiliate):
        """Test get_affiliate_stats closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        get_affiliate_stats(1)

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_process_payout_closes_session(self, mock_get_db, mock_affiliate):
        """Test process_payout closes database session."""
        mock_affiliate.pending_earnings = 100.0
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        process_payout(1, 50)

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_get_commission_history_closes_session(self, mock_get_db):
        """Test get_commission_history closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        get_commission_history(1)

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_get_referral_tree_closes_session(self, mock_get_db, mock_affiliate):
        """Test get_referral_tree closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        get_referral_tree(1)

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_create_affiliate_closes_session(self, mock_get_db):
        """Test create_affiliate closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = Mock()  # Existing email
        mock_get_db.return_value = mock_session

        create_affiliate("Test", "existing@test.com")

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_update_affiliate_closes_session(self, mock_get_db):
        """Test update_affiliate closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        update_affiliate(999, name="Test")

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_get_all_affiliates_closes_session(self, mock_get_db):
        """Test get_all_affiliates closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        get_all_affiliates()

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_get_affiliate_by_id_closes_session(self, mock_get_db):
        """Test get_affiliate_by_id closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_session

        get_affiliate_by_id(999)

        mock_session.close.assert_called_once()

    @patch('services.affiliate_service.get_db')
    def test_get_dashboard_stats_closes_session(self, mock_get_db):
        """Test get_dashboard_stats closes database session."""
        mock_session = Mock()
        mock_session.query.return_value.count.return_value = 0
        mock_session.query.return_value.filter.return_value.count.return_value = 0
        mock_session.query.return_value.all.return_value = []
        mock_get_db.return_value = mock_session

        get_dashboard_stats()

        mock_session.close.assert_called_once()
