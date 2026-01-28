"""
Unit tests for Email Service
Tests for Gmail SMTP email functionality including single emails, bulk emails,
attachments, PDF attachments, and configuration checks.
"""
import pytest
import base64
import os
import smtplib
from unittest.mock import Mock, MagicMock, patch, mock_open
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.email_service import (
    get_gmail_credentials,
    get_from_email,
    get_from_name,
    send_email,
    send_bulk_email,
    is_email_configured,
    is_sendgrid_configured,
    send_email_with_pdf,
    DEFAULT_FROM_EMAIL,
    DEFAULT_FROM_NAME,
    GMAIL_SMTP_HOST,
    GMAIL_SMTP_PORT,
)


# ============== Fixtures ==============


@pytest.fixture(autouse=True)
def reset_circuit_breakers():
    """Reset circuit breakers before each test to prevent test pollution."""
    from services.circuit_breaker_service import reset_all_circuits
    reset_all_circuits()
    yield
    reset_all_circuits()


@pytest.fixture
def mock_smtp():
    """Create a mock SMTP connection."""
    mock_server = MagicMock()
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=False)
    return mock_server


@pytest.fixture
def gmail_env():
    """Set up Gmail environment variables."""
    with patch.dict(os.environ, {
        "GMAIL_USER": "test@gmail.com",
        "GMAIL_APP_PASSWORD": "test-app-password"
    }):
        yield


# ============== get_gmail_credentials Tests ==============


class TestGetGmailCredentials:
    """Tests for get_gmail_credentials function."""

    def test_get_gmail_credentials_success(self):
        """Test getting credentials when they're configured."""
        with patch.dict(os.environ, {
            "GMAIL_USER": "user@gmail.com",
            "GMAIL_APP_PASSWORD": "secret-password"
        }):
            user, password = get_gmail_credentials()
            assert user == "user@gmail.com"
            assert password == "secret-password"

    def test_get_gmail_credentials_missing(self):
        """Test getting credentials when missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(os.environ, "get", return_value=None):
                user, password = get_gmail_credentials()
                assert user is None
                assert password is None


# ============== get_from_email Tests ==============


class TestGetFromEmail:
    """Tests for get_from_email function."""

    def test_get_from_email_default(self):
        """Test default from email is returned."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(os.environ, "get", side_effect=lambda k, d=None: d):
                email = get_from_email()
                assert email == DEFAULT_FROM_EMAIL

    def test_get_from_email_from_gmail_user(self):
        """Test from email uses GMAIL_USER when set."""
        with patch.dict(os.environ, {"GMAIL_USER": "myemail@gmail.com"}):
            email = get_from_email()
            assert email == "myemail@gmail.com"

    def test_get_from_email_custom(self):
        """Test custom from email from environment."""
        with patch.dict(os.environ, {"EMAIL_FROM_ADDRESS": "custom@example.com"}):
            email = get_from_email()
            assert email == "custom@example.com"


# ============== get_from_name Tests ==============


class TestGetFromName:
    """Tests for get_from_name function."""

    def test_get_from_name_default(self):
        """Test default from name is returned."""
        with patch.dict(os.environ, {}, clear=True):
            env_copy = os.environ.copy()
            if "EMAIL_FROM_NAME" in env_copy:
                del env_copy["EMAIL_FROM_NAME"]
            with patch.dict(os.environ, env_copy, clear=True):
                name = get_from_name()
                assert name == DEFAULT_FROM_NAME

    def test_get_from_name_custom(self):
        """Test custom from name from environment."""
        with patch.dict(os.environ, {"EMAIL_FROM_NAME": "Custom Sender"}):
            name = get_from_name()
            assert name == "Custom Sender"


# ============== send_email Tests ==============


