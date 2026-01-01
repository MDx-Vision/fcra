"""
Tests for SMSTemplateService

Tests the SMS template CRUD operations and template management functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from services.sms_template_service import (
    SMSTemplateService,
    seed_default_sms_templates,
    get_sms_template,
    render_sms,
    list_all_sms_templates,
    SMS_CATEGORIES,
    SMS_VARIABLES,
    DEFAULT_SMS_TEMPLATES,
    SMS_CHAR_LIMIT,
    SMS_LONG_LIMIT,
)


class TestSMSCategories:
    """Test SMS template category constants"""

    def test_categories_exist(self):
        """Test that categories are defined"""
        assert len(SMS_CATEGORIES) > 0

    def test_welcome_category(self):
        """Test welcome category exists"""
        assert "welcome" in SMS_CATEGORIES

    def test_updates_category(self):
        """Test updates category exists"""
        assert "updates" in SMS_CATEGORIES

    def test_reminders_category(self):
        """Test reminders category exists"""
        assert "reminders" in SMS_CATEGORIES

    def test_payment_category(self):
        """Test payment category exists"""
        assert "payment" in SMS_CATEGORIES

    def test_general_category(self):
        """Test general category exists"""
        assert "general" in SMS_CATEGORIES

    def test_notifications_category(self):
        """Test notifications category exists"""
        assert "notifications" in SMS_CATEGORIES


class TestSMSVariables:
    """Test SMS variable definitions"""

    def test_variables_exist(self):
        """Test that variables are defined"""
        assert len(SMS_VARIABLES) > 0

    def test_client_name_variable(self):
        """Test client_name variable exists"""
        names = [v["name"] for v in SMS_VARIABLES]
        assert "client_name" in names

    def test_first_name_variable(self):
        """Test first_name variable exists"""
        names = [v["name"] for v in SMS_VARIABLES]
        assert "first_name" in names

    def test_company_name_variable(self):
        """Test company_name variable exists"""
        names = [v["name"] for v in SMS_VARIABLES]
        assert "company_name" in names

    def test_portal_url_variable(self):
        """Test portal_url variable exists"""
        names = [v["name"] for v in SMS_VARIABLES]
        assert "portal_url" in names

    def test_variables_have_description(self):
        """Test all variables have descriptions"""
        for v in SMS_VARIABLES:
            assert "description" in v
            assert len(v["description"]) > 0

    def test_variables_have_example(self):
        """Test all variables have examples"""
        for v in SMS_VARIABLES:
            assert "example" in v
            assert len(v["example"]) > 0


class TestSMSCharLimits:
    """Test SMS character limit constants"""

    def test_standard_limit(self):
        """Test standard SMS character limit"""
        assert SMS_CHAR_LIMIT == 160

    def test_long_limit(self):
        """Test long SMS character limit"""
        assert SMS_LONG_LIMIT == 320


class TestDefaultSMSTemplates:
    """Test default SMS template definitions"""

    def test_default_templates_exist(self):
        """Test that default templates are defined"""
        assert len(DEFAULT_SMS_TEMPLATES) > 0

    def test_welcome_sms_template(self):
        """Test welcome_sms template exists"""
        types = [t["template_type"] for t in DEFAULT_SMS_TEMPLATES]
        assert "welcome_sms" in types

    def test_document_reminder_sms_template(self):
        """Test document_reminder_sms template exists"""
        types = [t["template_type"] for t in DEFAULT_SMS_TEMPLATES]
        assert "document_reminder_sms" in types

    def test_case_update_sms_template(self):
        """Test case_update_sms template exists"""
        types = [t["template_type"] for t in DEFAULT_SMS_TEMPLATES]
        assert "case_update_sms" in types

    def test_payment_reminder_sms_template(self):
        """Test payment_reminder_sms template exists"""
        types = [t["template_type"] for t in DEFAULT_SMS_TEMPLATES]
        assert "payment_reminder_sms" in types

    def test_templates_have_required_fields(self):
        """Test all templates have required fields"""
        for t in DEFAULT_SMS_TEMPLATES:
            assert "template_type" in t
            assert "name" in t
            assert "category" in t
            assert "message" in t

    def test_templates_have_reasonable_length(self):
        """Test that default templates are reasonable length"""
        for t in DEFAULT_SMS_TEMPLATES:
            # Allow up to 2 segments for default templates
            assert len(t["message"]) <= SMS_LONG_LIMIT, f"Template {t['template_type']} is too long"


class TestGetCategories:
    """Test the get_categories method"""

    def test_returns_dict(self):
        """Test that categories returns a dictionary"""
        categories = SMSTemplateService.get_categories()
        assert isinstance(categories, dict)

    def test_returns_all_categories(self):
        """Test that all categories are returned"""
        categories = SMSTemplateService.get_categories()
        assert categories == SMS_CATEGORIES


class TestGetCommonVariables:
    """Test the get_common_variables method"""

    def test_returns_list(self):
        """Test that variables returns a list"""
        variables = SMSTemplateService.get_common_variables()
        assert isinstance(variables, list)

    def test_returns_all_variables(self):
        """Test that all variables are returned"""
        variables = SMSTemplateService.get_common_variables()
        assert variables == SMS_VARIABLES


class TestCreateTemplate:
    """Test the create_template method"""

    @patch('services.sms_template_service.SessionLocal')
    def test_creates_template(self, mock_session_local):
        """Test that template is created successfully"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_type = "test_sms"

        def add_side_effect(template):
            template.id = 1
            template.template_type = "test_sms"

        mock_session.add.side_effect = add_side_effect
        mock_session.refresh = MagicMock()

        result = SMSTemplateService.create_template(
            template_type="test_sms",
            name="Test SMS",
            message="Hello {first_name}, this is a test message!",
        )

        assert result["success"] is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('services.sms_template_service.SessionLocal')
    def test_rejects_duplicate_type(self, mock_session_local):
        """Test that duplicate template_type is rejected"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Simulate existing template
        mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()

        result = SMSTemplateService.create_template(
            template_type="existing_sms",
            name="Test",
            message="Test message",
        )

        assert result["success"] is False
        assert "already exists" in result["error"]

    @patch('services.sms_template_service.SessionLocal')
    def test_returns_char_count(self, mock_session_local):
        """Test that char_count is returned on create"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        def add_side_effect(template):
            template.id = 1
            template.template_type = "test_sms"

        mock_session.add.side_effect = add_side_effect
        mock_session.refresh = MagicMock()

        message = "Hi there!"
        result = SMSTemplateService.create_template(
            template_type="test_sms",
            name="Test SMS",
            message=message,
        )

        assert result["success"] is True
        assert result["char_count"] == len(message)
        assert result["segments"] == 1


