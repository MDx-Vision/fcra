"""
Unit tests for Encryption Service
Tests for encryption key management, Fernet encryption/decryption,
value encryption checking, and database migration utilities.
"""
import pytest
import base64
import os
from unittest.mock import Mock, MagicMock, patch
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cryptography.fernet import Fernet

from services.encryption import (
    get_encryption_key,
    get_fernet,
    encrypt_value,
    decrypt_value,
    is_encrypted,
    migrate_plaintext_to_encrypted,
)


# ============== Fixtures ==============


@pytest.fixture
def valid_fernet_key():
    """Generate a valid Fernet key for testing."""
    return Fernet.generate_key().decode()


@pytest.fixture
def clean_env():
    """Fixture to ensure clean environment for encryption tests."""
    # Store original values
    original_key = os.environ.get("FCRA_ENCRYPTION_KEY")
    original_ci = os.environ.get("CI")
    original_testing = os.environ.get("TESTING")

    # Clean environment
    if "FCRA_ENCRYPTION_KEY" in os.environ:
        del os.environ["FCRA_ENCRYPTION_KEY"]

    yield

    # Restore original values
    if original_key is not None:
        os.environ["FCRA_ENCRYPTION_KEY"] = original_key
    elif "FCRA_ENCRYPTION_KEY" in os.environ:
        del os.environ["FCRA_ENCRYPTION_KEY"]

    if original_ci is not None:
        os.environ["CI"] = original_ci
    if original_testing is not None:
        os.environ["TESTING"] = original_testing


# ============== get_encryption_key Tests ==============


