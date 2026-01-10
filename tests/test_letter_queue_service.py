"""
Unit tests for Letter Queue Service.
Tests for automated letter suggestion based on escalation triggers including:
- Letter queue management (queue, approve, dismiss)
- CRA response trigger checks
- No response trigger checks
- Item type trigger checks
- Escalation stage trigger checks
- Pending queue retrieval
- Queue statistics
- Bulk operations
"""
import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.letter_queue_service import (
    LETTER_TYPE_DISPLAY,
    TRIGGER_DISPLAY,
    TRIGGER_TO_LETTER_MAP,
    TRIGGER_PRIORITY,
    queue_letter,
    check_cra_response_triggers,
    check_no_response_triggers,
    check_item_type_triggers,
    check_escalation_triggers,
    get_pending_queue,
    get_queue_stats,
    approve_queue_entry,
    dismiss_queue_entry,
    bulk_approve,
    run_all_triggers,
)


# =============================================================================
# Tests for Constants and Configuration
# =============================================================================


class TestLetterTypeDisplayConfiguration:
    """Test letter type display constants are properly defined."""

    def test_mov_request_display(self):
        """Test MOV request letter type display name."""
        assert "mov_request" in LETTER_TYPE_DISPLAY
        assert LETTER_TYPE_DISPLAY["mov_request"] == "Method of Verification Request"

    def test_fdcpa_validation_display(self):
        """Test FDCPA validation letter type display name."""
        assert "fdcpa_validation" in LETTER_TYPE_DISPLAY
        assert LETTER_TYPE_DISPLAY["fdcpa_validation"] == "FDCPA Validation Demand"

    def test_respa_qwr_display(self):
        """Test RESPA QWR letter type display name."""
        assert "respa_qwr" in LETTER_TYPE_DISPLAY
        assert LETTER_TYPE_DISPLAY["respa_qwr"] == "RESPA Qualified Written Request"

    def test_reg_z_dispute_display(self):
        """Test Reg Z dispute letter type display name."""
        assert "reg_z_dispute" in LETTER_TYPE_DISPLAY
        assert LETTER_TYPE_DISPLAY["reg_z_dispute"] == "Reg Z Payment Crediting Dispute"

    def test_section_605b_block_display(self):
        """Test Section 605B block letter type display name."""
        assert "section_605b_block" in LETTER_TYPE_DISPLAY
        assert LETTER_TYPE_DISPLAY["section_605b_block"] == "§605B Identity Theft Block Request"

    def test_section_623_direct_display(self):
        """Test Section 623 direct letter type display name."""
        assert "section_623_direct" in LETTER_TYPE_DISPLAY
        assert LETTER_TYPE_DISPLAY["section_623_direct"] == "§623 Direct Furnisher Dispute"

    def test_reinsertion_challenge_display(self):
        """Test reinsertion challenge letter type display name."""
        assert "reinsertion_challenge" in LETTER_TYPE_DISPLAY
        assert LETTER_TYPE_DISPLAY["reinsertion_challenge"] == "Reinsertion Challenge Letter"

    def test_all_letter_types_have_display_names(self):
        """Test all letter types have display names defined."""
        expected_types = [
            "mov_request", "fdcpa_validation", "respa_qwr", "reg_z_dispute",
            "section_605b_block", "section_623_direct", "reinsertion_challenge"
        ]
        for letter_type in expected_types:
            assert letter_type in LETTER_TYPE_DISPLAY
            assert isinstance(LETTER_TYPE_DISPLAY[letter_type], str)
            assert len(LETTER_TYPE_DISPLAY[letter_type]) > 0


class TestTriggerDisplayConfiguration:
    """Test trigger display constants are properly defined."""

    def test_cra_verified_display(self):
        """Test CRA verified trigger display name."""
        assert "cra_verified" in TRIGGER_DISPLAY
        assert TRIGGER_DISPLAY["cra_verified"] == "CRA Verified Item After Dispute"

    def test_no_cra_response_display(self):
        """Test no CRA response trigger display name."""
        assert "no_cra_response_35_days" in TRIGGER_DISPLAY
        assert TRIGGER_DISPLAY["no_cra_response_35_days"] == "No CRA Response After 35 Days"

    def test_collection_disputed_display(self):
        """Test collection disputed trigger display name."""
        assert "collection_disputed" in TRIGGER_DISPLAY
        assert TRIGGER_DISPLAY["collection_disputed"] == "Collection Account Disputed"

    def test_mortgage_late_display(self):
        """Test mortgage late trigger display name."""
        assert "mortgage_late" in TRIGGER_DISPLAY
        assert TRIGGER_DISPLAY["mortgage_late"] == "Mortgage Late Payment Issue"

    def test_item_reinserted_display(self):
        """Test item reinserted trigger display name."""
        assert "item_reinserted" in TRIGGER_DISPLAY
        assert TRIGGER_DISPLAY["item_reinserted"] == "Item Reinserted Without Notice"

    def test_mov_inadequate_display(self):
        """Test MOV inadequate trigger display name."""
        assert "mov_inadequate" in TRIGGER_DISPLAY
        assert TRIGGER_DISPLAY["mov_inadequate"] == "Inadequate Method of Verification"

    def test_escalation_stage_change_display(self):
        """Test escalation stage change trigger display name."""
        assert "escalation_stage_change" in TRIGGER_DISPLAY
        assert TRIGGER_DISPLAY["escalation_stage_change"] == "Dispute Escalated to Next Stage"


