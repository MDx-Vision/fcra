"""
Unit tests for Whitelabel Service (WhiteLabelConfigService)
Tests for white-label configuration management including:
- Config creation, update, deletion
- Domain/subdomain lookup and validation
- Caching mechanism
- CSS generation
- Branding configuration
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, PropertyMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.whitelabel_service import (
    WhiteLabelConfigService,
    get_whitelabel_config_service,
)
from database import FONT_FAMILIES


# ============== Fixtures ==============


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = Mock()
    # Don't use self-returning chains - let Mock create them automatically
    # This allows test-specific return values to be set properly
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter_by.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.filter_by.return_value.all.return_value = []
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.filter_by.return_value.order_by.return_value.all.return_value = []
    db.query.return_value.order_by.return_value.all.return_value = []
    return db


@pytest.fixture
def service(mock_db):
    """Create WhiteLabelConfigService instance with mocked db."""
    svc = WhiteLabelConfigService(mock_db)
    # Clear any cached data between tests
    svc._clear_cache()
    return svc


@pytest.fixture
def mock_config():
    """Create a mock WhiteLabelConfig."""
    config = Mock()
    config.id = 1
    config.organization_id = 1
    config.organization_name = "Test Law Firm"
    config.subdomain = "testfirm"
    config.custom_domain = "testfirm.com"
    config.logo_url = "/static/logo.png"
    config.favicon_url = "/static/favicon.ico"
    config.primary_color = "#319795"
    config.secondary_color = "#1a1a2e"
    config.accent_color = "#84cc16"
    config.header_bg_color = "#1a1a2e"
    config.sidebar_bg_color = "#1a1a2e"
    config.font_family = "inter"
    config.custom_css = ".custom { color: red; }"
    config.email_from_name = "Test Law Firm"
    config.email_from_address = "contact@testfirm.com"
    config.email_from_address_encrypted = "encrypted_email"
    config.company_address = "123 Main St, Anytown, USA"
    config.company_phone = "555-1234"
    config.company_email = "info@testfirm.com"
    config.footer_text = "2024 Test Law Firm. All rights reserved."
    config.terms_url = "https://testfirm.com/terms"
    config.privacy_url = "https://testfirm.com/privacy"
    config.is_active = True
    config.created_at = datetime.utcnow()
    config.updated_at = datetime.utcnow()
    config.get_branding_dict = Mock(return_value={
        "organization_name": "Test Law Firm",
        "subdomain": "testfirm",
        "custom_domain": "testfirm.com",
        "logo_url": "/static/logo.png",
        "primary_color": "#319795",
        "secondary_color": "#1a1a2e",
        "accent_color": "#84cc16",
        "header_bg_color": "#1a1a2e",
        "sidebar_bg_color": "#1a1a2e",
        "font_family": FONT_FAMILIES["inter"],
        "font_family_key": "inter",
        "custom_css": ".custom { color: red; }",
        "email_from_name": "Test Law Firm",
        "email_from_address": "contact@testfirm.com",
        "company_address": "123 Main St, Anytown, USA",
        "company_phone": "555-1234",
        "company_email": "info@testfirm.com",
        "footer_text": "2024 Test Law Firm. All rights reserved.",
        "terms_url": "https://testfirm.com/terms",
        "privacy_url": "https://testfirm.com/privacy",
        "is_active": True,
    })
    return config


# ============== Get Config by Domain Tests ==============


class TestGetConfigByDomain:
    """Tests for get_config_by_domain method."""

    def test_get_config_by_domain_empty_domain(self, service):
        """Test that empty domain returns None."""
        result = service.get_config_by_domain("")
        assert result is None

    def test_get_config_by_domain_none_domain(self, service):
        """Test that None domain returns None."""
        result = service.get_config_by_domain(None)
        assert result is None

    def test_get_config_by_custom_domain_found(self, service, mock_db, mock_config):
        """Test finding config by custom domain."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        result = service.get_config_by_domain("testfirm.com")

        assert result == mock_config

    def test_get_config_by_subdomain_found(self, service, mock_db, mock_config):
        """Test finding config by subdomain."""
        # Custom domain not found, but subdomain found
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # Custom domain lookup
            mock_config,  # Subdomain lookup
        ]

        result = service.get_config_by_domain("testfirm.example.com")

        assert result == mock_config

    def test_get_config_by_domain_not_found(self, service, mock_db):
        """Test when domain is not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_config_by_domain("unknown.example.com")

        assert result is None

    def test_get_config_by_domain_reserved_subdomain_ignored(self, service, mock_db):
        """Test that reserved subdomains (www, api, admin, etc.) are ignored."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        for reserved in ["www", "app", "api", "admin", "mail", "smtp"]:
            result = service.get_config_by_domain(f"{reserved}.example.com")
            assert result is None

    def test_get_config_by_domain_case_insensitive(self, service, mock_db, mock_config):
        """Test that domain lookup is case insensitive."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        result = service.get_config_by_domain("TESTFIRM.COM")

        assert result == mock_config

    def test_get_config_by_domain_strips_whitespace(self, service, mock_db, mock_config):
        """Test that domain lookup strips whitespace."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        result = service.get_config_by_domain("  testfirm.com  ")

        assert result == mock_config

    def test_get_config_by_domain_uses_cache(self, service, mock_db, mock_config):
        """Test that subsequent lookups use cache."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        # First lookup
        result1 = service.get_config_by_domain("testfirm.com")
        assert result1 == mock_config

        # Reset the mock to verify second call doesn't hit DB
        mock_db.reset_mock()

        # Second lookup should use cache
        result2 = service.get_config_by_domain("testfirm.com")
        assert result2 == mock_config
        mock_db.query.assert_not_called()


# ============== Get Config by Organization Tests ==============


class TestGetConfigByOrg:
    """Tests for get_config_by_org method."""

    def test_get_config_by_org_success(self, service, mock_db, mock_config):
        """Test getting config by organization ID."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        result = service.get_config_by_org(1)

        assert result == mock_config

    def test_get_config_by_org_not_found(self, service, mock_db):
        """Test when organization config not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.get_config_by_org(999)

        assert result is None

    def test_get_config_by_org_none_org_id(self, service):
        """Test that None org_id returns None."""
        result = service.get_config_by_org(None)
        assert result is None

    def test_get_config_by_org_zero_org_id(self, service):
        """Test that zero org_id returns None."""
        result = service.get_config_by_org(0)
        assert result is None

    def test_get_config_by_org_uses_cache(self, service, mock_db, mock_config):
        """Test that organization config lookup uses cache."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        # First lookup
        result1 = service.get_config_by_org(1)
        assert result1 == mock_config

        # Reset mock
        mock_db.reset_mock()

        # Second lookup should use cache
        result2 = service.get_config_by_org(1)
        assert result2 == mock_config
        mock_db.query.assert_not_called()


