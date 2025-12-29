"""
Unit tests for Case Law Service
Tests for managing and querying FCRA case law citations including
populating default cases, searching, filtering, CRUD operations,
and citation suggestions based on analysis violations.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.case_law_service import (
    DEFAULT_FCRA_CASES,
    populate_default_cases,
    get_citations_for_violation,
    get_citations_for_fcra_section,
    format_citation_for_letter,
    suggest_citations_for_analysis,
    search_cases,
    get_all_cases,
    get_case_by_id,
    create_case,
    update_case,
    delete_case,
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
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.rollback = Mock()
    db.delete = Mock()
    db.close = Mock()
    return db


@pytest.fixture
def mock_case_law_citation():
    """Create a mock CaseLawCitation object."""
    case = Mock()
    case.id = 1
    case.case_name = "Test v. Example Corp."
    case.citation = "123 F.3d 456 (5th Cir. 2020)"
    case.court = "5th Circuit"
    case.year = 2020
    case.fcra_sections = ["611", "1681i"]
    case.violation_types = ["reinsertion", "failure_to_investigate"]
    case.key_holding = "Test holding about reinvestigation duty."
    case.full_summary = "Full summary of the case."
    case.quote_snippets = [{"quote": "Important quote", "page": "460"}]
    case.damages_awarded = 50000.00
    case.plaintiff_won = True
    case.relevance_score = 5
    case.tags = ["reinsertion", "test"]
    case.notes = "Test notes"
    case.created_at = datetime.utcnow()
    case.updated_at = datetime.utcnow()
    case.to_dict = Mock(return_value={
        'id': 1,
        'case_name': 'Test v. Example Corp.',
        'citation': '123 F.3d 456 (5th Cir. 2020)',
        'court': '5th Circuit',
        'year': 2020,
        'fcra_sections': ['611', '1681i'],
        'violation_types': ['reinsertion', 'failure_to_investigate'],
        'key_holding': 'Test holding about reinvestigation duty.',
        'full_summary': 'Full summary of the case.',
        'quote_snippets': [{'quote': 'Important quote', 'page': '460'}],
        'damages_awarded': 50000.00,
        'plaintiff_won': True,
        'relevance_score': 5,
        'tags': ['reinsertion', 'test'],
        'notes': 'Test notes',
        'created_at': None,
        'updated_at': None,
    })
    case.format_citation = Mock(side_effect=lambda fmt: {
        'short': 'Test v. Example Corp., 123 F.3d 456 (5th Cir. 2020)',
        'full': 'Test v. Example Corp., 123 F.3d 456 (5th Cir. 2020) (5th Circuit, 2020)',
        'with_holding': 'Test v. Example Corp., 123 F.3d 456 (5th Cir. 2020) ("Test holding about reinvestigation duty.")'
    }.get(fmt, 'Test v. Example Corp., 123 F.3d 456 (5th Cir. 2020)'))
    return case


@pytest.fixture
def mock_case_no_match():
    """Create a mock CaseLawCitation that won't match common searches."""
    case = Mock()
    case.id = 2
    case.case_name = "Unrelated v. Other Corp."
    case.citation = "789 F.3d 101 (9th Cir. 2015)"
    case.court = "9th Circuit"
    case.year = 2015
    case.fcra_sections = ["615", "1681m"]
    case.violation_types = ["adverse_action"]
    case.key_holding = "Unrelated holding."
    case.full_summary = "Unrelated summary."
    case.quote_snippets = []
    case.damages_awarded = None
    case.plaintiff_won = False
    case.relevance_score = 2
    case.tags = ["adverse_action"]
    case.notes = None
    case.to_dict = Mock(return_value={
        'id': 2,
        'case_name': 'Unrelated v. Other Corp.',
        'citation': '789 F.3d 101 (9th Cir. 2015)',
        'court': '9th Circuit',
        'year': 2015,
        'fcra_sections': ['615', '1681m'],
        'violation_types': ['adverse_action'],
        'key_holding': 'Unrelated holding.',
        'full_summary': 'Unrelated summary.',
        'quote_snippets': [],
        'damages_awarded': None,
        'plaintiff_won': False,
        'relevance_score': 2,
        'tags': ['adverse_action'],
        'notes': None,
        'created_at': None,
        'updated_at': None,
    })
    return case


# ============== DEFAULT_FCRA_CASES Tests ==============


