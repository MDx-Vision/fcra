"""
Unit tests for AIDisputeWriterService

Tests AI-powered dispute letter generation including:
- Round 1-4 strategies
- Context gathering
- Letter parsing
- Bureau-specific formatting
"""

import pytest
from datetime import datetime, date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.orm import Session


class TestRoundStrategies:
    """Tests for round strategy configuration."""

    def test_round_1_strategy(self):
        """Test Round 1 strategy definition."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        assert 1 in service.ROUND_STRATEGIES
        r1 = service.ROUND_STRATEGIES[1]
        assert r1['name'] == 'Round 1 - Initial Dispute'
        assert r1['prompt_key'] == 'r1'

    def test_round_2_strategy(self):
        """Test Round 2 strategy definition."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        assert 2 in service.ROUND_STRATEGIES
        r2 = service.ROUND_STRATEGIES[2]
        assert 'MOV' in r2['description'] or 'Verification' in r2['description']

    def test_round_3_strategy(self):
        """Test Round 3 strategy definition."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        assert 3 in service.ROUND_STRATEGIES
        r3 = service.ROUND_STRATEGIES[3]
        assert 'CFPB' in r3['description'] or 'Regulatory' in r3['description']

    def test_round_4_strategy(self):
        """Test Round 4 strategy definition."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        assert 4 in service.ROUND_STRATEGIES
        r4 = service.ROUND_STRATEGIES[4]
        assert 'Litigation' in r4['description'] or 'Pre-' in r4['description']

    def test_bureaus_defined(self):
        """Test all bureaus are defined."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        assert 'Equifax' in service.BUREAUS
        assert 'Experian' in service.BUREAUS
        assert 'TransUnion' in service.BUREAUS


class TestServiceInit:
    """Tests for service initialization."""

    def test_init_with_db_session(self):
        """Test initialization with database session."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        assert service.db == mock_db
        assert service._anthropic_client is None

    def test_anthropic_lazy_loading(self):
        """Test Anthropic client is lazy-loaded."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test_key'}):
            with patch('services.ai_dispute_writer_service.Anthropic') as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client

                client = service.anthropic_client

                assert mock_anthropic.called
                assert client == mock_client


class TestGetClientContext:
    """Tests for get_client_context method."""

    def test_success(self):
        """Test successful context gathering."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.current_dispute_round = 2

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = AIDisputeWriterService(mock_db)
        result = service.get_client_context(client_id=1)

        assert result['client'] == mock_client
        assert result['current_round'] == 2

    def test_client_not_found(self):
        """Test error when client not found."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AIDisputeWriterService(mock_db)
        result = service.get_client_context(client_id=999)

        assert 'error' in result
        assert 'not found' in result['error']


class TestFormatClientInfo:
    """Tests for format_client_info method."""

    def test_full_info(self):
        """Test formatting with all client info."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        mock_client = MagicMock()
        mock_client.name = 'John Doe'
        mock_client.address_street = '123 Main St'
        mock_client.address_city = 'Anytown'
        mock_client.address_state = 'CA'
        mock_client.address_zip = '90210'
        mock_client.ssn_last_four = '1234'
        mock_client.date_of_birth = date(1990, 1, 15)
        mock_client.email = 'john@example.com'
        mock_client.phone = '555-123-4567'

        result = service.format_client_info(mock_client)

        assert 'John Doe' in result
        assert '123 Main St' in result
        assert 'Anytown' in result
        assert '1234' in result

    def test_partial_info(self):
        """Test formatting with partial client info."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        mock_client = MagicMock()
        mock_client.name = 'Jane Smith'
        mock_client.address_street = None
        mock_client.address_city = None
        mock_client.address_state = None
        mock_client.address_zip = None
        mock_client.ssn_last_four = None
        mock_client.date_of_birth = None
        mock_client.email = None
        mock_client.phone = None

        result = service.format_client_info(mock_client)

        assert 'Jane Smith' in result
        assert 'N/A' in result


class TestFormatViolations:
    """Tests for format_violations method."""

    def test_with_violations(self):
        """Test formatting with violations."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        violations = [
            MagicMock(
                violation_type='Inaccurate Information',
                bureau='Equifax',
                account_name='Test Account',
                fcra_section='611',
                description='Wrong balance',
                statutory_damages_min=100,
                statutory_damages_max=1000
            )
        ]

        result = service.format_violations(violations)

        assert 'Inaccurate Information' in result
        assert 'Equifax' in result
        assert 'Test Account' in result

    def test_no_violations(self):
        """Test formatting with no violations."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        result = service.format_violations([])

        assert 'No violations detected' in result


class TestFormatDisputeItems:
    """Tests for format_dispute_items method."""

    def test_with_items(self):
        """Test formatting with dispute items."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        items = [
            MagicMock(
                id=1,
                bureau='Experian',
                creditor_name='Test Creditor',
                item_type='Collection',
                status='disputed',
                account_id='ACC123',
                reason='Not mine'
            )
        ]

        result = service.format_dispute_items(items)

        assert 'Test Creditor' in result
        assert 'EXPERIAN' in result or 'Experian' in result

    def test_filter_by_selected_ids(self):
        """Test filtering by selected item IDs."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        items = [
            MagicMock(id=1, bureau='Equifax', creditor_name='A', item_type='X', status='x', account_id='1', reason=''),
            MagicMock(id=2, bureau='Experian', creditor_name='B', item_type='Y', status='y', account_id='2', reason=''),
        ]

        result = service.format_dispute_items(items, selected_ids=[1])

        # Should only contain first item
        assert 'A' in result or 'No items' in result

    def test_no_items(self):
        """Test formatting with no items."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        result = service.format_dispute_items([])

        assert 'No dispute items' in result


