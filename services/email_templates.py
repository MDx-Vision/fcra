"""
Email Templates for Brightpath Ascend FCRA Platform
Professional HTML email templates for client communications
"""

COMPANY_NAME = "Brightpath Ascend Group"
COMPANY_TAGLINE = "Empowering you to protect your credit—one call at a time."
PRIMARY_COLOR = "#319795"
SECONDARY_COLOR = "#84cc16"
DARK_COLOR = "#1a1a2e"


def get_base_template(content, subject):
    """
    Base HTML email template with Brightpath Ascend branding.
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f0f2f5; font-family: 'Segoe UI', Arial, sans-serif;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f0f2f5; padding: 20px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); padding: 30px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">{COMPANY_NAME}</h1>
                            <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 14px;">{COMPANY_TAGLINE}</p>
                        </td>
                    </tr>

                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            {content}
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: {DARK_COLOR}; padding: 25px 30px; text-align: center;">
                            <p style="color: #94a3b8; margin: 0 0 10px 0; font-size: 12px;">
                                © 2025 {COMPANY_NAME}. All rights reserved.
                            </p>
                            <p style="color: #64748b; margin: 0; font-size: 11px;">
                                This email was sent by {COMPANY_NAME}. If you have questions, reply to this email or contact us.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""


def welcome_email(client_name, portal_url=None):
    """
    Welcome email for new clients after signup.
    """
    first_name = client_name.split()[0] if client_name else "there"

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 20px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Access Your Client Portal
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">Welcome, {first_name}!</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Thank you for choosing {COMPANY_NAME} for your credit restoration needs. We're excited to help you on your journey to better credit.
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            <strong>Here's what happens next:</strong>
        </p>

        <ul style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li>Our team will review your credit report</li>
            <li>We'll identify all FCRA violations and inaccuracies</li>
            <li>You'll receive a comprehensive analysis with next steps</li>
            <li>We'll prepare dispute letters for each bureau</li>
        </ul>

        {portal_section}

        <p style="color: #64748b; font-size: 14px; margin-top: 30px;">
            If you have any questions, simply reply to this email or call our team.
        </p>
    """

    return get_base_template(content, f"Welcome to {COMPANY_NAME}")


def document_reminder_email(client_name, missing_docs, portal_url=None):
    """
    Reminder email for missing required documents.
    """
    first_name = client_name.split()[0] if client_name else "there"

    docs_list = "".join([f"<li>{doc}</li>" for doc in missing_docs])

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 25px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Upload Documents Now
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">Documents Needed, {first_name}</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            To continue processing your credit case, we need the following documents:
        </p>

        <ul style="color: #ef4444; line-height: 1.8; font-size: 15px; padding-left: 20px; font-weight: 500;">
            {docs_list}
        </ul>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Please upload these documents to your client portal as soon as possible so we can proceed with your case.
        </p>

        {portal_section}
    """

    return get_base_template(content, "Action Required: Documents Needed")


def case_update_email(client_name, status, details=None, portal_url=None):
    """
    Case status update notification email.
    """
    first_name = client_name.split()[0] if client_name else "there"

    status_info = {
        "active": {
            "title": "Your Case is Now Active",
            "message": "Great news! Your credit restoration case is now active and our team is reviewing your information.",
            "color": PRIMARY_COLOR,
        },
        "stage1_complete": {
            "title": "Analysis Complete",
            "message": "Your credit report analysis is complete. We've identified violations and prepared a detailed report for your review.",
            "color": SECONDARY_COLOR,
        },
        "stage2_complete": {
            "title": "Dispute Letters Ready",
            "message": "Your personalized dispute letters have been generated and are ready for review. These letters are customized for each bureau based on the violations we found.",
            "color": SECONDARY_COLOR,
        },
        "waiting_response": {
            "title": "Disputes Sent - Awaiting Response",
            "message": "Your dispute letters have been sent to the credit bureaus. By law, they must respond within 30-45 days.",
            "color": PRIMARY_COLOR,
        },
        "complete": {
            "title": "Case Completed",
            "message": "Congratulations! Your credit restoration case has been completed. Thank you for trusting us with your credit journey.",
            "color": SECONDARY_COLOR,
        },
    }

    info = status_info.get(
        status,
        {
            "title": f"Case Update: {status}",
            "message": f"Your case status has been updated to: {status}",
            "color": PRIMARY_COLOR,
        },
    )

    details_section = ""
    if details:
        details_section = f"""
            <div style="background-color: #f8fafc; border-left: 4px solid {info['color']}; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                <p style="color: #334155; margin: 0; font-size: 14px;">{details}</p>
            </div>
        """

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 25px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    View Details in Portal
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">{info['title']}</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            {info['message']}
        </p>

        {details_section}

        {portal_section}
    """

    return get_base_template(content, info["title"])


