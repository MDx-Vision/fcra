"""
Tests for LetterTemplateService
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from services.letter_template_service import (
    LetterTemplateService,
    CATEGORIES,
    TARGET_TYPES,
    COMMON_VARIABLES,
    BUREAU_ADDRESSES,
)


class TestLetterTemplateServiceConstants:
    """Test service constants and configuration"""

    def test_categories_defined(self):
        """Test that categories are defined"""
        assert CATEGORIES is not None
        assert isinstance(CATEGORIES, dict)
        assert len(CATEGORIES) >= 5

    def test_categories_have_required_keys(self):
        """Test that each category has required configuration"""
        for key, category in CATEGORIES.items():
            assert 'name' in category
            assert 'description' in category

    def test_initial_dispute_category(self):
        """Test initial dispute category configuration"""
        assert 'initial_dispute' in CATEGORIES
        category = CATEGORIES['initial_dispute']
        assert category['name'] == 'Initial Dispute'

    def test_target_types_defined(self):
        """Test that target types are defined"""
        assert TARGET_TYPES is not None
        assert isinstance(TARGET_TYPES, dict)
        assert 'bureau' in TARGET_TYPES
        assert 'furnisher' in TARGET_TYPES
        assert 'collector' in TARGET_TYPES

    def test_common_variables_defined(self):
        """Test that common variables are defined"""
        assert COMMON_VARIABLES is not None
        assert isinstance(COMMON_VARIABLES, list)
        assert len(COMMON_VARIABLES) >= 10

    def test_common_variables_have_required_keys(self):
        """Test that each variable has required keys"""
        for var in COMMON_VARIABLES:
            assert 'name' in var
            assert 'description' in var
            assert 'example' in var

    def test_bureau_addresses_defined(self):
        """Test that bureau addresses are defined"""
        assert BUREAU_ADDRESSES is not None
        assert 'equifax' in BUREAU_ADDRESSES
        assert 'experian' in BUREAU_ADDRESSES
        assert 'transunion' in BUREAU_ADDRESSES

    def test_bureau_addresses_have_required_keys(self):
        """Test that each bureau has required info"""
        for key, bureau in BUREAU_ADDRESSES.items():
            assert 'name' in bureau
            assert 'address' in bureau


class TestLetterTemplateServiceStaticMethods:
    """Test static/class methods"""

    def test_get_categories(self):
        """Test getting categories"""
        categories = LetterTemplateService.get_categories()
        assert categories is not None
        assert isinstance(categories, dict)
        assert 'initial_dispute' in categories

    def test_get_target_types(self):
        """Test getting target types"""
        target_types = LetterTemplateService.get_target_types()
        assert target_types is not None
        assert isinstance(target_types, dict)
        assert 'bureau' in target_types

    def test_get_common_variables(self):
        """Test getting common variables"""
        variables = LetterTemplateService.get_common_variables()
        assert variables is not None
        assert isinstance(variables, list)
        assert len(variables) > 0

    def test_get_bureau_addresses(self):
        """Test getting bureau addresses"""
        addresses = LetterTemplateService.get_bureau_addresses()
        assert addresses is not None
        assert 'equifax' in addresses


class TestLetterTemplateServiceTemplates:
    """Test template CRUD operations"""

    @patch('services.letter_template_service.get_db')
    def test_create_template_success(self, mock_get_db):
        """Test creating a template successfully"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.create_template(
            name='Test Template',
            code='test_template',
            category='initial_dispute',
            content='Hello {client_name}',
        )

        assert result['success'] is True
        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    @patch('services.letter_template_service.get_db')
    def test_create_template_duplicate_code(self, mock_get_db):
        """Test creating template with duplicate code fails"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()  # Existing
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.create_template(
            name='Test Template',
            code='existing_code',
            category='initial_dispute',
            content='Hello {client_name}',
        )

        assert result['success'] is False
        assert 'already exists' in result['error']

    @patch('services.letter_template_service.get_db')
    def test_get_template_success(self, mock_get_db):
        """Test getting a template"""
        mock_template = MagicMock()
        mock_template.to_dict.return_value = {'id': 1, 'name': 'Test'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        template = service.get_template(1)

        assert template is not None
        assert template['id'] == 1

    @patch('services.letter_template_service.get_db')
    def test_get_template_not_found(self, mock_get_db):
        """Test getting non-existent template"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        template = service.get_template(999)

        assert template is None

    @patch('services.letter_template_service.get_db')
    def test_list_templates_empty(self, mock_get_db):
        """Test listing templates when none exist"""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        templates = service.list_templates()

        assert templates == []

    @patch('services.letter_template_service.get_db')
    def test_list_templates_with_filters(self, mock_get_db):
        """Test listing templates with filters"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.all.return_value = []
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        templates = service.list_templates(
            category='initial_dispute',
            dispute_round=1,
            target_type='bureau',
        )

        assert templates == []

    @patch('services.letter_template_service.get_db')
    def test_update_template_success(self, mock_get_db):
        """Test updating a template"""
        mock_template = MagicMock()
        mock_template.content = 'Old content'
        mock_template.version = 1
        mock_template.to_dict.return_value = {'id': 1, 'name': 'Updated'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.update_template(
            template_id=1,
            updates={'name': 'Updated Template'}
        )

        assert result['success'] is True

    @patch('services.letter_template_service.get_db')
    def test_update_template_not_found(self, mock_get_db):
        """Test updating non-existent template"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.update_template(
            template_id=999,
            updates={'name': 'Updated'}
        )

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.letter_template_service.get_db')
    def test_delete_template_custom(self, mock_get_db):
        """Test deleting a custom template (hard delete)"""
        mock_template = MagicMock()
        mock_template.is_system = False

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.delete_template(1)

        assert result['success'] is True
        mock_db.delete.assert_called_once()

    @patch('services.letter_template_service.get_db')
    def test_delete_template_system(self, mock_get_db):
        """Test deleting a system template (soft delete)"""
        mock_template = MagicMock()
        mock_template.is_system = True

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.delete_template(1)

        assert result['success'] is True
        assert mock_template.is_active is False

    @patch('services.letter_template_service.get_db')
    def test_duplicate_template_success(self, mock_get_db):
        """Test duplicating a template"""
        mock_original = MagicMock()
        mock_original.name = 'Original'
        mock_original.category = 'initial_dispute'
        mock_original.content = 'Content'
        mock_original.id = 1

        mock_db = MagicMock()
        # First call returns original, second returns None (no duplicate)
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_original, None]
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.duplicate_template(
            template_id=1,
            new_name='Copy of Original',
            new_code='copy_original'
        )

        assert result['success'] is True