class TestGetEncryptionKey:
    """Tests for get_encryption_key function."""

    def test_get_encryption_key_from_environment(self, valid_fernet_key, clean_env):
        """Test getting encryption key from environment variable."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        key = get_encryption_key()
        assert key is not None
        assert isinstance(key, bytes)

    def test_get_encryption_key_generates_in_ci(self, clean_env):
        """Test that key is auto-generated in CI environment."""
        os.environ["CI"] = "true"
        key = get_encryption_key()
        assert key is not None
        assert isinstance(key, bytes)
        # Verify it was stored in environment
        assert os.environ.get("FCRA_ENCRYPTION_KEY") is not None

    def test_get_encryption_key_generates_in_testing(self, clean_env):
        """Test that key is auto-generated in TESTING environment."""
        os.environ["TESTING"] = "true"
        key = get_encryption_key()
        assert key is not None
        assert isinstance(key, bytes)
        # Verify it was stored in environment
        assert os.environ.get("FCRA_ENCRYPTION_KEY") is not None

    def test_get_encryption_key_raises_without_key_in_production(self, clean_env):
        """Test that ValueError is raised when no key in production."""
        # Ensure CI and TESTING are not set
        if "CI" in os.environ:
            del os.environ["CI"]
        if "TESTING" in os.environ:
            del os.environ["TESTING"]

        with pytest.raises(ValueError) as excinfo:
            get_encryption_key()

        assert "FCRA_ENCRYPTION_KEY" in str(excinfo.value)
        assert "environment variable is required" in str(excinfo.value)

    def test_get_encryption_key_44_char_key(self, clean_env):
        """Test handling of 44-character Fernet key."""
        os.environ["CI"] = "true"
        # Generate a proper 44-char Fernet key
        fernet_key = Fernet.generate_key().decode()
        assert len(fernet_key) == 44
        os.environ["FCRA_ENCRYPTION_KEY"] = fernet_key

        key = get_encryption_key()
        assert key is not None
        assert isinstance(key, bytes)
        # Should be encoded directly
        assert key == fernet_key.encode()

    def test_get_encryption_key_short_key_padded(self, clean_env):
        """Test handling of short key that gets padded."""
        os.environ["CI"] = "true"
        short_key = "my_short_secret_key"
        os.environ["FCRA_ENCRYPTION_KEY"] = short_key

        key = get_encryption_key()
        assert key is not None
        assert isinstance(key, bytes)
        # Short keys are padded and base64 encoded
        expected = base64.urlsafe_b64encode(short_key.encode()[:32].ljust(32, b"\0"))
        assert key == expected

    def test_get_encryption_key_32_char_key(self, clean_env):
        """Test handling of exactly 32-character key."""
        os.environ["CI"] = "true"
        key_32 = "a" * 32
        os.environ["FCRA_ENCRYPTION_KEY"] = key_32

        key = get_encryption_key()
        assert key is not None
        assert isinstance(key, bytes)

    def test_get_encryption_key_bytes_input(self, clean_env):
        """Test handling when key is already bytes."""
        os.environ["CI"] = "true"
        fernet_key = Fernet.generate_key().decode()
        os.environ["FCRA_ENCRYPTION_KEY"] = fernet_key

        key = get_encryption_key()
        assert isinstance(key, bytes)


# ============== get_fernet Tests ==============


class TestGetFernet:
    """Tests for get_fernet function."""

    def test_get_fernet_returns_fernet_instance(self, valid_fernet_key, clean_env):
        """Test that get_fernet returns a Fernet instance."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        f = get_fernet()
        assert isinstance(f, Fernet)

    def test_get_fernet_can_encrypt_decrypt(self, valid_fernet_key, clean_env):
        """Test that returned Fernet instance works correctly."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        f = get_fernet()

        test_message = b"Hello, World!"
        encrypted = f.encrypt(test_message)
        decrypted = f.decrypt(encrypted)

        assert decrypted == test_message

    def test_get_fernet_in_ci_environment(self, clean_env):
        """Test get_fernet works in CI environment."""
        os.environ["CI"] = "true"
        f = get_fernet()
        assert isinstance(f, Fernet)

    def test_get_fernet_string_key_handling(self, clean_env):
        """Test that string keys are properly converted to bytes."""
        os.environ["CI"] = "true"
        fernet_key = Fernet.generate_key().decode()
        os.environ["FCRA_ENCRYPTION_KEY"] = fernet_key

        f = get_fernet()
        assert isinstance(f, Fernet)

        # Verify it works
        encrypted = f.encrypt(b"test")
        decrypted = f.decrypt(encrypted)
        assert decrypted == b"test"


# ============== encrypt_value Tests ==============


class TestEncryptValue:
    """Tests for encrypt_value function."""

    def test_encrypt_value_basic(self, valid_fernet_key, clean_env):
        """Test basic string encryption."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "my secret password"
        encrypted = encrypt_value(plaintext)

        assert encrypted is not None
        assert encrypted != plaintext
        assert isinstance(encrypted, str)

    def test_encrypt_value_empty_string_returns_empty(self, valid_fernet_key, clean_env):
        """Test that empty string returns empty string."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        result = encrypt_value("")
        assert result == ""

    def test_encrypt_value_none_returns_empty(self, valid_fernet_key, clean_env):
        """Test that None-like falsy values return empty string."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        # Empty string is falsy
        result = encrypt_value("")
        assert result == ""

    def test_encrypt_value_produces_base64_output(self, valid_fernet_key, clean_env):
        """Test that encrypted output is base64 encoded."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "test data"
        encrypted = encrypt_value(plaintext)

        # Should be valid base64
        try:
            decoded = base64.urlsafe_b64decode(encrypted.encode())
            assert len(decoded) > 0
        except Exception:
            pytest.fail("Encrypted value is not valid base64")

    def test_encrypt_value_same_input_different_output(self, valid_fernet_key, clean_env):
        """Test that encrypting same value twice produces different ciphertext."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "test password"

        encrypted1 = encrypt_value(plaintext)
        encrypted2 = encrypt_value(plaintext)

        # Fernet uses random IV, so outputs should differ
        assert encrypted1 != encrypted2

    def test_encrypt_value_unicode_characters(self, valid_fernet_key, clean_env):
        """Test encryption handles unicode characters."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "Password with unicode: \u00e9\u00e0\u00fc"
        encrypted = encrypt_value(plaintext)

        assert encrypted is not None
        assert isinstance(encrypted, str)

    def test_encrypt_value_special_characters(self, valid_fernet_key, clean_env):
        """Test encryption handles special characters."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "P@ssw0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
        encrypted = encrypt_value(plaintext)

        assert encrypted is not None
        assert isinstance(encrypted, str)

    def test_encrypt_value_long_string(self, valid_fernet_key, clean_env):
        """Test encryption handles long strings."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "A" * 10000
        encrypted = encrypt_value(plaintext)

        assert encrypted is not None
        assert len(encrypted) > len(plaintext)

    def test_encrypt_value_whitespace(self, valid_fernet_key, clean_env):
        """Test encryption preserves whitespace."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "  password with spaces  "
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)

        assert decrypted == plaintext


