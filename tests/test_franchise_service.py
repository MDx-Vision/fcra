"""
Unit tests for Franchise Service
Tests for franchise/organization creation, member management,
permissions/access control, client management, and revenue tracking.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.franchise_service import (
    FranchiseService,
    get_org_filter,
    get_clients_for_org,
)
from database import (
    FRANCHISE_ORG_TYPES,
    FRANCHISE_MEMBER_ROLES,
)


# ============== Fixtures ==============


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock()
    db.query.return_value = db
    db.filter.return_value = db
    db.filter_by.return_value = db
    db.first.return_value = None
    db.all.return_value = []
    db.count.return_value = 0
    db.order_by.return_value = db
    db.limit.return_value = db
    db.scalar.return_value = None
    return db


@pytest.fixture
def service(mock_db):
    """Create FranchiseService instance with mocked db."""
    return FranchiseService(mock_db)


@pytest.fixture
def mock_organization():
    """Create a mock FranchiseOrganization."""
    org = Mock()
    org.id = 1
    org.name = "Test Organization"
    org.slug = "test-organization"
    org.org_type = "branch"
    org.parent_org_id = None
    org.parent = None
    org.is_active = True
    org.members = []
    org.clients = []
    org.settings = {}
    org.revenue_share_percent = 10.0
    org.max_users = 10
    org.max_clients = 100
    org.subscription_tier = "basic"
    org.license_number = "LIC-001"
    org.billing_contact_email = "billing@test.com"
    org.to_dict = Mock(return_value={
        'id': 1,
        'name': 'Test Organization',
        'slug': 'test-organization',
        'org_type': 'branch',
    })
    return org


@pytest.fixture
def mock_staff():
    """Create a mock Staff user."""
    staff = Mock()
    staff.id = 1
    staff.email = "staff@test.com"
    staff.first_name = "Test"
    staff.last_name = "Staff"
    staff.role = "paralegal"
    staff.full_name = "Test Staff"
    return staff


@pytest.fixture
def mock_admin_staff():
    """Create a mock admin Staff user."""
    staff = Mock()
    staff.id = 2
    staff.email = "admin@test.com"
    staff.first_name = "Admin"
    staff.last_name = "User"
    staff.role = "admin"
    staff.full_name = "Admin User"
    return staff


@pytest.fixture
def mock_client():
    """Create a mock Client."""
    client = Mock()
    client.id = 1
    client.name = "Test Client"
    client.email = "client@test.com"
    client.status = "active"
    return client


@pytest.fixture
def mock_membership():
    """Create a mock OrganizationMembership."""
    membership = Mock()
    membership.id = 1
    membership.organization_id = 1
    membership.staff_id = 1
    membership.role = "staff"
    membership.permissions = []
    membership.is_primary = True
    membership.organization = Mock()
    membership.organization.is_active = True
    membership.organization.name = "Test Organization"
    membership.has_permission = Mock(return_value=True)
    membership.to_dict = Mock(return_value={
        'id': 1,
        'organization_id': 1,
        'staff_id': 1,
        'role': 'staff',
    })
    return membership


# ============== Organization Creation Tests ==============


class TestCreateOrganization:
    """Tests for create_organization method."""

    def test_create_organization_success(self, service, mock_db):
        """Test successful organization creation."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.create_organization(
            name="New Law Firm",
            org_type="branch",
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_organization_invalid_org_type(self, service):
        """Test organization creation with invalid org_type."""
        with pytest.raises(ValueError) as exc_info:
            service.create_organization(
                name="New Law Firm",
                org_type="invalid_type",
            )
        assert "Invalid org_type" in str(exc_info.value)

    def test_create_organization_with_parent(self, service, mock_db, mock_organization):
        """Test organization creation with parent organization."""
        mock_organization.org_type = "headquarters"
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_organization,  # Parent org lookup
            None,  # Slug check during _generate_slug
            None,  # Existing slug check
        ]

        result = service.create_organization(
            name="Branch Office",
            org_type="branch",
            parent_org_id=1,
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_organization_parent_not_found(self, service, mock_db):
        """Test organization creation when parent not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            service.create_organization(
                name="Branch Office",
                org_type="branch",
                parent_org_id=999,
            )
        assert "Parent organization with ID 999 not found" in str(exc_info.value)

    def test_create_organization_invalid_hierarchy(self, service, mock_db, mock_organization):
        """Test organization creation with invalid hierarchy level."""
        mock_organization.org_type = "branch"  # Level 2
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization

        # Trying to create a headquarters under a branch (invalid)
        with pytest.raises(ValueError) as exc_info:
            service.create_organization(
                name="Sub Branch",
                org_type="headquarters",  # Level 0
                parent_org_id=1,
            )
        assert "Child organization type must be lower in hierarchy than parent" in str(exc_info.value)

    def test_create_organization_duplicate_slug(self, service, mock_db, mock_organization):
        """Test organization creation with duplicate slug."""
        # First call for slug generation check, return existing org
        # Second call for explicit slug check, also return existing org
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization

        with pytest.raises(ValueError) as exc_info:
            service.create_organization(
                name="Test Organization",
                org_type="branch",
                slug="test-organization",
            )
        assert "already exists" in str(exc_info.value)

    def test_create_organization_with_all_fields(self, service, mock_db):
        """Test organization creation with all optional fields."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.create_organization(
            name="Full Law Firm",
            org_type="regional",
            address="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            phone="555-1234",
            email="contact@firm.com",
            manager_staff_id=1,
            is_active=True,
            settings={"theme": "dark"},
            revenue_share_percent=15.0,
        )

        mock_db.add.assert_called_once()