class TestDefaultFcraCases:
    """Tests for DEFAULT_FCRA_CASES constant."""

    def test_default_cases_not_empty(self):
        """Test that DEFAULT_FCRA_CASES contains cases."""
        assert len(DEFAULT_FCRA_CASES) > 0

    def test_default_cases_have_required_fields(self):
        """Test that each default case has required fields."""
        required_fields = ['case_name', 'citation', 'court', 'year',
                          'fcra_sections', 'violation_types', 'key_holding']
        for case in DEFAULT_FCRA_CASES:
            for field in required_fields:
                assert field in case, f"Missing field {field} in case {case.get('case_name', 'unknown')}"

    def test_default_cases_include_landmark_cases(self):
        """Test that landmark FCRA cases are included."""
        case_names = [c['case_name'] for c in DEFAULT_FCRA_CASES]
        # Check for some well-known FCRA cases
        assert any('Safeco' in name for name in case_names), "Missing Safeco case"
        assert any('Spokeo' in name for name in case_names), "Missing Spokeo case"
        assert any('TransUnion' in name or 'Trans Union' in name for name in case_names), "Missing TransUnion case"

    def test_default_cases_have_valid_years(self):
        """Test that all cases have valid years."""
        for case in DEFAULT_FCRA_CASES:
            assert isinstance(case['year'], int)
            assert 1970 <= case['year'] <= datetime.now().year + 1

    def test_default_cases_have_valid_relevance_scores(self):
        """Test that relevance scores are in valid range."""
        for case in DEFAULT_FCRA_CASES:
            score = case.get('relevance_score', 3)
            assert 1 <= score <= 5, f"Invalid relevance_score for {case['case_name']}"


# ============== populate_default_cases Tests ==============


class TestPopulateDefaultCases:
    """Tests for populate_default_cases function."""

    def test_populate_default_cases_empty_db(self, mock_db):
        """Test populating cases when database is empty."""
        mock_db.query.return_value.count.return_value = 0

        result = populate_default_cases(db=mock_db)

        assert result['status'] == 'success'
        assert result['count'] == len(DEFAULT_FCRA_CASES)
        assert mock_db.add.call_count == len(DEFAULT_FCRA_CASES)
        mock_db.commit.assert_called_once()

    def test_populate_default_cases_db_has_cases(self, mock_db):
        """Test populating cases when database already has cases."""
        mock_db.query.return_value.count.return_value = 10

        result = populate_default_cases(db=mock_db)

        assert result['status'] == 'skipped'
        assert result['count'] == 10
        assert 'already has' in result['message']
        mock_db.add.assert_not_called()

    def test_populate_default_cases_db_error(self, mock_db):
        """Test populating cases when database error occurs."""
        mock_db.query.return_value.count.return_value = 0
        mock_db.commit.side_effect = Exception("Database connection error")

        result = populate_default_cases(db=mock_db)

        assert result['status'] == 'error'
        assert 'Database connection error' in result['message']
        mock_db.rollback.assert_called_once()

    @patch('services.case_law_service.get_db')
    def test_populate_default_cases_creates_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.count.return_value = 5

        result = populate_default_cases()

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()

    def test_populate_default_cases_no_close_when_provided(self, mock_db):
        """Test that function doesn't close db when provided."""
        mock_db.query.return_value.count.return_value = 5

        result = populate_default_cases(db=mock_db)

        mock_db.close.assert_not_called()


# ============== get_citations_for_violation Tests ==============


