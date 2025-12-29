"""
White-Label Service for Multi-Tenant Branding
Handles tenant management, branding, and access control for partner law firms.
"""

import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from database import (
    SUBSCRIPTION_TIERS,
    Analysis,
    Case,
    Client,
    Staff,
    TenantClient,
    TenantUser,
    WhiteLabelTenant,
)


class WhiteLabelService:
    """Service class for white-label tenant management"""

    def __init__(self, db: Session):
        self.db = db

    def create_tenant(
        self, name: str, slug: str, settings: Optional[Dict[str, Any]] = None
    ) -> WhiteLabelTenant:
        """
        Create a new white-label tenant.

        Args:
            name: Display name for the tenant
            slug: URL-friendly unique identifier
            settings: Optional dictionary with additional settings

        Returns:
            Created WhiteLabelTenant instance
        """
        settings = settings or {}

        existing = self.db.query(WhiteLabelTenant).filter_by(slug=slug).first()
        if existing:
            raise ValueError(f"Tenant with slug '{slug}' already exists")

        if settings.get("domain"):
            existing_domain = (
                self.db.query(WhiteLabelTenant)
                .filter_by(domain=settings["domain"])
                .first()
            )
            if existing_domain:
                raise ValueError(
                    f"Tenant with domain '{settings['domain']}' already exists"
                )

        api_key = self._generate_api_key()

        tier = settings.get("subscription_tier", "basic")
        tier_config = SUBSCRIPTION_TIERS.get(tier, SUBSCRIPTION_TIERS["basic"])

        tenant = WhiteLabelTenant(
            name=name,
            slug=slug,
            domain=settings.get("domain"),
            logo_url=settings.get("logo_url"),
            favicon_url=settings.get("favicon_url"),
            primary_color=settings.get("primary_color", "#319795"),
            secondary_color=settings.get("secondary_color", "#1a1a2e"),
            accent_color=settings.get("accent_color", "#84cc16"),
            company_name=settings.get("company_name", name),
            company_address=settings.get("company_address"),
            company_phone=settings.get("company_phone"),
            company_email=settings.get("company_email"),
            support_email=settings.get("support_email"),
            terms_url=settings.get("terms_url"),
            privacy_url=settings.get("privacy_url"),
            custom_css=settings.get("custom_css"),
            custom_js=settings.get("custom_js"),
            is_active=settings.get("is_active", True),
            subscription_tier=tier,
            max_users=settings.get("max_users", tier_config["max_users"]),
            max_clients=settings.get("max_clients", tier_config["max_clients"]),
            features_enabled=settings.get("features_enabled", tier_config["features"]),
            api_key=api_key,
            webhook_url=settings.get("webhook_url"),
        )

        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)

        return tenant

    def update_tenant(self, tenant_id: int, **kwargs) -> Optional[WhiteLabelTenant]:
        """
        Update an existing tenant.

        Args:
            tenant_id: ID of the tenant to update
            **kwargs: Fields to update

        Returns:
            Updated WhiteLabelTenant instance or None if not found
        """
        tenant = self.db.query(WhiteLabelTenant).filter_by(id=tenant_id).first()
        if not tenant:
            return None

        if "slug" in kwargs and kwargs["slug"] != tenant.slug:
            existing = (
                self.db.query(WhiteLabelTenant)
                .filter(
                    WhiteLabelTenant.slug == kwargs["slug"],
                    WhiteLabelTenant.id != tenant_id,
                )
                .first()
            )
            if existing:
                raise ValueError(f"Tenant with slug '{kwargs['slug']}' already exists")

        if (
            "domain" in kwargs
            and kwargs["domain"]
            and kwargs["domain"] != tenant.domain
        ):
            existing = (
                self.db.query(WhiteLabelTenant)
                .filter(
                    WhiteLabelTenant.domain == kwargs["domain"],
                    WhiteLabelTenant.id != tenant_id,
                )
                .first()
            )
            if existing:
                raise ValueError(
                    f"Tenant with domain '{kwargs['domain']}' already exists"
                )

        allowed_fields = [
            "name",
            "slug",
            "domain",
            "logo_url",
            "favicon_url",
            "primary_color",
            "secondary_color",
            "accent_color",
            "company_name",
            "company_address",
            "company_phone",
            "company_email",
            "support_email",
            "terms_url",
            "privacy_url",
            "custom_css",
            "custom_js",
            "is_active",
            "subscription_tier",
            "max_users",
            "max_clients",
            "features_enabled",
            "webhook_url",
        ]

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(tenant, key, value)

        tenant.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(tenant)

        return tenant

    def delete_tenant(self, tenant_id: int) -> bool:
        """
        Delete a tenant and all associated data.

        Args:
            tenant_id: ID of the tenant to delete

        Returns:
            True if deleted, False if not found
        """
        tenant = self.db.query(WhiteLabelTenant).filter_by(id=tenant_id).first()
        if not tenant:
            return False

        self.db.delete(tenant)
        self.db.commit()
        return True

    def get_tenant_by_id(self, tenant_id: int) -> Optional[WhiteLabelTenant]:
        """Get a tenant by ID"""
        return self.db.query(WhiteLabelTenant).filter_by(id=tenant_id).first()

    def get_tenant_by_slug(self, slug: str) -> Optional[WhiteLabelTenant]:
        """Get a tenant by slug"""
        return (
            self.db.query(WhiteLabelTenant).filter_by(slug=slug, is_active=True).first()
        )

    def get_tenant_by_domain(self, domain: str) -> Optional[WhiteLabelTenant]:
        """Get a tenant by custom domain"""
        if not domain:
            return None
        return (
            self.db.query(WhiteLabelTenant)
            .filter_by(domain=domain, is_active=True)
            .first()
        )

    def get_tenant_by_api_key(self, api_key: str) -> Optional[WhiteLabelTenant]:
        """Get a tenant by API key"""
        if not api_key:
            return None
        return (
            self.db.query(WhiteLabelTenant)
            .filter_by(api_key=api_key, is_active=True)
            .first()
        )

    def get_all_tenants(self, include_inactive: bool = False) -> List[WhiteLabelTenant]:
        """Get all tenants"""
        query = self.db.query(WhiteLabelTenant)
        if not include_inactive:
            query = query.filter_by(is_active=True)
        return query.order_by(WhiteLabelTenant.name).all()

    def get_tenant_branding(self, tenant_id: int) -> Optional[Dict[str, Any]]:
        """
        Get branding configuration for a tenant.

        Args:
            tenant_id: ID of the tenant

        Returns:
            Dictionary with branding configuration or None if not found
        """
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return None

        return tenant.get_branding_config()

    def get_default_branding(self) -> Dict[str, Any]:
        """Get default branding for non-tenant requests"""
        return {
            "primary_color": "#319795",
            "secondary_color": "#1a1a2e",
            "accent_color": "#84cc16",
            "logo_url": "/static/images/logo.png",
            "favicon_url": None,
            "company_name": "Brightpath Ascend",
            "company_address": None,
            "company_phone": None,
            "company_email": None,
            "support_email": None,
            "terms_url": None,
            "privacy_url": None,
            "custom_css": None,
            "custom_js": None,
        }

    def assign_user_to_tenant(
        self,
        staff_id: int,
        tenant_id: int,
        role: str = "user",
        is_primary_admin: bool = False,
    ) -> TenantUser:
        """
        Assign a staff member to a tenant.

        Args:
            staff_id: ID of the staff member
            tenant_id: ID of the tenant
            role: Role within the tenant (user, admin, etc.)
            is_primary_admin: Whether this user is the primary admin

        Returns:
            Created or updated TenantUser instance
        """
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant with ID {tenant_id} not found")

        staff = self.db.query(Staff).filter_by(id=staff_id).first()
        if not staff:
            raise ValueError(f"Staff member with ID {staff_id} not found")

        current_count = self.db.query(TenantUser).filter_by(tenant_id=tenant_id).count()
        if current_count >= tenant.max_users:
            raise ValueError(
                f"Tenant has reached maximum user limit ({tenant.max_users})"
            )

        existing = (
            self.db.query(TenantUser)
            .filter_by(tenant_id=tenant_id, staff_id=staff_id)
            .first()
        )

        if existing:
            existing.role = role
            existing.is_primary_admin = is_primary_admin
            self.db.commit()
            return existing

        tenant_user = TenantUser(
            tenant_id=tenant_id,
            staff_id=staff_id,
            role=role,
            is_primary_admin=is_primary_admin,
        )

        self.db.add(tenant_user)
        self.db.commit()
        self.db.refresh(tenant_user)

        return tenant_user

    def remove_user_from_tenant(self, staff_id: int, tenant_id: int) -> bool:
        """Remove a staff member from a tenant"""
        tenant_user = (
            self.db.query(TenantUser)
            .filter_by(tenant_id=tenant_id, staff_id=staff_id)
            .first()
        )

        if not tenant_user:
            return False

        self.db.delete(tenant_user)
        self.db.commit()
        return True

    def assign_client_to_tenant(self, client_id: int, tenant_id: int) -> TenantClient:
        """
        Assign a client to a tenant.

        Args:
            client_id: ID of the client
            tenant_id: ID of the tenant

        Returns:
            Created TenantClient instance
        """
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant with ID {tenant_id} not found")

        client = self.db.query(Client).filter_by(id=client_id).first()
        if not client:
            raise ValueError(f"Client with ID {client_id} not found")

        current_count = (
            self.db.query(TenantClient).filter_by(tenant_id=tenant_id).count()
        )
        if current_count >= tenant.max_clients:
            raise ValueError(
                f"Tenant has reached maximum client limit ({tenant.max_clients})"
            )

        existing = (
            self.db.query(TenantClient)
            .filter_by(tenant_id=tenant_id, client_id=client_id)
            .first()
        )

        if existing:
            return existing

        tenant_client = TenantClient(tenant_id=tenant_id, client_id=client_id)

        self.db.add(tenant_client)
        self.db.commit()
        self.db.refresh(tenant_client)

        return tenant_client

    def remove_client_from_tenant(self, client_id: int, tenant_id: int) -> bool:
        """Remove a client from a tenant"""
        tenant_client = (
            self.db.query(TenantClient)
            .filter_by(tenant_id=tenant_id, client_id=client_id)
            .first()
        )

        if not tenant_client:
            return False

        self.db.delete(tenant_client)
        self.db.commit()
        return True

    def get_tenant_users(self, tenant_id: int) -> List[TenantUser]:
        """Get all users assigned to a tenant"""
        return self.db.query(TenantUser).filter_by(tenant_id=tenant_id).all()

    def get_tenant_clients(self, tenant_id: int) -> List[TenantClient]:
        """Get all clients assigned to a tenant"""
        return self.db.query(TenantClient).filter_by(tenant_id=tenant_id).all()

    def get_user_tenants(self, staff_id: int) -> List[WhiteLabelTenant]:
        """Get all tenants a user belongs to"""
        tenant_users = self.db.query(TenantUser).filter_by(staff_id=staff_id).all()
        tenant_ids = [tu.tenant_id for tu in tenant_users]
        return (
            self.db.query(WhiteLabelTenant)
            .filter(
                WhiteLabelTenant.id.in_(tenant_ids), WhiteLabelTenant.is_active == True
            )
            .all()
        )

    def get_client_tenant(self, client_id: int) -> Optional[WhiteLabelTenant]:
        """Get the tenant a client belongs to"""
        tenant_client = (
            self.db.query(TenantClient).filter_by(client_id=client_id).first()
        )
        if not tenant_client:
            return None
        return self.get_tenant_by_id(tenant_client.tenant_id)

    def generate_tenant_api_key(self, tenant_id: int) -> str:
        """
        Regenerate API key for a tenant.

        Args:
            tenant_id: ID of the tenant

        Returns:
            New API key
        """
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant with ID {tenant_id} not found")

        new_api_key = self._generate_api_key()
        tenant.api_key = new_api_key
        tenant.updated_at = datetime.utcnow()
        self.db.commit()

        return new_api_key

    def validate_tenant_features(self, tenant_id: int, feature_name: str) -> bool:
        """
        Check if a tenant has access to a specific feature.

        Args:
            tenant_id: ID of the tenant
            feature_name: Name of the feature to check

        Returns:
            True if feature is enabled, False otherwise
        """
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant or not tenant.is_active:
            return False

        features = tenant.features_enabled or []
        if isinstance(features, dict):
            features = list(features.keys()) if features else []

        tier_config = SUBSCRIPTION_TIERS.get(
            tenant.subscription_tier, SUBSCRIPTION_TIERS["basic"]
        )
        tier_features = tier_config.get("features", [])

        return feature_name in features or feature_name in tier_features

    def get_tenant_usage_stats(self, tenant_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a tenant.

        Args:
            tenant_id: ID of the tenant

        Returns:
            Dictionary with usage statistics
        """
        tenant = self.get_tenant_by_id(tenant_id)
        if not tenant:
            return None

        user_count = self.db.query(TenantUser).filter_by(tenant_id=tenant_id).count()
        client_count = (
            self.db.query(TenantClient).filter_by(tenant_id=tenant_id).count()
        )

        client_ids = [tc.client_id for tc in self.get_tenant_clients(tenant_id)]

        case_count = 0
        analysis_count = 0
        active_clients = 0

        if client_ids:
            case_count = (
                self.db.query(Case).filter(Case.client_id.in_(client_ids)).count()
            )
            analysis_count = (
                self.db.query(Analysis)
                .filter(Analysis.client_id.in_(client_ids))
                .count()
            )
            active_clients = (
                self.db.query(Client)
                .filter(Client.id.in_(client_ids), Client.status == "active")
                .count()
            )

        return {
            "tenant_id": tenant_id,
            "tenant_name": tenant.name,
            "subscription_tier": tenant.subscription_tier,
            # Flat attributes for template compatibility
            "user_count": user_count,
            "max_users": tenant.max_users,
            "client_count": client_count,
            "max_clients": tenant.max_clients,
            "active_clients": active_clients,
            # Nested structure for API use
            "users": {
                "current": user_count,
                "max": tenant.max_users,
                "usage_percent": (
                    round((user_count / tenant.max_users) * 100, 1)
                    if tenant.max_users > 0
                    else 0
                ),
            },
            "clients": {
                "current": client_count,
                "max": tenant.max_clients,
                "active": active_clients,
                "usage_percent": (
                    round((client_count / tenant.max_clients) * 100, 1)
                    if tenant.max_clients > 0
                    else 0
                ),
            },
            "cases": case_count,
            "analyses": analysis_count,
            "is_active": tenant.is_active,
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "features_enabled": tenant.features_enabled or [],
        }

    def detect_tenant_from_host(self, host: str) -> Optional[WhiteLabelTenant]:
        """
        Detect tenant from request host.

        Args:
            host: Request host (e.g., 'partner.example.com' or 'partner.brightpathascend.com')

        Returns:
            Matched tenant or None
        """
        if not host:
            return None

        host = host.lower().split(":")[0]

        tenant = self.get_tenant_by_domain(host)
        if tenant:
            return tenant

        parts = host.split(".")
        if len(parts) >= 2:
            subdomain = parts[0]
            if subdomain not in ["www", "app", "api", "admin"]:
                tenant = self.get_tenant_by_slug(subdomain)
                if tenant:
                    return tenant

        return None

    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        return f"wl_{secrets.token_urlsafe(32)}"


def get_white_label_service(db: Session) -> WhiteLabelService:
    """Factory function to create WhiteLabelService instance"""
    return WhiteLabelService(db)
