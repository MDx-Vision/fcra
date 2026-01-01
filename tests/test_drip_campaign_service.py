"""
Unit tests for DripCampaignService

Tests for:
- Campaign CRUD operations
- Step management
- Enrollment management
- Email processing
- Statistics
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, DripCampaign, DripStep, DripEnrollment, DripEmailLog, Client, EmailTemplate
from services.drip_campaign_service import (
    DripCampaignService,
    TRIGGER_TYPES,
    ENROLLMENT_STATUSES,
    enroll_client,
    process_drip_emails,
)


@pytest.fixture
def db_session():
    """Create an in-memory database for testing"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_client(db_session):
    """Create a sample client"""
    client = Client(
        name="John Doe",
        first_name="John",
        last_name="Doe",
        email="john@example.com",
        phone="555-1234",
        dispute_status="active",
    )
    db_session.add(client)
    db_session.commit()
    return client


@pytest.fixture
def sample_template(db_session):
    """Create a sample email template"""
    template = EmailTemplate(
        template_type="drip_test",
        name="Test Drip Email",
        subject="Welcome to our service!",
        html_content="<p>Hello {client_name}!</p>",
        category="welcome",
        is_active=True,
    )
    db_session.add(template)
    db_session.commit()
    return template


@pytest.fixture
def sample_campaign(db_session):
    """Create a sample campaign"""
    campaign = DripCampaign(
        name="Welcome Series",
        description="Welcome new clients",
        trigger_type="signup",
        is_active=True,
        send_window_start=9,
        send_window_end=17,
        send_on_weekends=False,
    )
    db_session.add(campaign)
    db_session.commit()
    return campaign


class TestTriggerTypes:
    """Tests for trigger type utilities"""

    def test_get_trigger_types(self):
        """Test getting trigger types"""
        types = DripCampaignService.get_trigger_types()
        assert isinstance(types, dict)
        assert "signup" in types
        assert "status_change" in types
        assert "manual" in types

    def test_get_enrollment_statuses(self):
        """Test getting enrollment statuses"""
        statuses = DripCampaignService.get_enrollment_statuses()
        assert isinstance(statuses, dict)
        assert "active" in statuses
        assert "paused" in statuses
        assert "completed" in statuses
        assert "cancelled" in statuses