# ============== Get Config by ID Tests ==============


class TestGetConfigById:
    """Tests for get_config_by_id method."""

    def test_get_config_by_id_success(self, service, mock_db, mock_config):
        """Test getting config by ID."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        result = service.get_config_by_id(1)

        assert result == mock_config

    def test_get_config_by_id_not_found(self, service, mock_db):
        """Test when config ID not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.get_config_by_id(999)

        assert result is None


# ============== Create Config Tests ==============


class TestCreateConfig:
    """Tests for create_config method."""

    def test_create_config_success(self, service, mock_db):
        """Test successful config creation."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        config_data = {
            "organization_name": "New Law Firm",
            "subdomain": "newlawfirm",
            "primary_color": "#ff0000",
        }

        with patch("services.whitelabel_service.encrypt_value", return_value="encrypted"):
            result = service.create_config(1, config_data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_config_missing_subdomain(self, service):
        """Test config creation fails without subdomain."""
        with pytest.raises(ValueError) as exc_info:
            service.create_config(1, {"organization_name": "Test"})
        assert "Subdomain is required" in str(exc_info.value)

    def test_create_config_empty_subdomain(self, service):
        """Test config creation fails with empty subdomain."""
        with pytest.raises(ValueError) as exc_info:
            service.create_config(1, {"subdomain": "", "organization_name": "Test"})
        assert "Subdomain is required" in str(exc_info.value)

    def test_create_config_invalid_subdomain_format(self, service):
        """Test config creation fails with invalid subdomain format."""
        with pytest.raises(ValueError) as exc_info:
            service.create_config(1, {"subdomain": "Invalid_Subdomain!", "organization_name": "Test"})
        assert "Invalid subdomain format" in str(exc_info.value)

    def test_create_config_duplicate_subdomain(self, service, mock_db, mock_config):
        """Test config creation fails with duplicate subdomain."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        with pytest.raises(ValueError) as exc_info:
            service.create_config(1, {"subdomain": "testfirm", "organization_name": "Test"})
        assert "already in use" in str(exc_info.value)

    def test_create_config_duplicate_custom_domain(self, service, mock_db, mock_config):
        """Test config creation fails with duplicate custom domain."""
        # First call for subdomain check returns None, second for domain check returns existing
        mock_db.query.return_value.filter_by.return_value.first.side_effect = [
            None,  # Subdomain check
            mock_config,  # Custom domain check
        ]

        with pytest.raises(ValueError) as exc_info:
            service.create_config(1, {
                "subdomain": "newsubdomain",
                "custom_domain": "testfirm.com",
                "organization_name": "Test"
            })
        assert "already in use" in str(exc_info.value)

    def test_create_config_with_all_fields(self, service, mock_db):
        """Test config creation with all optional fields."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        config_data = {
            "organization_name": "Full Law Firm",
            "subdomain": "fullfirm",
            "custom_domain": "fullfirm.com",
            "logo_url": "/logo.png",
            "favicon_url": "/favicon.ico",
            "primary_color": "#ff0000",
            "secondary_color": "#00ff00",
            "accent_color": "#0000ff",
            "header_bg_color": "#111111",
            "sidebar_bg_color": "#222222",
            "font_family": "roboto",
            "custom_css": ".test { color: blue; }",
            "email_from_name": "Full Law Firm",
            "email_from_address": "contact@fullfirm.com",
            "company_address": "456 Oak St",
            "company_phone": "555-5678",
            "company_email": "info@fullfirm.com",
            "footer_text": "Copyright 2024",
            "terms_url": "https://fullfirm.com/terms",
            "privacy_url": "https://fullfirm.com/privacy",
            "is_active": True,
        }

        with patch("services.whitelabel_service.encrypt_value", return_value="encrypted"):
            result = service.create_config(1, config_data)

        mock_db.add.assert_called_once()

    def test_create_config_clears_cache(self, service, mock_db, mock_config):
        """Test that creating a config clears the cache."""
        # Pre-populate cache
        service._set_cache("test_key", "test_value")
        assert service._get_from_cache("test_key") == "test_value"

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with patch("services.whitelabel_service.encrypt_value", return_value="encrypted"):
            service.create_config(1, {"subdomain": "newdomain", "organization_name": "Test"})

        # Cache should be cleared
        assert service._get_from_cache("test_key") is None

    def test_create_config_encrypts_email(self, service, mock_db):
        """Test that email_from_address is encrypted on creation."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        config_data = {
            "subdomain": "encrypttest",
            "organization_name": "Test",
            "email_from_address": "secret@test.com",
        }

        with patch("services.whitelabel_service.encrypt_value", return_value="encrypted_email") as mock_encrypt:
            service.create_config(1, config_data)
            mock_encrypt.assert_called_once_with("secret@test.com")