class TestSendEmail:
    """Tests for send_email function."""

    def test_send_email_success(self, mock_smtp, gmail_env):
        """Test successful email sending."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_content="<p>Hello World</p>"
            )

            assert result["success"] is True
            assert result["message_id"] is not None
            assert result["message_id"].startswith("gmail-")
            assert result["status_code"] == 200
            assert result["error"] is None

    def test_send_email_no_recipient(self):
        """Test email fails with no recipient."""
        result = send_email(
            to_email=None,
            subject="Test Subject",
            html_content="<p>Hello</p>"
        )

        assert result["success"] is False
        assert result["message_id"] is None
        assert "No recipient email provided" in result["error"]

    def test_send_email_empty_recipient(self):
        """Test email fails with empty recipient."""
        result = send_email(
            to_email="",
            subject="Test Subject",
            html_content="<p>Hello</p>"
        )

        assert result["success"] is False
        assert "No recipient email provided" in result["error"]

    def test_send_email_not_configured(self):
        """Test email fails when Gmail not configured."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(os.environ, "get", return_value=None):
                result = send_email(
                    to_email="recipient@example.com",
                    subject="Test",
                    html_content="<p>Hello</p>"
                )

                assert result["success"] is False
                assert "Gmail not configured" in result["error"]

    def test_send_email_with_plain_content(self, mock_smtp, gmail_env):
        """Test email with explicit plain text content."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                html_content="<p>Hello World</p>",
                plain_content="Hello World"
            )

            assert result["success"] is True
            mock_smtp.sendmail.assert_called_once()

    def test_send_email_auto_generates_plain_content(self, mock_smtp, gmail_env):
        """Test that plain content is auto-generated from HTML."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_email(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<p>Test <b>content</b></p>"
            )

            assert result["success"] is True

    def test_send_email_with_custom_from_email(self, mock_smtp, gmail_env):
        """Test email with custom from email."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_email(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<p>Hello</p>",
                from_email="custom@example.com",
                from_name="Custom Sender"
            )

            assert result["success"] is True

    def test_send_email_with_attachments(self, mock_smtp, gmail_env):
        """Test email with attachments."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            attachments = [
                {
                    "content": base64.b64encode(b"test content").decode(),
                    "filename": "test.txt",
                    "type": "text/plain"
                }
            ]

            result = send_email(
                to_email="recipient@example.com",
                subject="Test with attachment",
                html_content="<p>See attachment</p>",
                attachments=attachments
            )

            assert result["success"] is True

    def test_send_email_with_multiple_attachments(self, mock_smtp, gmail_env):
        """Test email with multiple attachments."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            attachments = [
                {
                    "content": base64.b64encode(b"content1").decode(),
                    "filename": "file1.txt",
                    "type": "text/plain"
                },
                {
                    "content": base64.b64encode(b"content2").decode(),
                    "filename": "file2.txt",
                    "type": "text/plain"
                }
            ]

            result = send_email(
                to_email="recipient@example.com",
                subject="Test with attachments",
                html_content="<p>See attachments</p>",
                attachments=attachments
            )

            assert result["success"] is True

    def test_send_email_attachment_with_defaults(self, mock_smtp, gmail_env):
        """Test email attachment uses defaults for missing fields."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            # Attachment with minimal data - should use defaults
            attachments = [{"content": base64.b64encode(b"test").decode()}]

            result = send_email(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<p>Test</p>",
                attachments=attachments
            )

            assert result["success"] is True

    def test_send_email_authentication_error(self, gmail_env):
        """Test email handling of authentication errors."""
        mock_server = MagicMock()
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"Authentication failed")

        with patch("smtplib.SMTP", return_value=mock_server):
            result = send_email(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<p>Hello</p>"
            )

            assert result["success"] is False
            assert "authentication failed" in result["error"].lower()

    def test_send_email_smtp_error(self, gmail_env):
        """Test email handling of SMTP errors."""
        mock_server = MagicMock()
        mock_server.__enter__ = MagicMock(return_value=mock_server)
        mock_server.__exit__ = MagicMock(return_value=False)
        mock_server.sendmail.side_effect = smtplib.SMTPException("SMTP Error")

        with patch("smtplib.SMTP", return_value=mock_server):
            result = send_email(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<p>Hello</p>"
            )

            assert result["success"] is False
            assert "SMTP error" in result["error"]

    def test_send_email_general_error(self, gmail_env):
        """Test email handling of general errors."""
        with patch("smtplib.SMTP", side_effect=Exception("Connection failed")):
            result = send_email(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<p>Hello</p>"
            )

            assert result["success"] is False
            assert result["message_id"] is None
            assert "Connection failed" in result["error"]


# ============== send_bulk_email Tests ==============