class TestSlugGeneration:
    """Tests for slug generation."""

    def test_generate_slug_simple(self, service, mock_db):
        """Test slug generation from simple name."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        slug = service._generate_slug("Test Name")
        assert slug == "test-name"

    def test_generate_slug_with_special_chars(self, service, mock_db):
        """Test slug generation removes special characters."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        slug = service._generate_slug("Test & Co. Law Firm!")
        assert slug == "test-co-law-firm"

    def test_generate_slug_with_duplicate(self, service, mock_db):
        """Test slug generation appends number for duplicates."""
        existing_org = Mock()
        # First check returns existing, second returns None
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            existing_org,
            None,
        ]

        slug = service._generate_slug("Test Name")
        assert slug == "test-name-1"


# ============== Organization Update Tests ==============


class TestUpdateOrganization:
    """Tests for update_organization method."""

    def test_update_organization_success(self, service, mock_db, mock_organization):
        """Test successful organization update."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization

        result = service.update_organization(1, name="Updated Name")

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_organization_not_found(self, service, mock_db):
        """Test update when organization not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.update_organization(999, name="Updated Name")

        assert result is None
        mock_db.commit.assert_not_called()

    def test_update_organization_duplicate_slug(self, service, mock_db, mock_organization):
        """Test update with duplicate slug."""
        mock_organization.slug = "original-slug"
        other_org = Mock()
        other_org.id = 2

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization
        mock_db.query.return_value.filter.return_value.first.return_value = other_org

        with pytest.raises(ValueError) as exc_info:
            service.update_organization(1, slug="existing-slug")
        assert "already exists" in str(exc_info.value)

    def test_update_organization_invalid_org_type(self, service, mock_db, mock_organization):
        """Test update with invalid org_type."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization

        with pytest.raises(ValueError) as exc_info:
            service.update_organization(1, org_type="invalid_type")
        assert "Invalid org_type" in str(exc_info.value)

    def test_update_organization_ignores_unknown_fields(self, service, mock_db, mock_organization):
        """Test that unknown fields are ignored during update."""
        mock_organization.slug = "existing-slug"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization

        result = service.update_organization(1, unknown_field="value", name="Valid Name")

        # Should not raise an error, and commit should be called
        mock_db.commit.assert_called_once()


# ============== Organization Delete Tests ==============


class TestDeleteOrganization:
    """Tests for delete_organization method."""

    def test_delete_organization_success(self, service, mock_db, mock_organization):
        """Test successful organization deletion (soft delete)."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        result = service.delete_organization(1)

        assert result is True
        mock_db.commit.assert_called_once()

    def test_delete_organization_not_found(self, service, mock_db):
        """Test deletion when organization not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.delete_organization(999)

        assert result is False
        mock_db.commit.assert_not_called()

    def test_delete_organization_with_children(self, service, mock_db, mock_organization):
        """Test deletion fails when organization has children."""
        child_org = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization
        mock_db.query.return_value.filter_by.return_value.all.return_value = [child_org]

        with pytest.raises(ValueError) as exc_info:
            service.delete_organization(1)
        assert "Cannot delete organization with child organizations" in str(exc_info.value)


# ============== Organization Retrieval Tests ==============


class TestGetOrganization:
    """Tests for organization retrieval methods."""

    def test_get_organization_by_id(self, service, mock_db, mock_organization):
        """Test getting organization by ID."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization

        result = service.get_organization_by_id(1)

        assert result == mock_organization

    def test_get_organization_by_id_not_found(self, service, mock_db):
        """Test getting organization by ID when not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.get_organization_by_id(999)

        assert result is None

    def test_get_organization_by_slug(self, service, mock_db, mock_organization):
        """Test getting organization by slug."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization

        result = service.get_organization_by_slug("test-organization")

        assert result == mock_organization

    def test_get_all_organizations(self, service, mock_db, mock_organization):
        """Test getting all active organizations."""
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [mock_organization]

        result = service.get_all_organizations()

        assert len(result) == 1

    def test_get_all_organizations_include_inactive(self, service, mock_db, mock_organization):
        """Test getting all organizations including inactive."""
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_organization]

        result = service.get_all_organizations(include_inactive=True)

        assert len(result) == 1


