"""
Unit tests for Testimonial Service - Client reviews and testimonials

Tests cover:
- Creating testimonial requests
- Submitting testimonials
- Listing and filtering
- Approval workflow
- Public/portal display
- Statistics
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock


class TestCreateTestimonialRequest:
    """Tests for create_testimonial_request function"""

    @patch('services.testimonial_service.send_email')
    @patch('services.testimonial_service.get_client_success_metrics')
    @patch('services.testimonial_service.get_db')
    def test_returns_success(self, mock_get_db, mock_metrics, mock_email):
        """Should return success dict with token"""
        from services.testimonial_service import create_testimonial_request

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_client = Mock()
        mock_client.first_name = 'John'
        mock_client.last_name = 'Doe'
        mock_client.email = 'john@example.com'

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_client, None]
        mock_metrics.return_value = {'total_deleted': 10}

        result = create_testimonial_request(client_id=1)

        assert result['success'] is True
        assert 'token' in result
        mock_db.commit.assert_called()

    @patch('services.testimonial_service.get_db')
    def test_fails_client_not_found(self, mock_get_db):
        """Should fail if client not found"""
        from services.testimonial_service import create_testimonial_request

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = create_testimonial_request(client_id=999)

        assert result['success'] is False
        assert 'not found' in result['error']


class TestSubmitTestimonial:
    """Tests for submit_testimonial function"""

    @patch('services.testimonial_service.get_db')
    def test_invalid_token(self, mock_get_db):
        """Should fail with invalid token"""
        from services.testimonial_service import submit_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = submit_testimonial(token='invalid', rating=5, testimonial_text='Great!')

        assert result['success'] is False
        assert 'Invalid' in result['error']

    @patch('services.testimonial_service.get_db')
    def test_invalid_rating(self, mock_get_db):
        """Should fail with invalid rating"""
        from services.testimonial_service import submit_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_testimonial = Mock()
        mock_testimonial.submitted_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_testimonial

        result = submit_testimonial(token='valid', rating=6, testimonial_text='Great!')

        assert result['success'] is False
        assert 'between 1 and 5' in result['error']

    @patch('services.testimonial_service.get_db')
    def test_already_submitted(self, mock_get_db):
        """Should fail if already submitted"""
        from services.testimonial_service import submit_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_testimonial = Mock()
        mock_testimonial.submitted_at = datetime.utcnow()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_testimonial

        result = submit_testimonial(token='valid', rating=5, testimonial_text='Great!')

        assert result['success'] is False
        assert 'already submitted' in result['error']


class TestGetTestimonialByToken:
    """Tests for get_testimonial_by_token function"""

    @patch('services.testimonial_service.get_db')
    def test_returns_none_invalid_token(self, mock_get_db):
        """Should return None for invalid token"""
        from services.testimonial_service import get_testimonial_by_token

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_testimonial_by_token('invalid')

        assert result is None

    @patch('services.testimonial_service.get_db')
    def test_returns_testimonial_data(self, mock_get_db):
        """Should return testimonial with client info"""
        from services.testimonial_service import get_testimonial_by_token

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_testimonial = Mock()
        mock_testimonial.client_id = 1
        mock_testimonial.submitted_at = None
        mock_testimonial.to_dict.return_value = {'id': 1}

        mock_client = Mock()
        mock_client.first_name = 'John'

        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_testimonial, mock_client]

        result = get_testimonial_by_token('valid')

        assert result is not None
        assert result['client_first_name'] == 'John'


class TestListTestimonials:
    """Tests for list_testimonials function"""

    @patch('services.testimonial_service.get_db')
    def test_returns_paginated_list(self, mock_get_db):
        """Should return paginated results"""
        from services.testimonial_service import list_testimonials

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_query = mock_db.query.return_value.filter.return_value
        mock_query.count.return_value = 0
        mock_query.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []

        result = list_testimonials()

        assert 'testimonials' in result
        assert 'total' in result
        assert 'limit' in result
        assert 'offset' in result


class TestApproveTestimonial:
    """Tests for approve_testimonial function"""

    @patch('services.testimonial_service.get_db')
    def test_not_found(self, mock_get_db):
        """Should fail if not found"""
        from services.testimonial_service import approve_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = approve_testimonial(testimonial_id=999, staff_id=1)

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.testimonial_service.get_db')
    def test_approves_successfully(self, mock_get_db):
        """Should approve testimonial"""
        from services.testimonial_service import approve_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_testimonial = Mock()
        mock_testimonial.to_dict.return_value = {}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_testimonial

        result = approve_testimonial(testimonial_id=1, staff_id=1)

        assert result['success'] is True
        assert mock_testimonial.status == 'approved'
        mock_db.commit.assert_called()


class TestRejectTestimonial:
    """Tests for reject_testimonial function"""

    @patch('services.testimonial_service.get_db')
    def test_not_found(self, mock_get_db):
        """Should fail if not found"""
        from services.testimonial_service import reject_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = reject_testimonial(testimonial_id=999, staff_id=1)

        assert result['success'] is False

    @patch('services.testimonial_service.get_db')
    def test_rejects_successfully(self, mock_get_db):
        """Should reject testimonial"""
        from services.testimonial_service import reject_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_testimonial = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_testimonial

        result = reject_testimonial(testimonial_id=1, staff_id=1)

        assert result['success'] is True
        assert mock_testimonial.status == 'rejected'


class TestFeatureTestimonial:
    """Tests for feature_testimonial function"""

    @patch('services.testimonial_service.get_db')
    def test_not_found(self, mock_get_db):
        """Should fail if not found"""
        from services.testimonial_service import feature_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = feature_testimonial(testimonial_id=999)

        assert result['success'] is False

    @patch('services.testimonial_service.get_db')
    def test_requires_approval(self, mock_get_db):
        """Should require approved status"""
        from services.testimonial_service import feature_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_testimonial = Mock()
        mock_testimonial.status = 'pending'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_testimonial

        result = feature_testimonial(testimonial_id=1)

        assert result['success'] is False
        assert 'approved' in result['error']

    @patch('services.testimonial_service.get_db')
    def test_features_successfully(self, mock_get_db):
        """Should feature approved testimonial"""
        from services.testimonial_service import feature_testimonial

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_testimonial = Mock()
        mock_testimonial.status = 'approved'
        mock_testimonial.to_dict.return_value = {}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_testimonial

        result = feature_testimonial(testimonial_id=1)

        assert result['success'] is True
        assert mock_testimonial.status == 'featured'


class TestUpdateDisplayName:
    """Tests for update_display_name function"""

    @patch('services.testimonial_service.get_db')
    def test_not_found(self, mock_get_db):
        """Should fail if not found"""
        from services.testimonial_service import update_display_name

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = update_display_name(testimonial_id=999, display_name='Test')

        assert result['success'] is False

    @patch('services.testimonial_service.get_db')
    def test_updates_successfully(self, mock_get_db):
        """Should update display name"""
        from services.testimonial_service import update_display_name

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        mock_testimonial = Mock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_testimonial

        result = update_display_name(testimonial_id=1, display_name='John D.')

        assert result['success'] is True
        assert mock_testimonial.display_name == 'John D.'


class TestGetPublicTestimonials:
    """Tests for get_public_testimonials function"""

    @patch('services.testimonial_service.get_db')
    def test_returns_list(self, mock_get_db):
        """Should return list of testimonials"""
        from services.testimonial_service import get_public_testimonials

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = get_public_testimonials()

        assert isinstance(result, list)

    @patch('services.testimonial_service.get_db')
    def test_respects_limit(self, mock_get_db):
        """Should respect limit parameter"""
        from services.testimonial_service import get_public_testimonials

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        get_public_testimonials(limit=5)

        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.assert_called_with(5)


class TestGetPortalTestimonials:
    """Tests for get_portal_testimonials function"""

    @patch('services.testimonial_service.get_db')
    def test_returns_list(self, mock_get_db):
        """Should return list for portal"""
        from services.testimonial_service import get_portal_testimonials

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = get_portal_testimonials()

        assert isinstance(result, list)


class TestGetTestimonialStats:
    """Tests for get_testimonial_stats function"""

    @patch('services.testimonial_service.get_db')
    def test_returns_stats(self, mock_get_db):
        """Should return stats dictionary"""
        from services.testimonial_service import get_testimonial_stats

        mock_db = MagicMock()
        mock_get_db.return_value = mock_db
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.scalar.return_value = None

        result = get_testimonial_stats()

        assert 'total' in result
        assert 'pending' in result
        assert 'approved' in result
        assert 'average_rating' in result
        assert 'rating_distribution' in result


class TestBulkRequestTestimonials:
    """Tests for bulk_request_testimonials function"""

    @patch('services.testimonial_service.create_testimonial_request')
    def test_sends_to_multiple(self, mock_create):
        """Should send to multiple clients"""
        from services.testimonial_service import bulk_request_testimonials

        mock_create.return_value = {'success': True}

        result = bulk_request_testimonials(client_ids=[1, 2, 3])

        assert result['success'] is True
        assert result['sent'] == 3
        assert mock_create.call_count == 3

    @patch('services.testimonial_service.create_testimonial_request')
    def test_tracks_failures(self, mock_create):
        """Should track failed requests"""
        from services.testimonial_service import bulk_request_testimonials

        mock_create.side_effect = [
            {'success': True},
            {'success': False, 'error': 'Not found'},
            {'success': True}
        ]

        result = bulk_request_testimonials(client_ids=[1, 2, 3])

        assert result['sent'] == 2
        assert result['failed'] == 1

    @patch('services.testimonial_service.create_testimonial_request')
    def test_handles_empty_list(self, mock_create):
        """Should handle empty list"""
        from services.testimonial_service import bulk_request_testimonials

        result = bulk_request_testimonials(client_ids=[])

        assert result['success'] is True
        assert result['sent'] == 0
        mock_create.assert_not_called()
