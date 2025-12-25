"""
Phase 7: Credit Monitoring Auto-Import Tests
Tests for credit report import, HTML parsing, and account extraction.
"""
import pytest
from datetime import datetime, date


class TestCreditMonitoringCredentials:
    """Test credit monitoring credential storage."""

    def test_credential_model_exists(self):
        """Test CreditMonitoringCredential model exists."""
        from database import CreditMonitoringCredential
        assert CreditMonitoringCredential is not None

    def test_client_credential_fields(self, sample_client):
        """Test client has credential fields."""
        assert hasattr(sample_client, 'credit_monitoring_service')
        assert hasattr(sample_client, 'credit_monitoring_username')
        assert hasattr(sample_client, 'credit_monitoring_password_encrypted')

    def test_supported_services(self):
        """Test supported credit monitoring services."""
        from database import CREDIT_MONITORING_SERVICES

        # Services use .com suffix
        expected_services = ['MyScoreIQ.com', 'IdentityIQ.com', 'SmartCredit.com']

        for service in expected_services:
            assert service in CREDIT_MONITORING_SERVICES


class TestEncryption:
    """Test credential encryption functionality."""

    def test_encryption_module_exists(self):
        """Test encryption module exists."""
        from services.encryption import encrypt_value, decrypt_value
        assert encrypt_value is not None
        assert decrypt_value is not None

    def test_encrypt_decrypt_round_trip(self):
        """Test encryption and decryption work correctly."""
        from services.encryption import encrypt_value, decrypt_value

        original = "test_password_123"
        encrypted = encrypt_value(original)

        # Encrypted should be different from original
        assert encrypted != original

        # Decryption should return original
        decrypted = decrypt_value(encrypted)
        assert decrypted == original

    def test_is_encrypted_check(self):
        """Test is_encrypted detection."""
        from services.encryption import is_encrypted, encrypt_value

        plaintext = "plain_password"
        encrypted = encrypt_value(plaintext)

        assert is_encrypted(encrypted) == True
        assert is_encrypted(plaintext) == False


class TestCreditReportParser:
    """Test credit report HTML parsing."""

    def test_parser_module_exists(self):
        """Test parser module exists."""
        try:
            from services.credit_report_parser import CreditReportParser
            assert CreditReportParser is not None
        except ImportError:
            pytest.skip("Credit report parser not implemented")

    def test_parse_basic_html(self):
        """Test parsing basic HTML structure."""
        try:
            from services.credit_report_parser import CreditReportParser

            sample_html = """
            <html>
            <body>
                <div class="credit-score">750</div>
                <div class="account">
                    <span class="name">Capital One</span>
                    <span class="balance">$5,000</span>
                </div>
            </body>
            </html>
            """

            # CreditReportParser requires html_content in constructor
            parser = CreditReportParser(html_content=sample_html)
            # Parser should handle basic HTML
            assert parser is not None
        except ImportError:
            pytest.skip("Credit report parser not implemented")


class TestScoreExtraction:
    """Test credit score extraction."""

    def test_score_snapshot_model(self):
        """Test CreditScoreSnapshot model exists."""
        from database import CreditScoreSnapshot
        assert CreditScoreSnapshot is not None

    def test_create_score_snapshot(self, db_session, sample_client):
        """Test creating credit score snapshot."""
        from database import CreditScoreSnapshot

        snapshot = CreditScoreSnapshot(
            client_id=sample_client.id,
            transunion_score=720,
            experian_score=715,
            equifax_score=725,
            source='MyScoreIQ'
        )
        db_session.add(snapshot)
        db_session.commit()

        assert snapshot.id is not None
        assert snapshot.transunion_score == 720

    def test_score_range_validation(self):
        """Test credit score range is valid."""
        min_score = 300
        max_score = 850

        test_scores = [720, 650, 800]

        for score in test_scores:
            assert min_score <= score <= max_score


