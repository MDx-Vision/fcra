"""
Unit tests for OnboardingService

Tests onboarding wizard progress tracking and step completion.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.onboarding_service import OnboardingService, ONBOARDING_STEPS


class TestOnboardingSteps:
    """Tests for ONBOARDING_STEPS configuration"""

    def test_has_seven_steps(self):
        """Should have exactly 7 onboarding steps"""
        assert len(ONBOARDING_STEPS) == 7

    def test_steps_have_required_fields(self):
        """Each step should have key, name, description, icon"""
        for step in ONBOARDING_STEPS:
            assert 'key' in step
            assert 'name' in step
            assert 'description' in step
            assert 'icon' in step

    def test_step_keys_are_unique(self):
        """Step keys should be unique"""
        keys = [s['key'] for s in ONBOARDING_STEPS]
        assert len(keys) == len(set(keys))

    def test_correct_step_order(self):
        """Steps should be in correct order"""
        expected_order = [
            'personal_info',
            'id_documents',
            'ssn_card',
            'proof_of_address',
            'credit_monitoring',
            'agreement',
            'payment'
        ]
        actual_order = [s['key'] for s in ONBOARDING_STEPS]
        assert actual_order == expected_order


class TestGetOrCreateProgress:
    """Tests for get_or_create_progress method"""

    def test_creates_new_progress(self, db_session):
        """Should create new progress if none exists"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Test Client',
            email='onboard_test@example.com',
            first_name='Test',
            last_name='Client'
        )
        db_session.add(client)
        db_session.commit()

        service = OnboardingService(db_session)
        progress = service.get_or_create_progress(client.id)

        assert progress is not None
        assert progress.client_id == client.id
        assert progress.completion_percentage == 0
        assert progress.is_complete == False

    def test_returns_existing_progress(self, db_session):
        """Should return existing progress if exists"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Test Client 2',
            email='onboard_test2@example.com',
            first_name='Test',
            last_name='Client'
        )
        db_session.add(client)
        db_session.commit()

        # Create progress manually
        progress = OnboardingProgress(
            client_id=client.id,
            completion_percentage=50,
            personal_info_completed=True
        )
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        result = service.get_or_create_progress(client.id)

        assert result.id == progress.id
        assert result.completion_percentage == 50


class TestGetProgressSummary:
    """Tests for get_progress_summary method"""

    def test_returns_progress_summary(self, db_session):
        """Should return detailed progress summary"""
        from database import Client

        client = Client(
            name='Summary Test',
            email='summary_test@example.com',
            first_name='Summary',
            last_name='Test',
            address_street='123 Main St',
            address_city='Anytown',
            address_state='CA',
            address_zip='12345'
        )
        db_session.add(client)
        db_session.commit()

        service = OnboardingService(db_session)
        summary = service.get_progress_summary(client.id)

        assert 'client_id' in summary
        assert 'steps' in summary
        assert 'completed_steps' in summary
        assert 'total_steps' in summary
        assert 'percentage' in summary
        assert 'current_step' in summary
        assert 'is_complete' in summary

    def test_counts_completed_steps(self, db_session):
        """Should count completed steps correctly"""
        from database import Client

        # Create client with personal info complete
        client = Client(
            name='Count Test',
            email='count_test@example.com',
            first_name='Count',
            last_name='Test',
            address_street='123 Main St',
            address_city='Anytown',
            address_state='CA',
            address_zip='12345',
            date_of_birth=datetime(1990, 1, 1)
        )
        db_session.add(client)
        db_session.commit()

        service = OnboardingService(db_session)
        summary = service.get_progress_summary(client.id)

        # Personal info should be complete
        personal_step = next(s for s in summary['steps'] if s['key'] == 'personal_info')
        assert personal_step['is_complete'] == True

    def test_returns_error_for_missing_client(self, db_session):
        """Should return error for non-existent client"""
        service = OnboardingService(db_session)
        summary = service.get_progress_summary(99999)

        assert 'error' in summary


class TestCheckStepCompletion:
    """Tests for step completion checking"""

    def test_personal_info_incomplete(self, db_session):
        """Should detect incomplete personal info"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Incomplete Test',
            email='incomplete@example.com',
            first_name='Test'
            # Missing other fields
        )
        db_session.add(client)
        db_session.commit()

        progress = OnboardingProgress(client_id=client.id)
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        is_complete = service._check_step_completion(client, progress, 'personal_info')

        assert is_complete == False

    def test_personal_info_complete(self, db_session):
        """Should detect complete personal info"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Complete Test',
            email='complete@example.com',
            first_name='Complete',
            last_name='Test',
            address_street='123 Main',
            address_city='City',
            address_state='CA',
            address_zip='12345'
        )
        db_session.add(client)
        db_session.commit()

        progress = OnboardingProgress(client_id=client.id)
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        is_complete = service._check_step_completion(client, progress, 'personal_info')

        assert is_complete == True

    def test_agreement_incomplete(self, db_session):
        """Should detect unsigned agreement"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Agreement Test',
            email='agreement@example.com',
            agreement_signed=False
        )
        db_session.add(client)
        db_session.commit()

        progress = OnboardingProgress(client_id=client.id)
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        is_complete = service._check_step_completion(client, progress, 'agreement')

        assert is_complete == False

    def test_agreement_complete(self, db_session):
        """Should detect signed agreement"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Agreement Test 2',
            email='agreement2@example.com',
            agreement_signed=True
        )
        db_session.add(client)
        db_session.commit()

        progress = OnboardingProgress(client_id=client.id)
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        is_complete = service._check_step_completion(client, progress, 'agreement')

        assert is_complete == True

    def test_payment_incomplete(self, db_session):
        """Should detect incomplete payment"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Payment Test',
            email='payment@example.com',
            payment_status='pending'
        )
        db_session.add(client)
        db_session.commit()

        progress = OnboardingProgress(client_id=client.id)
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        is_complete = service._check_step_completion(client, progress, 'payment')

        assert is_complete == False

    def test_payment_complete(self, db_session):
        """Should detect completed payment"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Payment Test 2',
            email='payment2@example.com',
            payment_status='paid'
        )
        db_session.add(client)
        db_session.commit()

        progress = OnboardingProgress(client_id=client.id)
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        is_complete = service._check_step_completion(client, progress, 'payment')

        assert is_complete == True


class TestCompleteStep:
    """Tests for complete_step method"""

    def test_marks_step_complete(self, db_session):
        """Should mark step as complete"""
        from database import Client

        client = Client(
            name='Complete Step Test',
            email='complete_step@example.com'
        )
        db_session.add(client)
        db_session.commit()

        service = OnboardingService(db_session)
        result = service.complete_step(client.id, 'personal_info')

        assert result['success'] == True
        assert result['step'] == 'personal_info'
        assert 'completed_at' in result

    def test_invalid_step_key(self, db_session):
        """Should reject invalid step key"""
        from database import Client

        client = Client(
            name='Invalid Step Test',
            email='invalid_step@example.com'
        )
        db_session.add(client)
        db_session.commit()

        service = OnboardingService(db_session)
        result = service.complete_step(client.id, 'invalid_step')

        assert result['success'] == False
        assert 'error' in result

    def test_updates_percentage(self, db_session):
        """Should update completion percentage"""
        from database import Client

        client = Client(
            name='Percentage Test',
            email='percentage@example.com'
        )
        db_session.add(client)
        db_session.commit()

        service = OnboardingService(db_session)
        result = service.complete_step(client.id, 'personal_info')

        # 1 of 7 steps = 14%
        assert result['percentage'] == 14


class TestSyncProgress:
    """Tests for sync_progress method"""

    def test_syncs_progress(self, db_session):
        """Should sync progress based on actual data"""
        from database import Client

        client = Client(
            name='Sync Test',
            email='sync@example.com',
            first_name='Sync',
            last_name='Test',
            address_street='123 Main',
            address_city='City',
            address_state='CA',
            address_zip='12345',
            agreement_signed=True
        )
        db_session.add(client)
        db_session.commit()

        service = OnboardingService(db_session)
        result = service.sync_progress(client.id)

        assert result['success'] == True
        # Should have synced personal_info and agreement
        assert 'personal_info' in result['synced_steps']
        assert 'agreement' in result['synced_steps']

    def test_returns_error_for_missing_client(self, db_session):
        """Should return error for non-existent client"""
        service = OnboardingService(db_session)
        result = service.sync_progress(99999)

        assert result['success'] == False
        assert 'error' in result


class TestGetNextStep:
    """Tests for get_next_step method"""

    def test_returns_first_incomplete_step(self, db_session):
        """Should return first incomplete step"""
        from database import Client

        client = Client(
            name='Next Step Test',
            email='next_step@example.com'
        )
        db_session.add(client)
        db_session.commit()

        service = OnboardingService(db_session)
        next_step = service.get_next_step(client.id)

        assert next_step is not None
        assert next_step['key'] == 'personal_info'

    def test_returns_none_when_complete(self, db_session):
        """Should return None when all steps complete"""
        from database import Client, OnboardingProgress, ClientUpload

        client = Client(
            name='All Complete Test',
            email='all_complete@example.com',
            first_name='Test',
            last_name='User',
            address_street='123 Main',
            address_city='City',
            address_state='CA',
            address_zip='12345',
            credit_monitoring_service='identityiq',
            credit_monitoring_username='testuser',
            agreement_signed=True,
            payment_status='paid'
        )
        db_session.add(client)
        db_session.commit()

        # Create required document uploads
        uploads = [
            ClientUpload(client_id=client.id, document_type='drivers_license_front', category='id_verification', file_name='id.jpg', file_path='/tmp/id.jpg'),
            ClientUpload(client_id=client.id, document_type='ssn_card_front', category='id_verification', file_name='ssn.jpg', file_path='/tmp/ssn.jpg'),
            ClientUpload(client_id=client.id, document_type='utility_bill', category='proof_of_address', file_name='bill.pdf', file_path='/tmp/bill.pdf'),
        ]
        for upload in uploads:
            db_session.add(upload)
        db_session.commit()

        # Mark all steps complete
        progress = OnboardingProgress(
            client_id=client.id,
            personal_info_completed=True,
            id_documents_completed=True,
            ssn_card_completed=True,
            proof_of_address_completed=True,
            credit_monitoring_completed=True,
            agreement_completed=True,
            payment_completed=True,
            is_complete=True,
            completion_percentage=100
        )
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        next_step = service.get_next_step(client.id)

        assert next_step is None


class TestResetProgress:
    """Tests for reset_progress method"""

    def test_resets_progress(self, db_session):
        """Should delete progress record"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Reset Test',
            email='reset@example.com'
        )
        db_session.add(client)
        db_session.commit()

        progress = OnboardingProgress(
            client_id=client.id,
            completion_percentage=50
        )
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        result = service.reset_progress(client.id)

        assert result['success'] == True

        # Verify deleted
        remaining = db_session.query(OnboardingProgress).filter_by(client_id=client.id).first()
        assert remaining is None

    def test_handles_no_progress(self, db_session):
        """Should handle case with no progress to reset"""
        from database import Client

        client = Client(
            name='No Progress Test',
            email='no_progress@example.com'
        )
        db_session.add(client)
        db_session.commit()

        service = OnboardingService(db_session)
        result = service.reset_progress(client.id)

        assert result['success'] == True