class TestGetOrganizationHierarchy:
    """Tests for get_organization_hierarchy method."""

    def test_get_hierarchy_with_org_id(self, service, mock_db, mock_organization):
        """Test getting hierarchy starting from specific org."""
        mock_organization.children = []
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_organization
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            result = service.get_organization_hierarchy(1)

        assert len(result) == 1

    def test_get_hierarchy_org_not_found(self, service, mock_db):
        """Test getting hierarchy when org not found."""
        with patch.object(service, 'get_organization_by_id', return_value=None):
            result = service.get_organization_hierarchy(999)

        assert result == []

    def test_get_hierarchy_all_root_orgs(self, service, mock_db, mock_organization):
        """Test getting hierarchy for all root organizations."""
        mock_organization.children = []
        mock_organization.members = []
        mock_organization.clients = []

        # Setup the query chain for root orgs
        query_mock = Mock()
        query_mock.filter.return_value.order_by.return_value.all.return_value = [mock_organization]
        query_mock.filter_by.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = query_mock

        result = service.get_organization_hierarchy(None)

        assert len(result) == 1


class TestGetChildOrganizations:
    """Tests for get_child_organizations method."""

    def test_get_direct_children(self, service, mock_db, mock_organization):
        """Test getting direct children only."""
        child1 = Mock()
        child1.id = 2
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [child1]

        result = service.get_child_organizations(1, recursive=False)

        assert len(result) == 1

    def test_get_children_recursive(self, service, mock_db):
        """Test getting all descendants recursively."""
        child1 = Mock()
        child1.id = 2
        grandchild = Mock()
        grandchild.id = 3

        # First call returns child1, second call returns grandchild, third returns empty
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.side_effect = [
            [child1],
            [grandchild],
            [],
        ]

        result = service.get_child_organizations(1, recursive=True)

        assert len(result) == 2


# ============== Member Management Tests ==============


class TestAddMember:
    """Tests for add_member method."""

    def test_add_member_success(self, service, mock_db, mock_organization, mock_staff):
        """Test successful member addition."""
        # Set up side_effect to return staff first, then None for membership check
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_staff,  # staff lookup
            None,  # existing membership check
        ]

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            result = service.add_member(1, 1, role="staff")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_add_member_org_not_found(self, service, mock_db):
        """Test adding member when organization not found."""
        with patch.object(service, 'get_organization_by_id', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                service.add_member(999, 1)
            assert "Organization with ID 999 not found" in str(exc_info.value)

    def test_add_member_staff_not_found(self, service, mock_db, mock_organization):
        """Test adding member when staff not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with pytest.raises(ValueError) as exc_info:
                service.add_member(1, 999)
            assert "Staff user with ID 999 not found" in str(exc_info.value)

    def test_add_member_invalid_role(self, service, mock_db, mock_organization, mock_staff):
        """Test adding member with invalid role."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with pytest.raises(ValueError) as exc_info:
                service.add_member(1, 1, role="invalid_role")
            assert "Invalid role" in str(exc_info.value)

    def test_add_member_already_exists(self, service, mock_db, mock_organization, mock_staff, mock_membership):
        """Test adding member who is already a member."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_staff,  # staff lookup
            mock_membership,  # existing membership check
        ]

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with pytest.raises(ValueError) as exc_info:
                service.add_member(1, 1)
            assert "already a member" in str(exc_info.value)

    def test_add_member_as_primary(self, service, mock_db, mock_organization, mock_staff):
        """Test adding member and setting as primary."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_staff,  # staff lookup
            None,  # existing membership check
        ]
        mock_db.query.return_value.filter_by.return_value.update.return_value = None

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            result = service.add_member(1, 1, is_primary=True)

        mock_db.add.assert_called_once()