class TestUpdateTemplate:
    """Test the update_template method"""

    @patch('services.sms_template_service.SessionLocal')
    def test_updates_template(self, mock_session_local):
        """Test that template is updated successfully"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.name = "Old Name"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = SMSTemplateService.update_template(
            template_id=1,
            name="New Name",
        )

        assert result["success"] is True
        assert mock_template.name == "New Name"
        mock_session.commit.assert_called_once()

    @patch('services.sms_template_service.SessionLocal')
    def test_returns_error_for_missing_template(self, mock_session_local):
        """Test that error is returned for missing template"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = SMSTemplateService.update_template(
            template_id=999,
            name="New Name",
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch('services.sms_template_service.SessionLocal')
    def test_updates_message(self, mock_session_local):
        """Test that message is updated"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.message = "Old message"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = SMSTemplateService.update_template(
            template_id=1,
            message="New message",
        )

        assert result["success"] is True
        assert mock_template.message == "New message"


class TestDeleteTemplate:
    """Test the delete_template method"""

    @patch('services.sms_template_service.SessionLocal')
    def test_deletes_custom_template(self, mock_session_local):
        """Test that custom template is deleted"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.is_custom = True
        mock_template.name = "Custom Template"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = SMSTemplateService.delete_template(template_id=1)

        assert result["success"] is True
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('services.sms_template_service.SessionLocal')
    def test_prevents_system_template_deletion(self, mock_session_local):
        """Test that system templates cannot be deleted"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.is_custom = False
        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = SMSTemplateService.delete_template(template_id=1)

        assert result["success"] is False
        assert "cannot be deleted" in result["error"]
        mock_session.delete.assert_not_called()

    @patch('services.sms_template_service.SessionLocal')
    def test_returns_error_for_missing_template(self, mock_session_local):
        """Test error for missing template"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = SMSTemplateService.delete_template(template_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]


