"""
Shared pytest fixtures for all phase tests.
"""
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app
from database import (
    get_db, Base, engine, Client, Staff, Analysis, CreditReport,
    DisputeLetter, Violation, Standing, Damages, CaseScore,
    ClientTag, ClientTagAssignment, UserQuickLink,
    Case, Settlement, Notification
)
from datetime import datetime, date


@pytest.fixture
def app():
    """Create Flask application for testing."""
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def db_session():
    """Create a database session for testing."""
    db = get_db()
    yield db
    db.rollback()
    db.close()


@pytest.fixture
def sample_staff(db_session):
    """Create a sample staff member for testing."""
    staff = db_session.query(Staff).filter_by(email='test_staff@test.com').first()
    if not staff:
        from werkzeug.security import generate_password_hash
        staff = Staff(
            email='test_staff@test.com',
            password_hash=generate_password_hash('testpass123'),
            first_name='Test',
            last_name='Staff',
            role='admin',
            is_active=True
        )
        db_session.add(staff)
        db_session.commit()
    return staff


@pytest.fixture
def sample_client(db_session):
    """Create a sample client for testing."""
    client = db_session.query(Client).filter_by(email='test_client@test.com').first()
    if not client:
        client = Client(
            name='Test Client',
            first_name='Test',
            last_name='Client',
            email='test_client@test.com',
            phone='555-123-4567',
            address_street='123 Test St',
            address_city='Test City',
            address_state='CA',
            address_zip='90210',
            current_dispute_round=1,
            dispute_status='active',
            client_type='C',
            status='active'
        )
        db_session.add(client)
        db_session.commit()
    return client


@pytest.fixture
def sample_credit_report(db_session, sample_client):
    """Create a sample credit report for testing."""
    report = CreditReport(
        client_id=sample_client.id,
        client_name=sample_client.name,
        credit_provider='TestProvider',
        report_html='<html><body>Test Credit Report</body></html>',
        report_date=datetime.now()
    )
    db_session.add(report)
    db_session.commit()
    return report


@pytest.fixture
def sample_analysis(db_session, sample_client, sample_credit_report):
    """Create a sample analysis for testing."""
    analysis = Analysis(
        credit_report_id=sample_credit_report.id,
        client_id=sample_client.id,
        client_name=sample_client.name,
        dispute_round=1,
        analysis_mode='auto',
        stage=1,
        stage_1_analysis='Test analysis content',
        full_analysis='Full test analysis'
    )
    db_session.add(analysis)
    db_session.commit()
    return analysis


@pytest.fixture
def sample_tag(db_session):
    """Create a sample tag for testing."""
    tag = db_session.query(ClientTag).filter_by(name='TestTag').first()
    if not tag:
        tag = ClientTag(
            name='TestTag',
            color='#ff5733'
        )
        db_session.add(tag)
        db_session.commit()
    return tag


@pytest.fixture
def authenticated_client(client, sample_staff, db_session):
    """Create an authenticated test client with staff session."""
    with client.session_transaction() as sess:
        sess['staff_id'] = sample_staff.id
        sess['staff_email'] = sample_staff.email
        sess['staff_role'] = sample_staff.role
    return client


@pytest.fixture
def sample_violation(db_session, sample_analysis, sample_client):
    """Create a sample violation for testing."""
    violation = Violation(
        analysis_id=sample_analysis.id,
        client_id=sample_client.id,
        bureau='Equifax',
        account_name='Test Account',
        fcra_section='§611',
        violation_type='Inaccurate Information',
        description='Test violation description',
        statutory_damages_min=100,
        statutory_damages_max=1000,
        is_willful=False
    )
    db_session.add(violation)
    db_session.commit()
    return violation


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