def dispute_sent_email(client_name, bureau, tracking_info=None, portal_url=None):
    """
    Notification when dispute letter is sent to a bureau.
    """
    first_name = client_name.split()[0] if client_name else "there"

    tracking_section = ""
    if tracking_info:
        tracking_section = f"""
            <div style="background-color: #f0fdf4; border: 1px solid #86efac; padding: 15px 20px; margin: 20px 0; border-radius: 8px;">
                <p style="color: #166534; margin: 0; font-size: 14px;">
                    <strong>Tracking Number:</strong> {tracking_info}
                </p>
            </div>
        """

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 25px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Track Your Disputes
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">Dispute Letter Sent!</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Great news! Your dispute letter has been sent to <strong>{bureau}</strong>.
        </p>

        {tracking_section}

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            <strong>What to expect:</strong>
        </p>

        <ul style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li>The bureau has 30-45 days to investigate and respond</li>
            <li>We'll notify you immediately when we receive their response</li>
            <li>You can track the status in your client portal</li>
        </ul>

        {portal_section}
    """

    return get_base_template(content, f"Dispute Sent to {bureau}")


def cra_response_email(client_name, bureau, result_summary=None, portal_url=None):
    """
    Notification when CRA response is received.
    """
    first_name = client_name.split()[0] if client_name else "there"

    result_section = ""
    if result_summary:
        result_section = f"""
            <div style="background-color: #f8fafc; border-left: 4px solid {PRIMARY_COLOR}; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                <p style="color: #334155; margin: 0; font-size: 14px;">{result_summary}</p>
            </div>
        """

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 25px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    View Full Response
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">Response Received from {bureau}</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            We've received a response from <strong>{bureau}</strong> regarding your dispute.
        </p>

        {result_section}

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Log in to your client portal to review the complete response and see what items were updated or removed.
        </p>

        {portal_section}
    """

    return get_base_template(content, f"Bureau Response from {bureau}")


def payment_reminder_email(client_name, amount, due_date=None, payment_url=None):
    """
    Payment reminder for pending balance.
    """
    first_name = client_name.split()[0] if client_name else "there"
    formatted_amount = (
        f"${amount:,.2f}" if isinstance(amount, (int, float)) else f"${amount}"
    )

    due_section = ""
    if due_date:
        due_section = (
            f"<p style='color: #ef4444; font-weight: 600;'>Due Date: {due_date}</p>"
        )

    payment_section = ""
    if payment_url:
        payment_section = f"""
            <p style="margin: 25px 0;">
                <a href="{payment_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Make Payment Now
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">Payment Reminder</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            This is a friendly reminder that you have a pending payment for your credit restoration services.
        </p>

        <div style="background-color: #fef3c7; border: 1px solid #fbbf24; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center;">
            <p style="color: #92400e; margin: 0; font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Amount Due</p>
            <p style="color: {DARK_COLOR}; margin: 10px 0 0 0; font-size: 32px; font-weight: 700;">{formatted_amount}</p>
            {due_section}
        </div>

        {payment_section}

        <p style="color: #64748b; font-size: 14px;">
            If you've already made this payment, please disregard this notice. For questions about your balance, reply to this email.
        </p>
    """

    return get_base_template(content, "Payment Reminder")