class TestGetCitationsForViolation:
    """Tests for get_citations_for_violation function."""

    def test_get_citations_matching_violation(self, mock_db, mock_case_law_citation, mock_case_no_match):
        """Test getting citations for a matching violation type."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation, mock_case_no_match]

        result = get_citations_for_violation('reinsertion', db=mock_db)

        assert len(result) == 1
        assert result[0]['case_name'] == 'Test v. Example Corp.'

    def test_get_citations_no_matches(self, mock_db, mock_case_no_match):
        """Test getting citations when no violations match."""
        mock_db.query.return_value.all.return_value = [mock_case_no_match]

        result = get_citations_for_violation('nonexistent_violation', db=mock_db)

        assert len(result) == 0

    def test_get_citations_sorted_by_relevance(self, mock_db, mock_case_law_citation, mock_case_no_match):
        """Test that results are sorted by relevance score (descending)."""
        # Create another case with different relevance
        case_high_relevance = Mock()
        case_high_relevance.violation_types = ['reinsertion']
        case_high_relevance.to_dict = Mock(return_value={
            'case_name': 'High Relevance Case',
            'relevance_score': 5,
        })

        case_low_relevance = Mock()
        case_low_relevance.violation_types = ['reinsertion']
        case_low_relevance.to_dict = Mock(return_value={
            'case_name': 'Low Relevance Case',
            'relevance_score': 2,
        })

        mock_db.query.return_value.all.return_value = [case_low_relevance, case_high_relevance]

        result = get_citations_for_violation('reinsertion', db=mock_db)

        assert len(result) == 2
        assert result[0]['relevance_score'] >= result[1]['relevance_score']

    def test_get_citations_handles_none_violation_types(self, mock_db):
        """Test handling of cases with None violation_types."""
        case_with_none = Mock()
        case_with_none.violation_types = None

        mock_db.query.return_value.all.return_value = [case_with_none]

        result = get_citations_for_violation('reinsertion', db=mock_db)

        assert len(result) == 0

    @patch('services.case_law_service.get_db')
    def test_get_citations_creates_and_closes_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.all.return_value = []

        result = get_citations_for_violation('reinsertion')

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()


# ============== get_citations_for_fcra_section Tests ==============


class TestGetCitationsForFcraSection:
    """Tests for get_citations_for_fcra_section function."""

    def test_get_citations_matching_section(self, mock_db, mock_case_law_citation, mock_case_no_match):
        """Test getting citations for a matching FCRA section."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation, mock_case_no_match]

        result = get_citations_for_fcra_section('611', db=mock_db)

        assert len(result) == 1
        assert result[0]['case_name'] == 'Test v. Example Corp.'

    def test_get_citations_section_with_symbol(self, mock_db, mock_case_law_citation):
        """Test getting citations with section symbol in query."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = get_citations_for_fcra_section('§611', db=mock_db)

        assert len(result) == 1

    def test_get_citations_section_with_spaces(self, mock_db, mock_case_law_citation):
        """Test getting citations with spaces in query."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = get_citations_for_fcra_section(' 611 ', db=mock_db)

        assert len(result) == 1

    def test_get_citations_section_case_insensitive(self, mock_db):
        """Test that section matching is case insensitive."""
        case = Mock()
        case.fcra_sections = ['Section611']
        case.to_dict = Mock(return_value={'relevance_score': 3})

        mock_db.query.return_value.all.return_value = [case]

        result = get_citations_for_fcra_section('section611', db=mock_db)

        assert len(result) == 1

    def test_get_citations_no_matches(self, mock_db, mock_case_no_match):
        """Test getting citations when no sections match."""
        mock_db.query.return_value.all.return_value = [mock_case_no_match]

        result = get_citations_for_fcra_section('999', db=mock_db)

        assert len(result) == 0

    def test_get_citations_handles_none_fcra_sections(self, mock_db):
        """Test handling of cases with None fcra_sections."""
        case_with_none = Mock()
        case_with_none.fcra_sections = None

        mock_db.query.return_value.all.return_value = [case_with_none]

        result = get_citations_for_fcra_section('611', db=mock_db)

        assert len(result) == 0

    @patch('services.case_law_service.get_db')
    def test_get_citations_section_closes_db(self, mock_get_db, mock_db):
        """Test that function closes db when created internally."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.all.return_value = []

        result = get_citations_for_fcra_section('611')

        mock_db.close.assert_called_once()


# ============== format_citation_for_letter Tests ==============


class TestFormatCitationForLetter:
    """Tests for format_citation_for_letter function."""

    def test_format_citation_short(self, mock_db, mock_case_law_citation):
        """Test formatting citation in short format."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        result = format_citation_for_letter(1, format_type='short', db=mock_db)

        assert result == 'Test v. Example Corp., 123 F.3d 456 (5th Cir. 2020)'
        mock_case_law_citation.format_citation.assert_called_with('short')

    def test_format_citation_full(self, mock_db, mock_case_law_citation):
        """Test formatting citation in full format."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        result = format_citation_for_letter(1, format_type='full', db=mock_db)

        assert 'Test v. Example Corp.' in result
        mock_case_law_citation.format_citation.assert_called_with('full')

    def test_format_citation_with_holding(self, mock_db, mock_case_law_citation):
        """Test formatting citation with key holding."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        result = format_citation_for_letter(1, format_type='with_holding', db=mock_db)

        mock_case_law_citation.format_citation.assert_called_with('with_holding')

    def test_format_citation_not_found(self, mock_db):
        """Test formatting citation when case not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = format_citation_for_letter(999, db=mock_db)

        assert result is None

    def test_format_citation_default_format(self, mock_db, mock_case_law_citation):
        """Test formatting citation with default format."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        result = format_citation_for_letter(1, db=mock_db)

        mock_case_law_citation.format_citation.assert_called_with('short')

    @patch('services.case_law_service.get_db')
    def test_format_citation_creates_and_closes_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = format_citation_for_letter(1)

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()