class TestUpdateMember:
    """Tests for update_member method."""

    def test_update_member_success(self, service, mock_db, mock_membership):
        """Test successful member update."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_membership

        result = service.update_member(1, 1, role="manager")

        mock_db.commit.assert_called_once()

    def test_update_member_not_found(self, service, mock_db):
        """Test updating member when not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.update_member(1, 999)

        assert result is None

    def test_update_member_invalid_role(self, service, mock_db, mock_membership):
        """Test updating member with invalid role."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_membership

        with pytest.raises(ValueError) as exc_info:
            service.update_member(1, 1, role="invalid_role")
        assert "Invalid role" in str(exc_info.value)

    def test_update_member_set_primary(self, service, mock_db, mock_membership):
        """Test setting member as primary clears other primary flags."""
        mock_membership.is_primary = False
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_membership
        mock_db.query.return_value.filter_by.return_value.update.return_value = None

        result = service.update_member(1, 1, is_primary=True)

        mock_db.commit.assert_called()


class TestRemoveMember:
    """Tests for remove_member method."""

    def test_remove_member_success(self, service, mock_db, mock_membership):
        """Test successful member removal."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_membership

        result = service.remove_member(1, 1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_membership)
        mock_db.commit.assert_called_once()

    def test_remove_member_not_found(self, service, mock_db):
        """Test removing member when not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.remove_member(1, 999)

        assert result is False
        mock_db.delete.assert_not_called()


class TestGetOrganizationMembers:
    """Tests for get_organization_members method."""

    def test_get_organization_members(self, service, mock_db, mock_membership):
        """Test getting all members of an organization."""
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_membership]

        result = service.get_organization_members(1)

        assert len(result) == 1


# ============== Client Management Tests ==============


class TestAssignClientToOrg:
    """Tests for assign_client_to_org method."""

    def test_assign_client_success(self, service, mock_db, mock_organization, mock_client):
        """Test successful client assignment."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_client,  # client lookup
            None,  # existing assignment check
        ]

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            result = service.assign_client_to_org(1, 1)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_assign_client_org_not_found(self, service, mock_db):
        """Test assigning client when organization not found."""
        with patch.object(service, 'get_organization_by_id', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                service.assign_client_to_org(1, 999)
            assert "Organization with ID 999 not found" in str(exc_info.value)

    def test_assign_client_not_found(self, service, mock_db, mock_organization):
        """Test assigning client when client not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with pytest.raises(ValueError) as exc_info:
                service.assign_client_to_org(999, 1)
            assert "Client with ID 999 not found" in str(exc_info.value)

    def test_assign_client_already_assigned(self, service, mock_db, mock_organization, mock_client):
        """Test assigning client who is already assigned."""
        existing_assignment = Mock()
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_client,  # client lookup
            existing_assignment,  # existing assignment
        ]

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with pytest.raises(ValueError) as exc_info:
                service.assign_client_to_org(1, 1)
            assert "already assigned" in str(exc_info.value)


class TestUnassignClientFromOrg:
    """Tests for unassign_client_from_org method."""

    def test_unassign_client_success(self, service, mock_db):
        """Test successful client unassignment."""
        assignment = Mock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = assignment

        result = service.unassign_client_from_org(1, 1)

        assert result is True
        mock_db.delete.assert_called_once_with(assignment)

    def test_unassign_client_not_found(self, service, mock_db):
        """Test unassigning client when assignment not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.unassign_client_from_org(1, 1)

        assert result is False


class TestGetOrganizationClients:
    """Tests for get_organization_clients method."""

    def test_get_clients_single_org(self, service, mock_db):
        """Test getting clients for a single organization."""
        assignment = Mock()
        mock_db.query.return_value.filter_by.return_value.all.return_value = [assignment]

        result = service.get_organization_clients(1, include_child_orgs=False)

        assert len(result) == 1

    def test_get_clients_include_children(self, service, mock_db, mock_organization):
        """Test getting clients including child organizations."""
        assignment = Mock()
        child_org = Mock()
        child_org.id = 2

        mock_db.query.return_value.filter.return_value.all.return_value = [assignment]

        with patch.object(service, 'get_child_organizations', return_value=[child_org]):
            result = service.get_organization_clients(1, include_child_orgs=True)

        assert len(result) == 1


# ============== Transfer Tests ==============


class TestTransferClient:
    """Tests for transfer_client method."""

    def test_transfer_client_success(self, service, mock_db, mock_organization, mock_client):
        """Test successful client transfer initiation."""
        from_org = Mock()
        from_org.id = 1
        to_org = Mock()
        to_org.id = 2
        assignment = Mock()

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_client,  # client lookup
            assignment,  # client assignment check
            None,  # pending transfer check
        ]

        with patch.object(service, 'get_organization_by_id', side_effect=[from_org, to_org]):
            result = service.transfer_client(1, 1, 2, "Moving to new branch", 1)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_transfer_client_not_found(self, service, mock_db):
        """Test transfer when client not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            service.transfer_client(999, 1, 2, "reason", 1)
        assert "Client with ID 999 not found" in str(exc_info.value)

    def test_transfer_from_org_not_found(self, service, mock_db, mock_client):
        """Test transfer when source org not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        with patch.object(service, 'get_organization_by_id', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                service.transfer_client(1, 999, 2, "reason", 1)
            assert "Source organization with ID 999 not found" in str(exc_info.value)

    def test_transfer_to_org_not_found(self, service, mock_db, mock_client, mock_organization):
        """Test transfer when destination org not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client

        with patch.object(service, 'get_organization_by_id', side_effect=[mock_organization, None]):
            with pytest.raises(ValueError) as exc_info:
                service.transfer_client(1, 1, 999, "reason", 1)
            assert "Destination organization with ID 999 not found" in str(exc_info.value)

    def test_transfer_client_not_in_source_org(self, service, mock_db, mock_client, mock_organization):
        """Test transfer when client not assigned to source org."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_client,  # client lookup
            None,  # client assignment check - not found
        ]

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with pytest.raises(ValueError) as exc_info:
                service.transfer_client(1, 1, 2, "reason", 1)
            assert "not assigned to the source organization" in str(exc_info.value)

    def test_transfer_invalid_transfer_type(self, service, mock_db, mock_client, mock_organization):
        """Test transfer with invalid transfer type."""
        assignment = Mock()
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_client,
            assignment,
        ]

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with pytest.raises(ValueError) as exc_info:
                service.transfer_client(1, 1, 2, "reason", 1, transfer_type="invalid")
            assert "Invalid transfer_type" in str(exc_info.value)

    def test_transfer_pending_transfer_exists(self, service, mock_db, mock_client, mock_organization):
        """Test transfer when client has pending transfer."""
        assignment = Mock()
        pending_transfer = Mock()
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            mock_client,
            assignment,
            pending_transfer,  # existing pending transfer
        ]

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with pytest.raises(ValueError) as exc_info:
                service.transfer_client(1, 1, 2, "reason", 1)
            assert "already has a pending transfer" in str(exc_info.value)


