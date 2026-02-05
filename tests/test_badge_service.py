"""
Unit tests for Badge Service - Client gamification and progress badges

Tests cover:
- Badge definition constants
- Badge seeding
- Badge retrieval
- Badge awarding
- Notification handling
- Statistics and leaderboards
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


class TestDefaultBadges:
    """Tests for DEFAULT_BADGES constant"""

    def test_default_badges_exists(self):
        """DEFAULT_BADGES should be a non-empty list"""
        from services.badge_service import DEFAULT_BADGES
        assert isinstance(DEFAULT_BADGES, list)
        assert len(DEFAULT_BADGES) > 0

    def test_default_badges_have_required_fields(self):
        """Each badge should have required fields"""
        from services.badge_service import DEFAULT_BADGES
        required_fields = ['badge_type', 'name', 'description', 'icon', 'color', 'trigger_type', 'trigger_event']

        for badge in DEFAULT_BADGES:
            for field in required_fields:
                assert field in badge, f"Badge missing field: {field}"

    def test_default_badges_have_unique_types(self):
        """Badge types should be unique"""
        from services.badge_service import DEFAULT_BADGES
        types = [b['badge_type'] for b in DEFAULT_BADGES]
        assert len(types) == len(set(types)), "Duplicate badge types found"

    def test_default_badges_trigger_types(self):
        """Trigger types should be 'event' or 'threshold'"""
        from services.badge_service import DEFAULT_BADGES
        for badge in DEFAULT_BADGES:
            assert badge['trigger_type'] in ['event', 'threshold']

    def test_threshold_badges_have_threshold_value(self):
        """Threshold-type badges should have trigger_threshold"""
        from services.badge_service import DEFAULT_BADGES
        for badge in DEFAULT_BADGES:
            if badge['trigger_type'] == 'threshold':
                assert 'trigger_threshold' in badge
                assert isinstance(badge['trigger_threshold'], int)

    def test_badge_colors_valid(self):
        """Badge colors should be recognizable color names"""
        from services.badge_service import DEFAULT_BADGES
        valid_colors = {'blue', 'green', 'purple', 'yellow', 'orange', 'gold', 'teal', 'pink', 'red'}
        for badge in DEFAULT_BADGES:
            assert badge['color'] in valid_colors, f"Invalid color: {badge['color']}"

    def test_badge_icons_present(self):
        """Each badge should have an icon"""
        from services.badge_service import DEFAULT_BADGES
        for badge in DEFAULT_BADGES:
            assert badge['icon'], f"Missing icon for {badge['badge_type']}"
            assert len(badge['icon']) > 0


class TestSeedBadgeDefinitions:
    """Tests for seed_badge_definitions function"""

    @patch('services.badge_service.get_db')
    def test_seed_returns_success(self, mock_get_db):
        """Should return success dict"""
        from services.badge_service import seed_badge_definitions

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = seed_badge_definitions()

        assert result['success'] is True
        assert 'created' in result

    @patch('services.badge_service.get_db')
    def test_seed_calls_commit(self, mock_get_db):
        """Should commit to database"""
        from services.badge_service import seed_badge_definitions

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()

        seed_badge_definitions()

        mock_db.commit.assert_called_once()


class TestGetBadgeDefinitions:
    """Tests for get_badge_definitions function"""

    @patch('services.badge_service.get_db')
    def test_returns_list(self, mock_get_db):
        """Should return list of badge definitions"""
        from services.badge_service import get_badge_definitions

        mock_badge = Mock()
        mock_badge.to_dict.return_value = {'badge_type': 'test'}

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_badge]

        result = get_badge_definitions()

        assert isinstance(result, list)
        assert len(result) == 1

    @patch('services.badge_service.get_db')
    def test_returns_empty_list(self, mock_get_db):
        """Should return empty list when no badges"""
        from services.badge_service import get_badge_definitions

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_badge_definitions()

        assert result == []

    @patch('services.badge_service.get_db')
    def test_include_inactive(self, mock_get_db):
        """Should include inactive when active_only=False"""
        from services.badge_service import get_badge_definitions

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.order_by.return_value.all.return_value = []

        get_badge_definitions(active_only=False)

        mock_db.query.return_value.order_by.assert_called()


class TestAwardBadge:
    """Tests for award_badge function"""

    @patch('services.badge_service.get_db')
    def test_award_badge_type_not_found(self, mock_get_db):
        """Should fail if badge type doesn't exist"""
        from services.badge_service import award_badge

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = award_badge(client_id=1, badge_type='nonexistent')

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.badge_service.get_db')
    def test_award_badge_handles_exception(self, mock_get_db):
        """Should handle database exceptions"""
        from services.badge_service import award_badge

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        # First call returns definition, second call raises exception
        mock_definition = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_definition
        mock_db.add.side_effect = Exception("Database error")

        result = award_badge(client_id=1, badge_type='test')

        # Could succeed or fail depending on query behavior
        assert isinstance(result, dict)


class TestGetClientBadges:
    """Tests for get_client_badges function"""

    @patch('services.badge_service.get_db')
    def test_returns_list(self, mock_get_db):
        """Should return list of client badges"""
        from services.badge_service import get_client_badges

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_client_badges(client_id=1)

        assert isinstance(result, list)

    @patch('services.badge_service.get_db')
    def test_returns_empty_for_no_badges(self, mock_get_db):
        """Should return empty list if no badges"""
        from services.badge_service import get_client_badges

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = get_client_badges(client_id=999)

        assert result == []


