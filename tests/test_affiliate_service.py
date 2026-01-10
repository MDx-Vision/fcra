"""
Unit tests for AffiliateService

Tests affiliate management, commission tracking, and payout processing.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.affiliate_service import (
    AffiliateService,
    generate_affiliate_code,
    get_affiliate_by_code,
    record_client_referral,
    AFFILIATE_STATUSES,
    COMMISSION_TRIGGERS,
    PAYOUT_METHODS,
    PAYOUT_STATUSES,
)


class TestGenerateAffiliateCode:
    """Tests for the generate_affiliate_code function"""

    def test_generates_code_with_name_prefix(self):
        """Should generate code with 3-letter name prefix"""
        code = generate_affiliate_code("John Smith")
        assert code.startswith("JOH")
        assert len(code) == 8

    def test_generates_code_with_short_name(self):
        """Should pad short names with X"""
        code = generate_affiliate_code("Al")
        assert code.startswith("ALX")
        assert len(code) == 8

    def test_generates_code_with_single_letter_name(self):
        """Should pad single letter names"""
        code = generate_affiliate_code("A")
        assert code.startswith("AXX")
        assert len(code) == 8

    def test_generates_unique_codes(self):
        """Should generate unique codes each time"""
        codes = [generate_affiliate_code("Test") for _ in range(10)]
        assert len(set(codes)) == 10

    def test_generates_code_with_non_alpha_chars(self):
        """Should only use alphabetic characters for prefix"""
        code = generate_affiliate_code("John123!@#Smith")
        assert code[:3].isalpha()

    def test_generates_code_with_empty_name(self):
        """Should handle empty name"""
        code = generate_affiliate_code("")
        assert code.startswith("XXX")
        assert len(code) == 8


class TestConstants:
    """Tests for module constants"""

    def test_affiliate_statuses(self):
        """Should have all expected affiliate statuses"""
        assert "pending" in AFFILIATE_STATUSES
        assert "active" in AFFILIATE_STATUSES
        assert "suspended" in AFFILIATE_STATUSES
        assert "inactive" in AFFILIATE_STATUSES

    def test_commission_triggers(self):
        """Should have all expected commission triggers"""
        assert "signup" in COMMISSION_TRIGGERS
        assert "payment" in COMMISSION_TRIGGERS
        assert "subscription" in COMMISSION_TRIGGERS
        assert "milestone" in COMMISSION_TRIGGERS

    def test_payout_methods(self):
        """Should have all expected payout methods"""
        assert "paypal" in PAYOUT_METHODS
        assert "bank_transfer" in PAYOUT_METHODS
        assert "check" in PAYOUT_METHODS
        assert "venmo" in PAYOUT_METHODS
        assert "zelle" in PAYOUT_METHODS

    def test_payout_statuses(self):
        """Should have all expected payout statuses"""
        assert "pending" in PAYOUT_STATUSES
        assert "processing" in PAYOUT_STATUSES
        assert "completed" in PAYOUT_STATUSES
        assert "failed" in PAYOUT_STATUSES


class TestAffiliateServiceCreateAffiliate:
    """Tests for AffiliateService.create_affiliate"""

    def test_create_affiliate_success(self):
        """Should create affiliate successfully"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch('services.affiliate_service.Affiliate') as MockAffiliate:
            mock_instance = MagicMock()
            mock_instance.id = 1
            mock_instance.affiliate_code = "TES12345"
            MockAffiliate.return_value = mock_instance

            result = AffiliateService.create_affiliate(
                name="Test Affiliate",
                email="test@example.com",
                phone="555-1234",
                session=mock_session
            )

        assert result["success"] is True
        assert "affiliate_id" in result

    def test_create_affiliate_duplicate_email(self):
        """Should fail if email already exists"""
        mock_session = MagicMock()
        mock_existing = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_existing

        result = AffiliateService.create_affiliate(
            name="Test",
            email="existing@example.com",
            session=mock_session
        )

        assert result["success"] is False
        assert "already exists" in result["error"]

    def test_create_affiliate_with_parent(self):
        """Should create affiliate with parent relationship"""
        mock_session = MagicMock()
        mock_parent = MagicMock()
        mock_parent.id = 1
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            None, None, mock_parent
        ]

        with patch('services.affiliate_service.Affiliate') as MockAffiliate:
            mock_instance = MagicMock()
            mock_instance.id = 2
            mock_instance.affiliate_code = "TES12345"
            MockAffiliate.return_value = mock_instance

            result = AffiliateService.create_affiliate(
                name="Sub Affiliate",
                email="sub@example.com",
                parent_affiliate_id=1,
                session=mock_session
            )

        assert result["success"] is True

    def test_create_affiliate_invalid_parent(self):
        """Should fail if parent affiliate doesn't exist"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            None, None, None
        ]

        result = AffiliateService.create_affiliate(
            name="Sub Affiliate",
            email="sub@example.com",
            parent_affiliate_id=999,
            session=mock_session
        )

        assert result["success"] is False
        assert "Parent affiliate not found" in result["error"]


class TestAffiliateServiceUpdateAffiliate:
    """Tests for AffiliateService.update_affiliate"""

    def test_update_affiliate_success(self):
        """Should update affiliate successfully"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.name = "Old Name"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate

        result = AffiliateService.update_affiliate(
            affiliate_id=1,
            name="New Name",
            phone="555-9999",
            session=mock_session
        )

        assert result["success"] is True
        assert mock_affiliate.name == "New Name"
        assert mock_affiliate.phone == "555-9999"

    def test_update_affiliate_not_found(self):
        """Should fail if affiliate not found"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = AffiliateService.update_affiliate(
            affiliate_id=999,
            name="New Name",
            session=mock_session
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_update_affiliate_status_change(self):
        """Should update affiliate status"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.status = "pending"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate

        result = AffiliateService.update_affiliate(
            affiliate_id=1,
            status="active",
            session=mock_session
        )

        assert result["success"] is True
        assert mock_affiliate.status == "active"

    def test_update_affiliate_commission_rates(self):
        """Should update commission rates"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.commission_rate_1 = 0.10
        mock_affiliate.commission_rate_2 = 0.05
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate

        result = AffiliateService.update_affiliate(
            affiliate_id=1,
            commission_rate_1=0.15,
            commission_rate_2=0.08,
            session=mock_session
        )

        assert result["success"] is True
        assert mock_affiliate.commission_rate_1 == 0.15
        assert mock_affiliate.commission_rate_2 == 0.08


class TestAffiliateServiceGetAffiliate:
    """Tests for AffiliateService.get_affiliate"""

    def test_get_affiliate_by_id(self):
        """Should get affiliate by ID"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.id = 1
        mock_affiliate.name = "Test Affiliate"
        mock_affiliate.email = "test@example.com"
        mock_affiliate.phone = "555-1234"
        mock_affiliate.company_name = "Test Co"
        mock_affiliate.affiliate_code = "TES12345"
        mock_affiliate.parent_affiliate_id = None
        mock_affiliate.commission_rate_1 = 0.10
        mock_affiliate.commission_rate_2 = 0.05
        mock_affiliate.status = "active"
        mock_affiliate.payout_method = "paypal"
        mock_affiliate.payout_details = {}
        mock_affiliate.total_referrals = 5
        mock_affiliate.total_earnings = 100.0
        mock_affiliate.pending_earnings = 50.0
        mock_affiliate.paid_out = 50.0
        mock_affiliate.created_at = datetime.utcnow()
        mock_affiliate.updated_at = datetime.utcnow()

        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.count.return_value = 2

        result = AffiliateService.get_affiliate(affiliate_id=1, session=mock_session)

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "Test Affiliate"
        assert result["status"] == "active"

    def test_get_affiliate_by_code(self):
        """Should get affiliate by code"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.id = 1
        mock_affiliate.name = "Test Affiliate"
        mock_affiliate.email = "test@example.com"
        mock_affiliate.phone = None
        mock_affiliate.company_name = None
        mock_affiliate.affiliate_code = "TES12345"
        mock_affiliate.parent_affiliate_id = None
        mock_affiliate.commission_rate_1 = 0.10
        mock_affiliate.commission_rate_2 = 0.05
        mock_affiliate.status = "active"
        mock_affiliate.payout_method = None
        mock_affiliate.payout_details = None
        mock_affiliate.total_referrals = 0
        mock_affiliate.total_earnings = 0.0
        mock_affiliate.pending_earnings = 0.0
        mock_affiliate.paid_out = 0.0
        mock_affiliate.created_at = None
        mock_affiliate.updated_at = None

        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.count.return_value = 0

        result = AffiliateService.get_affiliate(affiliate_code="TES12345", session=mock_session)

        assert result is not None
        assert result["affiliate_code"] == "TES12345"

    def test_get_affiliate_not_found(self):
        """Should return None if affiliate not found"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = AffiliateService.get_affiliate(affiliate_id=999, session=mock_session)

        assert result is None

    def test_get_affiliate_no_params(self):
        """Should return None if no search params provided"""
        mock_session = MagicMock()
        result = AffiliateService.get_affiliate(session=mock_session)
        assert result is None