class TestApproveTransfer:
    """Tests for approve_transfer method."""

    def test_approve_transfer_success(self, service, mock_db):
        """Test successful transfer approval."""
        transfer = Mock()
        transfer.status = "pending"
        transfer.from_org_id = 1
        transfer.to_org_id = 2
        transfer.client_id = 1
        mock_db.query.return_value.filter_by.return_value.first.return_value = transfer
        mock_db.query.return_value.filter_by.return_value.delete.return_value = None

        result = service.approve_transfer(1, 1, approve=True)

        assert transfer.status == "approved"
        mock_db.add.assert_called_once()  # New assignment
        mock_db.commit.assert_called_once()

    def test_reject_transfer_success(self, service, mock_db):
        """Test successful transfer rejection."""
        transfer = Mock()
        transfer.status = "pending"
        mock_db.query.return_value.filter_by.return_value.first.return_value = transfer

        result = service.approve_transfer(1, 1, approve=False)

        assert transfer.status == "rejected"

    def test_approve_transfer_not_found(self, service, mock_db):
        """Test approving transfer when not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            service.approve_transfer(999, 1)
        assert "Transfer with ID 999 not found" in str(exc_info.value)

    def test_approve_transfer_already_processed(self, service, mock_db):
        """Test approving transfer that's already processed."""
        transfer = Mock()
        transfer.status = "approved"
        mock_db.query.return_value.filter_by.return_value.first.return_value = transfer

        with pytest.raises(ValueError) as exc_info:
            service.approve_transfer(1, 1)
        assert "already approved" in str(exc_info.value)