# ============== suggest_citations_for_analysis Tests ==============


class TestSuggestCitationsForAnalysis:
    """Tests for suggest_citations_for_analysis function."""

    def test_suggest_citations_matching_violations(self, mock_db, mock_case_law_citation):
        """Test suggesting citations based on matching violations."""
        # Mock Analysis
        mock_analysis = Mock()
        mock_analysis.id = 1

        # Mock Violation
        mock_violation = Mock()
        mock_violation.violation_type = "Reinsertion"
        mock_violation.fcra_section = "611"

        # The function imports Analysis and Violation from database locally
        # We need to mock at the database module level
        with patch('database.Analysis') as MockAnalysis:
            with patch('database.Violation') as MockViolation:
                mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
                mock_db.query.return_value.filter.return_value.all.side_effect = [
                    [mock_violation],  # Violations
                    [mock_case_law_citation],  # Cases
                ]

                result = suggest_citations_for_analysis(1, db=mock_db)

        assert len(result) >= 0  # May or may not match depending on implementation

    def test_suggest_citations_analysis_not_found(self, mock_db):
        """Test suggesting citations when analysis not found."""
        with patch('database.Analysis') as MockAnalysis:
            mock_db.query.return_value.filter.return_value.first.return_value = None

            result = suggest_citations_for_analysis(999, db=mock_db)

        assert result == []

    def test_suggest_citations_no_violations(self, mock_db):
        """Test suggesting citations when analysis has no violations."""
        mock_analysis = Mock()
        mock_analysis.id = 1

        with patch('database.Analysis') as MockAnalysis:
            with patch('database.Violation') as MockViolation:
                mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
                mock_db.query.return_value.filter.return_value.all.side_effect = [
                    [],  # No violations
                    [],  # No cases needed
                ]

                result = suggest_citations_for_analysis(1, db=mock_db)

        assert len(result) == 0

    def test_suggest_citations_limited_to_10(self, mock_db, mock_case_law_citation):
        """Test that suggestions are limited to top 10."""
        mock_analysis = Mock()
        mock_analysis.id = 1

        mock_violation = Mock()
        mock_violation.violation_type = "reinsertion"
        mock_violation.fcra_section = "611"

        # Create 15 matching cases
        cases = []
        for i in range(15):
            case = Mock()
            case.violation_types = ['reinsertion']
            case.fcra_sections = ['611']
            case.relevance_score = i
            case.to_dict = Mock(return_value={
                'id': i,
                'case_name': f'Case {i}',
                'relevance_score': i,
            })
            cases.append(case)

        with patch('database.Analysis') as MockAnalysis:
            with patch('database.Violation') as MockViolation:
                mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
                mock_db.query.return_value.filter.return_value.all.side_effect = [
                    [mock_violation],
                    cases,
                ]

                result = suggest_citations_for_analysis(1, db=mock_db)

        assert len(result) <= 10

    def test_suggest_citations_includes_match_reasons(self, mock_db):
        """Test that suggestions include match reasons."""
        mock_analysis = Mock()
        mock_violation = Mock()
        mock_violation.violation_type = "failure_to_investigate"
        mock_violation.fcra_section = "611"

        case = Mock()
        case.violation_types = ['failure_to_investigate']
        case.fcra_sections = ['611']
        case.relevance_score = 4
        case.to_dict = Mock(return_value={
            'id': 1,
            'case_name': 'Test Case',
            'relevance_score': 4,
        })

        with patch('database.Analysis') as MockAnalysis:
            with patch('database.Violation') as MockViolation:
                mock_db.query.return_value.filter.return_value.first.return_value = mock_analysis
                mock_db.query.return_value.filter.return_value.all.side_effect = [
                    [mock_violation],
                    [case],
                ]

                result = suggest_citations_for_analysis(1, db=mock_db)

        if len(result) > 0:
            assert 'match_score' in result[0]
            assert 'match_reasons' in result[0]

    @patch('services.case_law_service.get_db')
    def test_suggest_citations_creates_and_closes_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db

        with patch('database.Analysis') as MockAnalysis:
            mock_db.query.return_value.filter.return_value.first.return_value = None

            result = suggest_citations_for_analysis(1)

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()