class TestAffiliateServiceListAffiliates:
    """Tests for AffiliateService.list_affiliates"""

    def test_list_affiliates_all(self):
        """Should list all affiliates"""
        mock_session = MagicMock()
        mock_affiliate1 = MagicMock()
        mock_affiliate1.id = 1
        mock_affiliate1.name = "Affiliate 1"
        mock_affiliate1.email = "a1@example.com"
        mock_affiliate1.phone = None
        mock_affiliate1.company_name = None
        mock_affiliate1.affiliate_code = "AFF00001"
        mock_affiliate1.parent_affiliate_id = None
        mock_affiliate1.commission_rate_1 = 0.10
        mock_affiliate1.commission_rate_2 = 0.05
        mock_affiliate1.status = "active"
        mock_affiliate1.total_referrals = 5
        mock_affiliate1.total_earnings = 100.0
        mock_affiliate1.pending_earnings = 50.0
        mock_affiliate1.paid_out = 50.0
        mock_affiliate1.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = [mock_affiliate1]
        mock_session.query.return_value = mock_query
        mock_session.query.return_value.filter.return_value.count.return_value = 0

        result = AffiliateService.list_affiliates(session=mock_session)

        assert len(result) == 1
        assert result[0]["name"] == "Affiliate 1"

    def test_list_affiliates_by_status(self):
        """Should filter affiliates by status"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.id = 1
        mock_affiliate.name = "Active Affiliate"
        mock_affiliate.email = "active@example.com"
        mock_affiliate.phone = None
        mock_affiliate.company_name = None
        mock_affiliate.affiliate_code = "ACT12345"
        mock_affiliate.parent_affiliate_id = None
        mock_affiliate.commission_rate_1 = 0.10
        mock_affiliate.commission_rate_2 = 0.05
        mock_affiliate.status = "active"
        mock_affiliate.total_referrals = 0
        mock_affiliate.total_earnings = 0.0
        mock_affiliate.pending_earnings = 0.0
        mock_affiliate.paid_out = 0.0
        mock_affiliate.created_at = None

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [mock_affiliate]
        mock_session.query.return_value = mock_query
        mock_session.query.return_value.filter.return_value.count.return_value = 0

        result = AffiliateService.list_affiliates(status="active", session=mock_session)

        assert len(result) == 1
        assert result[0]["status"] == "active"


class TestAffiliateServiceDeleteAffiliate:
    """Tests for AffiliateService.delete_affiliate"""

    def test_delete_affiliate_success(self):
        """Should delete affiliate successfully"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.name = "Test Affiliate"
        mock_affiliate.total_referrals = 0
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.count.return_value = 0

        result = AffiliateService.delete_affiliate(affiliate_id=1, session=mock_session)

        assert result["success"] is True
        mock_session.delete.assert_called_once()

    def test_delete_affiliate_not_found(self):
        """Should fail if affiliate not found"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = AffiliateService.delete_affiliate(affiliate_id=999, session=mock_session)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_delete_affiliate_with_referrals(self):
        """Should fail if affiliate has referrals"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.total_referrals = 5
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate

        result = AffiliateService.delete_affiliate(affiliate_id=1, session=mock_session)

        assert result["success"] is False
        assert "existing referrals" in result["error"]

    def test_delete_affiliate_with_sub_affiliates(self):
        """Should fail if affiliate has sub-affiliates"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.total_referrals = 0
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.count.return_value = 2

        result = AffiliateService.delete_affiliate(affiliate_id=1, session=mock_session)

        assert result["success"] is False
        assert "sub-affiliates" in result["error"]


class TestAffiliateServiceRecordReferral:
    """Tests for AffiliateService.record_referral"""

    def test_record_referral_success(self):
        """Should record referral and create commission"""
        mock_session = MagicMock()

        mock_affiliate = MagicMock()
        mock_affiliate.id = 1
        mock_affiliate.affiliate_code = "TES12345"
        mock_affiliate.status = "active"
        mock_affiliate.commission_rate_1 = 0.10
        mock_affiliate.parent_affiliate_id = None
        mock_affiliate.total_referrals = 0
        mock_affiliate.pending_earnings = 0.0
        mock_affiliate.total_earnings = 0.0

        mock_client = MagicMock()
        mock_client.id = 100

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate, mock_client
        ]

        with patch('services.affiliate_service.Commission'):
            result = AffiliateService.record_referral(
                affiliate_code="TES12345",
                client_id=100,
                trigger_type="signup",
                trigger_amount=100.0,
                session=mock_session
            )

        assert result["success"] is True
        assert len(result["commissions"]) == 1
        assert result["commissions"][0]["level"] == 1
        assert result["commissions"][0]["amount"] == 10.0

    def test_record_referral_with_parent(self):
        """Should create two-level commission with parent affiliate"""
        mock_session = MagicMock()

        mock_affiliate = MagicMock()
        mock_affiliate.id = 2
        mock_affiliate.affiliate_code = "SUB12345"
        mock_affiliate.status = "active"
        mock_affiliate.commission_rate_1 = 0.10
        mock_affiliate.parent_affiliate_id = 1
        mock_affiliate.total_referrals = 0
        mock_affiliate.pending_earnings = 0.0
        mock_affiliate.total_earnings = 0.0

        mock_parent = MagicMock()
        mock_parent.id = 1
        mock_parent.status = "active"
        mock_parent.commission_rate_2 = 0.05
        mock_parent.pending_earnings = 0.0
        mock_parent.total_earnings = 0.0

        mock_client = MagicMock()
        mock_client.id = 100

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate, mock_client, mock_parent
        ]

        with patch('services.affiliate_service.Commission'):
            result = AffiliateService.record_referral(
                affiliate_code="SUB12345",
                client_id=100,
                trigger_type="signup",
                trigger_amount=100.0,
                session=mock_session
            )

        assert result["success"] is True
        assert len(result["commissions"]) == 2
        assert result["commissions"][1]["level"] == 2
        assert result["commissions"][1]["amount"] == 5.0

    def test_record_referral_affiliate_not_found(self):
        """Should fail if affiliate code not found"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = AffiliateService.record_referral(
            affiliate_code="INVALID",
            client_id=100,
            session=mock_session
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_record_referral_affiliate_inactive(self):
        """Should fail if affiliate is not active"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.status = "inactive"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate

        result = AffiliateService.record_referral(
            affiliate_code="TES12345",
            client_id=100,
            session=mock_session
        )

        assert result["success"] is False
        assert "not active" in result["error"]

    def test_record_referral_client_not_found(self):
        """Should fail if client not found"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.status = "active"
        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_affiliate, None
        ]

        result = AffiliateService.record_referral(
            affiliate_code="TES12345",
            client_id=999,
            session=mock_session
        )

        assert result["success"] is False
        assert "Client not found" in result["error"]


