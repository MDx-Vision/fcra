"""
Email Automation Service for Brightpath Ascend FCRA Platform
Handles automated email triggers similar to SMS automation
"""
from datetime import datetime
from services.email_service import send_email, is_sendgrid_configured
from services import email_templates


def get_custom_template(db, template_type):
    """
    Get custom template from database if it exists.
    Returns (subject, html_content) tuple or (None, None) if no custom template.
    """
    from database import EmailTemplate
    
    template = db.query(EmailTemplate).filter_by(template_type=template_type).first()
    if template and template.is_custom and template.html_content:
        return template.subject, template.html_content
    return None, None


def apply_template_merge_tags(html_content, values):
    """
    Replace merge tags in HTML content with actual values.
    Supports: {{client_name}}, {{client_email}}, {{portal_link}}, {{case_status}}, 
              {{missing_docs}}, {{company_name}}, {{support_email}}, and dynamic values.
    """
    if not html_content:
        return html_content
    
    default_values = {
        'company_name': 'Brightpath Ascend Group',
        'support_email': 'support@brightpathascend.com'
    }
    
    all_values = {**default_values, **values}
    
    result = html_content
    for tag, value in all_values.items():
        result = result.replace('{{' + tag + '}}', str(value) if value else '')
    
    return result


def get_email_settings(db):
    """
    Get email automation settings from database.
    Returns dict with all email settings.
    """
    from database import SignupSettings
    
    defaults = {
        'email_enabled': True,
        'welcome_email_enabled': True,
        'document_reminder_enabled': True,
        'case_update_enabled': True,
        'dispute_sent_enabled': True,
        'cra_response_enabled': True,
        'payment_reminder_enabled': True,
        'analysis_ready_enabled': True,
        'letters_ready_enabled': True,
        'reminder_delay_hours': 48
    }
    
    settings = {}
    for key, default_value in defaults.items():
        db_key = f'email_{key}'
        setting = db.query(SignupSettings).filter_by(setting_key=db_key).first()
        if setting:
            if isinstance(default_value, bool):
                settings[key] = setting.setting_value.lower() == 'true'
            elif isinstance(default_value, int):
                try:
                    settings[key] = int(setting.setting_value)
                except ValueError:
                    settings[key] = default_value
            else:
                settings[key] = setting.setting_value
        else:
            settings[key] = default_value
    
    return settings


def log_email(db, client_id, email_address, template_type, subject, status, error_message=None, message_id=None):
    """Log an email send attempt to the database."""
    from database import EmailLog
    
    log_entry = EmailLog(
        client_id=client_id,
        email_address=email_address,
        template_type=template_type,
        subject=subject,
        status=status,
        error_message=error_message,
        message_id=message_id,
        sent_at=datetime.utcnow()
    )
    db.add(log_entry)
    db.commit()
    return log_entry


def get_portal_url(client):
    """Get the portal URL for a client."""
    import os
    base_url = os.environ.get('REPLIT_DEV_DOMAIN', '')
    if base_url and not base_url.startswith('http'):
        base_url = f'https://{base_url}'
    
    if client.portal_token:
        return f"{base_url}/portal/{client.portal_token}"
    return None


def trigger_welcome_email(db, client_id):
    """
    Send welcome email to a new client.
    """
    from database import Client
    
    settings = get_email_settings(db)
    if not settings.get('email_enabled') or not settings.get('welcome_email_enabled'):
        return {'sent': False, 'reason': 'Welcome emails disabled'}
    
    if not is_sendgrid_configured():
        return {'sent': False, 'reason': 'SendGrid not configured'}
    
    client = db.query(Client).filter_by(id=client_id).first()
    if not client or not client.email:
        return {'sent': False, 'reason': 'Client not found or no email'}
    
    portal_url = get_portal_url(client)
    
    custom_subject, custom_html = get_custom_template(db, 'welcome')
    if custom_html:
        html_content = apply_template_merge_tags(custom_html, {
            'client_name': client.name,
            'client_email': client.email,
            'portal_link': portal_url or ''
        })
        subject = apply_template_merge_tags(custom_subject, {'client_name': client.name})
    else:
        html_content = email_templates.welcome_email(client.name, portal_url)
        subject = "Welcome to Brightpath Ascend Group!"
    
    result = send_email(client.email, subject, html_content)
    
    log_email(
        db, client_id, client.email, 'welcome', subject,
        'sent' if result['success'] else 'failed',
        result.get('error'),
        result.get('message_id')
    )
    
    return {'sent': result['success'], 'error': result.get('error')}