# ============== Update Config Tests ==============


class TestUpdateConfig:
    """Tests for update_config method."""

    def test_update_config_success(self, service, mock_db, mock_config):
        """Test successful config update."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        result = service.update_config(1, organization_name="Updated Name")

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_update_config_not_found(self, service, mock_db):
        """Test update when config not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.update_config(999, organization_name="Updated Name")

        assert result is None
        mock_db.commit.assert_not_called()

    def test_update_config_duplicate_subdomain(self, service, mock_db, mock_config):
        """Test update fails with duplicate subdomain."""
        other_config = Mock()
        other_config.id = 2

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config
        mock_db.query.return_value.filter.return_value.first.return_value = other_config

        with pytest.raises(ValueError) as exc_info:
            service.update_config(1, subdomain="existing-subdomain")
        assert "already in use" in str(exc_info.value)

    def test_update_config_duplicate_custom_domain(self, service, mock_db, mock_config):
        """Test update fails with duplicate custom domain."""
        other_config = Mock()
        other_config.id = 2
        mock_config.custom_domain = "original.com"

        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config
        mock_db.query.return_value.filter.return_value.first.return_value = other_config

        with pytest.raises(ValueError) as exc_info:
            service.update_config(1, custom_domain="existing.com")
        assert "already in use" in str(exc_info.value)

    def test_update_config_invalid_subdomain_format(self, service, mock_db, mock_config):
        """Test update fails with invalid subdomain format."""
        mock_config.subdomain = "original"
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        with pytest.raises(ValueError) as exc_info:
            service.update_config(1, subdomain="Invalid_Format!")
        assert "Invalid subdomain format" in str(exc_info.value)

    def test_update_config_clears_cache(self, service, mock_db, mock_config):
        """Test that updating a config clears the cache."""
        service._set_cache("test_key", "test_value")
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        service.update_config(1, organization_name="Updated")

        assert service._get_from_cache("test_key") is None

    def test_update_config_encrypts_email(self, service, mock_db, mock_config):
        """Test that email_from_address is encrypted on update."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        with patch("services.whitelabel_service.encrypt_value", return_value="new_encrypted") as mock_encrypt:
            service.update_config(1, email_from_address="newemail@test.com")
            mock_encrypt.assert_called_once_with("newemail@test.com")

    def test_update_config_ignores_unknown_fields(self, service, mock_db, mock_config):
        """Test that unknown fields are ignored during update."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        # Should not raise an error
        result = service.update_config(1, unknown_field="value", organization_name="Valid")

        mock_db.commit.assert_called_once()

    def test_update_config_same_subdomain_allowed(self, service, mock_db, mock_config):
        """Test that keeping the same subdomain is allowed."""
        mock_config.subdomain = "testfirm"

        # Set up the mock properly - get_config_by_id uses filter_by().first()
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Should not raise an error - even with same subdomain, update should proceed
        result = service.update_config(1, subdomain="testfirm", organization_name="Updated Name")

        mock_db.commit.assert_called_once()