class TestGetPendingTransfers:
    """Tests for get_pending_transfers method."""

    def test_get_pending_transfers_all(self, service, mock_db):
        """Test getting all pending transfers."""
        transfer = Mock()
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [transfer]

        result = service.get_pending_transfers()

        assert len(result) == 1

    def test_get_pending_transfers_incoming(self, service, mock_db):
        """Test getting incoming pending transfers."""
        transfer = Mock()
        mock_db.query.return_value.filter_by.return_value.filter_by.return_value.order_by.return_value.all.return_value = [transfer]

        result = service.get_pending_transfers(org_id=1, direction="incoming")

        assert len(result) == 1

    def test_get_pending_transfers_outgoing(self, service, mock_db):
        """Test getting outgoing pending transfers."""
        transfer = Mock()
        mock_db.query.return_value.filter_by.return_value.filter_by.return_value.order_by.return_value.all.return_value = [transfer]

        result = service.get_pending_transfers(org_id=1, direction="outgoing")

        assert len(result) == 1


class TestGetTransferHistory:
    """Tests for get_transfer_history method."""

    def test_get_transfer_history_all(self, service, mock_db):
        """Test getting all transfer history."""
        transfer = Mock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = [transfer]

        result = service.get_transfer_history()

        assert len(result) == 1

    def test_get_transfer_history_by_org(self, service, mock_db):
        """Test getting transfer history by organization."""
        transfer = Mock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [transfer]

        result = service.get_transfer_history(org_id=1)

        assert len(result) == 1

    def test_get_transfer_history_by_client(self, service, mock_db):
        """Test getting transfer history by client."""
        transfer = Mock()
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [transfer]

        result = service.get_transfer_history(client_id=1)

        assert len(result) == 1


# ============== Permissions Tests ==============


class TestCheckOrgPermission:
    """Tests for check_org_permission method."""

    def test_check_permission_direct_membership(self, service, mock_db, mock_membership):
        """Test checking permission for direct member."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_membership

        result = service.check_org_permission(1, 1, "view_org")

        assert result is True

    def test_check_permission_admin_user(self, service, mock_db, mock_admin_staff):
        """Test checking permission for admin user."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            None,  # No direct membership
            mock_admin_staff,  # Staff lookup - admin role
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        result = service.check_org_permission(2, 1, "any_permission")

        assert result is True

    def test_check_permission_no_membership(self, service, mock_db, mock_staff):
        """Test checking permission when user has no membership."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            None,  # No direct membership
            mock_staff,  # Staff lookup - not admin
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        result = service.check_org_permission(1, 1, "view_org")

        assert result is False

    def test_check_permission_inherited_from_parent(self, service, mock_db, mock_staff, mock_membership):
        """Test checking permission inherited from parent org membership."""
        mock_membership.role = "manager"
        mock_membership.organization_id = 1
        child_org = Mock()
        child_org.id = 2

        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            None,  # No direct membership in child org
            mock_staff,  # Staff lookup - not admin
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_membership]

        with patch.object(service, 'get_child_organizations', return_value=[child_org]):
            result = service.check_org_permission(1, 2, "view_org")

        assert result is True


class TestGetOrgPermissionContext:
    """Tests for get_org_permission_context method."""

    def test_permission_context_direct_member(self, service, mock_db, mock_membership):
        """Test getting permission context for direct member."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_membership

        result = service.get_org_permission_context(1, 1)

        assert result["has_access"] is True
        assert result["is_direct_member"] is True

    def test_permission_context_admin_user(self, service, mock_db, mock_admin_staff):
        """Test getting permission context for admin user."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            None,  # No direct membership
            mock_admin_staff,  # Staff lookup - admin role
        ]

        result = service.get_org_permission_context(2, 1)

        assert result["has_access"] is True
        assert result["role"] == "admin"
        assert "*" in result["permissions"]

    def test_permission_context_no_access(self, service, mock_db, mock_staff):
        """Test getting permission context when no access."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            None,  # No direct membership
            mock_staff,  # Staff lookup - not admin
        ]
        mock_db.query.return_value.filter_by.return_value.all.return_value = []

        result = service.get_org_permission_context(1, 999)

        assert result["has_access"] is False