def trigger_document_reminder_email(db, client_id, missing_docs):
    """
    Send document reminder email.
    """
    from database import Client
    
    settings = get_email_settings(db)
    if not settings.get('email_enabled') or not settings.get('document_reminder_enabled'):
        return {'sent': False, 'reason': 'Document reminder emails disabled'}
    
    if not is_sendgrid_configured():
        return {'sent': False, 'reason': 'SendGrid not configured'}
    
    client = db.query(Client).filter_by(id=client_id).first()
    if not client or not client.email:
        return {'sent': False, 'reason': 'Client not found or no email'}
    
    portal_url = get_portal_url(client)
    missing_docs_str = ', '.join(missing_docs) if isinstance(missing_docs, list) else str(missing_docs)
    
    custom_subject, custom_html = get_custom_template(db, 'document_reminder')
    if custom_html:
        html_content = apply_template_merge_tags(custom_html, {
            'client_name': client.name,
            'client_email': client.email,
            'portal_link': portal_url or '',
            'missing_docs': missing_docs_str
        })
        subject = apply_template_merge_tags(custom_subject, {'client_name': client.name})
    else:
        html_content = email_templates.document_reminder_email(client.name, missing_docs, portal_url)
        subject = "Action Required: Documents Needed"
    
    result = send_email(client.email, subject, html_content)
    
    log_email(
        db, client_id, client.email, 'document_reminder', subject,
        'sent' if result['success'] else 'failed',
        result.get('error'),
        result.get('message_id')
    )
    
    return {'sent': result['success'], 'error': result.get('error')}


def trigger_case_update_email(db, client_id, status, details=None):
    """
    Send case status update email.
    """
    from database import Client
    
    settings = get_email_settings(db)
    if not settings.get('email_enabled') or not settings.get('case_update_enabled'):
        return {'sent': False, 'reason': 'Case update emails disabled'}
    
    if not is_sendgrid_configured():
        return {'sent': False, 'reason': 'SendGrid not configured'}
    
    client = db.query(Client).filter_by(id=client_id).first()
    if not client or not client.email:
        return {'sent': False, 'reason': 'Client not found or no email'}
    
    portal_url = get_portal_url(client)
    status_display = status.replace('_', ' ').title() if status else ''
    
    custom_subject, custom_html = get_custom_template(db, 'case_update')
    if custom_html:
        html_content = apply_template_merge_tags(custom_html, {
            'client_name': client.name,
            'client_email': client.email,
            'portal_link': portal_url or '',
            'case_status': status_display
        })
        subject = apply_template_merge_tags(custom_subject, {'client_name': client.name, 'case_status': status_display})
    else:
        html_content = email_templates.case_update_email(client.name, status, details, portal_url)
        subject = f"Case Update: {status_display}"
    
    result = send_email(client.email, subject, html_content)
    
    log_email(
        db, client_id, client.email, 'case_update', subject,
        'sent' if result['success'] else 'failed',
        result.get('error'),
        result.get('message_id')
    )
    
    return {'sent': result['success'], 'error': result.get('error')}


def trigger_dispute_sent_email(db, client_id, bureau, tracking_info=None):
    """
    Send notification when dispute letter is mailed.
    """
    from database import Client
    
    settings = get_email_settings(db)
    if not settings.get('email_enabled') or not settings.get('dispute_sent_enabled'):
        return {'sent': False, 'reason': 'Dispute sent emails disabled'}
    
    if not is_sendgrid_configured():
        return {'sent': False, 'reason': 'SendGrid not configured'}
    
    client = db.query(Client).filter_by(id=client_id).first()
    if not client or not client.email:
        return {'sent': False, 'reason': 'Client not found or no email'}
    
    portal_url = get_portal_url(client)
    
    custom_subject, custom_html = get_custom_template(db, 'dispute_sent')
    if custom_html:
        html_content = apply_template_merge_tags(custom_html, {
            'client_name': client.name,
            'client_email': client.email,
            'portal_link': portal_url or '',
            'bureau': bureau or ''
        })
        subject = apply_template_merge_tags(custom_subject, {'client_name': client.name, 'bureau': bureau or ''})
    else:
        html_content = email_templates.dispute_sent_email(client.name, bureau, tracking_info, portal_url)
        subject = f"Dispute Letter Sent to {bureau}"
    
    result = send_email(client.email, subject, html_content)
    
    log_email(
        db, client_id, client.email, 'dispute_sent', subject,
        'sent' if result['success'] else 'failed',
        result.get('error'),
        result.get('message_id')
    )
    
    return {'sent': result['success'], 'error': result.get('error')}