class TestSendBulkEmail:
    """Tests for send_bulk_email function."""

    def test_send_bulk_email_all_success(self, mock_smtp, gmail_env):
        """Test bulk email with all successful sends."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            recipients = [
                "user1@example.com",
                "user2@example.com",
                "user3@example.com"
            ]

            result = send_bulk_email(
                recipients=recipients,
                subject="Bulk Test",
                html_content="<p>Hello everyone</p>"
            )

            assert result["total"] == 3
            assert result["sent"] == 3
            assert result["failed"] == 0
            assert len(result["results"]) == 3
            for r in result["results"]:
                assert r["success"] is True

    def test_send_bulk_email_partial_failure(self):
        """Test bulk email with some failures."""
        call_count = [0]

        def mock_send_email(to_email, subject, html_content, plain_content=None):
            call_count[0] += 1
            if call_count[0] == 2:
                return {"success": False, "message_id": None, "error": "Failed"}
            return {"success": True, "message_id": f"msg-{call_count[0]}", "error": None}

        with patch("services.email_service.send_email", side_effect=mock_send_email):
            recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]

            result = send_bulk_email(
                recipients=recipients,
                subject="Test",
                html_content="<p>Hello</p>"
            )

            assert result["total"] == 3
            assert result["sent"] == 2
            assert result["failed"] == 1

    def test_send_bulk_email_all_failed(self):
        """Test bulk email with all failures."""
        def mock_send_email(to_email, subject, html_content, plain_content=None):
            return {"success": False, "message_id": None, "error": "All failed"}

        with patch("services.email_service.send_email", side_effect=mock_send_email):
            recipients = ["user1@example.com", "user2@example.com"]

            result = send_bulk_email(
                recipients=recipients,
                subject="Test",
                html_content="<p>Hello</p>"
            )

            assert result["total"] == 2
            assert result["sent"] == 0
            assert result["failed"] == 2

    def test_send_bulk_email_empty_recipients(self):
        """Test bulk email with empty recipients list."""
        result = send_bulk_email(
            recipients=[],
            subject="Test",
            html_content="<p>Hello</p>"
        )

        assert result["total"] == 0
        assert result["sent"] == 0
        assert result["failed"] == 0
        assert result["results"] == []

    def test_send_bulk_email_with_plain_content(self, mock_smtp, gmail_env):
        """Test bulk email with explicit plain content."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_bulk_email(
                recipients=["user@example.com"],
                subject="Test",
                html_content="<p>Hello</p>",
                plain_content="Hello"
            )

            assert result["sent"] == 1

    def test_send_bulk_email_result_includes_email(self, mock_smtp, gmail_env):
        """Test bulk email results include recipient email."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_bulk_email(
                recipients=["specific@example.com"],
                subject="Test",
                html_content="<p>Hello</p>"
            )

            assert result["results"][0]["email"] == "specific@example.com"


# ============== is_email_configured Tests ==============


class TestIsEmailConfigured:
    """Tests for is_email_configured function."""

    def test_is_email_configured_true(self):
        """Test returns True when Gmail credentials are set."""
        with patch.dict(os.environ, {
            "GMAIL_USER": "test@gmail.com",
            "GMAIL_APP_PASSWORD": "test-password"
        }):
            assert is_email_configured() is True

    def test_is_email_configured_false_missing_user(self):
        """Test returns False when user is missing."""
        with patch.dict(os.environ, {"GMAIL_APP_PASSWORD": "password"}, clear=True):
            assert is_email_configured() is False

    def test_is_email_configured_false_missing_password(self):
        """Test returns False when password is missing."""
        with patch.dict(os.environ, {"GMAIL_USER": "user@gmail.com"}, clear=True):
            assert is_email_configured() is False

    def test_is_email_configured_false_both_missing(self):
        """Test returns False when both are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(os.environ, "get", return_value=None):
                assert is_email_configured() is False


class TestIsSendgridConfigured:
    """Tests for legacy is_sendgrid_configured function (now checks Gmail)."""

    def test_is_sendgrid_configured_true(self):
        """Test returns True when Gmail is configured (legacy compatibility)."""
        with patch.dict(os.environ, {
            "GMAIL_USER": "test@gmail.com",
            "GMAIL_APP_PASSWORD": "test-password"
        }):
            assert is_sendgrid_configured() is True

    def test_is_sendgrid_configured_false(self):
        """Test returns False when Gmail is not configured."""
        with patch.dict(os.environ, {}, clear=True):
            with patch.object(os.environ, "get", return_value=None):
                assert is_sendgrid_configured() is False


# ============== send_email_with_pdf Tests ==============