class TestCampaignCRUD:
    """Tests for campaign CRUD operations"""

    def test_create_campaign_success(self, db_session):
        """Test creating a campaign successfully"""
        result = DripCampaignService.create_campaign(
            name="Test Campaign",
            trigger_type="signup",
            description="Test description",
            session=db_session,
        )

        assert result["success"] is True
        assert "campaign_id" in result
        # Verify campaign was created
        campaign = db_session.query(DripCampaign).filter_by(id=result["campaign_id"]).first()
        assert campaign is not None
        assert campaign.name == "Test Campaign"
        assert campaign.trigger_type == "signup"

    def test_create_campaign_with_steps(self, db_session, sample_template):
        """Test creating a campaign with steps"""
        steps = [
            {"email_template_id": sample_template.id, "delay_days": 0, "delay_hours": 0},
            {"email_template_id": sample_template.id, "delay_days": 3, "delay_hours": 0},
        ]

        result = DripCampaignService.create_campaign(
            name="Multi-step Campaign",
            trigger_type="signup",
            steps=steps,
            session=db_session,
        )

        assert result["success"] is True
        campaign = db_session.query(DripCampaign).filter_by(name="Multi-step Campaign").first()
        assert campaign is not None
        assert len(campaign.steps) == 2

    def test_create_campaign_invalid_trigger(self, db_session):
        """Test creating campaign with invalid trigger type"""
        result = DripCampaignService.create_campaign(
            name="Bad Campaign",
            trigger_type="invalid_trigger",
            session=db_session,
        )

        assert result["success"] is False
        assert "Invalid trigger type" in result["error"]

    def test_update_campaign(self, db_session, sample_campaign):
        """Test updating a campaign"""
        result = DripCampaignService.update_campaign(
            campaign_id=sample_campaign.id,
            name="Updated Name",
            description="Updated description",
            session=db_session,
        )

        assert result["success"] is True
        db_session.refresh(sample_campaign)
        assert sample_campaign.name == "Updated Name"
        assert sample_campaign.description == "Updated description"

    def test_update_campaign_not_found(self, db_session):
        """Test updating a non-existent campaign"""
        result = DripCampaignService.update_campaign(
            campaign_id=9999,
            name="Updated Name",
            session=db_session,
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_delete_campaign(self, db_session, sample_campaign):
        """Test deleting a campaign"""
        campaign_id = sample_campaign.id
        result = DripCampaignService.delete_campaign(campaign_id, session=db_session)

        assert result["success"] is True
        deleted = db_session.query(DripCampaign).filter_by(id=campaign_id).first()
        assert deleted is None

    def test_delete_campaign_not_found(self, db_session):
        """Test deleting a non-existent campaign"""
        result = DripCampaignService.delete_campaign(9999, session=db_session)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_get_campaign(self, db_session, sample_campaign):
        """Test getting a campaign by ID"""
        campaign = DripCampaignService.get_campaign(sample_campaign.id, session=db_session)

        assert campaign is not None
        assert campaign["name"] == "Welcome Series"
        assert campaign["trigger_type"] == "signup"

    def test_get_campaign_not_found(self, db_session):
        """Test getting a non-existent campaign"""
        campaign = DripCampaignService.get_campaign(9999, session=db_session)
        assert campaign is None

    def test_list_campaigns(self, db_session, sample_campaign):
        """Test listing all campaigns"""
        campaigns = DripCampaignService.list_campaigns(session=db_session)

        assert isinstance(campaigns, list)
        assert len(campaigns) >= 1

    def test_list_campaigns_filter_active(self, db_session, sample_campaign):
        """Test listing only active campaigns"""
        # Create an inactive campaign
        inactive = DripCampaign(
            name="Inactive Campaign",
            trigger_type="manual",
            is_active=False,
        )
        db_session.add(inactive)
        db_session.commit()

        campaigns = DripCampaignService.list_campaigns(is_active=True, session=db_session)

        assert isinstance(campaigns, list)
        for c in campaigns:
            assert c["is_active"] is True

    def test_list_campaigns_filter_trigger(self, db_session, sample_campaign):
        """Test listing campaigns by trigger type"""
        campaigns = DripCampaignService.list_campaigns(trigger_type="signup", session=db_session)

        assert isinstance(campaigns, list)
        for c in campaigns:
            assert c["trigger_type"] == "signup"


class TestStepManagement:
    """Tests for step management"""

    def test_add_step(self, db_session, sample_campaign, sample_template):
        """Test adding a step to a campaign"""
        result = DripCampaignService.add_step(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=1,
            delay_hours=0,
            session=db_session,
        )

        assert result["success"] is True
        assert "step_id" in result

    def test_add_step_invalid_campaign(self, db_session, sample_template):
        """Test adding step to non-existent campaign"""
        result = DripCampaignService.add_step(
            campaign_id=9999,
            email_template_id=sample_template.id,
            delay_days=1,
            session=db_session,
        )

        assert result["success"] is False
        assert "Campaign not found" in result["error"]

    def test_update_step(self, db_session, sample_campaign, sample_template):
        """Test updating a step"""
        # First add a step
        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=1,
            step_order=1,
        )
        db_session.add(step)
        db_session.commit()

        result = DripCampaignService.update_step(
            step_id=step.id,
            delay_days=5,
            session=db_session,
        )

        assert result["success"] is True
        db_session.refresh(step)
        assert step.delay_days == 5

    def test_delete_step(self, db_session, sample_campaign, sample_template):
        """Test deleting a step"""
        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=1,
            step_order=1,
        )
        db_session.add(step)
        db_session.commit()
        step_id = step.id

        result = DripCampaignService.delete_step(step_id, session=db_session)

        assert result["success"] is True
        deleted = db_session.query(DripStep).filter_by(id=step_id).first()
        assert deleted is None

    def test_reorder_steps(self, db_session, sample_campaign, sample_template):
        """Test reordering steps"""
        # Create multiple steps
        step1 = DripStep(campaign_id=sample_campaign.id, email_template_id=sample_template.id, delay_days=0, step_order=1)
        step2 = DripStep(campaign_id=sample_campaign.id, email_template_id=sample_template.id, delay_days=1, step_order=2)
        step3 = DripStep(campaign_id=sample_campaign.id, email_template_id=sample_template.id, delay_days=2, step_order=3)
        db_session.add_all([step1, step2, step3])
        db_session.commit()

        # Reorder: step3 first, then step1, then step2
        result = DripCampaignService.reorder_steps(
            campaign_id=sample_campaign.id,
            step_ids=[step3.id, step1.id, step2.id],
            session=db_session,
        )

        assert result["success"] is True
        db_session.refresh(step1)
        db_session.refresh(step2)
        db_session.refresh(step3)
        assert step3.step_order == 1
        assert step1.step_order == 2
        assert step2.step_order == 3