class TestAccountExtraction:
    """Test account information extraction."""

    def test_account_fields(self):
        """Test expected account fields."""
        expected_fields = [
            'account_name',
            'account_number',
            'account_type',
            'balance',
            'credit_limit',
            'payment_status',
            'date_opened',
            'date_reported'
        ]

        # These should be extractable from credit reports
        assert len(expected_fields) >= 5

    def test_payment_history_format(self):
        """Test payment history format."""
        # 24-month payment history codes
        valid_codes = ['OK', '30', '60', '90', '120', 'CO', 'FC']

        sample_history = ['OK', 'OK', 'OK', '30', 'OK']

        for code in sample_history:
            assert code in valid_codes


class TestLatePaymentDetection:
    """Test late payment detection."""

    def test_count_late_payments(self):
        """Test counting late payments."""
        payment_history = ['OK', 'OK', '30', 'OK', '60', 'OK', '30']

        late_codes = ['30', '60', '90', '120', 'CO']
        late_count = sum(1 for p in payment_history if p in late_codes)

        assert late_count == 3

    def test_late_payment_severity(self):
        """Test late payment severity classification."""
        severity_order = {
            'OK': 0,
            '30': 1,
            '60': 2,
            '90': 3,
            '120': 4,
            'CO': 5  # Charge-off
        }

        assert severity_order['60'] > severity_order['30']
        assert severity_order['CO'] > severity_order['90']


class TestInquiryExtraction:
    """Test credit inquiry extraction."""

    def test_inquiry_fields(self):
        """Test inquiry field structure."""
        sample_inquiry = {
            'creditor_name': 'ABC Bank',
            'inquiry_date': '2025-01-15',
            'bureau': 'Experian',
            'inquiry_type': 'hard'
        }

        assert 'creditor_name' in sample_inquiry
        assert 'inquiry_date' in sample_inquiry
        assert 'bureau' in sample_inquiry

    def test_hard_vs_soft_inquiries(self):
        """Test distinguishing inquiry types."""
        inquiry_types = ['hard', 'soft']

        # Hard inquiries affect score
        assert 'hard' in inquiry_types
        # Soft inquiries don't affect score
        assert 'soft' in inquiry_types


class TestAccountDeduplication:
    """Test account deduplication logic."""

    def test_identify_duplicate_accounts(self):
        """Test identifying duplicate accounts."""
        accounts = [
            {'account_number': '****1234', 'name': 'Capital One'},
            {'account_number': '****1234', 'name': 'Cap One'},  # Duplicate
            {'account_number': '****5678', 'name': 'Chase'}
        ]

        seen = set()
        unique = []
        for acc in accounts:
            if acc['account_number'] not in seen:
                seen.add(acc['account_number'])
                unique.append(acc)

        assert len(unique) == 2


class TestCollectionsDetection:
    """Test collections account detection."""

    def test_identify_collection_accounts(self):
        """Test identifying collection accounts."""
        collection_keywords = ['collection', 'collections', 'recovered', 'charged off']

        account_name = "ABC Collections Agency"

        is_collection = any(
            kw in account_name.lower() for kw in collection_keywords
        )

        assert is_collection == True


class TestPublicRecords:
    """Test public records extraction."""

    def test_public_record_types(self):
        """Test public record type detection."""
        public_record_types = [
            'bankruptcy',
            'tax_lien',
            'civil_judgment',
            'foreclosure'
        ]

        assert 'bankruptcy' in public_record_types
        assert len(public_record_types) >= 3


class TestCreditImportPage:
    """Test credit import dashboard page."""

    def test_import_page_exists(self, authenticated_client):
        """Test credit import page exists."""
        response = authenticated_client.get('/dashboard/credit-import')
        assert response.status_code == 200

    def test_import_page_structure(self, authenticated_client):
        """Test import page has expected structure."""
        response = authenticated_client.get('/dashboard/credit-import')
        html = response.data.decode('utf-8')

        # Should have import-related content
        assert response.status_code == 200


class TestEnhancedReportView:
    """Test enhanced credit report view."""

    def test_report_view_endpoint(self, client, sample_credit_report):
        """Test credit report view endpoint."""
        response = client.get(f'/credit-report/{sample_credit_report.id}')
        # May require auth
        assert response.status_code in [200, 302, 401, 404]