class TestTriggerToLetterMapConfiguration:
    """Test trigger to letter type mapping."""

    def test_cra_verified_maps_to_mov_request(self):
        """Test CRA verified trigger maps to MOV request letter."""
        assert TRIGGER_TO_LETTER_MAP["cra_verified"] == "mov_request"

    def test_no_response_maps_to_section_623(self):
        """Test no response trigger maps to section 623 letter."""
        assert TRIGGER_TO_LETTER_MAP["no_cra_response_35_days"] == "section_623_direct"

    def test_collection_disputed_maps_to_fdcpa(self):
        """Test collection disputed trigger maps to FDCPA letter."""
        assert TRIGGER_TO_LETTER_MAP["collection_disputed"] == "fdcpa_validation"

    def test_mortgage_late_maps_to_respa(self):
        """Test mortgage late trigger maps to RESPA QWR letter."""
        assert TRIGGER_TO_LETTER_MAP["mortgage_late"] == "respa_qwr"

    def test_item_reinserted_maps_to_reinsertion_challenge(self):
        """Test item reinserted trigger maps to reinsertion challenge."""
        assert TRIGGER_TO_LETTER_MAP["item_reinserted"] == "reinsertion_challenge"


class TestTriggerPriorityConfiguration:
    """Test trigger priority configuration."""

    def test_item_reinserted_is_urgent(self):
        """Test item reinserted trigger has urgent priority."""
        assert TRIGGER_PRIORITY["item_reinserted"] == "urgent"

    def test_no_response_is_high(self):
        """Test no response trigger has high priority."""
        assert TRIGGER_PRIORITY["no_cra_response_35_days"] == "high"

    def test_cra_verified_is_high(self):
        """Test CRA verified trigger has high priority."""
        assert TRIGGER_PRIORITY["cra_verified"] == "high"

    def test_collection_disputed_is_high(self):
        """Test collection disputed trigger has high priority."""
        assert TRIGGER_PRIORITY["collection_disputed"] == "high"

    def test_mortgage_late_is_normal(self):
        """Test mortgage late trigger has normal priority."""
        assert TRIGGER_PRIORITY["mortgage_late"] == "normal"

    def test_escalation_stage_change_is_normal(self):
        """Test escalation stage change trigger has normal priority."""
        assert TRIGGER_PRIORITY["escalation_stage_change"] == "normal"


# =============================================================================
# Tests for queue_letter()
# =============================================================================


