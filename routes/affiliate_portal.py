"""
Affiliate Portal Routes

Provides authentication and portal views for affiliates to:
- Log in and manage their account
- View their referral stats and commissions
- Track the status of their referred clients
- See payout history
"""

import os
from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from database import SessionLocal, Affiliate, Commission, AffiliatePayout, Client

affiliate_portal = Blueprint('affiliate_portal', __name__, url_prefix='/affiliate')

# Check if running in CI mode for test authentication bypass
IS_CI = os.environ.get('CI', 'false').lower() == 'true'


def affiliate_login_required(f):
    """Decorator to require affiliate authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # CI mode bypass for testing
        if IS_CI:
            if 'affiliate_id' not in session:
                db = SessionLocal()
                try:
                    # Get or create test affiliate
                    affiliate = db.query(Affiliate).filter(
                        Affiliate.email == 'testaffiliate@example.com'
                    ).first()
                    if not affiliate:
                        affiliate = Affiliate(
                            name='Test Affiliate',
                            email='testaffiliate@example.com',
                            affiliate_code='TEST12345',
                            status='active',
                            password_hash=generate_password_hash('test123'),
                            commission_rate_1=0.10,
                            commission_rate_2=0.05
                        )
                        db.add(affiliate)
                        db.commit()
                        db.refresh(affiliate)
                    session['affiliate_id'] = affiliate.id
                    session['affiliate_name'] = affiliate.name
                    session['affiliate_code'] = affiliate.affiliate_code
                finally:
                    db.close()
            return f(*args, **kwargs)

        # Normal authentication check
        if 'affiliate_id' not in session:
            return redirect(url_for('affiliate_portal.login'))
        return f(*args, **kwargs)
    return decorated_function


@affiliate_portal.route('/login', methods=['GET', 'POST'])
def login():
    """Affiliate login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter email and password', 'error')
            return render_template('affiliate_portal/login.html')

        db = SessionLocal()
        try:
            affiliate = db.query(Affiliate).filter(Affiliate.email == email).first()

            if not affiliate:
                flash('Invalid email or password', 'error')
                return render_template('affiliate_portal/login.html')

            if not affiliate.password_hash:
                flash('Account not activated. Please contact support.', 'error')
                return render_template('affiliate_portal/login.html')

            if not check_password_hash(affiliate.password_hash, password):
                flash('Invalid email or password', 'error')
                return render_template('affiliate_portal/login.html')

            if affiliate.status != 'active':
                flash('Your account is not active. Please contact support.', 'error')
                return render_template('affiliate_portal/login.html')

            # Update login stats
            affiliate.last_login = datetime.utcnow()
            affiliate.login_count = (affiliate.login_count or 0) + 1
            db.commit()

            # Set session
            session['affiliate_id'] = affiliate.id
            session['affiliate_name'] = affiliate.name
            session['affiliate_code'] = affiliate.affiliate_code
            session['affiliate_email'] = affiliate.email

            return redirect(url_for('affiliate_portal.dashboard'))

        finally:
            db.close()

    return render_template('affiliate_portal/login.html')