def analysis_ready_email(
    client_name, violations_count=None, exposure=None, portal_url=None
):
    """
    Notification when credit analysis is complete.
    """
    first_name = client_name.split()[0] if client_name else "there"

    stats_section = ""
    if violations_count or exposure:
        stats_html = ""
        if violations_count:
            stats_html += f"""
                <div style="text-align: center; padding: 15px;">
                    <p style="color: #64748b; margin: 0; font-size: 12px; text-transform: uppercase;">Violations Found</p>
                    <p style="color: #ef4444; margin: 5px 0 0 0; font-size: 28px; font-weight: 700;">{violations_count}</p>
                </div>
            """
        if exposure:
            formatted_exposure = (
                f"${exposure:,.0f}" if isinstance(exposure, (int, float)) else exposure
            )
            stats_html += f"""
                <div style="text-align: center; padding: 15px;">
                    <p style="color: #64748b; margin: 0; font-size: 12px; text-transform: uppercase;">Potential Exposure</p>
                    <p style="color: {SECONDARY_COLOR}; margin: 5px 0 0 0; font-size: 28px; font-weight: 700;">{formatted_exposure}</p>
                </div>
            """
        stats_section = f"""
            <div style="display: flex; justify-content: center; gap: 40px; background-color: #f8fafc; padding: 20px; margin: 20px 0; border-radius: 8px;">
                {stats_html}
            </div>
        """

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 25px 0; text-align: center;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    View Your Analysis
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">Your Credit Analysis is Ready!</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Great news! Our AI-powered analysis of your credit report is complete. We've identified FCRA violations and inaccuracies that may be hurting your credit score.
        </p>

        {stats_section}

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Log in to your portal to review the full analysis, see each violation, and understand your next steps.
        </p>

        {portal_section}
    """

    return get_base_template(content, "Your Credit Analysis is Ready")


def letters_ready_email(client_name, letter_count, bureaus=None, portal_url=None):
    """
    Notification when dispute letters are generated.
    """
    first_name = client_name.split()[0] if client_name else "there"

    bureaus_section = ""
    if bureaus:
        bureaus_list = ", ".join(bureaus)
        bureaus_section = f"<p style='color: #334155; font-size: 14px;'>Bureaus: <strong>{bureaus_list}</strong></p>"

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 25px 0; text-align: center;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Download Your Letters
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">Your Dispute Letters Are Ready!</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <div style="background-color: #f0fdf4; border: 1px solid #86efac; padding: 20px; margin: 20px 0; border-radius: 8px; text-align: center;">
            <p style="color: #166534; margin: 0; font-size: 16px;">
                <strong>{letter_count}</strong> personalized dispute letter{"s" if letter_count != 1 else ""} ready
            </p>
            {bureaus_section}
        </div>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Your customized dispute letters have been generated based on the FCRA violations we identified. Each letter is tailored for the specific bureau and includes all required legal language.
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            <strong>Next steps:</strong>
        </p>

        <ul style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li>Review your letters in the portal</li>
            <li>Download and print each letter</li>
            <li>Mail via certified mail with return receipt</li>
            <li>Upload your mailing receipts to track responses</li>
        </ul>

        {portal_section}
    """

    return get_base_template(content, "Dispute Letters Ready")


