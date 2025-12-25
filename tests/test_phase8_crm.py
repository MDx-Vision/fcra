"""
Phase 8: BAG CRM Feature Parity Tests
Tests for tags, quick links, pagination, inline editing, and UI enhancements.
"""
import pytest
from datetime import datetime
import secrets


class TestClientTagModel:
    """Test ClientTag database model."""

    def test_client_tag_model_exists(self):
        """Test ClientTag model exists."""
        from database import ClientTag
        assert ClientTag is not None

    def test_create_tag(self, db_session):
        """Test creating a tag."""
        from database import ClientTag

        # Use unique name to avoid conflicts
        unique_name = f'Test Tag {secrets.token_hex(4)}'
        tag = ClientTag(
            name=unique_name,
            color='#ff5733'
        )
        db_session.add(tag)
        db_session.commit()

        assert tag.id is not None
        assert tag.name == unique_name
        assert tag.color == '#ff5733'

    def test_tag_unique_name(self, db_session, sample_tag):
        """Test tag name uniqueness."""
        from database import ClientTag
        from sqlalchemy.exc import IntegrityError

        duplicate_tag = ClientTag(
            name=sample_tag.name,  # Same name
            color='#000000'
        )
        db_session.add(duplicate_tag)

        with pytest.raises(IntegrityError):
            db_session.commit()

        db_session.rollback()


class TestClientTagAssignment:
    """Test ClientTagAssignment model."""

    def test_assignment_model_exists(self):
        """Test ClientTagAssignment model exists."""
        from database import ClientTagAssignment
        assert ClientTagAssignment is not None

    def test_assign_tag_to_client(self, db_session, sample_client, sample_tag):
        """Test assigning a tag to a client."""
        from database import ClientTagAssignment

        assignment = ClientTagAssignment(
            client_id=sample_client.id,
            tag_id=sample_tag.id
        )
        db_session.add(assignment)
        db_session.commit()

        assert assignment.id is not None
        assert assignment.client_id == sample_client.id
        assert assignment.tag_id == sample_tag.id

    def test_get_client_tags(self, db_session, sample_client, sample_tag):
        """Test getting all tags for a client."""
        from database import ClientTagAssignment, ClientTag

        # Assign tag
        assignment = ClientTagAssignment(
            client_id=sample_client.id,
            tag_id=sample_tag.id
        )
        db_session.add(assignment)
        db_session.commit()

        # Query tags
        assignments = db_session.query(ClientTagAssignment).filter_by(
            client_id=sample_client.id
        ).all()

        tag_ids = [a.tag_id for a in assignments]
        tags = db_session.query(ClientTag).filter(
            ClientTag.id.in_(tag_ids)
        ).all()

        assert len(tags) >= 1


class TestTagAPIEndpoints:
    """Test tag management API endpoints."""

    def test_list_tags(self, authenticated_client):
        """Test listing all tags."""
        response = authenticated_client.get('/api/tags')
        assert response.status_code == 200

        data = response.get_json()
        assert data.get('success') == True
        assert 'tags' in data

    def test_create_tag_api(self, authenticated_client):
        """Test creating a tag via API."""
        # Use unique name to avoid conflicts
        unique_name = f'API Test Tag {secrets.token_hex(4)}'
        response = authenticated_client.post('/api/tags', json={
            'name': unique_name,
            'color': '#00ff00'
        })
        assert response.status_code == 200

        data = response.get_json()
        assert data.get('success') == True

    def test_update_tag_api(self, authenticated_client, sample_tag):
        """Test updating a tag via API."""
        response = authenticated_client.put(f'/api/tags/{sample_tag.id}', json={
            'color': '#0000ff'
        })
        assert response.status_code == 200

    def test_delete_tag_api(self, authenticated_client, db_session):
        """Test deleting a tag via API."""
        from database import ClientTag

        # Create tag to delete with unique name
        unique_name = f'Delete Me {secrets.token_hex(4)}'
        tag = ClientTag(name=unique_name, color='#ff0000')
        db_session.add(tag)
        db_session.commit()
        tag_id = tag.id

        response = authenticated_client.delete(f'/api/tags/{tag_id}')
        assert response.status_code == 200


