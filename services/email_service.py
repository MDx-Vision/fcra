"""
Gmail SMTP Email Service for Brightpath Ascend FCRA Platform
Uses Gmail SMTP for transactional emails (replaces SendGrid)

Includes retry logic for transient SMTP failures.
"""

import base64
import logging
import os
import smtplib
import ssl
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from services.circuit_breaker_service import CircuitBreakerError, circuit_protected
from services.retry_service import retry_email

logger = logging.getLogger(__name__)

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


@circuit_protected("email")
@retry_email(max_attempts=3)
def _smtp_send_with_retry(gmail_user, gmail_password, from_email, to_email, msg_string):
    """
    Internal function to send email via SMTP with circuit breaker and retry logic.
    Separated to allow retry on transient SMTP failures.
    """
    context = ssl.create_default_context()
    with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT) as server:
        server.starttls(context=context)
        server.login(gmail_user, gmail_password)
        server.sendmail(from_email, to_email, msg_string)


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

        # Inject email open/click tracking
        try:
            import os

            base_url = os.environ.get(
                "BASE_URL", os.environ.get("REPLIT_DEV_DOMAIN", "")
            )
            if base_url and not base_url.startswith("http"):
                base_url = f"https://{base_url}"
            if base_url:
                from services.email_tracking_service import (
                    EmailTrackingService,
                    generate_tracking_id,
                )

                _tracking_id = generate_tracking_id()
                tracker = EmailTrackingService()
                try:
                    html_content = tracker.inject_tracking(
                        html_content, _tracking_id, base_url
                    )
                finally:
                    tracker.close()
        except Exception:
            _tracking_id = None

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
                        file_data = (
                            content.encode() if isinstance(content, str) else content
                        )

                    attachment = MIMEApplication(file_data)
                    attachment.add_header(
                        "Content-Disposition", "attachment", filename=filename
                    )
                    attachment.add_header("Content-Type", file_type)
                    msg_with_attachments.attach(attachment)

            msg = msg_with_attachments

        # Send via Gmail SMTP with retry logic
        logger.debug(f"Sending email to {to_email}: {subject}")
        _smtp_send_with_retry(
            gmail_user, gmail_password, from_email, to_email, msg.as_string()
        )
        logger.info(f"Email sent successfully to {to_email}")

        # Generate a pseudo message ID (Gmail doesn't return one via SMTP)
        import uuid

        message_id = f"gmail-{uuid.uuid4().hex[:16]}"

        # Log successful email
        try:
            from services.activity_logger import log_email_sent

            log_email_sent(to_email, subject)
        except:
            pass

        return {
            "success": True,
            "message_id": message_id,
            "status_code": 200,
            "error": None,
        }

    except smtplib.SMTPAuthenticationError as e:
        # Log failed email
        try:
            from services.activity_logger import log_email_failed

            log_email_failed(to_email, f"Auth failed: {str(e)}")
        except:
            pass
        return {
            "success": False,
            "message_id": None,
            "error": f"Gmail authentication failed. Check GMAIL_USER and GMAIL_APP_PASSWORD: {str(e)}",
        }
    except smtplib.SMTPException as e:
        try:
            from services.activity_logger import log_email_failed

            log_email_failed(to_email, f"SMTP error: {str(e)}")
        except:
            pass
        return {
            "success": False,
            "message_id": None,
            "error": f"SMTP error: {str(e)}",
        }
    except Exception as e:
        try:
            from services.activity_logger import log_email_failed

            log_email_failed(to_email, str(e))
        except:
            pass
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
    raise NotImplementedError(
        "SendGrid has been replaced with Gmail SMTP. Use send_email() directly."
    )


# =============================================================================
# Partner Portal Emails
# =============================================================================


