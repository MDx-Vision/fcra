"""
Unit tests for TwoFactorService.

Tests cover:
- TOTP generation and verification
- QR code generation
- Backup code generation and verification
- Device trust management
- Staff 2FA setup and verification
"""

import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

# Set CI environment for testing
os.environ["CI"] = "true"
os.environ["TESTING"] = "true"

from services.two_factor_service import (
    TwoFactorService,
    get_two_factor_service,
    BACKUP_CODE_COUNT,
    BACKUP_CODE_LENGTH,
    DEVICE_TRUST_DAYS,
    ISSUER_NAME,
)


class TestTwoFactorServiceInit:
    """Tests for TwoFactorService initialization."""

    def test_init_without_db(self):
        """Test service initializes without database."""
        service = TwoFactorService()
        assert service.db is None

    def test_init_with_db(self):
        """Test service initializes with database session."""
        mock_db = MagicMock()
        service = TwoFactorService(mock_db)
        assert service.db == mock_db

    def test_get_two_factor_service_singleton(self):
        """Test singleton pattern for service."""
        service1 = get_two_factor_service()
        service2 = get_two_factor_service()
        assert service1 is not None
        assert service2 is not None


class TestTOTPGeneration:
    """Tests for TOTP secret and code generation."""

    def test_generate_secret(self):
        """Test TOTP secret generation."""
        service = TwoFactorService()
        secret = service.generate_secret()

        assert secret is not None
        assert len(secret) == 32  # Base32 encoded
        assert secret.isalnum()

    def test_generate_secret_unique(self):
        """Test that generated secrets are unique."""
        service = TwoFactorService()
        secrets = [service.generate_secret() for _ in range(100)]

        assert len(set(secrets)) == 100  # All unique

    def test_encrypt_decrypt_secret(self):
        """Test secret encryption and decryption."""
        service = TwoFactorService()
        original_secret = service.generate_secret()

        encrypted = service.encrypt_secret(original_secret)
        decrypted = service.decrypt_secret(encrypted)

        assert encrypted != original_secret
        assert decrypted == original_secret

    def test_generate_current_code(self):
        """Test TOTP code generation."""
        service = TwoFactorService()
        secret = service.generate_secret()

        code = service.generate_current_code(secret)

        assert code is not None
        assert len(code) == 6
        assert code.isdigit()

    def test_verify_totp_valid_code(self):
        """Test TOTP verification with valid code."""
        service = TwoFactorService()
        secret = service.generate_secret()
        code = service.generate_current_code(secret)

        assert service.verify_totp(secret, code) is True

    def test_verify_totp_invalid_code(self):
        """Test TOTP verification with invalid code."""
        service = TwoFactorService()
        secret = service.generate_secret()

        assert service.verify_totp(secret, "000000") is False
        assert service.verify_totp(secret, "999999") is False

    def test_verify_totp_wrong_length(self):
        """Test TOTP verification with wrong length codes."""
        service = TwoFactorService()
        secret = service.generate_secret()

        assert service.verify_totp(secret, "12345") is False
        assert service.verify_totp(secret, "1234567") is False
        assert service.verify_totp(secret, "") is False

    def test_verify_totp_non_numeric(self):
        """Test TOTP verification with non-numeric input."""
        service = TwoFactorService()
        secret = service.generate_secret()

        assert service.verify_totp(secret, "abcdef") is False
        assert service.verify_totp(secret, "12345a") is False

    def test_verify_totp_with_spaces(self):
        """Test TOTP verification strips spaces."""
        service = TwoFactorService()
        secret = service.generate_secret()
        code = service.generate_current_code(secret)

        # Add spaces
        spaced_code = f"{code[:3]} {code[3:]}"
        assert service.verify_totp(secret, spaced_code) is True

    def test_verify_totp_with_dashes(self):
        """Test TOTP verification strips dashes."""
        service = TwoFactorService()
        secret = service.generate_secret()
        code = service.generate_current_code(secret)

        # Add dashes
        dashed_code = f"{code[:3]}-{code[3:]}"
        assert service.verify_totp(secret, dashed_code) is True

    def test_verify_totp_empty_secret(self):
        """Test TOTP verification with empty secret."""
        service = TwoFactorService()

        assert service.verify_totp("", "123456") is False
        assert service.verify_totp(None, "123456") is False