class TestAffiliateServiceGetCommissions:
    """Tests for AffiliateService.get_commissions"""

    def test_get_commissions_all(self):
        """Should get all commissions"""
        mock_session = MagicMock()
        mock_commission = MagicMock()
        mock_commission.id = 1
        mock_commission.affiliate_id = 1
        mock_commission.client_id = 100
        mock_commission.level = 1
        mock_commission.trigger_type = "signup"
        mock_commission.trigger_amount = 100.0
        mock_commission.commission_rate = 0.10
        mock_commission.commission_amount = 10.0
        mock_commission.status = "pending"
        mock_commission.paid_at = None
        mock_commission.payout_id = None
        mock_commission.notes = None
        mock_commission.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = [mock_commission]
        mock_session.query.return_value = mock_query

        result = AffiliateService.get_commissions(session=mock_session)

        assert len(result) == 1
        assert result[0]["commission_amount"] == 10.0

    def test_get_commissions_by_affiliate(self):
        """Should filter commissions by affiliate"""
        mock_session = MagicMock()
        mock_commission = MagicMock()
        mock_commission.id = 1
        mock_commission.affiliate_id = 1
        mock_commission.client_id = 100
        mock_commission.level = 1
        mock_commission.trigger_type = "signup"
        mock_commission.trigger_amount = 100.0
        mock_commission.commission_rate = 0.10
        mock_commission.commission_amount = 10.0
        mock_commission.status = "pending"
        mock_commission.paid_at = None
        mock_commission.payout_id = None
        mock_commission.notes = None
        mock_commission.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [mock_commission]
        mock_session.query.return_value = mock_query

        result = AffiliateService.get_commissions(affiliate_id=1, session=mock_session)

        assert len(result) == 1
        assert result[0]["affiliate_id"] == 1