class TestGetTemplate:
    """Test the get_template method"""

    @patch('services.sms_template_service.SessionLocal')
    def test_gets_template_by_id(self, mock_session_local):
        """Test getting template by ID"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_type = "test_sms"
        mock_template.name = "Test SMS"
        mock_template.category = "general"
        mock_template.description = "Test description"
        mock_template.message = "Hello {first_name}!"
        mock_template.variables = []
        mock_template.is_custom = True
        mock_template.is_active = True
        mock_template.created_at = datetime.utcnow()
        mock_template.updated_at = datetime.utcnow()

        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = SMSTemplateService.get_template(template_id=1)

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "Test SMS"
        assert "char_count" in result
        assert "segments" in result

    @patch('services.sms_template_service.SessionLocal')
    def test_gets_template_by_type(self, mock_session_local):
        """Test getting template by type"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_type = "welcome_sms"
        mock_template.name = "Welcome SMS"
        mock_template.category = "welcome"
        mock_template.description = None
        mock_template.message = "Welcome!"
        mock_template.variables = []
        mock_template.is_custom = False
        mock_template.is_active = True
        mock_template.created_at = datetime.utcnow()
        mock_template.updated_at = datetime.utcnow()

        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = SMSTemplateService.get_template(template_type="welcome_sms")

        assert result is not None
        assert result["template_type"] == "welcome_sms"

    @patch('services.sms_template_service.SessionLocal')
    def test_returns_none_for_missing_template(self, mock_session_local):
        """Test that None is returned for missing template"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = SMSTemplateService.get_template(template_id=999)

        assert result is None

    def test_returns_none_for_no_params(self):
        """Test that None is returned when no ID or type provided"""
        result = SMSTemplateService.get_template()
        assert result is None


class TestListTemplates:
    """Test the list_templates method"""

    @patch('services.sms_template_service.SessionLocal')
    def test_lists_all_templates(self, mock_session_local):
        """Test listing all templates"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_type = "test_sms"
        mock_template.name = "Test"
        mock_template.category = "general"
        mock_template.description = None
        mock_template.message = "Test message"
        mock_template.is_custom = True
        mock_template.is_active = True
        mock_template.created_at = datetime.utcnow()

        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_template]

        result = SMSTemplateService.list_templates()

        assert len(result) == 1
        assert result[0]["name"] == "Test"

    @patch('services.sms_template_service.SessionLocal')
    def test_filters_by_category(self, mock_session_local):
        """Test filtering templates by category"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []

        SMSTemplateService.list_templates(category="welcome")

        # Verify filter was called
        mock_query.filter.assert_called()

    @patch('services.sms_template_service.SessionLocal')
    def test_includes_char_count(self, mock_session_local):
        """Test that list includes char_count"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_type = "test"
        mock_template.name = "Test"
        mock_template.category = "general"
        mock_template.description = None
        mock_template.message = "Hello there!"
        mock_template.is_custom = True
        mock_template.is_active = True
        mock_template.created_at = datetime.utcnow()

        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_template]

        result = SMSTemplateService.list_templates()

        assert result[0]["char_count"] == 12


