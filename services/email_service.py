"""
SendGrid Email Service for Brightpath Ascend FCRA Platform
Uses Replit's SendGrid integration for transactional emails
"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Attachment, FileContent, FileName, FileType, Disposition
import base64


_sendgrid_client = None
DEFAULT_FROM_EMAIL = "support@brightpathascendgroup.com"
DEFAULT_FROM_NAME = "Brightpath Ascend Group"


def get_sendgrid_api_key():
    """Get SendGrid API key from environment."""
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        raise ValueError('SendGrid API key not configured. Set SENDGRID_API_KEY environment variable.')
    return api_key


def get_sendgrid_client():
    """Get a configured SendGrid client."""
    global _sendgrid_client
    
    if _sendgrid_client is None:
        api_key = get_sendgrid_api_key()
        _sendgrid_client = SendGridAPIClient(api_key)
    
    return _sendgrid_client


def get_from_email():
    """Get the configured from email address."""
    return os.environ.get('SENDGRID_FROM_EMAIL', DEFAULT_FROM_EMAIL)


def get_from_name():
    """Get the configured from name."""
    return os.environ.get('SENDGRID_FROM_NAME', DEFAULT_FROM_NAME)


def send_email(to_email, subject, html_content, plain_content=None, from_email=None, from_name=None, attachments=None):
    """
    Send a single email.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        html_content: HTML body content
        plain_content: Optional plain text content (auto-generated if not provided)
        from_email: Optional sender email (defaults to configured)
        from_name: Optional sender name (defaults to configured)
        attachments: Optional list of dicts with 'content', 'filename', 'type' keys
        
    Returns:
        dict with 'success', 'message_id', 'error' keys
    """
    try:
        if not to_email:
            return {
                'success': False,
                'message_id': None,
                'error': 'No recipient email provided'
            }
        
        if from_email is None:
            from_email = get_from_email()
        if from_name is None:
            from_name = get_from_name()
        
        if plain_content is None:
            import re
            plain_content = re.sub(r'<[^>]+>', '', html_content)
        
        message = Mail(
            from_email=Email(from_email, from_name),
            to_emails=To(to_email),
            subject=subject,
            plain_text_content=Content("text/plain", plain_content),
            html_content=Content("text/html", html_content)
        )
        
        if attachments:
            for att in attachments:
                attachment = Attachment()
                attachment.file_content = FileContent(att.get('content', ''))
                attachment.file_name = FileName(att.get('filename', 'attachment'))
                attachment.file_type = FileType(att.get('type', 'application/octet-stream'))
                attachment.disposition = Disposition('attachment')
                message.add_attachment(attachment)
        
        client = get_sendgrid_client()
        response = client.send(message)
        
        message_id = response.headers.get('X-Message-Id', '') if response.headers else ''
        
        return {
            'success': True,
            'message_id': message_id,
            'status_code': response.status_code,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'message_id': None,
            'error': str(e)
        }


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
        results.append({
            'email': email,
            'success': result['success'],
            'message_id': result.get('message_id'),
            'error': result.get('error')
        })
        
        if result['success']:
            sent_count += 1
        else:
            failed_count += 1
    
    return {
        'total': len(recipients),
        'sent': sent_count,
        'failed': failed_count,
        'results': results
    }


def is_sendgrid_configured():
    """
    Check if SendGrid is configured.
    Returns True if API key is set, False otherwise.
    """
    try:
        api_key = os.environ.get('SENDGRID_API_KEY')
        return bool(api_key)
    except Exception:
        return False


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
        with open(pdf_path, 'rb') as f:
            pdf_content = base64.b64encode(f.read()).decode()
        
        if pdf_filename is None:
            pdf_filename = os.path.basename(pdf_path)
        
        attachments = [{
            'content': pdf_content,
            'filename': pdf_filename,
            'type': 'application/pdf'
        }]
        
        return send_email(to_email, subject, html_content, attachments=attachments)
        
    except Exception as e:
        return {
            'success': False,
            'message_id': None,
            'error': f'Error attaching PDF: {str(e)}'
        }