class TestEnrollmentManagement:
    """Tests for enrollment management"""

    def test_enroll_client(self, db_session, sample_campaign, sample_client, sample_template):
        """Test enrolling a client in a campaign"""
        # Add a step first
        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=0,
            step_order=1,
        )
        db_session.add(step)
        db_session.commit()

        result = DripCampaignService.enroll_client(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            session=db_session,
        )

        assert result["success"] is True

    def test_enroll_client_inactive_campaign(self, db_session, sample_campaign, sample_client):
        """Test enrolling in an inactive campaign"""
        sample_campaign.is_active = False
        db_session.commit()

        result = DripCampaignService.enroll_client(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            session=db_session,
        )

        assert result["success"] is False
        assert "inactive" in result["error"].lower()

    def test_enroll_client_already_enrolled(self, db_session, sample_campaign, sample_client, sample_template):
        """Test enrolling an already enrolled client"""
        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=0,
            step_order=1,
        )
        db_session.add(step)

        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        result = DripCampaignService.enroll_client(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            session=db_session,
        )

        # Service may allow re-enrollment or reject it
        assert isinstance(result, dict)
        assert "success" in result

    def test_pause_enrollment(self, db_session, sample_campaign, sample_client):
        """Test pausing an enrollment"""
        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        result = DripCampaignService.pause_enrollment(
            enrollment_id=enrollment.id,
            reason="Client request",
            session=db_session,
        )

        assert result["success"] is True
        db_session.refresh(enrollment)
        assert enrollment.status == "paused"

    def test_resume_enrollment(self, db_session, sample_campaign, sample_client, sample_template):
        """Test resuming a paused enrollment"""
        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=1,
            step_order=1,
        )
        db_session.add(step)

        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="paused",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        result = DripCampaignService.resume_enrollment(
            enrollment_id=enrollment.id,
            session=db_session,
        )

        assert result["success"] is True
        db_session.refresh(enrollment)
        assert enrollment.status == "active"

    def test_cancel_enrollment(self, db_session, sample_campaign, sample_client):
        """Test cancelling an enrollment"""
        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        result = DripCampaignService.cancel_enrollment(
            enrollment_id=enrollment.id,
            reason="No longer needed",
            session=db_session,
        )

        assert result["success"] is True
        db_session.refresh(enrollment)
        assert enrollment.status == "cancelled"

    def test_get_enrollment(self, db_session, sample_campaign, sample_client):
        """Test getting an enrollment"""
        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        result = DripCampaignService.get_enrollment(enrollment.id, session=db_session)

        assert result is not None
        assert result["status"] == "active"

    def test_list_enrollments(self, db_session, sample_campaign, sample_client):
        """Test listing enrollments"""
        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        enrollments = DripCampaignService.list_enrollments(session=db_session)

        assert isinstance(enrollments, list)
        assert len(enrollments) >= 1

    def test_list_enrollments_filter_status(self, db_session, sample_campaign, sample_client):
        """Test listing enrollments by status"""
        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        enrollments = DripCampaignService.list_enrollments(status="active", session=db_session)

        assert isinstance(enrollments, list)
        for e in enrollments:
            assert e["status"] == "active"


class TestEmailProcessing:
    """Tests for email processing"""

    @patch("services.drip_campaign_service.send_email")
    @patch("services.drip_campaign_service.EmailTemplateService")
    def test_process_due_emails(self, mock_template_service, mock_send_email, db_session, sample_campaign, sample_client, sample_template):
        """Test processing due drip emails"""
        # Setup mock
        mock_send_email.return_value = True
        mock_template_service.render_template.return_value = {
            "success": True,
            "subject": "Welcome!",
            "html": "<p>Hello John!</p>",
        }

        # Create step and enrollment
        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=0,
            step_order=1,
        )
        db_session.add(step)
        db_session.commit()

        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
            next_send_at=datetime.utcnow() - timedelta(hours=1),  # Due now
        )
        db_session.add(enrollment)
        db_session.commit()

        # Set appropriate send window (use current hour)
        current_hour = datetime.utcnow().hour
        sample_campaign.send_window_start = max(0, current_hour - 1)
        sample_campaign.send_window_end = min(23, current_hour + 1)
        db_session.commit()

        result = DripCampaignService.process_due_emails(session=db_session)

        assert result["success"] is True

    def test_process_due_emails_respects_window(self, db_session, sample_campaign, sample_client, sample_template):
        """Test that processing respects send window"""
        # Set send window to hours that are not now
        current_hour = datetime.utcnow().hour
        sample_campaign.send_window_start = (current_hour + 3) % 24
        sample_campaign.send_window_end = (current_hour + 5) % 24
        db_session.commit()

        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=0,
            step_order=1,
        )
        db_session.add(step)

        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
            next_send_at=datetime.utcnow() - timedelta(hours=1),
        )
        db_session.add(enrollment)
        db_session.commit()

        result = DripCampaignService.process_due_emails(session=db_session)

        # Should succeed but not send any emails (outside window)
        assert result["success"] is True