def cra_response_received_email(
    client_name, bureau, items_deleted, items_verified, portal_url=None
):
    """
    Notification when CRA has responded to dispute.
    """
    first_name = client_name.split()[0] if client_name else "there"

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 25px 0; text-align: center;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    View Full Response
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">{bureau} Has Responded to Your Dispute</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Great news! {bureau} has responded to your dispute. Here's a summary of the results:
        </p>

        <div style="background-color: #f8fafc; border-radius: 8px; padding: 20px; margin: 20px 0;">
            <div style="margin-bottom: 15px;">
                <div style="background-color: #d1fae5; border-left: 4px solid #10b981; padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 12px;">
                    <p style="color: #065f46; margin: 0; font-size: 16px; font-weight: 600;">
                        ✅ Items Deleted: {items_deleted}
                    </p>
                </div>
                <div style="background-color: #fed7aa; border-left: 4px solid #f97316; padding: 15px; border-radius: 0 8px 8px 0;">
                    <p style="color: #9a3412; margin: 0; font-size: 16px; font-weight: 600;">
                        ⚠️ Items Verified: {items_verified}
                    </p>
                </div>
            </div>
        </div>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Our team is currently reviewing the response in detail. We'll analyze which items were successfully removed and determine the best strategy for any verified items that remain.
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            <strong>What happens next:</strong>
        </p>

        <ul style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li>We'll review the complete response for any FCRA violations</li>
            <li>For verified items, we'll prepare escalation letters if warranted</li>
            <li>You'll receive a detailed analysis within 2-3 business days</li>
            <li>We'll proceed to the next round of disputes if needed</li>
        </ul>

        {portal_section}

        <p style="color: #64748b; font-size: 14px; margin-top: 30px;">
            If you have questions about the response, feel free to reply to this email.
        </p>
    """

    return get_base_template(content, f"{bureau} Has Responded to Your Dispute")


def cra_no_response_violation_email(client_name, bureau, portal_url=None):
    """
    Alert email when CRA fails to respond within 30 days (FCRA violation).
    """
    first_name = client_name.split()[0] if client_name else "there"

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 25px 0; text-align: center;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    View Case Details
                </a>
            </p>
        """

    content = f"""
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">FCRA Violation: {bureau} Failed to Respond</h2>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <div style="background-color: #fee2e2; border: 2px solid #ef4444; padding: 20px; margin: 20px 0; border-radius: 8px;">
            <p style="color: #991b1b; margin: 0 0 10px 0; font-size: 18px; font-weight: 700;">
                ⚠️ FCRA Violation Detected
            </p>
            <p style="color: #7f1d1d; margin: 0; font-size: 15px; line-height: 1.6;">
                {bureau} has failed to respond to your dispute within the legally required 30-day period mandated by FCRA §611(a)(1). This is a serious violation of federal law.
            </p>
        </div>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            <strong>What this means for your case:</strong>
        </p>

        <ul style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li><strong>Stronger Legal Position:</strong> This violation significantly strengthens your case and may support claims for statutory damages</li>
            <li><strong>Immediate Action Required:</strong> Under FCRA law, {bureau} must delete the disputed items or provide a valid explanation</li>
            <li><strong>Escalation Protocol:</strong> We are immediately escalating this matter with a formal notice of violation</li>
            <li><strong>Documentation:</strong> All correspondence is being preserved for potential legal action</li>
        </ul>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Our legal team is preparing an escalated demand letter citing this FCRA violation. We will also document this for any potential legal claims, as willful violations can result in statutory damages.
        </p>

        <div style="background-color: #f0fdf4; border-left: 4px solid #10b981; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
            <p style="color: #065f46; margin: 0; font-size: 14px; line-height: 1.6;">
                <strong>Legal Reference:</strong> 15 U.S.C. §1681i(a)(1) requires credit reporting agencies to investigate disputes within 30 days. Failure to comply is a violation of federal law.
            </p>
        </div>

        {portal_section}

        <p style="color: #64748b; font-size: 14px; margin-top: 30px;">
            We're handling this violation aggressively on your behalf. If you have questions, please don't hesitate to reach out.
        </p>
    """

    return get_base_template(content, f"FCRA Violation: {bureau} Failed to Respond")


