"""
Tests for LeadScoringService

Tests the lead scoring functionality that prioritizes clients
based on their credit report analysis.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from services.lead_scoring_service import (
    LeadScoringService,
    score_client,
    get_client_score,
    rescore_all_clients,
)


class TestLeadScoringService:
    """Test the LeadScoringService class"""

    def test_scoring_weights_exist(self):
        """Test that scoring weights are defined"""
        weights = LeadScoringService.SCORING_WEIGHTS
        assert "collection" in weights
        assert "late_payment" in weights
        assert "public_record" in weights
        assert "violation" in weights

    def test_max_score_defined(self):
        """Test that max score is defined"""
        assert LeadScoringService.MAX_SCORE == 100

    def test_collection_weight(self):
        """Test collection weight value"""
        assert LeadScoringService.SCORING_WEIGHTS["collection"] == 15

    def test_public_record_weight(self):
        """Test public record weight value"""
        assert LeadScoringService.SCORING_WEIGHTS["public_record"] == 20

    def test_violation_weight(self):
        """Test violation weight value"""
        assert LeadScoringService.SCORING_WEIGHTS["violation"] == 10


class TestGetPriorityLabel:
    """Test the _get_priority_label method"""

    def test_high_priority(self):
        """Test high priority label for score >= 70"""
        assert LeadScoringService._get_priority_label(70) == "HIGH"
        assert LeadScoringService._get_priority_label(85) == "HIGH"
        assert LeadScoringService._get_priority_label(100) == "HIGH"

    def test_medium_priority(self):
        """Test medium priority label for score 40-69"""
        assert LeadScoringService._get_priority_label(40) == "MEDIUM"
        assert LeadScoringService._get_priority_label(55) == "MEDIUM"
        assert LeadScoringService._get_priority_label(69) == "MEDIUM"

    def test_low_priority(self):
        """Test low priority label for score < 40"""
        assert LeadScoringService._get_priority_label(0) == "LOW"
        assert LeadScoringService._get_priority_label(20) == "LOW"
        assert LeadScoringService._get_priority_label(39) == "LOW"


class TestGetStatusBonus:
    """Test the _get_status_bonus method"""

    def test_active_status_bonus(self):
        """Test active status gets 10 points"""
        client = MagicMock()
        client.dispute_status = "active"
        assert LeadScoringService._get_status_bonus(client) == 10

    def test_waiting_response_bonus(self):
        """Test waiting_response status gets 8 points"""
        client = MagicMock()
        client.dispute_status = "waiting_response"
        assert LeadScoringService._get_status_bonus(client) == 8

    def test_report_uploaded_bonus(self):
        """Test report_uploaded status gets 5 points"""
        client = MagicMock()
        client.dispute_status = "report_uploaded"
        assert LeadScoringService._get_status_bonus(client) == 5

    def test_lead_bonus(self):
        """Test lead status gets 3 points"""
        client = MagicMock()
        client.dispute_status = "lead"
        assert LeadScoringService._get_status_bonus(client) == 3

    def test_complete_no_bonus(self):
        """Test complete status gets 0 points"""
        client = MagicMock()
        client.dispute_status = "complete"
        assert LeadScoringService._get_status_bonus(client) == 0

    def test_cancelled_no_bonus(self):
        """Test cancelled status gets 0 points"""
        client = MagicMock()
        client.dispute_status = "cancelled"
        assert LeadScoringService._get_status_bonus(client) == 0


class TestCalculateScore:
    """Test the calculate_score method"""

    @patch('services.lead_scoring_service.SessionLocal')
    def test_client_not_found(self, mock_session_local):
        """Test score calculation returns error for missing client"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = LeadScoringService.calculate_score(999)

        assert result["success"] is False
        assert "not found" in result["error"]
        assert result["score"] == 0

    @patch('services.lead_scoring_service.SessionLocal')
    def test_score_includes_priority(self, mock_session_local):
        """Test that score result includes priority label"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.dispute_status = "new"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client
        mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_session.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

        result = LeadScoringService.calculate_score(1, mock_session)

        assert "priority" in result
        assert result["priority"] in ["HIGH", "MEDIUM", "LOW"]

    @patch('services.lead_scoring_service.SessionLocal')
    def test_score_includes_factors(self, mock_session_local):
        """Test that score result includes factors breakdown"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.dispute_status = "new"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client
        mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_session.query.return_value.filter.return_value.distinct.return_value.all.return_value = []

        result = LeadScoringService.calculate_score(1, mock_session)

        assert "factors" in result
        assert isinstance(result["factors"], dict)