class TestLetterTemplateServiceVariables:
    """Test variable handling"""

    def test_extract_variables_empty(self):
        """Test extracting variables from empty content"""
        service = LetterTemplateService()
        variables = service._extract_variables('')

        assert variables == []

    def test_extract_variables_none(self):
        """Test extracting variables from None"""
        service = LetterTemplateService()
        variables = service._extract_variables(None)

        assert variables == []

    def test_extract_variables_with_placeholders(self):
        """Test extracting variables from content with placeholders"""
        service = LetterTemplateService()
        content = 'Hello {client_name}, your address is {client_address}'
        variables = service._extract_variables(content)

        assert len(variables) == 2
        var_names = [v['name'] for v in variables]
        assert 'client_name' in var_names
        assert 'client_address' in var_names

    def test_extract_variables_duplicates_removed(self):
        """Test that duplicate variables are removed"""
        service = LetterTemplateService()
        content = '{client_name} and again {client_name}'
        variables = service._extract_variables(content)

        assert len(variables) == 1

    def test_extract_variables_custom_variable(self):
        """Test extracting custom (non-common) variables"""
        service = LetterTemplateService()
        content = 'Custom: {my_custom_var}'
        variables = service._extract_variables(content)

        assert len(variables) == 1
        assert variables[0]['name'] == 'my_custom_var'

    @patch('services.letter_template_service.get_db')
    def test_render_template_success(self, mock_get_db):
        """Test rendering a template with variables"""
        mock_template = MagicMock()
        mock_template.content = 'Hello {client_name}'
        mock_template.subject = 'Dear {client_name}'
        mock_template.footer = 'Regards'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_template
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.render_template(1, {'client_name': 'John'})

        assert result['success'] is True
        assert 'Hello John' in result['content']
        assert 'Dear John' in result['subject']

    @patch('services.letter_template_service.get_db')
    def test_render_template_not_found(self, mock_get_db):
        """Test rendering non-existent template"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.render_template(999, {})

        assert result['success'] is False
        assert 'not found' in result['error']


class TestLetterTemplateServiceVersions:
    """Test version management"""

    @patch('services.letter_template_service.get_db')
    def test_get_template_versions(self, mock_get_db):
        """Test getting version history"""
        mock_version = MagicMock()
        mock_version.to_dict.return_value = {'id': 1, 'version_number': 1}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_version]
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        versions = service.get_template_versions(1)

        assert len(versions) == 1
        assert versions[0]['version_number'] == 1

    @patch('services.letter_template_service.get_db')
    def test_get_version(self, mock_get_db):
        """Test getting specific version"""
        mock_version = MagicMock()
        mock_version.to_dict.return_value = {'id': 1, 'version_number': 1}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_version
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        version = service.get_version(1)

        assert version is not None
        assert version['version_number'] == 1

    @patch('services.letter_template_service.get_db')
    def test_restore_version_success(self, mock_get_db):
        """Test restoring a previous version"""
        mock_template = MagicMock()
        mock_template.id = 1
        mock_template.version = 2
        mock_template.to_dict.return_value = {'id': 1, 'version': 3}

        mock_version = MagicMock()
        mock_version.name = 'Old Name'
        mock_version.content = 'Old Content'
        mock_version.footer = 'Old Footer'
        mock_version.variables = []
        mock_version.version_number = 1

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.side_effect = [mock_template, mock_version]
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.restore_version(1, 1)

        assert result['success'] is True

    @patch('services.letter_template_service.get_db')
    def test_restore_version_template_not_found(self, mock_get_db):
        """Test restoring version for non-existent template"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.restore_version(999, 1)

        assert result['success'] is False
        assert 'not found' in result['error']


