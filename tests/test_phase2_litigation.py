"""
Phase 2: Litigation Features Tests
Tests for violations, standing, damages, case scoring, and litigation review.
"""
import pytest
from datetime import datetime, date


class TestViolationModel:
    """Test violation database operations."""

    def test_create_violation(self, db_session, sample_analysis, sample_client):
        """Test creating a violation record."""
        from database import Violation

        violation = Violation(
            analysis_id=sample_analysis.id,
            client_id=sample_client.id,
            bureau='TransUnion',
            account_name='Credit Card Account',
            fcra_section='§605B',
            violation_type='Failure to Conduct Reasonable Investigation',
            description='Bureau failed to investigate disputed item',
            statutory_damages_min=100,
            statutory_damages_max=1000,
            is_willful=True,
            willfulness_notes='Prior notice ignored'
        )
        db_session.add(violation)
        db_session.commit()

        assert violation.id is not None
        assert violation.is_willful == True
        assert violation.fcra_section == '§605B'

    def test_violation_damages_range(self, sample_violation):
        """Test that violation has valid damages range."""
        assert sample_violation.statutory_damages_min >= 0
        assert sample_violation.statutory_damages_max >= sample_violation.statutory_damages_min
        assert sample_violation.statutory_damages_max <= 1000  # FCRA cap


class TestStandingModel:
    """Test standing verification database operations."""

    def test_create_standing(self, db_session, sample_analysis, sample_client):
        """Test creating a standing record."""
        from database import Standing

        standing = Standing(
            analysis_id=sample_analysis.id,
            client_id=sample_client.id,
            has_concrete_harm=True,
            concrete_harm_type='Credit denial',
            concrete_harm_details='Denied for mortgage due to errors',
            has_dissemination=True,
            dissemination_details='Report shared with lender'
        )
        db_session.add(standing)
        db_session.commit()

        assert standing.id is not None
        assert standing.has_concrete_harm == True

    def test_standing_verification_elements(self, db_session, sample_analysis, sample_client):
        """Test that standing covers required legal elements."""
        from database import Standing

        standing = Standing(
            analysis_id=sample_analysis.id,
            client_id=sample_client.id,
            has_concrete_harm=True,
            has_dissemination=True
        )
        db_session.add(standing)
        db_session.commit()

        # Post-TransUnion requirements
        assert hasattr(standing, 'has_concrete_harm')
        assert hasattr(standing, 'has_dissemination')


class TestDamagesModel:
    """Test damages calculation database operations."""

    def test_create_damages(self, db_session, sample_analysis, sample_client):
        """Test creating a damages record."""
        from database import Damages

        damages = Damages(
            analysis_id=sample_analysis.id,
            client_id=sample_client.id,
            credit_denials_amount=10000,
            higher_interest_amount=2000,
            time_stress_amount=5000,
            actual_damages_total=17000,
            statutory_damages_total=3000
        )
        db_session.add(damages)
        db_session.commit()

        assert damages.id is not None
        assert damages.actual_damages_total > 0

    def test_damages_calculation_logic(self):
        """Test damages calculation helper functions."""
        from services.litigation_tools import calculate_damages

        violations = [
            {'fcra_section': '§611', 'is_willful': True},
            {'fcra_section': '§605B', 'is_willful': False}
        ]

        actual_damages_input = {
            'credit_denials': 10000,
            'higher_interest': 2000,
            'time_and_stress': 5000
        }

        result = calculate_damages(
            violations=violations,
            actual_damages_input=actual_damages_input
        )

        # total_exposure is nested under settlement
        assert 'settlement' in result
        assert result['settlement']['total_exposure'] >= 0


class TestCaseScoreModel:
    """Test case scoring database operations."""

    def test_create_case_score(self, db_session, sample_analysis, sample_client):
        """Test creating a case score record."""
        from database import CaseScore

        score = CaseScore(
            analysis_id=sample_analysis.id,
            client_id=sample_client.id,
            standing_score=3,
            violation_quality_score=4,
            willfulness_score=2,
            documentation_score=1,
            total_score=10,
            settlement_probability=85.0,
            case_strength='Strong'
        )
        db_session.add(score)
        db_session.commit()

        assert score.id is not None
        assert score.total_score == 10
        assert score.case_strength == 'Strong'

    def test_case_scoring_algorithm(self):
        """Test case scoring calculation."""
        from services.litigation_tools import calculate_case_score

        # Create mock standing and violations as dicts (what the function expects)
        standing = {
            'has_concrete_harm': True,
            'has_dissemination': True
        }

        violations = [
            {'is_willful': True, 'fcra_section': '§611'},
            {'is_willful': False, 'fcra_section': '§605B'}
        ]

        damages_data = {
            'total_exposure': 25000,
            'actual_damages': 10000
        }

        result = calculate_case_score(
            standing=standing,
            violations=violations,
            damages_data=damages_data,
            documentation_complete=True
        )

        assert 'total' in result
        assert 'case_strength' in result
        assert 'settlement_probability' in result
        assert result['total'] >= 0
        assert result['total'] <= 10


class TestLitigationTools:
    """Test litigation calculation tools."""

    def test_calculate_damages_import(self):
        """Test that calculate_damages can be imported."""
        from services.litigation_tools import calculate_damages
        assert calculate_damages is not None

    def test_calculate_case_score_import(self):
        """Test that calculate_case_score can be imported."""
        from services.litigation_tools import calculate_case_score
        assert calculate_case_score is not None

    def test_assess_willfulness_import(self):
        """Test that assess_willfulness can be imported."""
        from services.litigation_tools import assess_willfulness
        assert assess_willfulness is not None

    def test_statutory_damages_cap(self):
        """Test that statutory damages respect FCRA cap."""
        from services.litigation_tools import calculate_damages

        # Many violations should still cap at per-violation limits
        violations = [{'fcra_section': '§611', 'is_willful': True}] * 10

        actual_damages_input = {'credit_denials': 0}
        result = calculate_damages(violations=violations, actual_damages_input=actual_damages_input)

        # Per §1681n, statutory damages are $100-$1,000 per violation
        per_violation_max = 1000 * len(violations)
        statutory = result.get('statutory_damages', {}).get('total', 0) if isinstance(result.get('statutory_damages'), dict) else result.get('statutory_total', 0)
        assert statutory <= per_violation_max


class TestLitigationAPIEndpoints:
    """Test litigation-related API endpoints."""

    def test_get_violations(self, authenticated_client, sample_analysis):
        """Test getting violations for an analysis."""
        response = authenticated_client.get(f'/api/analysis/{sample_analysis.id}/violations')
        # May return empty list if no violations
        assert response.status_code == 200

    def test_add_violation(self, authenticated_client, sample_analysis):
        """Test adding a violation."""
        response = authenticated_client.post(
            f'/api/analysis/{sample_analysis.id}/violations',
            json={
                'bureau': 'Experian',
                'account_name': 'Test Account',
                'fcra_section': '§611',
                'violation_type': 'Inaccurate Information',
                'description': 'Test violation',
                'is_willful': False
            }
        )
        assert response.status_code == 200

    def test_get_case_score(self, authenticated_client, sample_analysis):
        """Test getting case score."""
        response = authenticated_client.get(f'/api/analysis/{sample_analysis.id}/score')
        assert response.status_code == 200