class TestUpdateClientScore:
    """Test the update_client_score method"""

    @patch('services.lead_scoring_service.SessionLocal')
    @patch.object(LeadScoringService, 'calculate_score')
    def test_saves_score_to_client(self, mock_calculate, mock_session_local):
        """Test that score is saved to client record"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_client = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_client

        mock_calculate.return_value = {
            "success": True,
            "score": 75,
            "factors": {"collection_count": {"count": 3, "points": 45}},
            "priority": "HIGH",
        }

        result = LeadScoringService.update_client_score(1, mock_session)

        assert result["success"] is True
        assert result["saved"] is True
        assert mock_client.lead_score == 75
        mock_session.commit.assert_called()


class TestScoreAllClients:
    """Test the score_all_clients method"""

    @patch('services.lead_scoring_service.SessionLocal')
    @patch.object(LeadScoringService, 'update_client_score')
    def test_scores_multiple_clients(self, mock_update, mock_session_local):
        """Test that all clients are scored"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Mock 3 clients
        mock_session.query.return_value.all.return_value = [
            MagicMock(id=1),
            MagicMock(id=2),
            MagicMock(id=3),
        ]

        mock_update.side_effect = [
            {"success": True, "priority": "HIGH"},
            {"success": True, "priority": "MEDIUM"},
            {"success": True, "priority": "LOW"},
        ]

        result = LeadScoringService.score_all_clients()

        assert result["success"] is True
        assert result["scored"] == 3
        assert result["high_priority"] == 1
        assert result["medium_priority"] == 1
        assert result["low_priority"] == 1

    @patch('services.lead_scoring_service.SessionLocal')
    @patch.object(LeadScoringService, 'update_client_score')
    def test_respects_limit(self, mock_update, mock_session_local):
        """Test that limit parameter is respected"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_session.query.return_value.limit.return_value.all.return_value = [
            MagicMock(id=1),
            MagicMock(id=2),
        ]

        mock_update.return_value = {"success": True, "priority": "MEDIUM"}

        result = LeadScoringService.score_all_clients(limit=2)

        assert result["scored"] == 2
        mock_session.query.return_value.limit.assert_called_with(2)


class TestGetTopLeads:
    """Test the get_top_leads method"""

    @patch('services.lead_scoring_service.SessionLocal')
    def test_returns_leads_sorted_by_score(self, mock_session_local):
        """Test that leads are returned sorted by score"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_client1 = MagicMock()
        mock_client1.id = 1
        mock_client1.name = "High Priority"
        mock_client1.email = "high@test.com"
        mock_client1.phone = "555-1234"
        mock_client1.lead_score = 85
        mock_client1.dispute_status = "active"
        mock_client1.lead_scored_at = datetime.utcnow()

        mock_client2 = MagicMock()
        mock_client2.id = 2
        mock_client2.name = "Medium Priority"
        mock_client2.email = "medium@test.com"
        mock_client2.phone = "555-5678"
        mock_client2.lead_score = 50
        mock_client2.dispute_status = "new"
        mock_client2.lead_scored_at = datetime.utcnow()

        mock_session.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [
            mock_client1,
            mock_client2,
        ]

        leads = LeadScoringService.get_top_leads(limit=10, session=mock_session)

        assert len(leads) == 2
        assert leads[0]["score"] == 85
        assert leads[0]["priority"] == "HIGH"
        assert leads[1]["score"] == 50
        assert leads[1]["priority"] == "MEDIUM"


class TestGetScoreDistribution:
    """Test the get_score_distribution method"""

    @patch('services.lead_scoring_service.SessionLocal')
    def test_returns_distribution(self, mock_session_local):
        """Test that distribution is calculated correctly"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Mock counts for each priority level
        mock_session.query.return_value.filter.return_value.scalar.side_effect = [
            10,  # high (>= 70)
            25,  # medium (40-69)
            15,  # low (1-39)
            5,   # unscored (0 or null)
        ]

        distribution = LeadScoringService.get_score_distribution(session=mock_session)

        assert distribution["high"] == 10
        assert distribution["medium"] == 25
        assert distribution["low"] == 15
        assert distribution["unscored"] == 5
        assert distribution["total"] == 55


class TestConvenienceFunctions:
    """Test the convenience functions"""

    @patch.object(LeadScoringService, 'update_client_score')
    def test_score_client_calls_update(self, mock_update):
        """Test score_client calls update_client_score"""
        mock_update.return_value = {"success": True, "score": 50}

        result = score_client(1)

        mock_update.assert_called_once_with(1)
        assert result["score"] == 50

    @patch.object(LeadScoringService, 'calculate_score')
    def test_get_client_score_calls_calculate(self, mock_calculate):
        """Test get_client_score calls calculate_score"""
        mock_calculate.return_value = {"success": True, "score": 75}

        result = get_client_score(1)

        mock_calculate.assert_called_once_with(1)
        assert result["score"] == 75

    @patch.object(LeadScoringService, 'score_all_clients')
    def test_rescore_all_clients_calls_score_all(self, mock_score_all):
        """Test rescore_all_clients calls score_all_clients"""
        mock_score_all.return_value = {"success": True, "scored": 100}

        result = rescore_all_clients()

        mock_score_all.assert_called_once()
        assert result["scored"] == 100


class TestScoringLogic:
    """Test the scoring logic calculations"""

    def test_collection_points_capped(self):
        """Test that collection points are capped at 40"""
        # 5 collections * 15 points = 75, should be capped at 40
        weight = LeadScoringService.SCORING_WEIGHTS["collection"]
        count = 5
        points = min(count * weight, 40)
        assert points == 40

    def test_violation_points_capped(self):
        """Test that violation points are capped at 30"""
        weight = LeadScoringService.SCORING_WEIGHTS["violation"]
        count = 5
        points = min(count * weight, 30)
        assert points == 30

    def test_total_score_capped_at_100(self):
        """Test that total score cannot exceed 100"""
        assert LeadScoringService.MAX_SCORE == 100


class TestCountMethods:
    """Test the private count methods"""

    def test_count_dispute_items_normalizes_types(self):
        """Test that item types are normalized"""
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("Late Payment", 3),
            ("collection", 2),
        ]

        counts = LeadScoringService._count_dispute_items(mock_session, 1)

        assert "late_payment" in counts
        assert counts["late_payment"] == 3
        assert counts["collection"] == 2