# ============== Revenue Tracking Tests ==============


class TestGetOrgStats:
    """Tests for get_org_stats method."""

    def test_get_org_stats_success(self, service, mock_db, mock_organization):
        """Test getting organization statistics."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter_by.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.scalar.return_value = None

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with patch.object(service, 'get_child_organizations', return_value=[]):
                result = service.get_org_stats(1, include_children=False)

        assert result["organization_id"] == 1
        assert "total_clients" in result
        assert "total_revenue" in result

    def test_get_org_stats_not_found(self, service, mock_db):
        """Test getting stats for non-existent org."""
        with patch.object(service, 'get_organization_by_id', return_value=None):
            result = service.get_org_stats(999)

        assert result == {}


class TestGetOrgRevenueReport:
    """Tests for get_org_revenue_report method."""

    def test_get_revenue_report_success(self, service, mock_db, mock_organization):
        """Test getting organization revenue report."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with patch.object(service, 'get_child_organizations', return_value=[]):
                result = service.get_org_revenue_report(1, period="month")

        assert result["organization_id"] == 1
        assert result["period"] == "month"
        assert "total_revenue" in result

    def test_get_revenue_report_not_found(self, service, mock_db):
        """Test getting revenue report for non-existent org."""
        with patch.object(service, 'get_organization_by_id', return_value=None):
            result = service.get_org_revenue_report(999)

        assert result == {}

    def test_get_revenue_report_different_periods(self, service, mock_db, mock_organization):
        """Test getting revenue report with different periods."""
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with patch.object(service, 'get_child_organizations', return_value=[]):
                for period in ["week", "month", "quarter", "year"]:
                    result = service.get_org_revenue_report(1, period=period)
                    assert result["period"] == period


class TestCalculateRevenueShare:
    """Tests for calculate_revenue_share method."""

    def test_calculate_revenue_share_no_parent(self, service, mock_db, mock_organization):
        """Test revenue share calculation for org without parent."""
        mock_organization.parent = None

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with patch.object(service, 'get_org_revenue_report', return_value={"total_revenue": 10000}):
                result = service.calculate_revenue_share(1)

        assert result["organization_id"] == 1
        assert result["revenue_shares"] == []
        assert result["net_revenue"] == 10000

    def test_calculate_revenue_share_with_parent(self, service, mock_db, mock_organization):
        """Test revenue share calculation with parent organization."""
        parent_org = Mock()
        parent_org.id = 0
        parent_org.name = "Parent Org"
        parent_org.parent = None

        mock_organization.parent = parent_org
        mock_organization.revenue_share_percent = 10.0

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with patch.object(service, 'get_org_revenue_report', return_value={"total_revenue": 10000}):
                result = service.calculate_revenue_share(1)

        assert result["total_revenue"] == 10000
        assert len(result["revenue_shares"]) == 1
        assert result["revenue_shares"][0]["share_amount"] == 1000  # 10% of 10000

    def test_calculate_revenue_share_not_found(self, service, mock_db):
        """Test revenue share for non-existent org."""
        with patch.object(service, 'get_organization_by_id', return_value=None):
            result = service.calculate_revenue_share(999)

        assert result == {}