class TestAffiliateServiceCreatePayout:
    """Tests for AffiliateService.create_payout"""

    def test_create_payout_success(self):
        """Should create payout successfully"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.id = 1
        mock_affiliate.name = "Test"
        mock_affiliate.pending_earnings = 100.0
        mock_affiliate.payout_method = "paypal"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate

        with patch('services.affiliate_service.AffiliatePayout') as MockPayout:
            mock_instance = MagicMock()
            mock_instance.id = 1
            MockPayout.return_value = mock_instance

            result = AffiliateService.create_payout(
                affiliate_id=1,
                amount=50.0,
                session=mock_session
            )

        assert result["success"] is True
        assert "payout_id" in result

    def test_create_payout_affiliate_not_found(self):
        """Should fail if affiliate not found"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = AffiliateService.create_payout(
            affiliate_id=999,
            amount=50.0,
            session=mock_session
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_create_payout_exceeds_pending(self):
        """Should fail if amount exceeds pending earnings"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.pending_earnings = 50.0
        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate

        result = AffiliateService.create_payout(
            affiliate_id=1,
            amount=100.0,
            session=mock_session
        )

        assert result["success"] is False
        assert "exceeds" in result["error"]


class TestAffiliateServiceProcessPayout:
    """Tests for AffiliateService.process_payout"""

    def test_process_payout_success(self):
        """Should process payout successfully"""
        mock_session = MagicMock()
        mock_payout = MagicMock()
        mock_payout.id = 1
        mock_payout.affiliate_id = 1
        mock_payout.amount = 50.0
        mock_payout.status = "pending"
        mock_payout.commission_ids = [1, 2]

        mock_affiliate = MagicMock()
        mock_affiliate.pending_earnings = 100.0
        mock_affiliate.paid_out = 50.0

        mock_commission = MagicMock()
        mock_commission.id = 1
        mock_commission.status = "pending"

        mock_session.query.return_value.filter.return_value.first.side_effect = [
            mock_payout, mock_affiliate, mock_commission, mock_commission
        ]

        result = AffiliateService.process_payout(
            payout_id=1,
            payout_reference="CHK-001",
            session=mock_session
        )

        assert result["success"] is True
        assert mock_payout.status == "completed"

    def test_process_payout_not_found(self):
        """Should fail if payout not found"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = AffiliateService.process_payout(payout_id=999, session=mock_session)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_process_payout_already_completed(self):
        """Should fail if payout already completed"""
        mock_session = MagicMock()
        mock_payout = MagicMock()
        mock_payout.status = "completed"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_payout

        result = AffiliateService.process_payout(payout_id=1, session=mock_session)

        assert result["success"] is False
        assert "already completed" in result["error"]