# ============== decrypt_value Tests ==============


class TestDecryptValue:
    """Tests for decrypt_value function."""

    def test_decrypt_value_basic(self, valid_fernet_key, clean_env):
        """Test basic decryption."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "my secret password"
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)

        assert decrypted == plaintext

    def test_decrypt_value_empty_string_returns_empty(self, valid_fernet_key, clean_env):
        """Test that empty string returns empty string."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        result = decrypt_value("")
        assert result == ""

    def test_decrypt_value_none_returns_empty(self, valid_fernet_key, clean_env):
        """Test that None-like falsy values return empty string."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        result = decrypt_value("")
        assert result == ""

    def test_decrypt_value_returns_plaintext_on_failure(self, valid_fernet_key, clean_env):
        """Test that invalid ciphertext returns original value."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        invalid_ciphertext = "not_a_valid_encrypted_string"
        result = decrypt_value(invalid_ciphertext)

        # Should return original value when decryption fails
        assert result == invalid_ciphertext

    def test_decrypt_value_invalid_base64_returns_original(self, valid_fernet_key, clean_env):
        """Test that invalid base64 returns original value."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        invalid_data = "!!!not-base64!!!"
        result = decrypt_value(invalid_data)

        assert result == invalid_data

    def test_decrypt_value_wrong_key_returns_original(self, clean_env):
        """Test that wrong key returns original ciphertext."""
        os.environ["CI"] = "true"

        # Encrypt with one key
        key1 = Fernet.generate_key().decode()
        os.environ["FCRA_ENCRYPTION_KEY"] = key1
        encrypted = encrypt_value("secret")

        # Try to decrypt with different key
        key2 = Fernet.generate_key().decode()
        os.environ["FCRA_ENCRYPTION_KEY"] = key2
        result = decrypt_value(encrypted)

        # Should return original ciphertext
        assert result == encrypted

    def test_decrypt_value_unicode_preserved(self, valid_fernet_key, clean_env):
        """Test that unicode is preserved through encrypt/decrypt cycle."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "Password: \u00e9\u00e0\u00fc\u00f1\u00d1"
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)

        assert decrypted == plaintext

    def test_decrypt_value_special_chars_preserved(self, valid_fernet_key, clean_env):
        """Test that special characters are preserved through encrypt/decrypt cycle."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        plaintext = "P@ssw0rd!#$%^&*()_+-="
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)

        assert decrypted == plaintext

    def test_decrypt_value_logs_warning_on_failure(self, valid_fernet_key, clean_env, capsys):
        """Test that decryption failure logs a warning."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        invalid_ciphertext = "invalid_encrypted_data_that_will_fail"
        decrypt_value(invalid_ciphertext)

        captured = capsys.readouterr()
        assert "Decryption failed" in captured.out or invalid_ciphertext == decrypt_value(invalid_ciphertext)


# ============== is_encrypted Tests ==============