def trigger_cra_response_email(db, client_id, bureau, result_summary=None):
    """
    Send notification when CRA response is received.
    """
    from database import Client
    
    settings = get_email_settings(db)
    if not settings.get('email_enabled') or not settings.get('cra_response_enabled'):
        return {'sent': False, 'reason': 'CRA response emails disabled'}
    
    if not is_sendgrid_configured():
        return {'sent': False, 'reason': 'SendGrid not configured'}
    
    client = db.query(Client).filter_by(id=client_id).first()
    if not client or not client.email:
        return {'sent': False, 'reason': 'Client not found or no email'}
    
    portal_url = get_portal_url(client)
    
    custom_subject, custom_html = get_custom_template(db, 'cra_response')
    if custom_html:
        html_content = apply_template_merge_tags(custom_html, {
            'client_name': client.name,
            'client_email': client.email,
            'portal_link': portal_url or '',
            'bureau': bureau or ''
        })
        subject = apply_template_merge_tags(custom_subject, {'client_name': client.name, 'bureau': bureau or ''})
    else:
        html_content = email_templates.cra_response_email(client.name, bureau, result_summary, portal_url)
        subject = f"Response Received from {bureau}"
    
    result = send_email(client.email, subject, html_content)
    
    log_email(
        db, client_id, client.email, 'cra_response', subject,
        'sent' if result['success'] else 'failed',
        result.get('error'),
        result.get('message_id')
    )
    
    return {'sent': result['success'], 'error': result.get('error')}


def trigger_payment_reminder_email(db, client_id, amount, due_date=None):
    """
    Send payment reminder email.
    """
    from database import Client
    
    settings = get_email_settings(db)
    if not settings.get('email_enabled') or not settings.get('payment_reminder_enabled'):
        return {'sent': False, 'reason': 'Payment reminder emails disabled'}
    
    if not is_sendgrid_configured():
        return {'sent': False, 'reason': 'SendGrid not configured'}
    
    client = db.query(Client).filter_by(id=client_id).first()
    if not client or not client.email:
        return {'sent': False, 'reason': 'Client not found or no email'}
    
    portal_url = get_portal_url(client)
    
    custom_subject, custom_html = get_custom_template(db, 'payment_reminder')
    if custom_html:
        html_content = apply_template_merge_tags(custom_html, {
            'client_name': client.name,
            'client_email': client.email,
            'portal_link': portal_url or '',
            'amount': str(amount) if amount else '',
            'due_date': str(due_date) if due_date else ''
        })
        subject = apply_template_merge_tags(custom_subject, {'client_name': client.name})
    else:
        html_content = email_templates.payment_reminder_email(client.name, amount, due_date)
        subject = "Payment Reminder - Brightpath Ascend Group"
    
    result = send_email(client.email, subject, html_content)
    
    log_email(
        db, client_id, client.email, 'payment_reminder', subject,
        'sent' if result['success'] else 'failed',
        result.get('error'),
        result.get('message_id')
    )
    
    return {'sent': result['success'], 'error': result.get('error')}


def trigger_analysis_ready_email(db, client_id, violations_count=None, exposure=None):
    """
    Send notification when credit analysis is complete.
    """
    from database import Client
    
    settings = get_email_settings(db)
    if not settings.get('email_enabled') or not settings.get('analysis_ready_enabled'):
        return {'sent': False, 'reason': 'Analysis ready emails disabled'}
    
    if not is_sendgrid_configured():
        return {'sent': False, 'reason': 'SendGrid not configured'}
    
    client = db.query(Client).filter_by(id=client_id).first()
    if not client or not client.email:
        return {'sent': False, 'reason': 'Client not found or no email'}
    
    portal_url = get_portal_url(client)
    
    custom_subject, custom_html = get_custom_template(db, 'analysis_ready')
    if custom_html:
        html_content = apply_template_merge_tags(custom_html, {
            'client_name': client.name,
            'client_email': client.email,
            'portal_link': portal_url or '',
            'violations_count': str(violations_count) if violations_count else '0',
            'exposure': str(exposure) if exposure else ''
        })
        subject = apply_template_merge_tags(custom_subject, {'client_name': client.name})
    else:
        html_content = email_templates.analysis_ready_email(client.name, violations_count, exposure, portal_url)
        subject = "Your Credit Analysis is Ready!"
    
    result = send_email(client.email, subject, html_content)
    
    log_email(
        db, client_id, client.email, 'analysis_ready', subject,
        'sent' if result['success'] else 'failed',
        result.get('error'),
        result.get('message_id')
    )
    
    return {'sent': result['success'], 'error': result.get('error')}


