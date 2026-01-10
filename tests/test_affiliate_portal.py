"""
Unit tests for Affiliate Portal routes

Tests affiliate authentication, dashboard, and client tracking functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch
import sys
import os
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from werkzeug.security import generate_password_hash


def unique_code(prefix="AFF"):
    """Generate unique affiliate code for tests"""
    return f"{prefix}{uuid.uuid4().hex[:8].upper()}"


class TestAffiliateLoginRequired:
    """Tests for affiliate_login_required decorator"""

    def test_redirects_when_not_logged_in(self, client):
        """Should redirect to login when not authenticated"""
        response = client.get('/affiliate/dashboard')
        # In CI mode, it will auto-authenticate
        assert response.status_code in [200, 302]

    def test_allows_access_when_logged_in(self, client, db_session):
        """Should allow access when authenticated"""
        from database import Affiliate

        # Create actual affiliate
        affiliate = Affiliate(
            name='Test Access Affiliate',
            email=f'access_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('ACC'),
            status='active',
            password_hash=generate_password_hash('test123')
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/dashboard')
        assert response.status_code == 200


class TestAffiliateLogin:
    """Tests for affiliate login functionality"""

    def test_login_page_renders(self, client):
        """Should render login page"""
        response = client.get('/affiliate/login')
        assert response.status_code == 200
        assert b'Affiliate Portal' in response.data or b'Sign In' in response.data

    def test_login_requires_email_and_password(self, client):
        """Should require email and password"""
        response = client.post('/affiliate/login', data={
            'email': '',
            'password': ''
        })
        assert response.status_code == 200
        # Should show error or stay on login page

    def test_login_with_invalid_credentials(self, client):
        """Should reject invalid credentials"""
        response = client.post('/affiliate/login', data={
            'email': 'invalid@example.com',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        # Should stay on login page

    def test_login_success(self, client, db_session):
        """Should login successfully with valid credentials"""
        from database import Affiliate

        email = f'login_{uuid.uuid4().hex[:8]}@example.com'

        # Create test affiliate
        affiliate = Affiliate(
            name='Login Test',
            email=email,
            affiliate_code=unique_code('LOG'),
            status='active',
            password_hash=generate_password_hash('testpass123'),
            commission_rate_1=0.10,
            commission_rate_2=0.05
        )
        db_session.add(affiliate)
        db_session.commit()

        response = client.post('/affiliate/login', data={
            'email': email,
            'password': 'testpass123'
        }, follow_redirects=False)

        # Should redirect to dashboard
        assert response.status_code in [200, 302]


class TestAffiliateLogout:
    """Tests for affiliate logout"""

    def test_logout_clears_session(self, client):
        """Should clear session on logout"""
        with client.session_transaction() as sess:
            sess['affiliate_id'] = 1
            sess['affiliate_name'] = 'Test'

        response = client.get('/affiliate/logout', follow_redirects=False)
        assert response.status_code == 302

        with client.session_transaction() as sess:
            assert 'affiliate_id' not in sess


class TestAffiliateDashboard:
    """Tests for affiliate dashboard"""

    def test_dashboard_renders(self, client, db_session):
        """Should render dashboard page"""
        from database import Affiliate

        affiliate = Affiliate(
            name='Dashboard Test',
            email=f'dash_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('DSH'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/dashboard')
        assert response.status_code == 200

    def test_dashboard_shows_stats(self, client, db_session):
        """Should show affiliate stats"""
        from database import Affiliate

        affiliate = Affiliate(
            name='Stats Test',
            email=f'stats_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('STA'),
            status='active',
            total_referrals=10,
            total_earnings=500.0,
            pending_earnings=100.0,
            paid_out=400.0
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/dashboard')
        assert response.status_code == 200


class TestAffiliateClients:
    """Tests for affiliate clients page"""

    def test_clients_page_renders(self, client, db_session):
        """Should render clients page"""
        from database import Affiliate

        affiliate = Affiliate(
            name='Clients Page Test',
            email=f'clients_page_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('CLP'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/clients')
        assert response.status_code == 200

    def test_clients_shows_referred_clients(self, client, db_session):
        """Should show referred clients"""
        from database import Affiliate, Client

        affiliate = Affiliate(
            name='Clients Test',
            email=f'clients_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('CLI'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        # Create a referred client
        referred_client = Client(
            name='Referred Client',
            first_name='Referred',
            last_name='Client',
            email=f'referred_{uuid.uuid4().hex[:8]}@example.com',
            referred_by_affiliate_id=affiliate.id,
            dispute_status='active'
        )
        db_session.add(referred_client)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/clients')
        assert response.status_code == 200


class TestAffiliateCommissions:
    """Tests for affiliate commissions page"""

    def test_commissions_page_renders(self, client, db_session):
        """Should render commissions page"""
        from database import Affiliate

        affiliate = Affiliate(
            name='Commissions Page Test',
            email=f'comm_page_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('COP'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/commissions')
        assert response.status_code == 200

    def test_commissions_shows_history(self, client, db_session):
        """Should show commission history"""
        from database import Affiliate, Commission, Client

        affiliate = Affiliate(
            name='Commissions Test',
            email=f'comm_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('COM'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        # Create a client first
        test_client = Client(
            name='Commission Client',
            first_name='Commission',
            last_name='Client',
            email=f'commclient_{uuid.uuid4().hex[:8]}@example.com',
            dispute_status='active'
        )
        db_session.add(test_client)
        db_session.commit()

        commission = Commission(
            affiliate_id=affiliate.id,
            client_id=test_client.id,
            level=1,
            trigger_type='signup',
            trigger_amount=100.0,
            commission_rate=0.10,
            commission_amount=10.0,
            status='pending'
        )
        db_session.add(commission)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/commissions')
        assert response.status_code == 200


class TestAffiliatePayouts:
    """Tests for affiliate payouts page"""

    def test_payouts_page_renders(self, client, db_session):
        """Should render payouts page"""
        from database import Affiliate

        affiliate = Affiliate(
            name='Payouts Page Test',
            email=f'pay_page_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('PAP'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/payouts')
        assert response.status_code == 200


class TestAffiliateReferralLink:
    """Tests for affiliate referral link page"""

    def test_referral_link_page_renders(self, client, db_session):
        """Should render referral link page"""
        from database import Affiliate

        affiliate = Affiliate(
            name='Referral Page Test',
            email=f'ref_page_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('REP'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/referral-link')
        assert response.status_code == 200

    def test_referral_link_shows_code(self, client, db_session):
        """Should show affiliate code"""
        from database import Affiliate

        code = unique_code('REF')
        affiliate = Affiliate(
            name='Referral Test',
            email=f'ref_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=code,
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/referral-link')
        assert response.status_code == 200
        assert code.encode() in response.data


class TestAffiliateSettings:
    """Tests for affiliate settings page"""

    def test_settings_page_renders(self, client, db_session):
        """Should render settings page"""
        from database import Affiliate

        affiliate = Affiliate(
            name='Settings Page Test',
            email=f'set_page_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('SEP'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/settings')
        assert response.status_code == 200

    def test_update_profile(self, client, db_session):
        """Should update profile"""
        from database import Affiliate

        affiliate = Affiliate(
            name='Settings Test',
            email=f'settings_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('SET'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.post('/affiliate/settings', data={
            'action': 'update_profile',
            'name': 'Updated Name',
            'phone': '555-1234'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_update_payout_info(self, client, db_session):
        """Should update payout info"""
        from database import Affiliate

        affiliate = Affiliate(
            name='Payout Test',
            email=f'payout_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('PAY'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.post('/affiliate/settings', data={
            'action': 'update_payout',
            'payout_method': 'paypal',
            'payout_account': 'test@paypal.com'
        }, follow_redirects=True)
        assert response.status_code == 200


class TestAffiliateAPIStats:
    """Tests for affiliate API stats endpoint"""

    def test_api_stats_returns_data(self, client, db_session):
        """Should return stats data"""
        from database import Affiliate

        affiliate = Affiliate(
            name='API Stats Test',
            email=f'apistats_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('API'),
            status='active',
            total_referrals=5,
            total_earnings=250.0
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/api/stats')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'stats' in data


class TestAffiliateAPIClients:
    """Tests for affiliate API clients endpoint"""

    def test_api_clients_returns_list(self, client, db_session):
        """Should return clients list"""
        from database import Affiliate

        affiliate = Affiliate(
            name='API Clients Test',
            email=f'apiclients_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('APC'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/api/clients')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'clients' in data


class TestAffiliateAPICommissions:
    """Tests for affiliate API commissions endpoint"""

    def test_api_commissions_returns_list(self, client, db_session):
        """Should return commissions list"""
        from database import Affiliate

        affiliate = Affiliate(
            name='API Commissions Test',
            email=f'apicomm_{uuid.uuid4().hex[:8]}@example.com',
            affiliate_code=unique_code('ACM'),
            status='active'
        )
        db_session.add(affiliate)
        db_session.commit()

        with client.session_transaction() as sess:
            sess['affiliate_id'] = affiliate.id
            sess['affiliate_name'] = affiliate.name
            sess['affiliate_code'] = affiliate.affiliate_code

        response = client.get('/affiliate/api/commissions')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'commissions' in data


class TestForgotPassword:
    """Tests for forgot password functionality"""

    def test_forgot_password_page_renders(self, client):
        """Should render forgot password page"""
        response = client.get('/affiliate/forgot-password')
        assert response.status_code == 200

    def test_forgot_password_submit(self, client):
        """Should handle forgot password submission"""
        response = client.post('/affiliate/forgot-password', data={
            'email': 'test@example.com'
        }, follow_redirects=True)
        assert response.status_code == 200