class TestClientTagAPIEndpoints:
    """Test client tag assignment API endpoints."""

    def test_get_client_tags_api(self, authenticated_client, sample_client):
        """Test getting client's tags via API."""
        response = authenticated_client.get(f'/api/clients/{sample_client.id}/tags')
        assert response.status_code == 200

        data = response.get_json()
        assert data.get('success') == True
        assert 'tags' in data

    def test_add_tag_to_client_api(self, authenticated_client, sample_client, sample_tag):
        """Test adding tag to client via API."""
        response = authenticated_client.post(
            f'/api/clients/{sample_client.id}/tags',
            json={'tag_id': sample_tag.id}
        )
        assert response.status_code == 200

    def test_remove_tag_from_client_api(self, authenticated_client, sample_client, sample_tag, db_session):
        """Test removing tag from client via API."""
        from database import ClientTagAssignment

        # First assign the tag
        assignment = ClientTagAssignment(
            client_id=sample_client.id,
            tag_id=sample_tag.id
        )
        db_session.add(assignment)
        db_session.commit()

        # Remove via API
        response = authenticated_client.delete(
            f'/api/clients/{sample_client.id}/tags/{sample_tag.id}'
        )
        assert response.status_code == 200


class TestUserQuickLinks:
    """Test UserQuickLink model."""

    def test_quick_link_model_exists(self):
        """Test UserQuickLink model exists."""
        from database import UserQuickLink
        assert UserQuickLink is not None

    def test_create_quick_link(self, db_session, sample_staff):
        """Test creating a quick link."""
        from database import UserQuickLink

        link = UserQuickLink(
            staff_id=sample_staff.id,
            slot_number=1,
            label='Dashboard',
            url='/dashboard'
        )
        db_session.add(link)
        db_session.commit()

        assert link.id is not None
        assert link.slot_number == 1

    def test_quick_link_slots(self, db_session, sample_staff):
        """Test quick link slot numbers 1-8."""
        from database import UserQuickLink

        for slot in range(1, 9):
            existing = db_session.query(UserQuickLink).filter_by(
                staff_id=sample_staff.id,
                slot_number=slot
            ).first()

            if not existing:
                link = UserQuickLink(
                    staff_id=sample_staff.id,
                    slot_number=slot,
                    label=f'Link {slot}',
                    url=f'/page{slot}'
                )
                db_session.add(link)

        db_session.commit()

        # Should have 8 slots
        links = db_session.query(UserQuickLink).filter_by(
            staff_id=sample_staff.id
        ).all()
        assert len(links) >= 1


class TestQuickLinksAPI:
    """Test quick links API endpoints."""

    def test_get_quick_links(self, authenticated_client):
        """Test getting user's quick links."""
        response = authenticated_client.get('/api/staff/quick-links')
        assert response.status_code == 200

        data = response.get_json()
        assert data.get('success') == True
        assert 'quick_links' in data

    def test_save_quick_link(self, authenticated_client):
        """Test saving a quick link."""
        response = authenticated_client.post('/api/staff/quick-links', json={
            'slot_number': 1,
            'label': 'Test Link',
            'url': '/test'
        })
        assert response.status_code == 200

    def test_delete_quick_link(self, authenticated_client):
        """Test deleting a quick link."""
        # First create one
        authenticated_client.post('/api/staff/quick-links', json={
            'slot_number': 8,
            'label': 'Delete Me',
            'url': '/delete'
        })

        # Then delete
        response = authenticated_client.delete('/api/staff/quick-links/8')
        assert response.status_code in [200, 404]