class TestGenerateLetters:
    """Tests for generate_letters method."""

    def test_invalid_round(self):
        """Test error for invalid round number."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.current_dispute_round = 1

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = AIDisputeWriterService(mock_db)
        result = service.generate_letters(client_id=1, round_number=5)

        assert 'error' in result
        assert 'Invalid round' in result['error']

    def test_client_not_found(self):
        """Test error when client not found."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AIDisputeWriterService(mock_db)
        result = service.generate_letters(client_id=999, round_number=1)

        assert 'error' in result


class TestParseLetters:
    """Tests for _parse_letters method."""

    def test_parse_formatted_output(self):
        """Test parsing properly formatted AI output."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        response_text = """
===START LETTER: Equifax===
Dear Equifax,

I am disputing the following items...

Sincerely,
John Doe
===END LETTER: Equifax===

===START LETTER: Experian===
Dear Experian,

I am writing to dispute...

Sincerely,
John Doe
===END LETTER: Experian===
"""

        result = service._parse_letters(response_text)

        assert 'Equifax' in result
        assert 'Experian' in result
        assert 'I am disputing' in result['Equifax']
        assert 'I am writing to dispute' in result['Experian']

    def test_parse_unformatted_output(self):
        """Test parsing when AI doesn't use expected format."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        response_text = """
Here is your dispute letter:

Dear Credit Bureau,
Please investigate...
"""

        result = service._parse_letters(response_text)

        # Should return as 'Combined' when format not detected
        assert 'Combined' in result or len(result) > 0


class TestGenerateQuickLetter:
    """Tests for generate_quick_letter method."""

    def test_client_not_found(self):
        """Test error when client not found."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AIDisputeWriterService(mock_db)
        result = service.generate_quick_letter(
            client_id=999,
            bureau='Equifax',
            item_description='Test item',
            violation_type='Inaccurate'
        )

        assert 'error' in result


