"""
Partner Portal Routes
Routes for white-label partner login and self-service management.
"""

import os
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from database import SessionLocal, WhiteLabelTenant, TenantUser, TenantClient, Client, Staff

partner_bp = Blueprint('partner', __name__, url_prefix='/partner')


def get_db():
    """Get database session"""
    return SessionLocal()


def partner_login_required(f):
    """Decorator to require partner login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # CI mode bypass for testing
        if os.getenv('CI') == 'true':
            db = get_db()
            try:
                tenant = db.query(WhiteLabelTenant).first()
                if not tenant:
                    # Create test tenant
                    tenant = WhiteLabelTenant(
                        name='Test Partner',
                        slug='test-partner',
                        admin_email='partner@example.com',
                        admin_password_hash=generate_password_hash('testpass123'),
                        is_active=True
                    )
                    db.add(tenant)
                    db.commit()
                    db.refresh(tenant)
                session['partner_id'] = tenant.id
                session['partner_name'] = tenant.name
            finally:
                db.close()

        if 'partner_id' not in session:
            return redirect(url_for('partner.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_partner():
    """Get current logged-in partner tenant"""
    if 'partner_id' not in session:
        return None
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()
        return tenant
    finally:
        db.close()


# ============================================================================
# Authentication Routes
# ============================================================================

@partner_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Partner login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('partner_portal/login.html')

        db = get_db()
        try:
            tenant = db.query(WhiteLabelTenant).filter_by(admin_email=email, is_active=True).first()

            if tenant and tenant.admin_password_hash and check_password_hash(tenant.admin_password_hash, password):
                # Update last login
                tenant.last_login = datetime.utcnow()
                db.commit()

                # Set session
                session['partner_id'] = tenant.id
                session['partner_name'] = tenant.name
                session['partner_slug'] = tenant.slug

                return redirect(url_for('partner.dashboard'))
            else:
                flash('Invalid email or password', 'error')
        finally:
            db.close()

    return render_template('partner_portal/login.html')


@partner_bp.route('/logout')
def logout():
    """Partner logout"""
    session.pop('partner_id', None)
    session.pop('partner_name', None)
    session.pop('partner_slug', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('partner.login'))


@partner_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not email:
            flash('Please enter your email address', 'error')
            return render_template('partner_portal/forgot_password.html')

        db = get_db()
        try:
            tenant = db.query(WhiteLabelTenant).filter_by(admin_email=email).first()

            if tenant:
                # Generate reset token
                token = secrets.token_urlsafe(32)
                tenant.password_reset_token = token
                tenant.password_reset_expires = datetime.utcnow() + timedelta(hours=24)
                db.commit()

                # TODO: Send password reset email
                flash('If an account exists with that email, a password reset link has been sent', 'success')
            else:
                # Don't reveal if email exists
                flash('If an account exists with that email, a password reset link has been sent', 'success')
        finally:
            db.close()

        return redirect(url_for('partner.login'))

    return render_template('partner_portal/forgot_password.html')


@partner_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset form"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(password_reset_token=token).first()

        if not tenant or (tenant.password_reset_expires and tenant.password_reset_expires < datetime.utcnow()):
            flash('Invalid or expired reset link', 'error')
            return redirect(url_for('partner.forgot_password'))

        if request.method == 'POST':
            password = request.form.get('password', '')
            confirm = request.form.get('confirm_password', '')

            if len(password) < 8:
                flash('Password must be at least 8 characters', 'error')
                return render_template('partner_portal/reset_password.html', token=token)

            if password != confirm:
                flash('Passwords do not match', 'error')
                return render_template('partner_portal/reset_password.html', token=token)

            tenant.admin_password_hash = generate_password_hash(password)
            tenant.password_reset_token = None
            tenant.password_reset_expires = None
            db.commit()

            flash('Password has been reset. Please log in.', 'success')
            return redirect(url_for('partner.login'))

        return render_template('partner_portal/reset_password.html', token=token)
    finally:
        db.close()


# ============================================================================
# Dashboard Routes
# ============================================================================

@partner_bp.route('/dashboard')
@partner_login_required
def dashboard():
    """Partner dashboard"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        # Get stats
        total_clients = db.query(TenantClient).filter_by(tenant_id=tenant.id).count()

        # Get client details for active count
        client_ids = [tc.client_id for tc in db.query(TenantClient).filter_by(tenant_id=tenant.id).all()]
        active_clients = 0
        if client_ids:
            active_clients = db.query(Client).filter(
                Client.id.in_(client_ids),
                Client.status.in_(['active', 'in_progress'])
            ).count()

        total_users = db.query(TenantUser).filter_by(tenant_id=tenant.id).count()

        # Get recent clients
        recent_clients = []
        if client_ids:
            recent_clients = db.query(Client).filter(
                Client.id.in_(client_ids)
            ).order_by(Client.created_at.desc()).limit(5).all()

        return render_template(
            'partner_portal/dashboard.html',
            tenant=tenant,
            stats={
                'total_clients': total_clients,
                'active_clients': active_clients,
                'total_users': total_users,
                'pending_disputes': 0  # Placeholder
            },
            recent_clients=recent_clients
        )
    finally:
        db.close()