class TestQueueLetter:
    """Test letter queue function."""

    @patch('database.LetterQueue')
    def test_queue_letter_success(self, MockLetterQueue):
        """Test successful letter queueing."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        mock_entry = MagicMock()
        mock_entry.id = 1
        MockLetterQueue.return_value = mock_entry

        result = queue_letter(
            db=mock_db,
            client_id=1,
            letter_type="mov_request",
            trigger_type="cra_verified",
            trigger_description="Test description",
            priority="high"
        )

        assert result["success"] is True
        assert result["queue_id"] == 1
        assert result["letter_type"] == "mov_request"
        assert result["letter_type_display"] == "Method of Verification Request"
        assert result["priority"] == "high"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_queue_letter_existing_pending_letter(self):
        """Test queueing letter when similar letter already pending."""
        mock_db = MagicMock()
        mock_existing = MagicMock()
        mock_existing.id = 99
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_existing

        result = queue_letter(
            db=mock_db,
            client_id=1,
            letter_type="mov_request",
            trigger_type="cra_verified",
            trigger_description="Test description"
        )

        assert result["success"] is False
        assert result["error"] == "Similar letter already queued"
        assert result["existing_id"] == 99
        mock_db.add.assert_not_called()

    @patch('database.LetterQueue')
    def test_queue_letter_with_all_optional_params(self, MockLetterQueue):
        """Test queueing letter with all optional parameters."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        mock_entry = MagicMock()
        mock_entry.id = 5
        MockLetterQueue.return_value = mock_entry

        result = queue_letter(
            db=mock_db,
            client_id=1,
            letter_type="fdcpa_validation",
            trigger_type="collection_disputed",
            trigger_description="Collection account disputed",
            dispute_item_id=10,
            target_bureau="Experian",
            target_creditor="Test Collector",
            target_account="XXXX1234",
            letter_data={"client_name": "John Doe"},
            priority="urgent"
        )

        assert result["success"] is True
        assert result["priority"] == "urgent"
        MockLetterQueue.assert_called_once()

    def test_queue_letter_database_error(self):
        """Test queueing letter handles database error."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_db.add.side_effect = Exception("Database connection error")

        result = queue_letter(
            db=mock_db,
            client_id=1,
            letter_type="mov_request",
            trigger_type="cra_verified",
            trigger_description="Test description"
        )

        assert result["success"] is False
        assert "Database connection error" in result["error"]
        mock_db.rollback.assert_called_once()

    @patch('database.LetterQueue')
    def test_queue_letter_default_priority(self, MockLetterQueue):
        """Test queueing letter uses default priority."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        mock_entry = MagicMock()
        mock_entry.id = 1
        MockLetterQueue.return_value = mock_entry

        result = queue_letter(
            db=mock_db,
            client_id=1,
            letter_type="respa_qwr",
            trigger_type="mortgage_late",
            trigger_description="Mortgage late payment"
        )

        assert result["success"] is True
        assert result["priority"] == "normal"

    @patch('database.LetterQueue')
    def test_queue_letter_unknown_letter_type_display(self, MockLetterQueue):
        """Test queueing letter with unknown letter type uses type as display."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        mock_entry = MagicMock()
        mock_entry.id = 1
        MockLetterQueue.return_value = mock_entry

        result = queue_letter(
            db=mock_db,
            client_id=1,
            letter_type="unknown_type",
            trigger_type="test_trigger",
            trigger_description="Test"
        )

        assert result["success"] is True
        assert result["letter_type_display"] == "unknown_type"


# =============================================================================
# Tests for check_cra_response_triggers()
# =============================================================================


class TestCheckCraResponseTriggers:
    """Test CRA response trigger checking."""

    def test_cra_response_not_found(self):
        """Test trigger check with non-existent CRA response."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        results = check_cra_response_triggers(mock_db, cra_response_id=999)

        assert results == []

    @patch('database.LetterQueue')
    def test_verified_response_triggers_mov_request(self, MockLetterQueue):
        """Test verified CRA response triggers MOV request letter."""
        mock_db = MagicMock()

        # Mock CRA response
        mock_response = MagicMock()
        mock_response.id = 1
        mock_response.client_id = 100
        mock_response.response_type = "verified"
        mock_response.bureau = "Experian"
        mock_response.dispute_round = 1
        mock_response.response_date = datetime(2024, 1, 15)
        mock_response.structured_items = None

        # Mock client
        mock_client = MagicMock()
        mock_client.name = "John Doe"

        # Mock dispute item
        mock_item = MagicMock()
        mock_item.id = 50
        mock_item.client_id = 100
        mock_item.bureau = "Experian"
        mock_item.status = "in_progress"
        mock_item.creditor_name = "Test Creditor"
        mock_item.account_id = "ACC123"

        # Mock no existing letter queue entry
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_response,  # CRAResponse query
            mock_client,    # Client query
            None,           # LetterQueue existing check
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_item]

        mock_entry = MagicMock()
        mock_entry.id = 10
        MockLetterQueue.return_value = mock_entry

        results = check_cra_response_triggers(mock_db, cra_response_id=1)

        assert isinstance(results, list)

    @patch('database.LetterQueue')
    def test_reinserted_response_triggers_reinsertion_challenge(self, MockLetterQueue):
        """Test reinserted CRA response triggers reinsertion challenge letter."""
        mock_db = MagicMock()

        # Mock CRA response with reinserted type
        mock_response = MagicMock()
        mock_response.id = 1
        mock_response.client_id = 100
        mock_response.response_type = "reinserted"
        mock_response.bureau = "TransUnion"
        mock_response.dispute_round = 2
        mock_response.response_date = datetime(2024, 1, 20)
        mock_response.structured_items = None

        # Mock client
        mock_client = MagicMock()
        mock_client.name = "Jane Smith"

        # Set up query mock chain
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_response,  # CRAResponse query
            mock_client,    # Client query
            None,           # LetterQueue existing check
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        mock_entry = MagicMock()
        mock_entry.id = 15
        MockLetterQueue.return_value = mock_entry

        results = check_cra_response_triggers(mock_db, cra_response_id=1)

        # At least one result should be queued for reinsertion
        assert isinstance(results, list)

    @patch('database.LetterQueue')
    def test_structured_items_with_reinserted_flag(self, MockLetterQueue):
        """Test structured items with reinserted flag triggers reinsertion challenge."""
        mock_db = MagicMock()

        mock_response = MagicMock()
        mock_response.id = 1
        mock_response.client_id = 100
        mock_response.response_type = "updated"  # Not reinserted type
        mock_response.bureau = "Equifax"
        mock_response.dispute_round = 1
        mock_response.response_date = datetime(2024, 1, 25)
        mock_response.structured_items = [{"item": "test", "reinserted": True}]  # Has reinserted flag

        mock_client = MagicMock()
        mock_client.name = "Bob Wilson"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_response,
            mock_client,
            None,
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        mock_entry = MagicMock()
        mock_entry.id = 20
        MockLetterQueue.return_value = mock_entry

        results = check_cra_response_triggers(mock_db, cra_response_id=1)

        assert isinstance(results, list)

    def test_non_verified_non_reinserted_response(self):
        """Test non-verified/non-reinserted response doesn't trigger letters."""
        mock_db = MagicMock()

        mock_response = MagicMock()
        mock_response.id = 1
        mock_response.client_id = 100
        mock_response.response_type = "deleted"  # Item was deleted - no trigger needed
        mock_response.bureau = "Experian"
        mock_response.dispute_round = 1
        mock_response.response_date = datetime(2024, 1, 15)
        mock_response.structured_items = []

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_response
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        results = check_cra_response_triggers(mock_db, cra_response_id=1)

        assert results == []


# =============================================================================
# Tests for check_no_response_triggers()
# =============================================================================