def send_partner_password_reset_email(
    email: str, reset_url: str, tenant_name: str = None
):
    """
    Send password reset email to partner portal admin.

    Args:
        email: Recipient email address
        reset_url: Password reset URL with token
        tenant_name: Optional tenant/company name for personalization
    """
    company_name = tenant_name or "Your Company"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #22c55e;">
            <h1 style="color: #1e293b; margin: 0;">Password Reset Request</h1>
        </div>

        <div style="padding: 30px 0;">
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                Hello,
            </p>
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                We received a request to reset your password for the <strong>{company_name}</strong> partner portal.
            </p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{reset_url}"
                   style="background-color: #22c55e; color: white; padding: 14px 28px; text-decoration: none;
                          border-radius: 6px; font-weight: bold; display: inline-block;">
                    Reset Password
                </a>
            </div>

            <p style="color: #64748b; font-size: 14px; line-height: 1.5;">
                This link will expire in 24 hours. If you didn't request this reset,
                you can safely ignore this email.
            </p>

            <p style="color: #64748b; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e2e8f0;">
                If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{reset_url}" style="color: #22c55e; word-break: break-all;">{reset_url}</a>
            </p>
        </div>

        <div style="text-align: center; padding-top: 20px; border-top: 1px solid #e2e8f0;">
            <p style="color: #94a3b8; font-size: 12px;">
                Brightpath Ascend Group Partner Portal
            </p>
        </div>
    </div>
    """

    return send_email(
        to_email=email,
        subject="Password Reset Request - Partner Portal",
        html_content=html_content,
    )


def send_partner_team_invitation_email(
    email: str,
    login_url: str,
    tenant_name: str,
    inviter_name: str = None,
    role: str = None,
):
    """
    Send team invitation email to new partner portal team member.

    Args:
        email: Recipient email address
        login_url: Partner portal login URL
        tenant_name: Company/tenant name
        inviter_name: Name of person who sent the invitation
        role: Role being assigned (e.g., 'admin', 'member')
    """
    role_display = role.replace("_", " ").title() if role else "Team Member"
    inviter_text = f"by {inviter_name}" if inviter_name else ""

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #22c55e;">
            <h1 style="color: #1e293b; margin: 0;">You're Invited!</h1>
        </div>

        <div style="padding: 30px 0;">
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                Hello,
            </p>
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                You've been invited {inviter_text} to join <strong>{tenant_name}</strong>
                on the Brightpath Ascend Group partner portal as a <strong>{role_display}</strong>.
            </p>

            <div style="background: #f8fafc; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h3 style="color: #1e293b; margin-top: 0;">What you can do:</h3>
                <ul style="color: #475569; line-height: 1.8;">
                    <li>View and manage your referred clients</li>
                    <li>Track commissions and payouts</li>
                    <li>Access analytics and reporting</li>
                    <li>Customize your branding settings</li>
                </ul>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{login_url}"
                   style="background-color: #22c55e; color: white; padding: 14px 28px; text-decoration: none;
                          border-radius: 6px; font-weight: bold; display: inline-block;">
                    Access Partner Portal
                </a>
            </div>

            <p style="color: #64748b; font-size: 14px; line-height: 1.5;">
                A temporary password has been set for your account. Please use the "Forgot Password"
                feature on the login page to set your own password.
            </p>
        </div>

        <div style="text-align: center; padding-top: 20px; border-top: 1px solid #e2e8f0;">
            <p style="color: #94a3b8; font-size: 12px;">
                Brightpath Ascend Group Partner Portal
            </p>
        </div>
    </div>
    """

    return send_email(
        to_email=email,
        subject=f"You've been invited to join {tenant_name} - Partner Portal",
        html_content=html_content,
    )


# =============================================================================
# Payment Notification Emails
# =============================================================================


