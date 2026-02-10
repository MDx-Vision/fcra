"""
Unit Tests for State Attorney General Complaint Service

Tests all functionality of the StateAGService including:
- AG contact database seeding and retrieval
- Complaint CRUD operations
- Status workflow transitions
- Letter generation
- Statistics and reporting
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta


class TestStateAGConstants:
    """Test service constants"""

    def test_violation_types_defined(self):
        """Verify all violation types are defined"""
        from services.state_ag_service import VIOLATION_TYPES

        assert 'failure_to_investigate' in VIOLATION_TYPES
        assert 'inaccurate_reporting' in VIOLATION_TYPES
        assert 'failure_to_correct' in VIOLATION_TYPES
        assert 'reinsertion' in VIOLATION_TYPES
        assert 'frivolous_response' in VIOLATION_TYPES
        assert 'identity_theft' in VIOLATION_TYPES
        assert len(VIOLATION_TYPES) == 10

    def test_complaint_statuses_defined(self):
        """Verify all complaint statuses are defined"""
        from services.state_ag_service import COMPLAINT_STATUSES

        assert 'draft' in COMPLAINT_STATUSES
        assert 'ready' in COMPLAINT_STATUSES
        assert 'filed' in COMPLAINT_STATUSES
        assert 'acknowledged' in COMPLAINT_STATUSES
        assert 'investigating' in COMPLAINT_STATUSES
        assert 'resolved' in COMPLAINT_STATUSES
        assert 'closed' in COMPLAINT_STATUSES

    def test_state_ag_database_has_50_states_plus_dc(self):
        """Verify database has all 50 states plus DC"""
        from services.state_ag_service import STATE_AG_DATABASE

        # 50 states + DC = 51
        assert len(STATE_AG_DATABASE) == 51

        # Check for specific states
        state_codes = [s['state_code'] for s in STATE_AG_DATABASE]
        assert 'CA' in state_codes
        assert 'NY' in state_codes
        assert 'TX' in state_codes
        assert 'FL' in state_codes
        assert 'NJ' in state_codes
        assert 'DC' in state_codes

    def test_state_ag_database_has_required_fields(self):
        """Verify each state entry has required fields"""
        from services.state_ag_service import STATE_AG_DATABASE

        required_fields = [
            'state_code', 'state_name', 'office_name',
            'address_line1', 'city', 'state', 'zip_code'
        ]

        for state in STATE_AG_DATABASE:
            for field in required_fields:
                assert field in state, f"Missing {field} for {state.get('state_code', 'unknown')}"


class TestStateAGServiceInit:
    """Test service initialization"""

    def test_init_without_session(self):
        """Service initializes without session"""
        from services.state_ag_service import StateAGService

        service = StateAGService()
        assert service._session is None
        assert service._owns_session is True

    def test_init_with_session(self):
        """Service initializes with provided session"""
        from services.state_ag_service import StateAGService

        mock_session = MagicMock()
        service = StateAGService(session=mock_session)
        assert service._session is mock_session
        assert service._owns_session is False

    def test_context_manager(self):
        """Service works as context manager"""
        from services.state_ag_service import StateAGService

        mock_session = MagicMock()
        with StateAGService(session=mock_session) as service:
            assert service._session is mock_session

    def test_factory_function(self):
        """Factory function returns service instance"""
        from services.state_ag_service import get_state_ag_service

        service = get_state_ag_service()
        assert service is not None


class TestStateAGContactOperations:
    """Test AG contact operations"""

    @pytest.fixture
    def service(self):
        """Create service with mock session"""
        from services.state_ag_service import StateAGService

        mock_session = MagicMock()
        service = StateAGService(session=mock_session)
        return service

    def test_seed_ag_contacts_creates_new(self, service):
        """Seeding creates new AG contacts"""
        from services.state_ag_service import STATE_AG_DATABASE

        # No existing contacts
        service.session.query.return_value.filter_by.return_value.first.return_value = None

        result = service.seed_ag_contacts()

        assert result['success'] is True
        assert result['data']['created'] == len(STATE_AG_DATABASE)
        assert service.session.add.called

    def test_seed_ag_contacts_updates_existing(self, service):
        """Seeding updates existing AG contacts"""
        # Return mock existing contact
        mock_contact = MagicMock()
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_contact

        result = service.seed_ag_contacts()

        assert result['success'] is True
        assert result['data']['updated'] > 0

    def test_get_all_ag_contacts(self, service):
        """Get all AG contacts returns list"""
        mock_contact = MagicMock()
        mock_contact.to_dict.return_value = {'state_code': 'NJ'}
        service.session.query.return_value.order_by.return_value.all.return_value = [mock_contact]

        contacts = service.get_all_ag_contacts()

        assert isinstance(contacts, list)
        assert len(contacts) == 1
        assert contacts[0]['state_code'] == 'NJ'

    def test_get_ag_contact_by_state(self, service):
        """Get AG contact by state code"""
        mock_contact = MagicMock()
        mock_contact.to_dict.return_value = {
            'state_code': 'CA',
            'state_name': 'California'
        }
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_contact

        contact = service.get_ag_contact_by_state('CA')

        assert contact is not None
        assert contact['state_code'] == 'CA'

    def test_get_ag_contact_by_state_not_found(self, service):
        """Get AG contact returns None for unknown state"""
        service.session.query.return_value.filter_by.return_value.first.return_value = None

        contact = service.get_ag_contact_by_state('XX')

        assert contact is None

    def test_get_ag_contact_by_id(self, service):
        """Get AG contact by ID"""
        mock_contact = MagicMock()
        mock_contact.to_dict.return_value = {'id': 1}
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_contact

        contact = service.get_ag_contact_by_id(1)

        assert contact is not None
        assert contact['id'] == 1


class TestComplaintCRUD:
    """Test complaint CRUD operations"""

    @pytest.fixture
    def service(self):
        """Create service with mock session"""
        from services.state_ag_service import StateAGService

        mock_session = MagicMock()
        service = StateAGService(session=mock_session)
        return service

    def test_create_complaint_success(self, service):
        """Create complaint successfully"""
        # Mock client and AG contact
        mock_client = MagicMock()
        mock_client.id = 1
        mock_ag_contact = MagicMock()
        mock_ag_contact.id = 1

        # Setup query returns
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Client':
                mock_query.filter_by.return_value.first.return_value = mock_client
            elif model.__name__ == 'StateAGContact':
                mock_query.filter_by.return_value.first.return_value = mock_ag_contact
            return mock_query

        service.session.query.side_effect = query_side_effect

        result = service.create_complaint(
            client_id=1,
            state_code='NJ',
            complaint_type='fcra_violation',
            bureaus=['Equifax', 'Experian'],
            violation_types=['failure_to_investigate']
        )

        assert result['success'] is True
        assert service.session.add.called

    def test_create_complaint_client_not_found(self, service):
        """Create complaint fails if client not found"""
        service.session.query.return_value.filter_by.return_value.first.return_value = None

        result = service.create_complaint(
            client_id=999,
            state_code='NJ',
            complaint_type='fcra_violation'
        )

        assert result['success'] is False
        assert result['error_code'] == 'CLIENT_NOT_FOUND'

    def test_create_complaint_invalid_type(self, service):
        """Create complaint fails with invalid type"""
        mock_client = MagicMock()
        mock_ag_contact = MagicMock()

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Client':
                mock_query.filter_by.return_value.first.return_value = mock_client
            elif model.__name__ == 'StateAGContact':
                mock_query.filter_by.return_value.first.return_value = mock_ag_contact
            return mock_query

        service.session.query.side_effect = query_side_effect

        result = service.create_complaint(
            client_id=1,
            state_code='NJ',
            complaint_type='invalid_type'
        )

        assert result['success'] is False
        assert result['error_code'] == 'INVALID_COMPLAINT_TYPE'

    def test_get_complaint(self, service):
        """Get complaint by ID"""
        mock_complaint = MagicMock()
        mock_complaint.to_dict.return_value = {'id': 1, 'status': 'draft'}
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        complaint = service.get_complaint(1)

        assert complaint is not None
        assert complaint['id'] == 1

    def test_get_complaint_not_found(self, service):
        """Get complaint returns None if not found"""
        service.session.query.return_value.filter_by.return_value.first.return_value = None

        complaint = service.get_complaint(999)

        assert complaint is None

    def test_get_client_complaints(self, service):
        """Get all complaints for a client"""
        mock_complaint = MagicMock()
        mock_complaint.to_dict.return_value = {'id': 1}
        service.session.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [mock_complaint]

        complaints = service.get_client_complaints(1)

        assert len(complaints) == 1

    def test_update_complaint(self, service):
        """Update complaint fields"""
        mock_complaint = MagicMock()
        mock_complaint.to_dict.return_value = {'id': 1, 'notes': 'Updated'}
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        result = service.update_complaint(1, {'notes': 'Updated'})

        assert result['success'] is True

    def test_update_complaint_not_found(self, service):
        """Update fails if complaint not found"""
        service.session.query.return_value.filter_by.return_value.first.return_value = None

        result = service.update_complaint(999, {'notes': 'test'})

        assert result['success'] is False
        assert result['error_code'] == 'COMPLAINT_NOT_FOUND'


class TestComplaintStatusWorkflow:
    """Test complaint status transitions"""

    @pytest.fixture
    def service(self):
        """Create service with mock session"""
        from services.state_ag_service import StateAGService

        mock_session = MagicMock()
        service = StateAGService(session=mock_session)
        return service

    def test_update_status_to_filed(self, service):
        """Update status to filed sets filed_at"""
        mock_complaint = MagicMock()
        mock_complaint.status = 'ready'
        mock_complaint.to_dict.return_value = {'id': 1, 'status': 'filed'}
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        result = service.update_complaint_status(1, 'filed')

        assert result['success'] is True
        assert mock_complaint.status == 'filed'
        assert mock_complaint.filed_at is not None

    def test_update_status_to_acknowledged(self, service):
        """Update status to acknowledged sets acknowledged_at"""
        mock_complaint = MagicMock()
        mock_complaint.status = 'filed'
        mock_complaint.notes = ''
        mock_complaint.to_dict.return_value = {'id': 1, 'status': 'acknowledged'}
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        result = service.update_complaint_status(1, 'acknowledged')

        assert result['success'] is True
        assert mock_complaint.acknowledged_at is not None

    def test_update_status_invalid(self, service):
        """Update with invalid status fails"""
        mock_complaint = MagicMock()
        mock_complaint.status = 'draft'
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        result = service.update_complaint_status(1, 'invalid_status')

        assert result['success'] is False
        assert result['error_code'] == 'INVALID_STATUS'

    def test_file_complaint_success(self, service):
        """File complaint sets all filing fields"""
        mock_complaint = MagicMock()
        mock_complaint.status = 'ready'
        mock_complaint.to_dict.return_value = {'id': 1, 'status': 'filed'}
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        result = service.file_complaint(
            1,
            filed_method='mail',
            tracking_number='123456789'
        )

        assert result['success'] is True
        assert mock_complaint.filed_method == 'mail'
        assert mock_complaint.tracking_number == '123456789'

    def test_file_complaint_invalid_method(self, service):
        """File complaint fails with invalid method"""
        mock_complaint = MagicMock()
        mock_complaint.status = 'ready'
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        result = service.file_complaint(1, filed_method='fax')

        assert result['success'] is False
        assert result['error_code'] == 'INVALID_FILING_METHOD'

    def test_file_complaint_wrong_status(self, service):
        """Cannot file already filed complaint"""
        mock_complaint = MagicMock()
        mock_complaint.status = 'filed'
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        result = service.file_complaint(1, filed_method='online')

        assert result['success'] is False
        assert result['error_code'] == 'INVALID_STATUS_FOR_FILING'

    def test_resolve_complaint_success(self, service):
        """Resolve complaint sets resolution fields"""
        mock_complaint = MagicMock()
        mock_complaint.status = 'investigating'
        mock_complaint.to_dict.return_value = {'id': 1, 'status': 'resolved'}
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        result = service.resolve_complaint(
            1,
            resolution_type='favorable',
            resolution_summary='Bureau agreed to delete items',
            damages_recovered=500.00
        )

        assert result['success'] is True
        assert mock_complaint.resolution_type == 'favorable'
        assert mock_complaint.damages_recovered == 500.00

    def test_resolve_complaint_invalid_type(self, service):
        """Resolve fails with invalid resolution type"""
        mock_complaint = MagicMock()
        mock_complaint.status = 'investigating'
        service.session.query.return_value.filter_by.return_value.first.return_value = mock_complaint

        result = service.resolve_complaint(1, resolution_type='invalid')

        assert result['success'] is False
        assert result['error_code'] == 'INVALID_RESOLUTION_TYPE'


class TestLetterGeneration:
    """Test complaint letter generation"""

    @pytest.fixture
    def service(self):
        """Create service with mock session"""
        from services.state_ag_service import StateAGService

        mock_session = MagicMock()
        service = StateAGService(session=mock_session)
        return service

    def test_generate_letter_template(self, service):
        """Generate letter using template"""
        # Setup mocks
        mock_complaint = MagicMock()
        mock_complaint.client_id = 1
        mock_complaint.violation_types = ['failure_to_investigate']
        mock_complaint.bureaus_complained = ['Equifax', 'Experian']
        mock_complaint.furnishers_complained = ['Test Creditor']
        mock_complaint.violation_summary = 'Test summary'
        mock_complaint.dispute_rounds_exhausted = 2
        mock_complaint.complaint_type = 'fcra_violation'

        mock_client = MagicMock()
        mock_client.first_name = 'John'
        mock_client.last_name = 'Doe'
        mock_client.address_street = '123 Main St'
        mock_client.address_city = 'Newark'
        mock_client.address_state = 'NJ'
        mock_client.address_zip = '07102'
        mock_client.ssn_last_four = '1234'
        mock_client.date_of_birth = datetime(1980, 1, 15)

        mock_ag_contact = MagicMock()
        mock_ag_contact.office_name = 'NJ Attorney General'
        mock_ag_contact.division_name = 'Consumer Affairs'
        mock_ag_contact.address_line1 = '124 Halsey St'
        mock_ag_contact.address_line2 = None
        mock_ag_contact.city = 'Newark'
        mock_ag_contact.state = 'NJ'
        mock_ag_contact.zip_code = '07102'
        mock_ag_contact.to_dict.return_value = {}

        mock_complaint.ag_contact = mock_ag_contact

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'StateAGComplaint':
                mock_query.filter_by.return_value.first.return_value = mock_complaint
            elif model.__name__ == 'Client':
                mock_query.filter_by.return_value.first.return_value = mock_client
            return mock_query

        service.session.query.side_effect = query_side_effect

        result = service.generate_complaint_letter(1, use_ai=False)

        assert result['success'] is True
        assert 'letter_content' in result['data']
        assert 'John Doe' in result['data']['letter_content']
        assert 'Fair Credit Reporting Act' in result['data']['letter_content']

    def test_generate_letter_complaint_not_found(self, service):
        """Generate letter fails if complaint not found"""
        service.session.query.return_value.filter_by.return_value.first.return_value = None

        result = service.generate_complaint_letter(999)

        assert result['success'] is False
        assert result['error_code'] == 'COMPLAINT_NOT_FOUND'


class TestStatisticsAndReporting:
    """Test statistics and reporting functions"""

    @pytest.fixture
    def service(self):
        """Create service with mock session"""
        from services.state_ag_service import StateAGService

        mock_session = MagicMock()
        service = StateAGService(session=mock_session)
        return service

    def test_get_complaint_statistics(self, service):
        """Get complaint statistics"""
        # Mock status counts
        service.session.query.return_value.group_by.return_value.all.return_value = [
            ('draft', 5),
            ('filed', 10),
            ('resolved', 3)
        ]
        service.session.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        service.session.query.return_value.filter.return_value.scalar.return_value = 1500.00
        service.session.query.return_value.filter.return_value.count.return_value = 8

        result = service.get_complaint_statistics()

        assert result['success'] is True
        assert 'by_status' in result['data']

    def test_get_overdue_complaints(self, service):
        """Get overdue complaints"""
        mock_complaint = MagicMock()
        mock_complaint.to_dict.return_value = {
            'id': 1,
            'status': 'filed',
            'filed_at': (datetime.utcnow() - timedelta(days=90)).isoformat()
        }
        service.session.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_complaint]

        overdue = service.get_overdue_complaints(days_threshold=60)

        assert len(overdue) == 1

    def test_get_escalation_candidates(self, service):
        """Get clients who are candidates for AG escalation"""
        mock_client = MagicMock()
        mock_client.id = 1
        mock_client.first_name = 'John'
        mock_client.last_name = 'Doe'
        mock_client.address_state = 'NJ'
        mock_client.current_dispute_round = 3
        mock_client.dispute_status = 'in_progress'

        # Mock the subquery for existing complaints
        mock_subquery = MagicMock()
        service.session.query.return_value.distinct.return_value = mock_subquery

        # Mock the main query
        service.session.query.return_value.filter.return_value.all.return_value = [mock_client]

        candidates = service.get_escalation_candidates(min_dispute_rounds=2)

        assert len(candidates) == 1
        assert candidates[0]['dispute_rounds'] == 3


class TestResponseHelpers:
    """Test response helper methods"""

    def test_success_response(self):
        """Success response format"""
        from services.state_ag_service import StateAGService

        service = StateAGService()
        response = service._success_response({'test': 'data'}, 'Test message')

        assert response['success'] is True
        assert response['data'] == {'test': 'data'}
        assert response['message'] == 'Test message'

    def test_error_response(self):
        """Error response format"""
        from services.state_ag_service import StateAGService

        service = StateAGService()
        response = service._error_response('Test error', 'TEST_ERROR', {'detail': 'info'})

        assert response['success'] is False
        assert response['error'] == 'Test error'
        assert response['error_code'] == 'TEST_ERROR'
        assert response['details'] == {'detail': 'info'}


class TestComplaintModel:
    """Test StateAGComplaint model methods"""

    def test_get_days_since_filed(self):
        """Calculate days since complaint was filed"""
        from database import StateAGComplaint

        complaint = StateAGComplaint()
        complaint.filed_at = datetime.utcnow() - timedelta(days=10)

        days = complaint.get_days_since_filed()
        assert days == 10

    def test_get_days_since_filed_not_filed(self):
        """Returns None if not filed"""
        from database import StateAGComplaint

        complaint = StateAGComplaint()
        complaint.filed_at = None

        days = complaint.get_days_since_filed()
        assert days is None

    def test_is_overdue_for_response(self):
        """Check if complaint is overdue"""
        from database import StateAGComplaint

        complaint = StateAGComplaint()
        complaint.status = 'filed'
        complaint.filed_at = datetime.utcnow() - timedelta(days=45)

        assert complaint.is_overdue_for_response(expected_days=30) is True
        assert complaint.is_overdue_for_response(expected_days=60) is False

    def test_is_overdue_resolved_complaint(self):
        """Resolved complaints are not overdue"""
        from database import StateAGComplaint

        complaint = StateAGComplaint()
        complaint.status = 'resolved'
        complaint.filed_at = datetime.utcnow() - timedelta(days=100)

        assert complaint.is_overdue_for_response() is False

    def test_to_dict(self):
        """Complaint serializes to dict"""
        from database import StateAGComplaint

        complaint = StateAGComplaint()
        complaint.id = 1
        complaint.client_id = 10
        complaint.complaint_type = 'fcra_violation'
        complaint.status = 'draft'
        complaint.bureaus_complained = ['Equifax']
        complaint.created_at = datetime.utcnow()

        data = complaint.to_dict()

        assert data['id'] == 1
        assert data['client_id'] == 10
        assert data['complaint_type'] == 'fcra_violation'
        assert 'Equifax' in data['bureaus_complained']


class TestStateAGContactModel:
    """Test StateAGContact model"""

    def test_to_dict(self):
        """AG contact serializes to dict"""
        from database import StateAGContact

        contact = StateAGContact()
        contact.id = 1
        contact.state_code = 'NJ'
        contact.state_name = 'New Jersey'
        contact.office_name = 'Attorney General'
        contact.city = 'Newark'
        contact.accepts_online = True

        data = contact.to_dict()

        assert data['id'] == 1
        assert data['state_code'] == 'NJ'
        assert data['accepts_online'] is True


class TestEdgeCases:
    """Test edge cases and error handling"""

    @pytest.fixture
    def service(self):
        """Create service with mock session"""
        from services.state_ag_service import StateAGService

        mock_session = MagicMock()
        service = StateAGService(session=mock_session)
        return service

    def test_create_complaint_state_not_found(self, service):
        """Create fails if state AG not in database"""
        mock_client = MagicMock()

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Client':
                mock_query.filter_by.return_value.first.return_value = mock_client
            elif model.__name__ == 'StateAGContact':
                mock_query.filter_by.return_value.first.return_value = None
            return mock_query

        service.session.query.side_effect = query_side_effect

        result = service.create_complaint(
            client_id=1,
            state_code='ZZ',  # Invalid state
            complaint_type='fcra_violation'
        )

        assert result['success'] is False
        assert result['error_code'] == 'STATE_NOT_FOUND'

    def test_seed_handles_exception(self, service):
        """Seeding handles database errors gracefully"""
        service.session.query.side_effect = Exception("Database error")

        result = service.seed_ag_contacts()

        assert result['success'] is False
        assert 'Database error' in result['error']

    def test_create_complaint_handles_exception(self, service):
        """Create handles database errors gracefully"""
        mock_client = MagicMock()
        mock_ag_contact = MagicMock()
        mock_ag_contact.id = 1

        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'Client':
                mock_query.filter_by.return_value.first.return_value = mock_client
            elif model.__name__ == 'StateAGContact':
                mock_query.filter_by.return_value.first.return_value = mock_ag_contact
            return mock_query

        service.session.query.side_effect = query_side_effect
        service.session.add.side_effect = Exception("Insert failed")

        result = service.create_complaint(
            client_id=1,
            state_code='NJ',
            complaint_type='fcra_violation'
        )

        assert result['success'] is False
        assert result['error_code'] == 'CREATE_ERROR'

    def test_state_code_case_insensitive(self, service):
        """State code lookups are case-insensitive"""
        mock_contact = MagicMock()
        mock_contact.to_dict.return_value = {'state_code': 'NJ'}

        service.session.query.return_value.filter_by.return_value.first.return_value = mock_contact

        # Test lowercase
        contact = service.get_ag_contact_by_state('nj')
        assert contact is not None

        # Verify uppercase was used in query
        service.session.query.return_value.filter_by.assert_called_with(state_code='NJ')