class TestQRCodeGeneration:
    """Tests for QR code generation."""

    def test_get_provisioning_uri(self):
        """Test provisioning URI generation."""
        service = TwoFactorService()
        secret = service.generate_secret()
        email = "test@example.com"

        uri = service.get_provisioning_uri(secret, email)

        assert uri.startswith("otpauth://totp/")
        # Email is URL-encoded (@ becomes %40)
        assert email.replace("@", "%40") in uri
        assert ISSUER_NAME.replace(" ", "%20") in uri
        assert "secret=" in uri

    def test_get_provisioning_uri_custom_issuer(self):
        """Test provisioning URI with custom issuer."""
        service = TwoFactorService()
        secret = service.generate_secret()
        email = "test@example.com"
        custom_issuer = "My Custom App"

        uri = service.get_provisioning_uri(secret, email, custom_issuer)

        assert custom_issuer.replace(" ", "%20") in uri

    def test_generate_qr_code(self):
        """Test QR code image generation."""
        service = TwoFactorService()
        secret = service.generate_secret()
        email = "test@example.com"

        qr_base64 = service.generate_qr_code(secret, email)

        assert qr_base64 is not None
        assert len(qr_base64) > 100  # Base64 PNG should be substantial
        # Verify it's valid base64 by decoding
        import base64
        decoded = base64.b64decode(qr_base64)
        assert decoded[:8] == b'\x89PNG\r\n\x1a\n'  # PNG header


class TestBackupCodes:
    """Tests for backup code generation and verification."""

    def test_generate_backup_codes_count(self):
        """Test backup codes generation returns correct count."""
        service = TwoFactorService()
        plain_codes, hashed_codes = service.generate_backup_codes()

        assert len(plain_codes) == BACKUP_CODE_COUNT
        assert len(hashed_codes) == BACKUP_CODE_COUNT

    def test_generate_backup_codes_format(self):
        """Test backup code format (XXXX-XXXX)."""
        service = TwoFactorService()
        plain_codes, _ = service.generate_backup_codes()

        for code in plain_codes:
            assert len(code) == 9  # 8 chars + 1 dash
            assert code[4] == "-"
            assert code[:4].isalnum()
            assert code[5:].isalnum()

    def test_generate_backup_codes_unique(self):
        """Test backup codes are unique."""
        service = TwoFactorService()
        plain_codes, _ = service.generate_backup_codes()

        assert len(set(plain_codes)) == len(plain_codes)

    def test_backup_codes_hashed_different(self):
        """Test hashed codes are different from plain codes."""
        service = TwoFactorService()
        plain_codes, hashed_codes = service.generate_backup_codes()

        for plain, hashed in zip(plain_codes, hashed_codes):
            assert plain != hashed
            assert len(hashed) == 64  # SHA256 hex

    def test_verify_backup_code_valid(self):
        """Test backup code verification with valid code."""
        service = TwoFactorService()
        plain_codes, hashed_codes = service.generate_backup_codes()

        # Verify each code
        for i, code in enumerate(plain_codes):
            valid, index = service.verify_backup_code(code, hashed_codes)
            assert valid is True
            assert index == i

    def test_verify_backup_code_case_insensitive(self):
        """Test backup code verification is case insensitive."""
        service = TwoFactorService()
        plain_codes, hashed_codes = service.generate_backup_codes()

        # Try lowercase
        valid, _ = service.verify_backup_code(plain_codes[0].lower(), hashed_codes)
        assert valid is True

    def test_verify_backup_code_without_dash(self):
        """Test backup code verification works without dash."""
        service = TwoFactorService()
        plain_codes, hashed_codes = service.generate_backup_codes()

        # Remove dash
        code_no_dash = plain_codes[0].replace("-", "")
        valid, _ = service.verify_backup_code(code_no_dash, hashed_codes)
        assert valid is True

    def test_verify_backup_code_invalid(self):
        """Test backup code verification with invalid code."""
        service = TwoFactorService()
        _, hashed_codes = service.generate_backup_codes()

        valid, index = service.verify_backup_code("XXXX-XXXX", hashed_codes)
        assert valid is False
        assert index == -1

    def test_verify_backup_code_empty(self):
        """Test backup code verification with empty inputs."""
        service = TwoFactorService()
        _, hashed_codes = service.generate_backup_codes()

        valid, index = service.verify_backup_code("", hashed_codes)
        assert valid is False

        valid, index = service.verify_backup_code("ABCD-1234", [])
        assert valid is False

        valid, index = service.verify_backup_code("ABCD-1234", None)
        assert valid is False

    def test_invalidate_backup_code(self):
        """Test backup code invalidation."""
        service = TwoFactorService()
        _, hashed_codes = service.generate_backup_codes()

        # Invalidate first code
        updated_codes = service.invalidate_backup_code(hashed_codes, 0)

        assert updated_codes[0] is None
        assert updated_codes[1] is not None

    def test_count_remaining_codes(self):
        """Test counting remaining backup codes."""
        service = TwoFactorService()
        _, hashed_codes = service.generate_backup_codes()

        # Initially all codes are valid
        assert service.count_remaining_codes(hashed_codes) == BACKUP_CODE_COUNT

        # Invalidate some codes
        hashed_codes = service.invalidate_backup_code(hashed_codes, 0)
        hashed_codes = service.invalidate_backup_code(hashed_codes, 1)

        assert service.count_remaining_codes(hashed_codes) == BACKUP_CODE_COUNT - 2

    def test_count_remaining_codes_empty(self):
        """Test counting remaining codes with empty list."""
        service = TwoFactorService()

        assert service.count_remaining_codes([]) == 0
        assert service.count_remaining_codes(None) == 0


