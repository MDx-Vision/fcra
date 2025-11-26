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
    return f'''
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
'''


def welcome_email(client_name, portal_url=None):
    """
    Welcome email for new clients after signup.
    """
    first_name = client_name.split()[0] if client_name else "there"
    
    portal_section = ""
    if portal_url:
        portal_section = f'''
            <p style="margin: 20px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Access Your Client Portal
                </a>
            </p>
        '''
    
    content = f'''
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
    '''
    
    return get_base_template(content, f"Welcome to {COMPANY_NAME}")


def document_reminder_email(client_name, missing_docs, portal_url=None):
    """
    Reminder email for missing required documents.
    """
    first_name = client_name.split()[0] if client_name else "there"
    
    docs_list = "".join([f"<li>{doc}</li>" for doc in missing_docs])
    
    portal_section = ""
    if portal_url:
        portal_section = f'''
            <p style="margin: 25px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Upload Documents Now
                </a>
            </p>
        '''
    
    content = f'''
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
    '''
    
    return get_base_template(content, "Action Required: Documents Needed")


def case_update_email(client_name, status, details=None, portal_url=None):
    """
    Case status update notification email.
    """
    first_name = client_name.split()[0] if client_name else "there"
    
    status_info = {
        'active': {
            'title': 'Your Case is Now Active',
            'message': 'Great news! Your credit restoration case is now active and our team is reviewing your information.',
            'color': PRIMARY_COLOR
        },
        'stage1_complete': {
            'title': 'Analysis Complete',
            'message': 'Your credit report analysis is complete. We\'ve identified violations and prepared a detailed report for your review.',
            'color': SECONDARY_COLOR
        },
        'stage2_complete': {
            'title': 'Dispute Letters Ready',
            'message': 'Your personalized dispute letters have been generated and are ready for review. These letters are customized for each bureau based on the violations we found.',
            'color': SECONDARY_COLOR
        },
        'waiting_response': {
            'title': 'Disputes Sent - Awaiting Response',
            'message': 'Your dispute letters have been sent to the credit bureaus. By law, they must respond within 30-45 days.',
            'color': PRIMARY_COLOR
        },
        'complete': {
            'title': 'Case Completed',
            'message': 'Congratulations! Your credit restoration case has been completed. Thank you for trusting us with your credit journey.',
            'color': SECONDARY_COLOR
        }
    }
    
    info = status_info.get(status, {
        'title': f'Case Update: {status}',
        'message': f'Your case status has been updated to: {status}',
        'color': PRIMARY_COLOR
    })
    
    details_section = ""
    if details:
        details_section = f'''
            <div style="background-color: #f8fafc; border-left: 4px solid {info['color']}; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                <p style="color: #334155; margin: 0; font-size: 14px;">{details}</p>
            </div>
        '''
    
    portal_section = ""
    if portal_url:
        portal_section = f'''
            <p style="margin: 25px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    View Details in Portal
                </a>
            </p>
        '''
    
    content = f'''
        <h2 style="color: {DARK_COLOR}; margin: 0 0 20px 0; font-size: 24px;">{info['title']}</h2>
        
        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>
        
        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            {info['message']}
        </p>
        
        {details_section}
        
        {portal_section}
    '''
    
    return get_base_template(content, info['title'])


def dispute_sent_email(client_name, bureau, tracking_info=None, portal_url=None):
    """
    Notification when dispute letter is sent to a bureau.
    """
    first_name = client_name.split()[0] if client_name else "there"
    
    tracking_section = ""
    if tracking_info:
        tracking_section = f'''
            <div style="background-color: #f0fdf4; border: 1px solid #86efac; padding: 15px 20px; margin: 20px 0; border-radius: 8px;">
                <p style="color: #166534; margin: 0; font-size: 14px;">
                    <strong>Tracking Number:</strong> {tracking_info}
                </p>
            </div>
        '''
    
    portal_section = ""
    if portal_url:
        portal_section = f'''
            <p style="margin: 25px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Track Your Disputes
                </a>
            </p>
        '''
    
    content = f'''
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
    '''
    
    return get_base_template(content, f"Dispute Sent to {bureau}")


