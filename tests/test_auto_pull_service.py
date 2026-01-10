"""
Tests for AutoPullService
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from services.auto_pull_service import (
    AutoPullService,
    SUPPORTED_SERVICES,
    FREQUENCIES,
    PULL_STATUSES,
    STATUS_SUCCESS,
    STATUS_FAILED,
    STATUS_PENDING,
)


class TestAutoPullServiceConstants:
    """Test service constants and configuration"""

    def test_supported_services_defined(self):
        """Test that supported services are defined"""
        assert SUPPORTED_SERVICES is not None
        assert isinstance(SUPPORTED_SERVICES, dict)
        assert len(SUPPORTED_SERVICES) >= 5

    def test_supported_services_have_required_keys(self):
        """Test that each service has required configuration"""
        for key, service in SUPPORTED_SERVICES.items():
            assert 'name' in service
            assert 'report_type' in service
            assert 'bureaus' in service
            assert isinstance(service['bureaus'], list)

    def test_identityiq_service(self):
        """Test IdentityIQ service configuration"""
        assert 'identityiq' in SUPPORTED_SERVICES
        service = SUPPORTED_SERVICES['identityiq']
        assert service['name'] == 'IdentityIQ'
        assert service['report_type'] == '3bureau'
        assert len(service['bureaus']) == 3

    def test_frequencies_defined(self):
        """Test that pull frequencies are defined"""
        assert FREQUENCIES is not None
        assert isinstance(FREQUENCIES, dict)
        assert 'manual' in FREQUENCIES
        assert 'daily' in FREQUENCIES
        assert 'weekly' in FREQUENCIES
        assert 'monthly' in FREQUENCIES

    def test_pull_statuses_defined(self):
        """Test that pull statuses are defined"""
        assert PULL_STATUSES is not None
        assert 'pending' in PULL_STATUSES
        assert 'success' in PULL_STATUSES
        assert 'failed' in PULL_STATUSES


class TestAutoPullServiceStaticMethods:
    """Test static/class methods"""

    def test_get_supported_services(self):
        """Test getting supported services"""
        services = AutoPullService.get_supported_services()
        assert services is not None
        assert isinstance(services, list)
        # Each item should have key, name, etc.
        assert len(services) >= 5
        # Check first item has expected keys
        first = services[0]
        assert 'key' in first
        assert 'name' in first
        assert 'bureaus' in first

    def test_get_frequencies(self):
        """Test getting frequencies"""
        frequencies = AutoPullService.get_frequencies()
        assert frequencies is not None
        assert isinstance(frequencies, list)
        # Each item should have value and label
        assert len(frequencies) >= 4
        first = frequencies[0]
        assert 'value' in first
        assert 'label' in first

    def test_get_frequencies_includes_manual(self):
        """Test that manual frequency is included"""
        frequencies = AutoPullService.get_frequencies()
        values = [f['value'] for f in frequencies]
        assert 'manual' in values

    def test_get_frequencies_includes_weekly(self):
        """Test that weekly frequency is included"""
        frequencies = AutoPullService.get_frequencies()
        values = [f['value'] for f in frequencies]
        assert 'weekly' in values


class TestAutoPullServiceCredentials:
    """Test credential management"""

    @patch('services.auto_pull_service.get_db')
    def test_get_credentials_empty(self, mock_get_db):
        """Test getting credentials when none exist"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        credentials = service.get_credentials()

        assert credentials == []

    @patch('services.auto_pull_service.get_db')
    def test_get_credentials_with_client_filter(self, mock_get_db):
        """Test getting credentials for specific client"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        credentials = service.get_credentials(client_id=123)

        assert credentials == []

    def test_add_credential_returns_expected_structure(self):
        """Test that add_credential returns expected structure"""
        service = AutoPullService()
        # Call with invalid service to test error path
        result = service.add_credential(
            client_id=1,
            service_name='fake_service',
            username='testuser',
            password='testpass',
            import_frequency='weekly'
        )

        # Should return dict with success key
        assert 'success' in result
        assert result['success'] is False
        assert 'error' in result

    @patch('services.auto_pull_service.get_db')
    def test_add_credential_duplicate(self, mock_get_db):
        """Test adding duplicate credential fails"""
        mock_db = MagicMock()
        # Return existing credential
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.first.return_value = MagicMock()
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        result = service.add_credential(
            client_id=1,
            service_name='identityiq',
            username='testuser',
            password='testpass'
        )

        assert result['success'] is False
        assert 'already exists' in result['error']

    @patch('services.auto_pull_service.get_db')
    def test_add_credential_invalid_service(self, mock_get_db):
        """Test adding credential with invalid service"""
        mock_db = MagicMock()
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        result = service.add_credential(
            client_id=1,
            service_name='invalid_service',
            username='testuser',
            password='testpass'
        )

        assert result['success'] is False
        assert 'Unsupported' in result['error']

    @patch('services.auto_pull_service.get_db')
    def test_delete_credential_success(self, mock_get_db):
        """Test deleting a credential (soft delete)"""
        mock_db = MagicMock()
        mock_cred = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cred
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        result = service.delete_credential(credential_id=1)

        assert result['success'] is True
        # Soft delete sets is_active to False
        assert mock_cred.is_active is False
        mock_db.commit.assert_called_once()

    @patch('services.auto_pull_service.get_db')
    def test_delete_credential_not_found(self, mock_get_db):
        """Test deleting non-existent credential"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        result = service.delete_credential(credential_id=999)

        assert result['success'] is False
        assert 'not found' in result['error']