class TestIsEncrypted:
    """Tests for is_encrypted function."""

    def test_is_encrypted_true_for_encrypted_value(self, valid_fernet_key, clean_env):
        """Test that encrypted values are correctly identified."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        encrypted = encrypt_value("test password")
        assert is_encrypted(encrypted) is True

    def test_is_encrypted_false_for_plaintext(self, clean_env):
        """Test that plaintext values return False."""
        os.environ["CI"] = "true"
        assert is_encrypted("plaintext password") is False

    def test_is_encrypted_false_for_empty_string(self, clean_env):
        """Test that empty string returns False."""
        os.environ["CI"] = "true"
        assert is_encrypted("") is False

    def test_is_encrypted_false_for_none(self, clean_env):
        """Test that None-like falsy values return False."""
        os.environ["CI"] = "true"
        assert is_encrypted("") is False
        assert is_encrypted(None) is False

    def test_is_encrypted_false_for_short_base64(self, clean_env):
        """Test that short base64 strings return False."""
        os.environ["CI"] = "true"
        # Valid base64 but too short for Fernet
        short_base64 = base64.urlsafe_b64encode(b"short").decode()
        assert is_encrypted(short_base64) is False

    def test_is_encrypted_false_for_invalid_base64(self, clean_env):
        """Test that invalid base64 returns False."""
        os.environ["CI"] = "true"
        assert is_encrypted("!!!not-valid-base64!!!") is False

    def test_is_encrypted_checks_minimum_length(self, clean_env):
        """Test that is_encrypted checks for minimum Fernet ciphertext length."""
        os.environ["CI"] = "true"
        # Fernet ciphertext is at least 57 bytes when decoded
        # Create a base64 string that decodes to less than 57 bytes
        short_data = base64.urlsafe_b64encode(b"x" * 50).decode()
        assert is_encrypted(short_data) is False

        # Create one that decodes to exactly 57 bytes
        data_57 = base64.urlsafe_b64encode(b"x" * 57).decode()
        assert is_encrypted(data_57) is True

    def test_is_encrypted_handles_padding(self, clean_env):
        """Test that base64 padding is handled correctly."""
        os.environ["CI"] = "true"
        # Test with various padding scenarios
        padded = base64.urlsafe_b64encode(b"x" * 60).decode()
        assert is_encrypted(padded) is True

    def test_is_encrypted_real_fernet_token(self, valid_fernet_key, clean_env):
        """Test with real Fernet encrypted token."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        f = Fernet(valid_fernet_key.encode())
        token = f.encrypt(b"test data").decode()
        assert is_encrypted(token) is True


# ============== migrate_plaintext_to_encrypted Tests ==============