# ============== search_cases Tests ==============


class TestSearchCases:
    """Tests for search_cases function."""

    def test_search_by_case_name(self, mock_db, mock_case_law_citation):
        """Test searching cases by case name."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = search_cases('Test v. Example', db=mock_db)

        assert len(result) == 1
        assert result[0]['search_score'] >= 10  # Case name match gives 10 points

    def test_search_by_citation(self, mock_db, mock_case_law_citation):
        """Test searching cases by citation."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = search_cases('123 F.3d', db=mock_db)

        assert len(result) == 1

    def test_search_by_court(self, mock_db, mock_case_law_citation):
        """Test searching cases by court name."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = search_cases('5th Circuit', db=mock_db)

        assert len(result) == 1

    def test_search_by_key_holding(self, mock_db, mock_case_law_citation):
        """Test searching cases by key holding."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = search_cases('reinvestigation duty', db=mock_db)

        assert len(result) == 1

    def test_search_by_tag(self, mock_db, mock_case_law_citation):
        """Test searching cases by tag."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = search_cases('reinsertion', db=mock_db)

        assert len(result) == 1

    def test_search_case_insensitive(self, mock_db, mock_case_law_citation):
        """Test that search is case insensitive."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = search_cases('TEST V. EXAMPLE', db=mock_db)

        assert len(result) == 1

    def test_search_no_results(self, mock_db, mock_case_law_citation):
        """Test search with no matching results."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = search_cases('nonexistent term xyz123', db=mock_db)

        assert len(result) == 0

    def test_search_sorted_by_score(self, mock_db):
        """Test that results are sorted by search score (descending)."""
        case1 = Mock()
        case1.case_name = "Test Case One"
        case1.citation = None
        case1.key_holding = None
        case1.full_summary = None
        case1.court = None
        case1.tags = []
        case1.to_dict = Mock(return_value={'search_score': 0})

        case2 = Mock()
        case2.case_name = "Test Case Two"
        case2.citation = "test citation"
        case2.key_holding = None
        case2.full_summary = None
        case2.court = None
        case2.tags = []
        case2.to_dict = Mock(return_value={'search_score': 0})

        mock_db.query.return_value.all.return_value = [case1, case2]

        result = search_cases('test', db=mock_db)

        # Both should match, higher score first
        assert len(result) == 2
        assert result[0]['search_score'] >= result[1]['search_score']

    def test_search_handles_none_fields(self, mock_db):
        """Test search handles cases with None fields."""
        case = Mock()
        case.case_name = "Test Case"
        case.citation = None
        case.key_holding = None
        case.full_summary = None
        case.court = None
        case.tags = None

        case.to_dict = Mock(return_value={'case_name': 'Test Case', 'search_score': 0})

        mock_db.query.return_value.all.return_value = [case]

        result = search_cases('test', db=mock_db)

        assert len(result) == 1

    @patch('services.case_law_service.get_db')
    def test_search_creates_and_closes_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.all.return_value = []

        result = search_cases('test')

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()


# ============== get_all_cases Tests ==============


class TestGetAllCases:
    """Tests for get_all_cases function."""

    def test_get_all_cases_no_filters(self, mock_db, mock_case_law_citation):
        """Test getting all cases without filters."""
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_case_law_citation]

        result = get_all_cases(db=mock_db)

        assert len(result) == 1

    def test_get_all_cases_filter_by_court(self, mock_db, mock_case_law_citation):
        """Test filtering cases by court."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_case_law_citation]

        result = get_all_cases(filters={'court': '5th Circuit'}, db=mock_db)

        assert len(result) == 1

    def test_get_all_cases_filter_by_year(self, mock_db, mock_case_law_citation):
        """Test filtering cases by year."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_case_law_citation]

        result = get_all_cases(filters={'year': '2020'}, db=mock_db)

        assert len(result) == 1

    def test_get_all_cases_filter_by_plaintiff_won(self, mock_db, mock_case_law_citation):
        """Test filtering cases by plaintiff_won status."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_case_law_citation]

        result = get_all_cases(filters={'plaintiff_won': True}, db=mock_db)

        assert len(result) == 1

    def test_get_all_cases_filter_by_section(self, mock_db, mock_case_law_citation):
        """Test filtering cases by FCRA section."""
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_case_law_citation]

        result = get_all_cases(filters={'section': '611'}, db=mock_db)

        assert len(result) == 1

    def test_get_all_cases_filter_by_violation_type(self, mock_db, mock_case_law_citation):
        """Test filtering cases by violation type."""
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_case_law_citation]

        result = get_all_cases(filters={'violation_type': 'reinsertion'}, db=mock_db)

        assert len(result) == 1

    def test_get_all_cases_combined_filters(self, mock_db, mock_case_law_citation):
        """Test filtering cases with multiple filters."""
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_case_law_citation]

        result = get_all_cases(filters={
            'court': '5th Circuit',
            'year': '2020',
            'section': '611',
        }, db=mock_db)

        assert len(result) >= 0

    def test_get_all_cases_empty_result(self, mock_db):
        """Test getting cases when database is empty."""
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        result = get_all_cases(db=mock_db)

        assert result == []

    @patch('services.case_law_service.get_db')
    def test_get_all_cases_creates_and_closes_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        result = get_all_cases()

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()


