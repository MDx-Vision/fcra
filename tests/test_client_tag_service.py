"""
Unit tests for the Client Tag Service.

Tests cover:
- Tag CRUD operations
- Tag assignments to clients
- Filtering clients by tags
- Bulk operations
- Statistics
"""

from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from services.client_tag_service import (
    ClientTagService,
    get_client_tag_service,
    get_available_colors,
    get_default_tags,
    TAG_COLORS,
    DEFAULT_TAGS,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def service(mock_db):
    """Create a client tag service with a mock database."""
    return ClientTagService(db_session=mock_db)


@pytest.fixture
def mock_tag():
    """Create a mock tag object."""
    tag = MagicMock()
    tag.id = 1
    tag.name = "VIP"
    tag.color = "#eab308"
    tag.created_at = datetime.utcnow()
    return tag


@pytest.fixture
def mock_client():
    """Create a mock client object."""
    client = MagicMock()
    client.id = 1
    client.first_name = "John"
    client.last_name = "Doe"
    client.email = "john@example.com"
    client.phone = "555-1234"
    client.dispute_status = "active"
    return client


@pytest.fixture
def mock_assignment():
    """Create a mock tag assignment object."""
    assignment = MagicMock()
    assignment.id = 1
    assignment.client_id = 1
    assignment.tag_id = 1
    assignment.created_at = datetime.utcnow()
    return assignment


# =============================================================================
# Constants Tests
# =============================================================================


class TestConstants:
    """Tests for module constants."""

    def test_tag_colors(self):
        """Test that TAG_COLORS is defined correctly."""
        assert isinstance(TAG_COLORS, list)
        assert len(TAG_COLORS) >= 5
        for color in TAG_COLORS:
            assert "name" in color
            assert "color" in color
            assert color["color"].startswith("#")

    def test_default_tags(self):
        """Test that DEFAULT_TAGS is defined correctly."""
        assert isinstance(DEFAULT_TAGS, list)
        assert len(DEFAULT_TAGS) >= 5
        for tag in DEFAULT_TAGS:
            assert "name" in tag
            assert "color" in tag

    def test_get_available_colors(self):
        """Test get_available_colors function."""
        colors = get_available_colors()
        assert colors == TAG_COLORS

    def test_get_default_tags(self):
        """Test get_default_tags function."""
        tags = get_default_tags()
        assert tags == DEFAULT_TAGS


# =============================================================================
# Service Initialization Tests
# =============================================================================


class TestServiceInitialization:
    """Tests for service initialization."""

    def test_init_with_db_session(self, mock_db):
        """Test initialization with provided database session."""
        service = ClientTagService(db_session=mock_db)
        assert service._db == mock_db
        assert service._owns_session is False

    def test_init_without_db_session(self):
        """Test initialization without database session."""
        service = ClientTagService()
        assert service._db is None
        assert service._owns_session is True

    def test_should_close_db(self, service):
        """Test _should_close_db returns False when session provided."""
        assert service._should_close_db() is False


# =============================================================================
# Create Tag Tests
# =============================================================================


class TestCreateTag:
    """Tests for create_tag functionality."""

    def test_create_tag_success(self, service, mock_db):
        """Test successful tag creation."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.create_tag(name="Priority", color="#ef4444")

        assert result["success"] is True
        assert "tag" in result
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_tag_empty_name(self, service, mock_db):
        """Test creating tag with empty name fails."""
        result = service.create_tag(name="", color="#ef4444")

        assert result["success"] is False
        assert "required" in result["error"].lower()

    def test_create_tag_duplicate_name(self, service, mock_db, mock_tag):
        """Test creating tag with duplicate name fails."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tag

        result = service.create_tag(name="VIP", color="#ef4444")

        assert result["success"] is False
        assert "exists" in result["error"].lower()

    def test_create_tag_invalid_color(self, service, mock_db):
        """Test creating tag with invalid color uses default."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.create_tag(name="Test", color="invalid")

        assert result["success"] is True
        # Should use default color


# =============================================================================
# Get Tag Tests
# =============================================================================


class TestGetTag:
    """Tests for get_tag functionality."""

    def test_get_tag_exists(self, service, mock_db, mock_tag):
        """Test getting an existing tag."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tag

        result = service.get_tag(1)

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "VIP"

    def test_get_tag_not_exists(self, service, mock_db):
        """Test getting a non-existent tag."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_tag(999)

        assert result is None


# =============================================================================
# Get All Tags Tests
# =============================================================================


class TestGetAllTags:
    """Tests for get_all_tags functionality."""

    def test_get_all_tags(self, service, mock_db, mock_tag):
        """Test getting all tags."""
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_tag]

        result = service.get_all_tags()

        assert len(result) == 1
        assert result[0]["name"] == "VIP"


# =============================================================================
# Update Tag Tests
# =============================================================================


class TestUpdateTag:
    """Tests for update_tag functionality."""

    def test_update_tag_success(self, service, mock_db, mock_tag):
        """Test successful tag update."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_tag, None]

        result = service.update_tag(1, name="Super VIP", color="#22c55e")

        assert result["success"] is True
        mock_db.commit.assert_called_once()

    def test_update_tag_not_found(self, service, mock_db):
        """Test updating non-existent tag."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.update_tag(999, name="Test")

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_update_tag_duplicate_name(self, service, mock_db, mock_tag):
        """Test updating tag to duplicate name fails."""
        other_tag = MagicMock()
        other_tag.id = 2
        other_tag.name = "Existing"
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_tag, other_tag]

        result = service.update_tag(1, name="Existing")

        assert result["success"] is False
        assert "exists" in result["error"].lower()


# =============================================================================
# Delete Tag Tests
# =============================================================================


class TestDeleteTag:
    """Tests for delete_tag functionality."""

    def test_delete_tag_success(self, service, mock_db, mock_tag):
        """Test successful tag deletion."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tag
        mock_db.query.return_value.filter.return_value.delete.return_value = 5

        result = service.delete_tag(1)

        assert result["success"] is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_delete_tag_not_found(self, service, mock_db):
        """Test deleting non-existent tag."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.delete_tag(999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# Assign Tag Tests
# =============================================================================


class TestAssignTag:
    """Tests for assign_tag functionality."""

    def test_assign_tag_success(self, service, mock_db, mock_client, mock_tag):
        """Test successful tag assignment."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_client,  # Client exists
            mock_tag,     # Tag exists
            None,         # Not already assigned
        ]

        result = service.assign_tag(client_id=1, tag_id=1)

        assert result["success"] is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_assign_tag_client_not_found(self, service, mock_db):
        """Test assigning tag to non-existent client."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.assign_tag(client_id=999, tag_id=1)

        assert result["success"] is False
        assert "client" in result["error"].lower()

    def test_assign_tag_tag_not_found(self, service, mock_db, mock_client):
        """Test assigning non-existent tag."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            None,
        ]

        result = service.assign_tag(client_id=1, tag_id=999)

        assert result["success"] is False
        assert "tag" in result["error"].lower()

    def test_assign_tag_already_assigned(self, service, mock_db, mock_client, mock_tag, mock_assignment):
        """Test assigning already assigned tag."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_client,
            mock_tag,
            mock_assignment,
        ]

        result = service.assign_tag(client_id=1, tag_id=1)

        assert result["success"] is True
        assert "already" in result["message"].lower()


# =============================================================================
# Remove Tag Tests
# =============================================================================


class TestRemoveTag:
    """Tests for remove_tag functionality."""

    def test_remove_tag_success(self, service, mock_db, mock_assignment):
        """Test successful tag removal."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_assignment

        result = service.remove_tag(client_id=1, tag_id=1)

        assert result["success"] is True
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_remove_tag_not_found(self, service, mock_db):
        """Test removing non-existent assignment."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.remove_tag(client_id=1, tag_id=1)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# Get Client Tags Tests
# =============================================================================


class TestGetClientTags:
    """Tests for get_client_tags functionality."""

    def test_get_client_tags(self, service, mock_db, mock_tag):
        """Test getting tags for a client."""
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_tag]

        result = service.get_client_tags(client_id=1)

        assert len(result) == 1
        assert result[0]["name"] == "VIP"


# =============================================================================
# Set Client Tags Tests
# =============================================================================


class TestSetClientTags:
    """Tests for set_client_tags functionality."""

    def test_set_client_tags_success(self, service, mock_db, mock_client, mock_tag):
        """Test setting all tags for a client."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_client,  # Client exists
            mock_tag,     # Tag 1 exists
        ]
        mock_db.query.return_value.filter.return_value.delete.return_value = 1

        result = service.set_client_tags(client_id=1, tag_ids=[1])

        assert result["success"] is True
        mock_db.commit.assert_called()

    def test_set_client_tags_client_not_found(self, service, mock_db):
        """Test setting tags for non-existent client."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.set_client_tags(client_id=999, tag_ids=[1])

        assert result["success"] is False
        assert "client" in result["error"].lower()


# =============================================================================
# Get Clients by Tag Tests
# =============================================================================


class TestGetClientsByTag:
    """Tests for get_clients_by_tag functionality."""

    def test_get_clients_by_tag_success(self, service, mock_db, mock_tag, mock_client):
        """Test getting clients with a specific tag."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tag
        mock_db.query.return_value.join.return_value.filter.return_value.scalar.return_value = 5
        mock_db.query.return_value.join.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [mock_client]

        result = service.get_clients_by_tag(tag_id=1)

        assert result["success"] is True
        assert len(result["clients"]) == 1
        assert result["total"] == 5

    def test_get_clients_by_tag_not_found(self, service, mock_db):
        """Test getting clients for non-existent tag."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_clients_by_tag(tag_id=999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()


# =============================================================================
# Bulk Operations Tests
# =============================================================================


class TestBulkOperations:
    """Tests for bulk tag operations."""

    def test_bulk_assign_tag_success(self, service, mock_db, mock_tag):
        """Test bulk assigning tag to clients."""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_tag,  # Tag exists
            None,      # Client 1 not assigned
            None,      # Client 2 not assigned
        ]

        result = service.bulk_assign_tag(client_ids=[1, 2], tag_id=1)

        assert result["success"] is True
        assert result["assigned"] == 2

    def test_bulk_assign_tag_not_found(self, service, mock_db):
        """Test bulk assign with non-existent tag."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.bulk_assign_tag(client_ids=[1, 2], tag_id=999)

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_bulk_remove_tag_success(self, service, mock_db):
        """Test bulk removing tag from clients."""
        mock_db.query.return_value.filter.return_value.delete.return_value = 5

        result = service.bulk_remove_tag(client_ids=[1, 2, 3], tag_id=1)

        assert result["success"] is True
        assert result["removed"] == 5


