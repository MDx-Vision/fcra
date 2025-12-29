"""
Unit tests for White Label Service
Tests for tenant management, branding configuration,
custom domain handling, API key management, and user/client assignments.
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.white_label_service import (
    WhiteLabelService,
    get_white_label_service,
)
from database import SUBSCRIPTION_TIERS


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
    """Create WhiteLabelService instance with mocked db."""
    return WhiteLabelService(mock_db)


@pytest.fixture
def mock_tenant():
    """Create a mock WhiteLabelTenant."""
    tenant = Mock()
    tenant.id = 1
    tenant.name = "Test Law Firm"
    tenant.slug = "test-law-firm"
    tenant.domain = "testlawfirm.com"
    tenant.logo_url = "/static/logo.png"
    tenant.favicon_url = "/static/favicon.ico"
    tenant.primary_color = "#319795"
    tenant.secondary_color = "#1a1a2e"
    tenant.accent_color = "#84cc16"
    tenant.company_name = "Test Law Firm LLC"
    tenant.is_active = True
    tenant.subscription_tier = "professional"
    tenant.max_users = 20
    tenant.max_clients = 500
    tenant.features_enabled = ["branding", "client_portal", "api_access"]
    tenant.api_key = "wl_test_api_key_12345"
    tenant.created_at = datetime.utcnow()
    tenant.updated_at = datetime.utcnow()
    tenant.get_branding_config = Mock(return_value={
        "primary_color": "#319795",
        "secondary_color": "#1a1a2e",
        "accent_color": "#84cc16",
        "logo_url": "/static/logo.png",
        "company_name": "Test Law Firm LLC",
    })
    return tenant


@pytest.fixture
def mock_staff():
    """Create a mock Staff user."""
    staff = Mock()
    staff.id = 1
    staff.email = "staff@testlawfirm.com"
    staff.full_name = "Test Staff"
    return staff


@pytest.fixture
def mock_client():
    """Create a mock Client."""
    client = Mock()
    client.id = 1
    client.name = "Test Client"
    client.email = "client@example.com"
    client.status = "active"
    return client


@pytest.fixture
def mock_tenant_user():
    """Create a mock TenantUser."""
    tenant_user = Mock()
    tenant_user.id = 1
    tenant_user.tenant_id = 1
    tenant_user.staff_id = 1
    tenant_user.role = "user"
    tenant_user.is_primary_admin = False
    return tenant_user


@pytest.fixture
def mock_tenant_client():
    """Create a mock TenantClient."""
    tenant_client = Mock()
    tenant_client.id = 1
    tenant_client.tenant_id = 1
    tenant_client.client_id = 1
    return tenant_client


# ============== Tenant Creation Tests ==============


class TestCreateTenant:
    """Tests for create_tenant method."""

    def test_create_tenant_success(self, service, mock_db):
        """Test successful tenant creation with minimal settings."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.create_tenant(name="New Law Firm", slug="new-law-firm")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_tenant_with_all_settings(self, service, mock_db):
        """Test tenant creation with all optional settings."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        settings = {
            "domain": "newlawfirm.com",
            "logo_url": "/static/logo.png",
            "primary_color": "#ff0000",
            "subscription_tier": "enterprise",
            "max_users": 100,
            "features_enabled": ["branding", "webhooks"],
        }

        result = service.create_tenant(name="New Law Firm", slug="new-law-firm", settings=settings)

        mock_db.add.assert_called_once()

    def test_create_tenant_duplicate_slug(self, service, mock_db, mock_tenant):
        """Test tenant creation fails with duplicate slug."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant

        with pytest.raises(ValueError) as exc_info:
            service.create_tenant(name="Another Firm", slug="test-law-firm")
        assert "already exists" in str(exc_info.value)

    def test_create_tenant_duplicate_domain(self, service, mock_db, mock_tenant):
        """Test tenant creation fails with duplicate domain."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [None, mock_tenant]

        with pytest.raises(ValueError) as exc_info:
            service.create_tenant(name="Another Firm", slug="another-firm", settings={"domain": "testlawfirm.com"})
        assert "domain" in str(exc_info.value).lower()

    def test_create_tenant_generates_api_key(self, service, mock_db):
        """Test tenant creation generates API key."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.create_tenant(name="API Firm", slug="api-firm")

        call_args = mock_db.add.call_args
        tenant_obj = call_args[0][0]
        assert tenant_obj.api_key.startswith("wl_")