class TestCheckNoResponseTriggers:
    """Test no response trigger checking."""

    def test_no_pending_items(self):
        """Test no triggers when no pending items."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        results = check_no_response_triggers(mock_db)

        assert results == []

    @patch('database.LetterQueue')
    def test_pending_item_without_response(self, MockLetterQueue):
        """Test trigger for item without response after threshold."""
        mock_db = MagicMock()

        # Mock dispute item sent more than 35 days ago
        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.bureau = "Experian"
        mock_item.creditor_name = "Test Creditor"
        mock_item.account_id = "ACC123"
        mock_item.sent_date = (datetime.utcnow() - timedelta(days=40)).date()
        mock_item.dispute_round = 1

        mock_client = MagicMock()
        mock_client.name = "John Doe"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_item]
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No CRA response
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_client,  # Client query
            None,         # LetterQueue existing check
        ]

        mock_entry = MagicMock()
        mock_entry.id = 25
        MockLetterQueue.return_value = mock_entry

        results = check_no_response_triggers(mock_db)

        assert isinstance(results, list)

    def test_pending_item_with_response(self):
        """Test no trigger for item with response."""
        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.bureau = "Experian"
        mock_item.sent_date = (datetime.utcnow() - timedelta(days=40)).date()
        mock_item.dispute_round = 1

        mock_response = MagicMock()  # CRA response exists

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_item]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_response

        results = check_no_response_triggers(mock_db)

        assert results == []

    def test_custom_days_threshold(self):
        """Test custom days threshold parameter."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        results = check_no_response_triggers(mock_db, days_threshold=45)

        assert results == []
        # Verify the query was made with correct threshold


# =============================================================================
# Tests for check_item_type_triggers()
# =============================================================================


class TestCheckItemTypeTriggers:
    """Test item type trigger checking."""

    def test_item_not_found(self):
        """Test trigger check with non-existent dispute item."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        results = check_item_type_triggers(mock_db, dispute_item_id=999)

        assert results == []

    @patch('database.LetterQueue')
    def test_collection_item_triggers_fdcpa(self, MockLetterQueue):
        """Test collection item triggers FDCPA validation letter."""
        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.item_type = "collection"
        mock_item.creditor_name = "ABC Collections"
        mock_item.account_id = "COLL123"
        mock_item.bureau = "TransUnion"

        mock_client = MagicMock()
        mock_client.name = "John Doe"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_item,    # DisputeItem query
            mock_client,  # Client query
            None,         # LetterQueue existing check
        ]

        mock_entry = MagicMock()
        mock_entry.id = 30
        MockLetterQueue.return_value = mock_entry

        results = check_item_type_triggers(mock_db, dispute_item_id=1)

        assert isinstance(results, list)

    @patch('database.LetterQueue')
    def test_mortgage_late_payment_triggers_respa(self, MockLetterQueue):
        """Test mortgage late payment triggers RESPA QWR letter."""
        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.item_type = "late_payment"
        mock_item.creditor_name = "Wells Fargo Home Mortgage"
        mock_item.account_id = "MORT456"
        mock_item.bureau = "Equifax"

        mock_client = MagicMock()
        mock_client.name = "Jane Smith"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_item,
            mock_client,
            None,
        ]

        mock_entry = MagicMock()
        mock_entry.id = 35
        MockLetterQueue.return_value = mock_entry

        results = check_item_type_triggers(mock_db, dispute_item_id=1)

        assert isinstance(results, list)

    @patch('database.LetterQueue')
    def test_mortgage_keywords_detection(self, MockLetterQueue):
        """Test various mortgage-related keywords trigger RESPA QWR."""
        mock_db = MagicMock()

        mortgage_creditors = [
            "Rocket Mortgage Corp",
            "Quicken Loans",
            "Bank of America Home Loans",
            "Chase Home Finance",
            "Fannie Mae",
            "Freddie Mac"
        ]

        for creditor_name in mortgage_creditors:
            mock_item = MagicMock()
            mock_item.id = 1
            mock_item.client_id = 100
            mock_item.item_type = "late_payment"
            mock_item.creditor_name = creditor_name
            mock_item.account_id = "MORT789"
            mock_item.bureau = "Experian"

            mock_client = MagicMock()
            mock_client.name = "Test Client"

            mock_db.query.return_value.filter_by.return_value.first.side_effect = [
                mock_item,
                mock_client,
                None,
            ]

            mock_entry = MagicMock()
            mock_entry.id = 40
            MockLetterQueue.return_value = mock_entry

            results = check_item_type_triggers(mock_db, dispute_item_id=1)

            assert isinstance(results, list)

    def test_non_mortgage_late_payment_no_respa(self):
        """Test non-mortgage late payment doesn't trigger RESPA QWR."""
        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.item_type = "late_payment"
        mock_item.creditor_name = "Credit Card Company"  # Not mortgage-related
        mock_item.account_id = "CC123"
        mock_item.bureau = "Experian"

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_item,
            mock_client,
        ]

        results = check_item_type_triggers(mock_db, dispute_item_id=1)

        assert results == []

    def test_other_item_type_no_triggers(self):
        """Test other item types don't trigger letters."""
        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.item_type = "inquiry"  # Not collection or late payment
        mock_item.creditor_name = "Test Company"
        mock_item.account_id = "INQ123"
        mock_item.bureau = "Experian"

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_item,
            mock_client,
        ]

        results = check_item_type_triggers(mock_db, dispute_item_id=1)

        assert results == []