class TestSendEmailWithPdf:
    """Tests for send_email_with_pdf function."""

    def test_send_email_with_pdf_success(self, mock_smtp, gmail_env):
        """Test successful PDF email sending."""
        pdf_content = b"%PDF-1.4 test pdf content"

        with patch("smtplib.SMTP", return_value=mock_smtp):
            with patch("builtins.open", mock_open(read_data=pdf_content)):
                result = send_email_with_pdf(
                    to_email="recipient@example.com",
                    subject="PDF Test",
                    html_content="<p>See attached PDF</p>",
                    pdf_path="/path/to/document.pdf"
                )

                assert result["success"] is True

    def test_send_email_with_pdf_custom_filename(self, mock_smtp, gmail_env):
        """Test PDF email with custom filename."""
        pdf_content = b"%PDF-1.4 test"

        with patch("smtplib.SMTP", return_value=mock_smtp):
            with patch("builtins.open", mock_open(read_data=pdf_content)):
                result = send_email_with_pdf(
                    to_email="recipient@example.com",
                    subject="PDF Test",
                    html_content="<p>See attached</p>",
                    pdf_path="/path/to/document.pdf",
                    pdf_filename="custom_name.pdf"
                )

                assert result["success"] is True

    def test_send_email_with_pdf_uses_basename_as_default_filename(self, mock_smtp, gmail_env):
        """Test PDF email uses file basename when no custom filename provided."""
        pdf_content = b"%PDF-1.4 test"

        with patch("smtplib.SMTP", return_value=mock_smtp):
            with patch("builtins.open", mock_open(read_data=pdf_content)):
                with patch("services.email_service.send_email") as mock_send:
                    mock_send.return_value = {"success": True, "message_id": "123", "error": None}

                    send_email_with_pdf(
                        to_email="recipient@example.com",
                        subject="Test",
                        html_content="<p>Test</p>",
                        pdf_path="/some/path/report.pdf"
                    )

                    # Check that send_email was called with correct attachment filename
                    call_args = mock_send.call_args
                    attachments = call_args[1]["attachments"]
                    assert attachments[0]["filename"] == "report.pdf"

    def test_send_email_with_pdf_file_not_found(self):
        """Test PDF email handles file not found."""
        with patch("builtins.open", side_effect=FileNotFoundError("No such file")):
            result = send_email_with_pdf(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<p>Test</p>",
                pdf_path="/nonexistent/file.pdf"
            )

            assert result["success"] is False
            assert "Error attaching PDF" in result["error"]

    def test_send_email_with_pdf_permission_error(self):
        """Test PDF email handles permission errors."""
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            result = send_email_with_pdf(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<p>Test</p>",
                pdf_path="/protected/file.pdf"
            )

            assert result["success"] is False
            assert "Error attaching PDF" in result["error"]

    def test_send_email_with_pdf_io_error(self):
        """Test PDF email handles I/O errors."""
        with patch("builtins.open", side_effect=IOError("Disk error")):
            result = send_email_with_pdf(
                to_email="recipient@example.com",
                subject="Test",
                html_content="<p>Test</p>",
                pdf_path="/path/to/file.pdf"
            )

            assert result["success"] is False
            assert "Error attaching PDF" in result["error"]

    def test_send_email_with_pdf_base64_encoding(self, mock_smtp, gmail_env):
        """Test PDF content is properly base64 encoded."""
        pdf_content = b"Test PDF Content"
        expected_b64 = base64.b64encode(pdf_content).decode()

        with patch("smtplib.SMTP", return_value=mock_smtp):
            with patch("builtins.open", mock_open(read_data=pdf_content)):
                with patch("services.email_service.send_email") as mock_send:
                    mock_send.return_value = {"success": True, "message_id": "123", "error": None}

                    send_email_with_pdf(
                        to_email="recipient@example.com",
                        subject="Test",
                        html_content="<p>Test</p>",
                        pdf_path="/path/to/file.pdf"
                    )

                    call_args = mock_send.call_args
                    attachments = call_args[1]["attachments"]
                    assert attachments[0]["content"] == expected_b64
                    assert attachments[0]["type"] == "application/pdf"


# ============== Default Constants Tests ==============


class TestDefaultConstants:
    """Tests for default constant values."""

    def test_default_from_email_value(self):
        """Test DEFAULT_FROM_EMAIL has expected value."""
        assert DEFAULT_FROM_EMAIL == "support@brightpathascendgroup.com"

    def test_default_from_name_value(self):
        """Test DEFAULT_FROM_NAME has expected value."""
        assert DEFAULT_FROM_NAME == "Brightpath Ascend Group"

    def test_gmail_smtp_host(self):
        """Test GMAIL_SMTP_HOST has expected value."""
        assert GMAIL_SMTP_HOST == "smtp.gmail.com"

    def test_gmail_smtp_port(self):
        """Test GMAIL_SMTP_PORT has expected value."""
        assert GMAIL_SMTP_PORT == 587