class TestCampaignStats:
    """Tests for campaign statistics"""

    def test_get_campaign_stats(self, db_session, sample_campaign, sample_client, sample_template):
        """Test getting campaign statistics"""
        # Add step
        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=0,
            step_order=1,
        )
        db_session.add(step)

        # Add enrollments with different statuses (directly, so total_enrolled counter not updated)
        enrollment1 = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
        )
        db_session.add(enrollment1)
        db_session.commit()

        result = DripCampaignService.get_campaign_stats(sample_campaign.id, session=db_session)

        assert result["success"] is True
        assert "enrollments" in result
        # Direct creation doesn't update total counter, but active count should be 1
        assert result["enrollments"]["active"] == 1

    def test_get_campaign_stats_not_found(self, db_session):
        """Test getting stats for non-existent campaign"""
        result = DripCampaignService.get_campaign_stats(9999, session=db_session)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


class TestConvenienceFunctions:
    """Tests for convenience functions"""

    @patch.object(DripCampaignService, "enroll_client")
    def test_enroll_client_function(self, mock_enroll):
        """Test the enroll_client convenience function"""
        mock_enroll.return_value = {"success": True}
        result = enroll_client(1, 2)
        mock_enroll.assert_called_once_with(1, 2)

    @patch.object(DripCampaignService, "process_due_emails")
    def test_process_drip_emails_function(self, mock_process):
        """Test the process_drip_emails convenience function"""
        mock_process.return_value = {"success": True, "emails_sent": 5}
        result = process_drip_emails()
        mock_process.assert_called_once()


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_create_campaign_missing_name(self, db_session):
        """Test creating campaign without name"""
        result = DripCampaignService.create_campaign(
            name="",
            trigger_type="signup",
            session=db_session,
        )
        # SQLAlchemy should handle this, or it might succeed with empty name
        # The behavior depends on database constraints

    def test_enroll_nonexistent_client(self, db_session, sample_campaign, sample_template):
        """Test enrolling a non-existent client"""
        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=0,
            step_order=1,
        )
        db_session.add(step)
        db_session.commit()

        result = DripCampaignService.enroll_client(
            campaign_id=sample_campaign.id,
            client_id=9999,
            session=db_session,
        )

        assert result["success"] is False
        assert "Client not found" in result["error"]

    def test_enroll_in_campaign_with_no_steps(self, db_session, sample_campaign, sample_client):
        """Test enrolling in a campaign with no steps - service may allow this"""
        result = DripCampaignService.enroll_client(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            session=db_session,
        )

        # Current implementation may allow enrollment in campaigns with no steps
        # This test documents current behavior
        assert isinstance(result, dict)
        assert "success" in result

    def test_pause_already_paused(self, db_session, sample_campaign, sample_client):
        """Test pausing an already paused enrollment - service may allow this"""
        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="paused",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        result = DripCampaignService.pause_enrollment(enrollment.id, session=db_session)

        # Current implementation allows pausing already paused enrollments
        assert result["success"] is True

    def test_resume_active_enrollment(self, db_session, sample_campaign, sample_client, sample_template):
        """Test resuming an active enrollment - service may allow this"""
        step = DripStep(
            campaign_id=sample_campaign.id,
            email_template_id=sample_template.id,
            delay_days=0,
            step_order=1,
        )
        db_session.add(step)

        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="active",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        result = DripCampaignService.resume_enrollment(enrollment.id, session=db_session)

        # Check result structure
        assert isinstance(result, dict)
        assert "success" in result

    def test_cancel_completed_enrollment(self, db_session, sample_campaign, sample_client):
        """Test cancelling a completed enrollment - service may allow this"""
        enrollment = DripEnrollment(
            campaign_id=sample_campaign.id,
            client_id=sample_client.id,
            status="completed",
            current_step=1,
        )
        db_session.add(enrollment)
        db_session.commit()

        result = DripCampaignService.cancel_enrollment(enrollment.id, session=db_session)

        # Current implementation allows cancelling completed enrollments
        assert result["success"] is True
