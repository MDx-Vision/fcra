"""
Input Validation and Sanitization for FCRA Litigation Platform

Provides:
- Data format validation (email, phone, SSN, etc.)
- HTML/script sanitization (XSS prevention)
- SQL injection pattern detection
- Request data validation decorators
"""
import re
import html
from functools import wraps
from flask import request, jsonify
import bleach

# Allowed HTML tags for rich text fields (very restrictive)
ALLOWED_TAGS = ['b', 'i', 'u', 'strong', 'em', 'p', 'br', 'ul', 'ol', 'li']
ALLOWED_ATTRIBUTES = {}

# Regex patterns for validation
PATTERNS = {
    'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
    'phone': re.compile(r'^[\d\s\-\(\)\+\.]{7,20}$'),
    'ssn': re.compile(r'^\d{3}-?\d{2}-?\d{4}$'),
    'zip': re.compile(r'^\d{5}(-\d{4})?$'),
    'state': re.compile(r'^[A-Z]{2}$'),
    'date': re.compile(r'^\d{4}-\d{2}-\d{2}$'),
    'uuid': re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.I),
    'alphanumeric': re.compile(r'^[a-zA-Z0-9\s\-_]+$'),
    'name': re.compile(r'^[a-zA-Z\s\-\'\.\,]+$'),
    'currency': re.compile(r'^\$?[\d,]+\.?\d{0,2}$'),
}

# SQL injection patterns to detect and block
SQL_INJECTION_PATTERNS = [
    re.compile(r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|TRUNCATE)\b)', re.I),
    re.compile(r'(--|#|/\*|\*/)', re.I),
    re.compile(r"('|\"|;)\s*(OR|AND)\s*('|\"|;|\d)", re.I),
    re.compile(r'\b(1\s*=\s*1|1\s*=\s*\'1\')\b', re.I),
]

# XSS patterns to detect
XSS_PATTERNS = [
    re.compile(r'<script[^>]*>.*?</script>', re.I | re.S),
    re.compile(r'javascript:', re.I),
    re.compile(r'on\w+\s*=', re.I),  # onclick=, onerror=, etc.
    re.compile(r'<iframe', re.I),
    re.compile(r'<object', re.I),
    re.compile(r'<embed', re.I),
]


class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, field, message):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def sanitize_string(value, max_length=None, allow_html=False):
    """
    Sanitize a string value.

    Args:
        value: The string to sanitize
        max_length: Maximum allowed length (truncates if exceeded)
        allow_html: If True, allows safe HTML tags; if False, escapes all HTML

    Returns:
        Sanitized string
    """
    if value is None:
        return None

    if not isinstance(value, str):
        value = str(value)

    # Strip leading/trailing whitespace
    value = value.strip()

    # Remove null bytes
    value = value.replace('\x00', '')

    # Sanitize HTML
    if allow_html:
        # Allow only safe tags
        value = bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    else:
        # Escape all HTML
        value = html.escape(value)

    # Truncate if needed
    if max_length and len(value) > max_length:
        value = value[:max_length]

    return value


def sanitize_html(value):
    """Sanitize HTML content, allowing only safe tags."""
    if value is None:
        return None
    return bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def validate_email(email):
    """Validate email format."""
    if not email:
        return False
    email = email.strip().lower()
    return bool(PATTERNS['email'].match(email))


def validate_phone(phone):
    """Validate phone number format."""
    if not phone:
        return True  # Phone is often optional
    phone = phone.strip()
    return bool(PATTERNS['phone'].match(phone))


def validate_ssn(ssn):
    """Validate SSN format (with or without dashes)."""
    if not ssn:
        return True  # SSN might be optional
    ssn = ssn.strip()
    return bool(PATTERNS['ssn'].match(ssn))


def validate_zip(zip_code):
    """Validate ZIP code format."""
    if not zip_code:
        return True
    zip_code = zip_code.strip()
    return bool(PATTERNS['zip'].match(zip_code))


def validate_state(state):
    """Validate 2-letter state code."""
    if not state:
        return True
    state = state.strip().upper()
    return bool(PATTERNS['state'].match(state))


def validate_date(date_str):
    """Validate date format (YYYY-MM-DD)."""
    if not date_str:
        return True
    return bool(PATTERNS['date'].match(date_str))


def validate_name(name):
    """Validate name contains only allowed characters."""
    if not name:
        return False
    name = name.strip()
    return bool(PATTERNS['name'].match(name)) and len(name) >= 1