# ============================================================================
# Branding Routes
# ============================================================================

@partner_bp.route('/branding')
@partner_login_required
def branding():
    """Branding management page"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()
        return render_template('partner_portal/branding.html', tenant=tenant)
    finally:
        db.close()


@partner_bp.route('/api/branding', methods=['PUT'])
@partner_login_required
def update_branding():
    """Update branding settings"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        data = request.json or {}

        # Update allowed fields
        allowed_fields = [
            'company_name', 'company_address', 'company_phone', 'company_email',
            'support_email', 'primary_color', 'secondary_color', 'accent_color',
            'terms_url', 'privacy_url', 'custom_css', 'custom_js'
        ]

        for field in allowed_fields:
            if field in data:
                setattr(tenant, field, data[field])

        tenant.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({'success': True, 'message': 'Branding updated successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()


@partner_bp.route('/api/branding/logo', methods=['POST'])
@partner_login_required
def upload_logo():
    """Upload logo"""
    if 'logo' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    file = request.files['logo']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400

    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        # Save file
        filename = secure_filename(f"partner_{tenant.id}_logo.{ext}")
        upload_dir = os.path.join('static', 'partner_logos')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # Update tenant
        tenant.logo_url = f'/static/partner_logos/{filename}'
        tenant.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({'success': True, 'logo_url': tenant.logo_url})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()


@partner_bp.route('/api/branding/favicon', methods=['POST'])
@partner_login_required
def upload_favicon():
    """Upload favicon"""
    if 'favicon' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400

    file = request.files['favicon']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    allowed_extensions = {'ico', 'png'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return jsonify({'success': False, 'error': 'Invalid file type. Use .ico or .png'}), 400

    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        # Save file
        filename = secure_filename(f"partner_{tenant.id}_favicon.{ext}")
        upload_dir = os.path.join('static', 'partner_logos')
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        file.save(filepath)

        # Update tenant
        tenant.favicon_url = f'/static/partner_logos/{filename}'
        tenant.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({'success': True, 'favicon_url': tenant.favicon_url})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()


# ============================================================================
# Client Routes
# ============================================================================

@partner_bp.route('/clients')
@partner_login_required
def clients():
    """Client management page"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        # Get client IDs for this tenant
        tenant_client_ids = [tc.client_id for tc in db.query(TenantClient).filter_by(tenant_id=tenant.id).all()]

        # Get all clients
        clients_list = []
        if tenant_client_ids:
            clients_list = db.query(Client).filter(
                Client.id.in_(tenant_client_ids)
            ).order_by(Client.created_at.desc()).all()

        # Stats
        stats = {
            'total': len(clients_list),
            'active': sum(1 for c in clients_list if c.status in ['active', 'in_progress']),
            'pending': sum(1 for c in clients_list if c.status in ['pending', 'signup']),
            'completed': sum(1 for c in clients_list if c.status == 'complete')
        }

        return render_template(
            'partner_portal/clients.html',
            tenant=tenant,
            clients=clients_list,
            stats=stats
        )
    finally:
        db.close()


@partner_bp.route('/api/clients', methods=['GET'])
@partner_login_required
def get_clients():
    """Get clients list as JSON"""
    db = get_db()
    try:
        tenant_id = session['partner_id']

        # Get client IDs for this tenant
        tenant_client_ids = [tc.client_id for tc in db.query(TenantClient).filter_by(tenant_id=tenant_id).all()]

        if not tenant_client_ids:
            return jsonify({'clients': []})

        # Get all clients
        clients = db.query(Client).filter(
            Client.id.in_(tenant_client_ids)
        ).order_by(Client.created_at.desc()).all()

        return jsonify({
            'clients': [{
                'id': c.id,
                'name': c.name,
                'email': c.email,
                'phone': c.phone,
                'status': c.status,
                'dispute_status': c.dispute_status,
                'current_round': c.current_dispute_round,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in clients]
        })
    finally:
        db.close()


@partner_bp.route('/api/clients/export', methods=['GET'])
@partner_login_required
def export_clients():
    """Export clients as CSV"""
    import csv
    from io import StringIO
    from flask import Response

    db = get_db()
    try:
        tenant_id = session['partner_id']

        # Get client IDs for this tenant
        tenant_client_ids = [tc.client_id for tc in db.query(TenantClient).filter_by(tenant_id=tenant_id).all()]

        clients = []
        if tenant_client_ids:
            clients = db.query(Client).filter(
                Client.id.in_(tenant_client_ids)
            ).order_by(Client.created_at.desc()).all()

        # Create CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Status', 'Dispute Status', 'Current Round', 'Created At'])

        for c in clients:
            writer.writerow([
                c.id, c.name, c.email, c.phone,
                c.status, c.dispute_status, c.current_dispute_round,
                c.created_at.isoformat() if c.created_at else ''
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=clients_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    finally:
        db.close()


# ============================================================================
# Team Routes
# ============================================================================

@partner_bp.route('/team')
@partner_login_required
def team():
    """Team management page"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        # Get team members
        team_members = db.query(TenantUser).filter_by(tenant_id=tenant.id).all()

        return render_template(
            'partner_portal/team.html',
            tenant=tenant,
            team_members=team_members
        )
    finally:
        db.close()


@partner_bp.route('/api/team', methods=['GET'])
@partner_login_required
def get_team():
    """Get team members as JSON"""
    db = get_db()
    try:
        tenant_id = session['partner_id']
        team_members = db.query(TenantUser).filter_by(tenant_id=tenant_id).all()

        return jsonify({
            'team': [m.to_dict() for m in team_members]
        })
    finally:
        db.close()


@partner_bp.route('/api/team', methods=['POST'])
@partner_login_required
def invite_team_member():
    """Invite a new team member"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        # Check team limit
        current_count = db.query(TenantUser).filter_by(tenant_id=tenant.id).count()
        if current_count >= tenant.max_users:
            return jsonify({'success': False, 'error': f'Team limit reached ({tenant.max_users} members)'}), 400

        data = request.json or {}
        email = data.get('email', '').strip().lower()
        role = data.get('role', 'user')

        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400

        # Check if staff exists
        staff = db.query(Staff).filter_by(email=email).first()

        if not staff:
            # Create new staff account
            staff = Staff(
                email=email,
                password_hash=generate_password_hash(secrets.token_urlsafe(16)),  # Random password
                first_name=data.get('first_name', ''),
                last_name=data.get('last_name', ''),
                role='viewer',
                is_active=True,
                force_password_change=True,
                organization_id=tenant.id
            )
            db.add(staff)
            db.commit()
            db.refresh(staff)

        # Check if already in team
        existing = db.query(TenantUser).filter_by(tenant_id=tenant.id, staff_id=staff.id).first()
        if existing:
            return jsonify({'success': False, 'error': 'User is already a team member'}), 400

        # Add to team
        tenant_user = TenantUser(
            tenant_id=tenant.id,
            staff_id=staff.id,
            role=role,
            is_primary_admin=False
        )
        db.add(tenant_user)
        db.commit()

        # TODO: Send invitation email

        return jsonify({'success': True, 'message': 'Team member invited successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()


@partner_bp.route('/api/team/<int:member_id>', methods=['DELETE'])
@partner_login_required
def remove_team_member(member_id):
    """Remove a team member"""
    db = get_db()
    try:
        tenant_id = session['partner_id']

        tenant_user = db.query(TenantUser).filter_by(id=member_id, tenant_id=tenant_id).first()
        if not tenant_user:
            return jsonify({'success': False, 'error': 'Team member not found'}), 404

        if tenant_user.is_primary_admin:
            return jsonify({'success': False, 'error': 'Cannot remove primary admin'}), 400

        db.delete(tenant_user)
        db.commit()

        return jsonify({'success': True, 'message': 'Team member removed'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()


# ============================================================================
# Analytics Routes
# ============================================================================

@partner_bp.route('/analytics')
@partner_login_required
def analytics():
    """Analytics page"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        # Get client IDs
        tenant_client_ids = [tc.client_id for tc in db.query(TenantClient).filter_by(tenant_id=tenant.id).all()]

        # Calculate stats
        stats = {
            'total_clients': len(tenant_client_ids),
            'active_clients': 0,
            'completed_cases': 0,
            'avg_completion_days': 0
        }

        if tenant_client_ids:
            clients = db.query(Client).filter(Client.id.in_(tenant_client_ids)).all()
            stats['active_clients'] = sum(1 for c in clients if c.status in ['active', 'in_progress'])
            stats['completed_cases'] = sum(1 for c in clients if c.status == 'complete')

        # Monthly client acquisition (last 6 months)
        monthly_data = []
        for i in range(6):
            month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
            month_start = month_start.replace(hour=0, minute=0, second=0, microsecond=0)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

            count = 0
            if tenant_client_ids:
                count = db.query(Client).filter(
                    Client.id.in_(tenant_client_ids),
                    Client.created_at >= month_start,
                    Client.created_at <= month_end
                ).count()

            monthly_data.insert(0, {
                'month': month_start.strftime('%b %Y'),
                'count': count
            })

        return render_template(
            'partner_portal/analytics.html',
            tenant=tenant,
            stats=stats,
            monthly_data=monthly_data
        )
    finally:
        db.close()


@partner_bp.route('/api/analytics/summary', methods=['GET'])
@partner_login_required
def get_analytics_summary():
    """Get analytics summary as JSON"""
    db = get_db()
    try:
        tenant_id = session['partner_id']

        # Get client IDs
        tenant_client_ids = [tc.client_id for tc in db.query(TenantClient).filter_by(tenant_id=tenant_id).all()]

        stats = {
            'total_clients': len(tenant_client_ids),
            'active_clients': 0,
            'completed_cases': 0,
            'success_rate': 0
        }

        if tenant_client_ids:
            clients = db.query(Client).filter(Client.id.in_(tenant_client_ids)).all()
            stats['active_clients'] = sum(1 for c in clients if c.status in ['active', 'in_progress'])
            stats['completed_cases'] = sum(1 for c in clients if c.status == 'complete')

            if stats['total_clients'] > 0:
                stats['success_rate'] = round(stats['completed_cases'] / stats['total_clients'] * 100, 1)

        return jsonify(stats)
    finally:
        db.close()


# ============================================================================
# Settings Routes
# ============================================================================

@partner_bp.route('/settings')
@partner_login_required
def settings():
    """Settings page"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()
        return render_template('partner_portal/settings.html', tenant=tenant)
    finally:
        db.close()


@partner_bp.route('/api/settings', methods=['PUT'])
@partner_login_required
def update_settings():
    """Update account settings"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        data = request.json or {}

        # Update allowed fields
        if 'admin_email' in data and data['admin_email']:
            new_email = data['admin_email'].strip().lower()
            # Check for duplicate
            existing = db.query(WhiteLabelTenant).filter(
                WhiteLabelTenant.admin_email == new_email,
                WhiteLabelTenant.id != tenant.id
            ).first()
            if existing:
                return jsonify({'success': False, 'error': 'Email already in use'}), 400
            tenant.admin_email = new_email

        if 'webhook_url' in data:
            tenant.webhook_url = data['webhook_url']

        tenant.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({'success': True, 'message': 'Settings updated successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()


@partner_bp.route('/api/settings/password', methods=['PUT'])
@partner_login_required
def change_password():
    """Change password"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        data = request.json or {}
        current = data.get('current_password', '')
        new_pass = data.get('new_password', '')
        confirm = data.get('confirm_password', '')

        if not tenant.admin_password_hash or not check_password_hash(tenant.admin_password_hash, current):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400

        if len(new_pass) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400

        if new_pass != confirm:
            return jsonify({'success': False, 'error': 'Passwords do not match'}), 400

        tenant.admin_password_hash = generate_password_hash(new_pass)
        tenant.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({'success': True, 'message': 'Password changed successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()


@partner_bp.route('/api/settings/regenerate-api-key', methods=['POST'])
@partner_login_required
def regenerate_api_key():
    """Regenerate API key"""
    db = get_db()
    try:
        tenant = db.query(WhiteLabelTenant).filter_by(id=session['partner_id']).first()

        tenant.api_key = secrets.token_urlsafe(32)
        tenant.updated_at = datetime.utcnow()
        db.commit()

        return jsonify({'success': True, 'api_key': tenant.api_key})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400
    finally:
        db.close()