def send_payment_failed_email(
    client_email: str,
    client_name: str,
    error_message: str = None,
    portal_url: str = None,
):
    """
    Send notification when a payment fails.

    Args:
        client_email: Client's email address
        client_name: Client's name for personalization
        error_message: Optional error details
        portal_url: URL to client portal for updating payment
    """
    first_name = client_name.split()[0] if client_name else "there"
    error_text = (
        f"<p style='color: #dc2626; font-size: 14px;'>Error: {error_message}</p>"
        if error_message
        else ""
    )
    portal_link = portal_url or "https://portal.brightpathascendgroup.com"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #dc2626;">
            <h1 style="color: #1e293b; margin: 0;">Payment Issue</h1>
        </div>

        <div style="padding: 30px 0;">
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                Hi {first_name},
            </p>
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                We were unable to process your recent payment. This may be due to
                insufficient funds, an expired card, or other issues with your payment method.
            </p>

            {error_text}

            <div style="background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <h3 style="color: #b91c1c; margin-top: 0;">What to do next:</h3>
                <ol style="color: #7f1d1d; line-height: 1.8;">
                    <li>Log in to your client portal</li>
                    <li>Go to your account settings</li>
                    <li>Update your payment method</li>
                    <li>Retry the payment</li>
                </ol>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{portal_link}"
                   style="background-color: #22c55e; color: white; padding: 14px 28px; text-decoration: none;
                          border-radius: 6px; font-weight: bold; display: inline-block;">
                    Update Payment Method
                </a>
            </div>

            <p style="color: #64748b; font-size: 14px; line-height: 1.5;">
                If you need assistance, please contact our support team.
            </p>
        </div>

        <div style="text-align: center; padding-top: 20px; border-top: 1px solid #e2e8f0;">
            <p style="color: #94a3b8; font-size: 12px;">
                Brightpath Ascend Group<br>
                <a href="mailto:support@brightpathascendgroup.com" style="color: #22c55e;">support@brightpathascendgroup.com</a>
            </p>
        </div>
    </div>
    """

    return send_email(
        to_email=client_email,
        subject="Action Required: Payment Issue - Brightpath Ascend Group",
        html_content=html_content,
    )


def send_payment_reminder_email(
    client_email: str,
    client_name: str,
    amount_due: float = None,
    due_date: str = None,
    portal_url: str = None,
):
    """
    Send reminder for upcoming payment.

    Args:
        client_email: Client's email address
        client_name: Client's name for personalization
        amount_due: Amount due
        due_date: When payment is due
        portal_url: URL to client portal
    """
    first_name = client_name.split()[0] if client_name else "there"
    amount_text = f"${amount_due:.2f}" if amount_due else "your scheduled payment"
    due_text = f" on {due_date}" if due_date else " soon"
    portal_link = portal_url or "https://portal.brightpathascendgroup.com"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #22c55e;">
            <h1 style="color: #1e293b; margin: 0;">Payment Reminder</h1>
        </div>

        <div style="padding: 30px 0;">
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                Hi {first_name},
            </p>
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                This is a friendly reminder that {amount_text} is due{due_text}.
            </p>

            <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 20px; margin: 20px 0; text-align: center;">
                <p style="color: #166534; font-size: 14px; margin: 0;">Amount Due</p>
                <p style="color: #15803d; font-size: 28px; font-weight: bold; margin: 10px 0;">{amount_text}</p>
                <p style="color: #166534; font-size: 14px; margin: 0;">Due{due_text}</p>
            </div>

            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                To ensure uninterrupted service, please make sure your payment method is up to date.
            </p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{portal_link}"
                   style="background-color: #22c55e; color: white; padding: 14px 28px; text-decoration: none;
                          border-radius: 6px; font-weight: bold; display: inline-block;">
                    View Account
                </a>
            </div>

            <p style="color: #64748b; font-size: 14px; line-height: 1.5;">
                If you have any questions about your account, please don't hesitate to reach out.
            </p>
        </div>

        <div style="text-align: center; padding-top: 20px; border-top: 1px solid #e2e8f0;">
            <p style="color: #94a3b8; font-size: 12px;">
                Brightpath Ascend Group<br>
                <a href="mailto:support@brightpathascendgroup.com" style="color: #22c55e;">support@brightpathascendgroup.com</a>
            </p>
        </div>
    </div>
    """

    return send_email(
        to_email=client_email,
        subject="Payment Reminder - Brightpath Ascend Group",
        html_content=html_content,
    )


def send_subscription_past_due_email(
    client_email: str,
    client_name: str,
    amount_due: float = None,
    portal_url: str = None,
):
    """
    Send dunning email for past-due subscription.

    Args:
        client_email: Client's email address
        client_name: Client's name for personalization
        amount_due: Amount that is past due
        portal_url: URL to billing portal
    """
    first_name = client_name.split()[0] if client_name else "there"
    amount_text = f"${amount_due:.2f}" if amount_due else "your outstanding balance"
    portal_link = portal_url or "https://portal.brightpathascendgroup.com/subscription"

    html_content = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; padding-bottom: 20px; border-bottom: 2px solid #f59e0b;">
            <h1 style="color: #1e293b; margin: 0;">Subscription Past Due</h1>
        </div>

        <div style="padding: 30px 0;">
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                Hi {first_name},
            </p>
            <p style="color: #334155; font-size: 16px; line-height: 1.6;">
                Your subscription payment of <strong>{amount_text}</strong> is past due.
                Please update your payment information to continue receiving our services.
            </p>

            <div style="background: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px; padding: 20px; margin: 20px 0;">
                <p style="color: #92400e; margin: 0; font-weight: bold;">
                    ⚠️ Your account access may be limited until payment is received.
                </p>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{portal_link}"
                   style="background-color: #22c55e; color: white; padding: 14px 28px; text-decoration: none;
                          border-radius: 6px; font-weight: bold; display: inline-block;">
                    Update Payment
                </a>
            </div>

            <p style="color: #64748b; font-size: 14px; line-height: 1.5;">
                If you've already made a payment, please disregard this email.
                If you have questions, contact our billing team.
            </p>
        </div>

        <div style="text-align: center; padding-top: 20px; border-top: 1px solid #e2e8f0;">
            <p style="color: #94a3b8; font-size: 12px;">
                Brightpath Ascend Group<br>
                <a href="mailto:billing@brightpathascendgroup.com" style="color: #22c55e;">billing@brightpathascendgroup.com</a>
            </p>
        </div>
    </div>
    """

    return send_email(
        to_email=client_email,
        subject="Action Required: Subscription Past Due - Brightpath Ascend Group",
        html_content=html_content,
    )