class TestAffiliateServiceGetPayouts:
    """Tests for AffiliateService.get_payouts"""

    def test_get_payouts_all(self):
        """Should get all payouts"""
        mock_session = MagicMock()
        mock_payout = MagicMock()
        mock_payout.id = 1
        mock_payout.affiliate_id = 1
        mock_payout.amount = 50.0
        mock_payout.payout_method = "paypal"
        mock_payout.payout_reference = "TXN-001"
        mock_payout.status = "completed"
        mock_payout.commission_ids = [1, 2]
        mock_payout.notes = None
        mock_payout.processed_by_id = 1
        mock_payout.processed_at = datetime.utcnow()
        mock_payout.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = [mock_payout]
        mock_session.query.return_value = mock_query

        result = AffiliateService.get_payouts(session=mock_session)

        assert len(result) == 1
        assert result[0]["amount"] == 50.0

    def test_get_payouts_by_affiliate(self):
        """Should filter payouts by affiliate"""
        mock_session = MagicMock()
        mock_payout = MagicMock()
        mock_payout.id = 1
        mock_payout.affiliate_id = 1
        mock_payout.amount = 50.0
        mock_payout.payout_method = "paypal"
        mock_payout.payout_reference = None
        mock_payout.status = "pending"
        mock_payout.commission_ids = []
        mock_payout.notes = None
        mock_payout.processed_by_id = None
        mock_payout.processed_at = None
        mock_payout.created_at = datetime.utcnow()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [mock_payout]
        mock_session.query.return_value = mock_query

        result = AffiliateService.get_payouts(affiliate_id=1, session=mock_session)

        assert len(result) == 1
        assert result[0]["affiliate_id"] == 1