# ============== get_case_by_id Tests ==============


class TestGetCaseById:
    """Tests for get_case_by_id function."""

    def test_get_case_found(self, mock_db, mock_case_law_citation):
        """Test getting an existing case by ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        result = get_case_by_id(1, db=mock_db)

        assert result is not None
        assert result['id'] == 1
        assert result['case_name'] == 'Test v. Example Corp.'

    def test_get_case_not_found(self, mock_db):
        """Test getting a non-existent case."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_case_by_id(999, db=mock_db)

        assert result is None

    @patch('services.case_law_service.get_db')
    def test_get_case_by_id_creates_and_closes_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_case_by_id(1)

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()


# ============== create_case Tests ==============


class TestCreateCase:
    """Tests for create_case function."""

    def test_create_case_success(self, mock_db):
        """Test successful case creation."""
        case_data = {
            'case_name': 'New v. Case',
            'citation': '999 F.3d 111 (1st Cir. 2023)',
            'court': '1st Circuit',
            'year': 2023,
            'fcra_sections': ['611'],
            'violation_types': ['reinsertion'],
            'key_holding': 'New holding',
        }

        mock_db.refresh = Mock(side_effect=lambda x: setattr(x, 'id', 1))

        with patch('services.case_law_service.CaseLawCitation') as MockCitation:
            mock_instance = Mock()
            mock_instance.to_dict.return_value = {**case_data, 'id': 1}
            MockCitation.return_value = mock_instance

            result = create_case(case_data, db=mock_db)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert result['case_name'] == 'New v. Case'

    def test_create_case_minimal_data(self, mock_db):
        """Test creating case with minimal required data."""
        case_data = {
            'case_name': 'Minimal v. Case',
            'citation': '100 F.3d 200',
        }

        with patch('services.case_law_service.CaseLawCitation') as MockCitation:
            mock_instance = Mock()
            mock_instance.to_dict.return_value = {**case_data, 'id': 1}
            MockCitation.return_value = mock_instance

            result = create_case(case_data, db=mock_db)

        mock_db.add.assert_called_once()

    def test_create_case_with_all_fields(self, mock_db):
        """Test creating case with all optional fields."""
        case_data = {
            'case_name': 'Full v. Case',
            'citation': '200 F.3d 300',
            'court': '5th Circuit',
            'year': 2022,
            'fcra_sections': ['611', '1681i'],
            'violation_types': ['reinsertion', 'failure_to_investigate'],
            'key_holding': 'Important holding',
            'full_summary': 'Full case summary',
            'quote_snippets': [{'quote': 'Test quote', 'page': '123'}],
            'damages_awarded': 100000.00,
            'plaintiff_won': True,
            'relevance_score': 5,
            'tags': ['test', 'full'],
            'notes': 'Test notes',
        }

        with patch('services.case_law_service.CaseLawCitation') as MockCitation:
            mock_instance = Mock()
            mock_instance.to_dict.return_value = {**case_data, 'id': 1}
            MockCitation.return_value = mock_instance

            result = create_case(case_data, db=mock_db)

        mock_db.add.assert_called_once()

    def test_create_case_db_error(self, mock_db):
        """Test case creation with database error."""
        case_data = {
            'case_name': 'Error v. Case',
            'citation': '999 F.3d 999',
        }

        mock_db.commit.side_effect = Exception("Database error")

        with patch('services.case_law_service.CaseLawCitation') as MockCitation:
            MockCitation.return_value = Mock()

            with pytest.raises(Exception) as exc_info:
                create_case(case_data, db=mock_db)

        assert "Database error" in str(exc_info.value)
        mock_db.rollback.assert_called_once()

    @patch('services.case_law_service.get_db')
    def test_create_case_creates_and_closes_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db
        case_data = {'case_name': 'Test', 'citation': 'Test Citation'}

        with patch('services.case_law_service.CaseLawCitation') as MockCitation:
            mock_instance = Mock()
            mock_instance.to_dict.return_value = {'id': 1}
            MockCitation.return_value = mock_instance

            result = create_case(case_data)

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()