class TestLetterTemplateServiceGeneration:
    """Test letter generation"""

    @patch('services.letter_template_service.get_db')
    def test_generate_letter_template_not_found(self, mock_get_db):
        """Test generating letter with non-existent template"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.generate_letter(
            template_id=999,
            client_id=1,
            target_type='bureau',
            target_name='Equifax'
        )

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.letter_template_service.get_db')
    def test_get_generated_letter(self, mock_get_db):
        """Test getting a generated letter"""
        mock_letter = MagicMock()
        mock_letter.to_dict.return_value = {'id': 1, 'content': 'Test'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_letter
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        letter = service.get_generated_letter(1)

        assert letter is not None
        assert letter['id'] == 1

    @patch('services.letter_template_service.get_db')
    def test_list_generated_letters(self, mock_get_db):
        """Test listing generated letters"""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.offset.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        letters = service.list_generated_letters()

        assert letters == []

    @patch('services.letter_template_service.get_db')
    def test_update_letter_status(self, mock_get_db):
        """Test updating letter status"""
        mock_letter = MagicMock()
        mock_letter.to_dict.return_value = {'id': 1, 'status': 'sent'}

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_letter
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.update_letter_status(1, 'sent')

        assert result['success'] is True

    @patch('services.letter_template_service.get_db')
    def test_update_letter_status_not_found(self, mock_get_db):
        """Test updating status of non-existent letter"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.update_letter_status(999, 'sent')

        assert result['success'] is False
        assert 'not found' in result['error']


class TestLetterTemplateServiceDashboard:
    """Test dashboard statistics"""

    @patch('services.letter_template_service.get_db')
    def test_get_dashboard_summary(self, mock_get_db):
        """Test getting dashboard summary"""
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        summary = service.get_dashboard_summary()

        assert summary is not None
        assert 'total_templates' in summary
        assert 'active_templates' in summary


class TestLetterTemplateServiceSeeding:
    """Test default template seeding"""

    @patch('services.letter_template_service.get_db')
    def test_seed_default_templates(self, mock_get_db):
        """Test seeding default templates"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None  # No existing
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.seed_default_templates()

        assert result['success'] is True
        assert result['templates_created'] >= 0

    @patch('services.letter_template_service.get_db')
    def test_seed_default_templates_already_exist(self, mock_get_db):
        """Test seeding when templates already exist"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock()  # Existing
        mock_get_db.return_value = mock_db

        service = LetterTemplateService()
        result = service.seed_default_templates()

        assert result['success'] is True
        assert result['templates_created'] == 0


class TestLetterTemplateServiceIntegration:
    """Integration-style tests"""

    def test_service_instantiation(self):
        """Test service can be instantiated"""
        service = LetterTemplateService()
        assert service is not None

    def test_all_categories_have_names(self):
        """Test all categories have display names"""
        for key, cat in CATEGORIES.items():
            assert cat['name'] is not None
            assert len(cat['name']) > 0

    def test_common_variables_include_essentials(self):
        """Test common variables include essential placeholders"""
        var_names = [v['name'] for v in COMMON_VARIABLES]
        assert 'client_name' in var_names
        assert 'client_address' in var_names
        assert 'bureau_name' in var_names
        assert 'current_date' in var_names

    def test_bureau_addresses_complete(self):
        """Test all major bureaus have addresses"""
        bureaus = ['equifax', 'experian', 'transunion']
        for bureau in bureaus:
            assert bureau in BUREAU_ADDRESSES
            assert BUREAU_ADDRESSES[bureau]['address'] is not None
