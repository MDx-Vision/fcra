"""
Twilio SMS Service for Replit Integration
Fetches Twilio credentials from Replit's connector API
"""
import os
import requests
from twilio.rest import Client as TwilioClient


_connection_settings = None
_twilio_client = None


def get_twilio_credentials():
    """
    Fetch Twilio credentials from Replit's connector API.
    Returns dict with account_sid, api_key, api_key_secret, phone_number.
    """
    global _connection_settings
    
    hostname = os.environ.get('REPLIT_CONNECTORS_HOSTNAME')
    
    repl_identity = os.environ.get('REPL_IDENTITY')
    web_repl_renewal = os.environ.get('WEB_REPL_RENEWAL')
    
    if repl_identity:
        x_replit_token = f'repl {repl_identity}'
    elif web_repl_renewal:
        x_replit_token = f'depl {web_repl_renewal}'
    else:
        raise ValueError('No REPL_IDENTITY or WEB_REPL_RENEWAL token found')
    
    if not hostname:
        raise ValueError('REPLIT_CONNECTORS_HOSTNAME not found')
    
    is_production = os.environ.get('REPLIT_DEPLOYMENT') == '1'
    target_environment = 'production' if is_production else 'development'
    
    url = f'https://{hostname}/api/v2/connection'
    params = {
        'include_secrets': 'true',
        'connector_names': 'twilio',
        'environment': target_environment
    }
    
    headers = {
        'Accept': 'application/json',
        'X_REPLIT_TOKEN': x_replit_token
    }
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    _connection_settings = data.get('items', [{}])[0] if data.get('items') else None
    
    if not _connection_settings:
        raise ValueError(f'Twilio {target_environment} connection not found')
    
    settings = _connection_settings.get('settings', {})
    account_sid = settings.get('account_sid')
    api_key = settings.get('api_key')
    api_key_secret = settings.get('api_key_secret')
    phone_number = settings.get('phone_number')
    
    if not account_sid or not api_key or not api_key_secret:
        raise ValueError(f'Twilio {target_environment} credentials incomplete')
    
    return {
        'account_sid': account_sid,
        'api_key': api_key,
        'api_key_secret': api_key_secret,
        'phone_number': phone_number
    }


def get_twilio_client():
    """
    Get a configured Twilio client.
    Returns a TwilioClient instance.
    """
    global _twilio_client
    
    if _twilio_client is None:
        creds = get_twilio_credentials()
        _twilio_client = TwilioClient(
            creds['api_key'],
            creds['api_key_secret'],
            creds['account_sid']
        )
    
    return _twilio_client


def get_twilio_phone_number():
    """Get the configured Twilio phone number for sending SMS."""
    creds = get_twilio_credentials()
    return creds.get('phone_number')


def format_phone_number(phone):
    """
    Format phone number to E.164 format for Twilio.
    Handles various input formats.
    """
    if not phone:
        return None
    
    digits = ''.join(filter(str.isdigit, str(phone)))
    
    if len(digits) == 10:
        return f'+1{digits}'
    elif len(digits) == 11 and digits.startswith('1'):
        return f'+{digits}'
    elif len(digits) > 10 and not digits.startswith('1'):
        return f'+{digits}'
    elif phone.startswith('+'):
        return phone
    
    return None


def send_sms(to_number, message, from_number=None):
    """
    Send a single SMS message.
    
    Args:
        to_number: Recipient phone number (any format, will be normalized)
        message: Message body (max 1600 characters for long SMS)
        from_number: Optional sender number (defaults to configured Twilio number)
        
    Returns:
        dict with 'success', 'message_sid', 'error' keys
    """
    try:
        formatted_to = format_phone_number(to_number)
        if not formatted_to:
            return {
                'success': False,
                'message_sid': None,
                'error': f'Invalid phone number format: {to_number}'
            }
        
        client = get_twilio_client()
        
        if from_number is None:
            from_number = get_twilio_phone_number()
        
        if not from_number:
            return {
                'success': False,
                'message_sid': None,
                'error': 'No Twilio phone number configured'
            }
        
        sms = client.messages.create(
            body=message,
            from_=from_number,
            to=formatted_to
        )
        
        return {
            'success': True,
            'message_sid': sms.sid,
            'error': None,
            'status': sms.status,
            'to': formatted_to,
            'from': from_number
        }
        
    except Exception as e:
        return {
            'success': False,
            'message_sid': None,
            'error': str(e)
        }


def send_bulk_sms(recipients, message):
    """
    Send SMS to multiple recipients.
    
    Args:
        recipients: List of phone numbers
        message: Message body
        
    Returns:
        dict with 'total', 'sent', 'failed', 'results' keys
    """
    results = []
    sent_count = 0
    failed_count = 0
    
    for phone in recipients:
        result = send_sms(phone, message)
        results.append({
            'phone': phone,
            'success': result['success'],
            'message_sid': result.get('message_sid'),
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


def get_sms_status(message_sid):
    """
    Get the delivery status of a sent SMS.
    
    Args:
        message_sid: Twilio message SID
        
    Returns:
        dict with status info
    """
    try:
        client = get_twilio_client()
        message = client.messages(message_sid).fetch()
        
        return {
            'success': True,
            'status': message.status,
            'error_code': message.error_code,
            'error_message': message.error_message,
            'date_sent': message.date_sent,
            'date_updated': message.date_updated
        }
    except Exception as e:
        return {
            'success': False,
            'status': 'unknown',
            'error': str(e)
        }


def is_twilio_configured():
    """
    Check if Twilio credentials are configured and valid.
    Returns True if configured, False otherwise.
    """
    try:
        creds = get_twilio_credentials()
        return bool(creds.get('account_sid') and creds.get('api_key') and creds.get('phone_number'))
    except Exception:
        return False