# ============== Tenant Update Tests ==============


class TestUpdateTenant:
    """Tests for update_tenant method."""

    def test_update_tenant_success(self, service, mock_db, mock_tenant):
        """Test successful tenant update."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant

        result = service.update_tenant(1, name="Updated Law Firm")

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_tenant_not_found(self, service, mock_db):
        """Test update when tenant not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.update_tenant(999, name="Updated Name")

        assert result is None
        mock_db.commit.assert_not_called()

    def test_update_tenant_duplicate_slug(self, service, mock_db, mock_tenant):
        """Test update fails with duplicate slug."""
        other_tenant = Mock()
        other_tenant.id = 2
        mock_tenant.slug = "original-slug"
        mock_tenant.id = 1

        query_mock = Mock()
        mock_db.query.return_value = query_mock
        query_mock.filter_by.return_value.first.return_value = mock_tenant
        query_mock.filter.return_value.first.return_value = other_tenant

        with pytest.raises(ValueError) as exc_info:
            service.update_tenant(1, slug="existing-slug")
        assert "already exists" in str(exc_info.value)


# ============== Tenant Deletion Tests ==============


class TestDeleteTenant:
    """Tests for delete_tenant method."""

    def test_delete_tenant_success(self, service, mock_db, mock_tenant):
        """Test successful tenant deletion."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant

        result = service.delete_tenant(1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_tenant)

    def test_delete_tenant_not_found(self, service, mock_db):
        """Test deletion when tenant not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.delete_tenant(999)

        assert result is False
        mock_db.delete.assert_not_called()


# ============== Tenant Retrieval Tests ==============


