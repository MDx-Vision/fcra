"""
Two-Factor Authentication (2FA) Service

Provides TOTP-based 2FA with backup codes, device trust, and SMS/email fallback.
"""

import base64
import hashlib
import hmac
import io
import os
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any

import pyotp
import qrcode
from qrcode.image.pure import PyPNGImage

from services.encryption import encrypt_value, decrypt_value


# Constants
BACKUP_CODE_COUNT = 10
BACKUP_CODE_LENGTH = 8
DEVICE_TRUST_DAYS = 30
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
ISSUER_NAME = "Brightpath Ascend"


class TwoFactorService:
    """Service for managing two-factor authentication."""

    def __init__(self, db_session=None):
        """Initialize the service with optional database session."""
        self.db = db_session

    # =========================================================================
    # TOTP Setup
    # =========================================================================

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret.

        Returns:
            Base32-encoded secret string
        """
        return pyotp.random_base32()

    def encrypt_secret(self, secret: str) -> str:
        """
        Encrypt a TOTP secret for database storage.

        Args:
            secret: Plain TOTP secret

        Returns:
            Encrypted secret string
        """
        return encrypt_value(secret)

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """
        Decrypt a stored TOTP secret.

        Args:
            encrypted_secret: Encrypted secret from database

        Returns:
            Plain TOTP secret
        """
        return decrypt_value(encrypted_secret)

    def get_totp(self, secret: str) -> pyotp.TOTP:
        """
        Get a TOTP object for generating/verifying codes.

        Args:
            secret: Plain TOTP secret

        Returns:
            pyotp.TOTP instance
        """
        return pyotp.TOTP(secret)

    def generate_current_code(self, secret: str) -> str:
        """
        Generate the current TOTP code.

        Args:
            secret: Plain TOTP secret

        Returns:
            6-digit TOTP code
        """
        totp = self.get_totp(secret)
        return totp.now()

    def verify_totp(self, secret: str, code: str, valid_window: int = 1) -> bool:
        """
        Verify a TOTP code.

        Args:
            secret: Plain TOTP secret
            code: 6-digit code to verify
            valid_window: Number of 30-second windows to check (default 1 = 90 seconds)

        Returns:
            True if code is valid
        """
        if not secret or not code:
            return False

        # Clean the code (remove spaces, dashes)
        code = code.replace(" ", "").replace("-", "")

        if len(code) != 6 or not code.isdigit():
            return False

        totp = self.get_totp(secret)
        return totp.verify(code, valid_window=valid_window)

    # =========================================================================
    # QR Code Generation
    # =========================================================================

    def get_provisioning_uri(self, secret: str, email: str, issuer: str = None) -> str:
        """
        Get the otpauth:// URI for authenticator apps.

        Args:
            secret: Plain TOTP secret
            email: User's email (used as account name)
            issuer: Optional issuer name (defaults to ISSUER_NAME)

        Returns:
            otpauth:// URI string
        """
        totp = self.get_totp(secret)
        return totp.provisioning_uri(
            name=email,
            issuer_name=issuer or ISSUER_NAME
        )

    def generate_qr_code(self, secret: str, email: str, issuer: str = None) -> str:
        """
        Generate a QR code for authenticator app setup.

        Args:
            secret: Plain TOTP secret
            email: User's email
            issuer: Optional issuer name

        Returns:
            Base64-encoded PNG image
        """
        uri = self.get_provisioning_uri(secret, email, issuer)

        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        return base64.b64encode(buffer.getvalue()).decode()

    # =========================================================================
    # Backup Codes
    # =========================================================================

    def generate_backup_codes(self, count: int = BACKUP_CODE_COUNT) -> Tuple[List[str], List[str]]:
        """
        Generate backup codes for account recovery.

        Args:
            count: Number of codes to generate

        Returns:
            Tuple of (plain_codes, hashed_codes)
            - plain_codes: Show to user once
            - hashed_codes: Store in database
        """
        plain_codes = []
        hashed_codes = []

        for _ in range(count):
            # Generate random code (e.g., "ABCD-1234")
            code = self._generate_backup_code()
            plain_codes.append(code)
            hashed_codes.append(self._hash_backup_code(code))

        return plain_codes, hashed_codes

    def _generate_backup_code(self) -> str:
        """Generate a single backup code."""
        # Generate 8 random alphanumeric characters
        chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Exclude confusing chars (0, O, 1, I)
        code = "".join(secrets.choice(chars) for _ in range(BACKUP_CODE_LENGTH))
        # Format as XXXX-XXXX
        return f"{code[:4]}-{code[4:]}"

    def _hash_backup_code(self, code: str) -> str:
        """Hash a backup code for storage."""
        # Normalize code (uppercase, remove dashes)
        normalized = code.upper().replace("-", "").replace(" ", "")
        return hashlib.sha256(normalized.encode()).hexdigest()

    def verify_backup_code(self, code: str, hashed_codes: List[str]) -> Tuple[bool, int]:
        """
        Verify a backup code and return which one was used.

        Args:
            code: Plain backup code from user
            hashed_codes: List of hashed codes from database

        Returns:
            Tuple of (is_valid, index_used)
            - index_used is -1 if not valid
        """
        if not code or not hashed_codes:
            return False, -1

        # Hash the provided code
        hashed = self._hash_backup_code(code)

        # Check against stored hashes
        for i, stored_hash in enumerate(hashed_codes):
            if stored_hash and stored_hash == hashed:
                return True, i

        return False, -1

    def invalidate_backup_code(self, hashed_codes: List[str], index: int) -> List[str]:
        """
        Invalidate a used backup code.

        Args:
            hashed_codes: List of hashed codes
            index: Index of code to invalidate

        Returns:
            Updated list with code marked as used (set to None)
        """
        if 0 <= index < len(hashed_codes):
            hashed_codes[index] = None
        return hashed_codes

    def count_remaining_codes(self, hashed_codes: List[str]) -> int:
        """Count how many backup codes are still valid."""
        if not hashed_codes:
            return 0
        return sum(1 for code in hashed_codes if code is not None)

    # =========================================================================
    # Device Trust
    # =========================================================================

    def generate_device_token(self) -> str:
        """Generate a unique device trust token."""
        return secrets.token_urlsafe(32)

    def create_trusted_device(self, user_agent: str, ip_address: str) -> Dict[str, Any]:
        """
        Create a trusted device record.

        Args:
            user_agent: Browser user agent
            ip_address: Client IP address

        Returns:
            Device record dict with token
        """
        return {
            "token": self.generate_device_token(),
            "user_agent": user_agent[:500] if user_agent else "",
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=DEVICE_TRUST_DAYS)).isoformat(),
            "last_used": datetime.utcnow().isoformat()
        }

    def is_device_trusted(self, device_token: str, trusted_devices: List[Dict]) -> bool:
        """
        Check if a device is trusted.

        Args:
            device_token: Token from cookie/header
            trusted_devices: List of trusted device records

        Returns:
            True if device is trusted and not expired
        """
        if not device_token or not trusted_devices:
            return False

        now = datetime.utcnow()

        for device in trusted_devices:
            if device.get("token") == device_token:
                expires_at = datetime.fromisoformat(device.get("expires_at", "1970-01-01"))
                if expires_at > now:
                    return True

        return False

    def update_device_last_used(self, device_token: str, trusted_devices: List[Dict]) -> List[Dict]:
        """Update the last_used timestamp for a trusted device."""
        for device in trusted_devices:
            if device.get("token") == device_token:
                device["last_used"] = datetime.utcnow().isoformat()
                break
        return trusted_devices

    def remove_expired_devices(self, trusted_devices: List[Dict]) -> List[Dict]:
        """Remove expired devices from the list."""
        if not trusted_devices:
            return []

        now = datetime.utcnow()
        return [
            device for device in trusted_devices
            if datetime.fromisoformat(device.get("expires_at", "1970-01-01")) > now
        ]

    def revoke_device(self, device_token: str, trusted_devices: List[Dict]) -> List[Dict]:
        """Revoke a specific trusted device."""
        if not trusted_devices:
            return []
        return [d for d in trusted_devices if d.get("token") != device_token]

    def revoke_all_devices(self) -> List[Dict]:
        """Revoke all trusted devices (returns empty list)."""
        return []

    # =========================================================================
    # Staff 2FA Management
    # =========================================================================

    def setup_2fa_for_staff(self, staff, method: str = 'totp') -> Dict[str, Any]:
        """
        Initialize 2FA setup for a staff member.

        Args:
            staff: Staff model instance
            method: 2FA method ('totp', 'sms', 'email')

        Returns:
            Setup data including secret, QR code, backup codes
        """
        # Generate new secret
        secret = self.generate_secret()
        encrypted_secret = self.encrypt_secret(secret)

        # Generate backup codes
        plain_codes, hashed_codes = self.generate_backup_codes()

        # Generate QR code for TOTP
        qr_code = None
        provisioning_uri = None
        if method == 'totp':
            qr_code = self.generate_qr_code(secret, staff.email)
            provisioning_uri = self.get_provisioning_uri(secret, staff.email)

        # Store in database (not enabled yet - user must verify first)
        staff.two_factor_secret = encrypted_secret
        staff.two_factor_method = method
        staff.two_factor_backup_codes = hashed_codes
        # Don't set two_factor_enabled = True yet - wait for verification

        if self.db:
            self.db.commit()

        return {
            "secret": secret,  # Show to user for manual entry
            "qr_code": qr_code,  # Base64 PNG
            "provisioning_uri": provisioning_uri,
            "backup_codes": plain_codes,  # Show once, never again
            "method": method
        }

    def verify_and_enable_2fa(self, staff, code: str) -> Tuple[bool, str]:
        """
        Verify a TOTP code and enable 2FA for the staff member.

        Args:
            staff: Staff model instance
            code: 6-digit TOTP code

        Returns:
            Tuple of (success, message)
        """
        if not staff.two_factor_secret:
            return False, "2FA setup not initiated. Please start setup first."

        # Decrypt the secret
        secret = self.decrypt_secret(staff.two_factor_secret)

        # Verify the code
        if not self.verify_totp(secret, code):
            return False, "Invalid verification code. Please try again."

        # Enable 2FA
        staff.two_factor_enabled = True
        staff.two_factor_verified_at = datetime.utcnow()

        if self.db:
            self.db.commit()

        return True, "Two-factor authentication enabled successfully."

    def disable_2fa(self, staff, code: str = None, use_backup: bool = False) -> Tuple[bool, str]:
        """
        Disable 2FA for a staff member.

        Args:
            staff: Staff model instance
            code: TOTP code or backup code
            use_backup: Whether the code is a backup code

        Returns:
            Tuple of (success, message)
        """
        if not staff.two_factor_enabled:
            return False, "2FA is not enabled."

        # Verify the code
        if use_backup:
            valid, index = self.verify_backup_code(code, staff.two_factor_backup_codes or [])
            if not valid:
                return False, "Invalid backup code."
        else:
            secret = self.decrypt_secret(staff.two_factor_secret)
            if not self.verify_totp(secret, code):
                return False, "Invalid verification code."

        # Disable 2FA
        staff.two_factor_enabled = False
        staff.two_factor_secret = None
        staff.two_factor_backup_codes = None
        staff.two_factor_verified_at = None
        staff.two_factor_last_used = None
        staff.trusted_devices = None

        if self.db:
            self.db.commit()

        return True, "Two-factor authentication disabled successfully."

    def verify_2fa_login(self, staff, code: str, device_token: str = None,
                         user_agent: str = None, ip_address: str = None,
                         trust_device: bool = False) -> Tuple[bool, str, Optional[str]]:
        """
        Verify 2FA during login.

        Args:
            staff: Staff model instance
            code: TOTP code or backup code
            device_token: Optional trusted device token
            user_agent: Browser user agent
            ip_address: Client IP
            trust_device: Whether to trust this device

        Returns:
            Tuple of (success, message, new_device_token)
        """
        if not staff.two_factor_enabled:
            return True, "2FA not required.", None

        # Check if device is trusted
        trusted_devices = staff.trusted_devices or []
        if device_token and self.is_device_trusted(device_token, trusted_devices):
            # Update last used
            staff.trusted_devices = self.update_device_last_used(device_token, trusted_devices)
            staff.two_factor_last_used = datetime.utcnow()
            if self.db:
                self.db.commit()
            return True, "Device trusted.", device_token

        # Try TOTP verification
        secret = self.decrypt_secret(staff.two_factor_secret)
        if self.verify_totp(secret, code):
            new_token = None

            if trust_device and user_agent and ip_address:
                # Add trusted device
                device = self.create_trusted_device(user_agent, ip_address)
                trusted_devices = self.remove_expired_devices(trusted_devices)
                trusted_devices.append(device)
                staff.trusted_devices = trusted_devices
                new_token = device["token"]

            staff.two_factor_last_used = datetime.utcnow()
            if self.db:
                self.db.commit()

            return True, "Verification successful.", new_token

        # Try backup code
        valid, index = self.verify_backup_code(code, staff.two_factor_backup_codes or [])
        if valid:
            # Invalidate used backup code
            staff.two_factor_backup_codes = self.invalidate_backup_code(
                staff.two_factor_backup_codes, index
            )
            staff.two_factor_last_used = datetime.utcnow()

            new_token = None
            if trust_device and user_agent and ip_address:
                device = self.create_trusted_device(user_agent, ip_address)
                trusted_devices = self.remove_expired_devices(trusted_devices or [])
                trusted_devices.append(device)
                staff.trusted_devices = trusted_devices
                new_token = device["token"]

            if self.db:
                self.db.commit()

            remaining = self.count_remaining_codes(staff.two_factor_backup_codes)
            return True, f"Backup code accepted. {remaining} codes remaining.", new_token

        return False, "Invalid verification code.", None

    def regenerate_backup_codes(self, staff, code: str) -> Tuple[bool, List[str], str]:
        """
        Regenerate backup codes (requires valid TOTP code).

        Args:
            staff: Staff model instance
            code: Current TOTP code for verification

        Returns:
            Tuple of (success, new_codes, message)
        """
        if not staff.two_factor_enabled:
            return False, [], "2FA is not enabled."

        # Verify current code
        secret = self.decrypt_secret(staff.two_factor_secret)
        if not self.verify_totp(secret, code):
            return False, [], "Invalid verification code."

        # Generate new codes
        plain_codes, hashed_codes = self.generate_backup_codes()
        staff.two_factor_backup_codes = hashed_codes

        if self.db:
            self.db.commit()

        return True, plain_codes, "Backup codes regenerated successfully."

    def get_2fa_status(self, staff) -> Dict[str, Any]:
        """
        Get 2FA status for a staff member.

        Args:
            staff: Staff model instance

        Returns:
            Status dict
        """
        backup_codes = staff.two_factor_backup_codes or []
        trusted_devices = staff.trusted_devices or []

        return {
            "enabled": staff.two_factor_enabled or False,
            "method": staff.two_factor_method or 'totp',
            "verified_at": staff.two_factor_verified_at.isoformat() if staff.two_factor_verified_at else None,
            "last_used": staff.two_factor_last_used.isoformat() if staff.two_factor_last_used else None,
            "backup_codes_remaining": self.count_remaining_codes(backup_codes),
            "trusted_devices_count": len(self.remove_expired_devices(trusted_devices))
        }

    # =========================================================================
    # Partner Portal 2FA (WhiteLabelTenant)
    # =========================================================================

    def setup_2fa_for_partner(self, tenant, method: str = 'totp') -> Dict[str, Any]:
        """Initialize 2FA setup for a partner portal admin."""
        secret = self.generate_secret()
        encrypted_secret = self.encrypt_secret(secret)
        plain_codes, hashed_codes = self.generate_backup_codes()

        qr_code = None
        provisioning_uri = None
        if method == 'totp':
            email = tenant.admin_email or tenant.company_email or f"{tenant.slug}@partner.local"
            qr_code = self.generate_qr_code(secret, email, f"{ISSUER_NAME} Partner")
            provisioning_uri = self.get_provisioning_uri(secret, email, f"{ISSUER_NAME} Partner")

        tenant.two_factor_secret = encrypted_secret
        tenant.two_factor_method = method
        tenant.two_factor_backup_codes = hashed_codes

        if self.db:
            self.db.commit()

        return {
            "secret": secret,
            "qr_code": qr_code,
            "provisioning_uri": provisioning_uri,
            "backup_codes": plain_codes,
            "method": method
        }

    def verify_and_enable_2fa_partner(self, tenant, code: str) -> Tuple[bool, str]:
        """Verify and enable 2FA for partner portal admin."""
        if not tenant.two_factor_secret:
            return False, "2FA setup not initiated."

        secret = self.decrypt_secret(tenant.two_factor_secret)
        if not self.verify_totp(secret, code):
            return False, "Invalid verification code."

        tenant.two_factor_enabled = True
        tenant.two_factor_verified_at = datetime.utcnow()

        if self.db:
            self.db.commit()

        return True, "Two-factor authentication enabled."

    def verify_2fa_partner_login(self, tenant, code: str) -> Tuple[bool, str]:
        """Verify 2FA during partner portal login."""
        if not tenant.two_factor_enabled:
            return True, "2FA not required."

        secret = self.decrypt_secret(tenant.two_factor_secret)
        if self.verify_totp(secret, code):
            return True, "Verification successful."

        # Try backup code
        valid, index = self.verify_backup_code(code, tenant.two_factor_backup_codes or [])
        if valid:
            tenant.two_factor_backup_codes = self.invalidate_backup_code(
                tenant.two_factor_backup_codes, index
            )
            if self.db:
                self.db.commit()
            remaining = self.count_remaining_codes(tenant.two_factor_backup_codes)
            return True, f"Backup code accepted. {remaining} codes remaining."

        return False, "Invalid verification code."


# Singleton instance
_service = None


def get_two_factor_service(db_session=None) -> TwoFactorService:
    """Get or create the TwoFactorService instance."""
    global _service
    if _service is None or db_session:
        _service = TwoFactorService(db_session)
    return _service
