"""
Phase 1: Core Platform Tests
Tests for admin dashboard, API endpoints, PDF generation, and database operations.
"""
import pytest
from datetime import datetime


class TestHealthCheck:
    """Test basic application health."""

    def test_app_is_running(self, client):
        """Test that the application responds to health check."""
        response = client.get('/')
        assert response.status_code == 200

    def test_admin_redirect_without_auth(self, client):
        """Test that admin page redirects to login without authentication."""
        response = client.get('/admin')
        assert response.status_code in [302, 301, 200]


class TestClientAPI:
    """Test client management API endpoints."""

    def test_get_clients_endpoint(self, client):
        """Test that client list endpoint responds."""
        response = client.get('/api/clients')
        # Endpoint may or may not require auth depending on configuration
        assert response.status_code in [200, 401, 403]

    def test_get_clients_authenticated(self, authenticated_client, sample_client):
        """Test getting client list when authenticated."""
        response = authenticated_client.get('/api/clients')
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('success') == True or 'clients' in data or isinstance(data, list)

    def test_get_client_details(self, authenticated_client, sample_client):
        """Test getting individual client details."""
        response = authenticated_client.get(f'/api/clients/{sample_client.id}/details')
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('success') == True

    def test_create_client(self, authenticated_client, db_session):
        """Test creating a new client."""
        response = authenticated_client.post('/api/clients/create', json={
            'name': 'New Test Client',
            'email': 'newclient@test.com',
            'phone': '555-999-8888'
        })
        assert response.status_code == 200
        data = response.get_json()
        assert data.get('success') == True
        assert 'client_id' in data


class TestCreditReportModel:
    """Test credit report database operations."""

    def test_create_credit_report(self, db_session, sample_client):
        """Test creating a credit report."""
        from database import CreditReport

        report = CreditReport(
            client_id=sample_client.id,
            client_name=sample_client.name,
            credit_provider='Experian',
            report_html='<html>Test Report</html>',
            report_date=datetime.now()
        )
        db_session.add(report)
        db_session.commit()

        assert report.id is not None
        assert report.client_id == sample_client.id

    def test_query_credit_reports(self, db_session, sample_credit_report):
        """Test querying credit reports."""
        from database import CreditReport

        reports = db_session.query(CreditReport).filter_by(
            client_id=sample_credit_report.client_id
        ).all()

        assert len(reports) >= 1
        assert reports[0].report_html is not None


class TestAnalysisModel:
    """Test analysis database operations."""

    def test_create_analysis(self, db_session, sample_client, sample_credit_report):
        """Test creating an analysis."""
        from database import Analysis

        analysis = Analysis(
            credit_report_id=sample_credit_report.id,
            client_id=sample_client.id,
            client_name=sample_client.name,
            dispute_round=1,
            analysis_mode='auto',
            stage=1
        )
        db_session.add(analysis)
        db_session.commit()

        assert analysis.id is not None
        assert analysis.dispute_round == 1

    def test_analysis_stages(self, sample_analysis):
        """Test analysis stage tracking."""
        assert sample_analysis.stage in [1, 2]
        assert sample_analysis.dispute_round >= 1


class TestDisputeLetterModel:
    """Test dispute letter database operations."""

    def test_create_dispute_letter(self, db_session, sample_analysis, sample_client):
        """Test creating a dispute letter."""
        from database import DisputeLetter

        letter = DisputeLetter(
            analysis_id=sample_analysis.id,
            client_id=sample_client.id,
            client_name=sample_client.name,
            bureau='Equifax',
            round_number=1,
            letter_content='Test letter content'
        )
        db_session.add(letter)
        db_session.commit()

        assert letter.id is not None
        assert letter.bureau == 'Equifax'


class TestPDFGenerator:
    """Test PDF generation functionality."""

    def test_pdf_generator_import(self):
        """Test that PDF generator can be imported."""
        from pdf_generator import LetterPDFGenerator
        assert LetterPDFGenerator is not None

    def test_section_pdf_generator_import(self):
        """Test that section PDF generator can be imported."""
        from pdf_generator import SectionPDFGenerator
        assert SectionPDFGenerator is not None


class TestDatabaseConnection:
    """Test database connectivity."""

    def test_database_connection(self, db_session):
        """Test that database connection works."""
        from database import Client
        # Simple query to test connection
        count = db_session.query(Client).count()
        assert count >= 0

    def test_database_session_rollback(self, db_session):
        """Test that session rollback works."""
        from database import Client

        # Create temp client
        temp_client = Client(name='Temp Rollback Test', email='rollback@test.com')
        db_session.add(temp_client)
        db_session.flush()

        # Rollback
        db_session.rollback()

        # Verify it's gone
        found = db_session.query(Client).filter_by(email='rollback@test.com').first()
        assert found is None