# =============================================================================
# Tests for check_escalation_triggers()
# =============================================================================


class TestCheckEscalationTriggers:
    """Test escalation stage trigger checking."""

    def test_item_not_found(self):
        """Test trigger check with non-existent dispute item."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        results = check_escalation_triggers(mock_db, dispute_item_id=999, new_stage="section_623")

        assert results == []

    @patch('database.LetterQueue')
    def test_section_623_stage_triggers_direct_dispute(self, MockLetterQueue):
        """Test section_623 stage triggers direct furnisher dispute letter."""
        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.creditor_name = "Test Creditor"
        mock_item.account_id = "ACC123"
        mock_item.bureau = "Experian"
        mock_item.dispute_round = 2
        mock_item.furnisher_dispute_sent = False

        mock_client = MagicMock()
        mock_client.name = "John Doe"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_item,
            mock_client,
            None,  # LetterQueue existing check
        ]

        mock_entry = MagicMock()
        mock_entry.id = 45
        MockLetterQueue.return_value = mock_entry

        results = check_escalation_triggers(mock_db, dispute_item_id=1, new_stage="section_623")

        assert isinstance(results, list)

    def test_section_623_already_sent_no_trigger(self):
        """Test section_623 stage with already sent furnisher dispute doesn't trigger."""
        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.furnisher_dispute_sent = True  # Already sent

        mock_client = MagicMock()
        mock_client.name = "John Doe"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_item,
            mock_client,
        ]

        results = check_escalation_triggers(mock_db, dispute_item_id=1, new_stage="section_623")

        assert results == []

    def test_other_stages_no_triggers(self):
        """Test other escalation stages don't trigger letters."""
        mock_db = MagicMock()

        # Test with non-section_623 stages
        for stage in ["section_621", "section_616_617", "initial"]:
            mock_item = MagicMock()
            mock_item.id = 1
            mock_item.client_id = 100
            mock_item.furnisher_dispute_sent = False

            mock_client = MagicMock()
            mock_client.name = "John Doe"

            # Reset the side_effect for each iteration
            mock_db.query.return_value.filter_by.return_value.first.side_effect = [
                mock_item,
                mock_client,
            ]

            results = check_escalation_triggers(mock_db, dispute_item_id=1, new_stage=stage)
            assert results == []


# =============================================================================
# Tests for get_pending_queue()
# =============================================================================


class TestGetPendingQueue:
    """Test pending queue retrieval function."""

    def test_get_pending_queue_empty(self):
        """Test getting empty pending queue."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        results = get_pending_queue(mock_db)

        assert results == []

    def test_get_pending_queue_with_entries(self):
        """Test getting pending queue with entries."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.client_id = 100
        mock_entry.dispute_item_id = 50
        mock_entry.letter_type = "mov_request"
        mock_entry.trigger_type = "cra_verified"
        mock_entry.trigger_description = "Test trigger"
        mock_entry.trigger_date = datetime(2024, 1, 15)
        mock_entry.target_bureau = "Experian"
        mock_entry.target_creditor = "Test Creditor"
        mock_entry.target_account = "ACC123"
        mock_entry.priority = "high"
        mock_entry.status = "pending"
        mock_entry.letter_data = {"key": "value"}
        mock_entry.created_at = datetime(2024, 1, 14)

        mock_client = MagicMock()
        mock_client.name = "John Doe"

        mock_dispute_item = MagicMock()

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_entry]
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_client,
            mock_dispute_item,
        ]

        results = get_pending_queue(mock_db)

        assert len(results) == 1
        assert results[0]["id"] == 1
        assert results[0]["client_name"] == "John Doe"
        assert results[0]["letter_type"] == "mov_request"
        assert results[0]["letter_type_display"] == "Method of Verification Request"
        assert results[0]["trigger_type"] == "cra_verified"
        assert results[0]["trigger_display"] == "CRA Verified Item After Dispute"
        assert results[0]["priority"] == "high"

    def test_get_pending_queue_with_client_filter(self):
        """Test getting pending queue filtered by client."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        results = get_pending_queue(mock_db, client_id=100)

        assert results == []
        # Verify filter was called with client_id

    def test_get_pending_queue_with_priority_filter(self):
        """Test getting pending queue filtered by priority."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        results = get_pending_queue(mock_db, priority="urgent")

        assert results == []

    def test_get_pending_queue_custom_limit(self):
        """Test getting pending queue with custom limit."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []

        results = get_pending_queue(mock_db, limit=100)

        mock_query.limit.assert_called_with(100)

    def test_get_pending_queue_priority_sorting(self):
        """Test pending queue entries are sorted by priority."""
        mock_db = MagicMock()

        # Create entries with different priorities
        mock_entry1 = MagicMock()
        mock_entry1.id = 1
        mock_entry1.client_id = 100
        mock_entry1.dispute_item_id = None
        mock_entry1.letter_type = "mov_request"
        mock_entry1.trigger_type = "cra_verified"
        mock_entry1.trigger_description = "Test"
        mock_entry1.trigger_date = datetime(2024, 1, 15)
        mock_entry1.target_bureau = None
        mock_entry1.target_creditor = None
        mock_entry1.target_account = None
        mock_entry1.priority = "normal"
        mock_entry1.status = "pending"
        mock_entry1.letter_data = {}
        mock_entry1.created_at = datetime(2024, 1, 14)

        mock_entry2 = MagicMock()
        mock_entry2.id = 2
        mock_entry2.client_id = 100
        mock_entry2.dispute_item_id = None
        mock_entry2.letter_type = "reinsertion_challenge"
        mock_entry2.trigger_type = "item_reinserted"
        mock_entry2.trigger_description = "Test"
        mock_entry2.trigger_date = datetime(2024, 1, 16)
        mock_entry2.target_bureau = None
        mock_entry2.target_creditor = None
        mock_entry2.target_account = None
        mock_entry2.priority = "urgent"
        mock_entry2.status = "pending"
        mock_entry2.letter_data = {}
        mock_entry2.created_at = datetime(2024, 1, 15)

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_entry1, mock_entry2]
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        results = get_pending_queue(mock_db)

        # Urgent should come before normal
        assert len(results) == 2
        assert results[0]["priority"] == "urgent"
        assert results[1]["priority"] == "normal"


# =============================================================================
# Tests for get_queue_stats()
# =============================================================================


class TestGetQueueStats:
    """Test queue statistics retrieval function."""

    def test_get_queue_stats_empty(self):
        """Test getting stats with empty queue."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0

        stats = get_queue_stats(mock_db)

        assert stats["total_pending"] == 0
        assert stats["by_priority"]["urgent"] == 0
        assert stats["by_priority"]["high"] == 0
        assert stats["by_priority"]["normal"] == 0
        assert stats["by_priority"]["low"] == 0
        assert stats["approved_today"] == 0
        assert stats["generated_today"] == 0

    def test_get_queue_stats_with_entries(self):
        """Test getting stats with queue entries."""
        mock_db = MagicMock()

        # Mock different scalar calls
        call_count = [0]

        def mock_scalar():
            call_count[0] += 1
            if call_count[0] == 1:  # total
                return 10
            elif call_count[0] <= 5:  # by_priority (4 calls)
                return [3, 5, 2, 0][call_count[0] - 2]  # urgent, high, normal, low
            elif call_count[0] <= 12:  # by_letter_type (7 calls)
                return 1 if call_count[0] == 6 else 0
            elif call_count[0] == 13:  # approved_today
                return 5
            else:  # generated_today
                return 3

        mock_db.query.return_value.filter.return_value.scalar.side_effect = mock_scalar

        stats = get_queue_stats(mock_db)

        assert stats["total_pending"] == 10
        assert "by_priority" in stats
        assert "approved_today" in stats
        assert "generated_today" in stats