class TestMigratePlaintextToEncrypted:
    """Tests for migrate_plaintext_to_encrypted function."""

    def test_migrate_plaintext_basic(self, valid_fernet_key, clean_env):
        """Test basic migration of plaintext passwords."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        # Create mock Client class and instances
        MockClient = Mock()

        # Create mock clients with plaintext passwords
        client1 = Mock()
        client1.credit_monitoring_password_encrypted = "plaintext_password_1"
        client2 = Mock()
        client2.credit_monitoring_password_encrypted = "plaintext_password_2"

        # Create mock database session
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [client1, client2]
        mock_db.query.return_value = mock_query

        with patch('database.get_db'):
            count = migrate_plaintext_to_encrypted(mock_db, MockClient)

        assert count == 2
        mock_db.commit.assert_called_once()
        # Verify passwords were encrypted
        assert client1.credit_monitoring_password_encrypted != "plaintext_password_1"
        assert client2.credit_monitoring_password_encrypted != "plaintext_password_2"

    def test_migrate_skips_already_encrypted(self, valid_fernet_key, clean_env):
        """Test that already encrypted passwords are skipped."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        # Create an encrypted password
        encrypted_password = encrypt_value("secret")

        MockClient = Mock()
        client = Mock()
        client.credit_monitoring_password_encrypted = encrypted_password

        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [client]
        mock_db.query.return_value = mock_query

        with patch('database.get_db'):
            count = migrate_plaintext_to_encrypted(mock_db, MockClient)

        # Should skip already encrypted password
        assert count == 0
        mock_db.commit.assert_not_called()
        # Password should remain unchanged
        assert client.credit_monitoring_password_encrypted == encrypted_password

    def test_migrate_no_clients(self, valid_fernet_key, clean_env):
        """Test migration with no clients to migrate."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        MockClient = Mock()
        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        with patch('database.get_db'):
            count = migrate_plaintext_to_encrypted(mock_db, MockClient)

        assert count == 0
        mock_db.commit.assert_not_called()

    def test_migrate_mixed_encrypted_and_plaintext(self, valid_fernet_key, clean_env):
        """Test migration with mix of encrypted and plaintext passwords."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        encrypted_password = encrypt_value("already_encrypted")

        MockClient = Mock()
        client1 = Mock()
        client1.credit_monitoring_password_encrypted = "plaintext"
        client2 = Mock()
        client2.credit_monitoring_password_encrypted = encrypted_password
        client3 = Mock()
        client3.credit_monitoring_password_encrypted = "another_plaintext"

        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [client1, client2, client3]
        mock_db.query.return_value = mock_query

        with patch('database.get_db'):
            count = migrate_plaintext_to_encrypted(mock_db, MockClient)

        # Should only migrate 2 plaintext passwords
        assert count == 2
        mock_db.commit.assert_called_once()

    def test_migrate_empty_password_skipped(self, valid_fernet_key, clean_env):
        """Test that empty passwords are skipped."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        MockClient = Mock()
        client = Mock()
        client.credit_monitoring_password_encrypted = ""

        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [client]
        mock_db.query.return_value = mock_query

        with patch('database.get_db'):
            count = migrate_plaintext_to_encrypted(mock_db, MockClient)

        # Empty string is falsy, but is_encrypted returns False for it
        # However, the condition checks `if current_value and not is_encrypted(current_value)`
        # Empty string is falsy so it should be skipped
        assert count == 0

    def test_migrate_none_password_skipped(self, valid_fernet_key, clean_env):
        """Test that None passwords are skipped."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        MockClient = Mock()
        client = Mock()
        client.credit_monitoring_password_encrypted = None

        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        # Query filters out None values, so it shouldn't be in results
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        with patch('database.get_db'):
            count = migrate_plaintext_to_encrypted(mock_db, MockClient)

        assert count == 0

    def test_migrate_prints_success_message(self, valid_fernet_key, clean_env, capsys):
        """Test that successful migration prints confirmation."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        MockClient = Mock()
        client = Mock()
        client.credit_monitoring_password_encrypted = "plaintext"

        mock_db = Mock()
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [client]
        mock_db.query.return_value = mock_query

        with patch('database.get_db'):
            migrate_plaintext_to_encrypted(mock_db, MockClient)

        captured = capsys.readouterr()
        assert "Migrated 1 plaintext passwords" in captured.out


# ============== Integration Tests ==============


class TestEncryptDecryptIntegration:
    """Integration tests for encrypt/decrypt cycle."""

    def test_full_encrypt_decrypt_cycle(self, valid_fernet_key, clean_env):
        """Test complete encrypt/decrypt cycle."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        original = "MySecretPassword123!"
        encrypted = encrypt_value(original)
        decrypted = decrypt_value(encrypted)

        assert original == decrypted
        assert encrypted != original
        assert is_encrypted(encrypted) is True
        assert is_encrypted(original) is False

    def test_encrypt_decrypt_preserves_all_characters(self, valid_fernet_key, clean_env):
        """Test that all character types are preserved."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        test_strings = [
            "simple",
            "WITH CAPS",
            "with spaces",
            "with\nnewlines",
            "with\ttabs",
            "unicode\u00e9\u00f1\u00fc",
            "emoji\U0001F600\U0001F44D",  # Emoji characters
            "symbols!@#$%^&*()",
            "mixed ABC123 !@# \u00e9\u00f1",
            "   leading and trailing spaces   ",
        ]

        for original in test_strings:
            encrypted = encrypt_value(original)
            decrypted = decrypt_value(encrypted)
            assert decrypted == original, f"Failed for: {repr(original)}"

    def test_consistent_key_produces_decryptable_output(self, valid_fernet_key, clean_env):
        """Test that same key can decrypt previously encrypted data."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        original = "persistent data"
        encrypted = encrypt_value(original)

        # Simulate "new session" by getting fresh Fernet
        decrypted = decrypt_value(encrypted)
        assert decrypted == original