class TestGetConsolidatedReport:
    """Tests for get_consolidated_report method."""

    def test_get_consolidated_report_success(self, service, mock_db, mock_organization):
        """Test getting consolidated report."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            with patch.object(service, 'get_child_organizations', return_value=[]):
                with patch.object(service, 'get_org_stats', return_value={"organization_id": 1}):
                    result = service.get_consolidated_report(1)

        assert result["organization_id"] == 1
        assert result["report_type"] == "consolidated"
        assert "summary" in result

    def test_get_consolidated_report_not_found(self, service, mock_db):
        """Test consolidated report for non-existent org."""
        with patch.object(service, 'get_organization_by_id', return_value=None):
            result = service.get_consolidated_report(999)

        assert result == {}


# ============== User Organizations Tests ==============


class TestGetUserOrganizations:
    """Tests for get_user_organizations method."""

    def test_get_user_organizations(self, service, mock_db, mock_membership, mock_organization):
        """Test getting all organizations a user belongs to."""
        mock_membership.organization = mock_organization
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_membership]

        result = service.get_user_organizations(1)

        assert len(result) == 1


class TestGetAccessibleOrganizations:
    """Tests for get_accessible_organizations method."""

    def test_get_accessible_orgs_direct_member(self, service, mock_db, mock_membership, mock_organization):
        """Test getting accessible orgs for direct member."""
        mock_membership.role = "staff"
        mock_membership.organization = mock_organization
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_membership]

        result = service.get_accessible_organizations(1)

        assert len(result) == 1

    def test_get_accessible_orgs_manager_with_children(self, service, mock_db, mock_membership, mock_organization):
        """Test getting accessible orgs for manager includes children."""
        mock_membership.role = "manager"
        mock_membership.organization = mock_organization
        mock_membership.organization_id = 1
        child_org = Mock()
        child_org.id = 2
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_membership]

        with patch.object(service, 'get_child_organizations', return_value=[child_org]):
            result = service.get_accessible_organizations(1)

        assert len(result) == 2


# ============== Organization Limits Tests ==============


class TestCheckOrgLimits:
    """Tests for check_org_limits method."""

    def test_check_org_limits_success(self, service, mock_db, mock_organization):
        """Test checking organization limits."""
        mock_db.query.return_value.filter_by.return_value.count.side_effect = [5, 50]  # users, clients

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            result = service.check_org_limits(1)

        assert result["organization_id"] == 1
        assert result["users"]["current"] == 5
        assert result["clients"]["current"] == 50
        assert result["can_add_users"] is True
        assert result["can_add_clients"] is True

    def test_check_org_limits_not_found(self, service, mock_db):
        """Test checking limits for non-existent org."""
        with patch.object(service, 'get_organization_by_id', return_value=None):
            result = service.check_org_limits(999)

        assert "error" in result

    def test_check_org_limits_at_limit(self, service, mock_db, mock_organization):
        """Test checking limits when at limit."""
        mock_organization.max_users = 10
        mock_organization.max_clients = 100
        mock_db.query.return_value.filter_by.return_value.count.side_effect = [10, 100]  # At limits

        with patch.object(service, 'get_organization_by_id', return_value=mock_organization):
            result = service.check_org_limits(1)

        assert result["users"]["at_limit"] is True
        assert result["clients"]["at_limit"] is True
        assert result["can_add_users"] is False
        assert result["can_add_clients"] is False


# ============== Helper Function Tests ==============


class TestGetOrgFilter:
    """Tests for get_org_filter helper function."""

    def test_get_org_filter_admin_user(self):
        """Test org filter returns None for admin user."""
        mock_db = Mock()
        mock_staff = Mock()
        mock_staff.role = "admin"

        result = get_org_filter(mock_db, mock_staff)

        assert result is None

    def test_get_org_filter_regular_user(self, mock_organization):
        """Test org filter returns org IDs for regular user."""
        mock_db = Mock()
        mock_staff = Mock()
        mock_staff.id = 1
        mock_staff.role = "paralegal"

        with patch('services.franchise_service.FranchiseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_accessible_organizations.return_value = [mock_organization]
            result = get_org_filter(mock_db, mock_staff)

        assert result == [1]

    def test_get_org_filter_no_memberships(self):
        """Test org filter when user has no memberships."""
        mock_db = Mock()
        mock_staff = Mock()
        mock_staff.id = 1
        mock_staff.role = "paralegal"
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with patch('services.franchise_service.FranchiseService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_accessible_organizations.return_value = []
            result = get_org_filter(mock_db, mock_staff)

        assert result == []


class TestGetClientsForOrg:
    """Tests for get_clients_for_org helper function."""

    def test_get_clients_for_org_none_org_ids(self):
        """Test returns None when org_ids is None."""
        mock_db = Mock()

        result = get_clients_for_org(mock_db, None)

        assert result is None

    def test_get_clients_for_org_empty_org_ids(self):
        """Test returns empty list when org_ids is empty."""
        mock_db = Mock()

        result = get_clients_for_org(mock_db, [])

        assert result == []

    def test_get_clients_for_org_with_org_ids(self):
        """Test returns client IDs for given org IDs."""
        mock_db = Mock()
        mock_assignment = Mock()
        mock_assignment.client_id = 1
        mock_unassigned = Mock()
        mock_unassigned.id = 2

        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_assignment],  # Assigned clients
            [mock_unassigned],  # Unassigned clients
        ]

        result = get_clients_for_org(mock_db, [1, 2])

        assert 1 in result
        assert 2 in result
