"""
Centralized Configuration Management for FCRA Litigation Platform

Provides:
- Environment variable loading with python-dotenv
- Validation of required settings
- Type coercion and defaults
- Categorized configuration access

Usage:
    from services.config import config

    # Access settings
    api_key = config.ANTHROPIC_API_KEY
    debug = config.DEBUG

    # Check if properly configured
    if config.is_configured('sendgrid'):
        send_email(...)
"""

import os
import secrets
from functools import lru_cache

# Load .env file if it exists (for local development)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""

    pass


class Config:
    """
    Centralized configuration management.
    All environment variables are accessed through this class.
    """

    # =========================================================================
    # CORE FLASK SETTINGS
    # =========================================================================

    @property
    def SECRET_KEY(self) -> str:
        """Flask secret key for session encryption. Auto-generated if not set."""
        return os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)

    @property
    def DEBUG(self) -> bool:
        """Enable Flask debug mode."""
        return os.environ.get("FLASK_DEBUG", "").lower() in ("true", "1", "yes")

    @property
    def ENV(self) -> str:
        """Flask environment (development, production, testing)."""
        return os.environ.get("FLASK_ENV", "development")

    @property
    def IS_PRODUCTION(self) -> bool:
        """Check if running in production."""
        return self.ENV == "production" or os.environ.get("REPLIT_DEPLOYMENT") == "1"

    @property
    def IS_CI(self) -> bool:
        """Check if running in CI environment."""
        return os.environ.get("CI", "").lower() == "true"

    @property
    def PORT(self) -> int:
        """Server port."""
        return int(os.environ.get("PORT", 5000))

    # =========================================================================
    # DATABASE
    # =========================================================================

    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL database connection URL."""
        return os.environ.get("DATABASE_URL", "")

    # =========================================================================
    # LOGGING
    # =========================================================================

    @property
    def LOG_LEVEL(self) -> str:
        """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        return os.environ.get("LOG_LEVEL", "INFO").upper()

    # =========================================================================
    # RATE LIMITING
    # =========================================================================

    @property
    def RATE_LIMIT_DEFAULT(self) -> str:
        """Default rate limit for all endpoints."""
        return os.environ.get("RATE_LIMIT_DEFAULT", "200 per minute")

    @property
    def RATE_LIMIT_AUTH(self) -> str:
        """Rate limit for authentication endpoints (stricter)."""
        return os.environ.get("RATE_LIMIT_AUTH", "5 per minute")

    @property
    def RATE_LIMIT_API(self) -> str:
        """Rate limit for standard API endpoints."""
        return os.environ.get("RATE_LIMIT_API", "100 per minute")

    @property
    def RATE_LIMIT_ANALYSIS(self) -> str:
        """Rate limit for AI analysis endpoints (expensive operations)."""
        return os.environ.get("RATE_LIMIT_ANALYSIS", "10 per minute")

    # =========================================================================
    # AI / ANTHROPIC
    # =========================================================================

    @property
    def ANTHROPIC_API_KEY(self) -> str:
        """Anthropic API key for Claude AI."""
        # Support both naming conventions
        return os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get(
            "FCRA Automation Secure", ""
        )

    # =========================================================================
    # EMAIL (GMAIL SMTP)
    # =========================================================================

    @property
    def GMAIL_USER(self) -> str:
        """Gmail email address for SMTP authentication."""
        return os.environ.get("GMAIL_USER", "")

    @property
    def GMAIL_APP_PASSWORD(self) -> str:
        """Gmail App Password for SMTP authentication (requires 2FA enabled)."""
        return os.environ.get("GMAIL_APP_PASSWORD", "")

    @property
    def EMAIL_FROM_ADDRESS(self) -> str:
        """Default sender email address."""
        return os.environ.get("EMAIL_FROM_ADDRESS", self.GMAIL_USER or "noreply@fcra-platform.com")

    @property
    def EMAIL_FROM_NAME(self) -> str:
        """Default sender name."""
        return os.environ.get("EMAIL_FROM_NAME", "Brightpath Ascend Group")

    # Legacy SendGrid properties (deprecated - kept for backward compatibility)
    @property
    def SENDGRID_API_KEY(self) -> str:
        """Deprecated - use GMAIL_USER and GMAIL_APP_PASSWORD instead."""
        return os.environ.get("SENDGRID_API_KEY", "")

    @property
    def SENDGRID_FROM_EMAIL(self) -> str:
        """Deprecated - use EMAIL_FROM_ADDRESS instead."""
        return self.EMAIL_FROM_ADDRESS

    @property
    def SENDGRID_FROM_NAME(self) -> str:
        """Deprecated - use EMAIL_FROM_NAME instead."""
        return self.EMAIL_FROM_NAME

    # =========================================================================
    # SMS (TWILIO)
    # =========================================================================

    @property
    def TWILIO_ACCOUNT_SID(self) -> str:
        """Twilio account SID."""
        return os.environ.get("TWILIO_ACCOUNT_SID", "")

    @property
    def TWILIO_AUTH_TOKEN(self) -> str:
        """Twilio authentication token."""
        return os.environ.get("TWILIO_AUTH_TOKEN", "")

    @property
    def TWILIO_PHONE_NUMBER(self) -> str:
        """Twilio phone number for sending SMS."""
        return os.environ.get("TWILIO_PHONE_NUMBER", "")

    @property
    def TWILIO_MESSAGING_SERVICE_SID(self) -> str:
        """Twilio Messaging Service SID for A2P 10DLC compliance."""
        return os.environ.get("TWILIO_MESSAGING_SERVICE_SID", "")

    # =========================================================================
    # PAYMENTS (STRIPE)
    # =========================================================================

    @property
    def STRIPE_SECRET_KEY(self) -> str:
        """Stripe secret API key."""
        return os.environ.get("STRIPE_SECRET_KEY", "")

    @property
    def STRIPE_WEBHOOK_SECRET(self) -> str:
        """Stripe webhook signing secret."""
        return os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    # =========================================================================
    # CERTIFIED MAIL (SENDCERTIFIED)
    # =========================================================================

    @property
    def SENDCERTIFIED_API_KEY(self) -> str:
        """SendCertifiedMail API key."""
        return os.environ.get("SENDCERTIFIEDMAIL_API_KEY", "")

    @property
    def SENDCERTIFIED_SFTP_HOST(self) -> str:
        """SendCertified SFTP hostname."""
        return os.environ.get("SENDCERTIFIED_SFTP_HOST", "")

    @property
    def SENDCERTIFIED_SFTP_USERNAME(self) -> str:
        """SendCertified SFTP username."""
        return os.environ.get("SENDCERTIFIED_SFTP_USERNAME", "")

    @property
    def SENDCERTIFIED_SFTP_PASSWORD(self) -> str:
        """SendCertified SFTP password."""
        return os.environ.get("SENDCERTIFIED_SFTP_PASSWORD", "")

    @property
    def SENDCERTIFIED_SFTP_PORT(self) -> int:
        """SendCertified SFTP port."""
        return int(os.environ.get("SENDCERTIFIED_SFTP_PORT", 22))

    # =========================================================================
    # CREDIT MONITORING SERVICES
    # =========================================================================

    @property
    def SMARTCREDIT_API_KEY(self) -> str:
        """SmartCredit API key."""
        return os.environ.get("SMARTCREDIT_API_KEY", "")

    @property
    def IDENTITYIQ_API_KEY(self) -> str:
        """IdentityIQ API key."""
        return os.environ.get("IDENTITYIQ_API_KEY", "")

    @property
    def IDENTITYIQ_API_SECRET(self) -> str:
        """IdentityIQ API secret."""
        return os.environ.get("IDENTITYIQ_API_SECRET", "")

    @property
    def EXPERIAN_API_KEY(self) -> str:
        """Experian API key."""
        return os.environ.get("EXPERIAN_API_KEY", "")

    @property
    def EXPERIAN_CLIENT_ID(self) -> str:
        """Experian client ID."""
        return os.environ.get("EXPERIAN_CLIENT_ID", "")

    @property
    def EXPERIAN_CLIENT_SECRET(self) -> str:
        """Experian client secret."""
        return os.environ.get("EXPERIAN_CLIENT_SECRET", "")

    @property
    def EXPERIAN_SUBSCRIBER_CODE(self) -> str:
        """Experian subscriber code."""
        return os.environ.get("EXPERIAN_SUBSCRIBER_CODE", "")

    # =========================================================================
    # NOTARIZATION (PROOF/NOTARIZE)
    # =========================================================================

    @property
    def NOTARIZE_API_KEY(self) -> str:
        """Notarize/Proof API key."""
        return os.environ.get("NOTARIZE_API_KEY") or os.environ.get("PROOF_API_KEY", "")

    @property
    def NOTARIZE_WEBHOOK_SECRET(self) -> str:
        """Notarize webhook signing secret."""
        return os.environ.get("NOTARIZE_WEBHOOK_SECRET", "")

    @property
    def NOTARIZE_SANDBOX(self) -> bool:
        """Use Notarize sandbox environment."""
        return os.environ.get("NOTARIZE_SANDBOX", "true").lower() in (
            "true",
            "1",
            "yes",
        )

    # =========================================================================
    # SECURITY
    # =========================================================================

    @property
    def ENCRYPTION_KEY(self) -> str:
        """Fernet encryption key for sensitive data."""
        return os.environ.get("FCRA_ENCRYPTION_KEY", "")

    # =========================================================================
    # REPLIT-SPECIFIC
    # =========================================================================

    @property
    def REPLIT_DEV_DOMAIN(self) -> str:
        """Replit development domain."""
        return os.environ.get("REPLIT_DEV_DOMAIN", "")

    @property
    def REPLIT_DEPLOYMENT(self) -> bool:
        """Check if deployed on Replit."""
        return os.environ.get("REPLIT_DEPLOYMENT") == "1"

    # =========================================================================
    # VALIDATION METHODS
    # =========================================================================

    def is_configured(self, service: str) -> bool:
        """
        Check if a service has all required configuration.

        Args:
            service: Service name (anthropic, sendgrid, twilio, stripe,
                    sendcertified, notarize, experian, identityiq, smartcredit)

        Returns:
            True if all required env vars are set for the service
        """
        checks = {
            "anthropic": lambda: bool(self.ANTHROPIC_API_KEY),
            "gmail": lambda: all([self.GMAIL_USER, self.GMAIL_APP_PASSWORD]),
            "email": lambda: all([self.GMAIL_USER, self.GMAIL_APP_PASSWORD]),  # Alias
            "sendgrid": lambda: all([self.GMAIL_USER, self.GMAIL_APP_PASSWORD]),  # Legacy - now checks Gmail
            "twilio": lambda: all(
                [
                    self.TWILIO_ACCOUNT_SID,
                    self.TWILIO_AUTH_TOKEN,
                    self.TWILIO_PHONE_NUMBER,
                ]
            ),
            "stripe": lambda: bool(self.STRIPE_SECRET_KEY),
            "sendcertified": lambda: all(
                [
                    self.SENDCERTIFIED_SFTP_HOST,
                    self.SENDCERTIFIED_SFTP_USERNAME,
                    self.SENDCERTIFIED_SFTP_PASSWORD,
                ]
            ),
            "notarize": lambda: bool(self.NOTARIZE_API_KEY),
            "experian": lambda: all(
                [
                    self.EXPERIAN_API_KEY,
                    self.EXPERIAN_CLIENT_ID,
                    self.EXPERIAN_CLIENT_SECRET,
                ]
            ),
            "identityiq": lambda: all(
                [self.IDENTITYIQ_API_KEY, self.IDENTITYIQ_API_SECRET]
            ),
            "smartcredit": lambda: bool(self.SMARTCREDIT_API_KEY),
            "database": lambda: bool(self.DATABASE_URL),
            "encryption": lambda: bool(self.ENCRYPTION_KEY),
        }

        check_func = checks.get(service.lower())
        if check_func is None:
            raise ValueError(f"Unknown service: {service}")
        return check_func()

    def validate_required(self, *services: str) -> None:
        """
        Validate that required services are configured.
        Raises ConfigurationError if any are missing.

        Args:
            *services: Service names to validate
        """
        missing = []
        for service in services:
            if not self.is_configured(service):
                missing.append(service)

        if missing:
            raise ConfigurationError(
                f"Missing configuration for: {', '.join(missing)}. "
                f"Please set the required environment variables."
            )

    def get_status(self) -> dict:
        """
        Get configuration status for all services.

        Returns:
            Dict mapping service names to configured status
        """
        services = [
            "anthropic",
            "gmail",
            "twilio",
            "stripe",
            "sendcertified",
            "notarize",
            "experian",
            "identityiq",
            "smartcredit",
            "database",
            "encryption",
        ]
        return {service: self.is_configured(service) for service in services}

    def __repr__(self) -> str:
        status = self.get_status()
        configured = [k for k, v in status.items() if v]
        return f"<Config env={self.ENV} configured={configured}>"


# Singleton instance
config = Config()


# Convenience function for quick access
@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get the configuration singleton."""
    return config