def cra_response_email(client_name, bureau, result_summary=None, portal_url=None):
    """
    Notification when CRA response is received.
    """
    first_name = client_name.split()[0] if client_name else "there"
    
    result_section = ""
    if result_summary:
        result_section = f'''
            <div style="background-color: #f8fafc; border-left: 4px solid {PRIMARY_COLOR}; padding: 15px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
                <p style="color: #334155; margin: 0; font-size: 14px;">{result_summary}</p>
            </div>
        '''
    
    portal_section = ""
    if portal_url:
        portal_section = f'''
            <p style="margin: 25px 0;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    View Full Response
                </a>
            </p>
        '''
    
    content = f'''
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
    '''
    
    return get_base_template(content, f"Bureau Response from {bureau}")


def payment_reminder_email(client_name, amount, due_date=None, payment_url=None):
    """
    Payment reminder for pending balance.
    """
    first_name = client_name.split()[0] if client_name else "there"
    formatted_amount = f"${amount:,.2f}" if isinstance(amount, (int, float)) else f"${amount}"
    
    due_section = ""
    if due_date:
        due_section = f"<p style='color: #ef4444; font-weight: 600;'>Due Date: {due_date}</p>"
    
    payment_section = ""
    if payment_url:
        payment_section = f'''
            <p style="margin: 25px 0;">
                <a href="{payment_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Make Payment Now
                </a>
            </p>
        '''
    
    content = f'''
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
    '''
    
    return get_base_template(content, "Payment Reminder")


def analysis_ready_email(client_name, violations_count=None, exposure=None, portal_url=None):
    """
    Notification when credit analysis is complete.
    """
    first_name = client_name.split()[0] if client_name else "there"
    
    stats_section = ""
    if violations_count or exposure:
        stats_html = ""
        if violations_count:
            stats_html += f'''
                <div style="text-align: center; padding: 15px;">
                    <p style="color: #64748b; margin: 0; font-size: 12px; text-transform: uppercase;">Violations Found</p>
                    <p style="color: #ef4444; margin: 5px 0 0 0; font-size: 28px; font-weight: 700;">{violations_count}</p>
                </div>
            '''
        if exposure:
            formatted_exposure = f"${exposure:,.0f}" if isinstance(exposure, (int, float)) else exposure
            stats_html += f'''
                <div style="text-align: center; padding: 15px;">
                    <p style="color: #64748b; margin: 0; font-size: 12px; text-transform: uppercase;">Potential Exposure</p>
                    <p style="color: {SECONDARY_COLOR}; margin: 5px 0 0 0; font-size: 28px; font-weight: 700;">{formatted_exposure}</p>
                </div>
            '''
        stats_section = f'''
            <div style="display: flex; justify-content: center; gap: 40px; background-color: #f8fafc; padding: 20px; margin: 20px 0; border-radius: 8px;">
                {stats_html}
            </div>
        '''
    
    portal_section = ""
    if portal_url:
        portal_section = f'''
            <p style="margin: 25px 0; text-align: center;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    View Your Analysis
                </a>
            </p>
        '''
    
    content = f'''
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
    '''
    
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
        portal_section = f'''
            <p style="margin: 25px 0; text-align: center;">
                <a href="{portal_url}" style="display: inline-block; background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); color: #ffffff; padding: 14px 32px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px;">
                    Download Your Letters
                </a>
            </p>
        '''
    
    content = f'''
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
    '''
    
    return get_base_template(content, "Dispute Letters Ready")


TEMPLATE_TYPES = {
    'welcome': welcome_email,
    'document_reminder': document_reminder_email,
    'case_update': case_update_email,
    'dispute_sent': dispute_sent_email,
    'cra_response': cra_response_email,
    'payment_reminder': payment_reminder_email,
    'analysis_ready': analysis_ready_email,
    'letters_ready': letters_ready_email
}


def get_template(template_type):
    """Get a template function by type name."""
    return TEMPLATE_TYPES.get(template_type)


def list_templates():
    """List all available template types."""
    return list(TEMPLATE_TYPES.keys())