def detect_sql_injection(value):
    """Check if value contains SQL injection patterns."""
    if not value or not isinstance(value, str):
        return False
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(value):
            return True
    return False


def detect_xss(value):
    """Check if value contains XSS patterns."""
    if not value or not isinstance(value, str):
        return False
    for pattern in XSS_PATTERNS:
        if pattern.search(value):
            return True
    return False


def sanitize_dict(data, rules=None):
    """
    Sanitize all string values in a dictionary.

    Args:
        data: Dictionary to sanitize
        rules: Optional dict mapping field names to validation rules
               e.g., {'email': 'email', 'phone': 'phone', 'notes': 'html'}

    Returns:
        Sanitized dictionary
    """
    if not isinstance(data, dict):
        return data

    rules = rules or {}
    sanitized = {}

    for key, value in data.items():
        if isinstance(value, str):
            # Check for SQL injection
            if detect_sql_injection(value):
                from services.logging_config import api_logger
                api_logger.warning(f"SQL injection attempt detected in field: {key}")
                value = sanitize_string(value)

            # Check for XSS
            if detect_xss(value):
                from services.logging_config import api_logger
                api_logger.warning(f"XSS attempt detected in field: {key}")
                value = sanitize_string(value)

            # Apply field-specific rules
            rule = rules.get(key)
            if rule == 'html':
                value = sanitize_html(value)
            elif rule == 'email':
                value = value.strip().lower()
            elif rule == 'phone':
                value = re.sub(r'[^\d\+\-\(\)\s]', '', value)
            else:
                value = sanitize_string(value)

        elif isinstance(value, dict):
            value = sanitize_dict(value, rules)

        elif isinstance(value, list):
            value = [sanitize_dict(v, rules) if isinstance(v, dict) else
                     sanitize_string(v) if isinstance(v, str) else v
                     for v in value]

        sanitized[key] = value

    return sanitized


def validate_request_data(required_fields=None, field_rules=None):
    """
    Decorator to validate and sanitize request JSON data.

    Args:
        required_fields: List of required field names
        field_rules: Dict mapping field names to validation rules
                    e.g., {'email': 'email', 'name': 'name'}

    Usage:
        @app.route('/api/clients/create', methods=['POST'])
        @validate_request_data(
            required_fields=['email', 'name'],
            field_rules={'email': 'email', 'phone': 'phone'}
        )
        def create_client():
            data = request.validated_data  # Use sanitized data
            ...
    """
    required_fields = required_fields or []
    field_rules = field_rules or {}

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get JSON data
            data = request.get_json(silent=True) or {}

            # Check required fields
            missing = [field for field in required_fields if not data.get(field)]
            if missing:
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields',
                    'missing_fields': missing
                }), 400

            # Validate specific fields
            errors = []
            for field, rule in field_rules.items():
                value = data.get(field)
                if value:
                    if rule == 'email' and not validate_email(value):
                        errors.append(f"Invalid email format: {field}")
                    elif rule == 'phone' and not validate_phone(value):
                        errors.append(f"Invalid phone format: {field}")
                    elif rule == 'ssn' and not validate_ssn(value):
                        errors.append(f"Invalid SSN format: {field}")
                    elif rule == 'zip' and not validate_zip(value):
                        errors.append(f"Invalid ZIP code: {field}")
                    elif rule == 'state' and not validate_state(value):
                        errors.append(f"Invalid state code: {field}")
                    elif rule == 'date' and not validate_date(value):
                        errors.append(f"Invalid date format (use YYYY-MM-DD): {field}")
                    elif rule == 'name' and not validate_name(value):
                        errors.append(f"Invalid name: {field}")

            if errors:
                return jsonify({
                    'success': False,
                    'error': 'Validation failed',
                    'errors': errors
                }), 400

            # Sanitize all data
            request.validated_data = sanitize_dict(data, field_rules)

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_credit_report_html(html_content):
    """
    Sanitize credit report HTML while preserving structure.
    More permissive than general sanitization since this is internal data.
    """
    if not html_content:
        return html_content

    # Remove script tags completely
    html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.I | re.S)

    # Remove event handlers
    html_content = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', html_content, flags=re.I)

    # Remove javascript: links
    html_content = re.sub(r'javascript:', '', html_content, flags=re.I)

    return html_content