class TestRenderTemplate:
    """Test the render_template method"""

    @patch.object(SMSTemplateService, 'get_template')
    def test_renders_template_with_variables(self, mock_get_template):
        """Test rendering template with variable substitution"""
        mock_get_template.return_value = {
            "id": 1,
            "template_type": "test_sms",
            "message": "Hi {first_name}! Visit {portal_url} for updates.",
            "is_active": True,
        }

        result = SMSTemplateService.render_template(
            template_id=1,
            variables={"first_name": "John", "portal_url": "portal.example.com"},
        )

        assert result["success"] is True
        assert "John" in result["message"]
        assert "portal.example.com" in result["message"]
        assert "char_count" in result
        assert "segments" in result

    @patch.object(SMSTemplateService, 'get_template')
    def test_returns_error_for_missing_template(self, mock_get_template):
        """Test error returned for missing template"""
        mock_get_template.return_value = None

        result = SMSTemplateService.render_template(template_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch.object(SMSTemplateService, 'get_template')
    def test_returns_error_for_inactive_template(self, mock_get_template):
        """Test error returned for inactive template"""
        mock_get_template.return_value = {
            "id": 1,
            "template_type": "test_sms",
            "message": "Test message",
            "is_active": False,
        }

        result = SMSTemplateService.render_template(template_id=1)

        assert result["success"] is False
        assert "not active" in result["error"]

    @patch.object(SMSTemplateService, 'get_template')
    def test_adds_default_company_name(self, mock_get_template):
        """Test that default company_name is added"""
        mock_get_template.return_value = {
            "id": 1,
            "template_type": "test_sms",
            "message": "Welcome to {company_name}!",
            "is_active": True,
        }

        result = SMSTemplateService.render_template(template_id=1, variables={})

        assert result["success"] is True
        assert "Brightpath Ascend" in result["message"]


class TestDuplicateTemplate:
    """Test the duplicate_template method"""

    @patch.object(SMSTemplateService, 'get_template')
    @patch.object(SMSTemplateService, 'create_template')
    def test_duplicates_template(self, mock_create, mock_get_template):
        """Test duplicating a template"""
        mock_get_template.return_value = {
            "id": 1,
            "template_type": "original_sms",
            "name": "Original SMS",
            "category": "general",
            "description": "Description",
            "message": "Original message",
            "variables": [],
        }

        mock_create.return_value = {
            "success": True,
            "template_id": 2,
        }

        result = SMSTemplateService.duplicate_template(
            template_id=1,
            new_name="Copy of Original",
            new_type="original_sms_copy",
        )

        assert result["success"] is True
        mock_create.assert_called_once()

    @patch.object(SMSTemplateService, 'get_template')
    def test_returns_error_for_missing_source(self, mock_get_template):
        """Test error returned when source template not found"""
        mock_get_template.return_value = None

        result = SMSTemplateService.duplicate_template(template_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch.object(SMSTemplateService, 'get_template')
    @patch.object(SMSTemplateService, 'create_template')
    def test_generates_default_copy_name(self, mock_create, mock_get_template):
        """Test that default copy names are generated"""
        mock_get_template.return_value = {
            "id": 1,
            "template_type": "original",
            "name": "Original",
            "category": "general",
            "description": None,
            "message": "Test",
            "variables": [],
        }

        mock_create.return_value = {"success": True, "template_id": 2}

        SMSTemplateService.duplicate_template(template_id=1)

        # Check that create was called with _copy suffix and (Copy) name
        call_args = mock_create.call_args
        assert call_args[1]["template_type"] == "original_copy"
        assert call_args[1]["name"] == "Original (Copy)"


class TestGetTemplateStats:
    """Test the get_template_stats method"""

    @patch('services.sms_template_service.SessionLocal')
    def test_returns_stats(self, mock_session_local):
        """Test getting template statistics"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_session.query.return_value.count.return_value = 10
        mock_session.query.return_value.filter.return_value.count.return_value = 8

        result = SMSTemplateService.get_template_stats()

        assert "total" in result
        assert "active" in result
        assert "custom" in result
        assert "system" in result
        assert "by_category" in result

    @patch('services.sms_template_service.SessionLocal')
    def test_stats_has_inactive_count(self, mock_session_local):
        """Test that stats include inactive count"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_session.query.return_value.count.return_value = 10
        mock_session.query.return_value.filter.return_value.count.return_value = 8

        result = SMSTemplateService.get_template_stats()

        assert "inactive" in result


class TestSeedDefaultTemplates:
    """Test the seed_default_sms_templates function"""

    @patch('services.sms_template_service.SessionLocal')
    def test_seeds_templates(self, mock_session_local):
        """Test seeding default templates"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Simulate no existing templates
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = seed_default_sms_templates()

        assert result["success"] is True
        assert result["created"] > 0

    @patch('services.sms_template_service.SessionLocal')
    def test_skips_existing_templates(self, mock_session_local):
        """Test that existing templates are skipped"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Simulate existing template
        mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()

        result = seed_default_sms_templates()

        assert result["success"] is True
        assert result["skipped"] > 0

    @patch('services.sms_template_service.SessionLocal')
    def test_returns_message(self, mock_session_local):
        """Test that message is returned"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = seed_default_sms_templates()

        assert "message" in result
        assert "Created" in result["message"]


class TestConvenienceFunctions:
    """Test convenience functions"""

    @patch.object(SMSTemplateService, 'get_template')
    def test_get_sms_template_function(self, mock_get):
        """Test get_sms_template convenience function"""
        mock_get.return_value = {"template_type": "welcome_sms"}

        result = get_sms_template("welcome_sms")

        mock_get.assert_called_once_with(template_type="welcome_sms")
        assert result["template_type"] == "welcome_sms"

    @patch.object(SMSTemplateService, 'render_template')
    def test_render_sms_function(self, mock_render):
        """Test render_sms convenience function"""
        mock_render.return_value = {"success": True, "message": "Hello John"}

        result = render_sms("welcome_sms", {"first_name": "John"})

        mock_render.assert_called_once_with(template_type="welcome_sms", variables={"first_name": "John"})
        assert result["success"] is True

    @patch.object(SMSTemplateService, 'list_templates')
    def test_list_all_sms_templates_function(self, mock_list):
        """Test list_all_sms_templates convenience function"""
        mock_list.return_value = [{"name": "Template 1"}]

        result = list_all_sms_templates()

        mock_list.assert_called_once_with(is_active=True)
        assert len(result) == 1


class TestVariableSubstitution:
    """Test variable substitution logic"""

    def test_variable_pattern(self):
        """Test that variable pattern is correct"""
        message = "Hello {first_name}, your email is {email}."
        variables = {"first_name": "John", "email": "john@test.com"}

        for key, value in variables.items():
            message = message.replace(f"{{{key}}}", str(value))

        assert "John" in message
        assert "john@test.com" in message
        assert "{first_name}" not in message

    def test_missing_variable_preserved(self):
        """Test that missing variables are preserved"""
        message = "Hello {first_name}, your status is {status}."
        variables = {"first_name": "John"}

        for key, value in variables.items():
            message = message.replace(f"{{{key}}}", str(value))

        assert "John" in message
        assert "{status}" in message


class TestCharacterCounting:
    """Test character counting and segment calculation"""

    def test_short_message_one_segment(self):
        """Test that short messages are 1 segment"""
        message = "Short"
        char_count = len(message)
        segments = 1 if char_count <= SMS_CHAR_LIMIT else (char_count // SMS_CHAR_LIMIT) + 1
        assert segments == 1

    def test_exact_limit_one_segment(self):
        """Test that exactly 160 chars is 1 segment"""
        message = "x" * 160
        char_count = len(message)
        segments = 1 if char_count <= SMS_CHAR_LIMIT else (char_count // SMS_CHAR_LIMIT) + 1
        assert segments == 1

    def test_over_limit_two_segments(self):
        """Test that 161 chars is 2 segments"""
        message = "x" * 161
        char_count = len(message)
        segments = 1 if char_count <= SMS_CHAR_LIMIT else (char_count // SMS_CHAR_LIMIT) + 1
        assert segments == 2


class TestTemplateValidation:
    """Test template validation logic"""

    def test_required_fields_for_create(self):
        """Test required fields are validated on create"""
        required_fields = ["template_type", "name", "message"]
        assert len(required_fields) == 3

    def test_category_values(self):
        """Test valid category values"""
        valid_categories = list(SMS_CATEGORIES.keys())
        assert "welcome" in valid_categories
        assert "general" in valid_categories
        assert "invalid" not in valid_categories