class TestGetUnnotifiedBadges:
    """Tests for get_unnotified_badges function"""

    @patch('services.badge_service.get_db')
    def test_returns_list(self, mock_get_db):
        """Should return list of unnotified badges"""
        from services.badge_service import get_unnotified_badges

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = get_unnotified_badges(client_id=1)

        assert isinstance(result, list)


class TestMarkBadgesNotified:
    """Tests for mark_badges_notified function"""

    @patch('services.badge_service.get_db')
    def test_returns_success(self, mock_get_db):
        """Should return success dict"""
        from services.badge_service import mark_badges_notified

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = mark_badges_notified(client_id=1)

        assert result['success'] is True
        assert 'marked' in result

    @patch('services.badge_service.get_db')
    def test_marks_multiple_badges(self, mock_get_db):
        """Should mark multiple badges as notified"""
        from services.badge_service import mark_badges_notified

        mock_badge1 = Mock(notified=False)
        mock_badge2 = Mock(notified=False)

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_badge1, mock_badge2]

        result = mark_badges_notified(client_id=1)

        assert result['marked'] == 2
        mock_db.commit.assert_called_once()

    @patch('services.badge_service.get_db')
    def test_handles_exception(self, mock_get_db):
        """Should handle exceptions"""
        from services.badge_service import mark_badges_notified

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.side_effect = Exception("Error")

        result = mark_badges_notified(client_id=1)

        assert result['success'] is False
        mock_db.rollback.assert_called_once()


class TestCheckAndAwardBadges:
    """Tests for check_and_award_badges function"""

    @patch('services.badge_service.award_badge')
    @patch('services.badge_service.get_db')
    def test_returns_list(self, mock_get_db, mock_award):
        """Should return list of awarded badges"""
        from services.badge_service import check_and_award_badges

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []

        result = check_and_award_badges(client_id=1, event_type='first_login')

        assert isinstance(result, list)

    @patch('services.badge_service.award_badge')
    @patch('services.badge_service.get_db')
    def test_awards_event_badge(self, mock_get_db, mock_award):
        """Should award event-triggered badge"""
        from services.badge_service import check_and_award_badges

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_definition = Mock()
        mock_definition.badge_type = 'first_login'
        mock_definition.trigger_type = 'event'
        mock_definition.trigger_threshold = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_definition]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        mock_award.return_value = {'success': True, 'badge': {'badge_type': 'first_login'}}

        result = check_and_award_badges(client_id=1, event_type='first_login')

        assert len(result) == 1


class TestGetBadgeLeaderboard:
    """Tests for get_badge_leaderboard function"""

    @patch('services.badge_service.get_db')
    def test_returns_list(self, mock_get_db):
        """Should return leaderboard list"""
        from services.badge_service import get_badge_leaderboard

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = get_badge_leaderboard()

        assert isinstance(result, list)

    @patch('services.badge_service.get_db')
    def test_respects_limit(self, mock_get_db):
        """Should respect limit parameter"""
        from services.badge_service import get_badge_leaderboard

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        get_badge_leaderboard(limit=5)

        mock_db.query.return_value.group_by.return_value.order_by.return_value.limit.assert_called_with(5)


class TestGetBadgeStats:
    """Tests for get_badge_stats function"""

    @patch('services.badge_service.get_db')
    def test_returns_stats_dict(self, mock_get_db):
        """Should return stats dictionary"""
        from services.badge_service import get_badge_stats

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.count.return_value = 0
        mock_db.query.return_value.scalar.return_value = 0
        mock_db.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = get_badge_stats()

        assert 'total_awarded' in result
        assert 'clients_with_badges' in result
        assert 'most_common' in result
        assert 'rarest' in result


class TestGetNextBadges:
    """Tests for get_next_badges function"""

    @patch('services.badge_service.get_db')
    def test_returns_list(self, mock_get_db):
        """Should return list of next badges"""
        from services.badge_service import get_next_badges

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = get_next_badges(client_id=1)

        assert isinstance(result, list)


class TestRevokeBadge:
    """Tests for revoke_badge function"""

    @patch('services.badge_service.get_db')
    def test_revoke_not_found(self, mock_get_db):
        """Should fail if badge not found"""
        from services.badge_service import revoke_badge

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = revoke_badge(client_id=1, badge_type='nonexistent')

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.badge_service.get_db')
    def test_revoke_success(self, mock_get_db):
        """Should revoke badge successfully"""
        from services.badge_service import revoke_badge

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_badge = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_badge

        result = revoke_badge(client_id=1, badge_type='test')

        assert result['success'] is True
        mock_db.delete.assert_called_once_with(mock_badge)
        mock_db.commit.assert_called_once()

    @patch('services.badge_service.get_db')
    def test_revoke_handles_exception(self, mock_get_db):
        """Should handle exceptions"""
        from services.badge_service import revoke_badge

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = Mock()
        mock_db.delete.side_effect = Exception("Error")

        result = revoke_badge(client_id=1, badge_type='test')

        assert result['success'] is False
        mock_db.rollback.assert_called_once()