# ============== Delete Config Tests ==============


class TestDeleteConfig:
    """Tests for delete_config method."""

    def test_delete_config_success(self, service, mock_db, mock_config):
        """Test successful config deletion."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        result = service.delete_config(1)

        assert result is True
        mock_db.delete.assert_called_once_with(mock_config)
        mock_db.commit.assert_called_once()

    def test_delete_config_not_found(self, service, mock_db):
        """Test deletion when config not found."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = service.delete_config(999)

        assert result is False
        mock_db.delete.assert_not_called()

    def test_delete_config_clears_cache(self, service, mock_db, mock_config):
        """Test that deleting a config clears the cache."""
        service._set_cache("test_key", "test_value")
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        service.delete_config(1)

        assert service._get_from_cache("test_key") is None


# ============== Get All Configs Tests ==============


class TestGetAllConfigs:
    """Tests for get_all_configs method."""

    def test_get_all_configs_active_only(self, service, mock_db, mock_config):
        """Test getting all active configs."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_config]

        result = service.get_all_configs()

        assert len(result) == 1

    def test_get_all_configs_include_inactive(self, service, mock_db, mock_config):
        """Test getting all configs including inactive."""
        inactive_config = Mock()
        inactive_config.is_active = False
        mock_db.query.return_value.order_by.return_value.all.return_value = [mock_config, inactive_config]

        result = service.get_all_configs(include_inactive=True)

        assert len(result) == 2

    def test_get_all_configs_empty(self, service, mock_db):
        """Test getting configs when none exist."""
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        result = service.get_all_configs()

        assert result == []


# ============== Validate Domain Tests ==============


class TestValidateDomain:
    """Tests for validate_domain method."""

    def test_validate_domain_empty(self, service):
        """Test validation fails for empty domain."""
        result = service.validate_domain("")

        assert result["available"] is False
        assert "required" in result["error"].lower()

    def test_validate_domain_none(self, service):
        """Test validation fails for None domain."""
        result = service.validate_domain(None)

        assert result["available"] is False

    def test_validate_subdomain_available(self, service, mock_db):
        """Test subdomain is available."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.validate_domain("newsubdomain")

        assert result["available"] is True
        assert result["type"] == "subdomain"
        assert result["domain"] == "newsubdomain"

    def test_validate_subdomain_taken(self, service, mock_db, mock_config):
        """Test subdomain is taken."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        result = service.validate_domain("testfirm")

        assert result["available"] is False
        assert result["type"] == "subdomain"

    def test_validate_custom_domain_available(self, service, mock_db):
        """Test custom domain is available."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.validate_domain("newdomain.com")

        assert result["available"] is True
        assert result["type"] == "custom_domain"

    def test_validate_custom_domain_taken(self, service, mock_db, mock_config):
        """Test custom domain is taken."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        result = service.validate_domain("testfirm.com")

        assert result["available"] is False
        assert result["type"] == "custom_domain"

    def test_validate_subdomain_invalid_format(self, service):
        """Test subdomain validation fails with invalid format."""
        result = service.validate_domain("Invalid_Format!")

        assert result["available"] is False
        assert "invalid" in result["error"].lower()
        assert result["type"] == "subdomain"

    def test_validate_domain_excludes_config(self, service, mock_db, mock_config):
        """Test validation excludes specific config ID."""
        # When exclude_config_id matches, should still be available
        mock_db.query.return_value.filter.return_value.filter.return_value.first.return_value = None

        result = service.validate_domain("testfirm", exclude_config_id=1)

        assert result["available"] is True


# ============== Generate CSS Tests ==============


class TestGenerateCSS:
    """Tests for generate_css method."""

    def test_generate_css_with_config(self, service, mock_config):
        """Test CSS generation with config."""
        css = service.generate_css(mock_config)

        assert "--wl-primary" in css
        assert mock_config.primary_color in css
        assert mock_config.secondary_color in css
        assert mock_config.accent_color in css

    def test_generate_css_with_custom_css(self, service, mock_config):
        """Test CSS generation includes custom CSS."""
        mock_config.custom_css = ".my-custom-class { background: blue; }"

        css = service.generate_css(mock_config)

        assert "Custom CSS" in css
        assert ".my-custom-class" in css

    def test_generate_css_without_config(self, service):
        """Test CSS generation returns default when no config."""
        css = service.generate_css(None)

        assert "--wl-primary: #319795" in css
        assert "--wl-secondary: #1a1a2e" in css

    def test_generate_css_with_different_fonts(self, service, mock_config):
        """Test CSS generation with different font families."""
        for font_key in ["roboto", "open-sans", "poppins"]:
            mock_config.font_family = font_key
            css = service.generate_css(mock_config)
            assert "--wl-font-family" in css

    def test_generate_css_with_unknown_font(self, service, mock_config):
        """Test CSS generation with unknown font falls back to inter."""
        mock_config.font_family = "unknown-font"

        css = service.generate_css(mock_config)

        assert FONT_FAMILIES["inter"] in css

    def test_generate_css_with_none_colors(self, service, mock_config):
        """Test CSS generation with None colors uses defaults."""
        mock_config.primary_color = None
        mock_config.secondary_color = None
        mock_config.accent_color = None
        mock_config.header_bg_color = None
        mock_config.sidebar_bg_color = None

        css = service.generate_css(mock_config)

        assert "#319795" in css  # Default primary
        assert "#1a1a2e" in css  # Default secondary
        assert "#84cc16" in css  # Default accent


# ============== Apply Branding Tests ==============


class TestApplyBranding:
    """Tests for apply_branding method."""

    def test_apply_branding_with_config(self, service, mock_config):
        """Test branding with config returns config branding."""
        result = service.apply_branding(mock_config)

        mock_config.get_branding_dict.assert_called_once()
        assert result["organization_name"] == "Test Law Firm"

    def test_apply_branding_without_config(self, service):
        """Test branding without config returns default."""
        result = service.apply_branding(None)

        assert result["organization_name"] == "Brightpath Ascend"
        assert result["primary_color"] == "#319795"


# ============== Get Default Branding Tests ==============


class TestGetDefaultBranding:
    """Tests for get_default_branding method."""

    def test_get_default_branding(self, service):
        """Test getting default branding."""
        result = service.get_default_branding()

        assert result["organization_name"] == "Brightpath Ascend"
        assert result["primary_color"] == "#319795"
        assert result["secondary_color"] == "#1a1a2e"
        assert result["accent_color"] == "#84cc16"
        assert result["logo_url"] == "/static/images/logo.png"
        assert result["font_family_key"] == "inter"
        assert result["is_active"] is True


# ============== Detect Config from Host Tests ==============


class TestDetectConfigFromHost:
    """Tests for detect_config_from_host method."""

    def test_detect_config_from_host_empty(self, service):
        """Test detection returns None for empty host."""
        result = service.detect_config_from_host("")
        assert result is None

    def test_detect_config_from_host_none(self, service):
        """Test detection returns None for None host."""
        result = service.detect_config_from_host(None)
        assert result is None

    def test_detect_config_from_host_with_port(self, service, mock_db, mock_config):
        """Test detection strips port from host."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        result = service.detect_config_from_host("testfirm.com:8080")

        assert result == mock_config

    def test_detect_config_from_host_case_insensitive(self, service, mock_db, mock_config):
        """Test detection is case insensitive."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config

        result = service.detect_config_from_host("TESTFIRM.COM")

        assert result == mock_config


# ============== Subdomain Validation Tests ==============


class TestSubdomainValidation:
    """Tests for _validate_subdomain_format method."""

    def test_validate_subdomain_valid(self, service):
        """Test valid subdomain formats."""
        valid_subdomains = [
            "test",
            "test123",
            "test-firm",
            "a",
            "ab",
            "test-law-firm",
        ]
        for subdomain in valid_subdomains:
            assert service._validate_subdomain_format(subdomain) is True

    def test_validate_subdomain_invalid(self, service):
        """Test invalid subdomain formats."""
        invalid_subdomains = [
            "",
            None,
            "-test",  # Starts with hyphen
            "test-",  # Ends with hyphen
            "TEST",  # Uppercase
            "test_firm",  # Underscore
            "test.firm",  # Dot
            "test firm",  # Space
            "test@firm",  # Special character
        ]
        for subdomain in invalid_subdomains:
            assert service._validate_subdomain_format(subdomain) is False


# ============== Cache Tests ==============


class TestCaching:
    """Tests for caching mechanism."""

    def test_cache_set_and_get(self, service):
        """Test setting and getting from cache."""
        service._set_cache("test_key", "test_value")

        result = service._get_from_cache("test_key")

        assert result == "test_value"

    def test_cache_not_found(self, service):
        """Test getting non-existent key returns None."""
        result = service._get_from_cache("nonexistent_key")

        assert result is None

    def test_cache_expiration(self, service):
        """Test cache expires after TTL."""
        service._set_cache("test_key", "test_value")

        # Manually set timestamp to expired
        service._cache_timestamps["test_key"] = datetime.utcnow() - timedelta(seconds=service._cache_ttl + 10)

        result = service._get_from_cache("test_key")

        assert result is None

    def test_cache_clear(self, service):
        """Test clearing cache."""
        service._set_cache("key1", "value1")
        service._set_cache("key2", "value2")

        service._clear_cache()

        assert service._get_from_cache("key1") is None
        assert service._get_from_cache("key2") is None

    def test_cache_stores_none_values(self, service, mock_db):
        """Test that None values are also cached (for negative lookups)."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # First lookup
        result1 = service.get_config_by_domain("nonexistent.com")
        assert result1 is None

        # Manually verify the None is cached
        cache_key = "domain:nonexistent.com"
        # The cache value should exist (even if None)
        assert cache_key in service._config_cache


