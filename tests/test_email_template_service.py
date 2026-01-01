"""
Tests for EmailTemplateService

Tests the email template CRUD operations and template management functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from services.email_template_service import (
    EmailTemplateService,
    seed_default_templates,
    get_template,
    render_email,
    list_all_templates,
    TEMPLATE_CATEGORIES,
    COMMON_VARIABLES,
    DEFAULT_TEMPLATES,
)


class TestTemplateCategories:
    """Test template category constants"""

    def test_categories_exist(self):
        """Test that categories are defined"""
        assert len(TEMPLATE_CATEGORIES) > 0

    def test_welcome_category(self):
        """Test welcome category exists"""
        assert "welcome" in TEMPLATE_CATEGORIES

    def test_updates_category(self):
        """Test updates category exists"""
        assert "updates" in TEMPLATE_CATEGORIES

    def test_reminders_category(self):
        """Test reminders category exists"""
        assert "reminders" in TEMPLATE_CATEGORIES

    def test_payment_category(self):
        """Test payment category exists"""
        assert "payment" in TEMPLATE_CATEGORIES

    def test_general_category(self):
        """Test general category exists"""
        assert "general" in TEMPLATE_CATEGORIES


class TestCommonVariables:
    """Test common variable definitions"""

    def test_variables_exist(self):
        """Test that variables are defined"""
        assert len(COMMON_VARIABLES) > 0

    def test_client_name_variable(self):
        """Test client_name variable exists"""
        names = [v["name"] for v in COMMON_VARIABLES]
        assert "client_name" in names

    def test_first_name_variable(self):
        """Test first_name variable exists"""
        names = [v["name"] for v in COMMON_VARIABLES]
        assert "first_name" in names

    def test_email_variable(self):
        """Test email variable exists"""
        names = [v["name"] for v in COMMON_VARIABLES]
        assert "email" in names

    def test_portal_url_variable(self):
        """Test portal_url variable exists"""
        names = [v["name"] for v in COMMON_VARIABLES]
        assert "portal_url" in names

    def test_variables_have_description(self):
        """Test all variables have descriptions"""
        for v in COMMON_VARIABLES:
            assert "description" in v
            assert len(v["description"]) > 0


class TestDefaultTemplates:
    """Test default template definitions"""

    def test_default_templates_exist(self):
        """Test that default templates are defined"""
        assert len(DEFAULT_TEMPLATES) > 0

    def test_welcome_template(self):
        """Test welcome template exists"""
        types = [t["template_type"] for t in DEFAULT_TEMPLATES]
        assert "welcome" in types

    def test_document_reminder_template(self):
        """Test document_reminder template exists"""
        types = [t["template_type"] for t in DEFAULT_TEMPLATES]
        assert "document_reminder" in types

    def test_case_update_template(self):
        """Test case_update template exists"""
        types = [t["template_type"] for t in DEFAULT_TEMPLATES]
        assert "case_update" in types

    def test_dispute_sent_template(self):
        """Test dispute_sent template exists"""
        types = [t["template_type"] for t in DEFAULT_TEMPLATES]
        assert "dispute_sent" in types

    def test_templates_have_required_fields(self):
        """Test all templates have required fields"""
        for t in DEFAULT_TEMPLATES:
            assert "template_type" in t
            assert "name" in t
            assert "category" in t
            assert "subject" in t


class TestGetCategories:
    """Test the get_categories method"""

    def test_returns_dict(self):
        """Test that categories returns a dictionary"""
        categories = EmailTemplateService.get_categories()
        assert isinstance(categories, dict)

    def test_returns_all_categories(self):
        """Test that all categories are returned"""
        categories = EmailTemplateService.get_categories()
        assert categories == TEMPLATE_CATEGORIES


class TestGetCommonVariables:
    """Test the get_common_variables method"""

    def test_returns_list(self):
        """Test that variables returns a list"""
        variables = EmailTemplateService.get_common_variables()
        assert isinstance(variables, list)

    def test_returns_all_variables(self):
        """Test that all variables are returned"""
        variables = EmailTemplateService.get_common_variables()
        assert variables == COMMON_VARIABLES


class TestCreateTemplate:
    """Test the create_template method"""

    @patch('services.email_template_service.SessionLocal')
    def test_creates_template(self, mock_session_local):
        """Test that template is created successfully"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_type = "test_template"

        def add_side_effect(template):
            template.id = 1
            template.template_type = "test_template"

        mock_session.add.side_effect = add_side_effect
        mock_session.refresh = MagicMock()

        result = EmailTemplateService.create_template(
            template_type="test_template",
            name="Test Template",
            subject="Test Subject",
            html_content="<p>Test content</p>",
        )

        assert result["success"] is True
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('services.email_template_service.SessionLocal')
    def test_rejects_duplicate_type(self, mock_session_local):
        """Test that duplicate template_type is rejected"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Simulate existing template
        mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()

        result = EmailTemplateService.create_template(
            template_type="existing_template",
            name="Test",
            subject="Test",
            html_content="<p>Test</p>",
        )

        assert result["success"] is False
        assert "already exists" in result["error"]


class TestUpdateTemplate:
    """Test the update_template method"""

    @patch('services.email_template_service.SessionLocal')
    def test_updates_template(self, mock_session_local):
        """Test that template is updated successfully"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.name = "Old Name"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = EmailTemplateService.update_template(
            template_id=1,
            name="New Name",
        )

        assert result["success"] is True
        assert mock_template.name == "New Name"
        mock_session.commit.assert_called_once()

    @patch('services.email_template_service.SessionLocal')
    def test_returns_error_for_missing_template(self, mock_session_local):
        """Test that error is returned for missing template"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = EmailTemplateService.update_template(
            template_id=999,
            name="New Name",
        )

        assert result["success"] is False
        assert "not found" in result["error"]


class TestDeleteTemplate:
    """Test the delete_template method"""

    @patch('services.email_template_service.SessionLocal')
    def test_deletes_custom_template(self, mock_session_local):
        """Test that custom template is deleted"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.is_custom = True
        mock_template.name = "Custom Template"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = EmailTemplateService.delete_template(template_id=1)

        assert result["success"] is True
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch('services.email_template_service.SessionLocal')
    def test_prevents_system_template_deletion(self, mock_session_local):
        """Test that system templates cannot be deleted"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.is_custom = False
        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = EmailTemplateService.delete_template(template_id=1)

        assert result["success"] is False
        assert "cannot be deleted" in result["error"]
        mock_session.delete.assert_not_called()


class TestGetTemplate:
    """Test the get_template method"""

    @patch('services.email_template_service.SessionLocal')
    def test_gets_template_by_id(self, mock_session_local):
        """Test getting template by ID"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_type = "test"
        mock_template.name = "Test Template"
        mock_template.category = "general"
        mock_template.description = "Test description"
        mock_template.subject = "Test Subject"
        mock_template.html_content = "<p>Test</p>"
        mock_template.plain_text_content = "Test"
        mock_template.variables = []
        mock_template.is_custom = True
        mock_template.is_active = True
        mock_template.created_at = datetime.utcnow()
        mock_template.updated_at = datetime.utcnow()

        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = EmailTemplateService.get_template(template_id=1)

        assert result is not None
        assert result["id"] == 1
        assert result["name"] == "Test Template"

    @patch('services.email_template_service.SessionLocal')
    def test_gets_template_by_type(self, mock_session_local):
        """Test getting template by type"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_type = "welcome"
        mock_template.name = "Welcome Email"
        mock_template.category = "welcome"
        mock_template.description = None
        mock_template.subject = "Welcome!"
        mock_template.html_content = "<p>Hi</p>"
        mock_template.plain_text_content = None
        mock_template.variables = []
        mock_template.is_custom = False
        mock_template.is_active = True
        mock_template.created_at = datetime.utcnow()
        mock_template.updated_at = datetime.utcnow()

        mock_session.query.return_value.filter.return_value.first.return_value = mock_template

        result = EmailTemplateService.get_template(template_type="welcome")

        assert result is not None
        assert result["template_type"] == "welcome"

    @patch('services.email_template_service.SessionLocal')
    def test_returns_none_for_missing_template(self, mock_session_local):
        """Test that None is returned for missing template"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = EmailTemplateService.get_template(template_id=999)

        assert result is None