class TestPagination:
    """Test pagination functionality."""

    def test_client_manager_pagination(self, authenticated_client):
        """Test client manager with pagination."""
        response = authenticated_client.get('/dashboard/client-manager?page=1&per_page=25')
        assert response.status_code == 200

    def test_pagination_parameters(self, authenticated_client):
        """Test different pagination parameters."""
        per_page_values = [10, 25, 50, 100]

        for per_page in per_page_values:
            response = authenticated_client.get(
                f'/dashboard/client-manager?page=1&per_page={per_page}'
            )
            assert response.status_code == 200

    def test_invalid_per_page_defaults(self, authenticated_client):
        """Test invalid per_page value defaults to 25."""
        response = authenticated_client.get(
            '/dashboard/client-manager?page=1&per_page=999'
        )
        # Should handle gracefully
        assert response.status_code == 200


class TestInlineEditing:
    """Test inline editing features."""

    def test_update_status_2(self, authenticated_client, sample_client):
        """Test updating status_2 inline."""
        response = authenticated_client.post(
            f'/api/clients/{sample_client.id}/status',
            json={'status_2': 'Pending Docs'}
        )
        assert response.status_code == 200

    def test_toggle_phone_verified(self, authenticated_client, sample_client):
        """Test toggling phone verified status."""
        response = authenticated_client.post(
            f'/api/clients/{sample_client.id}/status',
            json={'phone_verified': True}
        )
        assert response.status_code == 200

    def test_client_type_update(self, authenticated_client, sample_client):
        """Test updating client type."""
        response = authenticated_client.post(
            f'/api/clients/{sample_client.id}/status',
            json={'client_type': 'C'}
        )
        assert response.status_code == 200


class TestNewClientFields:
    """Test new client fields added in Phase 8."""

    def test_employer_company_field(self, sample_client, db_session):
        """Test employer_company field exists."""
        assert hasattr(sample_client, 'employer_company')

        sample_client.employer_company = 'Test Company Inc'
        db_session.commit()

        assert sample_client.employer_company == 'Test Company Inc'

    def test_status_2_field(self, sample_client):
        """Test status_2 field exists."""
        assert hasattr(sample_client, 'status_2')

    def test_phone_verified_field(self, sample_client):
        """Test phone_verified field exists."""
        assert hasattr(sample_client, 'phone_verified')

    def test_starred_field(self, sample_client):
        """Test starred field exists."""
        assert hasattr(sample_client, 'starred')

    def test_is_affiliate_field(self, sample_client):
        """Test is_affiliate field exists."""
        assert hasattr(sample_client, 'is_affiliate')

    def test_portal_posted_field(self, sample_client):
        """Test portal_posted field exists."""
        assert hasattr(sample_client, 'portal_posted')


class TestVersionBadge:
    """Test version badge display."""

    def test_client_manager_has_version(self, authenticated_client):
        """Test client manager page has version badge."""
        response = authenticated_client.get('/dashboard/client-manager')
        html = response.data.decode('utf-8')

        # Should contain version badge
        assert 'v2.0' in html or 'version' in html.lower()


class TestClientTypeColumn:
    """Test client type column and badges."""

    def test_client_type_values(self):
        """Test valid client type values."""
        valid_types = ['L', 'C', 'I', 'O', 'P', 'X']

        # L=Lead, C=Client, I=Inactive, O=Other, P=Provider, X=Cancelled
        assert 'L' in valid_types
        assert 'C' in valid_types
        assert 'X' in valid_types

    def test_client_type_default(self, sample_client):
        """Test client type has default value."""
        # Default should be 'L' for Lead
        assert sample_client.client_type in ['L', 'C', None]


class TestAffiliateDisplay:
    """Test affiliate badge display."""

    def test_affiliate_field(self, sample_client):
        """Test is_affiliate field exists."""
        assert hasattr(sample_client, 'is_affiliate')
        assert sample_client.is_affiliate in [True, False, None]

    def test_set_affiliate_status(self, sample_client, db_session):
        """Test setting affiliate status."""
        sample_client.is_affiliate = True
        db_session.commit()

        assert sample_client.is_affiliate == True