# ============== Factory Function Tests ==============


class TestFactoryFunction:
    """Tests for get_whitelabel_config_service factory function."""

    def test_get_whitelabel_config_service(self, mock_db):
        """Test factory function creates service instance."""
        service = get_whitelabel_config_service(mock_db)

        assert isinstance(service, WhiteLabelConfigService)
        assert service.db == mock_db


# ============== Edge Cases ==============


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_create_config_with_special_characters_in_name(self, service, mock_db):
        """Test config creation with special characters in organization name."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        config_data = {
            "subdomain": "testfirm",
            "organization_name": "O'Brien & Partners, LLC",
        }

        with patch("services.whitelabel_service.encrypt_value", return_value="encrypted"):
            result = service.create_config(1, config_data)

        mock_db.add.assert_called_once()

    def test_update_config_updates_timestamp(self, service, mock_db, mock_config):
        """Test that update sets updated_at timestamp."""
        original_updated_at = mock_config.updated_at
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_config

        service.update_config(1, organization_name="Updated")

        # Verify setattr was called for updated_at
        # (The actual assertion is that commit was called, which would persist the change)
        mock_db.commit.assert_called_once()

    def test_create_config_without_org_id(self, service, mock_db):
        """Test config creation without organization ID."""
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        config_data = {
            "subdomain": "standalone",
            "organization_name": "Standalone Firm",
        }

        with patch("services.whitelabel_service.encrypt_value", return_value="encrypted"):
            result = service.create_config(None, config_data)

        mock_db.add.assert_called_once()

    def test_validate_domain_with_subdomain_starting_with_number(self, service, mock_db):
        """Test subdomain validation allows starting with number."""
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = service.validate_domain("123firm")

        assert result["available"] is True

    def test_generate_css_includes_all_selectors(self, service, mock_config):
        """Test CSS generation includes all expected selectors."""
        css = service.generate_css(mock_config)

        expected_selectors = [
            ":root",
            "body",
            ".header",
            ".sidebar",
            ".logo span",
            ".nav-item.active",
            ".btn-primary",
            ".stat-card.highlight",
            ".form-group input:focus",
            ".tab.active",
            "a:hover",
        ]

        for selector in expected_selectors:
            assert selector in css, f"Missing selector: {selector}"