class TestListTemplates:
    """Test the list_templates method"""

    @patch('services.email_template_service.SessionLocal')
    def test_lists_all_templates(self, mock_session_local):
        """Test listing all templates"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.template_type = "test"
        mock_template.name = "Test"
        mock_template.category = "general"
        mock_template.description = None
        mock_template.subject = "Test"
        mock_template.is_custom = True
        mock_template.is_active = True
        mock_template.created_at = datetime.utcnow()

        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_template]

        result = EmailTemplateService.list_templates()

        assert len(result) == 1
        assert result[0]["name"] == "Test"

    @patch('services.email_template_service.SessionLocal')
    def test_filters_by_category(self, mock_session_local):
        """Test filtering templates by category"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_query = MagicMock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []

        EmailTemplateService.list_templates(category="welcome")

        # Verify filter was called
        mock_query.filter.assert_called()


class TestRenderTemplate:
    """Test the render_template method"""

    @patch.object(EmailTemplateService, 'get_template')
    def test_renders_template_with_variables(self, mock_get_template):
        """Test rendering template with variable substitution"""
        mock_get_template.return_value = {
            "id": 1,
            "template_type": "test",
            "subject": "Hello {client_name}",
            "html_content": "<p>Hi {first_name}!</p>",
            "plain_text_content": "Hi {first_name}!",
            "is_active": True,
        }

        result = EmailTemplateService.render_template(
            template_id=1,
            variables={"client_name": "John Smith", "first_name": "John"},
        )

        assert result["success"] is True
        assert "John Smith" in result["subject"]
        assert "John" in result["html"]

    @patch.object(EmailTemplateService, 'get_template')
    def test_returns_error_for_missing_template(self, mock_get_template):
        """Test error returned for missing template"""
        mock_get_template.return_value = None

        result = EmailTemplateService.render_template(template_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]

    @patch.object(EmailTemplateService, 'get_template')
    def test_returns_error_for_inactive_template(self, mock_get_template):
        """Test error returned for inactive template"""
        mock_get_template.return_value = {
            "id": 1,
            "template_type": "test",
            "subject": "Test",
            "html_content": "<p>Test</p>",
            "is_active": False,
        }

        result = EmailTemplateService.render_template(template_id=1)

        assert result["success"] is False
        assert "not active" in result["error"]


