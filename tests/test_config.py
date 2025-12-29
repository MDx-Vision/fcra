"""
Unit tests for Config Service
Tests for environment variable loading, configuration validation,
service configuration checks, and configuration status reporting.
"""
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.config import Config, ConfigurationError, config, get_config


# ============== Helper to create clean Config instance ==============


def create_clean_config():
    """Create a fresh Config instance for testing."""
    return Config()


# ============== Core Flask Settings Tests ==============


class TestSecretKey:
    """Tests for SECRET_KEY property."""

    def test_secret_key_from_env(self):
        """Test SECRET_KEY is loaded from environment variable."""
        with patch.dict(os.environ, {"FLASK_SECRET_KEY": "test-secret-123"}):
            cfg = create_clean_config()
            assert cfg.SECRET_KEY == "test-secret-123"

    def test_secret_key_auto_generated(self):
        """Test SECRET_KEY is auto-generated when not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove FLASK_SECRET_KEY if present
            env = {k: v for k, v in os.environ.items() if k != "FLASK_SECRET_KEY"}
            with patch.dict(os.environ, env, clear=True):
                cfg = create_clean_config()
                key = cfg.SECRET_KEY
                assert key is not None
                assert len(key) == 64  # 32 bytes hex = 64 chars

    def test_secret_key_generated_is_hex(self):
        """Test auto-generated SECRET_KEY is valid hex."""
        with patch.dict(os.environ, {}, clear=True):
            env = {k: v for k, v in os.environ.items() if k != "FLASK_SECRET_KEY"}
            with patch.dict(os.environ, env, clear=True):
                cfg = create_clean_config()
                key = cfg.SECRET_KEY
                # Should be valid hex string
                int(key, 16)


class TestDebug:
    """Tests for DEBUG property."""

    def test_debug_true_lowercase(self):
        """Test DEBUG is True when FLASK_DEBUG is 'true'."""
        with patch.dict(os.environ, {"FLASK_DEBUG": "true"}):
            cfg = create_clean_config()
            assert cfg.DEBUG is True

    def test_debug_true_uppercase(self):
        """Test DEBUG is True when FLASK_DEBUG is 'True'."""
        with patch.dict(os.environ, {"FLASK_DEBUG": "True"}):
            cfg = create_clean_config()
            assert cfg.DEBUG is True

    def test_debug_true_one(self):
        """Test DEBUG is True when FLASK_DEBUG is '1'."""
        with patch.dict(os.environ, {"FLASK_DEBUG": "1"}):
            cfg = create_clean_config()
            assert cfg.DEBUG is True

    def test_debug_true_yes(self):
        """Test DEBUG is True when FLASK_DEBUG is 'yes'."""
        with patch.dict(os.environ, {"FLASK_DEBUG": "yes"}):
            cfg = create_clean_config()
            assert cfg.DEBUG is True

    def test_debug_false_when_not_set(self):
        """Test DEBUG is False when FLASK_DEBUG is not set."""
        env = {k: v for k, v in os.environ.items() if k != "FLASK_DEBUG"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.DEBUG is False

    def test_debug_false_when_false(self):
        """Test DEBUG is False when FLASK_DEBUG is 'false'."""
        with patch.dict(os.environ, {"FLASK_DEBUG": "false"}):
            cfg = create_clean_config()
            assert cfg.DEBUG is False

    def test_debug_false_for_invalid_value(self):
        """Test DEBUG is False for any invalid value."""
        with patch.dict(os.environ, {"FLASK_DEBUG": "invalid"}):
            cfg = create_clean_config()
            assert cfg.DEBUG is False


class TestEnv:
    """Tests for ENV property."""

    def test_env_from_environment(self):
        """Test ENV is loaded from FLASK_ENV."""
        with patch.dict(os.environ, {"FLASK_ENV": "production"}):
            cfg = create_clean_config()
            assert cfg.ENV == "production"

    def test_env_default_development(self):
        """Test ENV defaults to 'development'."""
        env = {k: v for k, v in os.environ.items() if k != "FLASK_ENV"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.ENV == "development"

    def test_env_testing(self):
        """Test ENV can be 'testing'."""
        with patch.dict(os.environ, {"FLASK_ENV": "testing"}):
            cfg = create_clean_config()
            assert cfg.ENV == "testing"


class TestIsProduction:
    """Tests for IS_PRODUCTION property."""

    def test_is_production_with_production_env(self):
        """Test IS_PRODUCTION is True when ENV is production."""
        with patch.dict(os.environ, {"FLASK_ENV": "production"}):
            cfg = create_clean_config()
            assert cfg.IS_PRODUCTION is True

    def test_is_production_with_replit_deployment(self):
        """Test IS_PRODUCTION is True when REPLIT_DEPLOYMENT is 1."""
        with patch.dict(os.environ, {"FLASK_ENV": "development", "REPLIT_DEPLOYMENT": "1"}):
            cfg = create_clean_config()
            assert cfg.IS_PRODUCTION is True

    def test_is_production_false_in_development(self):
        """Test IS_PRODUCTION is False in development."""
        env = {k: v for k, v in os.environ.items() if k not in ["FLASK_ENV", "REPLIT_DEPLOYMENT"]}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.IS_PRODUCTION is False


class TestIsCI:
    """Tests for IS_CI property."""

    def test_is_ci_true(self):
        """Test IS_CI is True when CI environment variable is 'true'."""
        with patch.dict(os.environ, {"CI": "true"}):
            cfg = create_clean_config()
            assert cfg.IS_CI is True

    def test_is_ci_true_uppercase(self):
        """Test IS_CI is True when CI is 'True'."""
        with patch.dict(os.environ, {"CI": "True"}):
            cfg = create_clean_config()
            assert cfg.IS_CI is True

    def test_is_ci_false_when_not_set(self):
        """Test IS_CI is False when CI is not set."""
        env = {k: v for k, v in os.environ.items() if k != "CI"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.IS_CI is False

    def test_is_ci_false_for_other_values(self):
        """Test IS_CI is False for values other than 'true'."""
        with patch.dict(os.environ, {"CI": "false"}):
            cfg = create_clean_config()
            assert cfg.IS_CI is False


class TestPort:
    """Tests for PORT property."""

    def test_port_from_env(self):
        """Test PORT is loaded from environment."""
        with patch.dict(os.environ, {"PORT": "8080"}):
            cfg = create_clean_config()
            assert cfg.PORT == 8080

    def test_port_default(self):
        """Test PORT defaults to 5000."""
        env = {k: v for k, v in os.environ.items() if k != "PORT"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.PORT == 5000

    def test_port_is_integer(self):
        """Test PORT is returned as integer."""
        with patch.dict(os.environ, {"PORT": "3000"}):
            cfg = create_clean_config()
            assert isinstance(cfg.PORT, int)


# ============== Database Tests ==============


class TestDatabaseUrl:
    """Tests for DATABASE_URL property."""

    def test_database_url_from_env(self):
        """Test DATABASE_URL is loaded from environment."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
            cfg = create_clean_config()
            assert cfg.DATABASE_URL == "postgresql://localhost/test"

    def test_database_url_empty_default(self):
        """Test DATABASE_URL defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.DATABASE_URL == ""


# ============== Logging Tests ==============


class TestLogLevel:
    """Tests for LOG_LEVEL property."""

    def test_log_level_from_env(self):
        """Test LOG_LEVEL is loaded from environment."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            cfg = create_clean_config()
            assert cfg.LOG_LEVEL == "DEBUG"

    def test_log_level_default(self):
        """Test LOG_LEVEL defaults to INFO."""
        env = {k: v for k, v in os.environ.items() if k != "LOG_LEVEL"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.LOG_LEVEL == "INFO"

    def test_log_level_uppercase(self):
        """Test LOG_LEVEL is uppercased."""
        with patch.dict(os.environ, {"LOG_LEVEL": "warning"}):
            cfg = create_clean_config()
            assert cfg.LOG_LEVEL == "WARNING"


# ============== Rate Limiting Tests ==============


class TestRateLimits:
    """Tests for rate limiting properties."""

    def test_rate_limit_default_from_env(self):
        """Test RATE_LIMIT_DEFAULT from environment."""
        with patch.dict(os.environ, {"RATE_LIMIT_DEFAULT": "500 per minute"}):
            cfg = create_clean_config()
            assert cfg.RATE_LIMIT_DEFAULT == "500 per minute"

    def test_rate_limit_default_value(self):
        """Test RATE_LIMIT_DEFAULT default value."""
        env = {k: v for k, v in os.environ.items() if k != "RATE_LIMIT_DEFAULT"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.RATE_LIMIT_DEFAULT == "200 per minute"

    def test_rate_limit_auth_from_env(self):
        """Test RATE_LIMIT_AUTH from environment."""
        with patch.dict(os.environ, {"RATE_LIMIT_AUTH": "10 per minute"}):
            cfg = create_clean_config()
            assert cfg.RATE_LIMIT_AUTH == "10 per minute"

    def test_rate_limit_auth_default_value(self):
        """Test RATE_LIMIT_AUTH default value."""
        env = {k: v for k, v in os.environ.items() if k != "RATE_LIMIT_AUTH"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.RATE_LIMIT_AUTH == "5 per minute"

    def test_rate_limit_api_from_env(self):
        """Test RATE_LIMIT_API from environment."""
        with patch.dict(os.environ, {"RATE_LIMIT_API": "200 per minute"}):
            cfg = create_clean_config()
            assert cfg.RATE_LIMIT_API == "200 per minute"

    def test_rate_limit_api_default_value(self):
        """Test RATE_LIMIT_API default value."""
        env = {k: v for k, v in os.environ.items() if k != "RATE_LIMIT_API"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.RATE_LIMIT_API == "100 per minute"

    def test_rate_limit_analysis_from_env(self):
        """Test RATE_LIMIT_ANALYSIS from environment."""
        with patch.dict(os.environ, {"RATE_LIMIT_ANALYSIS": "20 per minute"}):
            cfg = create_clean_config()
            assert cfg.RATE_LIMIT_ANALYSIS == "20 per minute"

    def test_rate_limit_analysis_default_value(self):
        """Test RATE_LIMIT_ANALYSIS default value."""
        env = {k: v for k, v in os.environ.items() if k != "RATE_LIMIT_ANALYSIS"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.RATE_LIMIT_ANALYSIS == "10 per minute"


# ============== AI / Anthropic Tests ==============


class TestAnthropicApiKey:
    """Tests for ANTHROPIC_API_KEY property."""

    def test_anthropic_api_key_from_env(self):
        """Test ANTHROPIC_API_KEY from environment."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
            cfg = create_clean_config()
            assert cfg.ANTHROPIC_API_KEY == "sk-ant-test123"

    def test_anthropic_api_key_fallback(self):
        """Test ANTHROPIC_API_KEY falls back to FCRA Automation Secure."""
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}
        env["FCRA Automation Secure"] = "fallback-key"
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.ANTHROPIC_API_KEY == "fallback-key"

    def test_anthropic_api_key_empty_default(self):
        """Test ANTHROPIC_API_KEY defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k not in ["ANTHROPIC_API_KEY", "FCRA Automation Secure"]}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.ANTHROPIC_API_KEY == ""


# ============== Email (SendGrid) Tests ==============


class TestSendGridConfig:
    """Tests for SendGrid configuration properties."""

    def test_sendgrid_api_key_from_env(self):
        """Test SENDGRID_API_KEY from environment."""
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.test123"}):
            cfg = create_clean_config()
            assert cfg.SENDGRID_API_KEY == "SG.test123"

    def test_sendgrid_api_key_empty_default(self):
        """Test SENDGRID_API_KEY defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "SENDGRID_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.SENDGRID_API_KEY == ""

    def test_sendgrid_from_email_from_env(self):
        """Test SENDGRID_FROM_EMAIL from environment."""
        with patch.dict(os.environ, {"SENDGRID_FROM_EMAIL": "test@custom.com"}):
            cfg = create_clean_config()
            assert cfg.SENDGRID_FROM_EMAIL == "test@custom.com"

    def test_sendgrid_from_email_default(self):
        """Test SENDGRID_FROM_EMAIL default value."""
        env = {k: v for k, v in os.environ.items() if k != "SENDGRID_FROM_EMAIL"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.SENDGRID_FROM_EMAIL == "noreply@fcra-platform.com"

    def test_sendgrid_from_name_from_env(self):
        """Test SENDGRID_FROM_NAME from environment."""
        with patch.dict(os.environ, {"SENDGRID_FROM_NAME": "Custom Name"}):
            cfg = create_clean_config()
            assert cfg.SENDGRID_FROM_NAME == "Custom Name"

    def test_sendgrid_from_name_default(self):
        """Test SENDGRID_FROM_NAME default value."""
        env = {k: v for k, v in os.environ.items() if k != "SENDGRID_FROM_NAME"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.SENDGRID_FROM_NAME == "FCRA Litigation Platform"


# ============== SMS (Twilio) Tests ==============


class TestTwilioConfig:
    """Tests for Twilio configuration properties."""

    def test_twilio_account_sid_from_env(self):
        """Test TWILIO_ACCOUNT_SID from environment."""
        with patch.dict(os.environ, {"TWILIO_ACCOUNT_SID": "AC123456"}):
            cfg = create_clean_config()
            assert cfg.TWILIO_ACCOUNT_SID == "AC123456"

    def test_twilio_account_sid_empty_default(self):
        """Test TWILIO_ACCOUNT_SID defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "TWILIO_ACCOUNT_SID"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.TWILIO_ACCOUNT_SID == ""

    def test_twilio_auth_token_from_env(self):
        """Test TWILIO_AUTH_TOKEN from environment."""
        with patch.dict(os.environ, {"TWILIO_AUTH_TOKEN": "auth-token-123"}):
            cfg = create_clean_config()
            assert cfg.TWILIO_AUTH_TOKEN == "auth-token-123"

    def test_twilio_auth_token_empty_default(self):
        """Test TWILIO_AUTH_TOKEN defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "TWILIO_AUTH_TOKEN"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.TWILIO_AUTH_TOKEN == ""

    def test_twilio_phone_number_from_env(self):
        """Test TWILIO_PHONE_NUMBER from environment."""
        with patch.dict(os.environ, {"TWILIO_PHONE_NUMBER": "+15551234567"}):
            cfg = create_clean_config()
            assert cfg.TWILIO_PHONE_NUMBER == "+15551234567"

    def test_twilio_phone_number_empty_default(self):
        """Test TWILIO_PHONE_NUMBER defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "TWILIO_PHONE_NUMBER"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.TWILIO_PHONE_NUMBER == ""


# ============== Payments (Stripe) Tests ==============


class TestStripeConfig:
    """Tests for Stripe configuration properties."""

    def test_stripe_secret_key_from_env(self):
        """Test STRIPE_SECRET_KEY from environment."""
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test_123"}):
            cfg = create_clean_config()
            assert cfg.STRIPE_SECRET_KEY == "sk_test_123"

    def test_stripe_secret_key_empty_default(self):
        """Test STRIPE_SECRET_KEY defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "STRIPE_SECRET_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.STRIPE_SECRET_KEY == ""

    def test_stripe_webhook_secret_from_env(self):
        """Test STRIPE_WEBHOOK_SECRET from environment."""
        with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test123"}):
            cfg = create_clean_config()
            assert cfg.STRIPE_WEBHOOK_SECRET == "whsec_test123"

    def test_stripe_webhook_secret_empty_default(self):
        """Test STRIPE_WEBHOOK_SECRET defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "STRIPE_WEBHOOK_SECRET"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.STRIPE_WEBHOOK_SECRET == ""


# ============== Certified Mail (SendCertified) Tests ==============


class TestSendCertifiedConfig:
    """Tests for SendCertified configuration properties."""

    def test_sendcertified_api_key_from_env(self):
        """Test SENDCERTIFIED_API_KEY from environment."""
        with patch.dict(os.environ, {"SENDCERTIFIEDMAIL_API_KEY": "cert-key-123"}):
            cfg = create_clean_config()
            assert cfg.SENDCERTIFIED_API_KEY == "cert-key-123"

    def test_sendcertified_api_key_empty_default(self):
        """Test SENDCERTIFIED_API_KEY defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "SENDCERTIFIEDMAIL_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.SENDCERTIFIED_API_KEY == ""

    def test_sendcertified_sftp_host_from_env(self):
        """Test SENDCERTIFIED_SFTP_HOST from environment."""
        with patch.dict(os.environ, {"SENDCERTIFIED_SFTP_HOST": "sftp.certified.com"}):
            cfg = create_clean_config()
            assert cfg.SENDCERTIFIED_SFTP_HOST == "sftp.certified.com"

    def test_sendcertified_sftp_username_from_env(self):
        """Test SENDCERTIFIED_SFTP_USERNAME from environment."""
        with patch.dict(os.environ, {"SENDCERTIFIED_SFTP_USERNAME": "sftpuser"}):
            cfg = create_clean_config()
            assert cfg.SENDCERTIFIED_SFTP_USERNAME == "sftpuser"

    def test_sendcertified_sftp_password_from_env(self):
        """Test SENDCERTIFIED_SFTP_PASSWORD from environment."""
        with patch.dict(os.environ, {"SENDCERTIFIED_SFTP_PASSWORD": "sftppass"}):
            cfg = create_clean_config()
            assert cfg.SENDCERTIFIED_SFTP_PASSWORD == "sftppass"

    def test_sendcertified_sftp_port_from_env(self):
        """Test SENDCERTIFIED_SFTP_PORT from environment."""
        with patch.dict(os.environ, {"SENDCERTIFIED_SFTP_PORT": "2222"}):
            cfg = create_clean_config()
            assert cfg.SENDCERTIFIED_SFTP_PORT == 2222

    def test_sendcertified_sftp_port_default(self):
        """Test SENDCERTIFIED_SFTP_PORT defaults to 22."""
        env = {k: v for k, v in os.environ.items() if k != "SENDCERTIFIED_SFTP_PORT"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.SENDCERTIFIED_SFTP_PORT == 22

    def test_sendcertified_sftp_port_is_integer(self):
        """Test SENDCERTIFIED_SFTP_PORT is returned as integer."""
        with patch.dict(os.environ, {"SENDCERTIFIED_SFTP_PORT": "22"}):
            cfg = create_clean_config()
            assert isinstance(cfg.SENDCERTIFIED_SFTP_PORT, int)


# ============== Credit Monitoring Services Tests ==============


class TestCreditMonitoringConfig:
    """Tests for credit monitoring service configuration properties."""

    def test_smartcredit_api_key_from_env(self):
        """Test SMARTCREDIT_API_KEY from environment."""
        with patch.dict(os.environ, {"SMARTCREDIT_API_KEY": "smart-key-123"}):
            cfg = create_clean_config()
            assert cfg.SMARTCREDIT_API_KEY == "smart-key-123"

    def test_smartcredit_api_key_empty_default(self):
        """Test SMARTCREDIT_API_KEY defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "SMARTCREDIT_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.SMARTCREDIT_API_KEY == ""

    def test_identityiq_api_key_from_env(self):
        """Test IDENTITYIQ_API_KEY from environment."""
        with patch.dict(os.environ, {"IDENTITYIQ_API_KEY": "iiq-key-123"}):
            cfg = create_clean_config()
            assert cfg.IDENTITYIQ_API_KEY == "iiq-key-123"

    def test_identityiq_api_secret_from_env(self):
        """Test IDENTITYIQ_API_SECRET from environment."""
        with patch.dict(os.environ, {"IDENTITYIQ_API_SECRET": "iiq-secret-123"}):
            cfg = create_clean_config()
            assert cfg.IDENTITYIQ_API_SECRET == "iiq-secret-123"

    def test_experian_api_key_from_env(self):
        """Test EXPERIAN_API_KEY from environment."""
        with patch.dict(os.environ, {"EXPERIAN_API_KEY": "exp-key-123"}):
            cfg = create_clean_config()
            assert cfg.EXPERIAN_API_KEY == "exp-key-123"

    def test_experian_client_id_from_env(self):
        """Test EXPERIAN_CLIENT_ID from environment."""
        with patch.dict(os.environ, {"EXPERIAN_CLIENT_ID": "exp-client-123"}):
            cfg = create_clean_config()
            assert cfg.EXPERIAN_CLIENT_ID == "exp-client-123"

    def test_experian_client_secret_from_env(self):
        """Test EXPERIAN_CLIENT_SECRET from environment."""
        with patch.dict(os.environ, {"EXPERIAN_CLIENT_SECRET": "exp-secret-123"}):
            cfg = create_clean_config()
            assert cfg.EXPERIAN_CLIENT_SECRET == "exp-secret-123"

    def test_experian_subscriber_code_from_env(self):
        """Test EXPERIAN_SUBSCRIBER_CODE from environment."""
        with patch.dict(os.environ, {"EXPERIAN_SUBSCRIBER_CODE": "SUB123"}):
            cfg = create_clean_config()
            assert cfg.EXPERIAN_SUBSCRIBER_CODE == "SUB123"


# ============== Notarization Tests ==============


class TestNotarizeConfig:
    """Tests for Notarize configuration properties."""

    def test_notarize_api_key_from_env(self):
        """Test NOTARIZE_API_KEY from environment."""
        with patch.dict(os.environ, {"NOTARIZE_API_KEY": "notarize-key-123"}):
            cfg = create_clean_config()
            assert cfg.NOTARIZE_API_KEY == "notarize-key-123"

    def test_notarize_api_key_fallback_to_proof(self):
        """Test NOTARIZE_API_KEY falls back to PROOF_API_KEY."""
        env = {k: v for k, v in os.environ.items() if k != "NOTARIZE_API_KEY"}
        env["PROOF_API_KEY"] = "proof-key-123"
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.NOTARIZE_API_KEY == "proof-key-123"

    def test_notarize_api_key_empty_default(self):
        """Test NOTARIZE_API_KEY defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k not in ["NOTARIZE_API_KEY", "PROOF_API_KEY"]}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.NOTARIZE_API_KEY == ""

    def test_notarize_webhook_secret_from_env(self):
        """Test NOTARIZE_WEBHOOK_SECRET from environment."""
        with patch.dict(os.environ, {"NOTARIZE_WEBHOOK_SECRET": "webhook-secret-123"}):
            cfg = create_clean_config()
            assert cfg.NOTARIZE_WEBHOOK_SECRET == "webhook-secret-123"

    def test_notarize_sandbox_true_by_default(self):
        """Test NOTARIZE_SANDBOX defaults to True."""
        env = {k: v for k, v in os.environ.items() if k != "NOTARIZE_SANDBOX"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.NOTARIZE_SANDBOX is True

    def test_notarize_sandbox_false(self):
        """Test NOTARIZE_SANDBOX can be set to False."""
        with patch.dict(os.environ, {"NOTARIZE_SANDBOX": "false"}):
            cfg = create_clean_config()
            assert cfg.NOTARIZE_SANDBOX is False

    def test_notarize_sandbox_true_with_yes(self):
        """Test NOTARIZE_SANDBOX is True with 'yes'."""
        with patch.dict(os.environ, {"NOTARIZE_SANDBOX": "yes"}):
            cfg = create_clean_config()
            assert cfg.NOTARIZE_SANDBOX is True

    def test_notarize_sandbox_true_with_one(self):
        """Test NOTARIZE_SANDBOX is True with '1'."""
        with patch.dict(os.environ, {"NOTARIZE_SANDBOX": "1"}):
            cfg = create_clean_config()
            assert cfg.NOTARIZE_SANDBOX is True


# ============== Security Tests ==============


class TestSecurityConfig:
    """Tests for security configuration properties."""

    def test_encryption_key_from_env(self):
        """Test ENCRYPTION_KEY from environment."""
        with patch.dict(os.environ, {"FCRA_ENCRYPTION_KEY": "encryption-key-123"}):
            cfg = create_clean_config()
            assert cfg.ENCRYPTION_KEY == "encryption-key-123"

    def test_encryption_key_empty_default(self):
        """Test ENCRYPTION_KEY defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "FCRA_ENCRYPTION_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.ENCRYPTION_KEY == ""


# ============== Replit-Specific Tests ==============


class TestReplitConfig:
    """Tests for Replit-specific configuration properties."""

    def test_replit_dev_domain_from_env(self):
        """Test REPLIT_DEV_DOMAIN from environment."""
        with patch.dict(os.environ, {"REPLIT_DEV_DOMAIN": "test.replit.dev"}):
            cfg = create_clean_config()
            assert cfg.REPLIT_DEV_DOMAIN == "test.replit.dev"

    def test_replit_dev_domain_empty_default(self):
        """Test REPLIT_DEV_DOMAIN defaults to empty string."""
        env = {k: v for k, v in os.environ.items() if k != "REPLIT_DEV_DOMAIN"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.REPLIT_DEV_DOMAIN == ""

    def test_replit_deployment_true(self):
        """Test REPLIT_DEPLOYMENT is True when set to '1'."""
        with patch.dict(os.environ, {"REPLIT_DEPLOYMENT": "1"}):
            cfg = create_clean_config()
            assert cfg.REPLIT_DEPLOYMENT is True

    def test_replit_deployment_false(self):
        """Test REPLIT_DEPLOYMENT is False when not '1'."""
        with patch.dict(os.environ, {"REPLIT_DEPLOYMENT": "0"}):
            cfg = create_clean_config()
            assert cfg.REPLIT_DEPLOYMENT is False

    def test_replit_deployment_false_when_not_set(self):
        """Test REPLIT_DEPLOYMENT is False when not set."""
        env = {k: v for k, v in os.environ.items() if k != "REPLIT_DEPLOYMENT"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.REPLIT_DEPLOYMENT is False


# ============== is_configured Tests ==============


class TestIsConfigured:
    """Tests for is_configured method."""

    def test_is_configured_anthropic_true(self):
        """Test is_configured returns True for anthropic when key is set."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            cfg = create_clean_config()
            assert cfg.is_configured("anthropic") is True

    def test_is_configured_anthropic_false(self):
        """Test is_configured returns False for anthropic when key is not set."""
        env = {k: v for k, v in os.environ.items() if k not in ["ANTHROPIC_API_KEY", "FCRA Automation Secure"]}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("anthropic") is False

    def test_is_configured_sendgrid_true(self):
        """Test is_configured returns True for sendgrid when key is set."""
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.test"}):
            cfg = create_clean_config()
            assert cfg.is_configured("sendgrid") is True

    def test_is_configured_sendgrid_false(self):
        """Test is_configured returns False for sendgrid when key is not set."""
        env = {k: v for k, v in os.environ.items() if k != "SENDGRID_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("sendgrid") is False

    def test_is_configured_twilio_true(self):
        """Test is_configured returns True for twilio when all keys are set."""
        with patch.dict(os.environ, {
            "TWILIO_ACCOUNT_SID": "AC123",
            "TWILIO_AUTH_TOKEN": "token123",
            "TWILIO_PHONE_NUMBER": "+15551234567"
        }):
            cfg = create_clean_config()
            assert cfg.is_configured("twilio") is True

    def test_is_configured_twilio_false_missing_sid(self):
        """Test is_configured returns False for twilio when SID is missing."""
        env = {k: v for k, v in os.environ.items() if k != "TWILIO_ACCOUNT_SID"}
        env["TWILIO_AUTH_TOKEN"] = "token"
        env["TWILIO_PHONE_NUMBER"] = "+15551234567"
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("twilio") is False

    def test_is_configured_twilio_false_missing_token(self):
        """Test is_configured returns False for twilio when token is missing."""
        env = {k: v for k, v in os.environ.items() if k != "TWILIO_AUTH_TOKEN"}
        env["TWILIO_ACCOUNT_SID"] = "AC123"
        env["TWILIO_PHONE_NUMBER"] = "+15551234567"
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("twilio") is False

    def test_is_configured_twilio_false_missing_phone(self):
        """Test is_configured returns False for twilio when phone is missing."""
        env = {k: v for k, v in os.environ.items() if k != "TWILIO_PHONE_NUMBER"}
        env["TWILIO_ACCOUNT_SID"] = "AC123"
        env["TWILIO_AUTH_TOKEN"] = "token"
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("twilio") is False

    def test_is_configured_stripe_true(self):
        """Test is_configured returns True for stripe when key is set."""
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test_123"}):
            cfg = create_clean_config()
            assert cfg.is_configured("stripe") is True

    def test_is_configured_stripe_false(self):
        """Test is_configured returns False for stripe when key is not set."""
        env = {k: v for k, v in os.environ.items() if k != "STRIPE_SECRET_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("stripe") is False

    def test_is_configured_sendcertified_true(self):
        """Test is_configured returns True for sendcertified when all keys are set."""
        with patch.dict(os.environ, {
            "SENDCERTIFIED_SFTP_HOST": "sftp.test.com",
            "SENDCERTIFIED_SFTP_USERNAME": "user",
            "SENDCERTIFIED_SFTP_PASSWORD": "pass"
        }):
            cfg = create_clean_config()
            assert cfg.is_configured("sendcertified") is True

    def test_is_configured_sendcertified_false(self):
        """Test is_configured returns False for sendcertified when keys are missing."""
        env = {k: v for k, v in os.environ.items() if not k.startswith("SENDCERTIFIED_SFTP")}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("sendcertified") is False

    def test_is_configured_notarize_true(self):
        """Test is_configured returns True for notarize when key is set."""
        with patch.dict(os.environ, {"NOTARIZE_API_KEY": "notarize-key"}):
            cfg = create_clean_config()
            assert cfg.is_configured("notarize") is True

    def test_is_configured_notarize_false(self):
        """Test is_configured returns False for notarize when key is not set."""
        env = {k: v for k, v in os.environ.items() if k not in ["NOTARIZE_API_KEY", "PROOF_API_KEY"]}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("notarize") is False

    def test_is_configured_experian_true(self):
        """Test is_configured returns True for experian when all keys are set."""
        with patch.dict(os.environ, {
            "EXPERIAN_API_KEY": "exp-key",
            "EXPERIAN_CLIENT_ID": "exp-id",
            "EXPERIAN_CLIENT_SECRET": "exp-secret"
        }):
            cfg = create_clean_config()
            assert cfg.is_configured("experian") is True

    def test_is_configured_experian_false(self):
        """Test is_configured returns False for experian when keys are missing."""
        env = {k: v for k, v in os.environ.items() if not k.startswith("EXPERIAN")}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("experian") is False

    def test_is_configured_identityiq_true(self):
        """Test is_configured returns True for identityiq when all keys are set."""
        with patch.dict(os.environ, {
            "IDENTITYIQ_API_KEY": "iiq-key",
            "IDENTITYIQ_API_SECRET": "iiq-secret"
        }):
            cfg = create_clean_config()
            assert cfg.is_configured("identityiq") is True

    def test_is_configured_identityiq_false(self):
        """Test is_configured returns False for identityiq when keys are missing."""
        env = {k: v for k, v in os.environ.items() if not k.startswith("IDENTITYIQ")}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("identityiq") is False

    def test_is_configured_smartcredit_true(self):
        """Test is_configured returns True for smartcredit when key is set."""
        with patch.dict(os.environ, {"SMARTCREDIT_API_KEY": "smart-key"}):
            cfg = create_clean_config()
            assert cfg.is_configured("smartcredit") is True

    def test_is_configured_smartcredit_false(self):
        """Test is_configured returns False for smartcredit when key is not set."""
        env = {k: v for k, v in os.environ.items() if k != "SMARTCREDIT_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("smartcredit") is False

    def test_is_configured_database_true(self):
        """Test is_configured returns True for database when URL is set."""
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://localhost/test"}):
            cfg = create_clean_config()
            assert cfg.is_configured("database") is True

    def test_is_configured_database_false(self):
        """Test is_configured returns False for database when URL is not set."""
        env = {k: v for k, v in os.environ.items() if k != "DATABASE_URL"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("database") is False

    def test_is_configured_encryption_true(self):
        """Test is_configured returns True for encryption when key is set."""
        with patch.dict(os.environ, {"FCRA_ENCRYPTION_KEY": "encryption-key"}):
            cfg = create_clean_config()
            assert cfg.is_configured("encryption") is True

    def test_is_configured_encryption_false(self):
        """Test is_configured returns False for encryption when key is not set."""
        env = {k: v for k, v in os.environ.items() if k != "FCRA_ENCRYPTION_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("encryption") is False

    def test_is_configured_unknown_service_raises(self):
        """Test is_configured raises ValueError for unknown service."""
        cfg = create_clean_config()
        with pytest.raises(ValueError) as exc_info:
            cfg.is_configured("unknown_service")
        assert "Unknown service" in str(exc_info.value)
        assert "unknown_service" in str(exc_info.value)

    def test_is_configured_case_insensitive(self):
        """Test is_configured is case-insensitive."""
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.test"}):
            cfg = create_clean_config()
            assert cfg.is_configured("SENDGRID") is True
            assert cfg.is_configured("SendGrid") is True
            assert cfg.is_configured("sendgrid") is True


# ============== validate_required Tests ==============


class TestValidateRequired:
    """Tests for validate_required method."""

    def test_validate_required_passes_when_configured(self):
        """Test validate_required passes when all services are configured."""
        with patch.dict(os.environ, {
            "SENDGRID_API_KEY": "SG.test",
            "STRIPE_SECRET_KEY": "sk_test"
        }):
            cfg = create_clean_config()
            # Should not raise
            cfg.validate_required("sendgrid", "stripe")

    def test_validate_required_raises_when_missing(self):
        """Test validate_required raises ConfigurationError when service is missing."""
        env = {k: v for k, v in os.environ.items() if k != "SENDGRID_API_KEY"}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            with pytest.raises(ConfigurationError) as exc_info:
                cfg.validate_required("sendgrid")
            assert "sendgrid" in str(exc_info.value)
            assert "Missing configuration" in str(exc_info.value)

    def test_validate_required_lists_all_missing(self):
        """Test validate_required lists all missing services."""
        env = {k: v for k, v in os.environ.items() if k not in ["SENDGRID_API_KEY", "STRIPE_SECRET_KEY"]}
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            with pytest.raises(ConfigurationError) as exc_info:
                cfg.validate_required("sendgrid", "stripe")
            error_message = str(exc_info.value)
            assert "sendgrid" in error_message
            assert "stripe" in error_message

    def test_validate_required_partial_configuration(self):
        """Test validate_required with some services configured."""
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.test"}):
            env = {k: v for k, v in os.environ.items() if k != "STRIPE_SECRET_KEY"}
            env["SENDGRID_API_KEY"] = "SG.test"
            with patch.dict(os.environ, env, clear=True):
                cfg = create_clean_config()
                with pytest.raises(ConfigurationError) as exc_info:
                    cfg.validate_required("sendgrid", "stripe")
                error_message = str(exc_info.value)
                assert "stripe" in error_message
                assert "sendgrid" not in error_message

    def test_validate_required_no_services(self):
        """Test validate_required with no services passes."""
        cfg = create_clean_config()
        # Should not raise
        cfg.validate_required()


# ============== get_status Tests ==============


class TestGetStatus:
    """Tests for get_status method."""

    def test_get_status_returns_dict(self):
        """Test get_status returns a dictionary."""
        cfg = create_clean_config()
        status = cfg.get_status()
        assert isinstance(status, dict)

    def test_get_status_contains_all_services(self):
        """Test get_status includes all expected services."""
        cfg = create_clean_config()
        status = cfg.get_status()
        expected_services = [
            "anthropic", "sendgrid", "twilio", "stripe", "sendcertified",
            "notarize", "experian", "identityiq", "smartcredit",
            "database", "encryption"
        ]
        for service in expected_services:
            assert service in status

    def test_get_status_values_are_boolean(self):
        """Test get_status values are all booleans."""
        cfg = create_clean_config()
        status = cfg.get_status()
        for service, is_configured in status.items():
            assert isinstance(is_configured, bool), f"{service} should be boolean"

    def test_get_status_reflects_configuration(self):
        """Test get_status reflects actual configuration state."""
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.test"}):
            env = {k: v for k, v in os.environ.items() if k != "STRIPE_SECRET_KEY"}
            env["SENDGRID_API_KEY"] = "SG.test"
            with patch.dict(os.environ, env, clear=True):
                cfg = create_clean_config()
                status = cfg.get_status()
                assert status["sendgrid"] is True
                assert status["stripe"] is False


# ============== __repr__ Tests ==============


class TestRepr:
    """Tests for __repr__ method."""

    def test_repr_contains_env(self):
        """Test __repr__ contains environment information."""
        with patch.dict(os.environ, {"FLASK_ENV": "testing"}):
            cfg = create_clean_config()
            repr_str = repr(cfg)
            assert "testing" in repr_str

    def test_repr_contains_configured_services(self):
        """Test __repr__ contains configured services."""
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "SG.test"}):
            cfg = create_clean_config()
            repr_str = repr(cfg)
            assert "sendgrid" in repr_str

    def test_repr_format(self):
        """Test __repr__ has expected format."""
        cfg = create_clean_config()
        repr_str = repr(cfg)
        assert repr_str.startswith("<Config")
        assert "env=" in repr_str
        assert "configured=" in repr_str


# ============== Singleton Tests ==============


class TestConfigSingleton:
    """Tests for config singleton instance."""

    def test_config_is_instance_of_config_class(self):
        """Test config is an instance of Config."""
        assert isinstance(config, Config)

    def test_get_config_returns_singleton(self):
        """Test get_config returns the singleton instance."""
        result = get_config()
        assert result is config

    def test_get_config_cached(self):
        """Test get_config uses LRU cache."""
        result1 = get_config()
        result2 = get_config()
        assert result1 is result2


# ============== ConfigurationError Tests ==============


class TestConfigurationError:
    """Tests for ConfigurationError exception."""

    def test_configuration_error_is_exception(self):
        """Test ConfigurationError is an Exception."""
        assert issubclass(ConfigurationError, Exception)

    def test_configuration_error_message(self):
        """Test ConfigurationError stores message."""
        error = ConfigurationError("Missing API key")
        assert str(error) == "Missing API key"

    def test_configuration_error_can_be_raised(self):
        """Test ConfigurationError can be raised and caught."""
        with pytest.raises(ConfigurationError):
            raise ConfigurationError("Test error")


# ============== Edge Cases Tests ==============


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_string_env_var_treated_as_unset(self):
        """Test empty string environment variables are treated as unset for boolean checks."""
        env = {k: v for k, v in os.environ.items() if k not in ["ANTHROPIC_API_KEY", "FCRA Automation Secure"]}
        env["ANTHROPIC_API_KEY"] = ""
        with patch.dict(os.environ, env, clear=True):
            cfg = create_clean_config()
            assert cfg.is_configured("anthropic") is False

    def test_whitespace_env_var(self):
        """Test whitespace-only environment variables."""
        with patch.dict(os.environ, {"SENDGRID_API_KEY": "   "}):
            cfg = create_clean_config()
            # Whitespace is truthy, so this should be True
            assert cfg.is_configured("sendgrid") is True

    def test_special_characters_in_env_var(self):
        """Test environment variables with special characters."""
        special_key = "sk-test!@#$%^&*()_+-=[]{}|;:',.<>?"
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": special_key}):
            cfg = create_clean_config()
            assert cfg.STRIPE_SECRET_KEY == special_key

    def test_unicode_in_env_var(self):
        """Test environment variables with unicode characters."""
        unicode_value = "test-\u00e9\u00e8\u00ea"
        with patch.dict(os.environ, {"SENDGRID_FROM_NAME": unicode_value}):
            cfg = create_clean_config()
            assert cfg.SENDGRID_FROM_NAME == unicode_value

    def test_very_long_env_var(self):
        """Test environment variables with very long values."""
        long_value = "x" * 10000
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": long_value}):
            cfg = create_clean_config()
            assert cfg.ANTHROPIC_API_KEY == long_value

    def test_port_invalid_value(self):
        """Test PORT with invalid (non-integer) value raises error."""
        with patch.dict(os.environ, {"PORT": "invalid"}):
            cfg = create_clean_config()
            with pytest.raises(ValueError):
                _ = cfg.PORT

    def test_sftp_port_invalid_value(self):
        """Test SENDCERTIFIED_SFTP_PORT with invalid value raises error."""
        with patch.dict(os.environ, {"SENDCERTIFIED_SFTP_PORT": "invalid"}):
            cfg = create_clean_config()
            with pytest.raises(ValueError):
                _ = cfg.SENDCERTIFIED_SFTP_PORT

    def test_multiple_config_instances_independent(self):
        """Test multiple Config instances read environment independently."""
        with patch.dict(os.environ, {"FLASK_ENV": "test1"}):
            cfg1 = create_clean_config()
            assert cfg1.ENV == "test1"

        with patch.dict(os.environ, {"FLASK_ENV": "test2"}):
            cfg2 = create_clean_config()
            assert cfg2.ENV == "test2"

    def test_config_properties_are_dynamic(self):
        """Test config properties read environment dynamically."""
        cfg = create_clean_config()

        with patch.dict(os.environ, {"FLASK_ENV": "production"}):
            assert cfg.ENV == "production"

        with patch.dict(os.environ, {"FLASK_ENV": "development"}):
            assert cfg.ENV == "development"