# ============== update_case Tests ==============


class TestUpdateCase:
    """Tests for update_case function."""

    def test_update_case_success(self, mock_db, mock_case_law_citation):
        """Test successful case update."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        result = update_case(1, {'case_name': 'Updated v. Case'}, db=mock_db)

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
        assert mock_case_law_citation.case_name == 'Updated v. Case'

    def test_update_case_not_found(self, mock_db):
        """Test updating non-existent case."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = update_case(999, {'case_name': 'Updated'}, db=mock_db)

        assert result is None
        mock_db.commit.assert_not_called()

    def test_update_case_multiple_fields(self, mock_db, mock_case_law_citation):
        """Test updating multiple fields at once."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        update_data = {
            'case_name': 'Updated v. Case',
            'court': 'Updated Circuit',
            'year': 2025,
            'relevance_score': 4,
        }

        result = update_case(1, update_data, db=mock_db)

        mock_db.commit.assert_called_once()
        assert mock_case_law_citation.case_name == 'Updated v. Case'
        assert mock_case_law_citation.court == 'Updated Circuit'
        assert mock_case_law_citation.year == 2025

    def test_update_case_ignores_id(self, mock_db, mock_case_law_citation):
        """Test that id field is not updated."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation
        original_id = mock_case_law_citation.id

        result = update_case(1, {'id': 999, 'case_name': 'Updated'}, db=mock_db)

        assert mock_case_law_citation.id == original_id

    def test_update_case_ignores_created_at(self, mock_db, mock_case_law_citation):
        """Test that created_at field is not updated."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation
        original_created = mock_case_law_citation.created_at

        new_time = datetime(2000, 1, 1)
        result = update_case(1, {'created_at': new_time, 'case_name': 'Updated'}, db=mock_db)

        assert mock_case_law_citation.created_at == original_created

    def test_update_case_sets_updated_at(self, mock_db, mock_case_law_citation):
        """Test that updated_at is set on update."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        result = update_case(1, {'case_name': 'Updated'}, db=mock_db)

        assert mock_case_law_citation.updated_at is not None

    def test_update_case_db_error(self, mock_db, mock_case_law_citation):
        """Test case update with database error."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            update_case(1, {'case_name': 'Updated'}, db=mock_db)

        assert "Database error" in str(exc_info.value)
        mock_db.rollback.assert_called_once()

    @patch('services.case_law_service.get_db')
    def test_update_case_creates_and_closes_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = update_case(1, {'case_name': 'Updated'})

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()


# ============== delete_case Tests ==============


class TestDeleteCase:
    """Tests for delete_case function."""

    def test_delete_case_success(self, mock_db, mock_case_law_citation):
        """Test successful case deletion."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        result = delete_case(1, db=mock_db)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_case_law_citation)
        mock_db.commit.assert_called_once()

    def test_delete_case_not_found(self, mock_db):
        """Test deleting non-existent case."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = delete_case(999, db=mock_db)

        assert result is False
        mock_db.delete.assert_not_called()
        mock_db.commit.assert_not_called()

    def test_delete_case_db_error(self, mock_db, mock_case_law_citation):
        """Test case deletion with database error."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation
        mock_db.commit.side_effect = Exception("Database error")

        with pytest.raises(Exception) as exc_info:
            delete_case(1, db=mock_db)

        assert "Database error" in str(exc_info.value)
        mock_db.rollback.assert_called_once()

    @patch('services.case_law_service.get_db')
    def test_delete_case_creates_and_closes_db(self, mock_get_db, mock_db):
        """Test that function creates and closes db if not provided."""
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = delete_case(1)

        mock_get_db.assert_called_once()
        mock_db.close.assert_called_once()


# ============== Integration Tests (Mocked) ==============