def trigger_letters_ready_email(db, client_id, letter_count, bureaus=None):
    """
    Send notification when dispute letters are generated.
    """
    from database import Client
    
    settings = get_email_settings(db)
    if not settings.get('email_enabled') or not settings.get('letters_ready_enabled'):
        return {'sent': False, 'reason': 'Letters ready emails disabled'}
    
    if not is_sendgrid_configured():
        return {'sent': False, 'reason': 'SendGrid not configured'}
    
    client = db.query(Client).filter_by(id=client_id).first()
    if not client or not client.email:
        return {'sent': False, 'reason': 'Client not found or no email'}
    
    portal_url = get_portal_url(client)
    bureaus_str = ', '.join(bureaus) if isinstance(bureaus, list) else str(bureaus or '')
    
    custom_subject, custom_html = get_custom_template(db, 'letters_ready')
    if custom_html:
        html_content = apply_template_merge_tags(custom_html, {
            'client_name': client.name,
            'client_email': client.email,
            'portal_link': portal_url or '',
            'letter_count': str(letter_count) if letter_count else '',
            'bureaus': bureaus_str
        })
        subject = apply_template_merge_tags(custom_subject, {'client_name': client.name})
    else:
        html_content = email_templates.letters_ready_email(client.name, letter_count, bureaus, portal_url)
        subject = "Your Dispute Letters Are Ready!"
    
    result = send_email(client.email, subject, html_content)
    
    log_email(
        db, client_id, client.email, 'letters_ready', subject,
        'sent' if result['success'] else 'failed',
        result.get('error'),
        result.get('message_id')
    )
    
    return {'sent': result['success'], 'error': result.get('error')}


def send_test_email(to_email, message=None):
    """
    Send a test email to verify SendGrid configuration.
    """
    if not is_sendgrid_configured():
        return {'success': False, 'error': 'SendGrid not configured'}
    
    subject = "Test Email from Brightpath Ascend"
    
    if message:
        content = f'''
            <h2 style="color: #1a1a2e;">Test Email</h2>
            <p>{message}</p>
            <p style="color: #64748b; font-size: 14px; margin-top: 20px;">
                This is a test email to verify your SendGrid configuration is working correctly.
            </p>
        '''
    else:
        content = '''
            <h2 style="color: #1a1a2e;">Test Email Successful!</h2>
            <p>Your SendGrid email configuration is working correctly.</p>
            <p style="color: #64748b; font-size: 14px; margin-top: 20px;">
                Brightpath Ascend Group email automation is ready to use.
            </p>
        '''
    
    html_content = email_templates.get_base_template(content, subject)
    
    result = send_email(to_email, subject, html_content)
    return result


def send_custom_email(db, client_id, subject, message):
    """
    Send a custom email to a specific client.
    """
    from database import Client
    
    if not is_sendgrid_configured():
        return {'success': False, 'error': 'SendGrid not configured'}
    
    client = db.query(Client).filter_by(id=client_id).first()
    if not client or not client.email:
        return {'success': False, 'error': 'Client not found or no email'}
    
    first_name = client.name.split()[0] if client.name else "there"
    content = f'''
        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            Hi {first_name},
        </p>
        <p style="color: #334155; line-height: 1.6; font-size: 16px;">
            {message}
        </p>
    '''
    
    html_content = email_templates.get_base_template(content, subject)
    
    result = send_email(client.email, subject, html_content)
    
    log_email(
        db, client_id, client.email, 'custom', subject,
        'sent' if result['success'] else 'failed',
        result.get('error'),
        result.get('message_id')
    )
    
    return result