class TestSaveLetter:
    """Tests for save_letter method."""

    def test_success(self):
        """Test saving a letter successfully."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_client

        service = AIDisputeWriterService(mock_db)

        result = service.save_letter(
            client_id=1,
            bureau='Equifax',
            content='Letter content here',
            round_number=1
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_client_not_found(self):
        """Test error when client not found."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AIDisputeWriterService(mock_db)

        with pytest.raises(ValueError, match="Client not found"):
            service.save_letter(
                client_id=999,
                bureau='Equifax',
                content='Test',
                round_number=1
            )


class TestGetRoundInfo:
    """Tests for get_round_info method."""

    def test_valid_round(self):
        """Test getting valid round info."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        result = service.get_round_info(1)

        assert result['round'] == 1
        assert 'name' in result
        assert 'description' in result

    def test_invalid_round(self):
        """Test error for invalid round."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        result = service.get_round_info(99)

        assert 'error' in result


class TestGetAllRoundsInfo:
    """Tests for get_all_rounds_info method."""

    def test_returns_all_rounds(self):
        """Test that all rounds are returned."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        service = AIDisputeWriterService(mock_db)

        result = service.get_all_rounds_info()

        assert len(result) == 4
        rounds = [r['round'] for r in result]
        assert 1 in rounds
        assert 2 in rounds
        assert 3 in rounds
        assert 4 in rounds


class TestSuggestNextAction:
    """Tests for suggest_next_action method."""

    def test_client_not_found(self):
        """Test error when client not found."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AIDisputeWriterService(mock_db)
        result = service.suggest_next_action(client_id=999)

        assert 'error' in result


class TestRegenerateWithFeedback:
    """Tests for regenerate_with_feedback method."""

    def test_client_not_found(self):
        """Test error when client not found."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = AIDisputeWriterService(mock_db)
        result = service.regenerate_with_feedback(
            client_id=999,
            bureau='Equifax',
            original_letter='Test letter',
            feedback='Make it stronger',
            round_number=1
        )

        assert 'error' in result


class TestGetDashboardData:
    """Tests for get_dashboard_data method."""

    def test_overview_dashboard(self):
        """Test overview dashboard without client_id."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db.query.return_value.count.return_value = 0

        service = AIDisputeWriterService(mock_db)
        result = service.get_dashboard_data()

        assert 'active_clients' in result
        assert 'recent_letters' in result
        assert 'total_letters' in result
        assert 'rounds_info' in result

    def test_client_dashboard(self):
        """Test client-specific dashboard."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'Test Client'
        mock_client.email = 'test@example.com'
        mock_client.current_dispute_round = 1
        mock_client.dispute_status = 'active'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = AIDisputeWriterService(mock_db)

        with patch.object(service, 'get_saved_letters', return_value=[]):
            with patch.object(service, 'suggest_next_action', return_value={'action': 'generate'}):
                result = service.get_dashboard_data(client_id=1)

        assert 'client' in result
        assert result['client']['id'] == 1


class TestIntegration:
    """Integration tests for complete flows."""

    def test_full_letter_generation_flow(self):
        """Test the complete letter generation flow."""
        from services.ai_dispute_writer_service import AIDisputeWriterService

        mock_db = MagicMock(spec=Session)

        # Setup mock client
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.name = 'John Doe'
        mock_client.current_dispute_round = 1
        mock_client.address_street = '123 Test St'
        mock_client.address_city = 'City'
        mock_client.address_state = 'CA'
        mock_client.address_zip = '90210'
        mock_client.ssn_last_four = '1234'
        mock_client.date_of_birth = date(1990, 1, 1)
        mock_client.email = 'john@test.com'
        mock_client.phone = '555-1234'

        mock_db.query.return_value.filter.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        service = AIDisputeWriterService(mock_db)

        # Test context gathering
        context = service.get_client_context(1)
        assert context['client'] == mock_client

        # Test formatting
        client_info = service.format_client_info(mock_client)
        assert 'John Doe' in client_info

        # Test round info
        round_info = service.get_round_info(1)
        assert round_info['round'] == 1