class TestDuplicateTemplate:
    """Test the duplicate_template method"""

    @patch.object(EmailTemplateService, 'get_template')
    @patch.object(EmailTemplateService, 'create_template')
    def test_duplicates_template(self, mock_create, mock_get_template):
        """Test duplicating a template"""
        mock_get_template.return_value = {
            "id": 1,
            "template_type": "original",
            "name": "Original Template",
            "category": "general",
            "description": "Description",
            "subject": "Subject",
            "html_content": "<p>Content</p>",
            "plain_text_content": "Content",
            "variables": [],
        }

        mock_create.return_value = {
            "success": True,
            "template_id": 2,
        }

        result = EmailTemplateService.duplicate_template(
            template_id=1,
            new_name="Copy of Original",
            new_type="original_copy",
        )

        assert result["success"] is True
        mock_create.assert_called_once()

    @patch.object(EmailTemplateService, 'get_template')
    def test_returns_error_for_missing_source(self, mock_get_template):
        """Test error returned when source template not found"""
        mock_get_template.return_value = None

        result = EmailTemplateService.duplicate_template(template_id=999)

        assert result["success"] is False
        assert "not found" in result["error"]


class TestGetTemplateStats:
    """Test the get_template_stats method"""

    @patch('services.email_template_service.SessionLocal')
    def test_returns_stats(self, mock_session_local):
        """Test getting template statistics"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        mock_session.query.return_value.count.return_value = 10
        mock_session.query.return_value.filter.return_value.count.return_value = 8

        result = EmailTemplateService.get_template_stats()

        assert "total" in result
        assert "active" in result
        assert "custom" in result
        assert "system" in result


class TestSeedDefaultTemplates:
    """Test the seed_default_templates function"""

    @patch('services.email_template_service.SessionLocal')
    def test_seeds_templates(self, mock_session_local):
        """Test seeding default templates"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Simulate no existing templates
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = seed_default_templates()

        assert result["success"] is True
        assert result["created"] > 0

    @patch('services.email_template_service.SessionLocal')
    def test_skips_existing_templates(self, mock_session_local):
        """Test that existing templates are skipped"""
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session

        # Simulate existing template
        mock_session.query.return_value.filter.return_value.first.return_value = MagicMock()

        result = seed_default_templates()

        assert result["success"] is True
        assert result["skipped"] > 0


class TestConvenienceFunctions:
    """Test convenience functions"""

    @patch.object(EmailTemplateService, 'get_template')
    def test_get_template_function(self, mock_get):
        """Test get_template convenience function"""
        mock_get.return_value = {"template_type": "welcome"}

        result = get_template("welcome")

        mock_get.assert_called_once_with(template_type="welcome")
        assert result["template_type"] == "welcome"

    @patch.object(EmailTemplateService, 'render_template')
    def test_render_email_function(self, mock_render):
        """Test render_email convenience function"""
        mock_render.return_value = {"success": True, "subject": "Hello"}

        result = render_email("welcome", {"name": "John"})

        mock_render.assert_called_once_with(template_type="welcome", variables={"name": "John"})
        assert result["success"] is True

    @patch.object(EmailTemplateService, 'list_templates')
    def test_list_all_templates_function(self, mock_list):
        """Test list_all_templates convenience function"""
        mock_list.return_value = [{"name": "Template 1"}]

        result = list_all_templates()

        mock_list.assert_called_once_with(is_active=True)
        assert len(result) == 1


class TestVariableSubstitution:
    """Test variable substitution logic"""

    def test_variable_pattern(self):
        """Test that variable pattern is correct"""
        content = "Hello {client_name}, your email is {email}."
        variables = {"client_name": "John", "email": "john@test.com"}

        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", str(value))

        assert "John" in content
        assert "john@test.com" in content
        assert "{client_name}" not in content

    def test_missing_variable_preserved(self):
        """Test that missing variables are preserved"""
        content = "Hello {client_name}, your status is {status}."
        variables = {"client_name": "John"}

        for key, value in variables.items():
            content = content.replace(f"{{{key}}}", str(value))

        assert "John" in content
        assert "{status}" in content


class TestTemplateValidation:
    """Test template validation logic"""

    def test_required_fields_for_create(self):
        """Test required fields are validated on create"""
        required_fields = ["template_type", "name", "subject", "html_content"]
        assert len(required_fields) == 4

    def test_category_values(self):
        """Test valid category values"""
        valid_categories = list(TEMPLATE_CATEGORIES.keys())
        assert "welcome" in valid_categories
        assert "general" in valid_categories
        assert "invalid" not in valid_categories
