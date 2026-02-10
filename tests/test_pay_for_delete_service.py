"""
Unit tests for Pay-for-Delete Negotiation Service (ISSUE-007)
Tests CRUD operations, status transitions, statistics, and letter generation.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from services.pay_for_delete_service import (
    PayForDeleteService,
    P4D_STATUSES,
    COMMON_COLLECTORS,
    get_pay_for_delete_service,
    get_common_collectors,
    get_p4d_statuses,
)


class TestP4DConstants:
    """Test P4D constants and exports"""

    def test_p4d_statuses_has_all_required_statuses(self):
        """Ensure all status keys are present"""
        required = [
            "pending", "offered", "countered", "negotiating",
            "agreed", "payment_pending", "paid", "awaiting_deletion",
            "deleted", "failed", "cancelled"
        ]
        for status in required:
            assert status in P4D_STATUSES

    def test_p4d_statuses_have_descriptions(self):
        """All statuses should have human-readable descriptions"""
        for status, description in P4D_STATUSES.items():
            assert isinstance(description, str)
            assert len(description) > 5

    def test_common_collectors_has_entries(self):
        """Ensure common collectors list is populated"""
        assert len(COMMON_COLLECTORS) >= 5

    def test_common_collectors_have_required_fields(self):
        """Each collector should have name, p4d_friendly, typical_accept"""
        for collector in COMMON_COLLECTORS:
            assert "name" in collector
            assert "p4d_friendly" in collector
            assert "typical_accept" in collector

    def test_get_common_collectors_returns_list(self):
        """Factory function should return the collectors list"""
        result = get_common_collectors()
        assert isinstance(result, list)
        assert result == COMMON_COLLECTORS

    def test_get_p4d_statuses_returns_dict(self):
        """Factory function should return the status dict"""
        result = get_p4d_statuses()
        assert isinstance(result, dict)
        assert result == P4D_STATUSES


class TestPayForDeleteServiceCRUD:
    """Test CRUD operations for P4D negotiations"""

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session"""
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        session.query.return_value.filter_by.return_value.all.return_value = []
        session.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        return session

    @pytest.fixture
    def service(self, mock_session):
        """Create service instance with mock session"""
        return PayForDeleteService(session=mock_session)

    def test_create_negotiation_basic(self, service, mock_session):
        """Test creating a basic negotiation"""
        result = service.create_negotiation(
            client_id=1,
            collector_name="Portfolio Recovery Associates",
            original_balance=1500.00
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        assert result.client_id == 1
        assert result.collector_name == "Portfolio Recovery Associates"
        assert result.original_balance == 1500.00
        assert result.status == "pending"

    def test_create_negotiation_with_all_fields(self, service, mock_session):
        """Test creating negotiation with all optional fields"""
        result = service.create_negotiation(
            client_id=1,
            collector_name="Midland Credit Management",
            original_balance=2500.00,
            current_balance=2200.00,
            account_number="ACC-12345",
            original_creditor="Capital One",
            collector_address="123 Collection St",
            collector_phone="555-1234",
            collector_email="collections@example.com",
            dispute_item_id=42,
            assigned_staff_id=5,
            notes="Initial P4D attempt"
        )

        assert result.current_balance == 2200.00
        assert result.account_number == "ACC-12345"
        assert result.original_creditor == "Capital One"
        assert result.collector_address == "123 Collection St"
        assert result.notes == "Initial P4D attempt"

    def test_create_negotiation_current_balance_defaults_to_original(self, service, mock_session):
        """When current_balance not provided, use original_balance"""
        result = service.create_negotiation(
            client_id=1,
            collector_name="Test Collector",
            original_balance=1000.00
        )

        assert result.current_balance == 1000.00

    def test_get_negotiation_found(self, service, mock_session):
        """Test getting a negotiation by ID"""
        mock_negotiation = MagicMock()
        mock_negotiation.id = 1
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_negotiation

        result = service.get_negotiation(1)
        assert result == mock_negotiation

    def test_get_negotiation_not_found(self, service, mock_session):
        """Test getting a non-existent negotiation"""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = service.get_negotiation(999)
        assert result is None

    def test_get_client_negotiations(self, service, mock_session):
        """Test getting all negotiations for a client"""
        mock_negotiations = [MagicMock(id=1), MagicMock(id=2)]
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_negotiations

        result = service.get_client_negotiations(client_id=1)
        assert len(result) == 2

    def test_get_negotiations_by_status(self, service, mock_session):
        """Test getting negotiations by status"""
        mock_negotiations = [MagicMock(status="pending")]
        mock_session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = mock_negotiations

        result = service.get_negotiations_by_status("pending")
        assert len(result) == 1

    def test_get_all_negotiations_no_filters(self, service, mock_session):
        """Test getting all negotiations without filters"""
        mock_negotiations = [MagicMock(id=i) for i in range(5)]
        mock_session.query.return_value.order_by.return_value.all.return_value = mock_negotiations

        result = service.get_all_negotiations()
        assert len(result) == 5

    def test_get_all_negotiations_with_filters(self, service, mock_session):
        """Test getting negotiations with multiple filters"""
        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []

        result = service.get_all_negotiations(
            status="pending",
            client_id=1,
            assigned_staff_id=2
        )

        # Should have called filter multiple times
        assert mock_query.filter.call_count >= 1

    def test_update_negotiation_success(self, service, mock_session):
        """Test updating a negotiation"""
        mock_negotiation = MagicMock()
        mock_negotiation.notes = "Old notes"
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_negotiation

        result = service.update_negotiation(1, notes="New notes", status="offered")

        assert result.notes == "New notes"
        assert result.status == "offered"
        mock_session.commit.assert_called_once()

    def test_update_negotiation_not_found(self, service, mock_session):
        """Test updating a non-existent negotiation"""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = service.update_negotiation(999, notes="Test")
        assert result is None

    def test_delete_negotiation_success(self, service, mock_session):
        """Test deleting a negotiation"""
        mock_negotiation = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_negotiation

        result = service.delete_negotiation(1)

        assert result is True
        mock_session.delete.assert_called_once_with(mock_negotiation)
        mock_session.commit.assert_called_once()

    def test_delete_negotiation_not_found(self, service, mock_session):
        """Test deleting a non-existent negotiation"""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = service.delete_negotiation(999)
        assert result is False


class TestPayForDeleteStatusTransitions:
    """Test status transition methods"""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_negotiation(self):
        """Create a mock negotiation object"""
        negotiation = MagicMock()
        negotiation.id = 1
        negotiation.client_id = 1
        negotiation.original_balance = 1500.00
        negotiation.current_balance = 1500.00
        negotiation.status = "pending"
        return negotiation

    @pytest.fixture
    def service(self, mock_session, mock_negotiation):
        service = PayForDeleteService(session=mock_session)
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_negotiation
        return service

    def test_make_offer(self, service, mock_negotiation, mock_session):
        """Test making an initial offer"""
        result = service.make_offer(
            negotiation_id=1,
            offer_amount=500.00
        )

        assert result.initial_offer_amount == 500.00
        assert result.status == "offered"
        assert result.initial_offer_date is not None
        mock_session.commit.assert_called_once()

    def test_make_offer_calculates_percent(self, service, mock_negotiation, mock_session):
        """Test that offer percent is calculated correctly"""
        result = service.make_offer(
            negotiation_id=1,
            offer_amount=450.00
        )

        # 450 / 1500 = 30%
        assert result.initial_offer_percent == 30.0

    def test_make_offer_uses_provided_percent(self, service, mock_negotiation, mock_session):
        """Test that provided percent is used if given"""
        result = service.make_offer(
            negotiation_id=1,
            offer_amount=450.00,
            offer_percent=25.0
        )

        assert result.initial_offer_percent == 25.0

    def test_make_offer_not_found(self, service, mock_session):
        """Test making offer on non-existent negotiation"""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        result = service.make_offer(1, 500.00)
        assert result is None

    def test_record_counter_offer(self, service, mock_negotiation, mock_session):
        """Test recording a counter offer from collector"""
        result = service.record_counter_offer(
            negotiation_id=1,
            counter_amount=1000.00
        )

        assert result.counter_offer_amount == 1000.00
        assert result.status == "countered"
        assert result.counter_offer_date is not None
        mock_session.commit.assert_called_once()

    def test_make_counter_offer(self, service, mock_negotiation, mock_session):
        """Test making our counter to their counter"""
        result = service.make_counter_offer(
            negotiation_id=1,
            our_counter_amount=700.00
        )

        assert result.our_counter_amount == 700.00
        assert result.status == "negotiating"
        assert result.our_counter_date is not None
        mock_session.commit.assert_called_once()

    def test_accept_agreement(self, service, mock_negotiation, mock_session):
        """Test accepting an agreement"""
        result = service.accept_agreement(
            negotiation_id=1,
            agreed_amount=600.00,
            agreement_in_writing=True,
            agreement_signed_by="John Smith"
        )

        assert result.agreed_amount == 600.00
        assert result.status == "agreed"
        assert result.agreement_in_writing is True
        assert result.agreement_signed_by == "John Smith"
        mock_session.commit.assert_called_once()

    def test_accept_agreement_calculates_percent(self, service, mock_negotiation, mock_session):
        """Test that agreed percent is calculated correctly"""
        result = service.accept_agreement(
            negotiation_id=1,
            agreed_amount=600.00
        )

        # 600 / 1500 = 40%
        assert result.agreed_percent == 40.0

    def test_accept_agreement_with_deadlines(self, service, mock_negotiation, mock_session):
        """Test accepting agreement with payment/deletion deadlines"""
        payment_deadline = datetime.now() + timedelta(days=30)
        deletion_deadline = datetime.now() + timedelta(days=60)

        result = service.accept_agreement(
            negotiation_id=1,
            agreed_amount=600.00,
            payment_deadline=payment_deadline,
            deletion_deadline=deletion_deadline
        )

        assert result.payment_deadline is not None
        assert result.deletion_deadline is not None

    def test_record_payment(self, service, mock_negotiation, mock_session):
        """Test recording payment"""
        result = service.record_payment(
            negotiation_id=1,
            payment_amount=600.00,
            payment_method="certified_check",
            payment_confirmation="CHECK-12345"
        )

        assert result.payment_amount == 600.00
        assert result.payment_method == "certified_check"
        assert result.payment_confirmation == "CHECK-12345"
        assert result.status == "paid"
        assert result.payment_date is not None
        mock_session.commit.assert_called_once()

    def test_verify_deletion(self, service, mock_negotiation, mock_session):
        """Test verifying deletion on credit report"""
        result = service.verify_deletion(
            negotiation_id=1,
            verified_bureau="Equifax"
        )

        assert result.deletion_verified is True
        assert result.deletion_verified_bureau == "Equifax"
        assert result.status == "deleted"
        assert result.deletion_verified_date is not None
        mock_session.commit.assert_called_once()

    def test_mark_failed(self, service, mock_negotiation, mock_session):
        """Test marking negotiation as failed"""
        result = service.mark_failed(
            negotiation_id=1,
            reason="Collector refused P4D offer"
        )

        assert result.status == "failed"
        assert result.failure_reason == "Collector refused P4D offer"
        mock_session.commit.assert_called_once()

    def test_cancel_negotiation(self, service, mock_negotiation, mock_session):
        """Test cancelling a negotiation"""
        result = service.cancel_negotiation(
            negotiation_id=1,
            reason="Client changed mind"
        )

        assert result.status == "cancelled"
        assert result.failure_reason == "Client changed mind"
        mock_session.commit.assert_called_once()

    def test_cancel_negotiation_no_reason(self, service, mock_negotiation, mock_session):
        """Test cancelling without providing reason"""
        result = service.cancel_negotiation(negotiation_id=1)

        assert result.status == "cancelled"
        mock_session.commit.assert_called_once()


class TestPayForDeleteStatistics:
    """Test statistics and reporting methods"""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        return session

    @pytest.fixture
    def service(self, mock_session):
        return PayForDeleteService(session=mock_session)

    def test_get_statistics_empty(self, service, mock_session):
        """Test statistics with no negotiations"""
        mock_session.query.return_value.all.return_value = []

        result = service.get_statistics()

        assert result["total"] == 0
        assert result["success_rate"] == 0
        assert result["total_saved"] == 0
        assert result["avg_settlement_percent"] == 0

    def test_get_statistics_with_data(self, service, mock_session):
        """Test statistics with negotiations"""
        # Create mock negotiations
        deleted_neg = MagicMock()
        deleted_neg.status = "deleted"
        deleted_neg.original_balance = 1000.00
        deleted_neg.agreed_amount = 400.00
        deleted_neg.agreed_percent = 40.0

        failed_neg = MagicMock()
        failed_neg.status = "failed"
        failed_neg.original_balance = 500.00
        failed_neg.agreed_amount = None
        failed_neg.agreed_percent = None

        pending_neg = MagicMock()
        pending_neg.status = "pending"
        pending_neg.original_balance = 800.00
        pending_neg.agreed_amount = None
        pending_neg.agreed_percent = None

        mock_session.query.return_value.all.return_value = [deleted_neg, failed_neg, pending_neg]

        result = service.get_statistics()

        assert result["total"] == 3
        assert result["by_status"]["deleted"] == 1
        assert result["by_status"]["failed"] == 1
        assert result["by_status"]["pending"] == 1
        # Success rate: 1 deleted / (1 deleted + 1 failed) = 50%
        assert result["success_rate"] == 50.0
        # Total saved: 1000 - 400 = 600
        assert result["total_saved"] == 600.0
        # Avg settlement: 40%
        assert result["avg_settlement_percent"] == 40.0

    def test_get_pending_follow_ups(self, service, mock_session):
        """Test getting negotiations needing follow-up"""
        mock_negotiations = [MagicMock(id=1), MagicMock(id=2)]
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_negotiations

        result = service.get_pending_follow_ups()
        assert len(result) == 2

    def test_get_awaiting_deletion(self, service, mock_session):
        """Test getting paid negotiations awaiting deletion"""
        mock_negotiations = [MagicMock(status="paid"), MagicMock(status="awaiting_deletion")]
        mock_session.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_negotiations

        result = service.get_awaiting_deletion()
        assert len(result) == 2


class TestPayForDeleteLetterGeneration:
    """Test P4D offer letter generation"""

    @pytest.fixture
    def mock_session(self):
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        client.id = 1
        client.name = None
        client.first_name = "John"
        client.last_name = "Doe"
        client.address_street = "123 Main St"
        client.address_city = "Anytown"
        client.address_state = "TX"
        client.address_zip = "12345"
        return client

    @pytest.fixture
    def mock_negotiation(self):
        negotiation = MagicMock()
        negotiation.id = 1
        negotiation.client_id = 1
        negotiation.collector_name = "Portfolio Recovery Associates"
        negotiation.collector_address = "456 Collection Way, Dallas, TX 75001"
        negotiation.original_balance = 1500.00
        negotiation.current_balance = 1500.00
        negotiation.account_number = "ACC-12345"
        negotiation.original_creditor = "Capital One"
        negotiation.initial_offer_amount = None
        return negotiation

    @pytest.fixture
    def service(self, mock_session, mock_client, mock_negotiation):
        service = PayForDeleteService(session=mock_session)
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_negotiation,
            mock_client
        ]
        return service

    def test_generate_offer_letter_success(self, service, mock_session, mock_client, mock_negotiation):
        """Test generating an offer letter"""
        result = service.generate_offer_letter(
            negotiation_id=1,
            offer_amount=450.00
        )

        assert "content" in result
        assert "client_name" in result
        assert "collector_name" in result
        assert "offer_amount" in result
        assert result["offer_amount"] == 450.00
        assert result["offer_percent"] == 30.0

    def test_generate_offer_letter_contains_client_info(self, service, mock_session, mock_client, mock_negotiation):
        """Test letter contains client information"""
        result = service.generate_offer_letter(
            negotiation_id=1,
            offer_amount=450.00
        )

        content = result["content"]
        assert "John Doe" in content
        assert "123 Main St" in content
        assert "Anytown, TX 12345" in content

    def test_generate_offer_letter_contains_collector_info(self, service, mock_session, mock_client, mock_negotiation):
        """Test letter contains collector information"""
        result = service.generate_offer_letter(
            negotiation_id=1,
            offer_amount=450.00
        )

        content = result["content"]
        assert "Portfolio Recovery Associates" in content
        assert "456 Collection Way" in content

    def test_generate_offer_letter_contains_account_info(self, service, mock_session, mock_client, mock_negotiation):
        """Test letter contains account information"""
        result = service.generate_offer_letter(
            negotiation_id=1,
            offer_amount=450.00
        )

        content = result["content"]
        assert "ACC-12345" in content
        assert "Capital One" in content
        assert "$1,500.00" in content  # Current balance

    def test_generate_offer_letter_contains_settlement_terms(self, service, mock_session, mock_client, mock_negotiation):
        """Test letter contains settlement terms"""
        result = service.generate_offer_letter(
            negotiation_id=1,
            offer_amount=450.00
        )

        content = result["content"]
        assert "$450.00" in content
        assert "30%" in content
        assert "FULL DELETION" in content
        assert "WRITTEN AGREEMENT" in content
        assert "credit bureaus" in content.lower()

    def test_generate_offer_letter_negotiation_not_found(self, mock_session):
        """Test letter generation with invalid negotiation ID"""
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        service = PayForDeleteService(session=mock_session)

        result = service.generate_offer_letter(negotiation_id=999)

        assert "error" in result
        assert result["error"] == "Negotiation not found"

    def test_generate_offer_letter_client_not_found(self, service, mock_session, mock_negotiation):
        """Test letter generation when client not found"""
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_negotiation,
            None  # Client not found
        ]

        result = service.generate_offer_letter(negotiation_id=1)

        assert "error" in result
        assert result["error"] == "Client not found"

    def test_generate_offer_letter_calculates_suggested_amount(self, service, mock_session, mock_client, mock_negotiation):
        """Test letter uses calculated offer when not provided"""
        mock_negotiation.initial_offer_amount = None
        mock_session.query.return_value.filter_by.return_value.first.side_effect = [
            mock_negotiation,
            mock_client
        ]

        result = service.generate_offer_letter(negotiation_id=1)

        # Should suggest 30% of current balance = 450
        assert result["offer_amount"] == 450.00