def reinsertion_violation_alert_email(
    client_name, bureau, account_name, portal_url=None
):
    """
    URGENT alert when a previously deleted item is reinserted without notification.
    """
    first_name = client_name.split()[0] if client_name else "there"

    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 25px 0; text-align: center;">
                <a href="{portal_url}" style="display: inline-block; background: #ef4444; color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    View Case Details - Action Required
                </a>
            </p>
        """

    content = f"""
        <div style="background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%); padding: 20px; margin: -40px -30px 30px -30px; text-align: center;">
            <h2 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 700;">🚨 URGENT: FCRA Violation Detected</h2>
            <p style="color: rgba(255,255,255,0.95); margin: 10px 0 0 0; font-size: 15px;">Immediate Action Required</p>
        </div>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            <strong>We have detected a serious FCRA violation regarding your credit report with {bureau}.</strong>
        </p>

        <div style="background-color: #fee2e2; border: 3px solid #dc2626; padding: 20px; margin: 20px 0; border-radius: 8px;">
            <p style="color: #991b1b; margin: 0 0 15px 0; font-size: 17px; font-weight: 700;">
                Reinsertion Violation - FCRA §1681i(a)(5)(B)
            </p>
            <p style="color: #7f1d1d; margin: 0; font-size: 15px; line-height: 1.6;">
                <strong>Account:</strong> {account_name}
            </p>
            <p style="color: #7f1d1d; margin: 10px 0 0 0; font-size: 15px; line-height: 1.6;">
                This item was previously deleted from your credit report following our dispute. {bureau} has now illegally reinserted this item <strong>without providing you the required 5-day advance notice</strong> as mandated by federal law.
            </p>
        </div>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            <strong>What this violation means:</strong>
        </p>

        <ul style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li><strong>Federal Law Violation:</strong> FCRA §1681i(a)(5)(B) requires 5-day advance written notice before reinserting any deleted information</li>
            <li><strong>Statutory Damages:</strong> This violation entitles you to potential damages of <span style="background-color: #fef3c7; padding: 2px 6px; border-radius: 4px; font-weight: 600;">$100 - $1,000 per violation</span></li>
            <li><strong>Punitive Damages:</strong> If willful, additional punitive damages may apply</li>
            <li><strong>Attorney Fees:</strong> {bureau} may be liable for your attorney fees and costs</li>
        </ul>

        <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
            <p style="color: #78350f; margin: 0; font-size: 14px; line-height: 1.6;">
                <strong>Priority Case Status:</strong> Your case has been flagged as high-priority due to this violation. Our legal team is immediately preparing a formal demand letter and documenting this violation for potential litigation.
            </p>
        </div>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            <strong>Our immediate actions:</strong>
        </p>

        <ul style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li>Formal demand letter citing FCRA §1681i(a)(5)(B) violation</li>
            <li>Request for immediate removal of reinserted item</li>
            <li>Preservation of all evidence for potential legal claims</li>
            <li>Evaluation for statutory damages claim</li>
        </ul>

        {portal_section}

        <div style="background-color: #f8fafc; padding: 15px; margin-top: 30px; border-radius: 8px; border: 1px solid #e2e8f0;">
            <p style="color: #64748b; font-size: 13px; margin: 0; line-height: 1.5;">
                <strong>Legal Citation:</strong> 15 U.S.C. §1681i(a)(5)(B) - "A consumer reporting agency shall provide written notice to a consumer of the results of a reinvestigation... not later than 5 business days after the completion of the reinvestigation, by mail or, if authorized by the consumer for that purpose, by other means available to the agency."
            </p>
        </div>

        <p style="color: #64748b; font-size: 14px; margin-top: 25px;">
            This is a serious violation and we are treating it with the highest priority. Our team will contact you within 24 hours to discuss next steps.
        </p>
    """

    return get_base_template(content, "🚨 URGENT: Reinsertion Violation Detected")


def fcra_analysis_summary_email(
    client_name, violations, damages_info, case_strength, portal_url=None
):
    """
    Comprehensive FCRA analysis summary email for clients.
    This is the main email sent with the full report PDF attachment.

    Args:
        client_name: Client's full name
        violations: List of violation dicts with keys: bureau, account_name, violation_type, description
        damages_info: Dict with keys: total_exposure, settlement_target, violations_count
        case_strength: String like "Strong", "Moderate", "Weak"
        portal_url: Optional link to client portal
    """
    first_name = client_name.split()[0] if client_name else "there"

    # Determine case strength styling
    strength_colors = {
        "Strong": {"bg": "#dcfce7", "text": "#166534", "border": "#86efac"},
        "Moderate": {"bg": "#fef3c7", "text": "#92400e", "border": "#fcd34d"},
        "Weak": {"bg": "#fee2e2", "text": "#991b1b", "border": "#fca5a5"},
    }
    strength_style = strength_colors.get(case_strength, strength_colors["Moderate"])

    # Group violations by bureau
    violations_by_bureau = {}
    for v in violations[:10]:  # Limit to first 10 for email
        bureau = v.get("bureau", "Unknown")
        if bureau not in violations_by_bureau:
            violations_by_bureau[bureau] = []
        violations_by_bureau[bureau].append(v)

    # Build violations summary HTML
    violations_html = ""
    for bureau, bureau_violations in violations_by_bureau.items():
        violations_html += f"""
        <div style="background-color: #f8fafc; border-left: 4px solid {PRIMARY_COLOR}; padding: 15px 20px; margin: 15px 0; border-radius: 0 8px 8px 0;">
            <h3 style="color: {DARK_COLOR}; margin: 0 0 10px 0; font-size: 18px;">{bureau}</h3>
        """
        for v in bureau_violations:
            account = v.get("account_name", "Account")
            violation_type = v.get("violation_type", "FCRA Violation")
            description = (
                v.get("description", "")[:150] + "..."
                if len(v.get("description", "")) > 150
                else v.get("description", "")
            )
            violations_html += f"""
            <div style="margin-bottom: 12px;">
                <p style="color: #1e293b; margin: 0; font-size: 15px; font-weight: 600;">• {account}</p>
                <p style="color: #64748b; margin: 5px 0 0 15px; font-size: 14px; line-height: 1.5;">{violation_type}</p>
                <p style="color: #64748b; margin: 3px 0 0 15px; font-size: 13px; line-height: 1.4;">{description}</p>
            </div>
            """
        violations_html += "</div>"

    # Portal section
    portal_section = ""
    if portal_url:
        portal_section = f"""
            <p style="margin: 30px 0; text-align: center;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 16px 36px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Access Your Client Portal
                </a>
            </p>
        """

    content = f"""
        <div style="background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); padding: 20px; margin: -40px -30px 30px -30px; text-align: center;">
            <h2 style="color: #ffffff; margin: 0; font-size: 26px; font-weight: 700;">Your Credit Analysis is Complete</h2>
            <p style="color: rgba(255,255,255,0.95); margin: 10px 0 0 0; font-size: 15px;">Comprehensive FCRA Violations Report</p>
        </div>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            We've completed a comprehensive analysis of your credit report and identified significant FCRA (Fair Credit Reporting Act) violations. Please find your detailed report attached to this email.
        </p>

        <!-- Case Summary Box -->
        <div style="background-color: {strength_style['bg']}; border: 2px solid {strength_style['border']}; padding: 20px; margin: 25px 0; border-radius: 10px;">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="text-align: center; padding: 10px;">
                        <div style="font-size: 36px; font-weight: 700; color: {strength_style['text']};">{damages_info.get('violations_count', 0)}</div>
                        <div style="font-size: 13px; color: {strength_style['text']}; margin-top: 5px;">FCRA Violations</div>
                    </td>
                    <td style="text-align: center; padding: 10px; border-left: 1px solid {strength_style['border']};">
                        <div style="font-size: 36px; font-weight: 700; color: {strength_style['text']};">${"{:,.0f}".format(damages_info.get('total_exposure', 0))}</div>
                        <div style="font-size: 13px; color: {strength_style['text']}; margin-top: 5px;">Total Exposure</div>
                    </td>
                    <td style="text-align: center; padding: 10px; border-left: 1px solid {strength_style['border']};">
                        <div style="font-size: 24px; font-weight: 700; color: {strength_style['text']};">{case_strength}</div>
                        <div style="font-size: 13px; color: {strength_style['text']}; margin-top: 5px;">Case Strength</div>
                    </td>
                </tr>
            </table>
        </div>

        <h3 style="color: {DARK_COLOR}; margin: 30px 0 15px 0; font-size: 20px;">Key Findings</h3>

        <p style="color: #334155; line-height: 1.6; font-size: 15px;">
            Our analysis identified <strong>{damages_info.get('violations_count', 0)} FCRA violations</strong> across your credit reports. Here are some of the most significant issues:
        </p>

        {violations_html}

        <h3 style="color: {DARK_COLOR}; margin: 30px 0 15px 0; font-size: 20px;">What This Means For You</h3>

        <div style="background-color: #f0fdf4; border: 1px solid #86efac; padding: 20px; margin: 20px 0; border-radius: 8px;">
            <p style="color: #166534; margin: 0 0 15px 0; font-size: 16px; font-weight: 600;">
                Settlement Target: ${"{:,.0f}".format(damages_info.get('settlement_target', 0))}
            </p>
            <p style="color: #166534; margin: 0; font-size: 14px; line-height: 1.6;">
                Based on the violations identified, case law precedents, and your documentation, we've calculated a realistic settlement target. The attached full report includes detailed breakdowns of:
            </p>
        </div>

        <ul style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li><strong>Actual Damages:</strong> Credit denials, higher interest rates, emotional distress</li>
            <li><strong>Statutory Damages:</strong> $100-$1,000 per violation under FCRA §1681n and §1681o</li>
            <li><strong>Punitive Damages:</strong> Available for willful violations</li>
            <li><strong>Attorney Fees:</strong> Recoverable under FCRA §1681o(a)(2)</li>
        </ul>

        <h3 style="color: {DARK_COLOR}; margin: 30px 0 15px 0; font-size: 20px;">Next Steps</h3>

        <ol style="color: #334155; line-height: 1.8; font-size: 15px; padding-left: 20px;">
            <li><strong>Review Your Full Report:</strong> The attached PDF contains comprehensive details on each violation, legal citations, and your rights</li>
            <li><strong>Schedule a Call:</strong> We'll discuss strategy, timeline, and answer your questions</li>
            <li><strong>Bureau Dispute Letters:</strong> We'll prepare and send certified demand letters to all three bureaus</li>
            <li><strong>Track Progress:</strong> Monitor updates in your secure client portal</li>
        </ol>

        {portal_section}

        <div style="background-color: #fffbeb; border: 1px solid #fcd34d; padding: 15px 20px; margin: 25px 0; border-radius: 8px;">
            <p style="color: #92400e; margin: 0; font-size: 14px; line-height: 1.6;">
                <strong>Important:</strong> The full detailed report is attached as a PDF. Please review it carefully and keep it in a safe place. This document contains sensitive legal analysis and should be treated as confidential.
            </p>
        </div>

        <p style="color: #334155; line-height: 1.6; font-size: 15px;">
            If you have any questions about your report or next steps, please don't hesitate to reach out. We're here to help you every step of the way.
        </p>

        <p style="color: #334155; line-height: 1.6; font-size: 15px; margin-top: 25px;">
            Best regards,<br>
            <strong>{COMPANY_NAME} Team</strong>
        </p>
    """

    return get_base_template(content, "Your Credit Analysis is Complete")


TEMPLATE_TYPES = {
    "welcome": welcome_email,
    "document_reminder": document_reminder_email,
    "case_update": case_update_email,
    "dispute_sent": dispute_sent_email,
    "cra_response": cra_response_email,
    "payment_reminder": payment_reminder_email,
    "analysis_ready": analysis_ready_email,
    "letters_ready": letters_ready_email,
    "cra_response_received": cra_response_received_email,
    "cra_no_response_violation": cra_no_response_violation_email,
    "reinsertion_violation_alert": reinsertion_violation_alert_email,
}


def get_template(template_type):
    """Get a template function by type name."""
    return TEMPLATE_TYPES.get(template_type)


def list_templates():
    """List all available template types."""
    return list(TEMPLATE_TYPES.keys())
