"""
Encryption service for sensitive data storage.
Uses Fernet symmetric encryption with environment-managed key.
"""

import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def get_encryption_key():
    """Get encryption key from environment - fails if not configured."""
    key = os.environ.get("FCRA_ENCRYPTION_KEY")

    if not key:
        # In CI/testing, generate a temporary key
        if os.environ.get("CI") == "true" or os.environ.get("TESTING") == "true":
            key = Fernet.generate_key().decode()
            os.environ["FCRA_ENCRYPTION_KEY"] = key
        else:
            raise ValueError(
                "FCRA_ENCRYPTION_KEY environment variable is required. "
                'Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )

    if isinstance(key, str):
        try:
            key_bytes = (
                key.encode()
                if len(key) == 44
                else base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b"\0"))
            )
        except:
            raise ValueError(
                "Invalid FCRA_ENCRYPTION_KEY format. Must be a valid Fernet key."
            )
    else:
        key_bytes = key

    return key_bytes


def get_fernet():
    """Get Fernet instance with current key"""
    key = get_encryption_key()
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a plaintext string and return base64-encoded ciphertext.

    Args:
        plaintext: The string to encrypt

    Returns:
        Base64-encoded encrypted string
    """
    if not plaintext:
        return ""

    f = get_fernet()
    encrypted = f.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt a base64-encoded ciphertext string.

    Args:
        ciphertext: The encrypted string to decrypt

    Returns:
        Decrypted plaintext string
    """
    if not ciphertext:
        return ""

    try:
        f = get_fernet()
        decrypted = f.decrypt(ciphertext.encode())
        return decrypted.decode()
    except Exception as e:
        print(f"⚠️  Decryption failed (may be plaintext): {str(e)[:50]}")
        return ciphertext


def is_encrypted(value: str) -> bool:
    """Check if a value appears to be Fernet-encrypted"""
    if not value:
        return False
    try:
        decoded = base64.urlsafe_b64decode(value.encode())
        return len(decoded) >= 57
    except:
        return False


def migrate_plaintext_to_encrypted(db_session, Client):
    """
    Migrate existing plaintext passwords to encrypted format.
    Run this once to encrypt all existing passwords.
    """
    from database import get_db

    migrated = 0
    clients = (
        db_session.query(Client)
        .filter(
            Client.credit_monitoring_password_encrypted.isnot(None),
            Client.credit_monitoring_password_encrypted != "",
        )
        .all()
    )

    for client in clients:
        current_value = client.credit_monitoring_password_encrypted
        if current_value and not is_encrypted(current_value):
            encrypted = encrypt_value(current_value)
            client.credit_monitoring_password_encrypted = encrypted
            migrated += 1

    if migrated > 0:
        db_session.commit()
        print(f"✅ Migrated {migrated} plaintext passwords to encrypted format")

    return migrated