class TestDeviceTrust:
    """Tests for trusted device management."""

    def test_generate_device_token(self):
        """Test device token generation."""
        service = TwoFactorService()
        token = service.generate_device_token()

        assert token is not None
        assert len(token) >= 32

    def test_generate_device_token_unique(self):
        """Test device tokens are unique."""
        service = TwoFactorService()
        tokens = [service.generate_device_token() for _ in range(100)]

        assert len(set(tokens)) == 100

    def test_create_trusted_device(self):
        """Test creating a trusted device record."""
        service = TwoFactorService()
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        ip_address = "192.168.1.1"

        device = service.create_trusted_device(user_agent, ip_address)

        assert "token" in device
        assert device["user_agent"] == user_agent
        assert device["ip_address"] == ip_address
        assert "created_at" in device
        assert "expires_at" in device
        assert "last_used" in device

    def test_is_device_trusted_valid(self):
        """Test trusted device verification with valid token."""
        service = TwoFactorService()
        device = service.create_trusted_device("Mozilla", "192.168.1.1")

        trusted_devices = [device]

        assert service.is_device_trusted(device["token"], trusted_devices) is True

    def test_is_device_trusted_invalid(self):
        """Test trusted device verification with invalid token."""
        service = TwoFactorService()
        device = service.create_trusted_device("Mozilla", "192.168.1.1")

        trusted_devices = [device]

        assert service.is_device_trusted("invalid_token", trusted_devices) is False

    def test_is_device_trusted_empty(self):
        """Test trusted device verification with empty inputs."""
        service = TwoFactorService()

        assert service.is_device_trusted("token", []) is False
        assert service.is_device_trusted("token", None) is False
        assert service.is_device_trusted("", [{"token": "token"}]) is False
        assert service.is_device_trusted(None, [{"token": "token"}]) is False

    def test_is_device_trusted_expired(self):
        """Test trusted device verification with expired device."""
        service = TwoFactorService()

        # Create expired device
        expired_device = {
            "token": "test_token",
            "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
        }

        assert service.is_device_trusted("test_token", [expired_device]) is False

    def test_update_device_last_used(self):
        """Test updating device last_used timestamp."""
        service = TwoFactorService()
        device = service.create_trusted_device("Mozilla", "192.168.1.1")

        original_last_used = device["last_used"]

        import time
        time.sleep(0.01)  # Small delay

        updated_devices = service.update_device_last_used(
            device["token"], [device]
        )

        assert updated_devices[0]["last_used"] != original_last_used

    def test_remove_expired_devices(self):
        """Test removing expired devices."""
        service = TwoFactorService()

        # Create valid and expired devices
        valid_device = service.create_trusted_device("Mozilla", "192.168.1.1")
        expired_device = {
            "token": "expired_token",
            "expires_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
        }

        devices = [valid_device, expired_device]
        cleaned = service.remove_expired_devices(devices)

        assert len(cleaned) == 1
        assert cleaned[0]["token"] == valid_device["token"]

    def test_revoke_device(self):
        """Test revoking a specific device."""
        service = TwoFactorService()

        device1 = service.create_trusted_device("Mozilla", "192.168.1.1")
        device2 = service.create_trusted_device("Chrome", "192.168.1.2")

        devices = [device1, device2]
        updated = service.revoke_device(device1["token"], devices)

        assert len(updated) == 1
        assert updated[0]["token"] == device2["token"]

    def test_revoke_all_devices(self):
        """Test revoking all devices."""
        service = TwoFactorService()

        result = service.revoke_all_devices()

        assert result == []