class TestGetAllIncomplete:
    """Tests for get_all_incomplete method"""

    def test_returns_incomplete_clients(self, db_session):
        """Should return clients with incomplete onboarding"""
        from database import Client, OnboardingProgress

        # Create client with incomplete progress
        client = Client(
            name='Incomplete Client',
            email='incomplete_list@example.com',
            first_name='Incomplete',
            last_name='Client'
        )
        db_session.add(client)
        db_session.commit()

        progress = OnboardingProgress(
            client_id=client.id,
            completion_percentage=50,
            is_complete=False
        )
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        results = service.get_all_incomplete()

        assert len(results) >= 1
        found = any(r['client_id'] == client.id for r in results)
        assert found

    def test_excludes_complete_clients(self, db_session):
        """Should exclude clients with complete onboarding"""
        from database import Client, OnboardingProgress

        client = Client(
            name='Complete Client',
            email='complete_list@example.com',
            first_name='Complete',
            last_name='Client'
        )
        db_session.add(client)
        db_session.commit()

        progress = OnboardingProgress(
            client_id=client.id,
            completion_percentage=100,
            is_complete=True
        )
        db_session.add(progress)
        db_session.commit()

        service = OnboardingService(db_session)
        results = service.get_all_incomplete()

        found = any(r['client_id'] == client.id for r in results)
        assert found == False
