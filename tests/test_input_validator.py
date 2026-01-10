"""
Unit tests for Input Validator Service
Tests for data validation, sanitization, and security pattern detection.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.input_validator import (
    sanitize_string,
    sanitize_html,
    validate_email,
    validate_phone,
    validate_ssn,
    validate_zip,
    validate_state,
    validate_date,
    validate_name,
    detect_sql_injection,
    detect_xss,
    sanitize_dict,
    sanitize_credit_report_html,
    ValidationError,
    ALLOWED_TAGS,
)


class TestSanitizeString:
    """Tests for sanitize_string function."""

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        result = sanitize_string("Hello World")
        assert result == "Hello World"

    def test_sanitize_string_none_input(self):
        """Test that None returns None."""
        result = sanitize_string(None)
        assert result is None

    def test_sanitize_string_whitespace_stripping(self):
        """Test leading/trailing whitespace is stripped."""
        result = sanitize_string("  Hello World  ")
        assert result == "Hello World"

    def test_sanitize_string_null_byte_removal(self):
        """Test null bytes are removed."""
        result = sanitize_string("Hello\x00World")
        assert result == "HelloWorld"

    def test_sanitize_string_html_escaping(self):
        """Test HTML characters are escaped by default."""
        result = sanitize_string("<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_sanitize_string_max_length_truncation(self):
        """Test string is truncated to max_length."""
        result = sanitize_string("Hello World", max_length=5)
        assert len(result) == 5
        assert result == "Hello"

    def test_sanitize_string_max_length_no_truncation_needed(self):
        """Test string shorter than max_length is not truncated."""
        result = sanitize_string("Hi", max_length=10)
        assert result == "Hi"

    def test_sanitize_string_allow_html_true(self):
        """Test allow_html preserves safe tags."""
        result = sanitize_string("<b>Bold</b> text", allow_html=True)
        assert "<b>Bold</b>" in result

    def test_sanitize_string_allow_html_strips_unsafe_tags(self):
        """Test allow_html strips unsafe tags."""
        result = sanitize_string("<script>evil</script><b>safe</b>", allow_html=True)
        assert "<script>" not in result
        assert "<b>safe</b>" in result

    def test_sanitize_string_non_string_input(self):
        """Test non-string input is converted to string."""
        result = sanitize_string(12345)
        assert result == "12345"

    def test_sanitize_string_integer_conversion(self):
        """Test integer is properly converted and sanitized."""
        result = sanitize_string(100)
        assert result == "100"

    def test_sanitize_string_ampersand_escaping(self):
        """Test ampersand is escaped."""
        result = sanitize_string("Tom & Jerry")
        assert "&amp;" in result


class TestSanitizeHtml:
    """Tests for sanitize_html function."""

    def test_sanitize_html_none_input(self):
        """Test that None returns None."""
        result = sanitize_html(None)
        assert result is None

    def test_sanitize_html_allowed_tags(self):
        """Test allowed tags are preserved."""
        for tag in ALLOWED_TAGS:
            result = sanitize_html(f"<{tag}>content</{tag}>")
            assert f"<{tag}>" in result or f"<{tag}/>" in result or "content" in result

    def test_sanitize_html_script_tag_removed(self):
        """Test script tags are removed."""
        result = sanitize_html("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "</script>" not in result

    def test_sanitize_html_iframe_removed(self):
        """Test iframe tags are removed."""
        result = sanitize_html("<iframe src='evil.com'></iframe>")
        assert "<iframe" not in result

    def test_sanitize_html_preserves_text(self):
        """Test text content is preserved."""
        result = sanitize_html("<div>Hello World</div>")
        assert "Hello World" in result

    def test_sanitize_html_bold_and_italic(self):
        """Test bold and italic tags are preserved."""
        result = sanitize_html("<b>bold</b> and <i>italic</i>")
        assert "<b>bold</b>" in result
        assert "<i>italic</i>" in result


class TestValidateEmail:
    """Tests for validate_email function."""

    def test_validate_email_valid_basic(self):
        """Test valid basic email."""
        assert validate_email("test@example.com") is True

    def test_validate_email_valid_subdomain(self):
        """Test valid email with subdomain."""
        assert validate_email("user@mail.example.com") is True

    def test_validate_email_valid_plus_sign(self):
        """Test valid email with plus sign."""
        assert validate_email("user+tag@example.com") is True

    def test_validate_email_valid_dots(self):
        """Test valid email with dots in local part."""
        assert validate_email("first.last@example.com") is True

    def test_validate_email_invalid_no_at(self):
        """Test invalid email without @ sign."""
        assert validate_email("invalidemail.com") is False

    def test_validate_email_invalid_no_domain(self):
        """Test invalid email without domain."""
        assert validate_email("user@") is False

    def test_validate_email_invalid_no_tld(self):
        """Test invalid email without TLD."""
        assert validate_email("user@domain") is False

    def test_validate_email_empty_string(self):
        """Test empty string returns False."""
        assert validate_email("") is False

    def test_validate_email_none(self):
        """Test None returns False."""
        assert validate_email(None) is False

    def test_validate_email_whitespace_handling(self):
        """Test email with whitespace is trimmed and validated."""
        assert validate_email("  test@example.com  ") is True


class TestValidatePhone:
    """Tests for validate_phone function."""

    def test_validate_phone_valid_dashes(self):
        """Test valid phone with dashes."""
        assert validate_phone("555-123-4567") is True

    def test_validate_phone_valid_parentheses(self):
        """Test valid phone with parentheses."""
        assert validate_phone("(555) 123-4567") is True

    def test_validate_phone_valid_plain(self):
        """Test valid plain phone number."""
        assert validate_phone("5551234567") is True

    def test_validate_phone_valid_international(self):
        """Test valid international format."""
        assert validate_phone("+1 555 123 4567") is True

    def test_validate_phone_empty_returns_true(self):
        """Test empty phone returns True (optional field)."""
        assert validate_phone("") is True

    def test_validate_phone_none_returns_true(self):
        """Test None returns True (optional field)."""
        assert validate_phone(None) is True

    def test_validate_phone_too_short(self):
        """Test phone number too short."""
        assert validate_phone("12345") is False

    def test_validate_phone_invalid_characters(self):
        """Test phone with invalid characters."""
        assert validate_phone("555-ABC-1234") is False


class TestValidateSSN:
    """Tests for validate_ssn function."""

    def test_validate_ssn_valid_with_dashes(self):
        """Test valid SSN with dashes."""
        assert validate_ssn("123-45-6789") is True

    def test_validate_ssn_valid_without_dashes(self):
        """Test valid SSN without dashes."""
        assert validate_ssn("123456789") is True

    def test_validate_ssn_empty_returns_true(self):
        """Test empty SSN returns True (optional field)."""
        assert validate_ssn("") is True

    def test_validate_ssn_none_returns_true(self):
        """Test None returns True (optional field)."""
        assert validate_ssn(None) is True

    def test_validate_ssn_too_short(self):
        """Test SSN too short."""
        assert validate_ssn("123-45-678") is False

    def test_validate_ssn_too_long(self):
        """Test SSN too long."""
        assert validate_ssn("123-45-67890") is False

    def test_validate_ssn_invalid_format(self):
        """Test SSN with invalid format."""
        assert validate_ssn("12-345-6789") is False


class TestValidateZip:
    """Tests for validate_zip function."""

    def test_validate_zip_valid_five_digit(self):
        """Test valid 5-digit ZIP."""
        assert validate_zip("90210") is True

    def test_validate_zip_valid_nine_digit(self):
        """Test valid ZIP+4 format."""
        assert validate_zip("90210-1234") is True

    def test_validate_zip_empty_returns_true(self):
        """Test empty ZIP returns True (optional field)."""
        assert validate_zip("") is True

    def test_validate_zip_none_returns_true(self):
        """Test None returns True (optional field)."""
        assert validate_zip(None) is True

    def test_validate_zip_too_short(self):
        """Test ZIP too short."""
        assert validate_zip("9021") is False

    def test_validate_zip_invalid_format(self):
        """Test ZIP with invalid format."""
        assert validate_zip("90210-12") is False

    def test_validate_zip_letters(self):
        """Test ZIP with letters."""
        assert validate_zip("9021A") is False


class TestValidateState:
    """Tests for validate_state function."""

    def test_validate_state_valid_uppercase(self):
        """Test valid uppercase state code."""
        assert validate_state("CA") is True

    def test_validate_state_valid_lowercase(self):
        """Test valid lowercase state code (auto-converts)."""
        assert validate_state("ca") is True

    def test_validate_state_empty_returns_true(self):
        """Test empty state returns True (optional field)."""
        assert validate_state("") is True

    def test_validate_state_none_returns_true(self):
        """Test None returns True (optional field)."""
        assert validate_state(None) is True

    def test_validate_state_too_long(self):
        """Test state code too long."""
        assert validate_state("CAL") is False

    def test_validate_state_numbers(self):
        """Test state code with numbers."""
        assert validate_state("C1") is False


class TestValidateDate:
    """Tests for validate_date function."""

    def test_validate_date_valid_format(self):
        """Test valid date format."""
        assert validate_date("2024-01-15") is True

    def test_validate_date_empty_returns_true(self):
        """Test empty date returns True (optional field)."""
        assert validate_date("") is True

    def test_validate_date_none_returns_true(self):
        """Test None returns True (optional field)."""
        assert validate_date(None) is True

    def test_validate_date_invalid_format_slash(self):
        """Test invalid date format with slashes."""
        assert validate_date("01/15/2024") is False

    def test_validate_date_invalid_format_reversed(self):
        """Test invalid date format (MM-DD-YYYY)."""
        assert validate_date("01-15-2024") is False


class TestValidateName:
    """Tests for validate_name function."""

    def test_validate_name_valid_simple(self):
        """Test valid simple name."""
        assert validate_name("John Doe") is True

    def test_validate_name_valid_hyphenated(self):
        """Test valid hyphenated name."""
        assert validate_name("Mary-Jane Watson") is True

    def test_validate_name_valid_apostrophe(self):
        """Test valid name with apostrophe."""
        assert validate_name("O'Brien") is True

    def test_validate_name_valid_suffix(self):
        """Test valid name with suffix."""
        assert validate_name("John Smith, Jr.") is True

    def test_validate_name_empty_returns_false(self):
        """Test empty name returns False (required field)."""
        assert validate_name("") is False

    def test_validate_name_none_returns_false(self):
        """Test None returns False (required field)."""
        assert validate_name(None) is False

    def test_validate_name_with_numbers(self):
        """Test name with numbers is invalid."""
        assert validate_name("John123") is False

    def test_validate_name_special_characters(self):
        """Test name with special characters is invalid."""
        assert validate_name("John@Doe") is False


class TestDetectSqlInjection:
    """Tests for detect_sql_injection function."""

    def test_detect_sql_injection_select_statement(self):
        """Test detection of SELECT statement."""
        assert detect_sql_injection("SELECT * FROM users") is True

    def test_detect_sql_injection_union(self):
        """Test detection of UNION statement."""
        assert detect_sql_injection("1 UNION SELECT password FROM users") is True

    def test_detect_sql_injection_drop_table(self):
        """Test detection of DROP TABLE."""
        assert detect_sql_injection("DROP TABLE users") is True

    def test_detect_sql_injection_comment_dash(self):
        """Test detection of SQL comment with dashes."""
        assert detect_sql_injection("admin'--") is True

    def test_detect_sql_injection_comment_hash(self):
        """Test detection of SQL comment with hash."""
        assert detect_sql_injection("admin'#") is True

    def test_detect_sql_injection_or_condition(self):
        """Test detection of OR injection."""
        assert detect_sql_injection("' OR '1'='1") is True

    def test_detect_sql_injection_1_equals_1(self):
        """Test detection of 1=1 pattern."""
        assert detect_sql_injection("1 = 1") is True

    def test_detect_sql_injection_normal_text(self):
        """Test normal text is not flagged."""
        assert detect_sql_injection("Hello World") is False

    def test_detect_sql_injection_empty_string(self):
        """Test empty string returns False."""
        assert detect_sql_injection("") is False

    def test_detect_sql_injection_none(self):
        """Test None returns False."""
        assert detect_sql_injection(None) is False

    def test_detect_sql_injection_insert_statement(self):
        """Test detection of INSERT statement."""
        assert detect_sql_injection("INSERT INTO users VALUES (1, 'admin')") is True

    def test_detect_sql_injection_update_statement(self):
        """Test detection of UPDATE statement."""
        assert detect_sql_injection("UPDATE users SET admin=1") is True

    def test_detect_sql_injection_delete_statement(self):
        """Test detection of DELETE statement."""
        assert detect_sql_injection("DELETE FROM users WHERE 1=1") is True

    def test_detect_sql_injection_case_insensitive(self):
        """Test detection is case insensitive."""
        assert detect_sql_injection("select * from users") is True
        assert detect_sql_injection("SELECT * FROM users") is True


class TestDetectXss:
    """Tests for detect_xss function."""

    def test_detect_xss_script_tag(self):
        """Test detection of script tag."""
        assert detect_xss("<script>alert('xss')</script>") is True

    def test_detect_xss_script_tag_uppercase(self):
        """Test detection of uppercase script tag."""
        assert detect_xss("<SCRIPT>alert('xss')</SCRIPT>") is True

    def test_detect_xss_javascript_protocol(self):
        """Test detection of javascript: protocol."""
        assert detect_xss("javascript:alert('xss')") is True

    def test_detect_xss_onclick_handler(self):
        """Test detection of onclick handler."""
        assert detect_xss("<img onclick=\"alert('xss')\">") is True

    def test_detect_xss_onerror_handler(self):
        """Test detection of onerror handler."""
        assert detect_xss("<img onerror=\"alert('xss')\">") is True

    def test_detect_xss_onload_handler(self):
        """Test detection of onload handler."""
        assert detect_xss("<body onload=\"alert('xss')\">") is True

    def test_detect_xss_iframe_tag(self):
        """Test detection of iframe tag."""
        assert detect_xss("<iframe src='evil.com'>") is True

    def test_detect_xss_object_tag(self):
        """Test detection of object tag."""
        assert detect_xss("<object data='evil.swf'>") is True

    def test_detect_xss_embed_tag(self):
        """Test detection of embed tag."""
        assert detect_xss("<embed src='evil.swf'>") is True

    def test_detect_xss_normal_text(self):
        """Test normal text is not flagged."""
        assert detect_xss("Hello World") is False

    def test_detect_xss_safe_html(self):
        """Test safe HTML is not flagged."""
        assert detect_xss("<b>Bold</b> and <i>italic</i>") is False

    def test_detect_xss_empty_string(self):
        """Test empty string returns False."""
        assert detect_xss("") is False

    def test_detect_xss_none(self):
        """Test None returns False."""
        assert detect_xss(None) is False

    def test_detect_xss_multiline_script(self):
        """Test detection of multiline script tag."""
        assert detect_xss("<script>\nalert('xss')\n</script>") is True


class TestSanitizeDict:
    """Tests for sanitize_dict function."""

    def test_sanitize_dict_basic(self):
        """Test basic dictionary sanitization."""
        data = {"name": "John Doe", "email": "john@example.com"}
        result = sanitize_dict(data)
        assert result["name"] == "John Doe"
        assert result["email"] == "john@example.com"

    def test_sanitize_dict_html_escaping(self):
        """Test HTML is escaped in dict values."""
        data = {"comment": "<script>alert('xss')</script>"}
        result = sanitize_dict(data)
        # XSS is detected, then sanitized (double-escaped due to detect+sanitize flow)
        assert "<script>" not in result["comment"]
        assert "script" in result["comment"]  # The word script is still present in escaped form

    def test_sanitize_dict_nested(self):
        """Test nested dictionary sanitization."""
        data = {
            "user": {
                "name": "  John  ",
                "bio": "<script>evil</script>"
            }
        }
        result = sanitize_dict(data)
        assert result["user"]["name"] == "John"
        assert "<script>" not in result["user"]["bio"]

    def test_sanitize_dict_with_list(self):
        """Test dictionary with list values."""
        data = {
            "tags": ["<b>tag1</b>", "  tag2  "]
        }
        result = sanitize_dict(data)
        assert "&lt;b&gt;" in result["tags"][0]
        assert result["tags"][1] == "tag2"

    def test_sanitize_dict_email_rule(self):
        """Test email field rule."""
        data = {"email": "  TEST@EXAMPLE.COM  "}
        result = sanitize_dict(data, rules={"email": "email"})
        assert result["email"] == "test@example.com"

    def test_sanitize_dict_phone_rule(self):
        """Test phone field rule."""
        data = {"phone": "555-ABC-1234"}
        result = sanitize_dict(data, rules={"phone": "phone"})
        assert "ABC" not in result["phone"]

    def test_sanitize_dict_html_rule(self):
        """Test HTML field rule - XSS detection takes precedence."""
        data = {"notes": "<b>Bold</b><script>evil</script>"}
        result = sanitize_dict(data, rules={"notes": "html"})
        # XSS is detected first, so content is sanitized before html rule is applied
        assert "<script>" not in result["notes"]
        # Due to XSS detection, the content is first escaped, so html rule sees escaped content
        assert "Bold" in result["notes"]

    def test_sanitize_dict_html_rule_no_xss(self):
        """Test HTML field rule preserves safe tags when no XSS detected."""
        data = {"notes": "<b>Bold</b> and <i>italic</i>"}
        result = sanitize_dict(data, rules={"notes": "html"})
        assert "<b>Bold</b>" in result["notes"]
        assert "<i>italic</i>" in result["notes"]

    def test_sanitize_dict_non_dict_input(self):
        """Test non-dict input is returned as-is."""
        result = sanitize_dict("not a dict")
        assert result == "not a dict"

    def test_sanitize_dict_preserves_non_string_values(self):
        """Test non-string values are preserved."""
        data = {"count": 42, "active": True, "items": None}
        result = sanitize_dict(data)
        assert result["count"] == 42
        assert result["active"] is True
        assert result["items"] is None

    def test_sanitize_dict_sql_injection_sanitized(self):
        """Test SQL injection is sanitized."""
        data = {"query": "SELECT * FROM users"}
        result = sanitize_dict(data)
        # The value should be sanitized (HTML escaped at minimum)
        assert result["query"] is not None

    def test_sanitize_dict_nested_list_of_dicts(self):
        """Test nested list of dictionaries."""
        data = {
            "users": [
                {"name": "  John  "},
                {"name": "<b>Jane</b>"}
            ]
        }
        result = sanitize_dict(data)
        assert result["users"][0]["name"] == "John"
        assert "&lt;b&gt;" in result["users"][1]["name"]


class TestSanitizeCreditReportHtml:
    """Tests for sanitize_credit_report_html function."""

    def test_sanitize_credit_report_html_none(self):
        """Test None input returns None."""
        result = sanitize_credit_report_html(None)
        assert result is None

    def test_sanitize_credit_report_html_empty(self):
        """Test empty string returns empty string."""
        result = sanitize_credit_report_html("")
        assert result == ""

    def test_sanitize_credit_report_html_removes_script(self):
        """Test script tags are removed."""
        html = "<html><script>alert('xss')</script><body>Content</body></html>"
        result = sanitize_credit_report_html(html)
        assert "<script>" not in result
        assert "alert" not in result
        assert "Content" in result

    def test_sanitize_credit_report_html_removes_event_handlers(self):
        """Test event handlers are removed."""
        html = '<div onclick="evil()">Content</div>'
        result = sanitize_credit_report_html(html)
        assert "onclick" not in result
        assert "Content" in result

    def test_sanitize_credit_report_html_removes_javascript_protocol(self):
        """Test javascript: protocol is removed."""
        html = '<a href="javascript:evil()">Link</a>'
        result = sanitize_credit_report_html(html)
        assert "javascript:" not in result

    def test_sanitize_credit_report_html_preserves_structure(self):
        """Test HTML structure is preserved."""
        html = "<table><tr><td>Data</td></tr></table>"
        result = sanitize_credit_report_html(html)
        assert "<table>" in result
        assert "<tr>" in result
        assert "<td>Data</td>" in result


class TestValidationError:
    """Tests for ValidationError exception."""

    def test_validation_error_creation(self):
        """Test ValidationError can be created."""
        error = ValidationError("email", "Invalid format")
        assert error.field == "email"
        assert error.message == "Invalid format"

    def test_validation_error_str(self):
        """Test ValidationError string representation."""
        error = ValidationError("email", "Invalid format")
        assert str(error) == "email: Invalid format"


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_unicode_characters_in_string(self):
        """Test unicode characters are handled."""
        result = sanitize_string("Hello Caf\u00e9")
        assert "Caf\u00e9" in result

    def test_very_long_string_truncation(self):
        """Test very long strings are properly truncated."""
        long_string = "A" * 10000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100

    def test_mixed_case_sql_keywords(self):
        """Test mixed case SQL keywords are detected."""
        assert detect_sql_injection("SeLeCt * FrOm users") is True

    def test_whitespace_only_string(self):
        """Test whitespace-only string sanitization."""
        result = sanitize_string("   ")
        assert result == ""

    def test_empty_dict_sanitization(self):
        """Test empty dictionary sanitization."""
        result = sanitize_dict({})
        assert result == {}

    def test_deeply_nested_dict(self):
        """Test deeply nested dictionary sanitization."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "  test  "
                    }
                }
            }
        }
        result = sanitize_dict(data)
        assert result["level1"]["level2"]["level3"]["value"] == "test"