class TestStaff2FASetup:
    """Tests for staff 2FA setup workflow."""

    def test_setup_2fa_for_staff(self):
        """Test 2FA setup for staff member."""
        service = TwoFactorService()

        # Create mock staff
        staff = MagicMock()
        staff.email = "staff@example.com"
        staff.two_factor_enabled = False

        setup_data = service.setup_2fa_for_staff(staff)

        assert "secret" in setup_data
        assert "qr_code" in setup_data
        assert "backup_codes" in setup_data
        assert setup_data["method"] == "totp"

        # Verify staff was updated
        assert staff.two_factor_secret is not None
        assert staff.two_factor_method == "totp"
        assert staff.two_factor_backup_codes is not None

    def test_verify_and_enable_2fa(self):
        """Test 2FA verification and enabling."""
        service = TwoFactorService()

        # Create mock staff with setup data
        staff = MagicMock()
        staff.email = "staff@example.com"

        # Do setup first
        setup_data = service.setup_2fa_for_staff(staff)

        # Generate current code
        code = service.generate_current_code(setup_data["secret"])

        # Verify and enable
        success, message = service.verify_and_enable_2fa(staff, code)

        assert success is True
        assert staff.two_factor_enabled is True
        assert staff.two_factor_verified_at is not None

    def test_verify_and_enable_2fa_invalid_code(self):
        """Test 2FA verification with invalid code."""
        service = TwoFactorService()

        # Create mock staff with setup
        staff = MagicMock()
        staff.email = "staff@example.com"
        service.setup_2fa_for_staff(staff)

        success, message = service.verify_and_enable_2fa(staff, "000000")

        assert success is False
        assert "Invalid" in message

    def test_verify_and_enable_2fa_no_setup(self):
        """Test 2FA verification without setup."""
        service = TwoFactorService()

        staff = MagicMock()
        staff.two_factor_secret = None

        success, message = service.verify_and_enable_2fa(staff, "123456")

        assert success is False
        assert "not initiated" in message

    def test_disable_2fa_with_totp(self):
        """Test disabling 2FA with TOTP code."""
        service = TwoFactorService()

        # Setup and enable 2FA
        staff = MagicMock()
        staff.email = "staff@example.com"
        setup_data = service.setup_2fa_for_staff(staff)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa(staff, code)

        # Now disable
        new_code = service.generate_current_code(setup_data["secret"])
        success, message = service.disable_2fa(staff, new_code)

        assert success is True
        assert staff.two_factor_enabled is False
        assert staff.two_factor_secret is None

    def test_disable_2fa_with_backup_code(self):
        """Test disabling 2FA with backup code."""
        service = TwoFactorService()

        # Setup and enable 2FA
        staff = MagicMock()
        staff.email = "staff@example.com"
        setup_data = service.setup_2fa_for_staff(staff)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa(staff, code)

        # Disable with backup code
        backup_code = setup_data["backup_codes"][0]
        success, message = service.disable_2fa(staff, backup_code, use_backup=True)

        assert success is True

    def test_disable_2fa_not_enabled(self):
        """Test disabling 2FA when not enabled."""
        service = TwoFactorService()

        staff = MagicMock()
        staff.two_factor_enabled = False

        success, message = service.disable_2fa(staff, "123456")

        assert success is False
        assert "not enabled" in message

    def test_get_2fa_status(self):
        """Test getting 2FA status."""
        service = TwoFactorService()

        staff = MagicMock()
        staff.two_factor_enabled = True
        staff.two_factor_method = "totp"
        staff.two_factor_verified_at = datetime.utcnow()
        staff.two_factor_last_used = datetime.utcnow()
        staff.two_factor_backup_codes = ["hash1", "hash2", None]
        staff.trusted_devices = []

        status = service.get_2fa_status(staff)

        assert status["enabled"] is True
        assert status["method"] == "totp"
        assert status["backup_codes_remaining"] == 2
        assert status["trusted_devices_count"] == 0