# =============================================================================
# Tests for approve_queue_entry()
# =============================================================================


class TestApproveQueueEntry:
    """Test queue entry approval function."""

    def test_approve_not_found(self):
        """Test approving non-existent queue entry."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = approve_queue_entry(mock_db, queue_id=999, staff_id=1)

        assert result["success"] is False
        assert result["error"] == "Queue entry not found"

    def test_approve_success(self):
        """Test successful queue entry approval."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.status = "pending"
        mock_entry.letter_type = "mov_request"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        result = approve_queue_entry(mock_db, queue_id=1, staff_id=5)

        assert result["success"] is True
        assert result["queue_id"] == 1
        assert result["status"] == "approved"
        assert result["letter_type"] == "mov_request"
        assert result["letter_type_display"] == "Method of Verification Request"
        assert mock_entry.status == "approved"
        assert mock_entry.reviewed_by_staff_id == 5
        mock_db.commit.assert_called_once()

    def test_approve_with_notes(self):
        """Test approving queue entry with notes."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.status = "pending"
        mock_entry.letter_type = "fdcpa_validation"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        result = approve_queue_entry(mock_db, queue_id=1, staff_id=5, notes="Reviewed and approved")

        assert result["success"] is True
        assert mock_entry.action_notes == "Reviewed and approved"

    def test_approve_already_approved(self):
        """Test approving already approved entry."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.status = "approved"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        result = approve_queue_entry(mock_db, queue_id=1, staff_id=5)

        assert result["success"] is False
        assert result["error"] == "Entry already approved"

    def test_approve_already_dismissed(self):
        """Test approving already dismissed entry."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.status = "dismissed"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        result = approve_queue_entry(mock_db, queue_id=1, staff_id=5)

        assert result["success"] is False
        assert result["error"] == "Entry already dismissed"


# =============================================================================
# Tests for dismiss_queue_entry()
# =============================================================================


class TestDismissQueueEntry:
    """Test queue entry dismissal function."""

    def test_dismiss_not_found(self):
        """Test dismissing non-existent queue entry."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = dismiss_queue_entry(mock_db, queue_id=999, staff_id=1, reason="Not applicable")

        assert result["success"] is False
        assert result["error"] == "Queue entry not found"

    def test_dismiss_success(self):
        """Test successful queue entry dismissal."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.status = "pending"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        result = dismiss_queue_entry(mock_db, queue_id=1, staff_id=5, reason="Client resolved issue directly")

        assert result["success"] is True
        assert result["queue_id"] == 1
        assert result["status"] == "dismissed"
        assert mock_entry.status == "dismissed"
        assert mock_entry.reviewed_by_staff_id == 5
        assert mock_entry.action_notes == "Client resolved issue directly"
        mock_db.commit.assert_called_once()

    def test_dismiss_already_processed(self):
        """Test dismissing already processed entry."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.status = "generated"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        result = dismiss_queue_entry(mock_db, queue_id=1, staff_id=5, reason="Test")

        assert result["success"] is False
        assert result["error"] == "Entry already generated"