class TestGetTenant:
    """Tests for tenant retrieval methods."""

    def test_get_tenant_by_id(self, service, mock_db, mock_tenant):
        """Test getting tenant by ID."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant

        result = service.get_tenant_by_id(1)

        assert result == mock_tenant

    def test_get_tenant_by_slug(self, service, mock_db, mock_tenant):
        """Test getting tenant by slug."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant

        result = service.get_tenant_by_slug("test-law-firm")

        assert result == mock_tenant

    def test_get_tenant_by_domain(self, service, mock_db, mock_tenant):
        """Test getting tenant by domain."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant

        result = service.get_tenant_by_domain("testlawfirm.com")

        assert result == mock_tenant

    def test_get_all_tenants(self, service, mock_db, mock_tenant):
        """Test getting all active tenants."""
        mock_db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = [mock_tenant]

        result = service.get_all_tenants()

        assert len(result) == 1


# ============== API Key Management Tests ==============


class TestAPIKeyManagement:
    """Tests for API key management methods."""

    def test_get_tenant_by_api_key(self, service, mock_db, mock_tenant):
        """Test getting tenant by API key."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant

        result = service.get_tenant_by_api_key("wl_test_api_key_12345")

        assert result == mock_tenant

    def test_generate_tenant_api_key(self, service, mock_db, mock_tenant):
        """Test regenerating API key for tenant."""
        mock_tenant.api_key = "wl_old_key"

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            result = service.generate_tenant_api_key(1)

        assert result.startswith("wl_")
        assert result != "wl_old_key"

    def test_generate_tenant_api_key_not_found(self, service):
        """Test regenerating API key for non-existent tenant."""
        with patch.object(service, 'get_tenant_by_id', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                service.generate_tenant_api_key(999)
            assert "not found" in str(exc_info.value)


# ============== Branding Configuration Tests ==============


class TestBrandingConfiguration:
    """Tests for branding configuration methods."""

    def test_get_tenant_branding(self, service, mock_tenant):
        """Test getting tenant branding configuration."""
        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            result = service.get_tenant_branding(1)

        assert result is not None
        assert "primary_color" in result

    def test_get_tenant_branding_not_found(self, service):
        """Test getting branding for non-existent tenant."""
        with patch.object(service, 'get_tenant_by_id', return_value=None):
            result = service.get_tenant_branding(999)

        assert result is None

    def test_get_default_branding(self, service):
        """Test getting default branding."""
        result = service.get_default_branding()

        assert result["primary_color"] == "#319795"
        assert result["company_name"] == "Brightpath Ascend"


# ============== User Assignment Tests ==============


class TestUserAssignment:
    """Tests for user assignment to tenant methods."""

    def test_assign_user_to_tenant_success(self, service, mock_db, mock_tenant, mock_staff):
        """Test successful user assignment to tenant."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [mock_staff, None]
        mock_db.query.return_value.filter_by.return_value.count.return_value = 5

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            result = service.assign_user_to_tenant(1, 1, role="user")

        mock_db.add.assert_called_once()

    def test_assign_user_to_tenant_tenant_not_found(self, service):
        """Test assignment when tenant not found."""
        with patch.object(service, 'get_tenant_by_id', return_value=None):
            with pytest.raises(ValueError) as exc_info:
                service.assign_user_to_tenant(1, 999)
            assert "not found" in str(exc_info.value)

    def test_assign_user_to_tenant_max_users_reached(self, service, mock_db, mock_tenant, mock_staff):
        """Test assignment fails when max users reached."""
        mock_tenant.max_users = 5
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_staff
        mock_db.query.return_value.filter_by.return_value.count.return_value = 5

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            with pytest.raises(ValueError) as exc_info:
                service.assign_user_to_tenant(1, 1)
            assert "maximum user limit" in str(exc_info.value)

    def test_remove_user_from_tenant_success(self, service, mock_db, mock_tenant_user):
        """Test successful user removal from tenant."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant_user

        result = service.remove_user_from_tenant(1, 1)

        assert result is True
        mock_db.delete.assert_called_once()

    def test_remove_user_from_tenant_not_found(self, service, mock_db):
        """Test removing user when assignment not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.remove_user_from_tenant(999, 1)

        assert result is False


# ============== Client Assignment Tests ==============


class TestClientAssignment:
    """Tests for client assignment to tenant methods."""

    def test_assign_client_to_tenant_success(self, service, mock_db, mock_tenant, mock_client):
        """Test successful client assignment to tenant."""
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [mock_client, None]
        mock_db.query.return_value.filter_by.return_value.count.return_value = 50

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            result = service.assign_client_to_tenant(1, 1)

        mock_db.add.assert_called_once()

    def test_assign_client_to_tenant_max_clients_reached(self, service, mock_db, mock_tenant, mock_client):
        """Test assignment fails when max clients reached."""
        mock_tenant.max_clients = 100
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_client
        mock_db.query.return_value.filter_by.return_value.count.return_value = 100

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            with pytest.raises(ValueError) as exc_info:
                service.assign_client_to_tenant(1, 1)
            assert "maximum client limit" in str(exc_info.value)

    def test_remove_client_from_tenant_success(self, service, mock_db, mock_tenant_client):
        """Test successful client removal from tenant."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant_client

        result = service.remove_client_from_tenant(1, 1)

        assert result is True
        mock_db.delete.assert_called_once()


# ============== Tenant Users and Clients Retrieval Tests ==============


class TestTenantUsersAndClientsRetrieval:
    """Tests for retrieving users and clients assigned to tenants."""

    def test_get_tenant_users(self, service, mock_db, mock_tenant_user):
        """Test getting all users of a tenant."""
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_tenant_user]

        result = service.get_tenant_users(1)

        assert len(result) == 1

    def test_get_tenant_clients(self, service, mock_db, mock_tenant_client):
        """Test getting all clients of a tenant."""
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_tenant_client]

        result = service.get_tenant_clients(1)

        assert len(result) == 1

    def test_get_user_tenants(self, service, mock_db, mock_tenant, mock_tenant_user):
        """Test getting all tenants a user belongs to."""
        mock_tenant_user.tenant_id = 1
        mock_db.query.return_value.filter_by.return_value.all.return_value = [mock_tenant_user]
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_tenant]

        result = service.get_user_tenants(1)

        assert len(result) == 1

    def test_get_client_tenant(self, service, mock_db, mock_tenant, mock_tenant_client):
        """Test getting the tenant a client belongs to."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_tenant_client

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            result = service.get_client_tenant(1)

        assert result == mock_tenant


# ============== Feature Validation Tests ==============


class TestFeatureValidation:
    """Tests for validate_tenant_features method."""

    def test_validate_feature_enabled_directly(self, service, mock_tenant):
        """Test validating a feature enabled directly on tenant."""
        mock_tenant.features_enabled = ["custom_feature", "branding"]

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            result = service.validate_tenant_features(1, "custom_feature")

        assert result is True

    def test_validate_feature_from_tier(self, service, mock_tenant):
        """Test validating a feature from subscription tier."""
        mock_tenant.features_enabled = []
        mock_tenant.subscription_tier = "professional"

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            result = service.validate_tenant_features(1, "api_access")

        assert result is True

    def test_validate_feature_not_enabled(self, service, mock_tenant):
        """Test validating a feature that is not enabled."""
        mock_tenant.features_enabled = ["branding"]
        mock_tenant.subscription_tier = "basic"

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            result = service.validate_tenant_features(1, "webhooks")

        assert result is False

    def test_validate_feature_inactive_tenant(self, service, mock_tenant):
        """Test validating feature for inactive tenant returns False."""
        mock_tenant.is_active = False

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            result = service.validate_tenant_features(1, "branding")

        assert result is False


# ============== Usage Statistics Tests ==============


class TestUsageStatistics:
    """Tests for get_tenant_usage_stats method."""

    def test_get_tenant_usage_stats_success(self, service, mock_db, mock_tenant, mock_tenant_client):
        """Test getting tenant usage statistics."""
        mock_tenant_client.client_id = 1
        mock_db.query.return_value.filter_by.return_value.count.return_value = 5
        mock_db.query.return_value.filter.return_value.count.return_value = 10

        with patch.object(service, 'get_tenant_by_id', return_value=mock_tenant):
            with patch.object(service, 'get_tenant_clients', return_value=[mock_tenant_client]):
                result = service.get_tenant_usage_stats(1)

        assert result is not None
        assert result["tenant_id"] == 1
        assert "users" in result

    def test_get_tenant_usage_stats_not_found(self, service):
        """Test getting stats for non-existent tenant."""
        with patch.object(service, 'get_tenant_by_id', return_value=None):
            result = service.get_tenant_usage_stats(999)

        assert result is None


# ============== Custom Domain Detection Tests ==============


class TestCustomDomainDetection:
    """Tests for detect_tenant_from_host method."""

    def test_detect_tenant_from_custom_domain(self, service, mock_tenant):
        """Test detecting tenant from custom domain."""
        with patch.object(service, 'get_tenant_by_domain', return_value=mock_tenant):
            result = service.detect_tenant_from_host("testlawfirm.com")

        assert result == mock_tenant

    def test_detect_tenant_from_subdomain(self, service, mock_tenant):
        """Test detecting tenant from subdomain."""
        with patch.object(service, 'get_tenant_by_domain', return_value=None):
            with patch.object(service, 'get_tenant_by_slug', return_value=mock_tenant):
                result = service.detect_tenant_from_host("testfirm.brightpathascend.com")

        assert result == mock_tenant

    def test_detect_tenant_empty_host(self, service):
        """Test detecting tenant from empty/None host."""
        assert service.detect_tenant_from_host("") is None
        assert service.detect_tenant_from_host(None) is None

    def test_detect_tenant_from_host_with_port(self, service, mock_tenant):
        """Test detecting tenant from host with port."""
        with patch.object(service, 'get_tenant_by_domain', return_value=mock_tenant):
            result = service.detect_tenant_from_host("testlawfirm.com:8080")

        assert result == mock_tenant

    def test_detect_tenant_reserved_subdomain_ignored(self, service):
        """Test that reserved subdomains (www, api, admin) are ignored."""
        with patch.object(service, 'get_tenant_by_domain', return_value=None):
            assert service.detect_tenant_from_host("www.brightpathascend.com") is None
            assert service.detect_tenant_from_host("api.brightpathascend.com") is None
            assert service.detect_tenant_from_host("admin.brightpathascend.com") is None

    def test_detect_tenant_case_insensitive(self, service, mock_tenant):
        """Test that host detection is case insensitive."""
        with patch.object(service, 'get_tenant_by_domain', return_value=mock_tenant):
            result = service.detect_tenant_from_host("TESTLAWFIRM.COM")

        assert result == mock_tenant


# ============== Factory Function Tests ==============


class TestFactoryFunction:
    """Tests for get_white_label_service factory function."""

    def test_get_white_label_service(self, mock_db):
        """Test factory function creates service instance."""
        service = get_white_label_service(mock_db)

        assert isinstance(service, WhiteLabelService)
        assert service.db == mock_db