# =============================================================================
# Statistics Tests
# =============================================================================


class TestStatistics:
    """Tests for get_stats functionality."""

    def test_get_stats(self, service, mock_db):
        """Test getting tag statistics."""
        mock_db.query.return_value.scalar.return_value = 10
        mock_db.query.return_value.outerjoin.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []

        result = service.get_stats()

        assert "total_tags" in result
        assert "total_assignments" in result
        assert "clients_with_tags" in result
        assert "most_used" in result


# =============================================================================
# Seed Default Tags Tests
# =============================================================================


class TestSeedDefaultTags:
    """Tests for seed_default_tags functionality."""

    def test_seed_default_tags_success(self, service, mock_db):
        """Test seeding default tags."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.seed_default_tags()

        assert result["success"] is True
        assert result["created"] == len(DEFAULT_TAGS)

    def test_seed_default_tags_all_exist(self, service, mock_db, mock_tag):
        """Test seeding when all tags already exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_tag

        result = service.seed_default_tags()

        assert result["success"] is True
        assert result["created"] == 0
        assert result["skipped"] == len(DEFAULT_TAGS)


# =============================================================================
# Module-Level Functions Tests
# =============================================================================


class TestModuleLevelFunctions:
    """Tests for module-level convenience functions."""

    def test_get_client_tag_service_singleton(self):
        """Test that get_client_tag_service returns singleton."""
        service1 = get_client_tag_service()
        service2 = get_client_tag_service()

        assert service1 is service2