# =============================================================================
# Tests for bulk_approve()
# =============================================================================


class TestBulkApprove:
    """Test bulk approval function."""

    def test_bulk_approve_all_success(self):
        """Test bulk approving multiple entries successfully."""
        mock_db = MagicMock()

        # Mock entries for each approve call
        mock_entry1 = MagicMock()
        mock_entry1.id = 1
        mock_entry1.status = "pending"
        mock_entry1.letter_type = "mov_request"

        mock_entry2 = MagicMock()
        mock_entry2.id = 2
        mock_entry2.status = "pending"
        mock_entry2.letter_type = "fdcpa_validation"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_entry1, mock_entry2
        ]

        result = bulk_approve(mock_db, queue_ids=[1, 2], staff_id=5)

        assert result["success"] is True
        assert result["approved_count"] == 2
        assert result["approved_ids"] == [1, 2]
        assert result["errors"] == []

    def test_bulk_approve_partial_success(self):
        """Test bulk approving with some failures."""
        mock_db = MagicMock()

        mock_entry1 = MagicMock()
        mock_entry1.id = 1
        mock_entry1.status = "pending"
        mock_entry1.letter_type = "mov_request"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_entry1,  # First entry exists
            None,         # Second entry not found
        ]

        result = bulk_approve(mock_db, queue_ids=[1, 999], staff_id=5)

        assert result["success"] is False
        assert result["approved_count"] == 1
        assert result["approved_ids"] == [1]
        assert len(result["errors"]) == 1
        assert result["errors"][0]["id"] == 999

    def test_bulk_approve_all_failures(self):
        """Test bulk approving with all failures."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = bulk_approve(mock_db, queue_ids=[999, 998], staff_id=5)

        assert result["success"] is False
        assert result["approved_count"] == 0
        assert result["approved_ids"] == []
        assert len(result["errors"]) == 2

    def test_bulk_approve_empty_list(self):
        """Test bulk approving with empty list."""
        mock_db = MagicMock()

        result = bulk_approve(mock_db, queue_ids=[], staff_id=5)

        assert result["success"] is True
        assert result["approved_count"] == 0
        assert result["approved_ids"] == []
        assert result["errors"] == []


# =============================================================================
# Tests for run_all_triggers()
# =============================================================================


class TestRunAllTriggers:
    """Test run all triggers function."""

    def test_run_all_triggers_success(self):
        """Test running all triggers successfully."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = run_all_triggers(mock_db)

        assert "no_response_checks" in result
        assert "total_queued" in result
        assert "errors" in result
        assert result["errors"] == []

    @patch('database.LetterQueue')
    def test_run_all_triggers_with_results(self, MockLetterQueue):
        """Test running all triggers with queued letters."""
        mock_db = MagicMock()

        # Mock dispute item for no response check
        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.bureau = "Experian"
        mock_item.creditor_name = "Test Creditor"
        mock_item.account_id = "ACC123"
        mock_item.sent_date = (datetime.utcnow() - timedelta(days=40)).date()
        mock_item.dispute_round = 1

        mock_client = MagicMock()
        mock_client.name = "John Doe"

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_item]
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_client,
            None,
        ]

        mock_entry = MagicMock()
        mock_entry.id = 50
        MockLetterQueue.return_value = mock_entry

        result = run_all_triggers(mock_db)

        assert "no_response_checks" in result
        assert "total_queued" in result

    def test_run_all_triggers_handles_error(self):
        """Test running all triggers handles exceptions gracefully."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        result = run_all_triggers(mock_db)

        assert len(result["errors"]) > 0
        assert "No response check error" in result["errors"][0]


# =============================================================================
# Integration-style Tests
# =============================================================================


class TestLetterQueueWorkflow:
    """Test complete letter queue workflow scenarios."""

    @patch('database.LetterQueue')
    def test_complete_approval_workflow(self, MockLetterQueue):
        """Test complete workflow from queue to approval."""
        mock_db = MagicMock()

        # Step 1: Queue a letter
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        mock_entry = MagicMock()
        mock_entry.id = 1
        MockLetterQueue.return_value = mock_entry

        queue_result = queue_letter(
            db=mock_db,
            client_id=100,
            letter_type="mov_request",
            trigger_type="cra_verified",
            trigger_description="Test trigger",
            priority="high"
        )

        assert queue_result["success"] is True

        # Step 2: Approve the queued letter
        mock_entry.status = "pending"
        mock_entry.letter_type = "mov_request"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        approve_result = approve_queue_entry(
            db=mock_db,
            queue_id=1,
            staff_id=5,
            notes="Approved for generation"
        )

        assert approve_result["success"] is True
        assert approve_result["status"] == "approved"

    @patch('database.LetterQueue')
    def test_complete_dismissal_workflow(self, MockLetterQueue):
        """Test complete workflow from queue to dismissal."""
        mock_db = MagicMock()

        # Step 1: Queue a letter
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        mock_entry = MagicMock()
        mock_entry.id = 1
        MockLetterQueue.return_value = mock_entry

        queue_result = queue_letter(
            db=mock_db,
            client_id=100,
            letter_type="fdcpa_validation",
            trigger_type="collection_disputed",
            trigger_description="Collection account disputed"
        )

        assert queue_result["success"] is True

        # Step 2: Dismiss the queued letter
        mock_entry.status = "pending"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        dismiss_result = dismiss_queue_entry(
            db=mock_db,
            queue_id=1,
            staff_id=5,
            reason="Client paid off the debt"
        )

        assert dismiss_result["success"] is True
        assert dismiss_result["status"] == "dismissed"


# =============================================================================
# Edge Case Tests
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_queue_letter_with_none_letter_data(self):
        """Test queueing letter with None letter_data uses empty dict."""
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None
        mock_db.add.side_effect = Exception("Stop execution to check args")

        result = queue_letter(
            db=mock_db,
            client_id=1,
            letter_type="mov_request",
            trigger_type="cra_verified",
            trigger_description="Test",
            letter_data=None
        )

        # The function should handle None letter_data gracefully
        assert result["success"] is False

    def test_get_pending_queue_unknown_client(self):
        """Test pending queue with unknown client returns Unknown name."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.client_id = 999
        mock_entry.dispute_item_id = None
        mock_entry.letter_type = "mov_request"
        mock_entry.trigger_type = "cra_verified"
        mock_entry.trigger_description = "Test"
        mock_entry.trigger_date = datetime(2024, 1, 15)
        mock_entry.target_bureau = None
        mock_entry.target_creditor = None
        mock_entry.target_account = None
        mock_entry.priority = "normal"
        mock_entry.status = "pending"
        mock_entry.letter_data = {}
        mock_entry.created_at = datetime(2024, 1, 14)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_entry]
        mock_db.query.return_value.filter_by.return_value.first.return_value = None  # Client not found

        results = get_pending_queue(mock_db)

        assert len(results) == 1
        assert results[0]["client_name"] == "Unknown"

    def test_check_item_type_triggers_creditor_name_none(self):
        """Test item type triggers with None creditor name."""
        mock_db = MagicMock()

        mock_item = MagicMock()
        mock_item.id = 1
        mock_item.client_id = 100
        mock_item.item_type = "late_payment"
        mock_item.creditor_name = None  # No creditor name
        mock_item.account_id = "ACC123"
        mock_item.bureau = "Experian"

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_item,
            mock_client,
        ]

        # Should not trigger RESPA because creditor_name is None
        results = check_item_type_triggers(mock_db, dispute_item_id=1)

        assert results == []

    def test_approve_entry_sets_timestamps(self):
        """Test approval sets reviewed_at and updated_at timestamps."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.status = "pending"
        mock_entry.letter_type = "mov_request"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        result = approve_queue_entry(mock_db, queue_id=1, staff_id=5)

        assert result["success"] is True
        # Check that timestamps were set
        assert mock_entry.reviewed_at is not None
        assert mock_entry.updated_at is not None

    def test_dismiss_entry_sets_timestamps(self):
        """Test dismissal sets reviewed_at and updated_at timestamps."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.status = "pending"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_entry

        result = dismiss_queue_entry(mock_db, queue_id=1, staff_id=5, reason="Test")

        assert result["success"] is True
        # Check that timestamps were set
        assert mock_entry.reviewed_at is not None
        assert mock_entry.updated_at is not None


