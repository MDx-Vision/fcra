"""
Gmail SMTP Email Service for Brightpath Ascend FCRA Platform
Uses Gmail SMTP for transactional emails (replaces SendGrid)
"""

import base64
import os
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

DEFAULT_FROM_EMAIL = "support@brightpathascendgroup.com"
DEFAULT_FROM_NAME = "Brightpath Ascend Group"

# Gmail SMTP settings
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587  # TLS


def get_gmail_credentials():
    """Get Gmail credentials from environment."""
    user = os.environ.get("GMAIL_USER")
    password = os.environ.get("GMAIL_APP_PASSWORD")
    return user, password


def get_from_email():
    """Get the configured from email address."""
    # Use GMAIL_USER as default, fall back to configured FROM_EMAIL
    gmail_user = os.environ.get("GMAIL_USER")
    return os.environ.get("EMAIL_FROM_ADDRESS", gmail_user or DEFAULT_FROM_EMAIL)


def get_from_name():
    """Get the configured from name."""
    return os.environ.get("EMAIL_FROM_NAME", DEFAULT_FROM_NAME)


def is_email_configured():
    """
    Check if email (Gmail) is configured.
    Returns True if credentials are set, False otherwise.
    """
    user, password = get_gmail_credentials()
    return bool(user and password)


# Backward compatibility alias
def is_sendgrid_configured():
    """Legacy alias - checks if email is configured."""
    return is_email_configured()


def send_email(
    to_email,
    subject,
    html_content,
    plain_content=None,
    from_email=None,
    from_name=None,
    attachments=None,
):
    """
    Send a single email via Gmail SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body content
        plain_content: Optional plain text content (auto-generated if not provided)
        from_email: Optional sender email (defaults to configured)
        from_name: Optional sender name (defaults to configured)
        attachments: Optional list of dicts with 'content', 'filename', 'type' keys
                    (content should be base64-encoded string)

    Returns:
        dict with 'success', 'message_id', 'error' keys
    """
    try:
        if not to_email:
            return {
                "success": False,
                "message_id": None,
                "error": "No recipient email provided",
            }

        gmail_user, gmail_password = get_gmail_credentials()
        if not gmail_user or not gmail_password:
            return {
                "success": False,
                "message_id": None,
                "error": "Gmail not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD environment variables.",
            }

        if from_email is None:
            from_email = get_from_email()
        if from_name is None:
            from_name = get_from_name()

        # Auto-generate plain text from HTML if not provided
        if plain_content is None:
            import re
            plain_content = re.sub(r"<[^>]+>", "", html_content)

        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email

        # Attach plain text and HTML parts
        part1 = MIMEText(plain_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)

        # Handle attachments
        if attachments:
            # Convert to mixed multipart if we have attachments
            msg_with_attachments = MIMEMultipart("mixed")
            msg_with_attachments["Subject"] = msg["Subject"]
            msg_with_attachments["From"] = msg["From"]
            msg_with_attachments["To"] = msg["To"]

            # Add the alternative part (plain + html)
            msg_with_attachments.attach(msg)

            for att in attachments:
                content = att.get("content", "")
                filename = att.get("filename", "attachment")
                file_type = att.get("type", "application/octet-stream")

                # Decode base64 content
                if content:
                    try:
                        file_data = base64.b64decode(content)
                    except Exception:
                        file_data = content.encode() if isinstance(content, str) else content

                    attachment = MIMEApplication(file_data)
                    attachment.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=filename
                    )
                    attachment.add_header("Content-Type", file_type)
                    msg_with_attachments.attach(attachment)

            msg = msg_with_attachments

        # Send via Gmail SMTP
        context = ssl.create_default_context()
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(gmail_user, gmail_password)
            server.sendmail(from_email, to_email, msg.as_string())

        # Generate a pseudo message ID (Gmail doesn't return one via SMTP)
        import uuid
        message_id = f"gmail-{uuid.uuid4().hex[:16]}"

        return {
            "success": True,
            "message_id": message_id,
            "status_code": 200,
            "error": None,
        }

    except smtplib.SMTPAuthenticationError as e:
        return {
            "success": False,
            "message_id": None,
            "error": f"Gmail authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD: {str(e)}",
        }
    except smtplib.SMTPException as e:
        return {
            "success": False,
            "message_id": None,
            "error": f"SMTP error: {str(e)}",
        }
    except Exception as e:
        return {"success": False, "message_id": None, "error": str(e)}


def send_bulk_email(recipients, subject, html_content, plain_content=None):
    """
    Send email to multiple recipients.

    Args:
        recipients: List of email addresses
        subject: Email subject
        html_content: HTML body
        plain_content: Optional plain text body

    Returns:
        dict with 'total', 'sent', 'failed', 'results' keys
    """
    results = []
    sent_count = 0
    failed_count = 0

    for email in recipients:
        result = send_email(email, subject, html_content, plain_content)
        results.append(
            {
                "email": email,
                "success": result["success"],
                "message_id": result.get("message_id"),
                "error": result.get("error"),
            }
        )

        if result["success"]:
            sent_count += 1
        else:
            failed_count += 1

    return {
        "total": len(recipients),
        "sent": sent_count,
        "failed": failed_count,
        "results": results,
    }


def send_email_with_pdf(to_email, subject, html_content, pdf_path, pdf_filename=None):
    """
    Send email with a PDF attachment.

    Args:
        to_email: Recipient email
        subject: Email subject
        html_content: HTML body
        pdf_path: Path to PDF file
        pdf_filename: Optional filename for attachment

    Returns:
        dict with result info
    """
    try:
        with open(pdf_path, "rb") as f:
            pdf_content = base64.b64encode(f.read()).decode()

        if pdf_filename is None:
            pdf_filename = os.path.basename(pdf_path)

        attachments = [
            {
                "content": pdf_content,
                "filename": pdf_filename,
                "type": "application/pdf",
            }
        ]

        return send_email(to_email, subject, html_content, attachments=attachments)

    except Exception as e:
        return {
            "success": False,
            "message_id": None,
            "error": f"Error attaching PDF: {str(e)}",
        }


# Legacy SendGrid compatibility functions (for gradual migration)
def get_sendgrid_api_key():
    """Legacy function - returns empty string (no longer used)."""
    return ""


def get_sendgrid_client():
    """Legacy function - raises error (no longer used)."""
    raise NotImplementedError("SendGrid has been replaced with Gmail SMTP. Use send_email() directly.")