class TestAffiliateServiceGetStats:
    """Tests for AffiliateService.get_affiliate_stats"""

    def test_get_affiliate_stats_specific(self):
        """Should get stats for specific affiliate"""
        mock_session = MagicMock()
        mock_affiliate = MagicMock()
        mock_affiliate.id = 1
        mock_affiliate.total_referrals = 10
        mock_affiliate.total_earnings = 500.0

        mock_commission = MagicMock()
        mock_commission.commission_amount = 50.0
        mock_commission.status = "pending"

        mock_session.query.return_value.filter.return_value.first.return_value = mock_affiliate
        mock_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_commission], []
        ]

        result = AffiliateService.get_affiliate_stats(affiliate_id=1, session=mock_session)

        assert result["affiliate_id"] == 1
        assert result["total_referrals"] == 10

    def test_get_affiliate_stats_not_found(self):
        """Should return error if affiliate not found"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = AffiliateService.get_affiliate_stats(affiliate_id=999, session=mock_session)

        assert "error" in result
        assert "not found" in result["error"]


class TestAffiliateServiceGetDashboardData:
    """Tests for AffiliateService.get_dashboard_data"""

    def test_get_dashboard_data(self):
        """Should get dashboard data"""
        mock_session = MagicMock()

        with patch.object(AffiliateService, 'get_affiliate_stats') as mock_stats:
            mock_stats.return_value = {
                "total_affiliates": 10,
                "active_affiliates": 8,
                "total_earnings": 1000.0
            }

            mock_affiliate = MagicMock()
            mock_affiliate.id = 1
            mock_affiliate.name = "Top Affiliate"
            mock_affiliate.affiliate_code = "TOP12345"
            mock_affiliate.total_referrals = 50
            mock_affiliate.total_earnings = 500.0

            mock_payout = MagicMock()
            mock_payout.id = 1
            mock_payout.affiliate_id = 1
            mock_payout.amount = 100.0
            mock_payout.status = "completed"
            mock_payout.created_at = datetime.utcnow()

            mock_query = MagicMock()
            mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_affiliate]
            mock_query.order_by.return_value.limit.return_value.all.return_value = [mock_payout]
            mock_query.filter.return_value.count.return_value = 5
            mock_session.query.return_value = mock_query

            result = AffiliateService.get_dashboard_data(session=mock_session)

        assert "stats" in result
        assert "top_affiliates" in result
        assert "recent_payouts" in result
        assert "pending_payout_count" in result


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    def test_get_affiliate_by_code(self):
        """Should get affiliate by code using convenience function"""
        with patch.object(AffiliateService, 'get_affiliate') as mock_get:
            mock_get.return_value = {"id": 1, "affiliate_code": "TES12345"}

            result = get_affiliate_by_code("TES12345")

            mock_get.assert_called_once_with(affiliate_code="TES12345")
            assert result["affiliate_code"] == "TES12345"

    def test_record_client_referral(self):
        """Should record referral using convenience function"""
        with patch.object(AffiliateService, 'record_referral') as mock_record:
            mock_record.return_value = {"success": True, "affiliate_id": 1}

            result = record_client_referral("TES12345", 100, 500.0)

            mock_record.assert_called_once_with(
                affiliate_code="TES12345",
                client_id=100,
                trigger_type="signup",
                trigger_amount=500.0
            )
            assert result["success"] is True