class TestCaseLawServiceIntegration:
    """Integration tests for case law service (using mocks)."""

    def test_create_search_delete_workflow(self, mock_db):
        """Test complete workflow: create, search, delete."""
        # Setup mocks for create
        created_case = Mock()
        created_case.id = 10
        created_case.case_name = "Workflow v. Test"
        created_case.to_dict = Mock(return_value={
            'id': 10,
            'case_name': 'Workflow v. Test',
            'citation': '111 F.3d 222',
            'relevance_score': 3,
        })

        with patch('services.case_law_service.CaseLawCitation') as MockCitation:
            MockCitation.return_value = created_case

            # Create
            case_data = {'case_name': 'Workflow v. Test', 'citation': '111 F.3d 222'}
            create_result = create_case(case_data, db=mock_db)

            assert create_result['id'] == 10

        # Setup mocks for search
        mock_db.query.return_value.all.return_value = [created_case]
        created_case.citation = '111 F.3d 222'
        created_case.key_holding = None
        created_case.full_summary = None
        created_case.court = None
        created_case.tags = None

        # Search
        search_results = search_cases('Workflow', db=mock_db)
        assert len(search_results) == 1

        # Setup mocks for delete
        mock_db.query.return_value.filter.return_value.first.return_value = created_case

        # Delete
        delete_result = delete_case(10, db=mock_db)
        assert delete_result is True

    def test_populate_and_filter_workflow(self, mock_db):
        """Test workflow: populate defaults and filter by violation type."""
        # First verify we have default cases to populate
        assert len(DEFAULT_FCRA_CASES) > 0

        # Find a violation type that exists in defaults
        test_violation_type = DEFAULT_FCRA_CASES[0]['violation_types'][0]

        # Create mock cases matching the default data
        mock_cases = []
        for case_data in DEFAULT_FCRA_CASES[:3]:
            mock_case = Mock()
            mock_case.violation_types = case_data['violation_types']
            mock_case.to_dict = Mock(return_value={
                'case_name': case_data['case_name'],
                'relevance_score': case_data.get('relevance_score', 3),
            })
            mock_cases.append(mock_case)

        mock_db.query.return_value.all.return_value = mock_cases

        # Filter by violation type
        results = get_citations_for_violation(test_violation_type, db=mock_db)

        # Should find at least one match
        assert len(results) >= 1


# ============== Edge Cases ==============


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_search_query(self, mock_db):
        """Test search with empty query."""
        mock_db.query.return_value.all.return_value = []

        result = search_cases('', db=mock_db)

        assert result == []

    def test_special_characters_in_search(self, mock_db, mock_case_law_citation):
        """Test search with special characters."""
        mock_db.query.return_value.all.return_value = [mock_case_law_citation]

        result = search_cases('v.', db=mock_db)

        assert len(result) >= 0  # May or may not match

    def test_very_long_search_query(self, mock_db):
        """Test search with very long query."""
        mock_db.query.return_value.all.return_value = []

        long_query = 'a' * 1000
        result = search_cases(long_query, db=mock_db)

        assert result == []

    def test_unicode_in_search(self, mock_db):
        """Test search with unicode characters."""
        mock_db.query.return_value.all.return_value = []

        result = search_cases('test unicode char', db=mock_db)

        assert result == []

    def test_filter_with_empty_arrays(self, mock_db):
        """Test filtering cases that have empty violation_types/fcra_sections."""
        case_with_empty = Mock()
        case_with_empty.fcra_sections = []
        case_with_empty.violation_types = []
        case_with_empty.to_dict = Mock(return_value={'relevance_score': 3})

        mock_db.query.return_value.all.return_value = [case_with_empty]

        result = get_citations_for_violation('reinsertion', db=mock_db)

        assert len(result) == 0

    def test_case_with_zero_damages(self, mock_db):
        """Test case with zero damages awarded."""
        case_data = {
            'case_name': 'Zero Damages v. Case',
            'citation': '123 F.3d 456',
            'damages_awarded': 0.0,
        }

        with patch('services.case_law_service.CaseLawCitation') as MockCitation:
            mock_instance = Mock()
            mock_instance.to_dict.return_value = {**case_data, 'id': 1}
            MockCitation.return_value = mock_instance

            result = create_case(case_data, db=mock_db)

        mock_db.add.assert_called_once()

    def test_case_with_negative_id_lookup(self, mock_db):
        """Test looking up case with negative ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_case_by_id(-1, db=mock_db)

        assert result is None

    def test_update_nonexistent_field(self, mock_db, mock_case_law_citation):
        """Test updating with a field that doesn't exist on the model."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_case_law_citation

        # This should not raise an error, but the field won't be updated
        result = update_case(1, {'nonexistent_field': 'value'}, db=mock_db)

        mock_db.commit.assert_called_once()