@affiliate_portal.route('/logout')
def logout():
    """Log out affiliate"""
    session.pop('affiliate_id', None)
    session.pop('affiliate_name', None)
    session.pop('affiliate_code', None)
    session.pop('affiliate_email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('affiliate_portal.login'))


@affiliate_portal.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        # In a real app, send password reset email
        flash('If an account exists with this email, you will receive a password reset link.', 'success')
        return redirect(url_for('affiliate_portal.login'))

    return render_template('affiliate_portal/forgot_password.html')


@affiliate_portal.route('/')
@affiliate_portal.route('/dashboard')
@affiliate_login_required
def dashboard():
    """Affiliate dashboard - overview of stats and recent activity"""
    db = SessionLocal()
    try:
        affiliate_id = session.get('affiliate_id')
        affiliate = db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()

        if not affiliate:
            session.clear()
            return redirect(url_for('affiliate_portal.login'))

        # Get recent commissions
        recent_commissions = db.query(Commission).filter(
            Commission.affiliate_id == affiliate_id
        ).order_by(Commission.created_at.desc()).limit(5).all()

        # Get recent payouts
        recent_payouts = db.query(AffiliatePayout).filter(
            AffiliatePayout.affiliate_id == affiliate_id
        ).order_by(AffiliatePayout.created_at.desc()).limit(5).all()

        # Get referred clients count
        referred_clients = db.query(Client).filter(
            Client.referred_by_affiliate_id == affiliate_id
        ).count()

        # Get sub-affiliates
        sub_affiliates = db.query(Affiliate).filter(
            Affiliate.parent_affiliate_id == affiliate_id
        ).all()

        return render_template('affiliate_portal/dashboard.html',
            affiliate=affiliate,
            recent_commissions=recent_commissions,
            recent_payouts=recent_payouts,
            referred_clients=referred_clients,
            sub_affiliates=sub_affiliates
        )
    finally:
        db.close()


@affiliate_portal.route('/clients')
@affiliate_login_required
def clients():
    """View referred clients and their status"""
    db = SessionLocal()
    try:
        affiliate_id = session.get('affiliate_id')

        # Get all referred clients
        referred_clients = db.query(Client).filter(
            Client.referred_by_affiliate_id == affiliate_id
        ).order_by(Client.created_at.desc()).all()

        # Get commissions grouped by client
        client_commissions = {}
        commissions = db.query(Commission).filter(
            Commission.affiliate_id == affiliate_id
        ).all()
        for c in commissions:
            if c.client_id not in client_commissions:
                client_commissions[c.client_id] = []
            client_commissions[c.client_id].append(c)

        return render_template('affiliate_portal/clients.html',
            clients=referred_clients,
            client_commissions=client_commissions
        )
    finally:
        db.close()


@affiliate_portal.route('/commissions')
@affiliate_login_required
def commissions():
    """View commission history"""
    db = SessionLocal()
    try:
        affiliate_id = session.get('affiliate_id')

        # Get all commissions
        all_commissions = db.query(Commission).filter(
            Commission.affiliate_id == affiliate_id
        ).order_by(Commission.created_at.desc()).all()

        # Calculate totals
        total_earned = sum(c.commission_amount or 0 for c in all_commissions)
        pending = sum(c.commission_amount or 0 for c in all_commissions if c.status == 'pending')
        paid = sum(c.commission_amount or 0 for c in all_commissions if c.status == 'paid')

        return render_template('affiliate_portal/commissions.html',
            commissions=all_commissions,
            total_earned=total_earned,
            pending=pending,
            paid=paid
        )
    finally:
        db.close()


@affiliate_portal.route('/payouts')
@affiliate_login_required
def payouts():
    """View payout history"""
    db = SessionLocal()
    try:
        affiliate_id = session.get('affiliate_id')
        affiliate = db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()

        # Get all payouts
        all_payouts = db.query(AffiliatePayout).filter(
            AffiliatePayout.affiliate_id == affiliate_id
        ).order_by(AffiliatePayout.created_at.desc()).all()

        return render_template('affiliate_portal/payouts.html',
            affiliate=affiliate,
            payouts=all_payouts
        )
    finally:
        db.close()


@affiliate_portal.route('/referral-link')
@affiliate_login_required
def referral_link():
    """Get referral link and marketing materials"""
    db = SessionLocal()
    try:
        affiliate_id = session.get('affiliate_id')
        affiliate = db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()

        # Build referral URL
        base_url = request.host_url.rstrip('/')
        referral_url = f"{base_url}/get-started?ref={affiliate.affiliate_code}"

        return render_template('affiliate_portal/referral_link.html',
            affiliate=affiliate,
            referral_url=referral_url
        )
    finally:
        db.close()


@affiliate_portal.route('/settings', methods=['GET', 'POST'])
@affiliate_login_required
def settings():
    """Affiliate settings - update profile and payout info"""
    db = SessionLocal()
    try:
        affiliate_id = session.get('affiliate_id')
        affiliate = db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'update_profile':
                affiliate.name = request.form.get('name', affiliate.name)
                affiliate.phone = request.form.get('phone', affiliate.phone)
                affiliate.company_name = request.form.get('company_name', affiliate.company_name)
                db.commit()
                flash('Profile updated successfully!', 'success')

            elif action == 'update_payout':
                affiliate.payout_method = request.form.get('payout_method')
                affiliate.payout_details = {
                    'account': request.form.get('payout_account', ''),
                    'notes': request.form.get('payout_notes', '')
                }
                db.commit()
                flash('Payout information updated!', 'success')

            elif action == 'change_password':
                current = request.form.get('current_password')
                new_pass = request.form.get('new_password')
                confirm = request.form.get('confirm_password')

                if not affiliate.password_hash or check_password_hash(affiliate.password_hash, current):
                    if new_pass == confirm and len(new_pass) >= 6:
                        affiliate.password_hash = generate_password_hash(new_pass)
                        db.commit()
                        flash('Password changed successfully!', 'success')
                    else:
                        flash('Passwords do not match or too short (min 6 chars)', 'error')
                else:
                    flash('Current password is incorrect', 'error')

            return redirect(url_for('affiliate_portal.settings'))

        return render_template('affiliate_portal/settings.html', affiliate=affiliate)
    finally:
        db.close()


# API endpoints for AJAX calls

@affiliate_portal.route('/api/stats')
@affiliate_login_required
def api_stats():
    """Get affiliate stats for dashboard widgets"""
    db = SessionLocal()
    try:
        affiliate_id = session.get('affiliate_id')
        affiliate = db.query(Affiliate).filter(Affiliate.id == affiliate_id).first()

        # Count clients by status
        clients = db.query(Client).filter(Client.referred_by_affiliate_id == affiliate_id).all()
        status_counts = {}
        for c in clients:
            status = c.dispute_status or 'unknown'
            status_counts[status] = status_counts.get(status, 0) + 1

        return jsonify({
            'success': True,
            'stats': {
                'total_referrals': affiliate.total_referrals or 0,
                'total_earnings': affiliate.total_earnings or 0,
                'pending_earnings': affiliate.pending_earnings or 0,
                'paid_out': affiliate.paid_out or 0,
                'client_statuses': status_counts
            }
        })
    finally:
        db.close()


@affiliate_portal.route('/api/clients')
@affiliate_login_required
def api_clients():
    """Get referred clients with their status"""
    db = SessionLocal()
    try:
        affiliate_id = session.get('affiliate_id')

        clients = db.query(Client).filter(
            Client.referred_by_affiliate_id == affiliate_id
        ).order_by(Client.created_at.desc()).all()

        return jsonify({
            'success': True,
            'clients': [{
                'id': c.id,
                'name': f"{c.first_name or ''} {c.last_name or ''}".strip() or 'Unknown',
                'email': c.email,
                'status': c.status,
                'dispute_status': c.dispute_status,
                'created_at': c.created_at.isoformat() if c.created_at else None,
                'round_number': c.round_number or 0
            } for c in clients]
        })
    finally:
        db.close()


@affiliate_portal.route('/api/commissions')
@affiliate_login_required
def api_commissions():
    """Get commission history"""
    db = SessionLocal()
    try:
        affiliate_id = session.get('affiliate_id')

        commissions = db.query(Commission).filter(
            Commission.affiliate_id == affiliate_id
        ).order_by(Commission.created_at.desc()).limit(50).all()

        return jsonify({
            'success': True,
            'commissions': [{
                'id': c.id,
                'client_id': c.client_id,
                'level': c.level,
                'trigger_type': c.trigger_type,
                'trigger_amount': c.trigger_amount,
                'commission_rate': c.commission_rate,
                'commission_amount': c.commission_amount,
                'status': c.status,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in commissions]
        })
    finally:
        db.close()