class TestPayForDeleteServiceContextManager:
    """Test context manager and resource management"""

    def test_context_manager_closes_owned_session(self):
        """Test that context manager closes session when service creates it"""
        with patch('services.pay_for_delete_service.get_db') as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session

            # When no session is provided, service creates one and owns it
            with PayForDeleteService() as service:
                pass

            # Session should be closed when exiting context
            mock_session.close.assert_called_once()

    def test_context_manager_does_not_close_provided_session(self):
        """Test that context manager does NOT close externally provided session"""
        mock_session = MagicMock()

        with PayForDeleteService(session=mock_session) as service:
            pass

        # Session should NOT be closed - caller is responsible
        mock_session.close.assert_not_called()

    def test_close_method_with_owned_session(self):
        """Test explicit close method with owned session"""
        with patch('services.pay_for_delete_service.get_db') as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session

            service = PayForDeleteService()
            service.close()

            mock_session.close.assert_called_once()

    def test_close_method_with_provided_session(self):
        """Test explicit close method does not close provided session"""
        mock_session = MagicMock()
        service = PayForDeleteService(session=mock_session)

        service.close()

        # Provided session should not be closed
        mock_session.close.assert_not_called()

    def test_provided_session_ownership_is_false(self):
        """Test that provided session ownership is tracked correctly"""
        mock_session = MagicMock()

        # When session is provided, service does NOT own it
        service = PayForDeleteService(session=mock_session)
        assert service._owns_session is False

    def test_created_session_ownership_is_true(self):
        """Test that created session ownership is tracked correctly"""
        with patch('services.pay_for_delete_service.get_db') as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session

            # When no session provided, service creates and owns it
            service = PayForDeleteService()
            assert service._owns_session is True


class TestPayForDeleteFactoryFunction:
    """Test factory function"""

    def test_get_pay_for_delete_service_creates_instance(self):
        """Test factory function creates service instance"""
        with patch('services.pay_for_delete_service.get_db') as mock_get_db:
            mock_session = MagicMock()
            mock_get_db.return_value = mock_session

            service = get_pay_for_delete_service()

            assert isinstance(service, PayForDeleteService)

    def test_get_pay_for_delete_service_with_session(self):
        """Test factory function with provided session"""
        mock_session = MagicMock()

        service = get_pay_for_delete_service(session=mock_session)

        assert service.session == mock_session