class TestStaff2FALogin:
    """Tests for staff 2FA login verification."""

    def test_verify_2fa_login_not_enabled(self):
        """Test 2FA login when 2FA is not enabled."""
        service = TwoFactorService()

        staff = MagicMock()
        staff.two_factor_enabled = False

        success, message, token = service.verify_2fa_login(staff, "123456")

        assert success is True
        assert "not required" in message
        assert token is None

    def test_verify_2fa_login_with_totp(self):
        """Test 2FA login with valid TOTP code."""
        service = TwoFactorService()

        # Setup 2FA
        staff = MagicMock()
        staff.email = "staff@example.com"
        staff.trusted_devices = []
        setup_data = service.setup_2fa_for_staff(staff)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa(staff, code)

        # Login
        new_code = service.generate_current_code(setup_data["secret"])
        success, message, token = service.verify_2fa_login(staff, new_code)

        assert success is True
        assert staff.two_factor_last_used is not None

    def test_verify_2fa_login_with_backup_code(self):
        """Test 2FA login with backup code."""
        service = TwoFactorService()

        # Setup 2FA
        staff = MagicMock()
        staff.email = "staff@example.com"
        staff.trusted_devices = []
        setup_data = service.setup_2fa_for_staff(staff)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa(staff, code)

        # Login with backup code
        backup_code = setup_data["backup_codes"][0]
        success, message, token = service.verify_2fa_login(staff, backup_code)

        assert success is True
        assert "Backup code accepted" in message

    def test_verify_2fa_login_with_trusted_device(self):
        """Test 2FA login with trusted device."""
        service = TwoFactorService()

        # Setup 2FA
        staff = MagicMock()
        staff.email = "staff@example.com"
        setup_data = service.setup_2fa_for_staff(staff)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa(staff, code)

        # Create trusted device
        device = service.create_trusted_device("Mozilla", "192.168.1.1")
        staff.trusted_devices = [device]

        # Login with device token (no code needed)
        success, message, token = service.verify_2fa_login(
            staff, "", device["token"]
        )

        assert success is True
        assert "trusted" in message.lower()

    def test_verify_2fa_login_trust_new_device(self):
        """Test 2FA login and trusting new device."""
        service = TwoFactorService()

        # Setup 2FA
        staff = MagicMock()
        staff.email = "staff@example.com"
        staff.trusted_devices = []
        setup_data = service.setup_2fa_for_staff(staff)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa(staff, code)

        # Login with trust_device=True
        new_code = service.generate_current_code(setup_data["secret"])
        success, message, new_token = service.verify_2fa_login(
            staff, new_code, None,
            "Mozilla/5.0", "192.168.1.1",
            trust_device=True
        )

        assert success is True
        assert new_token is not None
        assert len(staff.trusted_devices) == 1

    def test_verify_2fa_login_invalid_code(self):
        """Test 2FA login with invalid code."""
        service = TwoFactorService()

        # Setup 2FA
        staff = MagicMock()
        staff.email = "staff@example.com"
        staff.trusted_devices = []
        setup_data = service.setup_2fa_for_staff(staff)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa(staff, code)

        # Try invalid code
        success, message, token = service.verify_2fa_login(staff, "000000")

        assert success is False
        assert "Invalid" in message

    def test_regenerate_backup_codes(self):
        """Test regenerating backup codes."""
        service = TwoFactorService()

        # Setup 2FA
        staff = MagicMock()
        staff.email = "staff@example.com"
        setup_data = service.setup_2fa_for_staff(staff)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa(staff, code)

        original_codes = setup_data["backup_codes"]

        # Regenerate
        new_code = service.generate_current_code(setup_data["secret"])
        success, new_codes, message = service.regenerate_backup_codes(staff, new_code)

        assert success is True
        assert len(new_codes) == BACKUP_CODE_COUNT
        assert new_codes != original_codes

    def test_regenerate_backup_codes_invalid_code(self):
        """Test regenerating backup codes with invalid TOTP."""
        service = TwoFactorService()

        # Setup 2FA
        staff = MagicMock()
        staff.email = "staff@example.com"
        setup_data = service.setup_2fa_for_staff(staff)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa(staff, code)

        success, new_codes, message = service.regenerate_backup_codes(staff, "000000")

        assert success is False
        assert new_codes == []


