"""
Unit tests for TimelineService

Tests timeline event creation, retrieval, and progress tracking.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.timeline_service import (
    TimelineService,
    EVENT_TYPES,
    log_signup_event,
    log_document_uploaded,
    log_analysis_complete,
    log_dispute_sent,
    log_response_received,
    log_status_changed
)


class TestEventTypes:
    """Tests for EVENT_TYPES configuration"""

    def test_has_required_event_types(self):
        """Should have key event types defined"""
        required = ['signup', 'document_uploaded', 'analysis_complete',
                    'dispute_sent', 'response_received', 'status_changed']
        for event_type in required:
            assert event_type in EVENT_TYPES

    def test_event_types_have_required_fields(self):
        """Each event type should have title, icon, category"""
        for key, config in EVENT_TYPES.items():
            assert 'title' in config
            assert 'icon' in config
            assert 'category' in config

    def test_milestone_events_marked(self):
        """Milestone events should be properly marked"""
        milestone_events = ['signup', 'agreement_signed', 'analysis_complete',
                          'dispute_sent', 'case_resolved']
        for event_type in milestone_events:
            if event_type in EVENT_TYPES:
                assert EVENT_TYPES[event_type].get('is_milestone', False) == True


class TestCreateEvent:
    """Tests for create_event method"""

    def test_creates_event_with_defaults(self, db_session):
        """Should create event using EVENT_TYPES defaults"""
        from database import Client, TimelineEvent

        client = Client(
            name='Timeline Test',
            email='timeline@example.com',
            first_name='Timeline',
            last_name='Test'
        )
        db_session.add(client)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.create_event(
            client_id=client.id,
            event_type='signup'
        )

        assert result['success'] == True
        assert result['event_type'] == 'signup'
        assert 'event_id' in result

        # Verify in database
        event = db_session.query(TimelineEvent).filter_by(id=result['event_id']).first()
        assert event is not None
        assert event.title == 'Account Created'
        assert event.icon == 'user-plus'
        assert event.event_category == 'onboarding'

    def test_creates_event_with_custom_values(self, db_session):
        """Should allow custom title, description, icon"""
        from database import Client

        client = Client(
            name='Custom Event Test',
            email='custom_event@example.com'
        )
        db_session.add(client)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.create_event(
            client_id=client.id,
            event_type='status_changed',
            title='Custom Title',
            description='Custom description',
            icon='star',
            is_milestone=True
        )

        assert result['success'] == True
        assert result['title'] == 'Custom Title'

    def test_creates_event_with_metadata(self, db_session):
        """Should store metadata correctly"""
        from database import Client, TimelineEvent

        client = Client(
            name='Metadata Test',
            email='metadata@example.com'
        )
        db_session.add(client)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.create_event(
            client_id=client.id,
            event_type='dispute_sent',
            metadata={'bureau': 'Equifax', 'round': 1}
        )

        event = db_session.query(TimelineEvent).filter_by(id=result['event_id']).first()
        assert event.metadata_json == {'bureau': 'Equifax', 'round': 1}

    def test_creates_event_with_related_entity(self, db_session):
        """Should store related entity reference"""
        from database import Client, TimelineEvent

        client = Client(
            name='Related Test',
            email='related@example.com'
        )
        db_session.add(client)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.create_event(
            client_id=client.id,
            event_type='document_uploaded',
            related_type='client_upload',
            related_id=123
        )

        event = db_session.query(TimelineEvent).filter_by(id=result['event_id']).first()
        assert event.related_type == 'client_upload'
        assert event.related_id == 123

    def test_returns_error_for_missing_client(self, db_session):
        """Should return error for non-existent client"""
        service = TimelineService(db_session)
        result = service.create_event(
            client_id=99999,
            event_type='signup'
        )

        assert result['success'] == False
        assert 'error' in result

    def test_creates_event_with_custom_date(self, db_session):
        """Should use provided event_date"""
        from database import Client, TimelineEvent

        client = Client(
            name='Date Test',
            email='date_test@example.com'
        )
        db_session.add(client)
        db_session.commit()

        custom_date = datetime(2025, 6, 15, 10, 30, 0)
        service = TimelineService(db_session)
        result = service.create_event(
            client_id=client.id,
            event_type='signup',
            event_date=custom_date
        )

        event = db_session.query(TimelineEvent).filter_by(id=result['event_id']).first()
        assert event.event_date == custom_date


class TestGetTimeline:
    """Tests for get_timeline method"""

    def test_returns_events_in_order(self, db_session):
        """Should return events in reverse chronological order"""
        from database import Client, TimelineEvent

        client = Client(
            name='Order Test',
            email='order@example.com'
        )
        db_session.add(client)
        db_session.commit()

        # Create events with different dates
        now = datetime.utcnow()
        for i in range(5):
            event = TimelineEvent(
                client_id=client.id,
                event_type='status_changed',
                title=f'Event {i}',
                event_date=now - timedelta(days=i)
            )
            db_session.add(event)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.get_timeline(client.id)

        assert result['success'] == True
        assert result['total'] == 5
        assert len(result['events']) == 5
        # First event should be most recent
        assert result['events'][0]['title'] == 'Event 0'
        assert result['events'][4]['title'] == 'Event 4'

    def test_filters_by_category(self, db_session):
        """Should filter events by category"""
        from database import Client, TimelineEvent

        client = Client(
            name='Category Test',
            email='category@example.com'
        )
        db_session.add(client)
        db_session.commit()

        # Create events in different categories
        categories = ['onboarding', 'documents', 'disputes']
        for cat in categories:
            for i in range(2):
                event = TimelineEvent(
                    client_id=client.id,
                    event_type='status_changed',
                    title=f'{cat} Event {i}',
                    event_category=cat,
                    event_date=datetime.utcnow()
                )
                db_session.add(event)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.get_timeline(client.id, category='documents')

        assert result['total'] == 2
        for event in result['events']:
            assert event['category'] == 'documents'

    def test_filters_milestones_only(self, db_session):
        """Should return only milestone events when requested"""
        from database import Client, TimelineEvent

        client = Client(
            name='Milestone Test',
            email='milestone@example.com'
        )
        db_session.add(client)
        db_session.commit()

        # Create mix of milestone and regular events
        for i in range(4):
            event = TimelineEvent(
                client_id=client.id,
                event_type='status_changed',
                title=f'Event {i}',
                is_milestone=(i % 2 == 0),
                event_date=datetime.utcnow()
            )
            db_session.add(event)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.get_timeline(client.id, milestones_only=True)

        assert result['total'] == 2
        for event in result['events']:
            assert event['is_milestone'] == True

    def test_respects_limit_and_offset(self, db_session):
        """Should paginate results correctly"""
        from database import Client, TimelineEvent

        client = Client(
            name='Pagination Test',
            email='pagination@example.com'
        )
        db_session.add(client)
        db_session.commit()

        # Create 10 events
        now = datetime.utcnow()
        for i in range(10):
            event = TimelineEvent(
                client_id=client.id,
                event_type='status_changed',
                title=f'Event {i}',
                event_date=now - timedelta(hours=i)
            )
            db_session.add(event)
        db_session.commit()

        service = TimelineService(db_session)

        # Get first page
        result1 = service.get_timeline(client.id, limit=3, offset=0)
        assert len(result1['events']) == 3
        assert result1['events'][0]['title'] == 'Event 0'

        # Get second page
        result2 = service.get_timeline(client.id, limit=3, offset=3)
        assert len(result2['events']) == 3
        assert result2['events'][0]['title'] == 'Event 3'

    def test_excludes_hidden_events(self, db_session):
        """Should not return hidden events"""
        from database import Client, TimelineEvent

        client = Client(
            name='Hidden Test',
            email='hidden@example.com'
        )
        db_session.add(client)
        db_session.commit()

        # Create visible and hidden events
        visible = TimelineEvent(
            client_id=client.id,
            event_type='signup',
            title='Visible Event',
            is_visible=True,
            event_date=datetime.utcnow()
        )
        hidden = TimelineEvent(
            client_id=client.id,
            event_type='status_changed',
            title='Hidden Event',
            is_visible=False,
            event_date=datetime.utcnow()
        )
        db_session.add_all([visible, hidden])
        db_session.commit()

        service = TimelineService(db_session)
        result = service.get_timeline(client.id)

        assert result['total'] == 1
        assert result['events'][0]['title'] == 'Visible Event'


class TestGetRecentEvents:
    """Tests for get_recent_events method"""

    def test_returns_recent_events(self, db_session):
        """Should return most recent events"""
        from database import Client, TimelineEvent

        client = Client(
            name='Recent Test',
            email='recent@example.com'
        )
        db_session.add(client)
        db_session.commit()

        now = datetime.utcnow()
        for i in range(10):
            event = TimelineEvent(
                client_id=client.id,
                event_type='status_changed',
                title=f'Event {i}',
                event_date=now - timedelta(hours=i)
            )
            db_session.add(event)
        db_session.commit()

        service = TimelineService(db_session)
        events = service.get_recent_events(client.id, limit=3)

        assert len(events) == 3
        assert events[0]['title'] == 'Event 0'


class TestGetMilestones:
    """Tests for get_milestones method"""

    def test_returns_milestones_in_order(self, db_session):
        """Should return milestones in chronological order"""
        from database import Client, TimelineEvent

        client = Client(
            name='Milestones Test',
            email='milestones@example.com'
        )
        db_session.add(client)
        db_session.commit()

        now = datetime.utcnow()
        milestones = ['signup', 'analysis_complete', 'dispute_sent']
        for i, event_type in enumerate(milestones):
            event = TimelineEvent(
                client_id=client.id,
                event_type=event_type,
                title=f'Milestone {i}',
                is_milestone=True,
                event_date=now - timedelta(days=10-i)
            )
            db_session.add(event)
        db_session.commit()

        service = TimelineService(db_session)
        milestones = service.get_milestones(client.id)

        assert len(milestones) == 3
        # Should be in chronological order (oldest first)
        assert milestones[0]['title'] == 'Milestone 0'


class TestGetProgressSummary:
    """Tests for get_progress_summary method"""

    def test_returns_empty_progress_for_new_client(self, db_session):
        """Should return initial progress for client with no events"""
        from database import Client

        client = Client(
            name='New Client',
            email='new_progress@example.com'
        )
        db_session.add(client)
        db_session.commit()

        service = TimelineService(db_session)
        progress = service.get_progress_summary(client.id)

        assert progress['success'] == True
        assert progress['total_events'] == 0
        assert progress['milestones_completed'] == 0
        assert progress['current_stage'] == 'signup'

    def test_returns_correct_stage_progress(self, db_session):
        """Should track stage completion correctly"""
        from database import Client, TimelineEvent

        client = Client(
            name='Stage Test',
            email='stage@example.com'
        )
        db_session.add(client)
        db_session.commit()

        # Create events for signup and onboarding
        events = [
            TimelineEvent(client_id=client.id, event_type='signup', title='Signup', event_date=datetime.utcnow()),
            TimelineEvent(client_id=client.id, event_type='onboarding_complete', title='Onboarding Done', event_date=datetime.utcnow()),
        ]
        for event in events:
            db_session.add(event)
        db_session.commit()

        service = TimelineService(db_session)
        progress = service.get_progress_summary(client.id)

        assert progress['current_stage'] == 'onboarded'

        # Check stages list
        stages = {s['key']: s['completed'] for s in progress['stages']}
        assert stages['signup'] == True
        assert stages['onboarding'] == True
        assert stages['report_uploaded'] == False


class TestHideEvent:
    """Tests for hide_event method"""

    def test_hides_event(self, db_session):
        """Should set is_visible to False"""
        from database import Client, TimelineEvent

        client = Client(
            name='Hide Test',
            email='hide@example.com'
        )
        db_session.add(client)
        db_session.commit()

        event = TimelineEvent(
            client_id=client.id,
            event_type='status_changed',
            title='To Hide',
            is_visible=True,
            event_date=datetime.utcnow()
        )
        db_session.add(event)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.hide_event(event.id)

        assert result['success'] == True
        db_session.refresh(event)
        assert event.is_visible == False

    def test_returns_error_for_missing_event(self, db_session):
        """Should return error for non-existent event"""
        service = TimelineService(db_session)
        result = service.hide_event(99999)

        assert result['success'] == False
        assert 'error' in result


class TestDeleteEvent:
    """Tests for delete_event method"""

    def test_deletes_event(self, db_session):
        """Should remove event from database"""
        from database import Client, TimelineEvent

        client = Client(
            name='Delete Test',
            email='delete@example.com'
        )
        db_session.add(client)
        db_session.commit()

        event = TimelineEvent(
            client_id=client.id,
            event_type='status_changed',
            title='To Delete',
            event_date=datetime.utcnow()
        )
        db_session.add(event)
        db_session.commit()
        event_id = event.id

        service = TimelineService(db_session)
        result = service.delete_event(event_id)

        assert result['success'] == True
        deleted = db_session.query(TimelineEvent).filter_by(id=event_id).first()
        assert deleted is None


class TestBackfillEvents:
    """Tests for backfill_events method"""

    def test_backfills_signup_event(self, db_session):
        """Should create signup event from client created_at"""
        from database import Client, TimelineEvent

        client = Client(
            name='Backfill Test',
            email='backfill@example.com',
            created_at=datetime(2025, 1, 1, 12, 0, 0)
        )
        db_session.add(client)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.backfill_events(client.id)

        assert result['success'] == True
        assert result['events_created'] >= 1

        signup = db_session.query(TimelineEvent).filter_by(
            client_id=client.id,
            event_type='signup'
        ).first()
        assert signup is not None

    def test_backfills_agreement_signed(self, db_session):
        """Should create agreement event if signed"""
        from database import Client, TimelineEvent

        client = Client(
            name='Agreement Backfill',
            email='agreement_backfill@example.com',
            agreement_signed=True
        )
        db_session.add(client)
        db_session.commit()

        service = TimelineService(db_session)
        result = service.backfill_events(client.id)

        assert result['events_created'] >= 1

        agreement = db_session.query(TimelineEvent).filter_by(
            client_id=client.id,
            event_type='agreement_signed'
        ).first()
        assert agreement is not None

    def test_does_not_duplicate_events(self, db_session):
        """Should not create duplicate events"""
        from database import Client, TimelineEvent

        client = Client(
            name='No Dup Test',
            email='nodup@example.com',
            created_at=datetime.utcnow()
        )
        db_session.add(client)
        db_session.commit()

        service = TimelineService(db_session)

        # First backfill
        result1 = service.backfill_events(client.id)
        # Second backfill
        result2 = service.backfill_events(client.id)

        assert result2['events_created'] == 0

        count = db_session.query(TimelineEvent).filter_by(
            client_id=client.id,
            event_type='signup'
        ).count()
        assert count == 1


class TestHelperFunctions:
    """Tests for helper logging functions"""

    def test_log_signup_event(self, db_session):
        """Should create signup event"""
        from database import Client, TimelineEvent

        client = Client(
            name='Log Signup Test',
            email='log_signup@example.com'
        )
        db_session.add(client)
        db_session.commit()

        log_signup_event(db_session, client.id)

        event = db_session.query(TimelineEvent).filter_by(
            client_id=client.id,
            event_type='signup'
        ).first()
        assert event is not None

    def test_log_document_uploaded(self, db_session):
        """Should create document upload event"""
        from database import Client, TimelineEvent

        client = Client(
            name='Log Doc Test',
            email='log_doc@example.com'
        )
        db_session.add(client)
        db_session.commit()

        log_document_uploaded(db_session, client.id, 'credit_report', 123)

        event = db_session.query(TimelineEvent).filter_by(
            client_id=client.id,
            event_type='credit_report_uploaded'
        ).first()
        assert event is not None
        assert event.related_id == 123

    def test_log_analysis_complete(self, db_session):
        """Should create analysis complete event with violations count"""
        from database import Client, TimelineEvent

        client = Client(
            name='Log Analysis Test',
            email='log_analysis@example.com'
        )
        db_session.add(client)
        db_session.commit()

        log_analysis_complete(db_session, client.id, 456, violations_count=5)

        event = db_session.query(TimelineEvent).filter_by(
            client_id=client.id,
            event_type='analysis_complete'
        ).first()
        assert event is not None
        assert event.metadata_json['violations_count'] == 5

    def test_log_dispute_sent(self, db_session):
        """Should create dispute sent event with bureau info"""
        from database import Client, TimelineEvent

        client = Client(
            name='Log Dispute Test',
            email='log_dispute@example.com'
        )
        db_session.add(client)
        db_session.commit()

        log_dispute_sent(db_session, client.id, 'Equifax', 789, round_number=2)

        event = db_session.query(TimelineEvent).filter_by(
            client_id=client.id,
            event_type='dispute_sent'
        ).first()
        assert event is not None
        assert 'Equifax' in event.title
        assert event.metadata_json['round'] == 2

    def test_log_response_received(self, db_session):
        """Should create response received event"""
        from database import Client, TimelineEvent

        client = Client(
            name='Log Response Test',
            email='log_response@example.com'
        )
        db_session.add(client)
        db_session.commit()

        log_response_received(db_session, client.id, 'TransUnion', 101)

        event = db_session.query(TimelineEvent).filter_by(
            client_id=client.id,
            event_type='response_received'
        ).first()
        assert event is not None
        assert 'TransUnion' in event.title

    def test_log_status_changed(self, db_session):
        """Should create status change event"""
        from database import Client, TimelineEvent

        client = Client(
            name='Log Status Test',
            email='log_status@example.com'
        )
        db_session.add(client)
        db_session.commit()

        log_status_changed(db_session, client.id, 'pending', 'in_progress')

        event = db_session.query(TimelineEvent).filter_by(
            client_id=client.id,
            event_type='status_changed'
        ).first()
        assert event is not None
        assert event.metadata_json['old_status'] == 'pending'
        assert event.metadata_json['new_status'] == 'in_progress'