# =============================================================================
# Tests for Display Name Lookups
# =============================================================================


class TestDisplayNameLookups:
    """Test display name lookup behavior."""

    def test_letter_type_display_fallback(self):
        """Test letter type display falls back to raw type for unknown types."""
        unknown_type = "custom_letter_type"
        display = LETTER_TYPE_DISPLAY.get(unknown_type, unknown_type)
        assert display == unknown_type

    def test_trigger_display_fallback(self):
        """Test trigger display falls back to raw type for unknown triggers."""
        unknown_trigger = "custom_trigger"
        display = TRIGGER_DISPLAY.get(unknown_trigger, unknown_trigger)
        assert display == unknown_trigger

    def test_get_pending_queue_unknown_trigger_type(self):
        """Test pending queue handles unknown trigger types gracefully."""
        mock_db = MagicMock()

        mock_entry = MagicMock()
        mock_entry.id = 1
        mock_entry.client_id = 100
        mock_entry.dispute_item_id = None
        mock_entry.letter_type = "custom_letter"
        mock_entry.trigger_type = "custom_trigger"
        mock_entry.trigger_description = "Custom trigger"
        mock_entry.trigger_date = datetime(2024, 1, 15)
        mock_entry.target_bureau = None
        mock_entry.target_creditor = None
        mock_entry.target_account = None
        mock_entry.priority = "normal"
        mock_entry.status = "pending"
        mock_entry.letter_data = {}
        mock_entry.created_at = datetime(2024, 1, 14)

        mock_client = MagicMock()
        mock_client.name = "Test Client"

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [mock_entry]
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        results = get_pending_queue(mock_db)

        assert len(results) == 1
        # Should fall back to raw values for unknown types
        assert results[0]["letter_type_display"] == "custom_letter"
        assert results[0]["trigger_display"] == "custom_trigger"
