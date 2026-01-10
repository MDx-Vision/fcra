"""
White-Label Service for Partner Law Firm Branding
Provides multi-tenant branding configuration for the client portal.
Uses Fernet encryption for sensitive config values.
"""

import re
import secrets
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from database import FONT_FAMILIES, FranchiseOrganization, WhiteLabelConfig
from services.encryption import decrypt_value, encrypt_value


class WhiteLabelConfigService:
    """Service class for white-label configuration management"""

    _config_cache: Dict[str, Any] = {}
    _cache_ttl = 300
    _cache_timestamps: Dict[str, datetime] = {}

    def __init__(self, db: Session):
        self.db = db

    def get_config_by_domain(self, domain: str) -> Optional[WhiteLabelConfig]:
        """
        Lookup white-label config by subdomain or custom domain.

        Args:
            domain: The domain or subdomain to look up

        Returns:
            WhiteLabelConfig if found, None otherwise
        """
        if not domain:
            return None

        domain = domain.lower().strip()

        cache_key = f"domain:{domain}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        config = (
            self.db.query(WhiteLabelConfig)
            .filter(
                WhiteLabelConfig.custom_domain == domain,
                WhiteLabelConfig.is_active == True,
            )
            .first()
        )

        if config:
            self._set_cache(cache_key, config)
            return config

        parts = domain.split(".")
        if len(parts) >= 2:
            subdomain = parts[0]
            if subdomain not in ["www", "app", "api", "admin", "mail", "smtp"]:
                config = (
                    self.db.query(WhiteLabelConfig)
                    .filter(
                        WhiteLabelConfig.subdomain == subdomain,
                        WhiteLabelConfig.is_active == True,
                    )
                    .first()
                )

                if config:
                    self._set_cache(cache_key, config)
                    return config

        self._set_cache(cache_key, None)
        return None

    def get_config_by_org(self, organization_id: int) -> Optional[WhiteLabelConfig]:
        """
        Lookup white-label config by organization ID.

        Args:
            organization_id: The organization ID

        Returns:
            WhiteLabelConfig if found, None otherwise
        """
        if not organization_id:
            return None

        cache_key = f"org:{organization_id}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        config = (
            self.db.query(WhiteLabelConfig)
            .filter(
                WhiteLabelConfig.organization_id == organization_id,
                WhiteLabelConfig.is_active == True,
            )
            .first()
        )

        self._set_cache(cache_key, config)
        return config

    def get_config_by_id(self, config_id: int) -> Optional[WhiteLabelConfig]:
        """Get a specific white-label config by ID"""
        return self.db.query(WhiteLabelConfig).filter_by(id=config_id).first()

    def create_config(
        self, org_id: Optional[int], config_data: Dict[str, Any]
    ) -> WhiteLabelConfig:
        """
        Create a new white-label configuration.

        Args:
            org_id: Organization ID (optional)
            config_data: Configuration data dictionary

        Returns:
            Created WhiteLabelConfig instance

        Raises:
            ValueError: If subdomain or custom_domain already exists
        """
        subdomain = config_data.get("subdomain", "").lower().strip()
        custom_domain = (
            config_data.get("custom_domain", "").lower().strip()
            if config_data.get("custom_domain")
            else None
        )

        if not subdomain:
            raise ValueError("Subdomain is required")

        if not self._validate_subdomain_format(subdomain):
            raise ValueError(
                "Invalid subdomain format. Use only lowercase letters, numbers, and hyphens."
            )

        existing = (
            self.db.query(WhiteLabelConfig).filter_by(subdomain=subdomain).first()
        )
        if existing:
            raise ValueError(f"Subdomain '{subdomain}' is already in use")

        if custom_domain:
            existing = (
                self.db.query(WhiteLabelConfig)
                .filter_by(custom_domain=custom_domain)
                .first()
            )
            if existing:
                raise ValueError(f"Custom domain '{custom_domain}' is already in use")

        email_from_address_encrypted = None
        if config_data.get("email_from_address"):
            email_from_address_encrypted = encrypt_value(
                config_data["email_from_address"]
            )

        config = WhiteLabelConfig(
            organization_id=org_id,
            organization_name=config_data.get("organization_name", ""),
            subdomain=subdomain,
            custom_domain=custom_domain,
            logo_url=config_data.get("logo_url"),
            favicon_url=config_data.get("favicon_url"),
            primary_color=config_data.get("primary_color", "#319795"),
            secondary_color=config_data.get("secondary_color", "#1a1a2e"),
            accent_color=config_data.get("accent_color", "#84cc16"),
            header_bg_color=config_data.get("header_bg_color", "#1a1a2e"),
            sidebar_bg_color=config_data.get("sidebar_bg_color", "#1a1a2e"),
            font_family=config_data.get("font_family", "inter"),
            custom_css=config_data.get("custom_css"),
            email_from_name=config_data.get("email_from_name"),
            email_from_address=config_data.get("email_from_address"),
            email_from_address_encrypted=email_from_address_encrypted,
            company_address=config_data.get("company_address"),
            company_phone=config_data.get("company_phone"),
            company_email=config_data.get("company_email"),
            footer_text=config_data.get("footer_text"),
            terms_url=config_data.get("terms_url"),
            privacy_url=config_data.get("privacy_url"),
            is_active=config_data.get("is_active", True),
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        self._clear_cache()

        return config

    def update_config(self, config_id: int, **kwargs) -> Optional[WhiteLabelConfig]:
        """
        Update an existing white-label configuration.

        Args:
            config_id: ID of the config to update
            **kwargs: Fields to update

        Returns:
            Updated WhiteLabelConfig instance or None if not found

        Raises:
            ValueError: If subdomain or custom_domain conflicts with existing config
        """
        config = self.get_config_by_id(config_id)
        if not config:
            return None

        if "subdomain" in kwargs and kwargs["subdomain"]:
            new_subdomain = kwargs["subdomain"].lower().strip()
            if new_subdomain != config.subdomain:
                if not self._validate_subdomain_format(new_subdomain):
                    raise ValueError("Invalid subdomain format")
                existing = (
                    self.db.query(WhiteLabelConfig)
                    .filter(
                        WhiteLabelConfig.subdomain == new_subdomain,
                        WhiteLabelConfig.id != config_id,
                    )
                    .first()
                )
                if existing:
                    raise ValueError(f"Subdomain '{new_subdomain}' is already in use")
                kwargs["subdomain"] = new_subdomain

        if "custom_domain" in kwargs and kwargs["custom_domain"]:
            new_domain = kwargs["custom_domain"].lower().strip()
            if new_domain != config.custom_domain:
                existing = (
                    self.db.query(WhiteLabelConfig)
                    .filter(
                        WhiteLabelConfig.custom_domain == new_domain,
                        WhiteLabelConfig.id != config_id,
                    )
                    .first()
                )
                if existing:
                    raise ValueError(f"Custom domain '{new_domain}' is already in use")
                kwargs["custom_domain"] = new_domain

        if "email_from_address" in kwargs and kwargs["email_from_address"]:
            kwargs["email_from_address_encrypted"] = encrypt_value(
                kwargs["email_from_address"]
            )

        allowed_fields = [
            "organization_id",
            "organization_name",
            "subdomain",
            "custom_domain",
            "logo_url",
            "favicon_url",
            "primary_color",
            "secondary_color",
            "accent_color",
            "header_bg_color",
            "sidebar_bg_color",
            "font_family",
            "custom_css",
            "email_from_name",
            "email_from_address",
            "email_from_address_encrypted",
            "company_address",
            "company_phone",
            "company_email",
            "footer_text",
            "terms_url",
            "privacy_url",
            "is_active",
        ]

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(config, key, value)

        setattr(config, 'updated_at', datetime.utcnow())
        self.db.commit()
        self.db.refresh(config)

        self._clear_cache()

        return config

    def delete_config(self, config_id: int) -> bool:
        """
        Delete a white-label configuration.

        Args:
            config_id: ID of the config to delete

        Returns:
            True if deleted, False if not found
        """
        config = self.get_config_by_id(config_id)
        if not config:
            return False

        self.db.delete(config)
        self.db.commit()

        self._clear_cache()

        return True

    def get_all_configs(self, include_inactive: bool = False) -> List[WhiteLabelConfig]:
        """
        Get all white-label configurations.

        Args:
            include_inactive: Whether to include inactive configs

        Returns:
            List of WhiteLabelConfig instances
        """
        query = self.db.query(WhiteLabelConfig)
        if not include_inactive:
            query = query.filter(WhiteLabelConfig.is_active == True)
        return query.order_by(WhiteLabelConfig.organization_name).all()

    def validate_domain(
        self, domain: str, exclude_config_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate if a domain/subdomain is available.

        Args:
            domain: Domain or subdomain to validate
            exclude_config_id: Config ID to exclude from check (for updates)

        Returns:
            Dictionary with validation result
        """
        if not domain:
            return {"available": False, "error": "Domain is required"}

        domain = domain.lower().strip()

        if "." in domain:
            query = self.db.query(WhiteLabelConfig).filter(
                WhiteLabelConfig.custom_domain == domain
            )
            domain_type = "custom_domain"
        else:
            if not self._validate_subdomain_format(domain):
                return {
                    "available": False,
                    "error": "Invalid format. Use only lowercase letters, numbers, and hyphens.",
                    "type": "subdomain",
                }
            query = self.db.query(WhiteLabelConfig).filter(
                WhiteLabelConfig.subdomain == domain
            )
            domain_type = "subdomain"

        if exclude_config_id:
            query = query.filter(WhiteLabelConfig.id != exclude_config_id)

        existing = query.first()

        if existing:
            return {
                "available": False,
                "error": f'This {domain_type.replace("_", " ")} is already in use',
                "type": domain_type,
            }

        return {"available": True, "domain": domain, "type": domain_type}

    def generate_css(self, config: WhiteLabelConfig) -> str:
        """
        Generate custom CSS from configuration.

        Args:
            config: WhiteLabelConfig instance

        Returns:
            CSS string with custom variables and styles
        """
        if not config:
            return self._get_default_css()

        font_family_key = str(config.font_family) if config.font_family else "inter"
        font_css = FONT_FAMILIES.get(font_family_key, FONT_FAMILIES["inter"])

        css = f"""
:root {{
    --wl-primary: {config.primary_color or '#319795'};
    --wl-secondary: {config.secondary_color or '#1a1a2e'};
    --wl-accent: {config.accent_color or '#84cc16'};
    --wl-header-bg: {config.header_bg_color or '#1a1a2e'};
    --wl-sidebar-bg: {config.sidebar_bg_color or '#1a1a2e'};
    --wl-font-family: {font_css};
}}

body {{
    font-family: var(--wl-font-family);
}}

.header, .portal-header {{
    background: linear-gradient(180deg, var(--wl-header-bg) 0%, color-mix(in srgb, var(--wl-header-bg), black 10%) 100%) !important;
}}

.sidebar {{
    background: linear-gradient(180deg, var(--wl-sidebar-bg) 0%, color-mix(in srgb, var(--wl-sidebar-bg), black 10%) 100%) !important;
}}

.logo span {{
    color: var(--wl-accent) !important;
}}

.nav-item.active {{
    background: linear-gradient(135deg, var(--wl-primary) 0%, var(--wl-accent) 100%) !important;
}}

.btn-primary {{
    background: linear-gradient(135deg, var(--wl-primary) 0%, var(--wl-accent) 100%) !important;
}}

.btn-primary:hover {{
    box-shadow: 0 4px 12px color-mix(in srgb, var(--wl-primary), transparent 60%) !important;
}}

.stat-card.highlight {{
    background: linear-gradient(135deg, var(--wl-secondary) 0%, color-mix(in srgb, var(--wl-secondary), black 10%) 100%) !important;
}}

.stat-card.highlight .stat-value {{
    color: var(--wl-accent) !important;
}}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {{
    border-color: var(--wl-primary) !important;
}}

.tab.active {{
    color: var(--wl-primary) !important;
    border-bottom-color: var(--wl-primary) !important;
}}

a:hover {{
    color: var(--wl-primary) !important;
}}
"""

        if config.custom_css:
            css += f"\n/* Custom CSS */\n{config.custom_css}"

        return css

    def apply_branding(
        self, config: Optional[WhiteLabelConfig] = None
    ) -> Dict[str, Any]:
        """
        Returns branding dictionary for templates.

        Args:
            config: WhiteLabelConfig instance (optional)

        Returns:
            Dictionary with branding configuration
        """
        if config:
            return config.get_branding_dict()

        return self._get_default_branding()

    def get_default_branding(self) -> Dict[str, Any]:
        """Get default Brightpath Ascend branding"""
        return self._get_default_branding()

    def detect_config_from_host(self, host: str) -> Optional[WhiteLabelConfig]:
        """
        Detect white-label config from request host.

        Args:
            host: Request host (e.g., 'partner.example.com')

        Returns:
            Matched WhiteLabelConfig or None
        """
        if not host:
            return None

        host = host.lower().split(":")[0]

        return self.get_config_by_domain(host)

    def _get_default_branding(self) -> Dict[str, Any]:
        """Return default branding configuration"""
        return {
            "organization_name": "Brightpath Ascend",
            "subdomain": None,
            "custom_domain": None,
            "logo_url": "/static/images/logo.png",
            "favicon_url": None,
            "primary_color": "#319795",
            "secondary_color": "#1a1a2e",
            "accent_color": "#84cc16",
            "header_bg_color": "#1a1a2e",
            "sidebar_bg_color": "#1a1a2e",
            "font_family": FONT_FAMILIES["inter"],
            "font_family_key": "inter",
            "custom_css": None,
            "email_from_name": "Brightpath Ascend",
            "email_from_address": None,
            "company_address": None,
            "company_phone": None,
            "company_email": None,
            "footer_text": "© 2024 Brightpath Ascend. All rights reserved.",
            "terms_url": None,
            "privacy_url": None,
            "is_active": True,
        }

    def _get_default_css(self) -> str:
        """Return default CSS variables"""
        return """
:root {
    --wl-primary: #319795;
    --wl-secondary: #1a1a2e;
    --wl-accent: #84cc16;
    --wl-header-bg: #1a1a2e;
    --wl-sidebar-bg: #1a1a2e;
    --wl-font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
"""

    def _validate_subdomain_format(self, subdomain: str) -> bool:
        """Validate subdomain format"""
        if not subdomain:
            return False
        pattern = r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?$"
        return bool(re.match(pattern, subdomain))

    def _get_from_cache(self, key: str) -> Any:
        """Get value from cache if not expired"""
        if key not in self._config_cache:
            return None

        timestamp = self._cache_timestamps.get(key)
        if (
            timestamp
            and (datetime.utcnow() - timestamp).total_seconds() > self._cache_ttl
        ):
            del self._config_cache[key]
            del self._cache_timestamps[key]
            return None

        return self._config_cache.get(key)

    def _set_cache(self, key: str, value: Any):
        """Set value in cache with timestamp"""
        self._config_cache[key] = value
        self._cache_timestamps[key] = datetime.utcnow()

    def _clear_cache(self):
        """Clear all cached configs"""
        self._config_cache.clear()
        self._cache_timestamps.clear()


def get_whitelabel_config_service(db: Session) -> WhiteLabelConfigService:
    """Factory function to create WhiteLabelConfigService instance"""
    return WhiteLabelConfigService(db)