class TestPartner2FA:
    """Tests for partner portal 2FA."""

    def test_setup_2fa_for_partner(self):
        """Test 2FA setup for partner."""
        service = TwoFactorService()

        tenant = MagicMock()
        tenant.admin_email = "partner@example.com"
        tenant.company_email = None
        tenant.slug = "partner"

        setup_data = service.setup_2fa_for_partner(tenant)

        assert "secret" in setup_data
        assert "qr_code" in setup_data
        assert "backup_codes" in setup_data
        assert tenant.two_factor_secret is not None

    def test_verify_and_enable_2fa_partner(self):
        """Test 2FA verification for partner."""
        service = TwoFactorService()

        tenant = MagicMock()
        tenant.admin_email = "partner@example.com"
        tenant.slug = "partner"

        setup_data = service.setup_2fa_for_partner(tenant)
        code = service.generate_current_code(setup_data["secret"])

        success, message = service.verify_and_enable_2fa_partner(tenant, code)

        assert success is True
        assert tenant.two_factor_enabled is True

    def test_verify_2fa_partner_login(self):
        """Test partner 2FA login."""
        service = TwoFactorService()

        tenant = MagicMock()
        tenant.admin_email = "partner@example.com"
        tenant.slug = "partner"

        setup_data = service.setup_2fa_for_partner(tenant)
        code = service.generate_current_code(setup_data["secret"])
        service.verify_and_enable_2fa_partner(tenant, code)

        # Login
        new_code = service.generate_current_code(setup_data["secret"])
        success, message = service.verify_2fa_partner_login(tenant, new_code)

        assert success is True


class TestConstants:
    """Tests for module constants."""

    def test_backup_code_count(self):
        """Test backup code count constant."""
        assert BACKUP_CODE_COUNT == 10

    def test_backup_code_length(self):
        """Test backup code length constant."""
        assert BACKUP_CODE_LENGTH == 8

    def test_device_trust_days(self):
        """Test device trust days constant."""
        assert DEVICE_TRUST_DAYS == 30

    def test_issuer_name(self):
        """Test issuer name constant."""
        assert ISSUER_NAME == "Brightpath Ascend"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