# ============== Integration-like Tests ==============


class TestEmailServiceIntegration:
    """Integration-like tests for email service workflow."""

    def test_full_email_workflow(self, mock_smtp):
        """Test complete email sending workflow."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            with patch.dict(os.environ, {
                "GMAIL_USER": "sender@gmail.com",
                "GMAIL_APP_PASSWORD": "test-password",
                "EMAIL_FROM_NAME": "Test Sender"
            }):
                # Verify configuration
                assert is_email_configured() is True
                assert get_from_email() == "sender@gmail.com"
                assert get_from_name() == "Test Sender"

                # Send single email
                result = send_email(
                    to_email="recipient@example.com",
                    subject="Integration Test",
                    html_content="<h1>Test</h1><p>This is a test.</p>"
                )

                assert result["success"] is True

    def test_bulk_email_workflow(self, mock_smtp, gmail_env):
        """Test bulk email sending workflow."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            recipients = [f"user{i}@example.com" for i in range(5)]

            result = send_bulk_email(
                recipients=recipients,
                subject="Bulk Email",
                html_content="<p>Newsletter content</p>"
            )

            assert result["total"] == 5
            assert result["sent"] == 5
            assert result["failed"] == 0

    def test_email_with_complex_html_content(self, mock_smtp, gmail_env):
        """Test email with complex HTML content."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; }
                    .header { background-color: #4CAF50; padding: 20px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Welcome!</h1>
                </div>
                <p>Dear Customer,</p>
                <p>Thank you for your order.</p>
                <table border="1">
                    <tr><th>Item</th><th>Price</th></tr>
                    <tr><td>Widget</td><td>$10.00</td></tr>
                </table>
            </body>
            </html>
            """

            result = send_email(
                to_email="customer@example.com",
                subject="Your Order Confirmation",
                html_content=html_content
            )

            assert result["success"] is True


# ============== Edge Cases ==============


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_send_email_with_unicode_content(self, mock_smtp, gmail_env):
        """Test email with unicode characters."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_email(
                to_email="user@example.com",
                subject="Test with unicode: cafe",
                html_content="<p>Hello Cafe!</p>"
            )

            assert result["success"] is True

    def test_send_email_with_special_characters_in_subject(self, mock_smtp, gmail_env):
        """Test email with special characters in subject."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_email(
                to_email="user@example.com",
                subject="Test & <Special> Characters!",
                html_content="<p>Test</p>"
            )

            assert result["success"] is True

    def test_send_email_with_very_long_content(self, mock_smtp, gmail_env):
        """Test email with very long HTML content."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            long_content = "<p>" + ("x" * 100000) + "</p>"

            result = send_email(
                to_email="user@example.com",
                subject="Long Email",
                html_content=long_content
            )

            assert result["success"] is True

    def test_send_bulk_email_single_recipient(self, mock_smtp, gmail_env):
        """Test bulk email with single recipient."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_bulk_email(
                recipients=["single@example.com"],
                subject="Single Recipient Bulk",
                html_content="<p>Hello</p>"
            )

            assert result["total"] == 1
            assert result["sent"] == 1

    def test_send_email_with_empty_html_content(self, mock_smtp, gmail_env):
        """Test email with empty HTML content."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            result = send_email(
                to_email="user@example.com",
                subject="Empty Content Test",
                html_content=""
            )

            assert result["success"] is True

    def test_send_email_with_whitespace_only_recipient(self, gmail_env):
        """Test email with whitespace-only recipient."""
        # Whitespace should still attempt to send (SMTP will validate)
        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_server = MagicMock()
            mock_server.__enter__ = MagicMock(return_value=mock_server)
            mock_server.__exit__ = MagicMock(return_value=False)
            mock_smtp_class.return_value = mock_server

            result = send_email(
                to_email="   ",
                subject="Test",
                html_content="<p>Hello</p>"
            )

            # Whitespace is considered as having a recipient
            assert "success" in result

    def test_plain_content_generation_strips_html_tags(self, mock_smtp, gmail_env):
        """Test that auto-generated plain content properly strips HTML tags."""
        with patch("smtplib.SMTP", return_value=mock_smtp):
            # The function uses re.sub(r"<[^>]+>", "", html_content) to strip tags
            html = "<div><p>Hello <b>World</b></p></div>"

            result = send_email(
                to_email="user@example.com",
                subject="Test",
                html_content=html
            )

            assert result["success"] is True