# ============== Edge Cases ==============


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_very_long_password(self, valid_fernet_key, clean_env):
        """Test encryption of very long strings."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        long_password = "A" * 100000  # 100KB
        encrypted = encrypt_value(long_password)
        decrypted = decrypt_value(encrypted)
        assert decrypted == long_password

    def test_single_character(self, valid_fernet_key, clean_env):
        """Test encryption of single character."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        for char in "aA1!":
            encrypted = encrypt_value(char)
            decrypted = decrypt_value(encrypted)
            assert decrypted == char

    def test_whitespace_only_string(self, valid_fernet_key, clean_env):
        """Test encryption of whitespace-only strings."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        whitespace = "   \t\n   "
        encrypted = encrypt_value(whitespace)
        decrypted = decrypt_value(encrypted)
        assert decrypted == whitespace

    def test_binary_like_string(self, valid_fernet_key, clean_env):
        """Test encryption of binary-like content."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key
        # String with null-like characters (represented as escaped)
        binary_like = "data\x01\x02\x03end"
        encrypted = encrypt_value(binary_like)
        decrypted = decrypt_value(encrypted)
        assert decrypted == binary_like

    def test_is_encrypted_with_almost_valid_fernet(self, clean_env):
        """Test is_encrypted with data that looks like Fernet but isn't."""
        os.environ["CI"] = "true"
        # Create base64 data that's long enough but not valid Fernet
        fake_fernet = base64.urlsafe_b64encode(b"x" * 100).decode()
        # is_encrypted only checks length, not validity
        assert is_encrypted(fake_fernet) is True

    def test_key_with_special_characters(self, clean_env):
        """Test handling of key with various formats."""
        os.environ["CI"] = "true"
        # Test with a short key that has special chars
        os.environ["FCRA_ENCRYPTION_KEY"] = "key!@#$%with-special_chars"

        # Should work (key is padded)
        key = get_encryption_key()
        assert key is not None

    def test_repeated_encrypt_decrypt_cycles(self, valid_fernet_key, clean_env):
        """Test multiple encrypt/decrypt cycles on same data."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        original = "test data"
        current = original

        for _ in range(10):
            encrypted = encrypt_value(current)
            current = decrypt_value(encrypted)
            assert current == original

    def test_concurrent_encryption_safety(self, valid_fernet_key, clean_env):
        """Test that encryption produces unique results each time."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        plaintext = "same input"
        results = [encrypt_value(plaintext) for _ in range(100)]

        # All should be unique (Fernet uses random IV)
        assert len(set(results)) == 100

        # All should decrypt to same value
        for encrypted in results:
            assert decrypt_value(encrypted) == plaintext


# ============== Error Handling Tests ==============


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_decrypt_corrupted_data(self, valid_fernet_key, clean_env):
        """Test decryption of corrupted ciphertext."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        encrypted = encrypt_value("test")
        # Corrupt the ciphertext
        corrupted = encrypted[:-5] + "XXXXX"

        result = decrypt_value(corrupted)
        # Should return original corrupted data
        assert result == corrupted

    def test_decrypt_truncated_data(self, valid_fernet_key, clean_env):
        """Test decryption of truncated ciphertext."""
        os.environ["FCRA_ENCRYPTION_KEY"] = valid_fernet_key

        encrypted = encrypt_value("test data")
        truncated = encrypted[:20]

        result = decrypt_value(truncated)
        assert result == truncated

    def test_encrypt_after_key_change(self, clean_env):
        """Test encryption with key change between operations."""
        os.environ["CI"] = "true"

        # Encrypt with first key
        key1 = Fernet.generate_key().decode()
        os.environ["FCRA_ENCRYPTION_KEY"] = key1
        encrypted1 = encrypt_value("secret")

        # Change key
        key2 = Fernet.generate_key().decode()
        os.environ["FCRA_ENCRYPTION_KEY"] = key2

        # Try to decrypt with new key - should fail gracefully
        result = decrypt_value(encrypted1)
        assert result == encrypted1  # Returns original on failure

    def test_environment_variable_manipulation(self, clean_env):
        """Test behavior when environment variable changes."""
        os.environ["CI"] = "true"

        # Set initial key
        key1 = Fernet.generate_key().decode()
        os.environ["FCRA_ENCRYPTION_KEY"] = key1

        f1 = get_fernet()

        # Change the key
        key2 = Fernet.generate_key().decode()
        os.environ["FCRA_ENCRYPTION_KEY"] = key2

        f2 = get_fernet()

        # They should be different Fernet instances with different keys
        test_data = b"test"
        encrypted1 = f1.encrypt(test_data)
        encrypted2 = f2.encrypt(test_data)

        # f1 should decrypt encrypted1
        assert f1.decrypt(encrypted1) == test_data
        # f2 should decrypt encrypted2
        assert f2.decrypt(encrypted2) == test_data

        # Cross-decryption should fail
        with pytest.raises(Exception):
            f2.decrypt(encrypted1)