class TestAutoPullServicePulls:
    """Test pull operations"""

    @patch('services.auto_pull_service.get_db')
    def test_get_due_pulls_empty(self, mock_get_db):
        """Test getting due pulls when none are due"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        due_pulls = service.get_due_pulls()

        assert due_pulls == []

    def test_initiate_pull_returns_expected_structure(self):
        """Test initiating pull returns expected structure"""
        service = AutoPullService()
        # Call with credential_id that won't exist -
        # result depends on DB state but should always return a dict
        result = service.initiate_pull(credential_id=999999)

        # Should return a dict with success key
        assert isinstance(result, dict)
        assert 'success' in result

    @patch('services.auto_pull_service.get_db')
    def test_get_pull_logs_empty(self, mock_get_db):
        """Test getting pull logs when none exist"""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        logs = service.get_pull_logs()

        assert logs == []

    @patch('services.auto_pull_service.get_db')
    def test_get_pull_logs_with_limit(self, mock_get_db):
        """Test getting pull logs with limit"""
        mock_db = MagicMock()
        mock_db.query.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        logs = service.get_pull_logs(limit=10)

        assert logs == []
        mock_db.query.return_value.order_by.return_value.limit.assert_called_with(10)


class TestAutoPullServiceStats:
    """Test statistics methods"""

    @patch('services.auto_pull_service.get_db')
    def test_get_pull_stats(self, mock_get_db):
        """Test getting pull statistics"""
        mock_db = MagicMock()
        # Mock various query results
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.filter.return_value.count.return_value = 0
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        stats = service.get_pull_stats()

        assert stats is not None
        assert 'total_credentials' in stats
        assert 'pulls_today' in stats

    @patch('services.auto_pull_service.decrypt_value')
    @patch('services.auto_pull_service.get_db')
    def test_validate_credentials_success(self, mock_get_db, mock_decrypt):
        """Test validating credentials that exist"""
        mock_db = MagicMock()
        mock_cred = MagicMock()
        mock_cred.username = 'testuser'
        mock_cred.password_encrypted = 'encrypted'
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cred
        mock_get_db.return_value = mock_db
        mock_decrypt.return_value = 'testpass'

        service = AutoPullService()
        result = service.validate_credentials(credential_id=1)

        assert result['success'] is True
        assert result['valid'] is True

    @patch('services.auto_pull_service.get_db')
    def test_validate_credentials_not_found(self, mock_get_db):
        """Test validating credentials that don't exist"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        result = service.validate_credentials(credential_id=999)

        assert result['success'] is False
        assert 'not found' in result['error']


