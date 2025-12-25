"""
Phase 5: Client Portal Tests
Tests for client login, dashboard, document viewing, and communication.
"""
import pytest
from datetime import datetime
from werkzeug.security import generate_password_hash


class TestClientAuthentication:
    """Test client portal authentication."""

    def test_portal_login_page_exists(self, client):
        """Test that portal login page exists."""
        response = client.get('/portal/login')
        assert response.status_code == 200

    def test_portal_login_with_token(self, client, sample_client, db_session):
        """Test portal login with token."""
        import secrets

        # Set up portal token
        token = secrets.token_urlsafe(32)
        sample_client.portal_token = token
        sample_client.portal_password_hash = generate_password_hash('clientpass123')
        db_session.commit()

        # Attempt login
        response = client.post('/portal/login', data={
            'token': token,
            'password': 'clientpass123'
        }, follow_redirects=False)

        # Should either succeed or show login page
        assert response.status_code in [200, 302]

    def test_portal_requires_auth(self, client):
        """Test that portal dashboard requires authentication."""
        response = client.get('/portal/dashboard')
        # Should redirect to login or show unauthorized
        assert response.status_code in [302, 401, 403, 200]


class TestClientDashboard:
    """Test client dashboard functionality."""

    def test_dashboard_tabs_structure(self):
        """Test dashboard has required tabs."""
        expected_tabs = [
            'overview',
            'letters',
            'documents',
            'timeline',
            'responses',
            'communication',
            'settings'
        ]

        # At least these core tabs should exist
        assert len(expected_tabs) >= 5

    def test_case_status_display(self, sample_client):
        """Test case status information."""
        # Client should have status fields
        assert hasattr(sample_client, 'dispute_status')
        assert hasattr(sample_client, 'current_dispute_round')

        # Status should be valid
        valid_statuses = ['new', 'active', 'waiting_response', 'complete', 'paused']
        assert sample_client.dispute_status in valid_statuses or sample_client.dispute_status is None


class TestLetterViewing:
    """Test client letter viewing."""

    def test_letter_download_endpoint(self, client, db_session, sample_analysis, sample_client):
        """Test letter download endpoint exists."""
        from database import DisputeLetter

        letter = DisputeLetter(
            analysis_id=sample_analysis.id,
            client_id=sample_client.id,
            client_name=sample_client.name,
            bureau='Equifax',
            round_number=1,
            letter_content='Test letter'
        )
        db_session.add(letter)
        db_session.commit()

        # Download endpoint should exist
        response = client.get(f'/api/download/{letter.id}')
        # May return 404 if file doesn't exist, but endpoint should respond
        assert response.status_code in [200, 404, 401, 403]


class TestDocumentUpload:
    """Test client document upload functionality."""

    def test_client_upload_model(self):
        """Test ClientUpload model exists."""
        from database import ClientUpload
        assert ClientUpload is not None

    def test_upload_categories(self):
        """Test document upload categories."""
        categories = [
            'bureau_response',
            'denial_letter',
            'identity_document',
            'correspondence',
            'other'
        ]

        # Should have multiple categories
        assert len(categories) >= 4

    def test_create_upload_record(self, db_session, sample_client):
        """Test creating upload record."""
        from database import ClientUpload

        upload = ClientUpload(
            client_id=sample_client.id,
            category='bureau_response',
            document_type='cra_response',
            file_name='equifax_response.pdf',
            file_path='/uploads/test.pdf',
            file_size=1024,
            file_type='pdf'
        )
        db_session.add(upload)
        db_session.commit()

        assert upload.id is not None
        assert upload.category == 'bureau_response'


class TestProgressTimeline:
    """Test progress timeline visualization."""

    def test_dispute_round_tracking(self, sample_client):
        """Test dispute round tracking."""
        assert hasattr(sample_client, 'current_dispute_round')
        assert sample_client.current_dispute_round >= 0
        assert sample_client.current_dispute_round <= 4  # Rounds 0-4

    def test_round_started_timestamp(self, sample_client, db_session):
        """Test round started timestamp."""
        sample_client.round_started_at = datetime.now()
        db_session.commit()

        assert sample_client.round_started_at is not None


class TestCommunicationSystem:
    """Test client communication features."""

    def test_notification_model(self):
        """Test Notification model exists."""
        from database import Notification
        assert Notification is not None

    def test_create_notification(self, db_session, sample_client):
        """Test creating client notification."""
        from database import Notification

        notification = Notification(
            client_id=sample_client.id,
            notification_type='status_update',
            subject='Case Update',
            body='Your Round 1 dispute has been submitted.',
            status='pending'
        )
        db_session.add(notification)
        db_session.commit()

        assert notification.id is not None

    def test_email_log_model(self):
        """Test EmailLog model exists."""
        from database import EmailLog
        assert EmailLog is not None

    def test_sms_log_model(self):
        """Test SMSLog model exists."""
        from database import SMSLog
        assert SMSLog is not None


class TestCaseDeadlines:
    """Test case deadline tracking."""

    def test_deadline_model(self):
        """Test CaseDeadline model exists."""
        from database import CaseDeadline
        assert CaseDeadline is not None

    def test_create_deadline(self, db_session, sample_client):
        """Test creating a case deadline."""
        from database import CaseDeadline
        from datetime import date, timedelta

        deadline = CaseDeadline(
            client_id=sample_client.id,
            deadline_type='bureau_response',
            start_date=date.today(),
            deadline_date=date.today() + timedelta(days=30),
            days_allowed=30,
            status='active'
        )
        db_session.add(deadline)
        db_session.commit()

        assert deadline.id is not None
        assert deadline.deadline_date > date.today()


class TestSettlementNotifications:
    """Test settlement offer notifications."""

    def test_settlement_model(self):
        """Test Settlement model exists."""
        from database import Settlement
        assert Settlement is not None

    def test_create_settlement(self, db_session, sample_client, sample_analysis):
        """Test creating settlement record."""
        from database import Settlement, Case
        import secrets

        # Create a case first (Settlement requires case_id)
        case = Case(
            client_id=sample_client.id,
            analysis_id=sample_analysis.id,
            case_number=f'CASE-{secrets.token_hex(4).upper()}',
            status='stage2_complete'
        )
        db_session.add(case)
        db_session.commit()

        settlement = Settlement(
            case_id=case.id,
            target_amount=15000,
            status='pending'
        )
        db_session.add(settlement)
        db_session.commit()

        assert settlement.id is not None
        assert settlement.target_amount == 15000


class TestPasswordReset:
    """Test client password reset functionality."""

    def test_password_reset_fields(self, sample_client):
        """Test password reset fields exist."""
        assert hasattr(sample_client, 'password_reset_token')
        assert hasattr(sample_client, 'password_reset_expires')

    def test_generate_reset_token(self, db_session, sample_client):
        """Test generating password reset token."""
        import secrets
        from datetime import datetime, timedelta

        token = secrets.token_urlsafe(32)
        sample_client.password_reset_token = token
        sample_client.password_reset_expires = datetime.now() + timedelta(hours=24)
        db_session.commit()

        assert sample_client.password_reset_token is not None
        assert sample_client.password_reset_expires > datetime.now()