class TestAutoPullServiceScheduling:
    """Test scheduling functionality"""

    @patch('services.auto_pull_service.get_db')
    def test_run_scheduled_pulls_none_due(self, mock_get_db):
        """Test running scheduled pulls when none are due"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        result = service.run_scheduled_pulls()

        assert result['total'] == 0
        assert result['success'] == 0
        assert result['failed'] == 0

    def test_frequencies_manual_is_none(self):
        """Test that manual frequency returns None"""
        assert FREQUENCIES['manual'] is None

    def test_frequencies_daily_is_one_day(self):
        """Test that daily frequency is 1 day"""
        assert FREQUENCIES['daily'] == timedelta(days=1)

    def test_frequencies_weekly_is_seven_days(self):
        """Test that weekly frequency is 7 days"""
        assert FREQUENCIES['weekly'] == timedelta(days=7)


class TestAutoPullServiceIntegration:
    """Integration-style tests"""

    def test_service_instantiation(self):
        """Test service can be instantiated"""
        service = AutoPullService()
        assert service is not None

    def test_supported_services_complete(self):
        """Test all expected services are configured"""
        expected_services = ['identityiq', 'myscoreiq', 'smartcredit']
        for svc in expected_services:
            assert svc in SUPPORTED_SERVICES
            assert SUPPORTED_SERVICES[svc]['name'] is not None

    def test_frequencies_have_timedeltas(self):
        """Test frequencies have proper timedelta values"""
        assert FREQUENCIES['manual'] is None
        assert FREQUENCIES['daily'] == timedelta(days=1)
        assert FREQUENCIES['weekly'] == timedelta(days=7)
        assert FREQUENCIES['monthly'] == timedelta(days=30)


class TestAutoPullServiceEdgeCases:
    """Test edge cases and error handling"""

    def test_add_credential_invalid_returns_error(self):
        """Test that invalid service returns proper error structure"""
        service = AutoPullService()
        result = service.add_credential(
            client_id=1,
            service_name='nonexistent_service',
            username='testuser',
            password='testpass'
        )

        assert result['success'] is False
        assert 'error' in result
        assert 'Unsupported' in result['error']

    @patch('services.auto_pull_service.get_db')
    def test_update_credential_not_found(self, mock_get_db):
        """Test updating non-existent credential"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        result = service.update_credential(
            credential_id=999,
            username='newuser'
        )

        assert result['success'] is False
        assert 'not found' in result['error']

    @patch('services.auto_pull_service.get_db')
    def test_update_credential_success(self, mock_get_db):
        """Test updating credential successfully"""
        mock_db = MagicMock()
        mock_cred = MagicMock()
        mock_cred.to_dict.return_value = {'id': 1, 'username': 'newuser'}
        mock_db.query.return_value.filter.return_value.first.return_value = mock_cred
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        result = service.update_credential(
            credential_id=1,
            username='newuser'
        )

        assert result['success'] is True
        assert mock_cred.username == 'newuser'
        mock_db.commit.assert_called_once()

    @patch('services.auto_pull_service.get_db')
    def test_get_credentials_with_service_filter(self, mock_get_db):
        """Test getting credentials filtered by service"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        credentials = service.get_credentials(service_name='identityiq')

        assert credentials == []

    @patch('services.auto_pull_service.get_db')
    def test_trigger_letter_send_pulls_no_credentials(self, mock_get_db):
        """Test triggering letter send pulls with no matching credentials"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []
        mock_get_db.return_value = mock_db

        service = AutoPullService()
        result = service.trigger_letter_send_pulls(client_id=1)

        assert result['total'] == 0
        assert result['success'] == 0
        assert result['failed'] == 0
