import os
import re
import io
import zipfile
import time
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm.attributes import flag_modified

# API Configuration
ANTHROPIC_API_KEY = os.environ.get('FCRA Automation Secure', '')
if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith('INVALID') or len(ANTHROPIC_API_KEY) < 20:
    print(f"⚠️  WARNING: Invalid or missing Anthropic API key!")
    print(f"   Expected: Secret 'FCRA Automation Secure' with valid sk-ant-... key")
    print(f"   Got: {'<empty>' if not ANTHROPIC_API_KEY else f'<too short: {len(ANTHROPIC_API_KEY)} chars>'}")
    ANTHROPIC_API_KEY = 'sk-ant-invalid-placeholder-key'

from anthropic import Anthropic
from prompt_loader import get_prompt_loader

try:
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    if 'invalid' in ANTHROPIC_API_KEY.lower():
        print("⚠️  Using placeholder API key - Stage 1 & Stage 2 will fail!")
    else:
        print("✅ Anthropic API client initialized")
except Exception as e:
    print(f"❌ Failed to initialize Anthropic client: {e}")
    # Still create a dummy client to prevent crashes
    client = None
from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for
from flask_cors import CORS
import os
from datetime import datetime
from database import init_db, get_db, Client, CreditReport, Analysis, DisputeLetter, Violation, Standing, Damages, CaseScore, Case, CaseEvent, Document, Notification, Settlement, AnalysisQueue, CRAResponse, DisputeItem, SecondaryBureauFreeze, ClientReferral, SignupDraft, Task, ClientNote, ClientDocument, SignupSettings, ClientUpload, SMSLog, EmailLog, EmailTemplate, CreditScoreSnapshot, CreditScoreProjection, CaseDeadline, Staff, STAFF_ROLES, check_staff_permission, Furnisher, FurnisherStats, CFPBComplaint
from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import uuid
from datetime import timedelta
from pdf_generator import LetterPDFGenerator, SectionPDFGenerator, CreditAnalysisPDFGenerator
from litigation_tools import calculate_damages, calculate_case_score, assess_willfulness
from jwt_utils import require_jwt, create_token
from services.encryption import encrypt_value, decrypt_value, migrate_plaintext_to_encrypted, is_encrypted
import json

app = Flask(__name__)

# Secret key for session management (use environment variable or generate secure key)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Session configuration for secure cookies
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session expiry

# Allow Replit frontend + WordPress frontend + any admin UIs
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# Allow large credit report uploads (up to 20MB)
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024

# Simple in-memory rate limiting for login attempts
login_attempts = {}  # {email: {'count': int, 'last_attempt': datetime}}

# Store received credit reports
credit_reports = []

# Track which analyses have been marked as delivered (in-memory flag)
delivered_cases = set()

# Initialize PDF generators
pdf_gen = LetterPDFGenerator()
section_pdf_gen = SectionPDFGenerator()

# Create required directories
os.makedirs("static/section_pdfs", exist_ok=True)
os.makedirs("static/generated_letters", exist_ok=True)
os.makedirs("static/logs", exist_ok=True)
os.makedirs("static/client_uploads", exist_ok=True)

# Initialize database
try:
    init_db()
    print("✅ Database initialized successfully")
    
    # Migrate any existing plaintext passwords to encrypted format
    try:
        db = get_db()
        migrated = migrate_plaintext_to_encrypted(db, Client)
        if migrated > 0:
            print(f"✅ Migrated {migrated} passwords to encrypted format")
        db.close()
    except Exception as me:
        print(f"⚠️  Password migration check: {me}")
except Exception as e:
    print(f"⚠️  Database initialization error: {e}")

def create_initial_admin():
    """Create initial admin account if no staff exists"""
    db = get_db()
    try:
        staff_count = db.query(Staff).count()
        if staff_count == 0:
            initial_password = 'ChangeMe123!'
            admin = Staff(
                email='admin@brightpathascend.com',
                password_hash=generate_password_hash(initial_password),
                first_name='Admin',
                last_name='User',
                role='admin',
                is_active=True,
                force_password_change=True
            )
            db.add(admin)
            db.commit()
            print("\n" + "="*60)
            print("🔐 INITIAL ADMIN ACCOUNT CREATED")
            print("="*60)
            print(f"   Email:    admin@brightpathascend.com")
            print(f"   Password: {initial_password}")
            print("   ⚠️  Please change this password immediately!")
            print("="*60 + "\n")
    except Exception as e:
        print(f"⚠️  Admin account setup: {e}")
    finally:
        db.close()

try:
    create_initial_admin()
except Exception as e:
    print(f"⚠️  Initial admin setup: {e}")

def require_staff(roles=None):
    """Decorator to require staff authentication and optional role check"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'staff_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect('/staff/login')
            
            if roles and session.get('staff_role') not in roles:
                if 'admin' not in roles and session.get('staff_role') != 'admin':
                    if request.is_json:
                        return jsonify({'error': 'Insufficient permissions'}), 403
                    return render_template('error.html', 
                        error='Access Denied', 
                        message='You do not have permission to access this page.'), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.route('/staff/login', methods=['GET', 'POST'])
def staff_login():
    """Staff login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            return render_template('staff_login.html', error='Please enter email and password')
        
        db = get_db()
        try:
            staff = db.query(Staff).filter_by(email=email).first()
            
            if not staff:
                return render_template('staff_login.html', error='Invalid email or password', email=email)
            
            if not staff.is_active:
                return render_template('staff_login.html', error='Account is disabled. Contact administrator.', email=email)
            
            if not check_password_hash(staff.password_hash, password):
                return render_template('staff_login.html', error='Invalid email or password', email=email)
            
            staff.last_login = datetime.utcnow()
            db.commit()
            
            session.permanent = True
            session['staff_id'] = staff.id
            session['staff_role'] = staff.role
            session['staff_name'] = staff.full_name
            session['staff_email'] = staff.email
            session['staff_initials'] = staff.initials
            
            if staff.force_password_change:
                return render_template('staff_login.html', force_change=True)
            
            return redirect('/dashboard')
            
        except Exception as e:
            print(f"Login error: {e}")
            return render_template('staff_login.html', error='Login error. Please try again.')
        finally:
            db.close()
    
    if 'staff_id' in session:
        return redirect('/dashboard')
    
    return render_template('staff_login.html')


@app.route('/staff/change-password', methods=['POST'])
def staff_change_password():
    """Handle forced password change"""
    if 'staff_id' not in session:
        return redirect('/staff/login')
    
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if len(new_password) < 8:
        return render_template('staff_login.html', force_change=True, error='Password must be at least 8 characters')
    
    if new_password != confirm_password:
        return render_template('staff_login.html', force_change=True, error='Passwords do not match')
    
    db = get_db()
    try:
        staff = db.query(Staff).filter_by(id=session['staff_id']).first()
        if staff:
            staff.password_hash = generate_password_hash(new_password)
            staff.force_password_change = False
            staff.updated_at = datetime.utcnow()
            db.commit()
            return redirect('/dashboard')
    except Exception as e:
        print(f"Password change error: {e}")
        return render_template('staff_login.html', force_change=True, error='Error updating password')
    finally:
        db.close()
    
    return redirect('/staff/login')


@app.route('/staff/logout')
def staff_logout():
    """Staff logout"""
    session.pop('staff_id', None)
    session.pop('staff_role', None)
    session.pop('staff_name', None)
    session.pop('staff_email', None)
    session.pop('staff_initials', None)
    return redirect('/staff/login')


@app.route('/api/staff/login', methods=['POST'])
def api_staff_login():
    """API endpoint for staff login"""
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password required'}), 400
    
    db = get_db()
    try:
        staff = db.query(Staff).filter_by(email=email).first()
        
        if not staff or not check_password_hash(staff.password_hash, password):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        if not staff.is_active:
            return jsonify({'success': False, 'error': 'Account disabled'}), 403
        
        staff.last_login = datetime.utcnow()
        db.commit()
        
        session.permanent = True
        session['staff_id'] = staff.id
        session['staff_role'] = staff.role
        session['staff_name'] = staff.full_name
        session['staff_email'] = staff.email
        session['staff_initials'] = staff.initials
        
        return jsonify({
            'success': True,
            'staff': {
                'id': staff.id,
                'name': staff.full_name,
                'email': staff.email,
                'role': staff.role
            },
            'force_password_change': staff.force_password_change
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/dashboard/staff')
@require_staff(roles=['admin'])
def dashboard_staff():
    """Staff management page - admin only"""
    db = get_db()
    try:
        staff_members = db.query(Staff).order_by(Staff.created_at.desc()).all()
        
        stats = {
            'total': len(staff_members),
            'admins': sum(1 for s in staff_members if s.role == 'admin'),
            'attorneys': sum(1 for s in staff_members if s.role == 'attorney'),
            'paralegals': sum(1 for s in staff_members if s.role == 'paralegal'),
            'viewers': sum(1 for s in staff_members if s.role == 'viewer')
        }
        
        message = request.args.get('message')
        error = request.args.get('error')
        
        return render_template('staff_management.html', 
            staff_members=staff_members,
            stats=stats,
            message=message,
            error=error
        )
    except Exception as e:
        return f"Error loading staff: {e}", 500
    finally:
        db.close()


@app.route('/api/staff/add', methods=['POST'])
@require_staff(roles=['admin'])
def api_staff_add():
    """Add a new staff member"""
    email = request.form.get('email', '').strip().lower()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    role = request.form.get('role', 'viewer')
    password = request.form.get('password', '')
    
    if not email or not password:
        return redirect('/dashboard/staff?error=Email and password are required')
    
    if role not in STAFF_ROLES:
        return redirect('/dashboard/staff?error=Invalid role selected')
    
    db = get_db()
    try:
        existing = db.query(Staff).filter_by(email=email).first()
        if existing:
            return redirect('/dashboard/staff?error=Email already exists')
        
        new_staff = Staff(
            email=email,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
            is_active=True,
            force_password_change=True,
            created_by_id=session.get('staff_id')
        )
        db.add(new_staff)
        db.commit()
        
        return redirect(f'/dashboard/staff?message=Staff member {first_name} {last_name} added successfully')
    except Exception as e:
        db.rollback()
        return redirect(f'/dashboard/staff?error=Error adding staff: {str(e)}')
    finally:
        db.close()


@app.route('/api/staff/update', methods=['POST'])
@require_staff(roles=['admin'])
def api_staff_update():
    """Update a staff member"""
    staff_id = request.form.get('staff_id')
    email = request.form.get('email', '').strip().lower()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    role = request.form.get('role', 'viewer')
    is_active = request.form.get('is_active', 'true') == 'true'
    
    if not staff_id or not email:
        return redirect('/dashboard/staff?error=Missing required fields')
    
    db = get_db()
    try:
        staff = db.query(Staff).filter_by(id=int(staff_id)).first()
        if not staff:
            return redirect('/dashboard/staff?error=Staff member not found')
        
        existing = db.query(Staff).filter(Staff.email == email, Staff.id != int(staff_id)).first()
        if existing:
            return redirect('/dashboard/staff?error=Email already in use')
        
        staff.email = email
        staff.first_name = first_name
        staff.last_name = last_name
        staff.role = role
        staff.is_active = is_active
        staff.updated_at = datetime.utcnow()
        db.commit()
        
        return redirect(f'/dashboard/staff?message=Staff member updated successfully')
    except Exception as e:
        db.rollback()
        return redirect(f'/dashboard/staff?error=Error updating staff: {str(e)}')
    finally:
        db.close()


@app.route('/api/staff/reset-password', methods=['POST'])
@require_staff(roles=['admin'])
def api_staff_reset_password():
    """Reset a staff member's password"""
    data = request.get_json() or {}
    staff_id = data.get('staff_id')
    
    if not staff_id:
        return jsonify({'success': False, 'error': 'Staff ID required'}), 400
    
    db = get_db()
    try:
        staff = db.query(Staff).filter_by(id=int(staff_id)).first()
        if not staff:
            return jsonify({'success': False, 'error': 'Staff member not found'}), 404
        
        temp_password = secrets.token_urlsafe(12)
        staff.password_hash = generate_password_hash(temp_password)
        staff.force_password_change = True
        staff.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({
            'success': True,
            'temp_password': temp_password,
            'message': 'Password reset successfully'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/staff/toggle-status', methods=['POST'])
@require_staff(roles=['admin'])
def api_staff_toggle_status():
    """Toggle a staff member's active status"""
    data = request.get_json() or {}
    staff_id = data.get('staff_id')
    
    if not staff_id:
        return jsonify({'success': False, 'error': 'Staff ID required'}), 400
    
    if int(staff_id) == session.get('staff_id'):
        return jsonify({'success': False, 'error': 'Cannot disable your own account'}), 400
    
    db = get_db()
    try:
        staff = db.query(Staff).filter_by(id=int(staff_id)).first()
        if not staff:
            return jsonify({'success': False, 'error': 'Staff member not found'}), 404
        
        staff.is_active = not staff.is_active
        staff.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({
            'success': True,
            'is_active': staff.is_active,
            'message': f'Staff member {"enabled" if staff.is_active else "disabled"}'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/')
def home():
    """Home page - shows form or status"""
    return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FCRA Analysis - Brightpath Ascend</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 40px auto;
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        h1 { color: #2c3e50; text-align: center; margin-bottom: 10px; }
        .subtitle { color: #7f8c8d; text-align: center; margin-bottom: 30px; font-size: 14px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; color: #34495e; font-weight: 600; margin-bottom: 8px; font-size: 14px; }
        .required { color: #e74c3c; }
        input, select, textarea {
            width: 100%;
            padding: 12px;
            border: 2px solid #ecf0f1;
            border-radius: 8px;
            font-size: 14px;
        }
        textarea { min-height: 120px; font-family: monospace; }
        button {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        button:disabled { background: #95a5a6; }
        .status {
            margin-top: 20px;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            display: none;
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 FCRA Analysis System</h1>
        <p class="subtitle">Brightpath Ascend Group</p>

        <form id="form">
            <div class="form-group">
                <label>CLIENT NAME <span class="required">*</span></label>
                <input type="text" id="clientName" required>
            </div>

            <div class="form-group">
                <label>CMM CONTACT ID <span class="required">*</span></label>
                <input type="text" id="cmmContactId" required>
            </div>

            <div class="form-group">
                <label>CREDIT PROVIDER <span class="required">*</span></label>
                <select id="creditProvider" required>
                    <option value="">-- Select Provider --</option>
                    <option value="IdentityIQ.com">IdentityIQ.com</option>
                    <option value="MyScoreIQ.com">MyScoreIQ.com</option>
                    <option value="SmartCredit.com">SmartCredit.com</option>
                    <option value="MyFreeScoreNow.com">MyFreeScoreNow.com</option>
                    <option value="HighScoreNow.com">HighScoreNow.com</option>
                    <option value="IdentityClub.com">IdentityClub.com</option>
                    <option value="PrivacyGuard.com">PrivacyGuard.com</option>
                    <option value="IDClub.com">IDClub.com</option>
                    <option value="MyThreeScores.com">MyThreeScores.com</option>
                    <option value="MyScore750.com">MyScore750.com</option>
                    <option value="CreditHeroScore.com">CreditHeroScore.com</option>
                    <option value="CFILifePlan.com">CFILifePlan.com</option>
                </select>
            </div>

            <div class="form-group">
                <label>DISPUTE ROUND <span class="required">*</span></label>
                <select id="disputeRound" required>
                    <option value="1">Round 1 - Initial Dispute (New Client)</option>
                    <option value="2">Round 2 - MOV Request / Follow-up</option>
                    <option value="3">Round 3 - Pre-Litigation Warning</option>
                    <option value="4">Round 4 - Final Demand / Intent to Sue</option>
                </select>
                <small style="color: #7f8c8d; display: block; margin-top: 5px;">
                    <strong>Round 1:</strong> New client - full analysis + initial strong RLPP letters<br>
                    <strong>Round 2+:</strong> Existing client - escalated letters based on bureau responses
                </small>
            </div>

            <div id="existingClientFields" style="display: none;">
                <div class="form-group">
                    <label>PREVIOUS DISPUTE LETTER(S)</label>
                    <textarea id="previousLetters" placeholder="Paste the dispute letters you previously sent to the bureaus..."></textarea>
                    <small style="color: #7f8c8d; display: block; margin-top: 5px;">
                        Copy/paste the actual letters you sent in previous rounds
                    </small>
                </div>

                <div class="form-group">
                    <label>BUREAU RESPONSE(S)</label>
                    <textarea id="bureauResponses" placeholder="Paste bureau responses here, or type 'NO RESPONSE' if they ignored you..."></textarea>
                    <small style="color: #7f8c8d; display: block; margin-top: 5px;">
                        Include all responses from Experian, TransUnion, and Equifax
                    </small>
                </div>

                <div class="form-group">
                    <label>DISPUTE TIMELINE</label>
                    <input type="text" id="disputeTimeline" placeholder="e.g., Sent 10/15/25, Response 11/1/25">
                    <small style="color: #7f8c8d; display: block; margin-top: 5px;">
                        Dates sent and received for violation tracking
                    </small>
                </div>
            </div>

<div class="form-group">
    <label>ANALYSIS MODE <span class="required">*</span></label>
    <select id="analysisMode" required>
        <option value="manual">Manual Review (Stop at verification checkpoint)</option>
        <option value="auto">Automatic (Generate complete report immediately)</option>
    </select>
    <small style="color: #7f8c8d; display: block; margin-top: 5px;">
        <strong>Manual:</strong> Review violations before client report (recommended for new cases)<br>
        <strong>Automatic:</strong> Generate everything in one pass (faster, for clear cases)
    </small>
</div>
            <div class="form-group">
                <label>CREDIT REPORT HTML <span class="required">*</span></label>
                <textarea id="creditReportHTML" required></textarea>
            </div>

            <button type="submit">🚀 ANALYZE</button>
            <div id="status" class="status"></div>
        </form>
    </div>

    <script>
        // Show/hide existing client fields based on dispute round
        document.getElementById('disputeRound').addEventListener('change', function() {
            const round = parseInt(this.value);
            const existingFields = document.getElementById('existingClientFields');
            
            if (round > 1) {
                existingFields.style.display = 'block';
            } else {
                existingFields.style.display = 'none';
            }
        });

        document.getElementById('form').addEventListener('submit', async function(e) {
            e.preventDefault();
            const btn = e.target.querySelector('button');
            const status = document.getElementById('status');

            btn.disabled = true;
            btn.textContent = '⏳ Sending...';

            try {
                const disputeRound = parseInt(document.getElementById('disputeRound').value);
                const payload = {
                    clientName: document.getElementById('clientName').value,
                    cmmContactId: document.getElementById('cmmContactId').value,
                    creditProvider: document.getElementById('creditProvider').value,
                    disputeRound: disputeRound,
                    analysisMode: document.getElementById('analysisMode').value,
                    creditReportHTML: document.getElementById('creditReportHTML').value
                };

                // Add existing client data for Round 2+
                if (disputeRound > 1) {
                    payload.previousLetters = document.getElementById('previousLetters').value;
                    payload.bureauResponses = document.getElementById('bureauResponses').value;
                    payload.disputeTimeline = document.getElementById('disputeTimeline').value;
                }

                const response = await fetch('/webhook', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (result.success) {
                    status.className = 'status success';
                    status.innerHTML = '✅ Success! Report received for ' + result.client;
                    status.style.display = 'block';
                    document.getElementById('form').reset();
                    document.getElementById('existingClientFields').style.display = 'none';
                } else {
                    throw new Error(result.error);
                }
            } catch (error) {
                status.className = 'status error';
                status.innerHTML = '❌ Error: ' + error.message;
                status.style.display = 'block';
            } finally {
                btn.disabled = false;
                btn.textContent = '🚀 ANALYZE';
            }
        });
    </script>
</body>
</html>'''


def clean_credit_report_html(html):
    """Strip unnecessary HTML to reduce size - but keep content intact"""
    from bs4 import BeautifulSoup
    import re

    print(f"📊 Original size: {len(html):,} characters")

    # Remove inline styles
    html = re.sub(r'style="[^"]*"', '', html)
    # Remove script tags
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    # Remove comments
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)
    # Remove base64 images
    html = re.sub(r'data:image/[^;]+;base64,[^"\']+', '', html)

    # Extract just the text content
    soup = BeautifulSoup(html, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)

    # If cleaning destroys everything (>99% reduction), return original HTML instead
    if len(text) < len(html) * 0.01:
        print(f"⚠️  Aggressive cleaning destroyed content! Using original HTML instead.")
        text = html

    print(f"✂️ Cleaned size: {len(text):,} characters")
    print(
        f"💰 Saved: {max(0, len(html) - len(text)):,} characters ({max(0, 100 - (len(text)/len(html)*100)):.1f}% reduction)"
    )

    return text


# Section markers for splitting credit reports (enhanced patterns)
SECTION_MARKERS = {
    "tradelines": ["ACCOUNTS", "TRADELINES", "REVOLVING ACCOUNTS", "INSTALLMENT ACCOUNTS", "OPEN ACCOUNTS", "CLOSED ACCOUNTS"],
    "collections": ["COLLECTION", "COLLECTIONS"],
    "public_records": ["PUBLIC RECORD", "PUBLIC RECORDS", "BANKRUPTCIES", "JUDGMENTS", "TAX LIENS"],
    "inquiries": ["INQUIRIES", "CREDIT INQUIRIES", "REGULAR INQUIRIES", "HARD INQUIRIES"],
}


def split_report_into_sections(text: str) -> dict:
    """Split cleaned report text into logical sections based on common headings"""
    sections = {k: [] for k in SECTION_MARKERS.keys()}
    current_key = None

    if not text:
        return {}

    lines = text.splitlines()
    for line in lines:
        upper = line.strip().upper()

        # Check if this line looks like a section heading
        new_key = None
        for key, markers in SECTION_MARKERS.items():
            if any(m in upper for m in markers):
                new_key = key
                break

        if new_key:
            current_key = new_key
            sections[current_key].append(line)
        elif current_key:
            sections[current_key].append(line)

    # Join and drop empty sections
    finalized = {}
    for key, lines_list in sections.items():
        joined = "\n".join(lines_list).strip()
        if joined:
            finalized[key] = joined

    print("📚 split_report_into_sections:", {k: len(v) for k, v in finalized.items()})
    return finalized


def merge_standing(standings: list) -> dict:
    """Merge multiple standing blocks (OR booleans, SUM counts, concatenate strings)"""
    if not standings:
        return {"has_concrete_harm": False, "concrete_harm_type": "", "harm_details": "", "has_dissemination": False, "dissemination_details": "", "has_causation": False, "causation_details": "", "denial_letters_count": 0, "adverse_action_notices_count": 0}

    merged = {
        "has_concrete_harm": False,
        "concrete_harm_type": [],
        "harm_details": [],
        "has_dissemination": False,
        "dissemination_details": [],
        "has_causation": False,
        "causation_details": [],
        "denial_letters_count": 0,
        "adverse_action_notices_count": 0,
    }

    for s in standings:
        if not s:
            continue
        merged["has_concrete_harm"] = merged["has_concrete_harm"] or s.get("has_concrete_harm", False)
        merged["has_dissemination"] = merged["has_dissemination"] or s.get("has_dissemination", False)
        merged["has_causation"] = merged["has_causation"] or s.get("has_causation", False)
        if s.get("concrete_harm_type"): merged["concrete_harm_type"].append(str(s.get("concrete_harm_type")))
        if s.get("harm_details"): merged["harm_details"].append(str(s.get("harm_details")))
        if s.get("dissemination_details"): merged["dissemination_details"].append(str(s.get("dissemination_details")))
        if s.get("causation_details"): merged["causation_details"].append(str(s.get("causation_details")))
        merged["denial_letters_count"] += int(s.get("denial_letters_count", 0) or 0)
        merged["adverse_action_notices_count"] += int(s.get("adverse_action_notices_count", 0) or 0)

    return {
        "has_concrete_harm": merged["has_concrete_harm"],
        "concrete_harm_type": " | ".join(merged["concrete_harm_type"]),
        "harm_details": "\n\n".join(merged["harm_details"]),
        "has_dissemination": merged["has_dissemination"],
        "dissemination_details": "\n\n".join(merged["dissemination_details"]),
        "has_causation": merged["has_causation"],
        "causation_details": "\n\n".join(merged["causation_details"]),
        "denial_letters_count": merged["denial_letters_count"],
        "adverse_action_notices_count": merged["adverse_action_notices_count"],
    }


def merge_actual_damages(damages_list: list) -> dict:
    """Merge multiple actual_damages blocks by summing numeric fields"""
    merged = {"credit_denials_amount": 0, "higher_interest_amount": 0, "credit_monitoring_amount": 0, "time_stress_amount": 0, "other_actual_amount": 0, "notes": ""}
    notes = []
    for d in damages_list:
        if not d:
            continue
        merged["credit_denials_amount"] += float(d.get("credit_denials_amount", 0) or 0)
        merged["higher_interest_amount"] += float(d.get("higher_interest_amount", 0) or 0)
        merged["credit_monitoring_amount"] += float(d.get("credit_monitoring_amount", 0) or 0)
        merged["time_stress_amount"] += float(d.get("time_stress_amount", 0) or 0)
        merged["other_actual_amount"] += float(d.get("other_actual_amount", 0) or 0)
        if d.get("notes"): notes.append(str(d["notes"]))
    merged["notes"] = "\n\n".join(notes)
    return merged


def merge_litigation_data(section_results: list) -> dict:
    """Merge litigation_data from multiple sections into one"""
    all_violations = []
    standings = []
    damages_blocks = []
    for r in section_results:
        if not r:
            continue
        all_violations.extend(r.get("violations", []) or [])
        standings.append(r.get("standing", {}) or {})
        damages_blocks.append(r.get("actual_damages", {}) or {})
    merged = {
        "violations": all_violations,
        "standing": merge_standing(standings),
        "actual_damages": merge_actual_damages(damages_blocks),
    }
    print(f"🧩 merge_litigation_data: {len(all_violations)} total violations merged")
    return merged


def run_stage1_for_all_sections(client_name, cmm_id, provider, credit_report_text, analysis_mode="manual", dispute_round=1, previous_letters="", bureau_responses="", dispute_timeline=""):
    """Split report into sections and run Stage 1 analysis per section, merge results"""
    import time
    
    sections = split_report_into_sections(credit_report_text)
    if not sections:
        return {'success': False, 'error': 'Could not detect any recognizable sections in report'}

    all_section_results = []
    combined_analysis_parts = []
    total_tokens = 0
    total_cost = 0.0
    any_cache_read = False

    for section_name, section_text in sections.items():
        print(f"\n🔍 Stage 1 analysis for section: {section_name} ({len(section_text):,} chars)")
        result = analyze_with_claude(
            client_name=client_name,
            cmm_id=cmm_id,
            provider=provider,
            credit_report_html=section_text,
            analysis_mode=analysis_mode,
            dispute_round=dispute_round,
            previous_letters=previous_letters,
            bureau_responses=bureau_responses,
            dispute_timeline=dispute_timeline,
            stage=1
        )

        if not result.get('success'):
            print(f"❌ Section {section_name} failed: {result.get('error')}")
            all_section_results.append({'section_name': section_name, 'analysis': '', 'raw_litigation_data': None, 'error': result.get('error')})
            continue

        analysis_text = result.get('analysis', '') or ''
        litigation_data = extract_litigation_data(analysis_text)
        combined_analysis_parts.append(f"\n\n{'='*80}\nSECTION: {section_name.upper()}\n{'='*80}\n\n{analysis_text}")
        all_section_results.append({'section_name': section_name, 'analysis': analysis_text, 'raw_litigation_data': litigation_data})
        total_tokens += int(result.get('tokens_used', 0) or 0)
        total_cost += float(result.get('cost', 0.0) or 0.0)
        any_cache_read = any_cache_read or bool(result.get('cache_read', False))
        time.sleep(1)  # Rate limit protection

    parsed_litigation_blocks = [r['raw_litigation_data'] for r in all_section_results if r.get('raw_litigation_data')]
    if not parsed_litigation_blocks:
        return {'success': False, 'error': 'No valid litigation_data extracted from any section', 'combined_analysis': "\n\n".join(combined_analysis_parts), 'per_section': all_section_results, 'tokens_used': total_tokens, 'cost': total_cost, 'cache_read': any_cache_read}

    merged_litigation = merge_litigation_data(parsed_litigation_blocks)
    return {'success': True, 'combined_analysis': "\n\n".join(combined_analysis_parts), 'litigation_data': merged_litigation, 'per_section': all_section_results, 'tokens_used': total_tokens, 'cost': total_cost, 'cache_read': any_cache_read}


def truncate_for_token_limit(text, max_tokens_for_report=140_000):
    """
    Hard cap the report size so the full prompt stays under Anthropic's 200k token limit.
    Rough approximation: ~4 characters per token for English text.
    """
    if not text:
        return text

    approx_tokens = len(text) / 4.0
    if approx_tokens <= max_tokens_for_report:
        return text

    ratio = max_tokens_for_report / approx_tokens
    new_len = int(len(text) * ratio)
    truncated = text[:new_len]

    print(
        f"⚠️ truncate_for_token_limit: report truncated for token limit: "
        f"{len(text):,} chars (~{approx_tokens:,.0f} tokens) -> "
        f"{len(truncated):,} chars (~{len(truncated)/4.0:,.0f} tokens)"
    )

    return truncated


def analyze_with_claude(client_name,
                        cmm_id,
                        provider,
                        credit_report_html,
                        analysis_mode='manual',
                        dispute_round=1,
                        previous_letters='',
                        bureau_responses='',
                        dispute_timeline='',
                        stage=1,
                        stage_1_results=''):
    """Send credit report to Claude for FCRA analysis - TWO STAGE WORKFLOW
    
    Stage 1: Violations/Standing/Damages analysis only (small prompt, fits token limit)
    Stage 2: Client documents/letters generation (uses Stage 1 results)
    """
    try:
        # CRITICAL: Clean & truncate HTML for Stage 1 to stay under 200k token limit
        if stage == 1:
            print(f"\n🧹 Cleaning credit report HTML to fit token limits...")
            credit_report_html = clean_credit_report_html(credit_report_html)
            print(f"🔒 Truncating to token limit...")
            credit_report_html = truncate_for_token_limit(credit_report_html, max_tokens_for_report=140_000)
        
        # Define round_names globally for both stages
        round_names = {
            1: "Round 1 - Initial Dispute (RLPP Strong Language)",
            2: "Round 2 - MOV Request / Follow-up",
            3: "Round 3 - Pre-Litigation Warning", 
            4: "Round 4 - Final Demand / Intent to Sue"
        }
        
        if stage == 1:
            # STAGE 1: COMPREHENSIVE violation detection prompt - finds ALL substantiated violations
            prompt = """You are an elite FCRA litigation attorney. Your task is COMPREHENSIVE violation detection.

**CRITICAL: Find EVERY substantiated violation - be thorough and aggressive in searching but only report REAL violations you can prove from the data. DO NOT fabricate or invent violations.**

===========================================================================
MATERIALITY STANDARD - CRITICAL FOR ALL VIOLATION TYPES
===========================================================================

**A difference is a violation ONLY IF it is MATERIAL (affects credit decisions):**
- Minor formatting differences are NOT violations (e.g., "10/2024" vs "10/01/2024")
- Trailing zeros or equivalent representations are NOT violations (e.g., "$1,500" vs "$1500.00")
- Date differences within the same month due to reporting cycles are NOT violations
- Only report violations where the contradiction is SUBSTANTIVE and PROVABLE

**SUBSTANTIVE means:**
- Balance difference of $100+ OR 10%+ of the balance amount
- Date difference of 30+ days that affects FCRA timeline calculations
- Status contradiction (e.g., "Open" vs "Closed", "Paid" vs "Charge-off")
- Missing required data element (DOLP on derogatory, account number, etc.)

===========================================================================
PARSING THE CLEANED CREDIT REPORT - HOW TO EXTRACT DATA
===========================================================================

The credit report has been cleaned to plain text. Look for these patterns:

**BUREAU SECTIONS:** Look for lines containing "TransUnion", "Experian", or "Equifax" as section headers.
The same account will appear in each bureau's section with potentially different data.

**COMMON FIELD PATTERNS (use these to extract data):**
- Date Last Active: Look for "Date Last Active:" or "Last Activity:" followed by MM/DD/YYYY or MM/YYYY
- Last Reported: Look for "Last Reported:" or "Reported:" followed by date
- Balance: Look for "Balance:" or "Current Balance:" followed by dollar amount (may have $ or commas)
- Payment Status: Look for "Payment Status:" or "Status:" followed by text like "Current", "Charge-off", "Paid"
- Date Opened: Look for "Date Opened:" or "Opened:" followed by date
- Date of Last Payment (DOLP): Look for "Date of Last Payment:" or "Last Payment:" followed by date or blank
- Account Number: Look for "Account #:" or "Account Number:" followed by partial/masked number

**MATCHING ACCOUNTS ACROSS BUREAUS:**
1. Find the account name/creditor (e.g., "CAPITAL ONE", "MIDLAND CREDIT")
2. Locate that creditor in each bureau section (TransUnion, Experian, Equifax)
3. Extract the same fields from each bureau's version
4. Compare values - only MATERIAL differences are violations

===========================================================================
VIOLATION TYPE CHECKLIST - CHECK EVERY SINGLE ONE WITH EXPLICIT DETECTION STEPS:
===========================================================================

**TYPE 1: BUREAU CONTRADICTIONS** (MOST VALUABLE - Check EVERY account across all 3 bureaus)
MATERIALITY THRESHOLD: Only report if difference is SUBSTANTIVE (affects credit decisions)
DETECTION STEPS:
1. For EACH account, extract: Date Last Active, Last Reported, Balance, Payment Status from TU/EX/EQ
2. Compare Date Last Active between TU vs EX vs EQ - MATERIAL difference (30+ days) = violation
3. Compare Last Reported dates - MATERIAL difference (30+ days) = violation  
4. Compare Balance amounts - MATERIAL difference ($100+ or 10%+) = violation
5. Compare Payment Status text - CONTRADICTORY status = violation (not just wording differences)
6. Check if account appears on some bureaus but NOT others = ghost account violation

Each MATERIAL difference found = separate violation entry with bureau_violations array showing each bureau's data

**TYPE 2: FUTURE DATE REPORTING** (PER SE UNREASONABLE - Check EVERY date field)
DETECTION STEPS:
1. Today's date is the analysis date - any date AFTER today is a future date
2. Scan ALL Date Last Active fields - is any date in the future?
3. Scan ALL Last Reported fields - is any date in the future?
4. Scan ALL Date Opened fields - is any date in the future?
5. Future dates are IMPOSSIBLE and constitute automatic willful violation

**TYPE 3: DUPLICATE ACCOUNTS**
DETECTION STEPS:
1. List all account numbers in the report
2. Check for exact duplicates (same account number twice)
3. Check for near-duplicates (same creditor, similar amounts, same dates)
4. Each duplicate = Metro 2 violation + §1681e(b)

**TYPE 4: MISSING DATE OF LAST PAYMENT (CUSHMAN VIOLATIONS)**
DETECTION STEPS:
1. Find ALL accounts with negative status (charge-off, collection, delinquent)
2. For each, check: Is "Date of Last Payment:" or "Last Payment:" present with an actual date?
3. If DOLP is blank/missing/"Not Reported" on derogatory account = Cushman violation
4. Per Cushman v. TransUnion, 115 F.3d 220: furnishers must maintain tangible proof

**TYPE 5: DISPUTE NOTATION WITHOUT RESOLUTION**
DETECTION STEPS:
1. Search for "Consumer disputes" or "Item disputed" or "Disputed" notations
2. For each disputed account, check: Is negative information still present?
3. If disputed AND still negative = failed reinvestigation under §1681i(a)(1)(A)

**TYPE 6: PAYMENT HISTORY CONTRADICTIONS**
MATERIALITY THRESHOLD: Status and history must actually contradict (not just incomplete data)
DETECTION STEPS:
1. Read Payment Status field (e.g., "Past due 30 days", "Current")
2. Read Payment History pattern (e.g., "CCCCC111CC" or grid with late markers)
3. Does status match pattern? "Current" status + recent late markers (1,2,3) = contradiction
4. Does pattern match status? All "C" pattern + "Past due" status = contradiction

**TYPE 7: STALE/RE-AGED ACCOUNTS**
DETECTION STEPS:
1. Find Date Opened and Date Last Active for each account
2. Calculate: Is Date Last Active implausibly recent for old accounts?
3. Check: Has the 7-year reporting period from Date of First Delinquency passed?
4. Re-aging (making old debt appear new) = violation

**TYPE 8: BALANCE DISCREPANCIES**
MATERIALITY THRESHOLD: Non-zero balance on closed/paid account is always material
DETECTION STEPS:
1. Check Account Status - is it "Closed" or "Paid" or "Paid/Closed"?
2. If closed/paid, check Balance - is it $0 or blank?
3. Closed/paid account with non-zero balance = violation
4. Compare balance across bureaus - MATERIAL difference ($100+ or 10%+) = violation

**TYPE 9: ACCOUNT STATUS CONTRADICTIONS**
DETECTION STEPS:
1. For each account, extract Status from TU/EX/EQ
2. Compare: "Open" vs "Closed" across bureaus = violation
3. Compare: "Paid" vs "Charge-off" across bureaus = violation
4. Note: "Current" vs "Pays as Agreed" are equivalent - NOT a violation

**TYPE 10: INQUIRY VIOLATIONS**
DETECTION STEPS:
1. List all hard inquiries with dates and creditor names
2. Check for same creditor pulling multiple times within 14 days (shopping exception exists for auto/mortgage)
3. Check for inquiries without apparent authorization (no new account opened)
4. Check for inquiry date anomalies (future dates, impossible dates)

**TYPE 11: MIXED FILE VIOLATIONS**
DETECTION STEPS:
1. Look for accounts with unfamiliar creditor names
2. Check for accounts with addresses not matching consumer's known addresses
3. Check for accounts with different name variations that suggest wrong person
4. Any account not belonging to consumer = mixed file violation

**TYPE 12: FURNISHER REPORTING FAILURES**
MATERIALITY THRESHOLD: Only SUBSTANTIVE differences in furnisher data
DETECTION STEPS:
1. Same creditor, same account number - compare data across all 3 bureaus
2. MATERIAL difference in what the furnisher reported to different bureaus = §1681s-2(a) violation
3. Document exactly what was reported to each bureau

===========================================================================
STANDING ANALYSIS (TransUnion LLC v. Ramirez, 141 S. Ct. 2190)
===========================================================================

**ELEMENT 1: DISSEMINATION (Score 1-3)**
- List EVERY hard inquiry with date and creditor name
- Each inquiry during inaccurate reporting = dissemination evidence
- 3+ inquiries with inaccurate info = STRONG dissemination

**ELEMENT 2: CONCRETE HARM (Score 1-4)**
- Credit scores in FAIR/POOR range (below 680) = suppression harm
- Calculate: Estimated score WITHOUT violations vs actual score
- Interest rate differential: Each 20 points = 0.5% rate increase
- Annual harm = rate differential × total balances × years
- 4 = Documented denial or >$2K harm; 3 = Score suppression <680; 2 = Minor harm; 1 = Speculative

**ELEMENT 3: CAUSATION (Score 1-3)**
- "But for" the inaccuracy, would harm have occurred?
- Temporal proximity: Did inquiries happen during inaccurate reporting?
- Direct link between specific violation and specific harm

**STANDING SCORE = Element1 + Element2 + Element3 (max 10)**
- Circuit adjustment: 2nd Circuit -2, 9th Circuit -1
- 8-10 = STRONG; 5-7 = MODERATE; 1-4 = WEAK

===========================================================================
WILLFULNESS ASSESSMENT (Safeco Insurance Co. v. Burr)
===========================================================================

Score each category:
1. Direct Knowledge (0-4): Major bureaus/banks have compliance programs
2. Pattern (0-5): Same violation on multiple accounts or consumers
3. Awareness (0-4): Prior complaints, settlements, consent orders
4. Recklessness (0-3): Automated responses, no real investigation

TOTAL: ___/16 (13+ = definite willful; 9-12 = likely willful; 5-8 = mixed)

===========================================================================
OUTPUT FORMAT (REQUIRED):
===========================================================================

After your analysis, output this JSON block. Use bureau_violations array to track each bureau separately:

<LITIGATION_DATA>
{
  "violations": [
    {
      "account_name": "OPENSKY CBNK",
      "violation_type": "Bureau Contradiction - Different Dates",
      "bureau_violations": [
        {"bureau": "TransUnion", "data_reported": "Date Last Active: 10/06/2025", "fcra_section": "§1681e(b)"},
        {"bureau": "Experian", "data_reported": "Date Last Active: 11/30/2022", "fcra_section": "§1681e(b)"}
      ],
      "description": "3-year date discrepancy between bureaus",
      "is_willful": true,
      "willfulness_indicators": "Future date is per se unreasonable"
    },
    {
      "account_name": "CAPITAL ONE",
      "violation_type": "Future Date Reporting",
      "bureau_violations": [
        {"bureau": "TransUnion", "data_reported": "Date Last Active: 12/15/2025", "fcra_section": "§1681e(b)"}
      ],
      "description": "Future date reporting - date after today is impossible",
      "is_willful": true,
      "willfulness_indicators": "Future dates cannot be verified and are per se unreasonable"
    },
    {
      "account_name": "MIDLAND CREDIT",
      "violation_type": "Missing Date of Last Payment (Cushman)",
      "bureau_violations": [
        {"bureau": "Equifax", "data_reported": "DOLP: Not Reported, Status: Charge-off", "fcra_section": "§1681s-2(a)"}
      ],
      "description": "Charge-off account lacks required Date of Last Payment",
      "is_willful": false,
      "willfulness_indicators": "Negligent failure to maintain records per Cushman v. TransUnion"
    }
  ],
  "standing": {
    "has_concrete_harm": true,
    "concrete_harm_type": "Credit Score Suppression / Higher Interest",
    "harm_details": "Scores 592-617 (Fair range) suppressed 80-120 points. 5 creditor inquiries during inaccurate reporting. Estimated $2,400-3,600 annual harm from rate differential.",
    "has_dissemination": true,
    "dissemination_details": "ACURA OF DEN 04/05/2024, CITIBANK 01/03/2025, CONTINENTAL FINANCE 06/24/2024, MACYS 01/26/2024, TBOM 11/30/2023 - all accessed during violation period",
    "has_causation": true,
    "causation_details": "But for violations, scores would be 686-726 (Good range). Client would qualify for prime lending. Automotive inquiry without new account suggests denial.",
    "denial_letters_count": 0,
    "adverse_action_notices_count": 0
  },
  "actual_damages": {
    "credit_denials_amount": 0,
    "higher_interest_amount": 2400,
    "credit_monitoring_amount": 0,
    "time_stress_amount": 1000,
    "other_actual_amount": 0,
    "notes": "Score suppression 80-120 pts = 8-12% higher rates. $25K balances × 10% differential = $2,500/yr. 40+ hours monitoring at $25/hr = $1,000"
  }
}
</LITIGATION_DATA>

**CRITICAL RULES:**
1. ACCURACY OVER QUANTITY - Find real violations but NEVER fabricate. Only report violations you can prove from the actual data.
2. Apply MATERIALITY STANDARD - Minor differences, formatting variations, and equivalent representations are NOT violations.
3. Use bureau_violations array to track EACH bureau's data separately for cross-bureau violations.
4. Provide SPECIFIC dates, amounts, account names - no placeholders or guesses.
5. Standing score should reflect actual harm (subprime scores = concrete harm).
6. Dollar amounts as numbers only (no $ signs).
7. Output JSON block at the very end.

===========================================================================
NO VIOLATIONS FOUND - ACCEPTABLE OUTCOME
===========================================================================

**If after thorough search you find NO substantiated violations, output an empty violations array:**

<LITIGATION_DATA>
{
  "violations": [],
  "standing": {
    "has_concrete_harm": false,
    "concrete_harm_type": "None identified",
    "harm_details": "No substantiated FCRA violations found in credit report. All data appears consistent across bureaus.",
    "has_dissemination": false,
    "dissemination_details": "No inaccurate information was disseminated.",
    "has_causation": false,
    "causation_details": "No causal link between credit reporting and harm.",
    "denial_letters_count": 0,
    "adverse_action_notices_count": 0
  },
  "actual_damages": {
    "credit_denials_amount": 0,
    "higher_interest_amount": 0,
    "credit_monitoring_amount": 0,
    "time_stress_amount": 0,
    "other_actual_amount": 0,
    "notes": "No violations identified - no damages calculation applicable."
  }
}
</LITIGATION_DATA>

**An empty violations array is acceptable and preferred if no PROVABLE violations exist.**
**Do NOT invent violations to fill the array - this destroys legal credibility.**"""
        else:
            # STAGE 2: Use comprehensive FCRA v2.6 + RLPP prompt
            print("\n🔨 Loading comprehensive FCRA v2.6 + RLPP prompt...")
            loader = get_prompt_loader()
            prompt = loader.build_comprehensive_stage2_prompt(dispute_round=dispute_round)
            
            if not prompt:
                return {'success': False, 'error': 'Failed to load comprehensive prompt templates'}
        
        # Stage 2 needs round_names variable
        if stage != 1:
            round_names = {
                1: "Round 1 - Initial Dispute (RLPP Strong Language)",
                2: "Round 2 - MOV Request / Follow-up",
                3: "Round 3 - Pre-Litigation Warning", 
                4: "Round 4 - Final Demand / Intent to Sue"
            }
        
        super_prompt = prompt
        
        # Stage 2 needs additional context in system prompt
        if stage != 1:
            super_prompt += """

You have Stage 1 analysis results. Now generate the client-facing documents:

PART 5: CLIENT-FACING REPORT (40-50 pages)
- Executive Summary
- Detailed violation analysis
- Standing assessment
- Damages calculation
- Legal strategy & case strength

PART 6: DISPUTE LETTERS
- Round """ + str(dispute_round) + """ letter with RLPP language
- Statutory citations
- Violation documentation
- Proof of willfulness

PART 7: MOV REQUEST (if applicable)
- Method of Verification request
- Bureau-specific requirements
- Deadline enforcement

Output the complete client-facing documents."""
        
        # For Stage 1, build dispute context and user message
        if stage == 1:
            round_names = {
                1: "Round 1 - Initial Dispute (RLPP Strong Language)",
                2: "Round 2 - MOV Request / Follow-up",
                3: "Round 3 - Pre-Litigation Warning", 
                4: "Round 4 - Final Demand / Intent to Sue"
            }
            
            dispute_context = ""
            if dispute_round > 1 and (previous_letters or bureau_responses):
                dispute_context = f"""

PREVIOUS DISPUTE CONTEXT:
Timeline: {dispute_timeline if dispute_timeline else 'Not provided'}
Previous Letters: {previous_letters if previous_letters else 'Not provided'}
Bureau Responses: {bureau_responses if bureau_responses else 'NO RESPONSE - Possible §611(a)(7) violation'}
"""
            
            user_message = f"""
🚨 STAGE 1: VIOLATIONS & DAMAGES ANALYSIS

CLIENT: {client_name} (CMM ID: {cmm_id})
Provider: {provider}
Dispute Round: {round_names.get(dispute_round, 'Round ' + str(dispute_round))}

{dispute_context}

CREDIT REPORT:
{credit_report_html}

TASK: Analyze ONLY for violations, standing, and damages.
Output JSON at end with violations, standing, actual_damages.
NO client reports, NO letters - just the analysis data.
"""
        else:
            # Stage 2: Generate comprehensive 107-page litigation package
            user_message = f"""
🚨 STAGE 2: GENERATE COMPREHENSIVE 107-PAGE LITIGATION PACKAGE

**CLIENT INFORMATION:**
- Name: {client_name}
- CMM ID: {cmm_id}
- Provider: {provider}
- Dispute Round: {dispute_round}

**STAGE 1 ANALYSIS RESULTS (USE THIS DATA):**
{stage_1_results}

**YOUR TASK:**
Generate complete client-facing litigation package with ALL PARTS (0-5):
- Part 0-3: Forensic analysis (use Stage 1 data from above)
- Part 4: Formal dispute letters (extract real violations from Stage 1)
- Part 5: MOV requests (where applicable)

Use RLPP aggressive language appropriate for Round {dispute_round}.
Include scissor markers (✂️) around each letter for easy extraction.
Total output: 80-120 pages, litigation-ready format.

CRITICAL: Use ACTUAL violations and account data from Stage 1 results above.
NO templates or placeholders. Extract real account names, bureaus, violations.
"""
        
        # Call Claude API
        print(f"\n🤖 Sending to Claude API for analysis...")
        print(f"   Stage: {stage}")
        print(f"   Analysis mode: {analysis_mode if stage == 1 else 'auto (Stage 2)'}")
        print(f"   Prompt size: {len(super_prompt):,} characters")
        print(f"   Report size: {len(credit_report_html):,} characters" if stage == 1 else "")
        
        import time
        start_time = time.time()
        
        # Normalize prompts to ensure cache consistency (strip whitespace)
        normalized_super_prompt = super_prompt.strip()
        normalized_user_message = user_message.strip()
        
        # Token logging for visibility
        approx_prompt_tokens = (len(normalized_super_prompt) + len(normalized_user_message)) / 4.0
        print(f"📏 Approx prompt tokens before API call: ~{approx_prompt_tokens:,.0f}")
        
        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=50000,
                temperature=0,
                timeout=900.0,
                system=[
                    {
                        "type": "text",
                        "text": normalized_super_prompt,
                        "cache_control": {"type": "ephemeral"}
                    }
                ],
                messages=[{
                    "role": "user",
                    "content": normalized_user_message
                }]
            )
        except Exception as api_err:
            error_msg = f"Claude API Error: {str(api_err)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
        
        elapsed_time = time.time() - start_time
        print(f"⏱️  API call completed in {elapsed_time:.1f} seconds")

        # Extract token usage and calculate cost savings (guard against errors)
        usage = getattr(message, 'usage', None)
        if usage:
            # Cost per million tokens (Anthropic pricing for Claude Sonnet 4)
            INPUT_COST_PER_MTOK = 3.00  # $3 per million input tokens
            CACHED_INPUT_COST_PER_MTOK = 0.30  # $0.30 per million cached tokens (90% discount)
            OUTPUT_COST_PER_MTOK = 15.00  # $15 per million output tokens
            
            # Calculate costs
            input_tokens = getattr(usage, 'input_tokens', 0)
            cache_creation_tokens = getattr(usage, 'cache_creation_input_tokens', 0)
            cache_read_tokens = getattr(usage, 'cache_read_input_tokens', 0)
            output_tokens = getattr(usage, 'output_tokens', 0)
            
            # Actual cost calculation
            cache_creation_cost = (cache_creation_tokens / 1_000_000) * INPUT_COST_PER_MTOK
            cache_read_cost = (cache_read_tokens / 1_000_000) * CACHED_INPUT_COST_PER_MTOK
            regular_input_cost = (input_tokens / 1_000_000) * INPUT_COST_PER_MTOK
            output_cost = (output_tokens / 1_000_000) * OUTPUT_COST_PER_MTOK
            
            total_input_tokens = input_tokens + cache_creation_tokens + cache_read_tokens
            total_cost = cache_creation_cost + cache_read_cost + regular_input_cost + output_cost
            cost_without_cache = ((input_tokens + cache_creation_tokens + cache_read_tokens) / 1_000_000) * INPUT_COST_PER_MTOK + output_cost
            
            savings = cost_without_cache - total_cost
            savings_percent = (savings / cost_without_cache * 100) if cost_without_cache > 0 else 0
            
            print("\n" + "="*60)
            print("💰 COST ANALYSIS")
            print("="*60)
            print(f"📊 Token Usage:")
            print(f"   Input tokens: {input_tokens:,}")
            if cache_creation_tokens > 0:
                print(f"   Cache creation: {cache_creation_tokens:,} (first request)")
            if cache_read_tokens > 0:
                print(f"   Cache read: {cache_read_tokens:,} (90% cheaper!)")
            print(f"   Output tokens: {output_tokens:,}")
            print(f"   Total: {total_input_tokens + output_tokens:,}")
            
            print(f"\n💵 Cost Breakdown:")
            if cache_creation_cost > 0:
                print(f"   Cache creation: ${cache_creation_cost:.4f}")
            if cache_read_cost > 0:
                print(f"   Cached input: ${cache_read_cost:.4f} ⚡")
            if regular_input_cost > 0:
                print(f"   Regular input: ${regular_input_cost:.4f}")
            print(f"   Output: ${output_cost:.4f}")
            print(f"   TOTAL: ${total_cost:.4f}")
            
            if cache_read_tokens > 0:
                print(f"\n🎉 SAVINGS:")
                print(f"   Without caching: ${cost_without_cache:.4f}")
                print(f"   With caching: ${total_cost:.4f}")
                print(f"   You saved: ${savings:.4f} ({savings_percent:.1f}%)")
            elif cache_creation_tokens > 0:
                print(f"\n📌 Cache Status: Created")
                print(f"   Next requests will save ~${cache_creation_cost * 0.9:.4f} (90% discount)")
            
            print("="*60 + "\n")

        analysis_result = ""
        for block in message.content:
            if block.type == 'text':
                analysis_result += block.text

        print(f"\n✅ Analysis result length: {len(analysis_result):,} characters")

        # Extract litigation data if Stage 1
        if stage == 1:
            extract_litigation_data(analysis_result)
        
        # Calculate totals safely
        total_tokens = 0
        total_cost_final = 0
        if usage:
            total_tokens = total_input_tokens + output_tokens
            total_cost_final = total_cost
        
        return {
            'success': True,
            'analysis': analysis_result,
            'client': client_name,
            'stage': stage,
            'tokens_used': total_tokens,
            'cost': total_cost_final,
            'cache_read': cache_read_tokens > 0 if usage else False
        }

    except Exception as e:
        print(f"❌ Claude API Error: {str(e)}")
        return {'success': False, 'error': str(e)}


def extract_litigation_data(analysis_text):
    """Extract structured litigation data from Claude's analysis"""
    import json
    import re
    
    try:
        # Try to find <LITIGATION_DATA> JSON block
        pattern = r'<LITIGATION_DATA>\s*(\{[\s\S]*?\})\s*</LITIGATION_DATA>'
        match = re.search(pattern, analysis_text)
        
        if match:
            json_str = match.group(1)
            print(f"✅ Found <LITIGATION_DATA> block ({len(json_str)} characters)")
        else:
            # Fallback: look for bare JSON at end
            last_brace = analysis_text.rfind('{')
            if last_brace == -1:
                print("⚠️  No JSON found in analysis")
                return None
            json_str = analysis_text[last_brace:]
            print(f"✅ Found bare JSON at end ({len(json_str)} characters)")
        
        # Parse JSON
        litigation_data = json.loads(json_str)
        
        # Validate structure
        if 'violations' not in litigation_data:
            litigation_data['violations'] = []
        if 'standing' not in litigation_data:
            litigation_data['standing'] = {}
        if 'actual_damages' not in litigation_data:
            litigation_data['actual_damages'] = {}
        
        # Ensure evidence fields are properly formatted for all violations
        for v in litigation_data.get('violations', []):
            if 'evidence' not in v:
                v['evidence'] = {}
            if not isinstance(v['evidence'], dict):
                v['evidence'] = {}
            v['evidence'].setdefault('transunion', 'Not specified')
            v['evidence'].setdefault('experian', 'Not specified')
            v['evidence'].setdefault('equifax', 'Not specified')
        
        print(f"   ✅ Extracted {len(litigation_data.get('violations', []))} violations")
        return litigation_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parse error: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error extracting litigation data: {str(e)}")
        return None


def auto_populate_litigation_database(analysis_id, client_id, litigation_data, db):
    """
    Automatically populate Violations, Standing, and Damages tables from extracted data
    """
    from litigation_tools import calculate_damages, calculate_case_score
    
    try:
        print(f"\n🤖 AUTO-POPULATING LITIGATION DATABASE...")
        
        # 1. POPULATE VIOLATIONS (handles both old single-bureau format and new bureau_violations array)
        violations_added = 0
        if litigation_data.get('violations'):
            for v_data in litigation_data['violations']:
                # Check for new bureau_violations array format
                bureau_violations = v_data.get('bureau_violations', [])
                
                if bureau_violations and isinstance(bureau_violations, list):
                    # NEW FORMAT: Create separate violation record per bureau
                    for bv in bureau_violations:
                        bureau = bv.get('bureau', 'Unknown')
                        fcra_section = bv.get('fcra_section', v_data.get('fcra_section', ''))
                        data_reported = bv.get('data_reported', '')
                        
                        violation = Violation(
                            analysis_id=analysis_id,
                            client_id=client_id,
                            account_name=v_data.get('account_name', 'Unknown'),
                            bureau=bureau,
                            fcra_section=fcra_section,
                            violation_type=v_data.get('violation_type', ''),
                            description=f"{v_data.get('description', '')} | {data_reported}",
                            is_willful=v_data.get('is_willful', False),
                            willfulness_notes=v_data.get('willfulness_indicators', ''),
                            statutory_damages_min=100,
                            statutory_damages_max=1000
                        )
                        db.add(violation)
                        violations_added += 1
                else:
                    # OLD FORMAT: Single bureau per violation (backwards compatibility)
                    violation = Violation(
                        analysis_id=analysis_id,
                        client_id=client_id,
                        account_name=v_data.get('account_name', 'Unknown'),
                        bureau=v_data.get('bureau', 'Unknown'),
                        fcra_section=v_data.get('fcra_section', ''),
                        violation_type=v_data.get('violation_type', ''),
                        description=v_data.get('description', ''),
                        is_willful=v_data.get('is_willful', False),
                        willfulness_notes=v_data.get('willfulness_indicators', ''),
                        statutory_damages_min=100,
                        statutory_damages_max=1000
                    )
                    db.add(violation)
                    violations_added += 1
            
            print(f"   ✅ Added {violations_added} violations")
        
        # 2. POPULATE STANDING
        if litigation_data.get('standing'):
            s_data = litigation_data['standing']
            standing = Standing(
                analysis_id=analysis_id,
                client_id=client_id,
                has_concrete_harm=s_data.get('has_concrete_harm', False),
                concrete_harm_type=s_data.get('concrete_harm_type', ''),
                concrete_harm_details=s_data.get('harm_details', ''),
                has_dissemination=s_data.get('has_dissemination', False),
                dissemination_details=s_data.get('dissemination_details', ''),
                has_causation=s_data.get('has_causation', False),
                causation_details=s_data.get('causation_details', ''),
                denial_letters_count=s_data.get('denial_letters_count', 0),
                adverse_action_notices_count=s_data.get('adverse_action_notices_count', 0),
                standing_verified=True
            )
            db.add(standing)
            print(f"   ✅ Added standing data (concrete harm: {s_data.get('has_concrete_harm', False)})")
        
        # Commit violations and standing before calculating damages
        db.commit()
        
        # 3. CALCULATE AND POPULATE DAMAGES
        violations_for_calc = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        violations_data = [{
            'fcra_section': v.fcra_section,
            'is_willful': v.is_willful,
            'violation_type': v.violation_type
        } for v in violations_for_calc]
        
        # Map Claude's output format to calculate_damages expected format
        claude_damages = litigation_data.get('actual_damages', {})
        actual_damages_input = {
            'credit_denials': claude_damages.get('credit_denials_amount', 0),
            'higher_interest': claude_damages.get('higher_interest_amount', 0),
            'credit_monitoring': claude_damages.get('credit_monitoring_amount', 0),
            'time_stress': claude_damages.get('time_stress_amount', 0),
            'other': claude_damages.get('other_actual_amount', 0),
            'notes': claude_damages.get('notes', '')
        }
        damages_calc = calculate_damages(violations_data, actual_damages_input)
        
        damages = Damages(
            analysis_id=analysis_id,
            client_id=client_id,
            credit_denials_amount=damages_calc['actual']['credit_denials'],
            higher_interest_amount=damages_calc['actual']['higher_interest'],
            credit_monitoring_amount=damages_calc['actual']['credit_monitoring'],
            time_stress_amount=damages_calc['actual']['time_stress'],
            other_actual_amount=damages_calc['actual']['other'],
            actual_damages_total=damages_calc['actual']['total'],
            section_605b_count=damages_calc['statutory']['605b']['count'],
            section_605b_amount=damages_calc['statutory']['605b']['amount'],
            section_607b_count=damages_calc['statutory']['607b']['count'],
            section_607b_amount=damages_calc['statutory']['607b']['amount'],
            section_611_count=damages_calc['statutory']['611']['count'],
            section_611_amount=damages_calc['statutory']['611']['amount'],
            section_623_count=damages_calc['statutory']['623']['count'],
            section_623_amount=damages_calc['statutory']['623']['amount'],
            statutory_damages_total=damages_calc['statutory']['total'],
            willfulness_multiplier=damages_calc['punitive']['multiplier'],
            punitive_damages_amount=damages_calc['punitive']['amount'],
            estimated_hours=damages_calc['attorney_fees']['estimated_hours'],
            hourly_rate=damages_calc['attorney_fees']['hourly_rate'],
            attorney_fees_projection=damages_calc['attorney_fees']['total'],
            total_exposure=damages_calc['settlement']['total_exposure'],
            settlement_target=damages_calc['settlement']['target'],
            minimum_acceptable=damages_calc['settlement']['minimum'],
            notes=actual_damages_input.get('notes', '')
        )
        db.add(damages)
        print(f"   ✅ Calculated damages (total exposure: ${damages_calc['settlement']['total_exposure']:,.2f})")
        
        # Commit damages before calculating score
        db.commit()
        
        # 4. CALCULATE AND POPULATE CASE SCORE
        standing_obj = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        standing_data = {
            'has_concrete_harm': standing_obj.has_concrete_harm if standing_obj else False,
            'has_dissemination': standing_obj.has_dissemination if standing_obj else False,
            'has_causation': standing_obj.has_causation if standing_obj else False,
            'denial_letters_count': standing_obj.denial_letters_count if standing_obj else 0
        }
        
        documentation_complete = len(violations_data) > 0 and standing_obj is not None
        
        score_data = calculate_case_score(
            standing_data,
            violations_data,
            damages_calc,
            documentation_complete
        )
        
        case_score = CaseScore(
            analysis_id=analysis_id,
            client_id=client_id,
            total_score=score_data['total'],
            standing_score=score_data['standing'],
            violation_quality_score=score_data['violation_quality'],
            willfulness_score=score_data['willfulness'],
            documentation_score=score_data['documentation'],
            settlement_probability=score_data['settlement_probability'],
            case_strength=score_data['case_strength'],
            recommendation=score_data['recommendation'],
            recommendation_notes='\n'.join(score_data['notes'])
        )
        db.add(case_score)
        print(f"   ✅ Calculated case score ({score_data['total']}/10 - {score_data['case_strength']})")
        
        # Final commit
        db.commit()
        
        print(f"✅ AUTO-POPULATION COMPLETE!")
        print(f"   Violations: {violations_added}")
        print(f"   Standing: Added")
        print(f"   Damages: ${damages_calc['settlement']['total_exposure']:,.2f}")
        print(f"   Case Score: {score_data['total']}/10")
        
        return True
        
    except Exception as e:
        print(f"❌ Error auto-populating database: {str(e)}")
        db.rollback()
        return False


@app.route('/webhook', methods=['POST'])
def webhook():
    """Receives credit report data from HTML form or file upload"""
    try:
        # Get data from request - support JSON, form data, and file uploads
        data = request.get_json(force=True, silent=True) or request.form.to_dict()

        # Extract the specific fields we need
        client_name = data.get('clientName', 'Unknown Client')
        cmm_contact_id = data.get('cmmContactId', 'Unknown')
        credit_provider = data.get('creditProvider', 'Unknown Provider')
        credit_report_html = data.get('creditReportHTML', '')
        analysis_mode = data.get('analysisMode', 'manual')
        dispute_round = int(data.get('disputeRound', 1))
        previous_letters = data.get('previousLetters', '')
        bureau_responses = data.get('bureauResponses', '')
        dispute_timeline = data.get('disputeTimeline', '')
        
        # Read uploaded file if HTML not in form data
        if not credit_report_html and 'creditReportHTML' in request.files:
            file = request.files['creditReportHTML']
            if file and file.filename:
                credit_report_html = file.read().decode('utf-8')
        
        credit_report_html = clean_credit_report_html(credit_report_html)
        # Validate we got the essential data
        if not credit_report_html:
            return jsonify({
                'success': False,
                'error': 'No credit report HTML provided'
            }), 400

        # Create report record
        report = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'client_name': client_name,
            'cmm_contact_id': cmm_contact_id,
            'credit_provider': credit_provider,
            'report_length': len(credit_report_html),
            'credit_report_html': credit_report_html,
            'status': 'received',
            'processed': False
        }
        # Analyze with Claude API (section-based Stage 1)
        analysis = run_stage1_for_all_sections(
            client_name=client_name,
            cmm_id=cmm_contact_id,
            provider=credit_provider,
            credit_report_text=credit_report_html,
            analysis_mode=analysis_mode,
            dispute_round=dispute_round,
            previous_letters=previous_letters,
            bureau_responses=bureau_responses,
            dispute_timeline=dispute_timeline
        )

        if analysis.get('success'):
            report['analysis'] = analysis.get('combined_analysis', '')
            report['processed'] = True
            report['tokens_used'] = analysis.get('tokens_used', 0)
            report['cost'] = analysis.get('cost', 0)
            print(f"✅ FCRA Section-based Analysis completed for {client_name}")
        else:
            report['analysis_error'] = analysis.get('error', 'Unknown error')
            print(f"⚠️ Section-based analysis failed: {analysis.get('error')}")
        # Store it
        credit_reports.append(report)

        # Log to console
        print("\n" + "=" * 60)
        print("✅ CREDIT REPORT RECEIVED")
        print("=" * 60)
        print(f"Client: {client_name}")
        print(f"CMM ID: {cmm_contact_id}")
        print(f"Provider: {credit_provider}")
        print(f"Report Size: {len(credit_report_html):,} characters")
        print(f"Time: {report['timestamp']}")
        print("=" * 60 + "\n")

        # Return success
        return jsonify({
            'success': True,
            'message': 'Credit report received successfully! ✅',
            'client': client_name,
            'cmm_id': cmm_contact_id,
            'timestamp': report['timestamp'],
            'report_size': len(credit_report_html),
            'total_reports': len(credit_reports)
        }), 200

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}\n")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/webhook/batch', methods=['POST'])
def webhook_batch():
    """Process multiple credit reports in batch - maximizes cache efficiency
    
    Features:
    - Input validation for each client entry
    - Error isolation (one failure doesn't abort the batch)
    - Complete results including analyses for automation
    - Shared prompt cache across all clients (90% savings after first)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid JSON or no data provided'
            }), 400
        
        clients = data.get('clients', [])
        
        if not clients:
            return jsonify({
                'success': False,
                'error': 'No clients provided in batch request. Expected "clients" array.'
            }), 400
        
        if not isinstance(clients, list):
            return jsonify({
                'success': False,
                'error': '"clients" must be an array'
            }), 400
        
        print("\n" + "=" * 60)
        print(f"📦 BATCH PROCESSING: {len(clients)} clients")
        print("=" * 60)
        
        results = []
        
        for idx, client_data in enumerate(clients, 1):
            # Validate client_data is a dictionary
            if not isinstance(client_data, dict):
                results.append({
                    'client_index': idx,
                    'client_name': f'Client {idx}',
                    'success': False,
                    'error': f'Client entry {idx} is not a valid object',
                    'analysis': None
                })
                print(f"⚠️ Skipping invalid client {idx} (not a valid object)")
                continue
            
            # Extract and validate fields
            client_name = client_data.get('clientName', f'Client {idx}')
            cmm_contact_id = client_data.get('cmmContactId', 'Unknown')
            credit_provider = client_data.get('creditProvider', 'Unknown Provider')
            credit_report_html = client_data.get('creditReportHTML', '')
            analysis_mode = client_data.get('analysisMode', 'manual')
            dispute_round = client_data.get('disputeRound', 1)
            previous_letters = client_data.get('previousLetters', '')
            bureau_responses = client_data.get('bureauResponses', '')
            dispute_timeline = client_data.get('disputeTimeline', '')
            
            print(f"\n🔄 Processing {idx}/{len(clients)}: {client_name}")
            
            # Validate required fields
            if not credit_report_html or not credit_report_html.strip():
                results.append({
                    'client_index': idx,
                    'client_name': client_name,
                    'success': False,
                    'error': 'No credit report HTML provided',
                    'analysis': None
                })
                print(f"⚠️ Skipping {client_name}: No credit report HTML")
                continue
            
            # Validate dispute_round is valid integer
            try:
                dispute_round = int(dispute_round)
                if dispute_round < 1 or dispute_round > 4:
                    raise ValueError("Dispute round must be 1-4")
            except (ValueError, TypeError) as e:
                results.append({
                    'client_index': idx,
                    'client_name': client_name,
                    'success': False,
                    'error': f'Invalid dispute_round: {str(e)}',
                    'analysis': None
                })
                print(f"⚠️ Skipping {client_name}: Invalid dispute round")
                continue
            
            # Process this client (isolated error handling)
            try:
                # Clean the report
                cleaned_html = clean_credit_report_html(credit_report_html)
                
                # Analyze with Claude API (benefits from cached prompt!)
                analysis_result = analyze_with_claude(
                    client_name=client_name,
                    cmm_id=cmm_contact_id,
                    provider=credit_provider,
                    credit_report_html=cleaned_html,
                    analysis_mode=analysis_mode,
                    dispute_round=dispute_round,
                    previous_letters=previous_letters,
                    bureau_responses=bureau_responses,
                    dispute_timeline=dispute_timeline
                )
                
                # Store report
                report = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'client_name': client_name,
                    'cmm_contact_id': cmm_contact_id,
                    'credit_provider': credit_provider,
                    'report_length': len(cleaned_html),
                    'credit_report_html': cleaned_html,
                    'status': 'processed' if analysis_result['success'] else 'failed',
                    'processed': analysis_result['success']
                }
                
                if analysis_result['success']:
                    report['analysis'] = analysis_result['analysis']
                    results.append({
                        'client_index': idx,
                        'client_name': client_name,
                        'cmm_contact_id': cmm_contact_id,
                        'success': True,
                        'message': 'Analysis completed successfully',
                        'analysis': analysis_result['analysis']  # Include full analysis for automation
                    })
                    print(f"✅ Completed: {client_name}")
                else:
                    report['analysis_error'] = analysis_result.get('error', 'Unknown error')
                    results.append({
                        'client_index': idx,
                        'client_name': client_name,
                        'cmm_contact_id': cmm_contact_id,
                        'success': False,
                        'error': analysis_result.get('error', 'Unknown error'),
                        'analysis': None
                    })
                    print(f"❌ Failed: {client_name} - {analysis_result.get('error', 'Unknown error')}")
                
                credit_reports.append(report)
                
            except Exception as client_error:
                # Isolate error - don't let one client crash the entire batch
                error_msg = f"Processing error: {str(client_error)}"
                results.append({
                    'client_index': idx,
                    'client_name': client_name,
                    'cmm_contact_id': cmm_contact_id,
                    'success': False,
                    'error': error_msg,
                    'analysis': None
                })
                print(f"❌ Error processing {client_name}: {error_msg}")
                continue
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print("\n" + "=" * 60)
        print("🎉 BATCH PROCESSING COMPLETE")
        print("=" * 60)
        print(f"✅ Successful: {successful}/{len(results)}")
        print(f"❌ Failed: {failed}/{len(results)}")
        if successful > 1:
            print(f"💰 Prompt caching saved ~70-90% on costs (after first request)!")
        print("=" * 60 + "\n")
        
        return jsonify({
            'success': True,  # Batch endpoint succeeded even if some clients failed
            'total_clients': len(results),
            'successful': successful,
            'failed': failed,
            'results': results,  # Includes full analyses for automation
            'message': f'Batch processing complete: {successful}/{len(results)} successful'
        }), 200
        
    except Exception as e:
        print(f"\n❌ BATCH ENDPOINT ERROR: {str(e)}\n")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Batch endpoint error: {str(e)}'
        }), 500


@app.route('/history')
def history():
    """View all received reports in JSON format"""
    # Don't include full HTML to keep response manageable
    summary = []
    for report in credit_reports:
        summary.append({
            'timestamp': report['timestamp'],
            'client_name': report['client_name'],
            'cmm_contact_id': report['cmm_contact_id'],
            'credit_provider': report['credit_provider'],
            'report_length': report['report_length'],
            'status': report['status'],
            'processed': report['processed']
        })

    return jsonify({
        'total_reports': len(credit_reports),
        'reports': summary
    }), 200


@app.route('/test')
def test():
    """Test endpoint to verify server is working"""
    return jsonify({
        'status': 'Server is running! ✅',
        'reports_received': len(credit_reports),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ready_for': 'Phase 2 - Claude API Integration'
    }), 200


@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear all stored reports (for testing)"""
    credit_reports.clear()
    return jsonify({'success': True, 'message': 'All reports cleared'}), 200


@app.route('/view/<int:report_id>')
def view_analysis(report_id):
    """View the Claude analysis for a specific report"""
    if report_id < len(credit_reports):
        report = credit_reports[report_id]
        return f"""
        <html>
        <head><title>FCRA Analysis - {report['client_name']}</title></head>
        <body style="font-family: Arial; max-width: 900px; margin: 40px auto; padding: 20px;">
            <h1>FCRA Analysis: {report['client_name']}</h1>
            <p><strong>CMM ID:</strong> {report['cmm_contact_id']}</p>
            <p><strong>Provider:</strong> {report['credit_provider']}</p>
            <p><strong>Date:</strong> {report['timestamp']}</p>
            <hr>
            <h2>Analysis:</h2>
            <pre style="white-space: pre-wrap; background: #f5f5f5; padding: 20px; border-radius: 8px;">{report.get('analysis', 'No analysis available')}</pre>
            <p><a href="/">← Back to Form</a></p>
        </body>
        </html>
        """
    return "Report not found", 404


@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for generating analyses and letters"""
    return render_template('admin.html')


# ============================================================
# PDF CREDIT REPORT PARSING ENDPOINTS
# ============================================================

@app.route('/api/credit-report/parse-pdf', methods=['POST'])
def parse_credit_report_pdf():
    """Parse a PDF credit report and extract structured data."""
    import tempfile
    from services.pdf_parser_service import parse_credit_report_pdf as parse_pdf, get_parsed_text_for_analysis
    
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'No file uploaded. Please select a PDF file.'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'No file selected. Please choose a PDF file.'
        }), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Please upload a PDF file.'
        }), 400
    
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        result = parse_pdf(temp_path)
        
        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Failed to parse PDF'),
                'is_password_protected': 'password' in (result.get('error', '')).lower(),
                'is_image_based': 'image' in (result.get('error', '')).lower() or 'ocr' in (result.get('error', '')).lower()
            }), 400
        
        formatted_text = get_parsed_text_for_analysis(result)
        
        return jsonify({
            'success': True,
            'bureau': result.get('bureau', 'Unknown'),
            'personal_info': result.get('personal_info', {}),
            'accounts': result.get('accounts', []),
            'inquiries': result.get('inquiries', []),
            'collections': result.get('collections', []),
            'public_records': result.get('public_records', []),
            'parsing_confidence': result.get('parsing_confidence', 0.0),
            'text_length': result.get('text_length', 0),
            'formatted_text': formatted_text,
            'raw_text': result.get('raw_text', '')[:50000]
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error processing PDF: {str(e)}'
        }), 500
    finally:
        if temp_path:
            try:
                import os
                os.unlink(temp_path)
            except:
                pass


@app.route('/api/credit-report/parse-and-analyze', methods=['POST'])
def parse_and_analyze_credit_report():
    """Parse a PDF credit report and immediately run FCRA analysis."""
    import tempfile
    from services.pdf_parser_service import parse_credit_report_pdf as parse_pdf, get_parsed_text_for_analysis
    
    db = get_db()
    temp_path = None
    
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded. Please select a PDF file.'
            }), 400
        
        file = request.files['file']
        client_name = request.form.get('clientName', '')
        client_email = request.form.get('clientEmail', '')
        credit_provider = request.form.get('creditProvider', 'Unknown')
        dispute_round = int(request.form.get('disputeRound', 1))
        
        if not client_name:
            return jsonify({
                'success': False,
                'error': 'Client name is required'
            }), 400
        
        if file.filename == '' or not file.filename.lower().endswith('.pdf'):
            return jsonify({
                'success': False,
                'error': 'Please upload a valid PDF file.'
            }), 400
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        parse_result = parse_pdf(temp_path)
        
        if not parse_result.get('success'):
            return jsonify({
                'success': False,
                'error': parse_result.get('error', 'Failed to parse PDF'),
                'is_password_protected': 'password' in (parse_result.get('error', '')).lower(),
                'is_image_based': 'image' in (parse_result.get('error', '')).lower()
            }), 400
        
        formatted_text = get_parsed_text_for_analysis(parse_result)
        
        if parse_result.get('bureau') and parse_result.get('bureau') != 'Unknown':
            credit_provider = parse_result.get('bureau')
        
        client = db.query(Client).filter_by(name=client_name).first()
        if not client:
            client = Client(name=client_name, email=client_email)
            db.add(client)
            db.commit()
            db.refresh(client)
        
        credit_report_record = CreditReport(
            client_id=client.id,
            client_name=client_name,
            credit_provider=credit_provider,
            report_html=formatted_text,
            report_date=datetime.now()
        )
        db.add(credit_report_record)
        db.commit()
        db.refresh(credit_report_record)
        
        section_analysis = run_stage1_for_all_sections(
            client_name=client_name,
            cmm_id=request.form.get('cmmContactId', ''),
            provider=credit_provider,
            credit_report_text=formatted_text,
            analysis_mode='manual',
            dispute_round=dispute_round,
            previous_letters='',
            bureau_responses='',
            dispute_timeline=''
        )
        
        if not section_analysis.get('success'):
            return jsonify({
                'success': False,
                'error': section_analysis.get('error', 'Analysis failed'),
                'parsed_data': {
                    'bureau': parse_result.get('bureau'),
                    'accounts_count': len(parse_result.get('accounts', [])),
                    'inquiries_count': len(parse_result.get('inquiries', [])),
                    'collections_count': len(parse_result.get('collections', []))
                }
            }), 500
        
        merged_litigation_data = section_analysis.get('litigation_data', {})
        
        analysis_record = Analysis(
            credit_report_id=credit_report_record.id,
            client_id=client.id,
            client_name=client_name,
            dispute_round=dispute_round,
            analysis_mode='manual',
            stage=1,
            stage_1_analysis=str(merged_litigation_data),
            cost=section_analysis.get('cost', 0),
            tokens_used=section_analysis.get('tokens_used', 0),
            cache_read=section_analysis.get('cache_read', False)
        )
        db.add(analysis_record)
        db.commit()
        db.refresh(analysis_record)
        
        if merged_litigation_data and merged_litigation_data.get('violations'):
            auto_populate_litigation_database(
                analysis_id=analysis_record.id,
                client_id=client.id,
                litigation_data=merged_litigation_data,
                db=db
            )
        
        return jsonify({
            'success': True,
            'analysis_id': analysis_record.id,
            'client_id': client.id,
            'parsed_data': {
                'bureau': parse_result.get('bureau'),
                'personal_info': parse_result.get('personal_info', {}),
                'accounts_count': len(parse_result.get('accounts', [])),
                'inquiries_count': len(parse_result.get('inquiries', [])),
                'collections_count': len(parse_result.get('collections', [])),
                'public_records_count': len(parse_result.get('public_records', [])),
                'parsing_confidence': parse_result.get('parsing_confidence', 0.0)
            },
            'violations_found': len(merged_litigation_data.get('violations', [])),
            'review_url': f'/analysis/{analysis_record.id}/review'
        }), 200
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500
    finally:
        db.close()
        if temp_path:
            try:
                import os
                os.unlink(temp_path)
            except:
                pass


@app.route('/api/analyze', methods=['POST'])
def analyze_and_generate_letters():
    """Process credit report, run AI analysis, generate PDF letters"""
    db = get_db()
    try:
        print(f"\n📋 /api/analyze endpoint called")
        data = request.get_json()
        if not data:
            print(f"❌ No JSON data received")
            return jsonify({'success': False, 'error': 'No JSON data in request'}), 400
        
        client_name = data.get('clientName')
        client_email = data.get('clientEmail', '')
        credit_provider = data.get('creditProvider', 'Unknown')
        credit_report_html = data.get('creditReportHTML', '')
        dispute_round = data.get('disputeRound', 1)
        analysis_mode = data.get('analysisMode', 'auto')
        
        print(f"📝 Client: {client_name}, Provider: {credit_provider}, Round: {dispute_round}")
        
        if not client_name or not credit_report_html:
            error_msg = 'Missing required fields'
            print(f"❌ {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # 🧹 Clean and analyze with section-based Stage 1
        try:
            print(f"🧹 Cleaning credit report in /api/analyze endpoint...")
            credit_report_text = clean_credit_report_html(credit_report_html)
            print(f"✅ Credit report cleaned successfully ({len(credit_report_text)} chars)")
        except Exception as e:
            error_msg = f"Error cleaning credit report: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # 🚀 Run Stage 1 on each section, merge results
        try:
            print(f"🚀 Starting Stage 1 analysis with sections...")
            section_analysis = run_stage1_for_all_sections(
                client_name=client_name,
                cmm_id=data.get('cmmContactId', ''),
                provider=credit_provider,
                credit_report_text=credit_report_text,
                analysis_mode='manual',
                dispute_round=dispute_round,
                previous_letters='',
                bureau_responses='',
                dispute_timeline=''
            )
            print(f"✅ Stage 1 analysis complete")
        except Exception as e:
            error_msg = f"Error in Stage 1 analysis: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'error': error_msg}), 500
        
        if not section_analysis.get('success'):
            error_msg = section_analysis.get('error', 'Analysis failed')
            print(f"❌ Analysis returned success=False: {error_msg}")
            return jsonify({'success': False, 'error': error_msg}), 500
        
        merged_litigation_data = section_analysis.get('litigation_data', {})
        
        # Create or get client
        client = db.query(Client).filter_by(name=client_name).first()
        if not client:
            client = Client(name=client_name, email=client_email)
            db.add(client)
            db.commit()
            db.refresh(client)
        
        # Save credit report
        credit_report_record = CreditReport(
            client_id=client.id,
            client_name=client_name,
            credit_provider=credit_provider,
            report_html=credit_report_html,
            report_date=datetime.now()
        )
        db.add(credit_report_record)
        db.commit()
        db.refresh(credit_report_record)
        
        # Save analysis with merged Stage 1 results from all sections
        analysis_record = Analysis(
            credit_report_id=credit_report_record.id,
            client_id=client.id,
            client_name=client_name,
            dispute_round=dispute_round,
            analysis_mode='manual',
            stage=1,  # This is Stage 1 analysis
            stage_1_analysis=str(merged_litigation_data),  # Store merged Stage 1 results
            cost=section_analysis.get('cost', 0),  # Cost is at top level of section_analysis
            tokens_used=section_analysis.get('tokens_used', 0),  # Tokens at top level
            cache_read=section_analysis.get('cache_read', False)
        )
        db.add(analysis_record)
        db.commit()
        db.refresh(analysis_record)
        
        # 🤖 AUTO-POPULATE LITIGATION DATABASE from merged section data
        if merged_litigation_data and merged_litigation_data.get('violations'):
            print(f"\n🎯 Merged litigation data found! Auto-populating database...")
            auto_populate_litigation_database(
                analysis_id=analysis_record.id,
                client_id=client.id,
                litigation_data=merged_litigation_data,
                db=db
            )
        else:
            print(f"\n⚠️  No violations found in merged analysis")
        
        # Extract and generate PDF letters
        letters_generated = []
        
        # Parse individual letters using START/END markers
        import re
        
        # Get combined analysis from section results
        combined_analysis_text = section_analysis.get('combined_analysis', '')
        
        # Find all individual letters
        letter_pattern = r"==.*?START OF DISPUTE LETTER: ([A-Za-z]+) - (.+?)==(.*?)==.*?END OF DISPUTE LETTER:"
        all_letters = re.findall(letter_pattern, combined_analysis_text, re.DOTALL | re.IGNORECASE)
        
        # Group letters by bureau
        bureau_letters = {'Equifax': [], 'Experian': [], 'TransUnion': []}
        for match in all_letters:
            bureau_name = match[0].strip().title()
            account_name = match[1].strip()
            letter_content = match[2].strip()
            
            if bureau_name in bureau_letters:
                bureau_letters[bureau_name].append({
                    'account': account_name,
                    'content': letter_content
                })
        
        # Generate one PDF per bureau combining all letters for that bureau
        for bureau, letters in bureau_letters.items():
            if not letters:
                continue
            
            # Combine all letters for this bureau
            combined_content = f"\n\n{'='*80}\n\n".join([
                f"ACCOUNT: {letter['account']}\n\n{letter['content']}" 
                for letter in letters
            ])
            
            # Generate PDF
            filename = f"{client_name.replace(' ', '_')}_{bureau}_Round{dispute_round}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join('static', 'generated_letters', filename)
            
            try:
                pdf_gen.generate_dispute_letter_pdf(
                    letter_content=combined_content,
                    client_name=client_name,
                    bureau=bureau,
                    round_number=dispute_round,
                    output_path=output_path
                )
                
                # Save letter record
                letter_record = DisputeLetter(
                    analysis_id=analysis_record.id,
                    client_id=client.id,
                    client_name=client_name,
                    bureau=bureau,
                    round_number=dispute_round,
                    letter_content=combined_content,
                    file_path=output_path
                )
                db.add(letter_record)
                db.commit()
                db.refresh(letter_record)
                
                letters_generated.append({
                    'letter_id': letter_record.id,
                    'bureau': bureau,
                    'round': dispute_round,
                    'filepath': output_path,
                    'letter_count': len(letters)
                })
                
                print(f"✅ Generated PDF for {bureau} with {len(letters)} letter(s)")
            except Exception as e:
                print(f"❌ Error generating PDF for {bureau}: {e}")
        
        return jsonify({
            'success': True,
            'client_name': client_name,
            'round': dispute_round,
            'cost': section_analysis.get('cost', 0),
            'tokens_used': section_analysis.get('tokens_used', 0),
            'analysis_id': analysis_record.id,
            'letters': letters_generated
        }), 200
        
    except Exception as e:
        print(f"Error in analyze_and_generate_letters: {e}")
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/debug/analysis/<int:analysis_id>')
def debug_analysis_content(analysis_id):
    """Debug endpoint to see what's actually in the database"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        return jsonify({
            'analysis_id': analysis.id,
            'stage': analysis.stage,
            'stage_1_analysis_length': len(analysis.stage_1_analysis or ''),
            'full_analysis_length': len(analysis.full_analysis or ''),
            'full_analysis_preview': (analysis.full_analysis or '')[:500],
            'full_analysis_exists': bool(analysis.full_analysis),
            'full_analysis_is_none': analysis.full_analysis is None,
            'full_analysis_is_empty': analysis.full_analysis == ''
        }), 200
    finally:
        db.close()


@app.route('/api/download/<int:letter_id>')
def download_letter(letter_id):
    """Download a generated PDF letter"""
    db = get_db()
    try:
        letter = db.query(DisputeLetter).filter_by(id=letter_id).first()
        
        if not letter:
            return jsonify({'error': 'Letter not found'}), 404
        
        file_path_str = str(letter.file_path)
        if not os.path.exists(file_path_str):
            return jsonify({'error': 'PDF file not found'}), 404
        
        return send_file(
            file_path_str,
            as_attachment=True,
            download_name=f"{letter.client_name}_{letter.bureau}_Round{letter.round_number}.pdf"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/download/analysis/<int:analysis_id>/full_report')
def download_full_report(analysis_id):
    """Download full litigation report PDF"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        # Get first letter from this analysis as template (all have same info)
        letter = db.query(DisputeLetter).filter_by(analysis_id=analysis_id).first()
        if not letter:
            return jsonify({'error': 'No letters generated yet. Click Accept Case first.'}), 404
        
        # Create comprehensive report combining violations, standing, damages + full Stage 2 analysis
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        
        # Start with header
        report_content = f"""
FCRA LITIGATION ANALYSIS REPORT
Client: {analysis.client_name}
Analysis ID: {analysis.id}
Date: {analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')}

CASE STRENGTH SCORE: {case_score.total_score if case_score else 'N/A'}/10

VIOLATIONS IDENTIFIED: {len(violations)}
"""
        for v in violations:
            report_content += f"\n* {v.fcra_section} - {v.violation_type} ({v.bureau})"
            report_content += f"\n  {v.description}"
            report_content += f"\n  Willful: {'Yes' if v.is_willful else 'No'}"
            report_content += f"\n  Statutory Damages: ${v.statutory_damages_min}-${v.statutory_damages_max}\n"
        
        report_content += f"\nSTANDING ANALYSIS:\n"
        if standing:
            report_content += f"* Concrete Harm: {'Yes' if standing.has_concrete_harm else 'No'}\n"
            report_content += f"* Dissemination: {'Yes' if standing.has_dissemination else 'No'}\n"
            report_content += f"* Causation: {'Yes' if standing.has_causation else 'No'}\n"
        
        report_content += f"\nDAMAGES CALCULATION:\n"
        if damages:
            report_content += f"* Actual Damages: ${damages.actual_damages_total}\n"
            report_content += f"* Statutory Damages: ${damages.statutory_damages_total}\n"
            report_content += f"* Punitive Damages: ${damages.punitive_damages_amount}\n"
            report_content += f"* Total Exposure: ${damages.total_exposure}\n"
            report_content += f"* Settlement Target (65%): ${damages.settlement_target}\n"
        
        # Add full Stage 2 comprehensive analysis if available
        if analysis.full_analysis:
            report_content += f"\n\n{'='*80}\nCOMPREHENSIVE LITIGATION ANALYSIS\n{'='*80}\n\n"
            report_content += analysis.full_analysis
        
        # Sanitize before PDF generation
        from pdf_generator import LetterPDFGenerator
        sanitizer = LetterPDFGenerator()
        report_content = sanitizer.sanitize_text_for_pdf(report_content)
        
        # Generate PDF using ReportLab (proven to work)
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.colors import HexColor
        from reportlab.lib.enums import TA_LEFT
        
        filename = f"{analysis.client_name.replace(' ', '_')}_Full_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = os.path.join('static', 'generated_letters', filename)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        doc = SimpleDocTemplate(output_path, pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom style with dark blue color
        custom_style = ParagraphStyle(
            'Custom',
            parent=styles['Normal'],
            fontSize=10,
            textColor=HexColor('#1a1a8e'),
            spaceAfter=8,
            fontName='Helvetica',
            leading=12
        )
        
        # Split content into lines and add to story (with chunking for large content)
        lines = report_content.split('\n')
        for i, line in enumerate(lines):
            if line.strip():
                # Chunk very long lines (>1000 chars) to avoid ReportLab errors
                if len(line) > 1000:
                    chunks = [line[j:j+1000] for j in range(0, len(line), 1000)]
                    for chunk in chunks:
                        try:
                            story.append(Paragraph(chunk, custom_style))
                        except Exception as e:
                            print(f"⚠️ Skipping line {i} (too complex for PDF): {str(e)[:100]}")
                else:
                    try:
                        story.append(Paragraph(line, custom_style))
                    except Exception as e:
                        print(f"⚠️ Skipping line {i}: {str(e)[:50]}")
            else:
                story.append(Spacer(1, 6))
        
        # Build PDF
        doc.build(story)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/download/analysis/<int:analysis_id>/round_<int:round_num>')
def download_round_letter(analysis_id, round_num):
    """Download dispute letter for specific round"""
    db = get_db()
    try:
        # Get first letter from this analysis/round
        letter = db.query(DisputeLetter).filter_by(
            analysis_id=analysis_id,
            round_number=round_num
        ).first()
        
        if not letter:
            return jsonify({'error': f'No letter found for Round {round_num}. Click Accept Case first.'}), 404
        
        file_path_str = str(letter.file_path)
        if not os.path.exists(file_path_str):
            return jsonify({'error': 'PDF file not found'}), 404
        
        return send_file(
            file_path_str,
            as_attachment=True,
            download_name=f"{letter.client_name}_Round{round_num}_Dispute_Letter.pdf"
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/approve/<int:analysis_id>', methods=['POST'])
def approve_analysis_stage_1(analysis_id):
    """
    Approve Stage 1 analysis and trigger Stage 2 (client documents generation).

    Behavior:
    - stage is NULL/0  → treat as Stage 1 (backwards compatible)
    - stage == 1      → run Stage 2, generate docs
    - stage == 2      → already approved, return existing letters (idempotent)
    - anything else   → return error
    """
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404

        # Backwards compatibility: if stage is None or 0, treat it as Stage 1
        if analysis.stage is None or analysis.stage == 0:
            analysis.stage = 1
            db.commit()

        # If Stage 2 already completed, return existing letters instead of error
        if analysis.stage == 2:
            letters = db.query(DisputeLetter).filter_by(analysis_id=analysis_id).all()
            letters_payload = [{
                'letter_id': l.id,
                'bureau': l.bureau,
                'round': l.round_number,
                'filepath': str(l.file_path)
            } for l in letters]

            return jsonify({
                'success': True,
                'analysis_id': analysis_id,
                'stage': 2,
                'message': 'Client documents already generated',
                'cost': analysis.cost or 0,
                'tokens': analysis.tokens_used or 0,
                'letters': letters_payload
            }), 200

        # Any other unexpected stage value
        if analysis.stage != 1:
            return jsonify({
                'success': False,
                'error': f'Analysis is not in Stage 1 (current stage: {analysis.stage})'
            }), 400

        print(f"\n🚀 STAGE 2: Generating client documents for analysis {analysis_id}...")

        # Get credit report for context
        credit_report = db.query(CreditReport).filter_by(id=analysis.credit_report_id).first()
        if not credit_report:
            return jsonify({'success': False, 'error': 'Credit report not found'}), 404

        # Run Stage 2 with Stage 1 results
        result = analyze_with_claude(
            client_name=analysis.client_name,
            cmm_id='',
            provider=credit_report.credit_provider,
            credit_report_html=credit_report.report_html,
            analysis_mode='auto',
            dispute_round=analysis.dispute_round,
            stage=2,  # STAGE 2: Generate client documents
            stage_1_results=analysis.stage_1_analysis  # Pass Stage 1 results
        )

        if not result.get('success'):
            return jsonify({
                'success': False,
                'error': result.get('error', 'Stage 2 generation failed')
            }), 500

        # CRITICAL FIX: Split UPDATE into two operations to bypass Neon SSL timeout on large TEXT
        # This solves "server closed the connection unexpectedly" on 90k+ character updates
        
        # STEP 1: Update metadata fields FIRST (no large text) - fast, reliable
        print(f"📋 STEP 1: Committing metadata (stage, cost, tokens)...")
        analysis.stage = 2
        analysis.approved_at = datetime.now()
        analysis.cost = (analysis.cost or 0) + result.get('cost', 0)
        analysis.tokens_used = (analysis.tokens_used or 0) + result.get('tokens_used', 0)
        
        retry_count = 0
        max_retries = 3
        while retry_count < max_retries:
            try:
                db.commit()
                print(f"✅ Metadata committed successfully (attempt {retry_count + 1})")
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    print(f"❌ Metadata commit failed: {str(e)[:50]}")
                    raise
                wait_time = 2 ** retry_count
                print(f"⚠️  Retrying metadata commit in {wait_time}s...")
                db.rollback()
                time.sleep(wait_time)
        
        # STEP 2: Update large text field SEPARATELY with streaming approach
        print(f"📋 STEP 2: Streaming full_analysis ({len(result.get('analysis', ''))} chars)...")
        analysis.full_analysis = result.get('analysis', '')
        flag_modified(analysis, 'full_analysis')
        
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            try:
                db.commit()
                print(f"✅ Full analysis committed successfully (attempt {retry_count + 1})")
                # Verify it saved
                db.refresh(analysis)
                print(f"✅ VERIFIED: full_analysis saved ({len(analysis.full_analysis or '')} chars)")
                break
            except Exception as e:
                retry_count += 1
                error_str = str(e)
                if retry_count >= max_retries:
                    print(f"❌ Full analysis commit FAILED after {max_retries} retries: {error_str[:80]}")
                    # Log the failure but continue - metadata is already saved
                    raise
                wait_time = 2 ** retry_count
                print(f"⚠️  Full analysis commit failed, retrying in {wait_time}s (SSL/connection issue, attempt {retry_count}/{max_retries})")
                db.rollback()
                time.sleep(wait_time)

        # Generate and save dispute letters from Stage 2 output
        print(f"📝 Extracting letters from Stage 2 output...")
        
        stage_2_text = result.get('analysis', '')
        bureau_letters = {}
        
        # Pattern 1: Scissor marker format (✂️ markers from FCRA v2.6 prompt)
        scissor_pattern = r'✂️.*?(?:DISPUTE LETTER|MOV REQUEST):\s*([A-Za-z\s]+).*?✂️\n(.*?)\n✂️.*?END OF'
        matches = re.findall(scissor_pattern, stage_2_text, re.DOTALL | re.IGNORECASE)
        
        if matches:
            print(f"   ✅ Found {len(matches)} letters using scissor markers")
        else:
            # Fallback: Original pattern (extract bureau and content only)
            print(f"   ⚠️  No scissor markers found, trying fallback pattern...")
            letter_pattern = r'\[([^:]+):\s*[^\]]*\]\s*\n(.*?)(?=\[|$)'
            fallback_matches = re.findall(letter_pattern, stage_2_text, re.DOTALL)
            
            if fallback_matches:
                matches = fallback_matches
                print(f"   ✅ Found {len(matches)} letters using fallback pattern")
            else:
                # Final fallback: Create comprehensive letter
                print(f"   ⚠️  No letters found. Creating fallback comprehensive letter...")
                matches = [('Comprehensive Analysis', stage_2_text[:10000])]
        
        print(f"📋 Total matches found: {len(matches)}")

        for bureau_name, letter_content in matches:
            bureau_name = bureau_name.strip().title()
            account_name = 'Multiple Accounts'  # Default since scissor markers don't include account
            letter_content = letter_content.strip()[:10000]  # Cap letter at 10k chars
            
            print(f"   Processing: bureau={bureau_name}, account={account_name}...")
            
            # Normalize bureau name to one of: Equifax, Experian, TransUnion, Comprehensive Analysis
            valid_bureaus = ['Equifax', 'Experian', 'TransUnion', 'Comprehensive Analysis', 'Comprehensiveanalysis']
            
            if bureau_name not in valid_bureaus:
                # Try to extract bureau name from content
                found = False
                for valid_bureau in ['Equifax', 'Experian', 'TransUnion']:
                    if valid_bureau.lower() in bureau_name.lower():
                        bureau_name = valid_bureau
                        found = True
                        break
                
                if not found:
                    # Default to Comprehensive Analysis for unparseable content
                    bureau_name = 'Comprehensive Analysis'
            
            # Final normalization
            if bureau_name == 'Comprehensiveanalysis':
                bureau_name = 'Comprehensive Analysis'
            
            if not bureau_name or len(bureau_name) == 0:
                print(f"   ⚠️  Skipping: empty bureau name")
                continue

            bureau_letters.setdefault(bureau_name, []).append({
                'account': account_name,
                'content': letter_content
            })
            print(f"   ✅ Added to {bureau_name}")

        letters_generated = []

        for bureau, letters in bureau_letters.items():
            if not letters:
                continue

            combined_content = f"\n\n{'='*80}\n\n".join(
                [f"ACCOUNT: {l['account']}\n\n{l['content']}" for l in letters]
            )

            filename = f"{analysis.client_name.replace(' ', '_')}_{bureau}_Round{analysis.dispute_round}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = os.path.join('static', 'generated_letters', filename)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            try:
                pdf_gen.generate_dispute_letter_pdf(
                    letter_content=combined_content,
                    client_name=analysis.client_name,
                    bureau=bureau,
                    round_number=analysis.dispute_round,
                    output_path=output_path
                )

                letter_record = DisputeLetter(
                    analysis_id=analysis_id,
                    client_id=analysis.client_id,
                    client_name=analysis.client_name,
                    bureau=bureau,
                    round_number=analysis.dispute_round,
                    letter_content=combined_content,
                    file_path=output_path
                )
                db.add(letter_record)
                db.commit()
                db.refresh(letter_record)

                letters_generated.append({
                    'letter_id': letter_record.id,
                    'bureau': bureau,
                    'round': analysis.dispute_round,
                    'filepath': output_path,
                    'letter_count': len(letters)
                })

                print(f"✅ Generated PDF for {bureau} with {len(letters)} letter(s)")
            except Exception as e:
                print(f"❌ Error generating PDF for {bureau}: {e}")

        print(f"✅ Stage 2 complete! Analysis {analysis_id} ready for delivery")

        return jsonify({
            'success': True,
            'analysis_id': analysis_id,
            'stage': 2,
            'message': 'Client documents generated successfully',
            'cost': result.get('cost', 0),
            'tokens': result.get('tokens_used', 0),
            'letters': letters_generated
        }), 200

    except Exception as e:
        print(f"❌ Error in approve_analysis_stage_1: {e}")
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/delivered', methods=['GET', 'POST'])
def delivered_status(analysis_id):
    """
    GET  -> return whether case is marked as delivered
    POST -> set/unset delivered flag (front-end toggle)
    """
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404

        global delivered_cases

        if request.method == 'GET':
            return jsonify({
                'success': True,
                'delivered': analysis_id in delivered_cases
            }), 200

        # POST
        data = request.get_json() or {}
        delivered = bool(data.get('delivered', False))

        if delivered:
            delivered_cases.add(analysis_id)
        else:
            delivered_cases.discard(analysis_id)

        return jsonify({
            'success': True,
            'delivered': analysis_id in delivered_cases
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/download_all')
def download_all_letters(analysis_id):
    """Create a ZIP with all generated PDFs for this analysis"""
    db = get_db()
    try:
        letters = db.query(DisputeLetter).filter_by(analysis_id=analysis_id).all()
        if not letters:
            return jsonify({'success': False, 'error': 'No letters found for this analysis'}), 404

        import io
        import zipfile

        # Create ZIP in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for l in letters:
                path = str(l.file_path)
                if not os.path.exists(path):
                    continue
                # Put each PDF into the zip with a clean filename
                arcname = f"{l.client_name}_{l.bureau}_Round{l.round_number}_{l.id}.pdf"
                zf.write(path, arcname=arcname)

        zip_buffer.seek(0)
        filename = f"FCRA_Letters_Analysis_{analysis_id}.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/analysis/<int:analysis_id>/review')
def review_litigation_analysis(analysis_id):
    """Litigation analysis review page"""
    return render_template('litigation_review.html', analysis_id=analysis_id)


@app.route('/api/analysis/<int:analysis_id>/data', methods=['GET'])
def get_analysis_data(analysis_id):
    """Get full analysis data for review page"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        
        return jsonify({
            'success': True,
            'analysis': {
                'id': analysis.id,
                'client_name': analysis.client_name,
                'dispute_round': analysis.dispute_round,
                'stage': analysis.stage,
                'cost': analysis.cost,
                'tokens_used': analysis.tokens_used,
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M:%S')
            },
            'violations': [{
                'id': v.id,
                'fcra_section': v.fcra_section,
                'violation_type': v.violation_type,
                'description': v.description,
                'bureau': v.bureau,
                'account_name': v.account_name,
                'is_willful': v.is_willful,
                'statutory_damages_min': v.statutory_damages_min,
                'statutory_damages_max': v.statutory_damages_max,
                'willfulness_notes': v.willfulness_notes
            } for v in violations],
            'standing': {
                'has_concrete_harm': standing.has_concrete_harm if standing else False,
                'concrete_harm_type': standing.concrete_harm_type if standing else '',
                'concrete_harm_details': standing.concrete_harm_details if standing else '',
                'has_dissemination': standing.has_dissemination if standing else False,
                'dissemination_details': standing.dissemination_details if standing else '',
                'has_causation': standing.has_causation if standing else False,
                'causation_details': standing.causation_details if standing else '',
                'denial_letters_count': standing.denial_letters_count if standing else 0,
                'adverse_action_notices_count': standing.adverse_action_notices_count if standing else 0
            } if standing else None,
            'damages': {
                'credit_denials_amount': damages.credit_denials_amount if damages else 0,
                'higher_interest_amount': damages.higher_interest_amount if damages else 0,
                'credit_monitoring_amount': damages.credit_monitoring_amount if damages else 0,
                'time_stress_amount': damages.time_stress_amount if damages else 0,
                'other_actual_amount': damages.other_actual_amount if damages else 0,
                'actual_damages_total': damages.actual_damages_total if damages else 0,
                'section_605b_count': damages.section_605b_count if damages else 0,
                'section_605b_amount': damages.section_605b_amount if damages else 0,
                'section_607b_count': damages.section_607b_count if damages else 0,
                'section_607b_amount': damages.section_607b_amount if damages else 0,
                'section_611_count': damages.section_611_count if damages else 0,
                'section_611_amount': damages.section_611_amount if damages else 0,
                'section_623_count': damages.section_623_count if damages else 0,
                'section_623_amount': damages.section_623_amount if damages else 0,
                'statutory_damages_total': damages.statutory_damages_total if damages else 0,
                'punitive_damages_amount': damages.punitive_damages_amount if damages else 0,
                'willfulness_multiplier': damages.willfulness_multiplier if damages else 0,
                'settlement_target': damages.settlement_target if damages else 0,
                'total_exposure': damages.total_exposure if damages else 0
            } if damages else None,
            'case_score': {
                'total_score': case_score.total_score if case_score else 0,
                'standing_score': case_score.standing_score if case_score else 0,
                'violation_quality_score': case_score.violation_quality_score if case_score else 0,
                'willfulness_score': case_score.willfulness_score if case_score else 0,
                'documentation_score': case_score.documentation_score if case_score else 0,
                'settlement_probability': case_score.settlement_probability if case_score else 0,
                'case_strength': case_score.case_strength if case_score else '',
                'recommendation': case_score.recommendation if case_score else ''
            } if case_score else None
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/admin/clients')
def view_all_clients():
    """View all clients and their analyses"""
    db = get_db()
    try:
        clients = db.query(Client).order_by(Client.created_at.desc()).all()
        
        clients_data = []
        for client in clients:
            analyses = db.query(Analysis).filter_by(client_id=client.id).order_by(Analysis.created_at.desc()).all()
            letters = db.query(DisputeLetter).filter_by(client_id=client.id).all()
            
            clients_data.append({
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'created_at': client.created_at.strftime('%Y-%m-%d %H:%M'),
                'total_analyses': len(analyses),
                'total_letters': len(letters),
                'latest_round': analyses[0].dispute_round if analyses else 0
            })
        
        return jsonify({
            'success': True,
            'clients': clients_data
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/violations', methods=['GET', 'POST'])
def manage_violations(analysis_id):
    """Get or add violations for an analysis"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        if request.method == 'POST':
            data = request.json
            violations_data = data.get('violations', [])
            
            for v_data in violations_data:
                willfulness_assessment = assess_willfulness(
                    v_data.get('description', ''),
                    v_data.get('violation_type', '')
                )
                
                violation = Violation(
                    analysis_id=analysis_id,
                    client_id=analysis.client_id,
                    bureau=v_data.get('bureau'),
                    account_name=v_data.get('account_name'),
                    fcra_section=v_data.get('fcra_section'),
                    violation_type=v_data.get('violation_type'),
                    description=v_data.get('description'),
                    statutory_damages_min=v_data.get('statutory_damages_min', 100),
                    statutory_damages_max=v_data.get('statutory_damages_max', 1000),
                    is_willful=willfulness_assessment['is_willful'],
                    willfulness_notes=', '.join(willfulness_assessment['indicators'])
                )
                db.add(violation)
            
            db.commit()
            return jsonify({'success': True, 'message': f'Added {len(violations_data)} violations'}), 200
        
        else:
            violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
            return jsonify({
                'success': True,
                'violations': [{
                    'id': v.id,
                    'bureau': v.bureau,
                    'account_name': v.account_name,
                    'fcra_section': v.fcra_section,
                    'violation_type': v.violation_type,
                    'description': v.description,
                    'statutory_damages_min': v.statutory_damages_min,
                    'statutory_damages_max': v.statutory_damages_max,
                    'is_willful': v.is_willful,
                    'willfulness_notes': v.willfulness_notes
                } for v in violations]
            }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/standing', methods=['GET', 'POST'])
def manage_standing(analysis_id):
    """Get or update standing verification for an analysis"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        if request.method == 'POST':
            data = request.json
            
            standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
            if not standing:
                standing = Standing(
                    analysis_id=analysis_id,
                    client_id=analysis.client_id
                )
                db.add(standing)
            
            standing.has_concrete_harm = data.get('has_concrete_harm', False)
            standing.concrete_harm_type = data.get('concrete_harm_type')
            standing.concrete_harm_details = data.get('concrete_harm_details')
            standing.has_dissemination = data.get('has_dissemination', False)
            standing.dissemination_details = data.get('dissemination_details')
            standing.has_causation = data.get('has_causation', False)
            standing.causation_details = data.get('causation_details')
            standing.denial_letters_count = data.get('denial_letters_count', 0)
            standing.adverse_action_notices_count = data.get('adverse_action_notices_count', 0)
            standing.standing_verified = data.get('standing_verified', False)
            standing.notes = data.get('notes')
            
            db.commit()
            return jsonify({'success': True, 'message': 'Standing updated'}), 200
        
        else:
            standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
            if not standing:
                return jsonify({'success': True, 'standing': None}), 200
            
            return jsonify({
                'success': True,
                'standing': {
                    'has_concrete_harm': standing.has_concrete_harm,
                    'concrete_harm_type': standing.concrete_harm_type,
                    'concrete_harm_details': standing.concrete_harm_details,
                    'has_dissemination': standing.has_dissemination,
                    'dissemination_details': standing.dissemination_details,
                    'has_causation': standing.has_causation,
                    'causation_details': standing.causation_details,
                    'denial_letters_count': standing.denial_letters_count,
                    'adverse_action_notices_count': standing.adverse_action_notices_count,
                    'standing_verified': standing.standing_verified,
                    'notes': standing.notes
                }
            }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/damages', methods=['GET', 'POST'])
def manage_damages(analysis_id):
    """Calculate and store damages for an analysis"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        if request.method == 'POST':
            data = request.json
            
            violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
            violations_data = [{
                'fcra_section': v.fcra_section,
                'is_willful': v.is_willful,
                'violation_type': v.violation_type
            } for v in violations]
            
            actual_damages_input = {
                'credit_denials': data.get('credit_denials_amount', 0),
                'higher_interest': data.get('higher_interest_amount', 0),
                'credit_monitoring': data.get('credit_monitoring_amount', 0),
                'time_stress': data.get('time_stress_amount', 0),
                'other': data.get('other_actual_amount', 0)
            }
            
            damages_calc = calculate_damages(violations_data, actual_damages_input)
            
            damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
            if not damages:
                damages = Damages(
                    analysis_id=analysis_id,
                    client_id=analysis.client_id
                )
                db.add(damages)
            
            damages.credit_denials_amount = damages_calc['actual']['credit_denials']
            damages.higher_interest_amount = damages_calc['actual']['higher_interest']
            damages.credit_monitoring_amount = damages_calc['actual']['credit_monitoring']
            damages.time_stress_amount = damages_calc['actual']['time_stress']
            damages.other_actual_amount = damages_calc['actual']['other']
            damages.actual_damages_total = damages_calc['actual']['total']
            
            damages.section_605b_count = damages_calc['statutory']['605b']['count']
            damages.section_605b_amount = damages_calc['statutory']['605b']['amount']
            damages.section_607b_count = damages_calc['statutory']['607b']['count']
            damages.section_607b_amount = damages_calc['statutory']['607b']['amount']
            damages.section_611_count = damages_calc['statutory']['611']['count']
            damages.section_611_amount = damages_calc['statutory']['611']['amount']
            damages.section_623_count = damages_calc['statutory']['623']['count']
            damages.section_623_amount = damages_calc['statutory']['623']['amount']
            damages.statutory_damages_total = damages_calc['statutory']['total']
            
            damages.willfulness_multiplier = damages_calc['punitive']['multiplier']
            damages.punitive_damages_amount = damages_calc['punitive']['amount']
            
            damages.estimated_hours = damages_calc['attorney_fees']['estimated_hours']
            damages.hourly_rate = damages_calc['attorney_fees']['hourly_rate']
            damages.attorney_fees_projection = damages_calc['attorney_fees']['total']
            
            damages.total_exposure = damages_calc['settlement']['total_exposure']
            damages.settlement_target = damages_calc['settlement']['target']
            damages.minimum_acceptable = damages_calc['settlement']['minimum']
            
            damages.notes = data.get('notes')
            
            db.commit()
            
            return jsonify({
                'success': True,
                'damages': damages_calc
            }), 200
        
        else:
            damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
            if not damages:
                return jsonify({'success': True, 'damages': None}), 200
            
            return jsonify({
                'success': True,
                'damages': {
                    'actual': {
                        'credit_denials': damages.credit_denials_amount,
                        'higher_interest': damages.higher_interest_amount,
                        'credit_monitoring': damages.credit_monitoring_amount,
                        'time_stress': damages.time_stress_amount,
                        'other': damages.other_actual_amount,
                        'total': damages.actual_damages_total
                    },
                    'statutory': {
                        '605b': {'count': damages.section_605b_count, 'amount': damages.section_605b_amount},
                        '607b': {'count': damages.section_607b_count, 'amount': damages.section_607b_amount},
                        '611': {'count': damages.section_611_count, 'amount': damages.section_611_amount},
                        '623': {'count': damages.section_623_count, 'amount': damages.section_623_amount},
                        'total': damages.statutory_damages_total
                    },
                    'punitive': {
                        'multiplier': damages.willfulness_multiplier,
                        'amount': damages.punitive_damages_amount
                    },
                    'attorney_fees': {
                        'estimated_hours': damages.estimated_hours,
                        'hourly_rate': damages.hourly_rate,
                        'total': damages.attorney_fees_projection
                    },
                    'settlement': {
                        'total_exposure': damages.total_exposure,
                        'target': damages.settlement_target,
                        'minimum': damages.minimum_acceptable
                    }
                }
            }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/score', methods=['GET', 'POST'])
def get_case_score(analysis_id):
    """Calculate and retrieve case strength score"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        
        standing_data = {
            'has_concrete_harm': standing.has_concrete_harm if standing else False,
            'has_dissemination': standing.has_dissemination if standing else False,
            'has_causation': standing.has_causation if standing else False
        }
        
        violations_data = [{
            'violation_type': v.violation_type,
            'is_willful': v.is_willful
        } for v in violations]
        
        damages_data = {}
        if damages:
            damages_data = {
                'total_exposure': damages.total_exposure,
                'statutory_total': damages.statutory_damages_total
            }
        
        documentation_complete = (standing.denial_letters_count > 0 if standing else False)
        
        score_result = calculate_case_score(
            standing_data,
            violations_data,
            damages_data,
            documentation_complete
        )
        
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        if not case_score:
            case_score = CaseScore(
                analysis_id=analysis_id,
                client_id=analysis.client_id
            )
            db.add(case_score)
        
        case_score.standing_score = score_result['standing']
        case_score.violation_quality_score = score_result['violation_quality']
        case_score.willfulness_score = score_result['willfulness']
        case_score.documentation_score = score_result['documentation']
        case_score.total_score = score_result['total']
        case_score.settlement_probability = score_result['settlement_probability']
        case_score.case_strength = score_result['case_strength']
        case_score.recommendation = score_result['recommendation']
        case_score.recommendation_notes = '\n'.join(score_result['notes'])
        
        db.commit()
        
        return jsonify({
            'success': True,
            'score': score_result
        }), 200
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/complete')
def get_complete_analysis(analysis_id):
    """Get complete litigation analysis including violations, damages, standing, and score"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        letters = db.query(DisputeLetter).filter_by(analysis_id=analysis_id).all()
        
        return jsonify({
            'success': True,
            'analysis': {
                'id': analysis.id,
                'client_name': analysis.client_name,
                'dispute_round': analysis.dispute_round,
                'analysis_mode': analysis.analysis_mode,
                'cost': analysis.cost,
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M')
            },
            'violations': [{
                'id': v.id,
                'bureau': v.bureau,
                'account_name': v.account_name,
                'fcra_section': v.fcra_section,
                'violation_type': v.violation_type,
                'description': v.description,
                'is_willful': v.is_willful,
                'statutory_damages_min': v.statutory_damages_min,
                'statutory_damages_max': v.statutory_damages_max
            } for v in violations],
            'standing': {
                'has_concrete_harm': standing.has_concrete_harm if standing else False,
                'concrete_harm_type': standing.concrete_harm_type if standing else None,
                'has_dissemination': standing.has_dissemination if standing else False,
                'has_causation': standing.has_causation if standing else False,
                'denial_letters_count': standing.denial_letters_count if standing else 0,
                'standing_verified': standing.standing_verified if standing else False
            } if standing else None,
            'damages': {
                'actual_total': damages.actual_damages_total if damages else 0,
                'statutory_total': damages.statutory_damages_total if damages else 0,
                'punitive_total': damages.punitive_damages_amount if damages else 0,
                'attorney_fees': damages.attorney_fees_projection if damages else 0,
                'total_exposure': damages.total_exposure if damages else 0,
                'settlement_target': damages.settlement_target if damages else 0,
                'minimum_acceptable': damages.minimum_acceptable if damages else 0
            } if damages else None,
            'case_score': {
                'total_score': case_score.total_score if case_score else 0,
                'standing_score': case_score.standing_score if case_score else 0,
                'violation_quality_score': case_score.violation_quality_score if case_score else 0,
                'willfulness_score': case_score.willfulness_score if case_score else 0,
                'documentation_score': case_score.documentation_score if case_score else 0,
                'settlement_probability': case_score.settlement_probability if case_score else 0,
                'case_strength': case_score.case_strength if case_score else 'Unknown',
                'recommendation': case_score.recommendation if case_score else 'Not scored'
            } if case_score else None,
            'letters': [{
                'id': l.id,
                'bureau': l.bureau,
                'round': l.round_number,
                'file_path': l.file_path
            } for l in letters]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# DASHBOARD & PLATFORM ROUTES
# ============================================================

def generate_case_number():
    """Generate unique case number like BA-2024-00001"""
    year = datetime.utcnow().year
    db = get_db()
    try:
        count = db.query(Case).filter(Case.case_number.like(f'BA-{year}-%')).count()
        return f"BA-{year}-{str(count + 1).zfill(5)}"
    finally:
        db.close()


def get_status_label(status):
    """Convert status code to readable label"""
    labels = {
        'intake': 'Intake',
        'stage1_pending': 'Analyzing...',
        'stage1_complete': 'Needs Review',
        'stage2_pending': 'Generating Docs...',
        'stage2_complete': 'Ready',
        'delivered': 'Delivered',
        'settled': 'Settled'
    }
    return labels.get(status, status)


@app.route('/dashboard')
@require_staff()
def dashboard():
    """Main admin dashboard"""
    db = get_db()
    try:
        from datetime import timedelta
        
        all_analyses = db.query(Analysis).all()
        all_damages = db.query(Damages).all()
        all_scores = db.query(CaseScore).all()
        
        total_exposure = sum(d.total_exposure or 0 for d in all_damages)
        active_cases = len(all_analyses)
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        new_this_week = db.query(Analysis).filter(Analysis.created_at >= one_week_ago).count()
        
        scores = [s.total_score for s in all_scores if s.total_score]
        avg_score = sum(scores) / len(scores) if scores else 0
        high_score_cases = len([s for s in scores if s >= 8])
        
        pending_review = db.query(Analysis).filter(Analysis.stage == 1, Analysis.approved_at == None).count()
        
        stats = {
            'total_exposure': total_exposure,
            'active_cases': active_cases,
            'new_this_week': new_this_week,
            'avg_score': avg_score,
            'high_score_cases': high_score_cases,
            'pending_review': pending_review
        }
        
        stage1_complete_count = db.query(Analysis).filter(Analysis.stage == 1, Analysis.approved_at == None).count()
        stage2_complete_count = db.query(Analysis).filter(Analysis.stage == 2).count()
        stage2_value = sum(
            (d.total_exposure or 0) 
            for d in db.query(Damages).join(Analysis).filter(Analysis.stage == 2).all()
        )
        
        pipeline = {
            'intake': 0,
            'stage1_pending': 0,
            'stage1_complete': stage1_complete_count,
            'stage2_pending': 0,
            'stage2_complete': stage2_complete_count,
            'stage2_value': stage2_value,
            'delivered': 0
        }
        
        recent_analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).limit(20).all()
        cases = []
        for analysis in recent_analyses:
            damages = db.query(Damages).filter_by(analysis_id=analysis.id).first()
            score = db.query(CaseScore).filter_by(analysis_id=analysis.id).first()
            client = db.query(Client).filter_by(id=analysis.client_id).first()
            
            if analysis.stage == 1 and not analysis.approved_at:
                status = 'stage1_complete'
            elif analysis.stage == 2:
                status = 'stage2_complete'
            else:
                status = 'intake'
            
            cases.append({
                'id': analysis.id,
                'analysis_id': analysis.id,
                'client_name': analysis.client_name,
                'client_email': client.email if client else None,
                'avatar_filename': client.avatar_filename if client else None,
                'status': status,
                'status_label': get_status_label(status),
                'score': score.total_score if score else None,
                'exposure': damages.total_exposure if damages else None
            })
        
        recent_activity = []
        for analysis in db.query(Analysis).order_by(Analysis.created_at.desc()).limit(5).all():
            if analysis.stage == 2:
                recent_activity.append({
                    'title': f'{analysis.client_name}',
                    'description': 'Documents ready for delivery',
                    'color': 'green',
                    'time': analysis.created_at.strftime('%I:%M %p')
                })
            elif analysis.stage == 1:
                recent_activity.append({
                    'title': f'{analysis.client_name}',
                    'description': 'Stage 1 analysis complete',
                    'color': 'blue',
                    'time': analysis.created_at.strftime('%I:%M %p')
                })
        
        return render_template('dashboard.html',
            stats=stats,
            pipeline=pipeline,
            cases=cases,
            recent_activity=recent_activity
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Dashboard error: {str(e)}", 500
    finally:
        db.close()


@app.route('/dashboard/analytics')
@require_staff()
def dashboard_analytics():
    """Analytics and Reporting Dashboard - Business Intelligence Metrics"""
    db = get_db()
    try:
        from datetime import timedelta
        from sqlalchemy import func, extract
        
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
        thirty_days_ago = now - timedelta(days=30)
        
        # ========== CLIENT STATS ==========
        total_clients = db.query(Client).count()
        new_this_month = db.query(Client).filter(Client.created_at >= start_of_month).count()
        
        # Client status breakdown
        active_clients = db.query(Client).filter(Client.status == 'active').count()
        paused_clients = db.query(Client).filter(Client.status == 'paused').count()
        complete_clients = db.query(Client).filter(Client.status == 'complete').count()
        signup_clients = db.query(Client).filter(Client.status == 'signup').count()
        
        client_stats = {
            'total': total_clients,
            'new_this_month': new_this_month,
            'active': active_clients,
            'paused': paused_clients,
            'complete': complete_clients,
            'signup': signup_clients
        }
        
        # ========== REVENUE STATS ==========
        # Total revenue collected (from signup_amount where payment_status = 'paid')
        total_revenue_cents = db.query(func.sum(Client.signup_amount)).filter(
            Client.payment_status == 'paid',
            Client.signup_amount.isnot(None)
        ).scalar() or 0
        total_revenue = total_revenue_cents / 100  # Convert cents to dollars
        
        # Revenue this month
        this_month_revenue_cents = db.query(func.sum(Client.signup_amount)).filter(
            Client.payment_status == 'paid',
            Client.signup_amount.isnot(None),
            Client.payment_received_at >= start_of_month
        ).scalar() or 0
        this_month_revenue = this_month_revenue_cents / 100
        
        # Revenue last month
        last_month_revenue_cents = db.query(func.sum(Client.signup_amount)).filter(
            Client.payment_status == 'paid',
            Client.signup_amount.isnot(None),
            Client.payment_received_at >= start_of_last_month,
            Client.payment_received_at < start_of_month
        ).scalar() or 0
        last_month_revenue = last_month_revenue_cents / 100
        
        # Revenue by tier
        tier_revenue = {}
        for tier in ['tier1', 'tier2', 'tier3', 'tier4', 'tier5', 'free']:
            tier_cents = db.query(func.sum(Client.signup_amount)).filter(
                Client.payment_status == 'paid',
                Client.signup_plan == tier,
                Client.signup_amount.isnot(None)
            ).scalar() or 0
            tier_revenue[tier] = tier_cents / 100
        
        revenue_stats = {
            'total': total_revenue,
            'this_month': this_month_revenue,
            'last_month': last_month_revenue,
            'by_tier': tier_revenue,
            'month_change': this_month_revenue - last_month_revenue
        }
        
        # ========== CASE STATS ==========
        total_analyses = db.query(Analysis).count()
        
        # Analyses by dispute round
        round_counts = {}
        for round_num in [1, 2, 3, 4]:
            count = db.query(Analysis).filter(Analysis.dispute_round == round_num).count()
            round_counts[f'round_{round_num}'] = count
        
        # Average case score
        all_scores = db.query(CaseScore.total_score).filter(CaseScore.total_score.isnot(None)).all()
        avg_case_score = sum(s[0] for s in all_scores) / len(all_scores) if all_scores else 0
        
        # Case score distribution
        high_score = len([s for s in all_scores if s[0] >= 8])
        medium_score = len([s for s in all_scores if 5 <= s[0] < 8])
        low_score = len([s for s in all_scores if s[0] < 5])
        
        case_stats = {
            'total_analyses': total_analyses,
            'by_round': round_counts,
            'avg_score': round(avg_case_score, 1),
            'high_score': high_score,
            'medium_score': medium_score,
            'low_score': low_score
        }
        
        # ========== DISPUTE PROGRESS ==========
        total_items = db.query(DisputeItem).count()
        items_deleted = db.query(DisputeItem).filter(DisputeItem.status == 'deleted').count()
        items_updated = db.query(DisputeItem).filter(DisputeItem.status == 'updated').count()
        items_verified = db.query(DisputeItem).filter(DisputeItem.status == 'verified').count()
        items_sent = db.query(DisputeItem).filter(DisputeItem.status == 'sent').count()
        items_in_progress = db.query(DisputeItem).filter(DisputeItem.status == 'in_progress').count()
        items_no_change = db.query(DisputeItem).filter(DisputeItem.status == 'no_change').count()
        
        # Success rate = deleted / (deleted + verified + no_change) if any completed
        completed_items = items_deleted + items_verified + items_no_change
        success_rate = (items_deleted / completed_items * 100) if completed_items > 0 else 0
        
        dispute_stats = {
            'total_items': total_items,
            'deleted': items_deleted,
            'updated': items_updated,
            'verified': items_verified,
            'sent': items_sent,
            'in_progress': items_in_progress,
            'no_change': items_no_change,
            'success_rate': round(success_rate, 1)
        }
        
        # ========== CRA RESPONSE STATS ==========
        total_responses = db.query(CRAResponse).count()
        response_types = {}
        for rtype in ['verified', 'deleted', 'updated', 'investigating', 'no_response', 'frivolous']:
            count = db.query(CRAResponse).filter(CRAResponse.response_type == rtype).count()
            response_types[rtype] = count
        
        cra_stats = {
            'total_responses': total_responses,
            'by_type': response_types
        }
        
        # ========== TIMELINE DATA (Last 30 days) ==========
        # Daily signups for the last 30 days
        signup_data = []
        revenue_data = []
        
        for i in range(30, -1, -1):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Count signups on this day
            day_signups = db.query(Client).filter(
                Client.created_at >= day_start,
                Client.created_at < day_end
            ).count()
            signup_data.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'label': day_start.strftime('%b %d'),
                'count': day_signups
            })
            
            # Revenue on this day
            day_revenue_cents = db.query(func.sum(Client.signup_amount)).filter(
                Client.payment_status == 'paid',
                Client.payment_received_at >= day_start,
                Client.payment_received_at < day_end,
                Client.signup_amount.isnot(None)
            ).scalar() or 0
            revenue_data.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'label': day_start.strftime('%b %d'),
                'amount': day_revenue_cents / 100
            })
        
        timeline_data = {
            'signups': signup_data,
            'revenue': revenue_data
        }
        
        return render_template('analytics.html',
            client_stats=client_stats,
            revenue_stats=revenue_stats,
            case_stats=case_stats,
            dispute_stats=dispute_stats,
            cra_stats=cra_stats,
            timeline_data=timeline_data
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Analytics error: {str(e)}", 500
    finally:
        db.close()


@app.route('/api/intake', methods=['POST'])
def api_intake():
    """New client intake endpoint"""
    db = get_db()
    try:
        data = request.json
        
        client_name = data.get('clientName', '').strip()
        client_email = data.get('clientEmail', '').strip()
        client_phone = data.get('clientPhone', '').strip()
        credit_provider = data.get('creditProvider', 'Unknown')
        dispute_round = int(data.get('disputeRound', 1))
        pricing_tier = data.get('pricingTier', 'tier1')
        credit_report_html = data.get('creditReportHTML', '')
        
        if not client_name:
            return jsonify({'success': False, 'error': 'Client name is required'}), 400
        if not credit_report_html:
            return jsonify({'success': False, 'error': 'Credit report is required'}), 400
        
        client = Client(
            name=client_name,
            email=client_email,
            phone=client_phone
        )
        db.add(client)
        db.flush()
        
        case_number = generate_case_number()
        portal_token = secrets.token_urlsafe(32)
        
        case = Case(
            client_id=client.id,
            case_number=case_number,
            status='stage1_pending',
            pricing_tier=pricing_tier,
            portal_token=portal_token,
            intake_at=datetime.utcnow()
        )
        db.add(case)
        db.flush()
        
        event = CaseEvent(
            case_id=case.id,
            event_type='intake',
            description=f'New client intake: {client_name}'
        )
        db.add(event)
        db.commit()
        
        print(f"📥 New client intake: {client_name} (Case #{case_number})")
        print(f"   Pricing tier: {pricing_tier}")
        print(f"   Portal token: {portal_token[:20]}...")
        
        from threading import Thread
        def run_analysis():
            try:
                import requests
                response = requests.post(
                    'http://localhost:5000/api/analyze',
                    json={
                        'clientName': client_name,
                        'clientEmail': client_email,
                        'creditProvider': credit_provider,
                        'creditReportHTML': credit_report_html,
                        'disputeRound': dispute_round,
                        'analysisMode': 'manual'
                    },
                    timeout=600
                )
                print(f"✅ Analysis started for {client_name}")
            except Exception as e:
                print(f"❌ Analysis error for {client_name}: {e}")
        
        thread = Thread(target=run_analysis)
        thread.start()
        
        return jsonify({
            'success': True,
            'case_number': case_number,
            'case_id': case.id,
            'client_id': client.id,
            'portal_token': portal_token,
            'message': f'Client added. Analysis starting...'
        })
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/dashboard/clients')
@require_staff(roles=['admin', 'paralegal', 'attorney'])
def dashboard_clients():
    """Client list page"""
    db = get_db()
    try:
        status_filter = request.args.get('status', 'all')
        
        query = db.query(Analysis).order_by(Analysis.created_at.desc())
        
        if status_filter == 'stage1_complete':
            query = query.filter(Analysis.stage == 1, Analysis.approved_at == None)
        elif status_filter == 'stage2_complete':
            query = query.filter(Analysis.stage == 2)
        
        analyses = query.all()
        
        cases = []
        for analysis in analyses:
            damages = db.query(Damages).filter_by(analysis_id=analysis.id).first()
            score = db.query(CaseScore).filter_by(analysis_id=analysis.id).first()
            client = db.query(Client).filter_by(id=analysis.client_id).first()
            
            if analysis.stage == 1 and not analysis.approved_at:
                status = 'stage1_complete'
            elif analysis.stage == 2:
                status = 'stage2_complete'
            else:
                status = 'intake'
            
            cases.append({
                'id': analysis.id,
                'analysis_id': analysis.id,
                'client_name': analysis.client_name,
                'client_email': client.email if client else None,
                'avatar_filename': client.avatar_filename if client else None,
                'status': status,
                'status_label': get_status_label(status),
                'score': score.total_score if score else None,
                'exposure': damages.total_exposure if damages else None,
                'violations': db.query(Violation).filter_by(analysis_id=analysis.id).count(),
                'created_at': analysis.created_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return render_template('clients.html', cases=cases, status_filter=status_filter)
    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        db.close()


@app.route('/dashboard/signups')
@require_staff(roles=['admin', 'paralegal'])
def dashboard_signups():
    """Admin view for signups and payment status"""
    db = get_db()
    try:
        from datetime import timedelta
        status_filter = request.args.get('status', 'all')
        
        # Get SignupDraft records (pending payments)
        drafts_query = db.query(SignupDraft).filter(SignupDraft.status == 'pending').order_by(SignupDraft.created_at.desc())
        drafts = []
        for draft in drafts_query.all():
            form_data = draft.form_data or {}
            drafts.append({
                'id': draft.id,
                'draft_uuid': draft.draft_uuid,
                'client_name': form_data.get('firstName', '') + ' ' + form_data.get('lastName', ''),
                'client_email': form_data.get('email', ''),
                'plan_tier': draft.plan_tier or 'unknown',
                'plan_amount': draft.plan_amount or 0,
                'status': draft.status,
                'created_at': draft.created_at.strftime('%Y-%m-%d %H:%M') if draft.created_at else '',
                'expires_at': draft.expires_at.strftime('%Y-%m-%d %H:%M') if draft.expires_at else ''
            })
        
        # Get Client records with payment info
        clients_query = db.query(Client).filter(Client.signup_plan != None).order_by(Client.created_at.desc())
        
        if status_filter == 'paid':
            clients_query = clients_query.filter(Client.payment_status == 'paid')
        elif status_filter == 'pending':
            clients_query = clients_query.filter(Client.payment_status == 'pending')
        elif status_filter == 'failed':
            clients_query = clients_query.filter(Client.payment_status == 'failed')
        elif status_filter == 'pending_manual':
            clients_query = clients_query.filter(Client.payment_pending == True)
        elif status_filter == 'free':
            clients_query = clients_query.filter(Client.signup_plan == 'free')
        
        clients = []
        for client in clients_query.limit(100).all():
            clients.append({
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'signup_plan': client.signup_plan,
                'signup_amount': client.signup_amount or 0,
                'payment_status': client.payment_status or 'pending',
                'payment_method': getattr(client, 'payment_method', None) or 'pending',
                'payment_pending': getattr(client, 'payment_pending', False) or False,
                'portal_token': client.portal_token,
                'created_at': client.created_at.strftime('%Y-%m-%d %H:%M') if client.created_at else '',
                'contacted': 'contacted' in (client.admin_notes or '').lower()
            })
        
        # Calculate stats
        from sqlalchemy import func
        one_week_ago = datetime.utcnow() - timedelta(days=7)
        
        total_revenue = db.query(func.sum(Client.signup_amount)).filter(
            Client.payment_status == 'paid',
            Client.signup_amount != None
        ).scalar() or 0
        
        pending_count = db.query(SignupDraft).filter(SignupDraft.status == 'pending').count()
        pending_count += db.query(Client).filter(Client.payment_status == 'pending', Client.signup_plan != None).count()
        
        paid_count = db.query(Client).filter(Client.payment_status == 'paid').count()
        paid_this_week = db.query(Client).filter(
            Client.payment_status == 'paid',
            Client.payment_received_at >= one_week_ago
        ).count()
        
        failed_count = db.query(Client).filter(Client.payment_status == 'failed').count()
        
        stats = {
            'total_revenue': total_revenue,
            'pending_count': pending_count,
            'paid_count': paid_count,
            'paid_this_week': paid_this_week,
            'failed_count': failed_count
        }
        
        return render_template('signups.html',
            drafts=drafts,
            clients=clients,
            stats=stats,
            status_filter=status_filter
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500
    finally:
        db.close()


@app.route('/api/signups/mark-contacted', methods=['POST'])
def api_mark_contacted():
    """Mark a signup as contacted"""
    db = get_db()
    try:
        data = request.json
        record_type = data.get('type')
        record_id = data.get('id')
        
        if not record_type or not record_id:
            return jsonify({'success': False, 'error': 'Missing type or id'}), 400
        
        if record_type == 'client':
            client = db.query(Client).filter_by(id=record_id).first()
            if not client:
                return jsonify({'success': False, 'error': 'Client not found'}), 404
            
            # Add contacted note
            current_notes = client.admin_notes or ''
            if 'contacted' not in current_notes.lower():
                contacted_note = f"[CONTACTED {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}]"
                client.admin_notes = contacted_note + ('\n' + current_notes if current_notes else '')
                db.commit()
            
            return jsonify({'success': True, 'message': 'Client marked as contacted'})
        
        elif record_type == 'draft':
            draft = db.query(SignupDraft).filter_by(id=record_id).first()
            if not draft:
                return jsonify({'success': False, 'error': 'Draft not found'}), 404
            
            # Update form_data to include contacted flag
            form_data = draft.form_data or {}
            form_data['contacted'] = True
            form_data['contacted_at'] = datetime.utcnow().isoformat()
            draft.form_data = form_data
            flag_modified(draft, 'form_data')
            db.commit()
            
            return jsonify({'success': True, 'message': 'Draft marked as contacted'})
        
        else:
            return jsonify({'success': False, 'error': 'Invalid record type'}), 400
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/dashboard/settings')
@require_staff(roles=['admin'])
def dashboard_settings():
    """Admin settings page for signup configuration"""
    db = get_db()
    try:
        import json
        
        settings = {}
        all_settings = db.query(SignupSettings).all()
        for s in all_settings:
            try:
                settings[s.setting_key] = json.loads(s.setting_value) if s.setting_value else None
            except:
                settings[s.setting_key] = s.setting_value
        
        defaults = {
            'field_name': 'required',
            'field_email': 'required',
            'field_phone': 'required',
            'field_address': 'optional',
            'field_dob': 'optional',
            'field_ssn': 'deferred',
            'field_credit_login': 'deferred',
            'field_referral': 'optional',
            'tier_free_enabled': True,
            'tier_free_desc': 'Basic Analysis - Free',
            'tier1_enabled': True,
            'tier1_price': 300,
            'tier1_desc': 'Initial credit analysis',
            'tier2_enabled': True,
            'tier2_price': 600,
            'tier2_desc': 'Two rounds of disputes',
            'tier3_enabled': True,
            'tier3_price': 900,
            'tier3_desc': 'Three rounds comprehensive',
            'tier4_enabled': True,
            'tier4_price': 1200,
            'tier4_desc': 'Litigation preparation',
            'tier5_enabled': True,
            'tier5_price': 1500,
            'tier5_desc': 'Complete package',
            'allow_pay_later': True,
            'payment_stripe_enabled': True,
            'payment_paypal_enabled': False,
            'payment_cashapp_enabled': False,
            'payment_venmo_enabled': False,
            'payment_zelle_enabled': False,
            'payment_cashapp': '',
            'payment_venmo': '',
            'payment_zelle': '',
            'payment_paypal': ''
        }
        
        for key, value in defaults.items():
            if key not in settings:
                settings[key] = value
        
        return render_template('settings.html', settings=settings)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500
    finally:
        db.close()


@app.route('/api/settings/save', methods=['POST'])
def api_save_settings():
    """Save signup settings"""
    db = get_db()
    try:
        import json
        data = request.json
        
        for key, value in data.items():
            setting = db.query(SignupSettings).filter_by(setting_key=key).first()
            if setting:
                setting.setting_value = json.dumps(value) if not isinstance(value, str) else value
                setting.updated_at = datetime.utcnow()
            else:
                setting = SignupSettings(
                    setting_key=key,
                    setting_value=json.dumps(value) if not isinstance(value, str) else value
                )
                db.add(setting)
        
        db.commit()
        return jsonify({'success': True, 'message': 'Settings saved'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settings/get')
def api_get_settings():
    """Get all signup settings as JSON"""
    db = get_db()
    try:
        import json
        settings = {}
        all_settings = db.query(SignupSettings).all()
        for s in all_settings:
            try:
                settings[s.setting_key] = json.loads(s.setting_value) if s.setting_value else None
            except:
                settings[s.setting_key] = s.setting_value
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/dashboard/settings/sms')
@require_staff(roles=['admin'])
def dashboard_sms_settings():
    """SMS Settings page for configuring Twilio SMS automation"""
    db = get_db()
    try:
        from services.sms_service import is_twilio_configured, get_twilio_phone_number
        from services.sms_automation import get_sms_settings
        from datetime import timedelta
        
        twilio_configured = False
        twilio_phone = None
        try:
            twilio_configured = is_twilio_configured()
            if twilio_configured:
                twilio_phone = get_twilio_phone_number()
        except Exception as e:
            print(f"Twilio check failed: {e}")
        
        settings = get_sms_settings(db)
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        logs = db.query(SMSLog).filter(
            SMSLog.sent_at >= thirty_days_ago
        ).order_by(SMSLog.sent_at.desc()).limit(50).all()
        
        total = db.query(SMSLog).filter(SMSLog.sent_at >= thirty_days_ago).count()
        sent = db.query(SMSLog).filter(
            SMSLog.sent_at >= thirty_days_ago,
            SMSLog.status == 'sent'
        ).count()
        failed = db.query(SMSLog).filter(
            SMSLog.sent_at >= thirty_days_ago,
            SMSLog.status == 'failed'
        ).count()
        
        template_types = db.query(SMSLog.template_type).filter(
            SMSLog.sent_at >= thirty_days_ago
        ).distinct().count()
        
        stats = {
            'total': total,
            'sent': sent,
            'failed': failed,
            'templates_used': template_types
        }
        
        return render_template('sms_settings.html',
            twilio_configured=twilio_configured,
            twilio_phone=twilio_phone,
            settings=settings,
            logs=logs,
            stats=stats
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500
    finally:
        db.close()


@app.route('/api/sms/settings', methods=['POST'])
def api_save_sms_settings():
    """Save SMS automation settings"""
    db = get_db()
    try:
        data = request.json
        
        setting_keys = [
            'sms_enabled', 'welcome_sms_enabled', 'document_reminder_enabled',
            'case_update_enabled', 'dispute_sent_enabled', 'cra_response_enabled',
            'payment_reminder_enabled', 'reminder_delay_hours'
        ]
        
        for key in setting_keys:
            if key in data:
                value = data[key]
                if isinstance(value, bool):
                    value = 'true' if value else 'false'
                else:
                    value = str(value)
                
                setting = db.query(SignupSettings).filter_by(setting_key=f'sms_{key}').first()
                if setting:
                    setting.setting_value = value
                    setting.updated_at = datetime.utcnow()
                else:
                    setting = SignupSettings(
                        setting_key=f'sms_{key}',
                        setting_value=value
                    )
                    db.add(setting)
        
        db.commit()
        return jsonify({'success': True, 'message': 'SMS settings saved'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/sms/test', methods=['POST'])
def api_send_test_sms():
    """Send a test SMS to verify Twilio configuration"""
    try:
        from services.sms_automation import send_test_sms
        
        data = request.json
        phone = data.get('phone')
        message = data.get('message')
        
        if not phone:
            return jsonify({'success': False, 'error': 'Phone number required'}), 400
        
        result = send_test_sms(phone, message)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/sms/send', methods=['POST'])
def api_send_sms():
    """Send an SMS to a specific client"""
    db = get_db()
    try:
        from services.sms_automation import send_custom_sms
        
        data = request.json
        client_id = data.get('client_id')
        message = data.get('message')
        
        if not client_id or not message:
            return jsonify({'success': False, 'error': 'client_id and message required'}), 400
        
        result = send_custom_sms(db, client_id, message)
        
        return jsonify(result)
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/sms/logs')
def api_get_sms_logs():
    """Get SMS logs with optional filters"""
    db = get_db()
    try:
        from datetime import timedelta
        
        days = request.args.get('days', 30, type=int)
        client_id = request.args.get('client_id', type=int)
        status = request.args.get('status')
        limit = request.args.get('limit', 100, type=int)
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = db.query(SMSLog).filter(SMSLog.sent_at >= cutoff)
        
        if client_id:
            query = query.filter(SMSLog.client_id == client_id)
        if status:
            query = query.filter(SMSLog.status == status)
        
        logs = query.order_by(SMSLog.sent_at.desc()).limit(limit).all()
        
        logs_data = []
        for log in logs:
            logs_data.append({
                'id': log.id,
                'client_id': log.client_id,
                'phone_number': log.phone_number,
                'message': log.message[:100] + '...' if len(log.message or '') > 100 else log.message,
                'template_type': log.template_type,
                'status': log.status,
                'twilio_sid': log.twilio_sid,
                'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                'error_message': log.error_message
            })
        
        return jsonify({'success': True, 'logs': logs_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# EMAIL AUTOMATION ROUTES
# ============================================================

@app.route('/dashboard/settings/email')
@require_staff(roles=['admin'])
def dashboard_email_settings():
    """Email Settings page for configuring SendGrid email automation"""
    db = get_db()
    try:
        from services.email_service import is_sendgrid_configured
        from services.email_automation import get_email_settings
        from datetime import timedelta
        
        sendgrid_configured = False
        try:
            sendgrid_configured = is_sendgrid_configured()
        except Exception as e:
            print(f"SendGrid check failed: {e}")
        
        settings = get_email_settings(db)
        
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        logs = db.query(EmailLog).filter(
            EmailLog.sent_at >= thirty_days_ago
        ).order_by(EmailLog.sent_at.desc()).limit(50).all()
        
        total = db.query(EmailLog).filter(EmailLog.sent_at >= thirty_days_ago).count()
        sent = db.query(EmailLog).filter(
            EmailLog.sent_at >= thirty_days_ago,
            EmailLog.status == 'sent'
        ).count()
        failed = db.query(EmailLog).filter(
            EmailLog.sent_at >= thirty_days_ago,
            EmailLog.status == 'failed'
        ).count()
        
        template_types = db.query(EmailLog.template_type).filter(
            EmailLog.sent_at >= thirty_days_ago
        ).distinct().count()
        
        stats = {
            'total': total,
            'sent': sent,
            'failed': failed,
            'templates_used': template_types
        }
        
        return render_template('email_settings.html',
            sendgrid_configured=sendgrid_configured,
            settings=settings,
            logs=logs,
            stats=stats
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500
    finally:
        db.close()


@app.route('/api/email/settings', methods=['POST'])
def api_save_email_settings():
    """Save email automation settings"""
    db = get_db()
    try:
        data = request.json
        
        setting_keys = [
            'email_enabled', 'welcome_email_enabled', 'document_reminder_enabled',
            'case_update_enabled', 'dispute_sent_enabled', 'cra_response_enabled',
            'payment_reminder_enabled', 'analysis_ready_enabled', 'letters_ready_enabled'
        ]
        
        for key in setting_keys:
            if key in data:
                value = data[key]
                if isinstance(value, bool):
                    value = 'true' if value else 'false'
                else:
                    value = str(value)
                
                setting = db.query(SignupSettings).filter_by(setting_key=f'email_{key}').first()
                if setting:
                    setting.setting_value = value
                    setting.updated_at = datetime.utcnow()
                else:
                    setting = SignupSettings(
                        setting_key=f'email_{key}',
                        setting_value=value
                    )
                    db.add(setting)
        
        db.commit()
        return jsonify({'success': True, 'message': 'Email settings saved'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/email/test', methods=['POST'])
def api_send_test_email():
    """Send a test email to verify SendGrid configuration"""
    try:
        from services.email_automation import send_test_email
        
        data = request.json
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'error': 'Email address required'}), 400
        
        result = send_test_email(email)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/email/send', methods=['POST'])
def api_send_email():
    """Send an email to a specific client"""
    db = get_db()
    try:
        from services.email_automation import send_custom_email
        
        data = request.json
        client_id = data.get('client_id')
        subject = data.get('subject')
        message = data.get('message')
        
        if not client_id or not subject or not message:
            return jsonify({'success': False, 'error': 'client_id, subject, and message required'}), 400
        
        result = send_custom_email(db, client_id, subject, message)
        
        return jsonify(result)
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/email/setup')
def api_email_setup():
    """Redirect to SendGrid integration setup"""
    return redirect('/dashboard/settings/email')


VALID_TEMPLATE_TYPES = [
    'welcome', 'document_reminder', 'case_update', 'dispute_sent',
    'cra_response', 'payment_reminder', 'analysis_ready', 'letters_ready'
]


def validate_template_type(template_type):
    """Validate that template_type is one of the allowed types"""
    return template_type in VALID_TEMPLATE_TYPES


def validate_email_format(email):
    """Basic email format validation"""
    import re
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


@app.route('/api/email-templates', methods=['GET'])
def api_get_email_templates():
    """Get all email templates - lists all template types with custom status"""
    db = get_db()
    try:
        template_types = VALID_TEMPLATE_TYPES
        
        custom_templates = db.query(EmailTemplate).all()
        custom_map = {t.template_type: t for t in custom_templates}
        
        templates = []
        for tt in template_types:
            if tt in custom_map:
                t = custom_map[tt]
                templates.append({
                    'template_type': tt,
                    'subject': t.subject,
                    'is_custom': t.is_custom,
                    'has_custom': True,
                    'updated_at': t.updated_at.isoformat() if t.updated_at else None
                })
            else:
                templates.append({
                    'template_type': tt,
                    'subject': get_default_subject(tt),
                    'is_custom': False,
                    'has_custom': False,
                    'updated_at': None
                })
        
        return jsonify({'success': True, 'templates': templates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/email-templates/<template_type>', methods=['GET'])
def api_get_email_template(template_type):
    """Get a specific email template by type"""
    if not validate_template_type(template_type):
        return jsonify({'success': False, 'error': f'Invalid template type: {template_type}'}), 400
    
    db = get_db()
    try:
        template = db.query(EmailTemplate).filter_by(template_type=template_type).first()
        
        if template:
            return jsonify({
                'success': True,
                'template': {
                    'template_type': template.template_type,
                    'subject': template.subject,
                    'html_content': template.html_content,
                    'design_json': template.design_json,
                    'is_custom': template.is_custom,
                    'updated_at': template.updated_at.isoformat() if template.updated_at else None
                }
            })
        else:
            return jsonify({
                'success': True,
                'template': {
                    'template_type': template_type,
                    'subject': get_default_subject(template_type),
                    'html_content': None,
                    'design_json': None,
                    'is_custom': False,
                    'updated_at': None
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/email-templates/<template_type>', methods=['POST'])
def api_save_email_template(template_type):
    """Save or update an email template"""
    if not validate_template_type(template_type):
        return jsonify({'success': False, 'error': f'Invalid template type: {template_type}'}), 400
    
    db = get_db()
    try:
        data = request.json
        subject = data.get('subject')
        html_content = data.get('html_content')
        design_json = data.get('design_json')
        
        if not subject or not subject.strip():
            return jsonify({'success': False, 'error': 'Subject is required'}), 400
        
        template = db.query(EmailTemplate).filter_by(template_type=template_type).first()
        
        if template:
            template.subject = subject
            template.html_content = html_content
            template.design_json = design_json
            template.is_custom = True
            template.updated_at = datetime.utcnow()
        else:
            template = EmailTemplate(
                template_type=template_type,
                subject=subject,
                html_content=html_content,
                design_json=design_json,
                is_custom=True
            )
            db.add(template)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'Template "{template_type}" saved successfully',
            'template': {
                'template_type': template.template_type,
                'subject': template.subject,
                'is_custom': template.is_custom
            }
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/email-templates/<template_type>/reset', methods=['POST'])
def api_reset_email_template(template_type):
    """Reset a template to default (delete custom version)"""
    if not validate_template_type(template_type):
        return jsonify({'success': False, 'error': f'Invalid template type: {template_type}'}), 400
    
    db = get_db()
    try:
        template = db.query(EmailTemplate).filter_by(template_type=template_type).first()
        
        if template:
            db.delete(template)
            db.commit()
            return jsonify({
                'success': True,
                'message': f'Template "{template_type}" reset to default'
            })
        else:
            return jsonify({
                'success': True,
                'message': f'Template "{template_type}" was already using default'
            })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/email-templates/<template_type>/preview', methods=['POST'])
def api_preview_email_template(template_type):
    """Send a preview email with the template"""
    if not validate_template_type(template_type):
        return jsonify({'success': False, 'error': f'Invalid template type: {template_type}'}), 400
    
    db = get_db()
    try:
        from services.email_service import send_email, is_sendgrid_configured
        from services import email_templates as default_templates
        
        if not is_sendgrid_configured():
            return jsonify({'success': False, 'error': 'SendGrid not configured. Please connect SendGrid first.'}), 400
        
        data = request.json
        preview_email = data.get('email', '').strip()
        html_content = data.get('html_content')
        subject = data.get('subject', f'Preview: {template_type}')
        
        if not preview_email:
            return jsonify({'success': False, 'error': 'Preview email address required'}), 400
        
        if not validate_email_format(preview_email):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        if html_content:
            test_html = apply_merge_tags(html_content, {
                'client_name': 'Test Client',
                'client_email': preview_email,
                'portal_link': 'https://example.com/portal/test123',
                'case_status': 'Active',
                'missing_docs': 'Driver\'s License, Utility Bill',
                'company_name': 'Brightpath Ascend Group',
                'support_email': 'support@brightpathascend.com'
            })
        else:
            test_html = default_templates.get_base_template(
                '<h2>Template Preview</h2><p>This is a preview of the default template.</p>',
                subject
            )
        
        result = send_email(preview_email, f'[Preview] {subject}', test_html)
        
        if result['success']:
            return jsonify({'success': True, 'message': 'Preview email sent!'})
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Failed to send')}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


def get_default_subject(template_type):
    """Get the default subject line for a template type"""
    subjects = {
        'welcome': 'Welcome to Brightpath Ascend Group!',
        'document_reminder': 'Action Required: Documents Needed',
        'case_update': 'Case Update',
        'dispute_sent': 'Dispute Letter Sent',
        'cra_response': 'Response Received',
        'payment_reminder': 'Payment Reminder',
        'analysis_ready': 'Your Credit Analysis is Ready!',
        'letters_ready': 'Your Dispute Letters Are Ready!'
    }
    return subjects.get(template_type, f'{template_type.replace("_", " ").title()} Notification')


CRA_ADDRESSES = {
    # Main 3 CRAs - Dispute Addresses
    'equifax_name': 'Equifax Information Services LLC',
    'equifax_address': 'P.O. Box 740256, Atlanta, GA 30374-0256',
    'equifax_phone': '1-800-685-1111',
    'experian_name': 'Experian',
    'experian_address': 'P.O. Box 4500, Allen, TX 75013',
    'experian_phone': '1-888-397-3742',
    'transunion_name': 'TransUnion LLC',
    'transunion_address': 'P.O. Box 2000, Chester, PA 19016-2000',
    'transunion_phone': '1-800-916-8800',
    
    # Main 3 CRAs - Freeze Addresses
    'equifax_freeze_address': 'P.O. Box 105788, Atlanta, GA 30348-5788',
    'equifax_freeze_phone': '1-800-349-9960',
    'experian_freeze_address': 'P.O. Box 9554, Allen, TX 75013',
    'experian_freeze_phone': '1-888-397-3742',
    'transunion_freeze_address': 'P.O. Box 160, Woodlyn, PA 19094',
    'transunion_freeze_phone': '1-888-909-8872',
    
    # Secondary Bureaus (9 bureaus)
    'innovis_name': 'Innovis',
    'innovis_address': 'P.O. Box 1358, Columbus, OH 43216-1358',
    'innovis_phone': '1-800-540-2505',
    'innovis_freeze_address': 'P.O. Box 1358, Columbus, OH 43216-1358',
    
    'chexsystems_name': 'ChexSystems',
    'chexsystems_address': 'Attn: Consumer Relations, 7805 Hudson Road, Suite 100, Woodbury, MN 55125',
    'chexsystems_phone': '1-800-428-9623',
    'chexsystems_freeze_address': 'P.O. Box 583399, Minneapolis, MN 55458',
    
    'clarity_name': 'Clarity Services Inc',
    'clarity_address': 'P.O. Box 5717, Clearwater, FL 33758',
    'clarity_phone': '1-866-390-3118',
    
    'lexisnexis_name': 'LexisNexis',
    'lexisnexis_address': 'P.O. Box 105108, Atlanta, GA 30348-5108',
    'lexisnexis_phone': '1-888-497-0011',
    
    'corelogic_name': 'CoreLogic Teletrack',
    'corelogic_address': 'P.O. Box 509124, San Diego, CA 92150',
    'corelogic_phone': '1-877-309-5226',
    
    'factortrust_name': 'Factor Trust Inc',
    'factortrust_address': 'P.O. Box 327, Alpharetta, GA 30009',
    'factortrust_phone': '1-484-671-5880',
    
    'microbilt_name': 'MicroBilt / PRBC',
    'microbilt_address': '1640 Airport Road, Suite 115, Kennesaw, GA 30144',
    'microbilt_phone': '1-866-536-3569',
    
    'lexisnexis_risk_name': 'LexisNexis Risk Solutions',
    'lexisnexis_risk_address': 'P.O. Box 105108, Atlanta, GA 30348',
    'lexisnexis_risk_phone': '1-800-456-1244',
    
    'datax_name': 'DataX Ltd',
    'datax_address': 'P.O. Box 105168, Atlanta, GA 30348',
    'datax_phone': '1-800-295-4790',
}


def apply_merge_tags(html_content, values):
    """Replace merge tags in HTML content with actual values"""
    if not html_content:
        return html_content
    
    all_values = {**CRA_ADDRESSES, **values}
    
    result = html_content
    for tag, value in all_values.items():
        result = result.replace('{{' + tag + '}}', str(value) if value else '')
    return result


@app.route('/api/signups/confirm-payment', methods=['POST'])
def api_confirm_payment():
    """Confirm manual payment for a client"""
    db = get_db()
    try:
        data = request.json
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'Missing client_id'}), 400
        
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        client.payment_status = 'paid'
        client.payment_pending = False
        client.payment_received_at = datetime.utcnow()
        
        current_notes = client.admin_notes or ''
        payment_note = f"[PAYMENT CONFIRMED {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} via {client.payment_method or 'manual'}]"
        client.admin_notes = payment_note + ('\n' + current_notes if current_notes else '')
        
        db.commit()
        return jsonify({'success': True, 'message': 'Payment confirmed'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/dashboard/case/<int:case_id>')
@require_staff(roles=['admin', 'paralegal', 'attorney', 'viewer'])
def dashboard_case_detail(case_id):
    """Single case detail page"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=case_id).first()
        if not analysis:
            return "Case not found", 404
        
        violations = db.query(Violation).filter_by(analysis_id=case_id).all()
        standing = db.query(Standing).filter_by(analysis_id=case_id).first()
        damages = db.query(Damages).filter_by(analysis_id=case_id).first()
        score = db.query(CaseScore).filter_by(analysis_id=case_id).first()
        letters = db.query(DisputeLetter).filter_by(analysis_id=case_id).all()
        client = db.query(Client).filter_by(id=analysis.client_id).first()
        
        return render_template('case_detail.html',
            analysis=analysis,
            client=client,
            violations=violations,
            standing=standing,
            damages=damages,
            score=score,
            letters=letters
        )
    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        db.close()


@app.route('/portal/<token>')
def client_portal(token):
    """Client-facing portal to view their case"""
    db = get_db()
    try:
        # First try to find client by portal token
        client = db.query(Client).filter_by(portal_token=token).first()
        
        # If not found, try to find a case with this token
        case = None
        if client:
            case = db.query(Case).filter_by(client_id=client.id).first()
        else:
            case = db.query(Case).filter_by(portal_token=token).first()
            if case:
                client = db.query(Client).filter_by(id=case.client_id).first()
        
        # Must have at least a client
        if not client:
            return "Invalid or expired access link", 404
        
        # Get analysis - first try from case, then by client
        analysis = None
        if case and case.analysis_id:
            analysis = db.query(Analysis).filter_by(id=case.analysis_id).first()
        
        if not analysis:
            analysis = db.query(Analysis).filter_by(client_id=client.id).order_by(Analysis.created_at.desc()).first()
        
        violations = []
        damages = None
        score = None
        letters = []
        cra_responses = []
        
        if analysis:
            violations = db.query(Violation).filter_by(analysis_id=analysis.id).all()
            damages = db.query(Damages).filter_by(analysis_id=analysis.id).first()
            score = db.query(CaseScore).filter_by(analysis_id=analysis.id).first()
            letters = db.query(DisputeLetter).filter_by(analysis_id=analysis.id).all()
        
        cra_responses = db.query(CRAResponse).filter_by(client_id=client.id).order_by(CRAResponse.created_at.desc()).all()
        
        # Get dispute items grouped by bureau
        dispute_items = db.query(DisputeItem).filter_by(client_id=client.id).order_by(DisputeItem.bureau, DisputeItem.created_at.desc()).all()
        
        # Get secondary bureau freezes
        secondary_freezes = db.query(SecondaryBureauFreeze).filter_by(client_id=client.id).all()
        
        # If no secondary freezes exist for this client, create default ones
        if not secondary_freezes:
            default_bureaus = [
                'Innovis', 'ChexSystems', 'Clarity Services Inc', 'LexisNexis', 
                'CoreLogic Teletrack', 'Factor Trust Inc', 'MicroBilt / PRBC',
                'LexisNexis Risk Solutions (A TransUnion Company)', 'DataX Ltd'
            ]
            for bureau in default_bureaus:
                freeze = SecondaryBureauFreeze(
                    client_id=client.id,
                    bureau_name=bureau,
                    status='pending'
                )
                db.add(freeze)
            db.commit()
            secondary_freezes = db.query(SecondaryBureauFreeze).filter_by(client_id=client.id).all()
        
        return render_template('client_portal.html',
            token=token,
            case=case,
            client=client,
            analysis=analysis,
            violations=violations,
            damages=damages,
            score=score,
            letters=letters,
            cra_responses=cra_responses,
            dispute_items=dispute_items,
            secondary_freezes=secondary_freezes,
            now=datetime.utcnow()
        )
    except Exception as e:
        return f"Error: {str(e)}", 500
    finally:
        db.close()


# ============================================================
# CLIENT PORTAL AUTHENTICATION ROUTES
# ============================================================

def check_rate_limit(email):
    """Check if login attempts are rate limited. Returns (allowed, wait_seconds)"""
    now = datetime.utcnow()
    if email in login_attempts:
        attempts = login_attempts[email]
        time_diff = (now - attempts['last_attempt']).total_seconds()
        
        if time_diff > 900:
            login_attempts[email] = {'count': 0, 'last_attempt': now}
            return True, 0
        
        if attempts['count'] >= 5:
            wait_time = 900 - int(time_diff)
            return False, max(0, wait_time)
    
    return True, 0


def record_login_attempt(email, success=False):
    """Record a login attempt"""
    now = datetime.utcnow()
    if success:
        if email in login_attempts:
            del login_attempts[email]
    else:
        if email not in login_attempts:
            login_attempts[email] = {'count': 0, 'last_attempt': now}
        login_attempts[email]['count'] += 1
        login_attempts[email]['last_attempt'] = now


@app.route('/portal/login', methods=['GET', 'POST'])
def portal_login():
    """Client portal login page"""
    if request.method == 'GET':
        if 'client_id' in session:
            return redirect('/portal/dashboard')
        return render_template('portal_login.html')
    
    db = get_db()
    try:
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        if not email or not password:
            return render_template('portal_login.html', error='Email and password are required')
        
        allowed, wait_time = check_rate_limit(email)
        if not allowed:
            minutes = wait_time // 60
            return render_template('portal_login.html', 
                error=f'Too many login attempts. Please wait {minutes} minutes before trying again.')
        
        client = db.query(Client).filter(Client.email.ilike(email)).first()
        
        if not client:
            record_login_attempt(email, success=False)
            return render_template('portal_login.html', error='Invalid email or password')
        
        if not client.portal_password_hash:
            record_login_attempt(email, success=False)
            return render_template('portal_login.html', 
                error='No password set. Please use your portal access link or contact support.')
        
        if not check_password_hash(client.portal_password_hash, password):
            record_login_attempt(email, success=False)
            return render_template('portal_login.html', error='Invalid email or password')
        
        record_login_attempt(email, success=True)
        
        session.permanent = True
        session['client_id'] = client.id
        session['client_email'] = client.email
        session['client_name'] = client.name
        
        if client.portal_token:
            return redirect(f'/portal/{client.portal_token}')
        else:
            portal_token = secrets.token_urlsafe(32)
            client.portal_token = portal_token
            db.commit()
            return redirect(f'/portal/{portal_token}')
            
    except Exception as e:
        print(f"Login error: {e}")
        return render_template('portal_login.html', error='An error occurred. Please try again.')
    finally:
        db.close()


@app.route('/portal/dashboard')
def portal_dashboard():
    """Redirect authenticated clients to their portal"""
    if 'client_id' not in session:
        return redirect('/portal/login')
    
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=session['client_id']).first()
        if client and client.portal_token:
            return redirect(f'/portal/{client.portal_token}')
        return redirect('/portal/login')
    finally:
        db.close()


@app.route('/portal/logout')
def portal_logout():
    """Log out client and clear session"""
    session.pop('client_id', None)
    session.pop('client_email', None)
    session.pop('client_name', None)
    return redirect('/portal/login')


@app.route('/api/portal/set-password', methods=['POST'])
def api_portal_set_password():
    """Set or update password for a client (from portal)"""
    db = get_db()
    try:
        data = request.json
        token = data.get('token', '')
        password = data.get('password', '')
        current_password = data.get('current_password', '')
        
        if not token:
            return jsonify({'success': False, 'error': 'Portal token required'}), 400
        
        if not password or len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        client = db.query(Client).filter_by(portal_token=token).first()
        if not client:
            return jsonify({'success': False, 'error': 'Invalid portal token'}), 404
        
        if client.portal_password_hash:
            if not current_password:
                return jsonify({'success': False, 'error': 'Current password required'}), 400
            if not check_password_hash(client.portal_password_hash, current_password):
                return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
        
        client.portal_password_hash = generate_password_hash(password)
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password set successfully. You can now log in with your email and password.'
        })
        
    except Exception as e:
        print(f"Set password error: {e}")
        db.rollback()
        return jsonify({'success': False, 'error': 'Failed to set password'}), 500
    finally:
        db.close()


@app.route('/api/portal/forgot-password', methods=['POST'])
def api_portal_forgot_password():
    """Send password reset email"""
    db = get_db()
    try:
        data = request.json
        email = data.get('email', '').strip().lower()
        
        if not email:
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        
        client = db.query(Client).filter(Client.email.ilike(email)).first()
        
        if not client:
            return jsonify({
                'success': True,
                'message': 'If an account exists with that email, a password reset link has been sent.'
            })
        
        reset_token = secrets.token_urlsafe(32)
        client.password_reset_token = reset_token
        client.password_reset_expires = datetime.utcnow() + timedelta(hours=24)
        db.commit()
        
        try:
            from services.email_service import send_email, is_sendgrid_configured
            
            if is_sendgrid_configured():
                reset_url = f"{request.host_url}portal/login?token={reset_token}"
                
                html_content = f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #1a1a2e;">Brightpath Ascend Group</h1>
                    </div>
                    
                    <h2 style="color: #333;">Password Reset Request</h2>
                    
                    <p>Hello {client.first_name or client.name},</p>
                    
                    <p>We received a request to reset your password for your Client Portal account.</p>
                    
                    <p>Click the button below to reset your password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background: linear-gradient(135deg, #84cc16, #22c55e); color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">Reset Password</a>
                    </div>
                    
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #3b82f6;">{reset_url}</p>
                    
                    <p><strong>This link will expire in 24 hours.</strong></p>
                    
                    <p>If you didn't request this password reset, you can safely ignore this email.</p>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                    
                    <p style="color: #64748b; font-size: 12px;">
                        Brightpath Ascend Group<br>
                        Credit Repair & FCRA Litigation Services
                    </p>
                </div>
                """
                
                result = send_email(
                    to_email=client.email,
                    subject='Reset Your Password - Brightpath Ascend Client Portal',
                    html_content=html_content
                )
                
                if not result['success']:
                    print(f"Failed to send reset email: {result.get('error')}")
            else:
                print(f"SendGrid not configured. Reset token for {email}: {reset_token}")
                
        except Exception as email_error:
            print(f"Email sending error: {email_error}")
        
        return jsonify({
            'success': True,
            'message': 'If an account exists with that email, a password reset link has been sent.'
        })
        
    except Exception as e:
        print(f"Forgot password error: {e}")
        db.rollback()
        return jsonify({'success': False, 'error': 'Failed to process request'}), 500
    finally:
        db.close()


@app.route('/api/portal/reset-password', methods=['POST'])
def api_portal_reset_password():
    """Reset password using token from email"""
    db = get_db()
    try:
        data = request.json
        token = data.get('token', '').strip()
        password = data.get('password', '')
        
        if not token:
            return jsonify({'success': False, 'error': 'Reset token is required'}), 400
        
        if not password or len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        client = db.query(Client).filter_by(password_reset_token=token).first()
        
        if not client:
            return jsonify({'success': False, 'error': 'Invalid or expired reset link'}), 400
        
        if client.password_reset_expires and client.password_reset_expires < datetime.utcnow():
            client.password_reset_token = None
            client.password_reset_expires = None
            db.commit()
            return jsonify({'success': False, 'error': 'Reset link has expired. Please request a new one.'}), 400
        
        client.portal_password_hash = generate_password_hash(password)
        client.password_reset_token = None
        client.password_reset_expires = None
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password has been reset successfully. You can now log in.'
        })
        
    except Exception as e:
        print(f"Reset password error: {e}")
        db.rollback()
        return jsonify({'success': False, 'error': 'Failed to reset password'}), 500
    finally:
        db.close()


# ============================================================
# CLIENT SIGNUP & ONBOARDING ROUTES
# ============================================================

@app.route('/signup')
def client_signup():
    """Public client signup page"""
    return render_template('client_signup.html')


@app.route('/api/client/signup', methods=['POST'])
def api_client_signup():
    """Handle new client registration"""
    db = get_db()
    try:
        data = request.json
        
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        
        if not first_name or not last_name or not email:
            return jsonify({'success': False, 'error': 'Name and email are required'}), 400
        
        existing = db.query(Client).filter_by(email=email).first()
        if existing:
            return jsonify({'success': False, 'error': 'An account with this email already exists'}), 400
        
        referral_code = 'BP' + secrets.token_hex(4).upper()
        portal_token = secrets.token_urlsafe(32)
        
        from datetime import date
        dob_str = data.get('dateOfBirth', '')
        dob = None
        if dob_str:
            try:
                dob = date.fromisoformat(dob_str)
            except:
                pass
        
        client = Client(
            name=f"{first_name} {last_name}",
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address_street=data.get('addressStreet', ''),
            address_city=data.get('addressCity', ''),
            address_state=data.get('addressState', ''),
            address_zip=data.get('addressZip', ''),
            ssn_last_four=data.get('ssnLast4', ''),
            date_of_birth=dob,
            credit_monitoring_service=data.get('creditService', ''),
            credit_monitoring_username=data.get('creditUsername', ''),
            credit_monitoring_password_encrypted=encrypt_value(data.get('creditPassword', '')) if data.get('creditPassword') else '',
            current_dispute_round=0,
            dispute_status='new',
            referral_code=referral_code,
            portal_token=portal_token,
            status='signup',
            signup_completed=True,
            agreement_signed=data.get('agreeTerms', False),
            agreement_signed_at=datetime.utcnow() if data.get('agreeTerms') else None
        )
        
        ref_code = data.get('referralCode', '').strip()
        if ref_code:
            referrer = db.query(Client).filter_by(referral_code=ref_code).first()
            if referrer:
                client.referred_by_client_id = referrer.id
                referral = ClientReferral(
                    referring_client_id=referrer.id,
                    referred_name=client.name,
                    referred_email=client.email,
                    referred_phone=client.phone,
                    status='signed_up'
                )
                db.add(referral)
        
        db.add(client)
        db.flush()
        
        case_number = generate_case_number()
        case = Case(
            client_id=client.id,
            case_number=case_number,
            status='intake',
            pricing_tier='tier1',
            portal_token=portal_token,
            intake_at=datetime.utcnow()
        )
        db.add(case)
        db.flush()
        
        event = CaseEvent(
            case_id=case.id,
            event_type='signup',
            description=f'Client {client.name} signed up via web portal'
        )
        db.add(event)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'clientId': client.id,
            'caseNumber': case_number,
            'referralCode': referral_code,
            'portalToken': portal_token,
            'message': 'Registration complete! We will pull your credit report and begin your analysis.'
        }), 201
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# STRIPE PAYMENT INTEGRATION
# ============================================================

@app.route('/api/stripe/pricing-tiers', methods=['GET'])
def get_pricing_tiers():
    """Return available pricing tiers for display"""
    from services.stripe_client import PRICING_TIERS
    
    tiers = []
    for key, tier in PRICING_TIERS.items():
        tiers.append({
            'id': key,
            'name': tier['name'],
            'amount': tier['amount'],
            'display': tier['display'],
            'description': get_tier_description(key)
        })
    
    return jsonify({'success': True, 'tiers': tiers}), 200


def get_tier_description(tier_key):
    """Get description for each pricing tier"""
    descriptions = {
        'tier1': 'Basic credit restoration package with initial dispute letters',
        'tier2': 'Standard package with follow-up rounds and bureau monitoring',
        'tier3': 'Premium package with comprehensive dispute strategy',
        'tier4': 'Advanced package with litigation preparation support',
        'tier5': 'Elite package with full litigation support and priority handling'
    }
    return descriptions.get(tier_key, '')


@app.route('/api/client/signup/draft', methods=['POST'])
def api_create_signup_draft():
    """Save draft signup data and return draft UUID for payment flow"""
    db = get_db()
    try:
        data = request.json
        
        first_name = data.get('firstName', '').strip()
        last_name = data.get('lastName', '').strip()
        email = data.get('email', '').strip()
        
        if not first_name or not last_name or not email:
            return jsonify({'success': False, 'error': 'Name and email are required'}), 400
        
        existing_client = db.query(Client).filter_by(email=email).first()
        if existing_client:
            return jsonify({'success': False, 'error': 'An account with this email already exists'}), 400
        
        plan_tier = data.get('planTier', 'tier1')
        from services.stripe_client import PRICING_TIERS
        tier_info = PRICING_TIERS.get(plan_tier)
        if not tier_info:
            return jsonify({'success': False, 'error': 'Invalid pricing tier'}), 400
        
        draft_uuid = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        form_data = {
            'firstName': first_name,
            'lastName': last_name,
            'email': email,
            'phone': data.get('phone', ''),
            'addressStreet': data.get('addressStreet', ''),
            'addressCity': data.get('addressCity', ''),
            'addressState': data.get('addressState', ''),
            'addressZip': data.get('addressZip', ''),
            'dateOfBirth': data.get('dateOfBirth', ''),
            'ssnLast4': data.get('ssnLast4', ''),
            'referralCode': data.get('referralCode', ''),
            'creditService': data.get('creditService', ''),
            'creditUsername': data.get('creditUsername', ''),
            'creditPassword': data.get('creditPassword', ''),
            'agreeTerms': data.get('agreeTerms', False),
            'agreeComms': data.get('agreeComms', False)
        }
        
        draft = SignupDraft(
            draft_uuid=draft_uuid,
            form_data=form_data,
            plan_tier=plan_tier,
            plan_amount=tier_info['amount'],
            status='pending',
            expires_at=expires_at
        )
        
        db.add(draft)
        db.commit()
        
        return jsonify({
            'success': True,
            'draftId': draft_uuid,
            'planTier': plan_tier,
            'planAmount': tier_info['amount'],
            'planDisplay': tier_info['display'],
            'expiresAt': expires_at.isoformat()
        }), 201
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/client/signup/complete-free', methods=['POST'])
def api_complete_free_signup():
    """Complete a free tier signup without payment"""
    db = get_db()
    try:
        data = request.json
        draft_id = data.get('draftId')
        
        if not draft_id:
            return jsonify({'success': False, 'error': 'Draft ID is required'}), 400
        
        draft = db.query(SignupDraft).filter_by(draft_uuid=draft_id).first()
        if not draft:
            return jsonify({'success': False, 'error': 'Signup draft not found'}), 404
        
        if draft.status != 'pending':
            return jsonify({'success': False, 'error': f'Draft is not pending (status: {draft.status})'}), 400
        
        form_data = draft.form_data or {}
        
        referral_code = generate_referral_code()
        portal_token = str(uuid.uuid4())
        
        client = Client(
            name=f"{form_data.get('firstName', '')} {form_data.get('lastName', '')}".strip(),
            email=form_data.get('email', ''),
            phone=form_data.get('phone', ''),
            address=f"{form_data.get('addressStreet', '')}, {form_data.get('addressCity', '')} {form_data.get('addressState', '')} {form_data.get('addressZip', '')}".strip(' ,'),
            credit_service=form_data.get('creditService', ''),
            credit_username=form_data.get('creditUsername', ''),
            credit_password=form_data.get('creditPassword', ''),
            status='lead',
            signup_plan='free',
            signup_amount=0,
            payment_status='paid',
            payment_method='free',
            payment_pending=False,
            payment_received_at=datetime.utcnow(),
            referral_code=referral_code,
            portal_token=portal_token,
            referred_by=form_data.get('referralCode', ''),
            consent_signed=form_data.get('agreeTerms', False),
            consent_date=datetime.utcnow() if form_data.get('agreeTerms') else None
        )
        
        db.add(client)
        draft.status = 'completed'
        db.commit()
        
        try:
            from services.sms_automation import trigger_welcome_sms
            sms_result = trigger_welcome_sms(db, client.id)
            if sms_result.get('sent'):
                print(f"📱 Welcome SMS sent to client {client.id}")
        except Exception as sms_error:
            print(f"⚠️  SMS trigger error (non-fatal): {sms_error}")
        
        try:
            from services.email_automation import trigger_welcome_email
            email_result = trigger_welcome_email(db, client.id)
            if email_result.get('sent'):
                print(f"📧 Welcome email sent to client {client.id}")
        except Exception as email_error:
            print(f"⚠️  Email trigger error (non-fatal): {email_error}")
        
        return jsonify({
            'success': True,
            'clientId': client.id,
            'referralCode': referral_code,
            'portalToken': portal_token
        }), 201
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/client/signup/complete-manual', methods=['POST'])
def api_complete_manual_signup():
    """Complete a signup with manual payment (CashApp, Venmo, Zelle, PayPal, Pay Later)"""
    db = get_db()
    try:
        data = request.json
        draft_id = data.get('draftId')
        payment_method = data.get('paymentMethod', 'pending')
        
        if not draft_id:
            return jsonify({'success': False, 'error': 'Draft ID is required'}), 400
        
        draft = db.query(SignupDraft).filter_by(draft_uuid=draft_id).first()
        if not draft:
            return jsonify({'success': False, 'error': 'Signup draft not found'}), 404
        
        if draft.status != 'pending':
            return jsonify({'success': False, 'error': f'Draft is not pending (status: {draft.status})'}), 400
        
        form_data = draft.form_data or {}
        
        referral_code = generate_referral_code()
        portal_token = str(uuid.uuid4())
        
        client = Client(
            name=f"{form_data.get('firstName', '')} {form_data.get('lastName', '')}".strip(),
            email=form_data.get('email', ''),
            phone=form_data.get('phone', ''),
            address=f"{form_data.get('addressStreet', '')}, {form_data.get('addressCity', '')} {form_data.get('addressState', '')} {form_data.get('addressZip', '')}".strip(' ,'),
            credit_service=form_data.get('creditService', ''),
            credit_username=form_data.get('creditUsername', ''),
            credit_password=form_data.get('creditPassword', ''),
            status='lead',
            signup_plan=draft.plan_tier,
            signup_amount=draft.plan_amount,
            payment_status='pending',
            payment_method=payment_method,
            payment_pending=True,
            referral_code=referral_code,
            portal_token=portal_token,
            referred_by=form_data.get('referralCode', ''),
            consent_signed=form_data.get('agreeTerms', False),
            consent_date=datetime.utcnow() if form_data.get('agreeTerms') else None
        )
        
        db.add(client)
        draft.status = 'completed'
        db.commit()
        
        try:
            from services.sms_automation import trigger_welcome_sms
            sms_result = trigger_welcome_sms(db, client.id)
            if sms_result.get('sent'):
                print(f"📱 Welcome SMS sent to client {client.id}")
        except Exception as sms_error:
            print(f"⚠️  SMS trigger error (non-fatal): {sms_error}")
        
        try:
            from services.email_automation import trigger_welcome_email
            email_result = trigger_welcome_email(db, client.id)
            if email_result.get('sent'):
                print(f"📧 Welcome email sent to client {client.id}")
        except Exception as email_error:
            print(f"⚠️  Email trigger error (non-fatal): {email_error}")
        
        return jsonify({
            'success': True,
            'clientId': client.id,
            'referralCode': referral_code,
            'portalToken': portal_token,
            'paymentPending': True
        }), 201
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/stripe/checkout-session', methods=['POST'])
def api_create_checkout_session():
    """Create Stripe Checkout session for payment"""
    db = get_db()
    try:
        data = request.json
        draft_id = data.get('draftId')
        
        if not draft_id:
            return jsonify({'success': False, 'error': 'Draft ID is required'}), 400
        
        draft = db.query(SignupDraft).filter_by(draft_uuid=draft_id).first()
        if not draft:
            return jsonify({'success': False, 'error': 'Signup draft not found'}), 404
        
        if draft.status != 'pending':
            return jsonify({'success': False, 'error': f'Draft is not pending (status: {draft.status})'}), 400
        
        if draft.expires_at < datetime.utcnow():
            draft.status = 'expired'
            db.commit()
            return jsonify({'success': False, 'error': 'Draft has expired. Please start over.'}), 400
        
        host = request.host_url.rstrip('/')
        success_url = f"{host}/signup/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{host}/signup?cancelled=true"
        
        form_data = draft.form_data or {}
        customer_email = form_data.get('email', '')
        
        from services.stripe_client import create_checkout_session
        session = create_checkout_session(
            draft_id=draft_id,
            tier_key=draft.plan_tier,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=customer_email
        )
        
        draft.stripe_checkout_session_id = session.id
        db.commit()
        
        return jsonify({
            'success': True,
            'sessionId': session.id,
            'checkoutUrl': session.url
        }), 200
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/stripe/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events (payment confirmations)"""
    db = get_db()
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        if not sig_header:
            print("⚠️  Stripe webhook: Missing Stripe-Signature header")
            return jsonify({'error': 'Missing signature'}), 400
        
        from services.stripe_client import verify_webhook_signature, get_webhook_secret
        
        try:
            event = verify_webhook_signature(payload, sig_header)
        except Exception as e:
            print(f"⚠️  Stripe webhook signature verification failed: {e}")
            return jsonify({'error': 'Invalid signature'}), 400
        
        event_type = event.get('type') if isinstance(event, dict) else event.type
        print(f"🔔 Stripe webhook received: {event_type}")
        
        if event_type == 'checkout.session.completed':
            session = event.get('data', {}).get('object', {}) if isinstance(event, dict) else event.data.object
            handle_checkout_completed(db, session)
        
        elif event_type == 'payment_intent.succeeded':
            payment_intent = event.get('data', {}).get('object', {}) if isinstance(event, dict) else event.data.object
            handle_payment_succeeded(db, payment_intent)
        
        elif event_type == 'payment_intent.payment_failed':
            payment_intent = event.get('data', {}).get('object', {}) if isinstance(event, dict) else event.data.object
            handle_payment_failed(db, payment_intent)
        
        return jsonify({'received': True}), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Stripe webhook error: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


def handle_checkout_completed(db, session):
    """Handle checkout.session.completed event - promote draft to client"""
    try:
        session_id = session.get('id') if isinstance(session, dict) else session.id
        metadata = session.get('metadata', {}) if isinstance(session, dict) else session.metadata
        customer_id = session.get('customer') if isinstance(session, dict) else session.customer
        payment_intent_id = session.get('payment_intent') if isinstance(session, dict) else session.payment_intent
        amount_total = session.get('amount_total') if isinstance(session, dict) else session.amount_total
        
        draft_id = metadata.get('draft_id') if metadata else None
        tier = metadata.get('tier') if metadata else None
        
        if not draft_id:
            print(f"⚠️  Checkout session {session_id} has no draft_id in metadata")
            return
        
        draft = db.query(SignupDraft).filter_by(draft_uuid=draft_id).first()
        if not draft:
            print(f"⚠️  Draft {draft_id} not found for session {session_id}")
            return
        
        if draft.status == 'paid':
            print(f"✅ Draft {draft_id} already processed")
            return
        
        form_data = draft.form_data or {}
        
        first_name = form_data.get('firstName', '')
        last_name = form_data.get('lastName', '')
        email = form_data.get('email', '')
        
        existing = db.query(Client).filter_by(email=email).first()
        if existing:
            print(f"⚠️  Client with email {email} already exists")
            draft.status = 'paid'
            draft.promoted_client_id = existing.id
            draft.promoted_at = datetime.utcnow()
            db.commit()
            return
        
        referral_code = 'BP' + secrets.token_hex(4).upper()
        portal_token = secrets.token_urlsafe(32)
        
        from datetime import date
        dob_str = form_data.get('dateOfBirth', '')
        dob = None
        if dob_str:
            try:
                dob = date.fromisoformat(dob_str)
            except:
                pass
        
        client = Client(
            name=f"{first_name} {last_name}",
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=form_data.get('phone', ''),
            address_street=form_data.get('addressStreet', ''),
            address_city=form_data.get('addressCity', ''),
            address_state=form_data.get('addressState', ''),
            address_zip=form_data.get('addressZip', ''),
            ssn_last_four=form_data.get('ssnLast4', ''),
            date_of_birth=dob,
            credit_monitoring_service=form_data.get('creditService', ''),
            credit_monitoring_username=form_data.get('creditUsername', ''),
            credit_monitoring_password_encrypted=encrypt_value(form_data.get('creditPassword', '')) if form_data.get('creditPassword') else '',
            current_dispute_round=0,
            dispute_status='new',
            referral_code=referral_code,
            portal_token=portal_token,
            status='active',
            signup_completed=True,
            agreement_signed=form_data.get('agreeTerms', False),
            agreement_signed_at=datetime.utcnow() if form_data.get('agreeTerms') else None,
            signup_plan=tier or draft.plan_tier,
            signup_amount=amount_total or draft.plan_amount,
            stripe_customer_id=customer_id,
            stripe_checkout_session_id=session_id,
            stripe_payment_intent_id=payment_intent_id,
            payment_status='paid',
            payment_received_at=datetime.utcnow()
        )
        
        ref_code = form_data.get('referralCode', '').strip()
        if ref_code:
            referrer = db.query(Client).filter_by(referral_code=ref_code).first()
            if referrer:
                client.referred_by_client_id = referrer.id
                referral = ClientReferral(
                    referring_client_id=referrer.id,
                    referred_name=client.name,
                    referred_email=client.email,
                    referred_phone=client.phone,
                    status='signed_up'
                )
                db.add(referral)
        
        db.add(client)
        db.flush()
        
        case_number = generate_case_number()
        case = Case(
            client_id=client.id,
            case_number=case_number,
            status='intake',
            pricing_tier=tier or draft.plan_tier,
            base_fee=amount_total / 100 if amount_total else 0,
            portal_token=portal_token,
            intake_at=datetime.utcnow()
        )
        db.add(case)
        db.flush()
        
        event = CaseEvent(
            case_id=case.id,
            event_type='signup',
            description=f'Client {client.name} signed up via Stripe payment ({tier or draft.plan_tier})',
            event_data=json.dumps({'payment_intent': payment_intent_id, 'amount': amount_total})
        )
        db.add(event)
        
        draft.status = 'paid'
        draft.promoted_client_id = client.id
        draft.promoted_at = datetime.utcnow()
        
        db.commit()
        
        print(f"✅ Promoted draft {draft_id} to client {client.id} ({client.email})")
        
        try:
            from services.sms_automation import trigger_welcome_sms
            sms_result = trigger_welcome_sms(db, client.id)
            if sms_result.get('sent'):
                print(f"📱 Welcome SMS sent to client {client.id}")
            else:
                print(f"📱 Welcome SMS skipped: {sms_result.get('reason', 'unknown')}")
        except Exception as sms_error:
            print(f"⚠️  SMS trigger error (non-fatal): {sms_error}")
        
        try:
            from services.email_automation import trigger_welcome_email
            email_result = trigger_welcome_email(db, client.id)
            if email_result.get('sent'):
                print(f"📧 Welcome email sent to client {client.id}")
            else:
                print(f"📧 Welcome email skipped: {email_result.get('reason', 'unknown')}")
        except Exception as email_error:
            print(f"⚠️  Email trigger error (non-fatal): {email_error}")
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"❌ Error handling checkout completed: {e}")


def handle_payment_succeeded(db, payment_intent):
    """Handle payment_intent.succeeded event"""
    payment_intent_id = payment_intent.get('id') if isinstance(payment_intent, dict) else payment_intent.id
    print(f"💰 Payment succeeded: {payment_intent_id}")


def handle_payment_failed(db, payment_intent):
    """Handle payment_intent.payment_failed event"""
    payment_intent_id = payment_intent.get('id') if isinstance(payment_intent, dict) else payment_intent.id
    print(f"❌ Payment failed: {payment_intent_id}")


@app.route('/signup/success')
def signup_success():
    """Success page after Stripe checkout"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return render_template('client_signup.html', success=False, error='Missing session ID')
    
    db = get_db()
    try:
        draft = db.query(SignupDraft).filter_by(stripe_checkout_session_id=session_id).first()
        
        if not draft:
            return render_template('client_signup.html', success=False, error='Session not found')
        
        if draft.status == 'paid' and draft.promoted_client_id:
            client = db.query(Client).filter_by(id=draft.promoted_client_id).first()
            if client:
                return render_template('client_signup.html', 
                    success=True, 
                    referral_code=client.referral_code,
                    client_name=client.name,
                    portal_token=client.portal_token
                )
        
        return render_template('client_signup.html', 
            success=True,
            pending=True,
            message='Your payment is being processed. You will receive a confirmation email shortly.'
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('client_signup.html', success=False, error=str(e))
    finally:
        db.close()


@app.route('/api/client/import', methods=['POST'])
def api_client_import():
    """Import existing client at their current dispute round"""
    db = get_db()
    try:
        data = request.json
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        
        if not name:
            return jsonify({'success': False, 'error': 'Client name is required'}), 400
        
        from datetime import date
        dob_str = data.get('dateOfBirth', '')
        dob = None
        if dob_str:
            try:
                dob = date.fromisoformat(dob_str)
            except:
                pass
        
        referral_code = 'BP' + secrets.token_hex(4).upper()
        portal_token = secrets.token_urlsafe(32)
        
        client = Client(
            name=name,
            first_name=data.get('firstName', ''),
            last_name=data.get('lastName', ''),
            email=email,
            phone=data.get('phone', ''),
            address_street=data.get('addressStreet', ''),
            address_city=data.get('addressCity', ''),
            address_state=data.get('addressState', ''),
            address_zip=data.get('addressZip', ''),
            ssn_last_four=data.get('ssnLast4', ''),
            date_of_birth=dob,
            credit_monitoring_service=data.get('creditService', ''),
            credit_monitoring_username=data.get('creditUsername', ''),
            current_dispute_round=int(data.get('currentRound', 1)),
            current_dispute_step=data.get('currentStep', ''),
            dispute_status=data.get('disputeStatus', 'active'),
            legacy_system_id=data.get('legacySystemId', ''),
            legacy_case_number=data.get('legacyCaseNumber', ''),
            imported_at=datetime.utcnow(),
            import_notes=data.get('importNotes', ''),
            referral_code=referral_code,
            portal_token=portal_token,
            status='active',
            signup_completed=True,
            agreement_signed=True
        )
        
        db.add(client)
        db.flush()
        
        case_number = generate_case_number()
        case = Case(
            client_id=client.id,
            case_number=case_number,
            status='intake',
            pricing_tier=data.get('pricingTier', 'tier1'),
            portal_token=portal_token,
            intake_at=datetime.utcnow()
        )
        db.add(case)
        db.flush()
        
        event = CaseEvent(
            case_id=case.id,
            event_type='import',
            description=f'Client imported from legacy system at round {client.current_dispute_round}'
        )
        db.add(event)
        
        db.commit()
        
        return jsonify({
            'success': True,
            'clientId': client.id,
            'caseId': case.id,
            'caseNumber': case_number,
            'message': f'Client imported successfully at round {client.current_dispute_round}'
        }), 201
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/cra-response/upload', methods=['POST'])
def api_cra_response_upload():
    """Upload CRA response letter with automated dispute round handling"""
    db = get_db()
    try:
        client_id = request.form.get('clientId')
        case_id = request.form.get('caseId')
        bureau = request.form.get('bureau')
        dispute_round = int(request.form.get('disputeRound', 1))
        response_type = request.form.get('responseType', 'unknown')
        items_deleted = int(request.form.get('itemsDeleted', 0))
        items_verified = int(request.form.get('itemsVerified', 0))
        items_updated = int(request.form.get('itemsUpdated', 0))
        auto_analyze = request.form.get('autoAnalyze', 'false').lower() == 'true'
        
        if not client_id or not bureau:
            return jsonify({'success': False, 'error': 'Client ID and bureau are required'}), 400
        
        file = request.files.get('file')
        if not file:
            return jsonify({'success': False, 'error': 'File is required'}), 400
        
        os.makedirs('static/cra_responses', exist_ok=True)
        filename = f"{client_id}_{bureau}_round{dispute_round}_{secrets.token_hex(4)}.pdf"
        file_path = f"static/cra_responses/{filename}"
        file.save(file_path)
        
        from datetime import date
        response_date_str = request.form.get('responseDate', '')
        response_date = None
        if response_date_str:
            try:
                response_date = date.fromisoformat(response_date_str)
            except:
                pass
        
        cra_response = CRAResponse(
            client_id=int(client_id),
            case_id=int(case_id) if case_id else None,
            bureau=bureau,
            dispute_round=dispute_round,
            response_type=response_type,
            response_date=response_date,
            received_date=date.today(),
            file_path=file_path,
            file_name=file.filename,
            file_size=os.path.getsize(file_path),
            uploaded_by_admin=True,
            items_deleted=items_deleted,
            items_verified=items_verified,
            items_updated=items_updated,
            requires_follow_up=(response_type in ['verified', 'investigating'])
        )
        
        if cra_response.requires_follow_up:
            from datetime import timedelta
            cra_response.follow_up_deadline = datetime.utcnow() + timedelta(days=30)
        
        db.add(cra_response)
        
        client = db.query(Client).filter_by(id=int(client_id)).first()
        if client:
            client.last_bureau_response_at = datetime.utcnow()
            if response_type in ['verified', 'investigating']:
                client.dispute_status = 'waiting_response'
            elif response_type == 'deleted':
                client.dispute_status = 'active'
        
        if response_type == 'deleted' or items_deleted > 0:
            dispute_items = db.query(DisputeItem).filter(
                DisputeItem.client_id == int(client_id),
                DisputeItem.bureau == bureau,
                DisputeItem.dispute_round == dispute_round,
                DisputeItem.status.in_(['sent', 'in_progress', 'to_do'])
            ).all()
            
            items_to_mark = min(items_deleted, len(dispute_items)) if items_deleted > 0 else len(dispute_items)
            for i, item in enumerate(dispute_items):
                if i < items_to_mark:
                    item.status = 'deleted'
                    item.response_date = date.today()
            
            print(f"📋 Marked {items_to_mark} DisputeItems as 'deleted' for client {client_id}, bureau {bureau}")
        
        from services.deadline_service import complete_deadline
        active_deadlines = db.query(CaseDeadline).filter(
            CaseDeadline.client_id == int(client_id),
            CaseDeadline.bureau == bureau,
            CaseDeadline.dispute_round == dispute_round,
            CaseDeadline.deadline_type == 'cra_response',
            CaseDeadline.status == 'active'
        ).all()
        
        for deadline in active_deadlines:
            deadline.status = 'completed'
            deadline.completed_at = datetime.utcnow()
            deadline.notes = (deadline.notes or '') + f"\n[Auto-completed] Response received: {response_type}"
        
        case_event = CaseEvent(
            case_id=int(case_id) if case_id else None,
            event_type='cra_response_received',
            description=f'{bureau} response received for round {dispute_round}: {response_type}',
            event_data=json.dumps({
                'client_id': int(client_id),
                'bureau': bureau,
                'dispute_round': dispute_round,
                'response_type': response_type,
                'items_deleted': items_deleted,
                'items_verified': items_verified,
                'items_updated': items_updated
            })
        )
        db.add(case_event)
        
        db.commit()
        
        round_status = check_round_complete_internal(db, int(client_id), dispute_round)
        
        if round_status.get('round_complete'):
            print(f"🎯 Round {dispute_round} complete for client {client_id}! All bureaus responded.")
            try:
                from services.email_automation import send_admin_notification
                send_admin_notification(
                    subject=f"Dispute Round {dispute_round} Complete - Client #{client_id}",
                    message=f"All 3 bureaus have responded for client #{client_id} in round {dispute_round}.\n\nSuccess Rate: {round_status.get('success_rate', 0):.1f}%\nDeleted: {round_status.get('total_deleted', 0)}\n\nConsider advancing to the next round."
                )
            except Exception as email_err:
                print(f"⚠️  Admin notification error (non-fatal): {email_err}")
        
        try:
            from services.sms_automation import trigger_cra_response
            sms_result = trigger_cra_response(db, int(client_id), bureau)
            if sms_result.get('sent'):
                print(f"📱 CRA response SMS sent to client {client_id} for {bureau}")
        except Exception as sms_error:
            print(f"⚠️  SMS trigger error (non-fatal): {sms_error}")
        
        analysis_result = None
        if auto_analyze:
            try:
                from services.ocr_service import analyze_cra_response
                analysis_result = analyze_cra_response(cra_response.id)
                if analysis_result.get('success'):
                    print(f"🤖 Auto-analyzed CRA response {cra_response.id}: {analysis_result.get('summary', {})}")
                else:
                    print(f"⚠️  Auto-analyze failed: {analysis_result.get('error')}")
            except Exception as analyze_error:
                print(f"⚠️  Auto-analyze error (non-fatal): {analyze_error}")
                analysis_result = {'success': False, 'error': str(analyze_error)}
        
        response_data = {
            'success': True,
            'responseId': cra_response.id,
            'message': f'{bureau} response uploaded successfully',
            'roundStatus': round_status
        }
        
        if auto_analyze and analysis_result:
            response_data['analysis'] = analysis_result
        
        return jsonify(response_data), 201
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


def check_round_complete_internal(db, client_id, dispute_round):
    """Internal helper to check if a dispute round is complete"""
    bureaus = ['Experian', 'TransUnion', 'Equifax']
    responses = db.query(CRAResponse).filter(
        CRAResponse.client_id == client_id,
        CRAResponse.dispute_round == dispute_round
    ).all()
    
    bureaus_responded = set()
    total_deleted = 0
    total_verified = 0
    total_updated = 0
    
    for resp in responses:
        if resp.bureau in bureaus:
            bureaus_responded.add(resp.bureau)
        total_deleted += resp.items_deleted or 0
        total_verified += resp.items_verified or 0
        total_updated += resp.items_updated or 0
    
    bureaus_missing = [b for b in bureaus if b not in bureaus_responded]
    round_complete = len(bureaus_missing) == 0
    
    total_items = total_deleted + total_verified + total_updated
    success_rate = (total_deleted / total_items * 100) if total_items > 0 else 0
    
    client = db.query(Client).filter_by(id=client_id).first()
    
    next_action = None
    if round_complete:
        if dispute_round < 4:
            next_action = 'advance_round'
        else:
            next_action = 'complete_or_litigation'
    
    return {
        'round_complete': round_complete,
        'bureaus_responded': list(bureaus_responded),
        'bureaus_missing': bureaus_missing,
        'total_deleted': total_deleted,
        'total_verified': total_verified,
        'total_updated': total_updated,
        'success_rate': success_rate,
        'current_round': dispute_round,
        'client_dispute_round': client.current_dispute_round if client else None,
        'next_action': next_action
    }


@app.route('/api/client/<int:client_id>/responses')
def api_client_responses(client_id):
    """Get all CRA responses for a client"""
    db = get_db()
    try:
        responses = db.query(CRAResponse).filter_by(client_id=client_id).order_by(CRAResponse.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'responses': [{
                'id': r.id,
                'bureau': r.bureau,
                'disputeRound': r.dispute_round,
                'responseType': r.response_type,
                'responseDate': r.response_date.isoformat() if r.response_date else None,
                'receivedDate': r.received_date.isoformat() if r.received_date else None,
                'fileName': r.file_name,
                'filePath': r.file_path,
                'itemsVerified': r.items_verified,
                'itemsDeleted': r.items_deleted,
                'itemsUpdated': r.items_updated,
                'requiresFollowUp': r.requires_follow_up,
                'followUpDeadline': r.follow_up_deadline.isoformat() if r.follow_up_deadline else None,
                'createdAt': r.created_at.isoformat()
            } for r in responses]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# CRA RESPONSE ANALYSIS ENDPOINTS (AI-Powered)
# ============================================================

@app.route('/api/cra-response/<int:response_id>/analyze', methods=['POST'])
def api_analyze_cra_response(response_id):
    """
    Analyze a CRA response document using Claude AI.
    Extracts items, matches to existing DisputeItems, and detects reinsertion violations.
    
    Returns analysis results for staff review before applying changes.
    """
    db = get_db()
    try:
        cra_response = db.query(CRAResponse).filter_by(id=response_id).first()
        if not cra_response:
            return jsonify({'success': False, 'error': 'CRA Response not found'}), 404
        
        if not cra_response.file_path:
            return jsonify({'success': False, 'error': 'No file attached to this CRA response'}), 400
        
        from services.ocr_service import analyze_cra_response
        result = analyze_cra_response(response_id)
        
        if result.get('success'):
            event = CaseEvent(
                case_id=cra_response.case_id,
                event_type='cra_response_analyzed',
                description=f'AI analyzed {cra_response.bureau} response for round {cra_response.dispute_round}',
                event_data=json.dumps({
                    'cra_response_id': response_id,
                    'ocr_record_id': result.get('ocr_record_id'),
                    'items_found': result.get('summary', {}).get('total_items_found', 0),
                    'items_matched': result.get('summary', {}).get('items_matched', 0),
                    'reinsertion_violations': result.get('summary', {}).get('reinsertion_violations', 0),
                    'tokens_used': result.get('tokens_used', 0)
                })
            )
            db.add(event)
            db.commit()
            
            print(f"✅ CRA Response {response_id} analyzed: {result.get('summary', {})}")
        
        return jsonify(result)
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/cra-response/<int:response_id>/analysis')
def api_get_cra_response_analysis(response_id):
    """Get the analysis results for a CRA response (for review)."""
    db = get_db()
    try:
        from database import CRAResponseOCR
        
        ocr_records = db.query(CRAResponseOCR).filter(
            CRAResponseOCR.client_id == db.query(CRAResponse.client_id).filter_by(id=response_id).scalar()
        ).order_by(CRAResponseOCR.created_at.desc()).all()
        
        if not ocr_records:
            return jsonify({'success': False, 'error': 'No analysis found for this response'}), 404
        
        latest = ocr_records[0]
        
        from services.ocr_service import get_analysis_for_review
        result = get_analysis_for_review(latest.id)
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/cra-response/<int:response_id>/apply-analysis', methods=['POST'])
def api_apply_cra_response_analysis(response_id):
    """
    Apply the reviewed analysis to update DisputeItem statuses.
    Accepts optional edits to the matched items before applying.
    """
    db = get_db()
    try:
        data = request.json or {}
        ocr_record_id = data.get('ocr_record_id')
        reviewed_items = data.get('reviewed_items')
        create_violations = data.get('create_violations', True)
        
        staff_user = session.get('staff_email') or session.get('staff_name') or 'unknown'
        
        if not ocr_record_id:
            from database import CRAResponseOCR
            cra_response = db.query(CRAResponse).filter_by(id=response_id).first()
            if not cra_response:
                return jsonify({'success': False, 'error': 'CRA Response not found'}), 404
            
            ocr_record = db.query(CRAResponseOCR).filter(
                CRAResponseOCR.client_id == cra_response.client_id,
                CRAResponseOCR.bureau == cra_response.bureau
            ).order_by(CRAResponseOCR.created_at.desc()).first()
            
            if not ocr_record:
                return jsonify({'success': False, 'error': 'No analysis found. Run analyze first.'}), 400
            
            ocr_record_id = ocr_record.id
        
        from services.ocr_service import apply_analysis_updates
        result = apply_analysis_updates(
            ocr_record_id=ocr_record_id,
            reviewed_items=reviewed_items,
            create_violations=create_violations,
            staff_user=staff_user
        )
        
        if result.get('success'):
            cra_response = db.query(CRAResponse).filter_by(id=response_id).first()
            
            updates_made = result.get('updates_made', [])
            deleted_count = len([u for u in updates_made if u.get('new_status') == 'deleted'])
            verified_count = len([u for u in updates_made if u.get('new_status') == 'verified'])
            updated_count = len([u for u in updates_made if u.get('new_status') == 'updated'])
            
            if cra_response:
                cra_response.items_deleted = (cra_response.items_deleted or 0) + deleted_count
                cra_response.items_verified = (cra_response.items_verified or 0) + verified_count
                cra_response.items_updated = (cra_response.items_updated or 0) + updated_count
            
            event = CaseEvent(
                case_id=cra_response.case_id if cra_response else None,
                event_type='analysis_applied',
                description=f'Applied AI analysis: {len(updates_made)} items updated',
                event_data=json.dumps({
                    'cra_response_id': response_id,
                    'ocr_record_id': ocr_record_id,
                    'updates_applied': result.get('updates_applied', 0),
                    'violations_created': result.get('violations_created', 0),
                    'applied_by': staff_user
                })
            )
            db.add(event)
            db.commit()
            
            print(f"✅ Analysis applied for response {response_id}: {result.get('updates_applied', 0)} updates")
        
        return jsonify(result)
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/cra-response/list')
def api_list_cra_responses():
    """Get all CRA responses with analysis status for dashboard."""
    db = get_db()
    try:
        from database import CRAResponseOCR
        
        responses = db.query(CRAResponse).order_by(CRAResponse.created_at.desc()).limit(100).all()
        
        response_list = []
        for r in responses:
            ocr_record = db.query(CRAResponseOCR).filter(
                CRAResponseOCR.client_id == r.client_id,
                CRAResponseOCR.bureau == r.bureau
            ).order_by(CRAResponseOCR.created_at.desc()).first()
            
            client = db.query(Client).filter_by(id=r.client_id).first()
            
            response_list.append({
                'id': r.id,
                'clientId': r.client_id,
                'clientName': client.name if client else 'Unknown',
                'bureau': r.bureau,
                'disputeRound': r.dispute_round,
                'responseType': r.response_type,
                'responseDate': r.response_date.isoformat() if r.response_date else None,
                'fileName': r.file_name,
                'filePath': r.file_path,
                'itemsVerified': r.items_verified,
                'itemsDeleted': r.items_deleted,
                'itemsUpdated': r.items_updated,
                'hasAnalysis': ocr_record is not None,
                'analysisReviewed': ocr_record.reviewed if ocr_record else False,
                'ocrRecordId': ocr_record.id if ocr_record else None,
                'confidenceScore': ocr_record.ocr_confidence if ocr_record else None,
                'createdAt': r.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'responses': response_list
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# DISPUTE ROUND AUTOMATION ENDPOINTS
# ============================================================

@app.route('/api/dispute/advance-round', methods=['POST'])
def api_advance_dispute_round():
    """
    Advance a client to the next dispute round.
    Creates CRA response deadlines for each bureau.
    """
    db = get_db()
    try:
        data = request.json
        client_id = data.get('client_id')
        new_round = int(data.get('new_round', 1))
        
        if not client_id:
            return jsonify({'success': False, 'error': 'Client ID is required'}), 400
        
        if new_round < 1 or new_round > 4:
            return jsonify({'success': False, 'error': 'Round must be between 1 and 4'}), 400
        
        client = db.query(Client).filter_by(id=int(client_id)).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        old_round = client.current_dispute_round or 0
        client.current_dispute_round = new_round
        client.round_started_at = datetime.utcnow()
        client.dispute_status = 'active'
        
        from services.deadline_service import create_deadline
        from datetime import date
        bureaus = ['Experian', 'TransUnion', 'Equifax']
        created_deadlines = []
        
        for bureau in bureaus:
            try:
                deadline = create_deadline(
                    db=db,
                    client_id=int(client_id),
                    case_id=None,
                    deadline_type='cra_response',
                    bureau=bureau,
                    dispute_round=new_round,
                    start_date=date.today(),
                    days_allowed=30
                )
                created_deadlines.append({
                    'id': deadline.id,
                    'bureau': bureau,
                    'deadline_date': deadline.deadline_date.isoformat()
                })
            except Exception as dl_err:
                print(f"⚠️  Failed to create deadline for {bureau}: {dl_err}")
        
        case = db.query(Case).filter_by(client_id=int(client_id)).first()
        if case:
            event = CaseEvent(
                case_id=case.id,
                event_type='round_advanced',
                description=f'Dispute round advanced from {old_round} to {new_round}',
                event_data=json.dumps({
                    'client_id': int(client_id),
                    'old_round': old_round,
                    'new_round': new_round,
                    'deadlines_created': len(created_deadlines)
                })
            )
            db.add(event)
        
        db.commit()
        
        print(f"✅ Client {client_id} advanced to round {new_round}. Created {len(created_deadlines)} deadlines.")
        
        return jsonify({
            'success': True,
            'client_id': int(client_id),
            'old_round': old_round,
            'new_round': new_round,
            'deadlines_created': created_deadlines,
            'message': f'Successfully advanced to Round {new_round}'
        }), 200
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/dispute/check-round-complete', methods=['GET', 'POST'])
def api_check_round_complete():
    """
    Check if a dispute round is complete (all 3 bureaus responded).
    Returns completion status and recommended next action.
    """
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.json
            client_id = data.get('client_id')
            dispute_round = data.get('dispute_round')
        else:
            client_id = request.args.get('client_id')
            dispute_round = request.args.get('dispute_round')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'Client ID is required'}), 400
        
        client = db.query(Client).filter_by(id=int(client_id)).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        if not dispute_round:
            dispute_round = client.current_dispute_round or 1
        else:
            dispute_round = int(dispute_round)
        
        result = check_round_complete_internal(db, int(client_id), dispute_round)
        result['success'] = True
        result['client_name'] = client.name
        
        return jsonify(result), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/dispute/round-summary')
def api_dispute_round_summary():
    """
    Get summary of all clients' dispute round status for the dashboard.
    Shows clients ready to advance and clients with incomplete rounds.
    """
    db = get_db()
    try:
        clients = db.query(Client).filter(
            Client.current_dispute_round > 0,
            Client.dispute_status.in_(['active', 'waiting_response'])
        ).all()
        
        clients_ready_to_advance = []
        clients_incomplete_rounds = []
        
        for client in clients:
            dispute_round = client.current_dispute_round
            round_status = check_round_complete_internal(db, client.id, dispute_round)
            
            client_info = {
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'current_round': dispute_round,
                'dispute_status': client.dispute_status,
                'round_started_at': client.round_started_at.isoformat() if client.round_started_at else None,
                'bureaus_responded': round_status.get('bureaus_responded', []),
                'bureaus_missing': round_status.get('bureaus_missing', []),
                'total_deleted': round_status.get('total_deleted', 0),
                'total_verified': round_status.get('total_verified', 0),
                'success_rate': round_status.get('success_rate', 0),
                'round_complete': round_status.get('round_complete', False),
                'next_action': round_status.get('next_action')
            }
            
            if round_status.get('round_complete'):
                clients_ready_to_advance.append(client_info)
            else:
                clients_incomplete_rounds.append(client_info)
        
        from datetime import date
        active_deadlines = db.query(CaseDeadline).filter(
            CaseDeadline.status == 'active',
            CaseDeadline.deadline_type == 'cra_response'
        ).count()
        
        overdue_deadlines = db.query(CaseDeadline).filter(
            CaseDeadline.status == 'active',
            CaseDeadline.deadline_type == 'cra_response',
            CaseDeadline.deadline_date < date.today()
        ).count()
        
        return jsonify({
            'success': True,
            'ready_to_advance': clients_ready_to_advance,
            'incomplete_rounds': clients_incomplete_rounds,
            'stats': {
                'total_active_clients': len(clients),
                'ready_count': len(clients_ready_to_advance),
                'incomplete_count': len(clients_incomplete_rounds),
                'active_deadlines': active_deadlines,
                'overdue_deadlines': overdue_deadlines
            }
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/dispute/client/<int:client_id>/round-history')
def api_client_round_history(client_id):
    """Get dispute round history for a specific client"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        round_history = []
        for round_num in range(1, 5):
            responses = db.query(CRAResponse).filter(
                CRAResponse.client_id == client_id,
                CRAResponse.dispute_round == round_num
            ).all()
            
            if responses:
                round_data = {
                    'round': round_num,
                    'bureaus': {},
                    'total_deleted': 0,
                    'total_verified': 0,
                    'total_updated': 0
                }
                
                for resp in responses:
                    round_data['bureaus'][resp.bureau] = {
                        'response_type': resp.response_type,
                        'response_date': resp.response_date.isoformat() if resp.response_date else None,
                        'items_deleted': resp.items_deleted or 0,
                        'items_verified': resp.items_verified or 0,
                        'items_updated': resp.items_updated or 0
                    }
                    round_data['total_deleted'] += resp.items_deleted or 0
                    round_data['total_verified'] += resp.items_verified or 0
                    round_data['total_updated'] += resp.items_updated or 0
                
                total_items = round_data['total_deleted'] + round_data['total_verified'] + round_data['total_updated']
                round_data['success_rate'] = (round_data['total_deleted'] / total_items * 100) if total_items > 0 else 0
                round_data['is_complete'] = len(round_data['bureaus']) >= 3
                
                round_history.append(round_data)
        
        return jsonify({
            'success': True,
            'client_id': client_id,
            'client_name': client.name,
            'current_round': client.current_dispute_round,
            'dispute_status': client.dispute_status,
            'round_history': round_history
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/dashboard/import')
@require_staff(roles=['admin', 'paralegal'])
def dashboard_import():
    """Admin page for importing existing clients"""
    return render_template('client_import.html')


@app.route('/api/credit-analysis/generate/<int:client_id>', methods=['POST'])
def api_generate_credit_analysis(client_id):
    """Generate a basic credit analysis PDF for a client"""
    db = get_db()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        data = request.json or {}
        
        credit_scores = {
            'equifax': data.get('equifax_score', '-'),
            'experian': data.get('experian_score', '-'),
            'transunion': data.get('transunion_score', '-')
        }
        
        negative_items = data.get('negative_items', [])
        
        report_date = datetime.now().strftime("%B %d, %Y")
        
        os.makedirs('generated_pdfs', exist_ok=True)
        safe_name = client.name.replace(' ', '_').lower()
        output_path = f"generated_pdfs/credit_analysis_{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        generator = CreditAnalysisPDFGenerator()
        pdf_path = generator.generate_credit_analysis_pdf(
            client_name=client.name,
            report_date=report_date,
            credit_scores=credit_scores,
            negative_items=negative_items,
            output_path=output_path
        )
        
        return jsonify({
            'success': True,
            'pdf_path': pdf_path,
            'client_name': client.name,
            'generated_at': report_date
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/credit-analysis/download/<path:filename>')
def download_credit_analysis(filename):
    """Download a generated credit analysis PDF"""
    return send_file(
        f"generated_pdfs/{filename}",
        as_attachment=True,
        mimetype='application/pdf'
    )


@app.route('/api/import/template')
def api_import_template():
    """Download CSV template for bulk import"""
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'first_name', 'last_name', 'email', 'phone',
        'address_street', 'address_city', 'address_state', 'address_zip',
        'date_of_birth', 'ssn_last_4', 'credit_service',
        'current_round', 'current_step', 'dispute_status',
        'legacy_system_id', 'legacy_case_number', 'import_notes'
    ])
    writer.writerow([
        'John', 'Doe', 'john@example.com', '(555) 123-4567',
        '123 Main St', 'New York', 'NY', '10001',
        '1985-06-15', '1234', 'IdentityIQ.com',
        '2', 'waiting_response', 'active',
        'CMM-12345', 'CASE-001', 'Transferred from CMM'
    ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='client_import_template.csv'
    )


@app.route('/api/client/import/bulk', methods=['POST'])
def api_client_import_bulk():
    """Bulk import clients from CSV file"""
    import csv
    import io
    
    db = get_db()
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'success': False, 'error': 'CSV file is required'}), 400
        
        content = file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        
        results = []
        imported = 0
        failed = 0
        
        for row in reader:
            try:
                name = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
                if not name or name == ' ':
                    results.append({'name': 'Unknown', 'success': False, 'error': 'Name required'})
                    failed += 1
                    continue
                
                from datetime import date
                dob_str = row.get('date_of_birth', '')
                dob = None
                if dob_str:
                    try:
                        dob = date.fromisoformat(dob_str)
                    except:
                        pass
                
                referral_code = 'BP' + secrets.token_hex(4).upper()
                portal_token = secrets.token_urlsafe(32)
                
                client = Client(
                    name=name,
                    first_name=row.get('first_name', ''),
                    last_name=row.get('last_name', ''),
                    email=row.get('email', ''),
                    phone=row.get('phone', ''),
                    address_street=row.get('address_street', ''),
                    address_city=row.get('address_city', ''),
                    address_state=row.get('address_state', ''),
                    address_zip=row.get('address_zip', ''),
                    ssn_last_four=row.get('ssn_last_4', ''),
                    date_of_birth=dob,
                    credit_monitoring_service=row.get('credit_service', ''),
                    current_dispute_round=int(row.get('current_round', 1)),
                    current_dispute_step=row.get('current_step', ''),
                    dispute_status=row.get('dispute_status', 'active'),
                    legacy_system_id=row.get('legacy_system_id', ''),
                    legacy_case_number=row.get('legacy_case_number', ''),
                    imported_at=datetime.utcnow(),
                    import_notes=row.get('import_notes', ''),
                    referral_code=referral_code,
                    portal_token=portal_token,
                    status='active',
                    signup_completed=True,
                    agreement_signed=True
                )
                
                db.add(client)
                db.flush()
                
                case_number = generate_case_number()
                case = Case(
                    client_id=client.id,
                    case_number=case_number,
                    status='intake',
                    pricing_tier='tier1',
                    portal_token=portal_token,
                    intake_at=datetime.utcnow()
                )
                db.add(case)
                
                results.append({'name': name, 'success': True, 'caseNumber': case_number})
                imported += 1
                
            except Exception as row_error:
                results.append({'name': row.get('first_name', 'Unknown'), 'success': False, 'error': str(row_error)})
                failed += 1
        
        db.commit()
        
        return jsonify({
            'success': True,
            'imported': imported,
            'failed': failed,
            'results': results
        }), 200
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/referral', methods=['POST'])
def api_submit_referral():
    """Submit a client referral"""
    db = get_db()
    try:
        data = request.json
        
        referring_client_id = data.get('referringClientId')
        referred_name = data.get('referredName', '').strip()
        referred_email = data.get('referredEmail', '').strip()
        referred_phone = data.get('referredPhone', '').strip()
        comments = data.get('comments', '').strip()
        
        if not referred_name or not referred_email:
            return jsonify({'success': False, 'error': 'Name and email are required'}), 400
        
        referral = ClientReferral(
            referring_client_id=int(referring_client_id) if referring_client_id else None,
            referred_name=referred_name,
            referred_email=referred_email,
            referred_phone=referred_phone,
            status='pending'
        )
        
        db.add(referral)
        db.commit()
        
        return jsonify({
            'success': True,
            'referralId': referral.id,
            'message': 'Referral submitted successfully! We will reach out to them soon.'
        }), 201
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# MANUAL REVIEW INTERFACE ENDPOINTS
# ============================================================

@app.route('/analysis/<int:analysis_id>/review')
def analysis_review_page(analysis_id):
    """Render the manual review interface for an analysis"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'error': 'Analysis not found'}), 404
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        
        return render_template('analysis_review.html',
            analysis=analysis,
            violations=violations,
            standing=standing,
            damages=damages,
            score=score
        )
    finally:
        db.close()


@app.route('/api/violation', methods=['POST'])
def api_add_violation():
    """Add a new violation manually"""
    db = get_db()
    try:
        data = request.json
        
        analysis_id = data.get('analysis_id')
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404
        
        violation = Violation(
            analysis_id=analysis_id,
            client_id=analysis.client_id,
            bureau=data.get('bureau', 'Unknown'),
            account_name=data.get('account_name', 'Unknown Account'),
            fcra_section=data.get('fcra_section', '611'),
            violation_type=data.get('violation_type', 'Unknown'),
            description=data.get('description', ''),
            statutory_damages_min=float(data.get('statutory_damages_min', 100)),
            statutory_damages_max=float(data.get('statutory_damages_max', 1000)),
            is_willful=bool(data.get('is_willful', False)),
            willfulness_notes=data.get('willfulness_notes', '')
        )
        
        db.add(violation)
        db.commit()
        db.refresh(violation)
        
        return jsonify({
            'success': True,
            'violation_id': violation.id,
            'message': 'Violation added successfully'
        }), 201
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/violation/<int:violation_id>', methods=['GET'])
def api_get_violation(violation_id):
    """Get a single violation"""
    db = get_db()
    try:
        violation = db.query(Violation).filter_by(id=violation_id).first()
        if not violation:
            return jsonify({'success': False, 'error': 'Violation not found'}), 404
        
        return jsonify({
            'success': True,
            'violation': {
                'id': violation.id,
                'analysis_id': violation.analysis_id,
                'bureau': violation.bureau,
                'account_name': violation.account_name,
                'fcra_section': violation.fcra_section,
                'violation_type': violation.violation_type,
                'description': violation.description,
                'statutory_damages_min': violation.statutory_damages_min,
                'statutory_damages_max': violation.statutory_damages_max,
                'is_willful': violation.is_willful,
                'willfulness_notes': violation.willfulness_notes
            }
        }), 200
    finally:
        db.close()


@app.route('/api/violation/<int:violation_id>', methods=['PUT'])
def api_update_violation(violation_id):
    """Update an existing violation"""
    db = get_db()
    try:
        violation = db.query(Violation).filter_by(id=violation_id).first()
        if not violation:
            return jsonify({'success': False, 'error': 'Violation not found'}), 404
        
        data = request.json
        
        if 'bureau' in data:
            violation.bureau = data['bureau']
        if 'account_name' in data:
            violation.account_name = data['account_name']
        if 'fcra_section' in data:
            violation.fcra_section = data['fcra_section']
        if 'violation_type' in data:
            violation.violation_type = data['violation_type']
        if 'description' in data:
            violation.description = data['description']
        if 'statutory_damages_min' in data:
            violation.statutory_damages_min = float(data['statutory_damages_min'])
        if 'statutory_damages_max' in data:
            violation.statutory_damages_max = float(data['statutory_damages_max'])
        if 'is_willful' in data:
            violation.is_willful = bool(data['is_willful'])
        if 'willfulness_notes' in data:
            violation.willfulness_notes = data['willfulness_notes']
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Violation updated'}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/violation/<int:violation_id>', methods=['DELETE'])
def api_delete_violation(violation_id):
    """Delete a violation"""
    db = get_db()
    try:
        violation = db.query(Violation).filter_by(id=violation_id).first()
        if not violation:
            return jsonify({'success': False, 'error': 'Violation not found'}), 404
        
        db.delete(violation)
        db.commit()
        
        return jsonify({'success': True, 'message': 'Violation deleted'}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/standing', methods=['PUT'])
def api_update_standing(analysis_id):
    """Update standing data for an analysis"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404
        
        data = request.json
        
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        
        if not standing:
            standing = Standing(
                analysis_id=analysis_id,
                client_id=analysis.client_id
            )
            db.add(standing)
        
        standing.has_concrete_harm = bool(data.get('has_concrete_harm', False))
        standing.concrete_harm_type = data.get('concrete_harm_type', '')
        standing.concrete_harm_details = data.get('concrete_harm_details', '')
        standing.has_dissemination = bool(data.get('has_dissemination', False))
        standing.dissemination_details = data.get('dissemination_details', '')
        standing.has_causation = bool(data.get('has_causation', False))
        standing.causation_details = data.get('causation_details', '')
        standing.denial_letters_count = int(data.get('denial_letters_count', 0))
        standing.adverse_action_notices_count = int(data.get('adverse_action_notices_count', 0))
        standing.standing_verified = True
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Standing updated'}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/analysis/<int:analysis_id>/damages', methods=['PUT'])
def api_update_damages(analysis_id):
    """Update damages data and recalculate totals"""
    db = get_db()
    try:
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404
        
        data = request.json
        
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        
        if not damages:
            damages = Damages(
                analysis_id=analysis_id,
                client_id=analysis.client_id
            )
            db.add(damages)
        
        damages.credit_denials_amount = float(data.get('credit_denials_amount', 0))
        damages.higher_interest_amount = float(data.get('higher_interest_amount', 0))
        damages.credit_monitoring_amount = float(data.get('credit_monitoring_amount', 0))
        damages.time_stress_amount = float(data.get('time_stress_amount', 0))
        damages.other_actual_amount = float(data.get('other_actual_amount', 0))
        damages.notes = data.get('notes', '')
        
        damages.actual_damages_total = (
            damages.credit_denials_amount +
            damages.higher_interest_amount +
            damages.credit_monitoring_amount +
            damages.time_stress_amount +
            damages.other_actual_amount
        )
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        violations_data = [{
            'fcra_section': v.fcra_section,
            'is_willful': v.is_willful,
            'violation_type': v.violation_type
        } for v in violations]
        
        actual_damages_input = {
            'credit_denials': damages.credit_denials_amount,
            'higher_interest': damages.higher_interest_amount,
            'credit_monitoring': damages.credit_monitoring_amount,
            'time_stress': damages.time_stress_amount,
            'other': damages.other_actual_amount,
            'notes': damages.notes
        }
        damages_calc = calculate_damages(violations_data, actual_damages_input)
        
        damages.statutory_damages_total = damages_calc['statutory']['total']
        damages.section_605b_count = damages_calc['statutory']['605b']['count']
        damages.section_605b_amount = damages_calc['statutory']['605b']['amount']
        damages.section_607b_count = damages_calc['statutory']['607b']['count']
        damages.section_607b_amount = damages_calc['statutory']['607b']['amount']
        damages.section_611_count = damages_calc['statutory']['611']['count']
        damages.section_611_amount = damages_calc['statutory']['611']['amount']
        damages.section_623_count = damages_calc['statutory']['623']['count']
        damages.section_623_amount = damages_calc['statutory']['623']['amount']
        damages.willfulness_multiplier = damages_calc['punitive']['multiplier']
        damages.punitive_damages_amount = damages_calc['punitive']['amount']
        damages.estimated_hours = damages_calc['attorney_fees']['estimated_hours']
        damages.hourly_rate = damages_calc['attorney_fees']['hourly_rate']
        damages.attorney_fees_projection = damages_calc['attorney_fees']['total']
        damages.total_exposure = damages_calc['settlement']['total_exposure']
        damages.settlement_target = damages_calc['settlement']['target']
        damages.minimum_acceptable = damages_calc['settlement']['minimum']
        
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        standing_data = {
            'has_concrete_harm': standing.has_concrete_harm if standing else False,
            'has_dissemination': standing.has_dissemination if standing else False,
            'has_causation': standing.has_causation if standing else False,
            'denial_letters_count': standing.denial_letters_count if standing else 0
        }
        documentation_complete = len(violations_data) > 0 and standing is not None
        
        score_data = calculate_case_score(standing_data, violations_data, damages_calc, documentation_complete)
        
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        if not case_score:
            case_score = CaseScore(analysis_id=analysis_id, client_id=analysis.client_id)
            db.add(case_score)
        
        case_score.total_score = score_data['total']
        case_score.standing_score = score_data['standing']
        case_score.violation_quality_score = score_data['violation_quality']
        case_score.willfulness_score = score_data['willfulness']
        case_score.documentation_score = score_data['documentation']
        case_score.settlement_probability = score_data['settlement_probability']
        case_score.case_strength = score_data['case_strength']
        case_score.recommendation = score_data['recommendation']
        case_score.recommendation_notes = '\n'.join(score_data['notes'])
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Damages updated and scores recalculated'}), 200
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# ENHANCED DOCUMENT GENERATION ENDPOINTS
# ============================================================

@app.route('/api/generate/client-report/<int:analysis_id>', methods=['POST'])
def api_generate_client_report(analysis_id):
    """Generate comprehensive 40-50 page client report"""
    db = get_db()
    try:
        from services.pdf.client_report import ClientReportBuilder
        
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        
        client_data = {
            'client_name': analysis.client_name,
            'report_date': datetime.now().strftime("%B %d, %Y"),
            'dispute_round': analysis.dispute_round,
            'credit_scores': {},
            'violations': [{
                'id': v.id,
                'bureau': v.bureau,
                'account_name': v.account_name,
                'fcra_section': v.fcra_section,
                'violation_type': v.violation_type,
                'description': v.description,
                'statutory_damages_min': v.statutory_damages_min,
                'statutory_damages_max': v.statutory_damages_max,
                'is_willful': v.is_willful,
                'willfulness_notes': v.willfulness_notes
            } for v in violations],
            'standing': {
                'has_concrete_harm': standing.has_concrete_harm if standing else False,
                'concrete_harm_type': standing.concrete_harm_type if standing else '',
                'concrete_harm_details': standing.concrete_harm_details if standing else '',
                'has_dissemination': standing.has_dissemination if standing else False,
                'dissemination_details': standing.dissemination_details if standing else '',
                'has_causation': standing.has_causation if standing else False,
                'causation_details': standing.causation_details if standing else '',
                'denial_letters_count': standing.denial_letters_count if standing else 0,
                'adverse_action_notices_count': standing.adverse_action_notices_count if standing else 0
            } if standing else None,
            'damages': {
                'actual_damages_total': damages.actual_damages_total if damages else 0,
                'statutory_damages_total': damages.statutory_damages_total if damages else 0,
                'punitive_damages_amount': damages.punitive_damages_amount if damages else 0,
                'total_exposure': damages.total_exposure if damages else 0,
                'settlement_target': damages.settlement_target if damages else 0,
                'minimum_acceptable': damages.minimum_acceptable if damages else 0,
                'credit_denials_amount': damages.credit_denials_amount if damages else 0,
                'higher_interest_amount': damages.higher_interest_amount if damages else 0,
                'credit_monitoring_amount': damages.credit_monitoring_amount if damages else 0,
                'time_stress_amount': damages.time_stress_amount if damages else 0,
                'other_actual_amount': damages.other_actual_amount if damages else 0,
                'section_605b_count': damages.section_605b_count if damages else 0,
                'section_605b_amount': damages.section_605b_amount if damages else 0,
                'section_607b_count': damages.section_607b_count if damages else 0,
                'section_607b_amount': damages.section_607b_amount if damages else 0,
                'section_611_count': damages.section_611_count if damages else 0,
                'section_611_amount': damages.section_611_amount if damages else 0,
                'section_623_count': damages.section_623_count if damages else 0,
                'section_623_amount': damages.section_623_amount if damages else 0,
                'attorney_fees_projection': damages.attorney_fees_projection if damages else 0,
                'notes': damages.notes if damages else ''
            } if damages else None,
            'case_score': {
                'total_score': case_score.total_score if case_score else 0,
                'case_strength': case_score.case_strength if case_score else 'Unknown',
                'standing_score': case_score.standing_score if case_score else 0,
                'violation_quality_score': case_score.violation_quality_score if case_score else 0,
                'willfulness_score': case_score.willfulness_score if case_score else 0,
                'documentation_score': case_score.documentation_score if case_score else 0,
                'settlement_probability': case_score.settlement_probability if case_score else 0,
                'recommendation': case_score.recommendation if case_score else 'pending'
            } if case_score else None
        }
        
        os.makedirs('static/generated_reports', exist_ok=True)
        safe_name = analysis.client_name.replace(' ', '_')
        filename = f"{safe_name}_Client_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = f"static/generated_reports/{filename}"
        
        builder = ClientReportBuilder()
        builder.generate(output_path, client_data)
        
        doc = Document(
            case_id=None,
            analysis_id=analysis_id,
            document_type='client_report',
            filename=filename,
            file_path=output_path,
            file_size=os.path.getsize(output_path)
        )
        db.add(doc)
        db.commit()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': output_path,
            'document_id': doc.id
        }), 200
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/generate/internal-memo/<int:analysis_id>', methods=['POST'])
def api_generate_internal_memo(analysis_id):
    """Generate 3-5 page internal staff analysis memo"""
    db = get_db()
    try:
        from services.pdf.internal_memo import InternalMemoBuilder
        
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404
        
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        standing = db.query(Standing).filter_by(analysis_id=analysis_id).first()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        case_score = db.query(CaseScore).filter_by(analysis_id=analysis_id).first()
        
        case_data = {
            'client_name': analysis.client_name,
            'analysis_id': analysis.id,
            'dispute_round': analysis.dispute_round,
            'violations': [{
                'id': v.id,
                'bureau': v.bureau,
                'account_name': v.account_name,
                'fcra_section': v.fcra_section,
                'violation_type': v.violation_type,
                'description': v.description,
                'statutory_damages_min': v.statutory_damages_min,
                'statutory_damages_max': v.statutory_damages_max,
                'is_willful': v.is_willful,
                'willfulness_notes': v.willfulness_notes
            } for v in violations],
            'standing': {
                'has_concrete_harm': standing.has_concrete_harm if standing else False,
                'concrete_harm_type': standing.concrete_harm_type if standing else '',
                'has_dissemination': standing.has_dissemination if standing else False,
                'dissemination_details': standing.dissemination_details if standing else '',
                'has_causation': standing.has_causation if standing else False,
                'causation_details': standing.causation_details if standing else ''
            } if standing else None,
            'damages': {
                'actual_damages_total': damages.actual_damages_total if damages else 0,
                'statutory_damages_total': damages.statutory_damages_total if damages else 0,
                'punitive_damages_amount': damages.punitive_damages_amount if damages else 0,
                'total_exposure': damages.total_exposure if damages else 0,
                'settlement_target': damages.settlement_target if damages else 0,
                'minimum_acceptable': damages.minimum_acceptable if damages else 0,
                'attorney_fees_projection': damages.attorney_fees_projection if damages else 0
            } if damages else None,
            'case_score': {
                'total_score': case_score.total_score if case_score else 0,
                'case_strength': case_score.case_strength if case_score else 'Unknown',
                'standing_score': case_score.standing_score if case_score else 0,
                'violation_quality_score': case_score.violation_quality_score if case_score else 0,
                'willfulness_score': case_score.willfulness_score if case_score else 0,
                'documentation_score': case_score.documentation_score if case_score else 0,
                'settlement_probability': case_score.settlement_probability if case_score else 0,
                'recommendation': case_score.recommendation if case_score else 'pending'
            } if case_score else None
        }
        
        os.makedirs('static/generated_reports', exist_ok=True)
        safe_name = analysis.client_name.replace(' ', '_')
        filename = f"{safe_name}_Internal_Memo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        output_path = f"static/generated_reports/{filename}"
        
        builder = InternalMemoBuilder()
        builder.generate(output_path, case_data)
        
        doc = Document(
            case_id=None,
            analysis_id=analysis_id,
            document_type='internal_memo',
            filename=filename,
            file_path=output_path,
            file_size=os.path.getsize(output_path)
        )
        db.add(doc)
        db.commit()
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': output_path,
            'document_id': doc.id
        }), 200
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/generate/round-letters/<int:analysis_id>', methods=['POST'])
def api_generate_round_letters(analysis_id):
    """Generate round-specific dispute letters"""
    db = get_db()
    try:
        from services.pdf.round_letters import RoundLetterBuilder
        
        analysis = db.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            return jsonify({'success': False, 'error': 'Analysis not found'}), 404
        
        client = db.query(Client).filter_by(id=analysis.client_id).first()
        violations = db.query(Violation).filter_by(analysis_id=analysis_id).all()
        damages = db.query(Damages).filter_by(analysis_id=analysis_id).first()
        
        dispute_round = analysis.dispute_round
        
        client_data = {
            'client_name': client.name if client else analysis.client_name,
            'ssn_last_four': client.ssn_last_four if client else 'XXXX',
            'address': {
                'street': client.address_street if client else '',
                'city': client.address_city if client else '',
                'state': client.address_state if client else '',
                'zip': client.address_zip if client else ''
            } if client else {},
            'violations': [{
                'id': v.id,
                'bureau': v.bureau,
                'account_name': v.account_name,
                'fcra_section': v.fcra_section,
                'violation_type': v.violation_type,
                'description': v.description,
                'is_willful': v.is_willful
            } for v in violations],
            'damages': {
                'total_exposure': damages.total_exposure if damages else 0,
                'settlement_target': damages.settlement_target if damages else 0,
                'actual_damages_total': damages.actual_damages_total if damages else 0,
                'statutory_damages_total': damages.statutory_damages_total if damages else 0,
                'punitive_damages_amount': damages.punitive_damages_amount if damages else 0,
                'attorney_fees_projection': damages.attorney_fees_projection if damages else 0
            } if damages else None
        }
        
        os.makedirs('static/generated_letters', exist_ok=True)
        builder = RoundLetterBuilder()
        
        generated_letters = []
        bureaus = ['Equifax', 'Experian', 'TransUnion']
        
        for bureau in bureaus:
            safe_name = analysis.client_name.replace(' ', '_')
            filename = f"{safe_name}_{bureau}_R{dispute_round}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path = f"static/generated_letters/{filename}"
            
            if dispute_round == 1:
                builder.generate_round_1(output_path, client_data, bureau)
            elif dispute_round == 2:
                builder.generate_round_2(output_path, client_data, bureau)
            elif dispute_round == 3:
                builder.generate_round_3(output_path, client_data, bureau)
            elif dispute_round == 4:
                builder.generate_round_4(output_path, client_data, bureau)
            else:
                builder.generate_round_1(output_path, client_data, bureau)
            
            letter_record = DisputeLetter(
                analysis_id=analysis_id,
                client_id=analysis.client_id,
                client_name=analysis.client_name,
                bureau=bureau,
                round_number=dispute_round,
                letter_content=f"Round {dispute_round} letter generated",
                file_path=output_path
            )
            db.add(letter_record)
            
            generated_letters.append({
                'bureau': bureau,
                'filename': filename,
                'filepath': output_path
            })
        
        db.commit()
        
        return jsonify({
            'success': True,
            'round': dispute_round,
            'letters': generated_letters
        }), 200
        
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# DISPUTE ITEM & SECONDARY FREEZE API ENDPOINTS
# ============================================================

@app.route('/api/dispute-items/batch-update', methods=['POST'])
def api_batch_update_dispute_items():
    """Batch update dispute item comments from client portal"""
    db = get_db()
    try:
        data = request.json
        updates = data.get('updates', [])
        
        for update in updates:
            item_id = update.get('id')
            comments = update.get('comments', '')
            
            if item_id:
                item = db.query(DisputeItem).filter_by(id=item_id).first()
                if item:
                    item.comments = comments
                    item.updated_at = datetime.utcnow()
        
        db.commit()
        return jsonify({'success': True, 'updated': len(updates)}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/secondary-freezes/batch-update', methods=['POST'])
def api_batch_update_secondary_freezes():
    """Batch update secondary bureau freeze status from client portal"""
    db = get_db()
    try:
        data = request.json
        updates = data.get('updates', [])
        
        for update in updates:
            freeze_id = update.get('id')
            status = update.get('status', 'pending')
            comments = update.get('comments', '')
            
            if freeze_id:
                freeze = db.query(SecondaryBureauFreeze).filter_by(id=freeze_id).first()
                if freeze:
                    freeze.status = status
                    freeze.comments = comments
                    freeze.updated_at = datetime.utcnow()
                    
                    if status == 'frozen' and not freeze.freeze_confirmed_at:
                        freeze.freeze_confirmed_at = datetime.utcnow()
        
        db.commit()
        return jsonify({'success': True, 'updated': len(updates)}), 200
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# CONTACT LIST MANAGEMENT ENDPOINTS
# ============================================================

@app.route('/dashboard/contacts')
@require_staff(roles=['admin', 'paralegal', 'attorney'])
def dashboard_contacts():
    """Enhanced contact list page with CRM features"""
    db = get_db()
    try:
        filter_type = request.args.get('filter', 'all')
        page = int(request.args.get('page', 1))
        rows_per_page = request.args.get('rows', '25')
        
        query = db.query(Client)
        
        if filter_type == 'mark1':
            query = query.filter(Client.mark_1 == True)
        elif filter_type == 'mark2':
            query = query.filter(Client.mark_2 == True)
        elif filter_type == 'affiliates':
            query = query.filter(Client.is_affiliate == True)
        elif filter_type == 'active':
            query = query.filter(Client.client_type == 'C')
        elif filter_type == 'leads':
            query = query.filter(Client.client_type == 'L')
        elif filter_type == 'follow_up':
            query = query.filter(Client.follow_up_date != None)
        elif filter_type == 'signups':
            query = query.filter(Client.signup_completed == True)
        elif filter_type == 'last25':
            query = query.order_by(Client.created_at.desc()).limit(25)
            contacts = query.all()
            return render_template('contacts.html', 
                                 contacts=contacts, 
                                 filter=filter_type,
                                 page=1,
                                 total_pages=1,
                                 total_contacts=len(contacts),
                                 rows_per_page=25)
        
        total_contacts = query.count()
        
        if rows_per_page == 'all':
            contacts = query.order_by(Client.created_at.desc()).all()
            total_pages = 1
            rows_per_page_int = total_contacts
        else:
            rows_per_page_int = int(rows_per_page)
            total_pages = max(1, (total_contacts + rows_per_page_int - 1) // rows_per_page_int)
            offset = (page - 1) * rows_per_page_int
            contacts = query.order_by(Client.created_at.desc()).offset(offset).limit(rows_per_page_int).all()
        
        return render_template('contacts.html',
                             contacts=contacts,
                             filter=filter_type,
                             page=page,
                             total_pages=total_pages,
                             total_contacts=total_contacts,
                             rows_per_page=rows_per_page)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('contacts.html',
                             contacts=[],
                             filter='all',
                             page=1,
                             total_pages=1,
                             total_contacts=0,
                             rows_per_page=25)
    finally:
        db.close()


@app.route('/dashboard/automation-tools')
@require_staff(roles=['admin', 'paralegal'])
def dashboard_automation_tools():
    """Automation tools dashboard page"""
    db = get_db()
    try:
        clients = db.query(Client).order_by(Client.first_name).all()
        return render_template('automation_tools.html', clients=clients)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('automation_tools.html', clients=[])
    finally:
        db.close()


@app.route('/api/freeze-letters/generate', methods=['POST'])
def api_generate_freeze_letters():
    """Generate freeze letters for selected bureaus"""
    db = get_db()
    try:
        data = request.json
        client_id = data.get('client_id')
        bureaus = data.get('bureaus', [])
        
        if not client_id:
            return jsonify({'success': False, 'error': 'Client ID is required'}), 400
        if not bureaus:
            return jsonify({'success': False, 'error': 'At least one bureau must be selected'}), 400
        
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        bureau_name_map = {
            'equifax': 'Equifax',
            'experian': 'Experian',
            'transunion': 'TransUnion',
            'innovis': 'Innovis',
            'chexsystems': 'ChexSystems',
            'clarity_services': 'Clarity Services Inc',
            'lexisnexis': 'LexisNexis',
            'corelogic': 'CoreLogic Teletrack',
            'factor_trust': 'Factor Trust Inc',
            'microbilt': 'MicroBilt/PRBC',
            'lexisnexis_risk': 'LexisNexis Risk Solutions',
            'datax': 'DataX Ltd'
        }
        
        mapped_bureaus = [bureau_name_map.get(b, b) for b in bureaus]
        
        from services.freeze_letter_service import generate_freeze_letters
        result = generate_freeze_letters(client_id, mapped_bureaus)
        
        if result.get('success'):
            return jsonify({
                'success': True,
                'batch_id': result.get('batch_id'),
                'pdf_path': result.get('pdf_path'),
                'bureaus_count': len(mapped_bureaus)
            })
        else:
            return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/freeze-letters/recent', methods=['GET'])
def api_get_recent_freeze_letters():
    """Get recent freeze letter batches"""
    db = get_db()
    try:
        from database import FreezeLetterBatch
        batches = db.query(FreezeLetterBatch).order_by(FreezeLetterBatch.created_at.desc()).limit(20).all()
        
        result = []
        for batch in batches:
            client = db.query(Client).filter_by(id=batch.client_id).first()
            result.append({
                'id': batch.batch_uuid,
                'client_name': client.name if client else f'Client {batch.client_id}',
                'created_at': batch.created_at.isoformat() if batch.created_at else None,
                'bureaus': batch.bureaus_included or [],
                'status': batch.status or 'generated'
            })
        
        return jsonify({'success': True, 'batches': result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': True, 'batches': []})
    finally:
        db.close()


@app.route('/api/freeze-letters/download/<batch_id>')
def api_download_freeze_letters(batch_id):
    """Download freeze letters PDF or DOCX"""
    db = get_db()
    try:
        from database import FreezeLetterBatch
        batch = db.query(FreezeLetterBatch).filter_by(batch_uuid=batch_id).first()
        
        if not batch:
            return jsonify({'success': False, 'error': 'Batch not found'}), 404
        
        file_format = request.args.get('format', 'pdf').lower()
        
        if file_format == 'docx':
            if batch.generated_docx_path and os.path.exists(batch.generated_docx_path):
                return send_file(batch.generated_docx_path, as_attachment=True)
            elif batch.generated_pdf_path:
                docx_path = batch.generated_pdf_path.replace('.pdf', '.docx')
                if os.path.exists(docx_path):
                    return send_file(docx_path, as_attachment=True)
            return jsonify({'success': False, 'error': 'Word document not found'}), 404
        else:
            if batch.generated_pdf_path and os.path.exists(batch.generated_pdf_path):
                return send_file(batch.generated_pdf_path, as_attachment=True)
            return jsonify({'success': False, 'error': 'PDF not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/action-plan/generate/<int:client_id>', methods=['POST'])
def api_generate_action_plan(client_id):
    """Generate a branded Action Plan PDF for a client"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        data = request.json or {}
        
        from services.pdf.brightpath_builder import create_action_plan_pdf
        from datetime import datetime, timedelta
        
        client_name = client.name or f"{client.first_name or ''} {client.last_name or ''}".strip()
        
        case = db.query(Case).filter_by(client_id=client_id).first()
        
        hearing_date = data.get('hearing_date', (datetime.now() + timedelta(days=21)).strftime('%B %d, %Y'))
        fcra_value = "$56,000 - $76,000 (estimated)"
        if case and case.total_potential_damages:
            low = int(case.total_potential_damages * 0.8)
            high = int(case.total_potential_damages * 1.2)
            fcra_value = f"${low:,} - ${high:,} (estimated)"
        
        case_info = {
            'plaintiff': data.get('plaintiff', 'N/A'),
            'defendant': client_name,
            'amount': data.get('amount_claimed', 'N/A'),
            'court': data.get('court', 'N/A'),
            'case_number': data.get('case_number', ''),
            'hearing_date': hearing_date,
            'fcra_value': fcra_value
        }
        
        critical_deadline = data.get('critical_deadline')
        deadlines = [f"CRITICAL DEADLINE: {critical_deadline}"] if critical_deadline else []
        
        base_date = datetime.now()
        week1_tasks = data.get('week1_tasks', [
            {'text': 'File Notice of Intent to Defend at courthouse', 'checked': False, 'date': (base_date + timedelta(days=2)).strftime('%b %d')},
            {'text': 'Mail Demand Letter to Plaintiff\'s attorneys (certified)', 'checked': False, 'date': (base_date + timedelta(days=2)).strftime('%b %d')},
            {'text': 'Mail MOV Demand (certified)', 'checked': False, 'date': (base_date + timedelta(days=2)).strftime('%b %d')},
            {'text': 'Organize all credit reports and documents', 'checked': False, 'date': (base_date + timedelta(days=3)).strftime('%b %d')},
            {'text': 'Review and prepare Answer with Affirmative Defenses', 'checked': False, 'date': (base_date + timedelta(days=4)).strftime('%b %d')},
        ])
        
        week2_tasks = data.get('week2_tasks', [
            {'text': 'File Answer with Affirmative Defenses at courthouse', 'checked': False, 'date': (base_date + timedelta(days=7)).strftime('%b %d')},
            {'text': 'Prepare evidence binder (organized by violation)', 'checked': False, 'date': (base_date + timedelta(days=8)).strftime('%b %d')},
            {'text': 'Practice presenting your case (5-10 minutes)', 'checked': False, 'date': (base_date + timedelta(days=8)).strftime('%b %d')},
            {'text': 'Review questions to ask at hearing', 'checked': False, 'date': (base_date + timedelta(days=9)).strftime('%b %d')},
            {'text': 'Confirm hearing time and location', 'checked': False, 'date': (base_date + timedelta(days=9)).strftime('%b %d')},
        ])
        
        hearing_tasks = data.get('hearing_tasks', [
            {'text': 'Arrive 30 minutes early', 'checked': False},
            {'text': 'Bring evidence binder and all documents', 'checked': False},
            {'text': 'Dress professionally (business casual minimum)', 'checked': False},
            {'text': 'Turn off cell phone before entering courtroom', 'checked': False},
            {'text': 'Address judge as \'Your Honor\'', 'checked': False},
        ])
        
        what_to_bring = data.get('what_to_bring', [
            'All 3 credit reports (Experian, TransUnion, Equifax)',
            'Notice of Intent to Defend (filed copy)',
            'Answer with Affirmative Defenses (filed copy)',
            'Demand Letter to attorneys (copy + certified mail receipt)',
            'MOV Demand (copy + certified mail receipt)',
            'Any responses received',
            'Government-issued photo ID',
            'Pen and notepad for notes'
        ])
        
        costs = data.get('costs', [
            ('Filing Notice of Intent to Defend', '$0 - $25'),
            ('Certified Mail (Demand Letter)', '$8 - $12'),
            ('Certified Mail (MOV Demand)', '$8 - $12'),
            ('Filing Answer', '$0 - $25'),
            ('TOTAL ESTIMATED', '$16 - $74')
        ])
        
        output_dir = 'generated_documents/action_plans'
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        client_name_safe = client_name.replace(' ', '_').replace('/', '_')[:50]
        output_path = os.path.join(output_dir, f"{client_name_safe}_Action_Plan_{timestamp}.pdf")
        
        pdf_path = create_action_plan_pdf(
            client_name=client_name,
            case_info=case_info,
            deadlines=deadlines,
            week1_tasks=week1_tasks,
            week2_tasks=week2_tasks,
            hearing_tasks=hearing_tasks,
            what_to_bring=what_to_bring,
            costs=costs,
            output_path=output_path
        )
        
        return jsonify({
            'success': True,
            'pdf_path': pdf_path,
            'message': f'Action Plan generated for {client_name}'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/action-plan/download/<path:filename>')
def api_download_action_plan(filename):
    """Download an action plan PDF"""
    try:
        filepath = os.path.join('generated_documents/action_plans', os.path.basename(filename))
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/scanner')
def scanner_page():
    """Mobile document scanner page"""
    return render_template('document_scanner.html')


@app.route('/portal/<token>/scanner')
def portal_scanner(token):
    """Client portal scanner - automatically links documents to client"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(portal_token=token).first()
        if not client:
            case = db.query(Case).filter_by(portal_token=token).first()
            if case:
                client = db.query(Client).filter_by(id=case.client_id).first()
        
        if not client:
            return "Invalid or expired access link", 404
        
        return render_template('document_scanner.html', 
                             client_id=client.id,
                             client_name=client.name,
                             portal_token=token,
                             is_portal=True)
    finally:
        db.close()


@app.route('/api/scanner/document-types', methods=['GET'])
def api_get_document_types():
    """Get supported document types for scanning"""
    from services.document_scanner_service import get_document_types
    return jsonify({'success': True, 'document_types': get_document_types()})


@app.route('/api/scanner/session/start', methods=['POST'])
def api_start_scan_session():
    """Start a new document scanning session"""
    from services.document_scanner_service import create_scan_session
    data = request.json or {}
    result = create_scan_session(
        client_id=data.get('client_id'),
        client_name=data.get('client_name'),
        document_type=data.get('document_type', 'credit_report')
    )
    return jsonify(result)


@app.route('/api/scanner/session/add-image', methods=['POST'])
def api_add_scan_image():
    """Add an image to an existing scan session"""
    from services.document_scanner_service import get_scan_session
    
    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400
    
    session = get_scan_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image provided'}), 400
    
    image_file = request.files['image']
    image_data = image_file.read()
    filename = image_file.filename or 'upload.jpg'
    
    result = session.add_image(image_data, filename)
    return jsonify(result)


@app.route('/api/scanner/session/remove-image', methods=['POST'])
def api_remove_scan_image():
    """Remove an image from a scan session"""
    from services.document_scanner_service import get_scan_session
    
    data = request.json or {}
    session_id = data.get('session_id')
    page_number = data.get('page_number')
    
    if not session_id or not page_number:
        return jsonify({'success': False, 'error': 'session_id and page_number required'}), 400
    
    session = get_scan_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    success = session.remove_image(page_number)
    return jsonify({'success': success})


@app.route('/api/scanner/session/status', methods=['GET'])
def api_scan_session_status():
    """Get status of a scan session"""
    from services.document_scanner_service import get_scan_session
    
    session_id = request.args.get('session_id')
    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400
    
    session = get_scan_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    return jsonify({'success': True, **session.get_status()})


@app.route('/api/scanner/session/finalize', methods=['POST'])
def api_finalize_scan_session():
    """Finalize scan session - create PDF and run OCR"""
    from services.document_scanner_service import get_scan_session
    
    data = request.json or {}
    session_id = data.get('session_id')
    run_ocr = data.get('run_ocr', True)
    
    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400
    
    session = get_scan_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    result = session.finalize(run_ocr=run_ocr)
    return jsonify(result)


@app.route('/api/scanner/session/cancel', methods=['POST'])
def api_cancel_scan_session():
    """Cancel a scan session and cleanup"""
    from services.document_scanner_service import get_scan_session, scan_sessions
    
    data = request.json or {}
    session_id = data.get('session_id')
    
    if not session_id:
        return jsonify({'success': False, 'error': 'session_id required'}), 400
    
    session = get_scan_session(session_id)
    if not session:
        return jsonify({'success': False, 'error': 'Session not found'}), 404
    
    removed = session.cancel()
    if session_id in scan_sessions:
        del scan_sessions[session_id]
    
    return jsonify({'success': True, 'images_removed': removed})


@app.route('/api/scanner/download')
def api_download_scanned_file():
    """Download a scanned PDF or text file"""
    filepath = request.args.get('path')
    if not filepath:
        return jsonify({'success': False, 'error': 'path required'}), 400
    
    allowed_dirs = ['generated_documents/scanned_pdfs', 'uploads/scans']
    is_allowed = any(allowed_dir in filepath for allowed_dir in allowed_dirs)
    
    if not is_allowed:
        return jsonify({'success': False, 'error': 'Invalid path'}), 403
    
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'success': False, 'error': 'File not found'}), 404


@app.route('/api/scanner/scanned-documents', methods=['GET'])
def api_list_scanned_documents():
    """List all scanned documents in the output folder"""
    import glob
    from datetime import datetime
    
    scan_folder = 'generated_documents/scanned_pdfs'
    documents = []
    
    pdf_files = glob.glob(os.path.join(scan_folder, '*.pdf'))
    
    for pdf_path in sorted(pdf_files, key=os.path.getmtime, reverse=True):
        filename = os.path.basename(pdf_path)
        text_path = pdf_path.replace('.pdf', '_text.txt')
        
        parts = filename.replace('.pdf', '').split('_')
        client_name = parts[0] if parts else 'Unknown'
        doc_type = parts[1] if len(parts) > 1 else 'unknown'
        
        doc_type_labels = {
            'cra-response-r1': 'CRA Response R1',
            'cra-response-r2': 'CRA Response R2',
            'cra-response-r3': 'CRA Response R3',
            'cra-response-r4': 'CRA Response R4',
            'cra-response': 'CRA Response',
            'collection-letter': 'Collection Letter',
            'creditor-response': 'Creditor Response',
            'court-document': 'Court Document',
            'id-document': 'ID Document',
            'proof-of-address': 'Proof of Address',
            'other': 'Other'
        }
        
        stat = os.stat(pdf_path)
        
        text_preview = ''
        word_count = 0
        if os.path.exists(text_path):
            with open(text_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
                word_count = len(full_text.split())
                text_preview = full_text[:500] + ('...' if len(full_text) > 500 else '')
        
        documents.append({
            'filename': filename,
            'pdf_path': pdf_path,
            'text_path': text_path if os.path.exists(text_path) else None,
            'client_name': client_name,
            'document_type': doc_type_labels.get(doc_type, doc_type.replace('-', ' ').title()),
            'document_type_key': doc_type,
            'file_size': stat.st_size,
            'file_size_formatted': f"{stat.st_size / 1024:.1f} KB",
            'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'created_at_formatted': datetime.fromtimestamp(stat.st_mtime).strftime('%b %d, %Y %I:%M %p'),
            'word_count': word_count,
            'text_preview': text_preview
        })
    
    return jsonify({
        'success': True,
        'count': len(documents),
        'documents': documents
    })


@app.route('/dashboard/scanned-documents')
@require_staff(roles=['admin', 'paralegal', 'attorney'])
def dashboard_scanned_documents():
    """Admin view of scanned documents"""
    return render_template('scanned_documents.html')


@app.route('/api/deadlines/upcoming', methods=['GET'])
def api_get_upcoming_deadlines():
    """Get upcoming deadlines with urgency indicators"""
    db = get_db()
    try:
        from services.deadline_service import get_upcoming_deadlines
        deadlines = get_upcoming_deadlines(db, days_ahead=90, include_overdue=True)
        
        formatted = []
        for d in deadlines:
            formatted.append({
                'id': d['id'],
                'client_name': d.get('client_name', 'Unknown'),
                'type': d.get('deadline_type_name', d.get('deadline_type', 'Unknown')),
                'bureau': d.get('bureau'),
                'due_date': d['deadline_date'].isoformat() if hasattr(d['deadline_date'], 'isoformat') else str(d['deadline_date']),
                'days_left': d.get('days_remaining', 0),
                'status': d.get('status', 'active')
            })
        
        return jsonify({'success': True, 'deadlines': formatted})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': True, 'deadlines': []})
    finally:
        db.close()


@app.route('/api/deadlines/<int:deadline_id>/complete', methods=['POST'])
def api_complete_deadline(deadline_id):
    """Mark a deadline as complete"""
    db = get_db()
    try:
        from services.deadline_service import complete_deadline
        result = complete_deadline(db, deadline_id)
        return jsonify({'success': result is not None})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/deadlines/<int:deadline_id>/extend', methods=['POST'])
def api_extend_deadline(deadline_id):
    """Extend a deadline by specified days"""
    db = get_db()
    try:
        data = request.json
        extra_days = data.get('days', 15)
        
        from services.deadline_service import extend_deadline
        from database import CaseDeadline
        
        deadline = db.query(CaseDeadline).filter_by(id=deadline_id).first()
        if deadline:
            new_total_days = deadline.days_allowed + extra_days
            result = extend_deadline(db, deadline_id, new_total_days)
            return jsonify({'success': result is not None})
        return jsonify({'success': False, 'error': 'Deadline not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlement/calculate', methods=['POST'])
def api_calculate_settlement():
    """Calculate settlement value based on violations and damages"""
    try:
        data = request.json
        
        total_violations = data.get('total_violations', 0)
        willful_violations = data.get('willful_violations', 0)
        negligent_violations = data.get('negligent_violations', 0)
        actual_damages = data.get('actual_damages', [])
        
        statutory_min = willful_violations * 100
        statutory_max = willful_violations * 1000
        
        actual_total = sum(float(d.get('amount', 0)) for d in actual_damages)
        
        punitive_min = statutory_min * 1.0
        punitive_max = statutory_max * 3.0
        
        total_min = statutory_min + actual_total + punitive_min
        total_max = statutory_max + actual_total + punitive_max
        
        attorney_fees = (total_min + total_max) / 2 * 0.35
        
        if willful_violations > 3 and total_max > 10000:
            likelihood = 'High'
        elif total_max > 5000:
            likelihood = 'Medium'
        else:
            likelihood = 'Low'
        
        recommended_demand = ((total_min + total_max) / 2) * 2.5
        
        return jsonify({
            'success': True,
            'statutory_min': statutory_min,
            'statutory_max': statutory_max,
            'punitive_min': punitive_min,
            'punitive_max': punitive_max,
            'actual_damages_total': actual_total,
            'attorney_fees': attorney_fees,
            'total_min': total_min,
            'total_max': total_max,
            'likelihood': likelihood,
            'recommended_demand': recommended_demand
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/clients')
def api_get_all_clients():
    """Get all clients for credit tracker"""
    db = get_db()
    try:
        clients = db.query(Client).order_by(Client.name).all()
        return jsonify({
            'success': True,
            'clients': [{
                'id': c.id,
                'name': c.name,
                'email': c.email,
                'status': c.status
            } for c in clients]
        })
    finally:
        db.close()


@app.route('/api/clients/<int:client_id>/details', methods=['GET'])
def api_get_client_details(client_id):
    """Get full client details including documents for modal"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        documents = db.query(ClientDocument).filter_by(client_id=client_id).all()
        
        client_data = {
            'id': client.id,
            'first_name': client.first_name,
            'last_name': client.last_name,
            'name': client.name,
            'email': client.email,
            'phone': client.phone,
            'phone_2': getattr(client, 'phone_2', None),
            'mobile': getattr(client, 'mobile', None),
            'company': getattr(client, 'company', None),
            'website': getattr(client, 'website', None),
            'address_street': client.address_street,
            'address_city': client.address_city,
            'address_state': client.address_state,
            'address_zip': client.address_zip,
            'client_type': getattr(client, 'client_type', 'L'),
            'status_2': getattr(client, 'status_2', None),
            'is_affiliate': getattr(client, 'is_affiliate', False),
            'follow_up_date': client.follow_up_date.isoformat() if hasattr(client, 'follow_up_date') and client.follow_up_date else None,
            'groups': getattr(client, 'groups', None),
            'mark_1': getattr(client, 'mark_1', False),
            'mark_2': getattr(client, 'mark_2', False),
            'created_at': client.created_at.strftime('%Y-%m-%d %H:%M') if client.created_at else None,
            'updated_at': client.updated_at.strftime('%Y-%m-%d %H:%M') if client.updated_at else None
        }
        
        docs_data = [{
            'document_type': doc.document_type,
            'received': doc.received,
            'received_at': doc.received_at.strftime('%Y-%m-%d') if doc.received_at else None
        } for doc in documents]
        
        return jsonify({'success': True, 'client': client_data, 'documents': docs_data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/clients/<int:client_id>/status', methods=['POST'])
def api_update_client_status(client_id):
    """Update client status and fields"""
    db = get_db()
    try:
        data = request.json
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        updateable_fields = [
            'client_type', 'status_2', 'company', 'phone_2', 'mobile', 'website',
            'is_affiliate', 'follow_up_date', 'groups', 'mark_1', 'mark_2',
            'first_name', 'last_name', 'email', 'phone',
            'address_street', 'address_city', 'address_state', 'address_zip'
        ]
        
        for field in updateable_fields:
            if field in data:
                value = data[field]
                if field == 'follow_up_date' and value:
                    from datetime import date as date_type
                    if isinstance(value, str):
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                setattr(client, field, value)
        
        client.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({'success': True, 'message': 'Client updated'})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/clients/create', methods=['POST'])
def api_create_client():
    """Create a new client"""
    db = get_db()
    try:
        data = request.json
        
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        name = f"{first_name} {last_name}".strip() or data.get('email', 'Unknown')
        
        client = Client(
            name=name,
            first_name=first_name,
            last_name=last_name,
            email=data.get('email', ''),
            phone=data.get('phone', ''),
            address_street=data.get('address_street', ''),
            address_city=data.get('address_city', ''),
            address_state=data.get('address_state', ''),
            address_zip=data.get('address_zip', ''),
            portal_token=secrets.token_urlsafe(32)
        )
        
        for field in ['client_type', 'status_2', 'company', 'phone_2', 'mobile', 'website', 'is_affiliate', 'groups']:
            if field in data:
                setattr(client, field, data[field])
        
        if data.get('follow_up_date'):
            client.follow_up_date = datetime.strptime(data['follow_up_date'], '%Y-%m-%d').date()
        
        db.add(client)
        db.commit()
        
        return jsonify({'success': True, 'client_id': client.id})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/clients/<int:client_id>/delete', methods=['POST'])
def api_delete_client(client_id):
    """Delete a client"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        db.query(Task).filter_by(client_id=client_id).delete()
        db.query(ClientNote).filter_by(client_id=client_id).delete()
        db.query(ClientDocument).filter_by(client_id=client_id).delete()
        
        db.delete(client)
        db.commit()
        
        return jsonify({'success': True, 'message': 'Client deleted'})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/clients/<int:client_id>/tasks', methods=['GET', 'POST'])
def api_client_tasks(client_id):
    """Get or create tasks for a client"""
    db = get_db()
    try:
        if request.method == 'GET':
            tasks = db.query(Task).filter_by(client_id=client_id).order_by(Task.due_date.desc()).all()
            tasks_data = [{
                'id': t.id,
                'title': t.title,
                'task_type': t.task_type,
                'description': t.description,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'due_time': t.due_time,
                'status': t.status,
                'assigned_to': t.assigned_to,
                'created_at': t.created_at.strftime('%Y-%m-%d %H:%M') if t.created_at else None
            } for t in tasks]
            return jsonify({'success': True, 'tasks': tasks_data})
        else:
            data = request.json
            task = Task(
                client_id=client_id,
                title=data.get('title'),
                task_type=data.get('task_type', 'other'),
                description=data.get('description'),
                due_time=data.get('due_time'),
                status='pending',
                assigned_to=data.get('assigned_to')
            )
            if data.get('due_date'):
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            
            db.add(task)
            db.commit()
            return jsonify({'success': True, 'task_id': task.id})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/clients/<int:client_id>/notes', methods=['GET', 'POST'])
def api_client_notes(client_id):
    """Get or create notes for a client"""
    db = get_db()
    try:
        if request.method == 'GET':
            notes = db.query(ClientNote).filter_by(client_id=client_id).order_by(ClientNote.created_at.desc()).all()
            notes_data = [{
                'id': n.id,
                'note_content': n.note_content,
                'created_by': n.created_by,
                'created_at': n.created_at.strftime('%Y-%m-%d %H:%M') if n.created_at else None
            } for n in notes]
            return jsonify({'success': True, 'notes': notes_data})
        else:
            data = request.json
            note = ClientNote(
                client_id=client_id,
                note_content=data.get('note_content'),
                created_by=data.get('created_by', 'Admin')
            )
            db.add(note)
            db.commit()
            return jsonify({'success': True, 'note_id': note.id})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/clients/<int:client_id>/documents', methods=['POST'])
def api_update_client_documents(client_id):
    """Update document receipt status for a client"""
    db = get_db()
    try:
        data = request.json
        documents = data.get('documents', [])
        
        for doc_data in documents:
            doc_type = doc_data.get('document_type')
            received = doc_data.get('received', False)
            
            existing = db.query(ClientDocument).filter_by(
                client_id=client_id, 
                document_type=doc_type
            ).first()
            
            if existing:
                existing.received = received
                existing.received_at = datetime.utcnow() if received and not existing.received_at else existing.received_at
                existing.updated_at = datetime.utcnow()
            else:
                new_doc = ClientDocument(
                    client_id=client_id,
                    document_type=doc_type,
                    received=received,
                    received_at=datetime.utcnow() if received else None
                )
                db.add(new_doc)
        
        db.commit()
        return jsonify({'success': True, 'message': 'Documents updated'})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/clients/<int:client_id>/documents', methods=['GET'])
def api_get_client_documents(client_id):
    """Get document receipt status for a client (LMR-style document tracking)"""
    db = get_db()
    try:
        documents = db.query(ClientDocument).filter_by(client_id=client_id).all()
        
        doc_types = ['agreement', 'cr_login', 'drivers_license', 'ssn_card', 'utility_bill', 'poa']
        doc_labels = {
            'agreement': 'Agreement Document',
            'cr_login': 'Credit Report Login',
            'drivers_license': "Driver's License",
            'ssn_card': 'Social Security Card',
            'utility_bill': 'Utility Bill',
            'poa': 'Power of Attorney'
        }
        
        doc_map = {d.document_type: d for d in documents}
        
        docs_data = []
        for doc_type in doc_types:
            doc = doc_map.get(doc_type)
            docs_data.append({
                'document_type': doc_type,
                'label': doc_labels.get(doc_type, doc_type),
                'received': doc.received if doc else False,
                'received_at': doc.received_at.strftime('%Y-%m-%d') if doc and doc.received_at else None
            })
        
        received_count = sum(1 for d in docs_data if d['received'])
        total_count = len(docs_data)
        
        return jsonify({
            'success': True, 
            'documents': docs_data,
            'received_count': received_count,
            'total_count': total_count,
            'all_received': received_count == total_count
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/clients/<int:client_id>/documents/toggle', methods=['POST'])
def api_toggle_client_document(client_id):
    """Quick toggle a single document received status"""
    db = get_db()
    try:
        data = request.json
        doc_type = data.get('document_type')
        
        if not doc_type:
            return jsonify({'success': False, 'error': 'document_type required'}), 400
        
        existing = db.query(ClientDocument).filter_by(
            client_id=client_id, 
            document_type=doc_type
        ).first()
        
        if existing:
            existing.received = not existing.received
            existing.received_at = datetime.utcnow() if existing.received else None
            existing.updated_at = datetime.utcnow()
            new_status = existing.received
        else:
            new_doc = ClientDocument(
                client_id=client_id,
                document_type=doc_type,
                received=True,
                received_at=datetime.utcnow()
            )
            db.add(new_doc)
            new_status = True
        
        db.commit()
        return jsonify({
            'success': True, 
            'received': new_status,
            'received_at': datetime.utcnow().strftime('%Y-%m-%d') if new_status else None
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# DOCUMENT CENTER - Client Upload Management
# ============================================================

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'gif', 'doc', 'docx', 'txt'}
UPLOAD_FOLDER = 'static/client_uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/api/client/upload', methods=['POST'])
def api_client_upload():
    """Handle document upload from client portal or admin"""
    db = get_db()
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        client_id = request.form.get('client_id')
        if not client_id:
            return jsonify({'success': False, 'error': 'Client ID required'}), 400
        
        client = db.query(Client).filter_by(id=int(client_id)).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        category = request.form.get('category', 'other')
        document_type = request.form.get('document_type', 'misc')
        
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{client_id}_{timestamp}_{filename}"
        
        client_folder = os.path.join(UPLOAD_FOLDER, str(client_id))
        os.makedirs(client_folder, exist_ok=True)
        
        file_path = os.path.join(client_folder, unique_filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
        
        upload = ClientUpload(
            client_id=int(client_id),
            case_id=int(request.form.get('case_id')) if request.form.get('case_id') else None,
            category=category,
            document_type=document_type,
            bureau=request.form.get('bureau'),
            dispute_round=int(request.form.get('dispute_round')) if request.form.get('dispute_round') else None,
            response_type=request.form.get('response_type'),
            sender_name=request.form.get('sender_name'),
            account_number=request.form.get('account_number'),
            amount_claimed=float(request.form.get('amount_claimed')) if request.form.get('amount_claimed') else None,
            file_path=file_path,
            file_name=filename,
            file_size=file_size,
            file_type=file_ext,
            notes=request.form.get('notes'),
            priority=request.form.get('priority', 'normal'),
            requires_action=request.form.get('requires_action') == 'true'
        )
        
        if request.form.get('document_date'):
            upload.document_date = datetime.strptime(request.form.get('document_date'), '%Y-%m-%d').date()
        if request.form.get('received_date'):
            upload.received_date = datetime.strptime(request.form.get('received_date'), '%Y-%m-%d').date()
        if request.form.get('action_deadline'):
            upload.action_deadline = datetime.strptime(request.form.get('action_deadline'), '%Y-%m-%d').date()
        
        db.add(upload)
        db.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Document uploaded successfully',
            'upload_id': upload.id,
            'file_path': file_path
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/client/<int:client_id>/uploads', methods=['GET'])
def api_get_client_uploads(client_id):
    """Get all document uploads for a client"""
    db = get_db()
    try:
        category = request.args.get('category')
        
        query = db.query(ClientUpload).filter_by(client_id=client_id)
        if category:
            query = query.filter_by(category=category)
        
        uploads = query.order_by(ClientUpload.uploaded_at.desc()).all()
        
        uploads_data = [{
            'id': u.id,
            'category': u.category,
            'document_type': u.document_type,
            'bureau': u.bureau,
            'dispute_round': u.dispute_round,
            'response_type': u.response_type,
            'sender_name': u.sender_name,
            'account_number': u.account_number,
            'amount_claimed': u.amount_claimed,
            'file_name': u.file_name,
            'file_size': u.file_size,
            'file_type': u.file_type,
            'file_path': u.file_path,
            'document_date': u.document_date.isoformat() if u.document_date else None,
            'received_date': u.received_date.isoformat() if u.received_date else None,
            'uploaded_at': u.uploaded_at.strftime('%Y-%m-%d %H:%M') if u.uploaded_at else None,
            'reviewed': u.reviewed,
            'reviewed_by': u.reviewed_by,
            'reviewed_at': u.reviewed_at.strftime('%Y-%m-%d %H:%M') if u.reviewed_at else None,
            'notes': u.notes,
            'requires_action': u.requires_action,
            'action_deadline': u.action_deadline.isoformat() if u.action_deadline else None,
            'priority': u.priority
        } for u in uploads]
        
        return jsonify({'success': True, 'uploads': uploads_data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/upload/<int:upload_id>/review', methods=['POST'])
def api_review_upload(upload_id):
    """Mark document as reviewed"""
    db = get_db()
    try:
        data = request.json or {}
        
        upload = db.query(ClientUpload).filter_by(id=upload_id).first()
        if not upload:
            return jsonify({'success': False, 'error': 'Upload not found'}), 404
        
        upload.reviewed = True
        upload.reviewed_by = data.get('reviewed_by', 'Admin')
        upload.reviewed_at = datetime.utcnow()
        
        if 'notes' in data:
            upload.notes = data['notes']
        if 'requires_action' in data:
            upload.requires_action = data['requires_action']
        if 'priority' in data:
            upload.priority = data['priority']
        if data.get('action_deadline'):
            upload.action_deadline = datetime.strptime(data['action_deadline'], '%Y-%m-%d').date()
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Document marked as reviewed'})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/upload/<int:upload_id>', methods=['DELETE'])
def api_delete_upload(upload_id):
    """Delete an uploaded document"""
    db = get_db()
    try:
        upload = db.query(ClientUpload).filter_by(id=upload_id).first()
        if not upload:
            return jsonify({'success': False, 'error': 'Upload not found'}), 404
        
        if upload.file_path and os.path.exists(upload.file_path):
            os.remove(upload.file_path)
        
        db.delete(upload)
        db.commit()
        
        return jsonify({'success': True, 'message': 'Document deleted'})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/dashboard/documents')
@require_staff(roles=['admin', 'paralegal', 'attorney'])
def dashboard_documents():
    """Admin view of all client document uploads"""
    db = get_db()
    try:
        status_filter = request.args.get('status', 'pending')
        category_filter = request.args.get('category', 'all')
        
        query = db.query(ClientUpload, Client).join(Client, ClientUpload.client_id == Client.id)
        
        if status_filter == 'pending':
            query = query.filter(ClientUpload.reviewed == False)
        elif status_filter == 'reviewed':
            query = query.filter(ClientUpload.reviewed == True)
        elif status_filter == 'urgent':
            query = query.filter(ClientUpload.priority == 'urgent')
        elif status_filter == 'action':
            query = query.filter(ClientUpload.requires_action == True)
        
        if category_filter != 'all':
            query = query.filter(ClientUpload.category == category_filter)
        
        results = query.order_by(ClientUpload.uploaded_at.desc()).limit(100).all()
        
        uploads = [{
            'id': u.id,
            'client_id': u.client_id,
            'client_name': c.name,
            'category': u.category,
            'document_type': u.document_type,
            'bureau': u.bureau,
            'sender_name': u.sender_name,
            'file_name': u.file_name,
            'file_path': u.file_path,
            'uploaded_at': u.uploaded_at,
            'reviewed': u.reviewed,
            'requires_action': u.requires_action,
            'priority': u.priority,
            'action_deadline': u.action_deadline
        } for u, c in results]
        
        pending_count = db.query(ClientUpload).filter(ClientUpload.reviewed == False).count()
        urgent_count = db.query(ClientUpload).filter(ClientUpload.priority == 'urgent').count()
        action_count = db.query(ClientUpload).filter(ClientUpload.requires_action == True).count()
        
        return render_template('documents.html',
                             uploads=uploads,
                             status_filter=status_filter,
                             category_filter=category_filter,
                             pending_count=pending_count,
                             urgent_count=urgent_count,
                             action_count=action_count)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return render_template('documents.html',
                             uploads=[],
                             status_filter='pending',
                             category_filter='all',
                             pending_count=0,
                             urgent_count=0,
                             action_count=0)
    finally:
        db.close()


@app.route('/api/portal/<token>/upload', methods=['POST'])
def api_portal_upload(token):
    """Handle document upload from client portal"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(portal_token=token).first()
        if not client:
            return jsonify({'success': False, 'error': 'Invalid portal token'}), 404
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'File type not allowed'}), 400
        
        category = request.form.get('category', 'other')
        document_type = request.form.get('document_type', 'misc')
        
        filename = secure_filename(file.filename)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{client.id}_{timestamp}_{filename}"
        
        client_folder = os.path.join(UPLOAD_FOLDER, str(client.id))
        os.makedirs(client_folder, exist_ok=True)
        
        file_path = os.path.join(client_folder, unique_filename)
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'unknown'
        
        upload = ClientUpload(
            client_id=client.id,
            category=category,
            document_type=document_type,
            bureau=request.form.get('bureau'),
            dispute_round=int(request.form.get('dispute_round')) if request.form.get('dispute_round') else None,
            response_type=document_type if category == 'cra_response' else request.form.get('response_type'),
            sender_name=request.form.get('sender_name'),
            account_number=request.form.get('account_number'),
            amount_claimed=float(request.form.get('amount_claimed')) if request.form.get('amount_claimed') else None,
            file_path=file_path,
            file_name=filename,
            file_size=file_size,
            file_type=file_ext,
            notes=request.form.get('notes'),
            priority='high' if category == 'legal' else request.form.get('priority', 'normal'),
            requires_action=category == 'legal'
        )
        
        if request.form.get('document_date'):
            upload.document_date = datetime.strptime(request.form.get('document_date'), '%Y-%m-%d').date()
        if request.form.get('received_date'):
            upload.received_date = datetime.strptime(request.form.get('received_date'), '%Y-%m-%d').date()
        if request.form.get('action_deadline'):
            upload.action_deadline = datetime.strptime(request.form.get('action_deadline'), '%Y-%m-%d').date()
        
        db.add(upload)
        db.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Document uploaded successfully',
            'upload_id': upload.id
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/portal/<token>/uploads', methods=['GET'])
def api_portal_get_uploads(token):
    """Get uploaded documents for client portal"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(portal_token=token).first()
        if not client:
            return jsonify({'success': False, 'error': 'Invalid portal token'}), 404
        
        uploads = db.query(ClientUpload).filter_by(client_id=client.id).order_by(ClientUpload.uploaded_at.desc()).all()
        
        uploads_data = [{
            'id': u.id,
            'category': u.category,
            'document_type': u.document_type,
            'file_name': u.file_name,
            'file_type': u.file_type,
            'uploaded_at': u.uploaded_at.strftime('%Y-%m-%d %H:%M') if u.uploaded_at else None,
            'reviewed': u.reviewed,
            'notes': u.notes
        } for u in uploads]
        
        return jsonify({'success': True, 'uploads': uploads_data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/portal/<token>/avatar', methods=['POST'])
def api_portal_upload_avatar(token):
    """Upload avatar image for client"""
    MAX_AVATAR_SIZE = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_MIMETYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}
    
    db = get_db()
    try:
        client = db.query(Client).filter_by(portal_token=token).first()
        if not client:
            return jsonify({'success': False, 'error': 'Invalid portal token'}), 404
        
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_AVATAR_SIZE:
            return jsonify({'success': False, 'error': 'Image too large (max 5MB)'}), 400
        
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'success': False, 'error': 'Only image files allowed (png, jpg, jpeg, gif, webp)'}), 400
        
        if file.mimetype not in ALLOWED_MIMETYPES:
            return jsonify({'success': False, 'error': 'Invalid image type'}), 400
        
        if client.avatar_filename:
            old_path = os.path.join('static', 'avatars', secure_filename(client.avatar_filename))
            if os.path.exists(old_path):
                os.remove(old_path)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_filename = secure_filename(f"client_{client.id}_{timestamp}.{ext}")
        avatar_path = os.path.join('static', 'avatars', safe_filename)
        
        os.makedirs(os.path.join('static', 'avatars'), exist_ok=True)
        file.save(avatar_path)
        
        client.avatar_filename = safe_filename
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avatar uploaded successfully',
            'avatar_url': f'/static/avatars/{safe_filename}'
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/portal/<token>/avatar', methods=['DELETE'])
def api_portal_delete_avatar(token):
    """Delete client avatar"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(portal_token=token).first()
        if not client:
            return jsonify({'success': False, 'error': 'Invalid portal token'}), 404
        
        if client.avatar_filename:
            old_path = os.path.join('static', 'avatars', client.avatar_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
            client.avatar_filename = None
            db.commit()
        
        return jsonify({'success': True, 'message': 'Avatar removed'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/client/<int:client_id>/avatar', methods=['POST'])
def api_admin_upload_avatar(client_id):
    """Admin upload avatar for client"""
    MAX_AVATAR_SIZE = 5 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ALLOWED_MIMETYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}
    
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        if 'avatar' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400
        
        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        if file_size > MAX_AVATAR_SIZE:
            return jsonify({'success': False, 'error': 'Image too large (max 5MB)'}), 400
        
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            return jsonify({'success': False, 'error': 'Only image files allowed'}), 400
        
        if file.mimetype not in ALLOWED_MIMETYPES:
            return jsonify({'success': False, 'error': 'Invalid image type'}), 400
        
        if client.avatar_filename:
            old_path = os.path.join('static', 'avatars', secure_filename(client.avatar_filename))
            if os.path.exists(old_path):
                os.remove(old_path)
        
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        safe_filename = secure_filename(f"client_{client.id}_{timestamp}.{ext}")
        avatar_path = os.path.join('static', 'avatars', safe_filename)
        
        os.makedirs(os.path.join('static', 'avatars'), exist_ok=True)
        file.save(avatar_path)
        
        client.avatar_filename = safe_filename
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avatar uploaded successfully',
            'avatar_url': f'/static/avatars/{safe_filename}'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlement/client/<int:client_id>', methods=['GET'])
def api_get_client_settlements(client_id):
    """Get all settlement estimates for a client"""
    db = get_db()
    try:
        from database import SettlementEstimate
        estimates = db.query(SettlementEstimate).filter_by(client_id=client_id).order_by(SettlementEstimate.created_at.desc()).all()
        
        estimates_data = [{
            'id': e.id,
            'case_id': e.case_id,
            'total_violations': e.total_violations,
            'willful_violations': e.willful_violations,
            'total_low': e.total_low,
            'total_high': e.total_high,
            'settlement_likelihood': e.settlement_likelihood,
            'recommended_demand': e.recommended_demand,
            'created_at': e.created_at.isoformat() if e.created_at else None
        } for e in estimates]
        
        return jsonify({'success': True, 'estimates': estimates_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==============================================================================
# CLIENT DISPUTE TIMELINE API
# ==============================================================================

@app.route('/api/client/<int:client_id>/timeline', methods=['GET'])
def api_client_timeline(client_id):
    """Get complete dispute timeline for a client - merges data from multiple sources"""
    db = get_db()
    try:
        from datetime import date as date_type
        
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        events = []
        
        # 1. Client creation / round started events
        if client.created_at:
            events.append({
                'type': 'milestone',
                'event_type': 'client_created',
                'date': client.created_at.isoformat(),
                'date_display': client.created_at.strftime('%b %d, %Y'),
                'bureau': None,
                'description': 'Case opened',
                'details': f'Client {client.name} enrolled in credit repair program',
                'round': 0,
                'icon': '🎯',
                'color': 'gray'
            })
        
        if client.round_started_at:
            events.append({
                'type': 'milestone',
                'event_type': 'round_started',
                'date': client.round_started_at.isoformat(),
                'date_display': client.round_started_at.strftime('%b %d, %Y'),
                'bureau': None,
                'description': f'Round {client.current_dispute_round or 1} started',
                'details': 'Dispute round initiated',
                'round': client.current_dispute_round or 1,
                'icon': '🔄',
                'color': 'gray'
            })
        
        # 2. Dispute Letters sent
        letters = db.query(DisputeLetter).filter_by(client_id=client_id).all()
        for letter in letters:
            letter_date = letter.sent_at or letter.created_at
            if letter_date:
                events.append({
                    'type': 'dispute_sent',
                    'event_type': 'letter_sent',
                    'date': letter_date.isoformat(),
                    'date_display': letter_date.strftime('%b %d, %Y'),
                    'bureau': letter.bureau,
                    'description': f'Dispute letter sent to {letter.bureau}',
                    'details': f'Round {letter.round_number} dispute letter generated and sent',
                    'round': letter.round_number or 1,
                    'icon': '📤',
                    'color': 'blue',
                    'file_path': letter.file_path
                })
        
        # 3. CRA Responses received
        responses = db.query(CRAResponse).filter_by(client_id=client_id).all()
        for resp in responses:
            resp_date = resp.received_date or resp.response_date or resp.created_at
            if resp_date:
                if isinstance(resp_date, date_type) and not isinstance(resp_date, datetime):
                    resp_date = datetime.combine(resp_date, datetime.min.time())
                
                response_desc = f'{resp.bureau} responded'
                if resp.response_type:
                    response_desc = f'{resp.bureau}: {resp.response_type.replace("_", " ").title()}'
                
                details_parts = []
                if resp.items_verified:
                    details_parts.append(f'{resp.items_verified} items verified')
                if resp.items_deleted:
                    details_parts.append(f'{resp.items_deleted} items deleted')
                if resp.items_updated:
                    details_parts.append(f'{resp.items_updated} items updated')
                
                events.append({
                    'type': 'response_received',
                    'event_type': 'cra_response',
                    'date': resp_date.isoformat(),
                    'date_display': resp_date.strftime('%b %d, %Y'),
                    'bureau': resp.bureau,
                    'description': response_desc,
                    'details': ', '.join(details_parts) if details_parts else f'Response from {resp.bureau}',
                    'round': resp.dispute_round or 1,
                    'icon': '📬',
                    'color': 'orange',
                    'response_type': resp.response_type
                })
        
        # 4. Dispute Items with status changes (deleted/updated items)
        items = db.query(DisputeItem).filter_by(client_id=client_id).all()
        for item in items:
            if item.status in ['deleted', 'updated', 'positive']:
                item_date = item.response_date or item.updated_at or item.created_at
                if item_date:
                    if isinstance(item_date, date_type) and not isinstance(item_date, datetime):
                        item_date = datetime.combine(item_date, datetime.min.time())
                    
                    if item.status == 'deleted':
                        events.append({
                            'type': 'item_resolved',
                            'event_type': 'item_deleted',
                            'date': item_date.isoformat(),
                            'date_display': item_date.strftime('%b %d, %Y'),
                            'bureau': item.bureau,
                            'description': f'Item deleted from {item.bureau}',
                            'details': f'{item.creditor_name or "Account"} ({item.item_type or "item"}) removed',
                            'round': item.dispute_round or 1,
                            'icon': '✅',
                            'color': 'green',
                            'creditor': item.creditor_name
                        })
                    elif item.status == 'updated':
                        events.append({
                            'type': 'item_updated',
                            'event_type': 'item_updated',
                            'date': item_date.isoformat(),
                            'date_display': item_date.strftime('%b %d, %Y'),
                            'bureau': item.bureau,
                            'description': f'Item updated on {item.bureau}',
                            'details': f'{item.creditor_name or "Account"} information corrected',
                            'round': item.dispute_round or 1,
                            'icon': '📝',
                            'color': 'green',
                            'creditor': item.creditor_name
                        })
            
            # Track when items were sent for dispute
            if item.sent_date:
                sent_date = item.sent_date
                if isinstance(sent_date, date_type) and not isinstance(sent_date, datetime):
                    sent_date = datetime.combine(sent_date, datetime.min.time())
                
                events.append({
                    'type': 'dispute_sent',
                    'event_type': 'item_disputed',
                    'date': sent_date.isoformat(),
                    'date_display': sent_date.strftime('%b %d, %Y'),
                    'bureau': item.bureau,
                    'description': f'Item disputed with {item.bureau}',
                    'details': f'{item.creditor_name or "Account"} ({item.item_type or "item"}) disputed',
                    'round': item.dispute_round or 1,
                    'icon': '📋',
                    'color': 'blue',
                    'creditor': item.creditor_name
                })
        
        # 5. Deadlines (due and overdue)
        deadlines = db.query(CaseDeadline).filter_by(client_id=client_id).all()
        today = datetime.utcnow().date()
        for deadline in deadlines:
            if deadline.deadline_date:
                deadline_dt = deadline.deadline_date
                if isinstance(deadline_dt, date_type) and not isinstance(deadline_dt, datetime):
                    deadline_dt = datetime.combine(deadline_dt, datetime.min.time())
                
                is_overdue = deadline.deadline_date < today and deadline.status != 'completed'
                
                if is_overdue:
                    events.append({
                        'type': 'overdue',
                        'event_type': 'deadline_overdue',
                        'date': deadline_dt.isoformat(),
                        'date_display': deadline_dt.strftime('%b %d, %Y'),
                        'bureau': deadline.bureau,
                        'description': f'OVERDUE: {deadline.deadline_type.replace("_", " ").title()}',
                        'details': f'{deadline.bureau or "Bureau"} response deadline passed',
                        'round': deadline.dispute_round or 1,
                        'icon': '⚠️',
                        'color': 'red',
                        'days_overdue': (today - deadline.deadline_date).days
                    })
                elif deadline.status == 'completed':
                    events.append({
                        'type': 'milestone',
                        'event_type': 'deadline_met',
                        'date': deadline_dt.isoformat(),
                        'date_display': deadline_dt.strftime('%b %d, %Y'),
                        'bureau': deadline.bureau,
                        'description': f'Deadline met: {deadline.deadline_type.replace("_", " ").title()}',
                        'details': 'Response received within required timeframe',
                        'round': deadline.dispute_round or 1,
                        'icon': '✓',
                        'color': 'gray'
                    })
                else:
                    # Upcoming deadline
                    days_until = (deadline.deadline_date - today).days
                    if days_until <= 7:
                        events.append({
                            'type': 'deadline_upcoming',
                            'event_type': 'deadline_upcoming',
                            'date': deadline_dt.isoformat(),
                            'date_display': deadline_dt.strftime('%b %d, %Y'),
                            'bureau': deadline.bureau,
                            'description': f'Deadline in {days_until} days: {deadline.deadline_type.replace("_", " ").title()}',
                            'details': f'{deadline.bureau or "Bureau"} must respond by this date',
                            'round': deadline.dispute_round or 1,
                            'icon': '⏰',
                            'color': 'orange',
                            'days_until': days_until
                        })
        
        # Sort events by date (newest first for display, but we'll return both orders)
        events.sort(key=lambda x: x['date'], reverse=True)
        
        # Calculate summary stats
        summary = {
            'total_events': len(events),
            'letters_sent': len([e for e in events if e['event_type'] == 'letter_sent']),
            'responses_received': len([e for e in events if e['event_type'] == 'cra_response']),
            'items_deleted': len([e for e in events if e['event_type'] == 'item_deleted']),
            'items_updated': len([e for e in events if e['event_type'] == 'item_updated']),
            'overdue_deadlines': len([e for e in events if e['event_type'] == 'deadline_overdue']),
            'current_round': client.current_dispute_round or 1
        }
        
        return jsonify({
            'success': True,
            'client_id': client_id,
            'client_name': client.name,
            'events': events,
            'summary': summary
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==============================================================================
# DEADLINE TRACKING API
# ==============================================================================

@app.route('/api/deadlines/create', methods=['POST'])
def api_create_deadline():
    """Create a new deadline for tracking"""
    db = get_db()
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'client_id required'}), 400
        
        deadline_type = data.get('deadline_type', 'cra_response')
        bureau = data.get('bureau')
        dispute_round = data.get('dispute_round')
        start_date = data.get('start_date')
        days_allowed = data.get('days_allowed', 30)
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        else:
            start_date = datetime.utcnow().date()
        
        from services.deadline_service import create_deadline
        deadline = create_deadline(
            db, client_id, data.get('case_id'), deadline_type,
            bureau, dispute_round, start_date, days_allowed
        )
        
        return jsonify({
            'success': True,
            'deadline_id': deadline.id,
            'deadline_date': deadline.deadline_date.isoformat(),
            'message': f'Deadline created for {deadline.deadline_date}'
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/deadlines/client/<int:client_id>', methods=['GET'])
def api_get_client_deadlines(client_id):
    """Get all deadlines for a client"""
    db = get_db()
    try:
        include_completed = request.args.get('include_completed', 'false').lower() == 'true'
        
        from services.deadline_service import get_client_deadlines
        deadlines = get_client_deadlines(db, client_id, include_completed)
        
        return jsonify({'success': True, 'deadlines': deadlines})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/deadlines/check-reminders', methods=['POST'])
def api_check_deadline_reminders():
    """Check and send deadline reminders (for scheduled task)"""
    db = get_db()
    try:
        from services.deadline_service import check_and_send_reminders
        stats = check_and_send_reminders(db)
        
        return jsonify({
            'success': True,
            'reminders_sent': stats.get('reminders_sent', 0),
            'overdue_notices_sent': stats.get('overdue_notices_sent', 0),
            'message': 'Deadline reminders checked'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==============================================================================
# NOTARIZATION API (Proof.com Integration)
# ==============================================================================

@app.route('/api/notarization/create', methods=['POST'])
def api_create_notarization():
    """Create a new notarization order via Proof.com"""
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        document_path = data.get('document_path')
        document_name = data.get('document_name', 'Document')
        signer_email = data.get('signer_email')
        signer_name = data.get('signer_name')
        
        if not all([client_id, document_path, signer_email, signer_name]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        from services.notarization_service import create_notarization_order, is_proof_configured
        
        if not is_proof_configured():
            return jsonify({
                'success': False,
                'error': 'Proof.com API not configured. Please add PROOF_API_KEY.'
            }), 400
        
        result = create_notarization_order(
            client_id, document_path, document_name, signer_email, signer_name
        )
        
        return jsonify({
            'success': True,
            'order_id': result['order_id'],
            'session_link': result['session_link'],
            'message': 'Notarization order created. Client will receive an email to complete the session.'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notarization/<int:order_id>/status', methods=['GET'])
def api_get_notarization_status(order_id):
    """Check status of a notarization order"""
    try:
        from services.notarization_service import get_notarization_status
        result = get_notarization_status(order_id)
        
        if result:
            return jsonify({'success': True, 'status': result['status'], 'details': result})
        else:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notarization/client/<int:client_id>', methods=['GET'])
def api_get_client_notarizations(client_id):
    """Get all notarization orders for a client"""
    try:
        from services.notarization_service import get_orders_by_client
        orders = get_orders_by_client(client_id)
        
        orders_data = [{
            'id': o['id'],
            'document_name': o['document_name'],
            'status': o['status'],
            'session_link': o['session_link'],
            'notarized_at': o['notarized_at'],
            'created_at': o['created_at']
        } for o in orders]
        
        return jsonify({'success': True, 'orders': orders_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/notarization/webhook', methods=['POST'])
def api_notarization_webhook():
    """Handle Proof.com webhook callbacks"""
    try:
        webhook_data = request.json
        
        from services.notarization_service import handle_webhook
        result = handle_webhook(webhook_data)
        
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# CERTIFIED MAIL API (SendCertifiedMail.com Integration)
# ==============================================================================

@app.route('/api/certified-mail/send', methods=['POST'])
def api_send_certified_mail():
    """Send a document via certified mail"""
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        recipient_name = data.get('recipient_name')
        recipient_address = data.get('recipient_address')
        document_path = data.get('document_path')
        letter_type = data.get('letter_type', 'dispute')
        bureau = data.get('bureau')
        dispute_round = data.get('dispute_round')
        
        if not all([client_id, recipient_name, recipient_address, document_path]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        from services.certified_mail_service import send_certified_letter, is_certified_mail_configured
        
        result = send_certified_letter(
            client_id, recipient_name, recipient_address, document_path,
            letter_type, bureau, dispute_round
        )
        
        return jsonify({
            'success': True,
            'order_id': result['order_id'],
            'tracking_number': result['tracking_number'],
            'cost': result['cost'],
            'mock_mode': not is_certified_mail_configured(),
            'message': 'Certified mail order created'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/certified-mail/<int:order_id>/status', methods=['GET'])
def api_get_certified_mail_status(order_id):
    """Check status of a certified mail order"""
    try:
        from services.certified_mail_service import check_delivery_status
        result = check_delivery_status(order_id)
        
        if result:
            return jsonify({'success': True, 'status': result['status'], 'details': result})
        else:
            return jsonify({'success': False, 'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/certified-mail/client/<int:client_id>', methods=['GET'])
def api_get_client_certified_mail(client_id):
    """Get all certified mail orders for a client"""
    try:
        from services.certified_mail_service import get_orders_by_client
        orders = get_orders_by_client(client_id)
        
        return jsonify({'success': True, 'orders': orders})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/certified-mail/cost', methods=['GET'])
def api_get_certified_mail_cost():
    """Get estimated cost for certified mail"""
    try:
        pages = int(request.args.get('pages', 1))
        mail_class = request.args.get('class', 'certified')
        
        from services.certified_mail_service import get_mailing_cost
        cost = get_mailing_cost(pages, mail_class)
        
        return jsonify({'success': True, 'cost': cost})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/certified-mail/webhook', methods=['POST'])
def api_certified_mail_webhook():
    """Handle SendCertifiedMail.com webhook callbacks"""
    try:
        webhook_data = request.json
        
        from services.certified_mail_service import handle_webhook
        result = handle_webhook(webhook_data)
        
        return jsonify({'success': True})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# OCR / DOCUMENT EXTRACTION API
# ==============================================================================

@app.route('/api/ocr/extract-cra-response', methods=['POST'])
def api_extract_cra_response():
    """Extract data from a CRA response document using AI"""
    db = get_db()
    try:
        data = request.json or {}
        upload_id = data.get('upload_id')
        file_path = data.get('file_path')
        file_type = data.get('file_type', 'pdf')
        bureau = data.get('bureau')
        
        if not upload_id and not file_path:
            return jsonify({'success': False, 'error': 'upload_id or file_path required'}), 400
        
        if upload_id:
            upload = db.query(ClientUpload).filter_by(id=upload_id).first()
            if not upload:
                return jsonify({'success': False, 'error': 'Upload not found'}), 404
            file_path = upload.file_path
            file_type = upload.file_type
            bureau = upload.bureau
        
        from services.ocr_service import extract_cra_response_data, update_client_upload_ocr
        result = extract_cra_response_data(file_path, file_type, bureau)
        
        if upload_id and result.get('success'):
            update_client_upload_ocr(upload_id, result.get('data', {}))
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/ocr/analyze-collection-letter', methods=['POST'])
def api_analyze_collection_letter():
    """Analyze a collection letter for FDCPA violations"""
    db = get_db()
    try:
        data = request.json or {}
        upload_id = data.get('upload_id')
        file_path = data.get('file_path')
        file_type = data.get('file_type', 'pdf')
        
        if not upload_id and not file_path:
            return jsonify({'success': False, 'error': 'upload_id or file_path required'}), 400
        
        if upload_id:
            upload = db.query(ClientUpload).filter_by(id=upload_id).first()
            if not upload:
                return jsonify({'success': False, 'error': 'Upload not found'}), 404
            file_path = upload.file_path
            file_type = upload.file_type
        
        from services.ocr_service import analyze_collection_letter, update_client_upload_ocr
        result = analyze_collection_letter(file_path, file_type)
        
        if upload_id and result.get('success'):
            update_client_upload_ocr(upload_id, result.get('data', {}))
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/ocr/detect-violations', methods=['POST'])
def api_detect_fcra_violations():
    """Detect FCRA violations from document data"""
    try:
        data = request.json or {}
        document_data = data.get('document_data', {})
        document_type = data.get('document_type', 'cra_response')
        
        if not document_data:
            return jsonify({'success': False, 'error': 'document_data required'}), 400
        
        from services.ocr_service import detect_fcra_violations
        result = detect_fcra_violations(document_data, document_type)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ocr/process-upload/<int:upload_id>', methods=['POST'])
def api_process_upload_ocr(upload_id):
    """Process a client upload with AI extraction based on category"""
    db = get_db()
    try:
        upload = db.query(ClientUpload).filter_by(id=upload_id).first()
        if not upload:
            return jsonify({'success': False, 'error': 'Upload not found'}), 404
        
        category = upload.category
        
        from services.ocr_service import process_upload_for_ocr
        result = process_upload_for_ocr(upload_id, category)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/ocr/batch-process', methods=['POST'])
def api_batch_process_ocr():
    """Batch process multiple uploads with AI extraction"""
    try:
        data = request.json or {}
        upload_ids = data.get('upload_ids', [])
        category = data.get('category', 'cra_response')
        
        if not upload_ids:
            return jsonify({'success': False, 'error': 'upload_ids required'}), 400
        
        from services.ocr_service import batch_process_uploads
        result = batch_process_uploads(upload_ids, category)
        
        return jsonify({
            'success': True,
            'processed': result.get('processed', 0),
            'failed': result.get('failed', 0),
            'results': result.get('results', [])
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# LIMITED POA MANAGEMENT API
# ==============================================================================

@app.route('/api/poa/generate', methods=['POST'])
def api_generate_poa():
    """Generate a Limited Power of Attorney document for a client"""
    db = get_db()
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'client_id required'}), 400
        
        client = db.query(Client).filter_by(id=int(client_id)).first()
        if not client:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        from database import LimitedPOA
        
        poa = LimitedPOA(
            client_id=client.id,
            poa_type=data.get('poa_type', 'credit_dispute'),
            effective_date=datetime.utcnow().date(),
            expiration_date=(datetime.utcnow() + timedelta(days=365)).date(),
            scope=data.get('scope', {
                'dispute_credit_reports': True,
                'communicate_with_cras': True,
                'request_credit_freezes': True,
                'obtain_credit_reports': True
            }),
            status='draft'
        )
        
        db.add(poa)
        db.commit()
        
        return jsonify({
            'success': True,
            'poa_id': poa.id,
            'message': 'Limited POA created. Ready for signature and notarization.'
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/poa/client/<int:client_id>', methods=['GET'])
def api_get_client_poa(client_id):
    """Get all Limited POA documents for a client"""
    db = get_db()
    try:
        from database import LimitedPOA
        poas = db.query(LimitedPOA).filter_by(client_id=client_id).order_by(LimitedPOA.created_at.desc()).all()
        
        poas_data = [{
            'id': p.id,
            'poa_type': p.poa_type,
            'status': p.status,
            'signed': p.signed,
            'signed_at': p.signed_at.isoformat() if p.signed_at else None,
            'notarized': p.notarized,
            'notarized_at': p.notarized_at.isoformat() if p.notarized_at else None,
            'effective_date': p.effective_date.isoformat() if p.effective_date else None,
            'expiration_date': p.expiration_date.isoformat() if p.expiration_date else None,
            'scope': p.scope,
            'created_at': p.created_at.isoformat() if p.created_at else None
        } for p in poas]
        
        return jsonify({'success': True, 'poas': poas_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==============================================================================
# ATTORNEY REFERRAL API
# ==============================================================================

@app.route('/api/attorney-referral/create', methods=['POST'])
def api_create_attorney_referral():
    """Create an attorney referral for a high-value case"""
    db = get_db()
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        case_id = data.get('case_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'client_id required'}), 400
        
        from database import AttorneyReferral
        
        referral = AttorneyReferral(
            client_id=client_id,
            case_id=case_id,
            attorney_name=data.get('attorney_name'),
            attorney_firm=data.get('attorney_firm'),
            attorney_email=data.get('attorney_email'),
            attorney_phone=data.get('attorney_phone'),
            referral_reason=data.get('referral_reason'),
            case_summary=data.get('case_summary'),
            estimated_value=data.get('estimated_value'),
            fee_arrangement=data.get('fee_arrangement', 'contingency'),
            referral_fee_percent=data.get('referral_fee_percent', 25.0),
            status='pending'
        )
        
        db.add(referral)
        db.commit()
        
        return jsonify({
            'success': True,
            'referral_id': referral.id,
            'message': 'Attorney referral created'
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/attorney-referral/<int:referral_id>', methods=['PUT'])
def api_update_attorney_referral(referral_id):
    """Update attorney referral status and outcome"""
    db = get_db()
    try:
        data = request.json or {}
        
        from database import AttorneyReferral
        referral = db.query(AttorneyReferral).filter_by(id=referral_id).first()
        
        if not referral:
            return jsonify({'success': False, 'error': 'Referral not found'}), 404
        
        if 'status' in data:
            referral.status = data['status']
        if 'attorney_accepted' in data:
            referral.attorney_accepted = data['attorney_accepted']
            referral.attorney_response_at = datetime.utcnow()
        if 'outcome' in data:
            referral.outcome = data['outcome']
        if 'settlement_amount' in data:
            referral.settlement_amount = data['settlement_amount']
        if 'referral_fee_received' in data:
            referral.referral_fee_received = data['referral_fee_received']
        
        referral.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({'success': True, 'message': 'Referral updated'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/attorney-referrals', methods=['GET'])
def api_list_attorney_referrals():
    """List all attorney referrals"""
    db = get_db()
    try:
        status_filter = request.args.get('status')
        
        from database import AttorneyReferral
        query = db.query(AttorneyReferral, Client).join(Client, AttorneyReferral.client_id == Client.id)
        
        if status_filter:
            query = query.filter(AttorneyReferral.status == status_filter)
        
        results = query.order_by(AttorneyReferral.created_at.desc()).all()
        
        referrals_data = [{
            'id': r.id,
            'client_id': r.client_id,
            'client_name': c.name,
            'attorney_name': r.attorney_name,
            'attorney_firm': r.attorney_firm,
            'estimated_value': r.estimated_value,
            'status': r.status,
            'attorney_accepted': r.attorney_accepted,
            'settlement_amount': r.settlement_amount,
            'created_at': r.created_at.isoformat() if r.created_at else None
        } for r, c in results]
        
        return jsonify({'success': True, 'referrals': referrals_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==============================================================================
# E-SIGNATURE API
# ==============================================================================

@app.route('/api/esignature/create', methods=['POST'])
def api_create_signature_request():
    """Create a new e-signature request"""
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        document_type = data.get('document_type', 'client_agreement')
        document_name = data.get('document_name')
        document_path = data.get('document_path')
        signer_email = data.get('signer_email')
        signer_name = data.get('signer_name')
        
        if not all([client_id, document_name, signer_email, signer_name]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        from services.esignature_service import create_signature_request
        result = create_signature_request(
            client_id, document_type, document_name, document_path,
            signer_email, signer_name
        )
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/sign/<token>')
def signature_page(token):
    """Display signature capture page for client"""
    from services.esignature_service import verify_signing_token
    result = verify_signing_token(token)
    
    if not result.get('success'):
        return render_template('signature_error.html', error=result.get('error', 'Invalid or expired link'))
    
    return render_template('signature_capture.html', 
                         request_data=result,
                         token=token)


@app.route('/api/esignature/capture', methods=['POST'])
def api_capture_signature():
    """Capture and save signature"""
    try:
        data = request.json or {}
        token = data.get('token')
        signature_data = data.get('signature_data')
        
        if not token or not signature_data:
            return jsonify({'success': False, 'error': 'Token and signature_data required'}), 400
        
        from services.esignature_service import verify_signing_token, capture_signature
        
        verify_result = verify_signing_token(token)
        if not verify_result.get('success'):
            return jsonify(verify_result), 400
        
        request_id = verify_result.get('request_id')
        result = capture_signature(request_id, signature_data)
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/esignature/<int:request_id>/status', methods=['GET'])
def api_get_signature_status(request_id):
    """Get status of a signature request"""
    try:
        from services.esignature_service import get_signature_status
        result = get_signature_status(request_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/esignature/client/<int:client_id>/pending', methods=['GET'])
def api_get_pending_signatures(client_id):
    """Get pending signature requests for a client"""
    try:
        from services.esignature_service import get_pending_signatures
        result = get_pending_signatures(client_id)
        return jsonify({'success': True, 'pending': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/esignature/<int:request_id>/remind', methods=['POST'])
def api_send_signature_reminder(request_id):
    """Send reminder for pending signature"""
    try:
        from services.esignature_service import send_signature_reminder
        result = send_signature_reminder(request_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/esignature/types', methods=['GET'])
def api_get_signature_types():
    """Get supported document types for e-signature"""
    try:
        from services.esignature_service import list_document_types
        types = list_document_types()
        return jsonify({'success': True, 'types': types})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# METRO2 VIOLATION DETECTION API
# ==============================================================================

@app.route('/api/metro2/detect-violations', methods=['POST'])
def api_detect_metro2_violations():
    """Detect Metro2 format violations in tradeline data"""
    try:
        data = request.json or {}
        tradeline_data = data.get('tradeline_data', {})
        
        if not tradeline_data:
            return jsonify({'success': False, 'error': 'tradeline_data required'}), 400
        
        from services.metro2_service import detect_metro2_violations
        violations = detect_metro2_violations(tradeline_data)
        
        return jsonify({
            'success': True,
            'violations': violations,
            'violation_count': len(violations)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metro2/analyze-collection', methods=['POST'])
def api_analyze_collection_account():
    """Analyze a collection account for Metro2 violations"""
    try:
        data = request.json or {}
        collection_data = data.get('collection_data', {})
        
        if not collection_data:
            return jsonify({'success': False, 'error': 'collection_data required'}), 400
        
        from services.metro2_service import analyze_collection_account
        violations = analyze_collection_account(collection_data)
        
        return jsonify({
            'success': True,
            'violations': violations,
            'violation_count': len(violations)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metro2/calculate-damages', methods=['POST'])
def api_calculate_metro2_damages():
    """Calculate potential damages from Metro2 violations"""
    try:
        data = request.json or {}
        violations = data.get('violations', [])
        
        from services.metro2_service import calculate_violation_damages
        damage_info = calculate_violation_damages(violations)
        
        return jsonify({
            'success': True,
            'damages': damage_info
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metro2/generate-dispute-points', methods=['POST'])
def api_generate_metro2_dispute_points():
    """Generate dispute language for Metro2 violations"""
    try:
        data = request.json or {}
        violations = data.get('violations', [])
        
        from services.metro2_service import generate_metro2_dispute_points
        dispute_points = generate_metro2_dispute_points(violations)
        
        return jsonify({
            'success': True,
            'dispute_points': dispute_points
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/metro2/payment-codes', methods=['GET'])
def api_get_payment_codes():
    """Get Metro2 payment status code reference"""
    try:
        from services.metro2_service import PAYMENT_STATUS_CODES, PAYMENT_HISTORY_CODES
        return jsonify({
            'success': True,
            'status_codes': PAYMENT_STATUS_CODES,
            'history_codes': PAYMENT_HISTORY_CODES
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# DEBT VALIDATION LETTERS API
# ==============================================================================

@app.route('/api/validation-letters/generate', methods=['POST'])
def api_generate_validation_letters():
    """Generate debt validation letters for collection accounts"""
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        collections = data.get('collections', [])
        case_id = data.get('case_id')
        
        if not client_id:
            return jsonify({'success': False, 'error': 'client_id required'}), 400
        
        from services.debt_validation_service import generate_validation_letters
        
        if collections:
            result = generate_validation_letters(client_id, collections=collections)
        elif case_id:
            result = generate_validation_letters(client_id, case_id=case_id)
        else:
            return jsonify({'success': False, 'error': 'Either collections or case_id required'}), 400
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/validation-letters/auto-generate/<int:case_id>', methods=['POST'])
def api_auto_generate_validation_letters(case_id):
    """Auto-generate validation letters from case analysis"""
    try:
        from services.debt_validation_service import auto_generate_validation_letters_from_analysis
        result = auto_generate_validation_letters_from_analysis(case_id)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/validation-letters/agencies', methods=['GET'])
def api_get_collection_agencies():
    """Get list of common collection agencies with addresses"""
    try:
        from services.debt_validation_service import get_common_collection_agencies
        agencies = get_common_collection_agencies()
        return jsonify({'success': True, 'agencies': agencies})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/validation-letters/single', methods=['POST'])
def api_generate_single_validation_letter():
    """Generate a single debt validation letter"""
    try:
        data = request.json or {}
        client_id = data.get('client_id')
        collection_info = data.get('collection_info', {})
        
        if not client_id:
            return jsonify({'success': False, 'error': 'client_id required'}), 400
        if not collection_info.get('creditor_name'):
            return jsonify({'success': False, 'error': 'creditor_name required in collection_info'}), 400
        
        from services.debt_validation_service import generate_validation_letter_single
        result = generate_validation_letter_single(client_id, collection_info)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ==============================================================================
# PWA MANIFEST AND SERVICE WORKER
# ==============================================================================

@app.route('/manifest.json')
def pwa_manifest():
    """Serve PWA manifest for installable web app"""
    manifest = {
        "name": "Brightpath Ascend FCRA Platform",
        "short_name": "Brightpath FCRA",
        "description": "Comprehensive FCRA litigation automation platform",
        "start_url": "/dashboard",
        "display": "standalone",
        "background_color": "#1a1a2e",
        "theme_color": "#319795",
        "orientation": "any",
        "icons": [
            {
                "src": "/static/images/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/images/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "categories": ["business", "productivity"],
        "shortcuts": [
            {
                "name": "Dashboard",
                "short_name": "Dashboard",
                "description": "View dashboard",
                "url": "/dashboard",
                "icons": [{"src": "/static/images/icon-192.png", "sizes": "192x192"}]
            },
            {
                "name": "Contacts",
                "short_name": "Contacts",
                "description": "Manage contacts",
                "url": "/dashboard/contacts",
                "icons": [{"src": "/static/images/icon-192.png", "sizes": "192x192"}]
            }
        ]
    }
    return jsonify(manifest)


@app.route('/sw.js')
def service_worker():
    """Serve service worker for offline functionality and push notifications"""
    sw_content = '''
// Brightpath Ascend FCRA Platform Service Worker
const CACHE_NAME = 'brightpath-fcra-v1';
const urlsToCache = [
    '/',
    '/dashboard',
    '/static/images/logo.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// Install event
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
    self.skipWaiting();
});

// Activate event
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch event - network first, cache fallback
self.addEventListener('fetch', event => {
    if (event.request.method !== 'GET') return;
    
    event.respondWith(
        fetch(event.request)
            .then(response => {
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME)
                        .then(cache => cache.put(event.request, responseClone));
                }
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});

// Push notification event
self.addEventListener('push', event => {
    const data = event.data ? event.data.json() : {};
    const title = data.title || 'Brightpath Ascend';
    const options = {
        body: data.body || 'You have a new notification',
        icon: '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        data: data.url || '/dashboard',
        actions: [
            { action: 'open', title: 'Open' },
            { action: 'dismiss', title: 'Dismiss' }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Notification click event
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.action === 'dismiss') return;
    
    event.waitUntil(
        clients.openWindow(event.notification.data)
    );
});
'''
    response = app.response_class(
        response=sw_content,
        status=200,
        mimetype='application/javascript'
    )
    response.headers['Cache-Control'] = 'no-cache'
    return response


# ============================================================
# CREDIT SCORE IMPROVEMENT TRACKING
# ============================================================

@app.route('/api/credit-score/snapshot', methods=['POST'])
def add_credit_score_snapshot():
    """Add a new credit score snapshot for a client"""
    from services.credit_score_calculator import add_score_snapshot
    
    data = request.json
    client_id = data.get('client_id')
    
    if not client_id:
        return jsonify({'success': False, 'error': 'client_id required'}), 400
    
    result = add_score_snapshot(
        client_id=client_id,
        equifax=data.get('equifax'),
        experian=data.get('experian'),
        transunion=data.get('transunion'),
        negatives=data.get('negatives', 0),
        removed=data.get('removed', 0),
        milestone=data.get('milestone'),
        dispute_round=data.get('dispute_round', 0),
        snapshot_type=data.get('snapshot_type', 'manual'),
        source=data.get('source'),
        notes=data.get('notes')
    )
    
    return jsonify(result)


@app.route('/api/credit-score/projection/<int:client_id>')
def get_credit_score_projection(client_id):
    """Get comprehensive credit score projection for a client"""
    from services.credit_score_calculator import calculate_client_projection
    
    projection = calculate_client_projection(client_id)
    if not projection:
        return jsonify({'success': False, 'error': 'Client not found'}), 404
    
    return jsonify({'success': True, 'data': projection})


@app.route('/api/credit-score/summary/<int:client_id>')
def get_credit_score_summary(client_id):
    """Get quick summary of client's credit improvement"""
    from services.credit_score_calculator import get_improvement_summary
    
    summary = get_improvement_summary(client_id)
    return jsonify({'success': True, 'data': summary})


@app.route('/api/credit-score/timeline/<int:client_id>')
def get_credit_score_timeline(client_id):
    """Get score history timeline for charts"""
    from services.credit_score_calculator import get_score_timeline
    
    timeline = get_score_timeline(client_id)
    return jsonify({'success': True, 'data': timeline})


@app.route('/api/credit-score/estimate', methods=['POST'])
def estimate_score_improvement():
    """Quick estimate of potential score improvement"""
    from services.credit_score_calculator import quick_estimate
    
    data = request.json
    current_score = data.get('current_score', 550)
    num_negatives = data.get('num_negatives', 0)
    
    estimate = quick_estimate(current_score, num_negatives)
    return jsonify({'success': True, 'data': estimate})


@app.route('/api/credit-score/item-types')
def get_credit_score_item_types():
    """Get all negative item types with their score impact data"""
    from services.credit_score_calculator import get_all_item_types, SEVERITY_LEVELS
    
    item_types = get_all_item_types()
    return jsonify({
        'success': True,
        'data': {
            'categories': item_types,
            'severity_levels': SEVERITY_LEVELS
        }
    })


@app.route('/api/credit-score/estimate-detailed', methods=['POST'])
def estimate_score_detailed():
    """Detailed estimate based on specific item types"""
    from services.credit_score_calculator import estimate_by_item_types
    
    data = request.json
    current_score = data.get('current_score', 550)
    selected_items = data.get('items', [])
    
    estimate = estimate_by_item_types(current_score, selected_items)
    return jsonify({'success': True, 'data': estimate})


@app.route('/api/credit-score/history/<int:client_id>')
def get_credit_score_history(client_id):
    """Get all score snapshots for a client"""
    db = get_db()
    try:
        snapshots = db.query(CreditScoreSnapshot).filter_by(
            client_id=client_id
        ).order_by(CreditScoreSnapshot.created_at.desc()).all()
        
        history = []
        for s in snapshots:
            history.append({
                'id': s.id,
                'equifax': s.equifax_score,
                'experian': s.experian_score,
                'transunion': s.transunion_score,
                'average': s.average_score,
                'negatives': s.total_negatives,
                'removed': s.total_removed,
                'milestone': s.milestone,
                'dispute_round': s.dispute_round,
                'snapshot_type': s.snapshot_type,
                'source': s.source,
                'notes': s.notes,
                'created_at': s.created_at.isoformat() if s.created_at else None,
            })
        
        return jsonify({'success': True, 'data': history})
    finally:
        db.close()


@app.route('/dashboard/credit-tracker')
@require_staff(roles=['admin', 'paralegal', 'attorney'])
def credit_tracker_dashboard():
    """Credit score improvement tracker dashboard page"""
    return render_template('credit_tracker.html')


@app.route('/dashboard/credit-tracker/<int:client_id>')
@require_staff(roles=['admin', 'paralegal', 'attorney'])
def credit_tracker_client(client_id):
    """Credit score tracker for specific client"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return "Client not found", 404
        return render_template('credit_tracker_client.html', client=client)
    finally:
        db.close()


# =============================================================
# CALENDAR VIEW FOR DEADLINES
# =============================================================

@app.route('/dashboard/calendar')
@require_staff()
def calendar_dashboard():
    """Calendar view showing all case deadlines"""
    return render_template('calendar.html')


@app.route('/api/calendar/events')
def get_calendar_events():
    """
    API endpoint returning deadlines in FullCalendar format.
    Supports filtering by client_name, bureau, deadline_type.
    """
    from datetime import date, timedelta
    
    db = get_db()
    try:
        client_filter = request.args.get('client', '').strip()
        bureau_filter = request.args.get('bureau', '').strip()
        type_filter = request.args.get('type', '').strip()
        
        query = db.query(CaseDeadline, Client).join(
            Client, CaseDeadline.client_id == Client.id
        )
        
        if client_filter:
            query = query.filter(Client.name.ilike(f'%{client_filter}%'))
        
        if bureau_filter:
            query = query.filter(CaseDeadline.bureau == bureau_filter)
        
        if type_filter:
            query = query.filter(CaseDeadline.deadline_type == type_filter)
        
        results = query.all()
        
        color_map = {
            'cra_response': '#3498db',
            'reinvestigation': '#f39c12',
            'data_furnisher': '#27ae60',
            'client_action': '#f1c40f',
            'legal_filing': '#e74c3c'
        }
        
        type_labels = {
            'cra_response': 'CRA Response',
            'reinvestigation': 'Reinvestigation',
            'data_furnisher': 'Data Furnisher',
            'client_action': 'Client Action',
            'legal_filing': 'Legal Filing'
        }
        
        events = []
        today = date.today()
        
        for deadline, client in results:
            is_overdue = deadline.deadline_date < today and deadline.status == 'active'
            base_color = color_map.get(deadline.deadline_type, '#95a5a6')
            event_color = '#e74c3c' if is_overdue else base_color
            
            type_label = type_labels.get(deadline.deadline_type, deadline.deadline_type.replace('_', ' ').title())
            bureau_suffix = f" ({deadline.bureau})" if deadline.bureau else ""
            
            events.append({
                'id': deadline.id,
                'title': f"{type_label} - {client.name}{bureau_suffix}",
                'start': deadline.deadline_date.isoformat(),
                'color': event_color,
                'textColor': '#ffffff',
                'extendedProps': {
                    'client_id': client.id,
                    'client_name': client.name,
                    'client_email': client.email or '',
                    'deadline_type': deadline.deadline_type,
                    'deadline_type_label': type_label,
                    'bureau': deadline.bureau or 'N/A',
                    'dispute_round': deadline.dispute_round or 1,
                    'start_date': deadline.start_date.isoformat() if deadline.start_date else '',
                    'days_allowed': deadline.days_allowed or 30,
                    'status': deadline.status,
                    'is_overdue': is_overdue,
                    'notes': deadline.notes or ''
                }
            })
        
        return jsonify(events)
        
    except Exception as e:
        print(f"Error fetching calendar events: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/calendar/stats')
def get_calendar_stats():
    """
    Get calendar statistics: upcoming this week, overdue count.
    """
    from datetime import date, timedelta
    
    db = get_db()
    try:
        today = date.today()
        week_from_now = today + timedelta(days=7)
        
        upcoming_this_week = db.query(CaseDeadline).filter(
            CaseDeadline.status == 'active',
            CaseDeadline.deadline_date >= today,
            CaseDeadline.deadline_date <= week_from_now
        ).count()
        
        overdue_count = db.query(CaseDeadline).filter(
            CaseDeadline.status == 'active',
            CaseDeadline.deadline_date < today
        ).count()
        
        total_active = db.query(CaseDeadline).filter(
            CaseDeadline.status == 'active'
        ).count()
        
        completed_this_month = db.query(CaseDeadline).filter(
            CaseDeadline.status == 'completed',
            CaseDeadline.completed_at >= today.replace(day=1)
        ).count()
        
        return jsonify({
            'success': True,
            'upcoming_this_week': upcoming_this_week,
            'overdue_count': overdue_count,
            'total_active': total_active,
            'completed_this_month': completed_this_month
        })
        
    except Exception as e:
        print(f"Error fetching calendar stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ==============================================================================
# SETTLEMENT TRACKING MODULE
# ==============================================================================

@app.route('/dashboard/settlements')
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def dashboard_settlements():
    """Settlement tracking dashboard with pipeline view"""
    db = get_db()
    try:
        settlements = db.query(Settlement).order_by(Settlement.created_at.desc()).all()
        
        status_counts = {
            'pending': 0,
            'demand_sent': 0,
            'negotiating': 0,
            'accepted': 0,
            'rejected': 0,
            'litigated': 0
        }
        
        total_settled = 0
        total_pending_value = 0
        total_contingency = 0
        settlement_amounts = []
        
        settlement_list = []
        for s in settlements:
            case = db.query(Case).filter_by(id=s.case_id).first()
            client = None
            if case:
                client = db.query(Client).filter_by(id=case.client_id).first()
            
            status = s.status or 'pending'
            if status in status_counts:
                status_counts[status] += 1
            
            if status == 'accepted' and s.final_amount:
                total_settled += s.final_amount
                settlement_amounts.append(s.final_amount)
            elif status in ['pending', 'demand_sent', 'negotiating']:
                total_pending_value += s.target_amount or 0
            
            if s.contingency_earned:
                total_contingency += s.contingency_earned
            
            settlement_list.append({
                'id': s.id,
                'case_id': s.case_id,
                'client_name': client.name if client else 'Unknown',
                'client_id': client.id if client else None,
                'target_amount': s.target_amount or 0,
                'minimum_acceptable': s.minimum_acceptable or 0,
                'initial_demand': s.initial_demand or 0,
                'counter_offer_1': s.counter_offer_1,
                'counter_offer_2': s.counter_offer_2,
                'final_amount': s.final_amount,
                'status': status,
                'settled_at': s.settled_at,
                'payment_received': s.payment_received,
                'payment_amount': s.payment_amount,
                'contingency_earned': s.contingency_earned,
                'created_at': s.created_at
            })
        
        avg_settlement = sum(settlement_amounts) / len(settlement_amounts) if settlement_amounts else 0
        
        stats = {
            'total_settled': total_settled,
            'total_pending_value': total_pending_value,
            'avg_settlement': avg_settlement,
            'total_contingency': total_contingency,
            'count_settled': len(settlement_amounts),
            'count_pending': status_counts['pending'] + status_counts['demand_sent'] + status_counts['negotiating']
        }
        
        return render_template('settlements.html',
            settlements=settlement_list,
            status_counts=status_counts,
            stats=stats
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}", 500
    finally:
        db.close()


@app.route('/api/settlements', methods=['GET'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_list_settlements():
    """List all settlements with optional filters"""
    db = get_db()
    try:
        query = db.query(Settlement)
        
        status = request.args.get('status')
        if status:
            query = query.filter(Settlement.status == status)
        
        client_id = request.args.get('client_id')
        if client_id:
            case_ids = [c.id for c in db.query(Case).filter_by(client_id=client_id).all()]
            query = query.filter(Settlement.case_id.in_(case_ids))
        
        date_from = request.args.get('date_from')
        if date_from:
            query = query.filter(Settlement.created_at >= datetime.strptime(date_from, '%Y-%m-%d'))
        
        date_to = request.args.get('date_to')
        if date_to:
            query = query.filter(Settlement.created_at <= datetime.strptime(date_to, '%Y-%m-%d'))
        
        settlements = query.order_by(Settlement.created_at.desc()).all()
        
        result = []
        for s in settlements:
            case = db.query(Case).filter_by(id=s.case_id).first()
            client = None
            if case:
                client = db.query(Client).filter_by(id=case.client_id).first()
            
            result.append({
                'id': s.id,
                'case_id': s.case_id,
                'client_name': client.name if client else 'Unknown',
                'client_id': client.id if client else None,
                'target_amount': s.target_amount,
                'minimum_acceptable': s.minimum_acceptable,
                'initial_demand': s.initial_demand,
                'initial_demand_date': s.initial_demand_date.isoformat() if s.initial_demand_date else None,
                'counter_offer_1': s.counter_offer_1,
                'counter_offer_1_date': s.counter_offer_1_date.isoformat() if s.counter_offer_1_date else None,
                'counter_offer_2': s.counter_offer_2,
                'counter_offer_2_date': s.counter_offer_2_date.isoformat() if s.counter_offer_2_date else None,
                'final_amount': s.final_amount,
                'status': s.status,
                'settled_at': s.settled_at.isoformat() if s.settled_at else None,
                'settlement_notes': s.settlement_notes,
                'payment_received': s.payment_received,
                'payment_amount': s.payment_amount,
                'payment_date': s.payment_date.isoformat() if s.payment_date else None,
                'contingency_earned': s.contingency_earned,
                'transunion_target': s.transunion_target,
                'experian_target': s.experian_target,
                'equifax_target': s.equifax_target,
                'created_at': s.created_at.isoformat() if s.created_at else None
            })
        
        return jsonify({'success': True, 'settlements': result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlements', methods=['POST'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_create_settlement():
    """Create a new settlement from a case"""
    db = get_db()
    try:
        data = request.json
        case_id = data.get('case_id')
        
        if not case_id:
            return jsonify({'success': False, 'error': 'case_id is required'}), 400
        
        case = db.query(Case).filter_by(id=case_id).first()
        if not case:
            return jsonify({'success': False, 'error': 'Case not found'}), 404
        
        existing = db.query(Settlement).filter_by(case_id=case_id).first()
        if existing:
            return jsonify({'success': False, 'error': 'Settlement already exists for this case', 'settlement_id': existing.id}), 400
        
        damages = None
        if case.analysis_id:
            damages = db.query(Damages).filter_by(analysis_id=case.analysis_id).first()
        
        target_amount = data.get('target_amount') or (damages.settlement_target if damages else 0)
        minimum_acceptable = data.get('minimum_acceptable') or (damages.minimum_acceptable if damages else 0)
        
        settlement = Settlement(
            case_id=case_id,
            target_amount=target_amount,
            minimum_acceptable=minimum_acceptable,
            transunion_target=data.get('transunion_target', 0),
            experian_target=data.get('experian_target', 0),
            equifax_target=data.get('equifax_target', 0),
            status='pending',
            initial_demand=data.get('initial_demand', target_amount),
            initial_demand_date=datetime.utcnow() if data.get('initial_demand') else None,
            settlement_notes=data.get('notes')
        )
        
        db.add(settlement)
        db.commit()
        
        return jsonify({
            'success': True,
            'settlement_id': settlement.id,
            'message': 'Settlement created successfully'
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlements/<int:settlement_id>', methods=['GET'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_get_settlement(settlement_id):
    """Get settlement details"""
    db = get_db()
    try:
        s = db.query(Settlement).filter_by(id=settlement_id).first()
        if not s:
            return jsonify({'success': False, 'error': 'Settlement not found'}), 404
        
        case = db.query(Case).filter_by(id=s.case_id).first()
        client = None
        analysis = None
        damages = None
        score = None
        
        if case:
            client = db.query(Client).filter_by(id=case.client_id).first()
            if case.analysis_id:
                analysis = db.query(Analysis).filter_by(id=case.analysis_id).first()
                damages = db.query(Damages).filter_by(analysis_id=case.analysis_id).first()
                score = db.query(CaseScore).filter_by(analysis_id=case.analysis_id).first()
        
        return jsonify({
            'success': True,
            'settlement': {
                'id': s.id,
                'case_id': s.case_id,
                'client_name': client.name if client else 'Unknown',
                'client_id': client.id if client else None,
                'target_amount': s.target_amount,
                'minimum_acceptable': s.minimum_acceptable,
                'initial_demand': s.initial_demand,
                'initial_demand_date': s.initial_demand_date.isoformat() if s.initial_demand_date else None,
                'counter_offer_1': s.counter_offer_1,
                'counter_offer_1_date': s.counter_offer_1_date.isoformat() if s.counter_offer_1_date else None,
                'counter_offer_2': s.counter_offer_2,
                'counter_offer_2_date': s.counter_offer_2_date.isoformat() if s.counter_offer_2_date else None,
                'final_amount': s.final_amount,
                'status': s.status,
                'settled_at': s.settled_at.isoformat() if s.settled_at else None,
                'settlement_notes': s.settlement_notes,
                'payment_received': s.payment_received,
                'payment_amount': s.payment_amount,
                'payment_date': s.payment_date.isoformat() if s.payment_date else None,
                'contingency_earned': s.contingency_earned,
                'transunion_target': s.transunion_target,
                'experian_target': s.experian_target,
                'equifax_target': s.equifax_target,
                'created_at': s.created_at.isoformat() if s.created_at else None,
                'updated_at': s.updated_at.isoformat() if s.updated_at else None
            },
            'case': {
                'id': case.id if case else None,
                'case_number': case.case_number if case else None,
                'contingency_percent': case.contingency_percent if case else 0
            } if case else None,
            'damages': {
                'total_exposure': damages.total_exposure if damages else 0,
                'settlement_target': damages.settlement_target if damages else 0,
                'minimum_acceptable': damages.minimum_acceptable if damages else 0
            } if damages else None,
            'score': {
                'total_score': score.total_score if score else 0,
                'case_strength': score.case_strength if score else None,
                'settlement_probability': score.settlement_probability if score else 0
            } if score else None
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlements/<int:settlement_id>', methods=['PUT'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_update_settlement(settlement_id):
    """Update settlement details"""
    db = get_db()
    try:
        s = db.query(Settlement).filter_by(id=settlement_id).first()
        if not s:
            return jsonify({'success': False, 'error': 'Settlement not found'}), 404
        
        data = request.json
        
        updatable = ['target_amount', 'minimum_acceptable', 'initial_demand', 'status',
                     'settlement_notes', 'transunion_target', 'experian_target', 'equifax_target']
        
        for field in updatable:
            if field in data:
                setattr(s, field, data[field])
        
        if 'initial_demand' in data and data['initial_demand'] and not s.initial_demand_date:
            s.initial_demand_date = datetime.utcnow()
        
        if 'status' in data and data['status'] == 'demand_sent' and not s.initial_demand_date:
            s.initial_demand_date = datetime.utcnow()
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Settlement updated'})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlements/<int:settlement_id>/offer', methods=['POST'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_add_counter_offer(settlement_id):
    """Add a counter-offer to settlement"""
    db = get_db()
    try:
        s = db.query(Settlement).filter_by(id=settlement_id).first()
        if not s:
            return jsonify({'success': False, 'error': 'Settlement not found'}), 404
        
        data = request.json
        amount = data.get('amount')
        
        if not amount:
            return jsonify({'success': False, 'error': 'Offer amount is required'}), 400
        
        if not s.counter_offer_1:
            s.counter_offer_1 = amount
            s.counter_offer_1_date = datetime.utcnow()
            s.status = 'negotiating'
            offer_num = 1
        elif not s.counter_offer_2:
            s.counter_offer_2 = amount
            s.counter_offer_2_date = datetime.utcnow()
            offer_num = 2
        else:
            return jsonify({'success': False, 'error': 'Maximum of 2 counter-offers allowed. Use settle endpoint to finalize.'}), 400
        
        if data.get('notes'):
            current_notes = s.settlement_notes or ''
            s.settlement_notes = f"[Counter-Offer {offer_num}: ${amount:,.2f}] {data.get('notes')}\n{current_notes}"
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'Counter-offer {offer_num} recorded',
            'offer_number': offer_num,
            'amount': amount
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlements/<int:settlement_id>/settle', methods=['POST'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_mark_settled(settlement_id):
    """Mark settlement as accepted/settled with final amount"""
    db = get_db()
    try:
        s = db.query(Settlement).filter_by(id=settlement_id).first()
        if not s:
            return jsonify({'success': False, 'error': 'Settlement not found'}), 404
        
        data = request.json
        final_amount = data.get('final_amount')
        
        if not final_amount:
            return jsonify({'success': False, 'error': 'Final settlement amount is required'}), 400
        
        s.final_amount = final_amount
        s.status = 'accepted'
        s.settled_at = datetime.utcnow()
        
        if data.get('notes'):
            current_notes = s.settlement_notes or ''
            s.settlement_notes = f"[SETTLED ${final_amount:,.2f}] {data.get('notes')}\n{current_notes}"
        
        case = db.query(Case).filter_by(id=s.case_id).first()
        if case:
            contingency_percent = case.contingency_percent or 0
            s.contingency_earned = final_amount * (contingency_percent / 100)
            case.status = 'settled'
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Settlement marked as accepted',
            'final_amount': final_amount,
            'contingency_earned': s.contingency_earned
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlements/<int:settlement_id>/reject', methods=['POST'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_mark_rejected(settlement_id):
    """Mark settlement as rejected"""
    db = get_db()
    try:
        s = db.query(Settlement).filter_by(id=settlement_id).first()
        if not s:
            return jsonify({'success': False, 'error': 'Settlement not found'}), 404
        
        data = request.json
        
        s.status = 'rejected'
        
        if data.get('notes'):
            current_notes = s.settlement_notes or ''
            s.settlement_notes = f"[REJECTED] {data.get('notes')}\n{current_notes}"
        
        if data.get('move_to_litigation'):
            s.status = 'litigated'
        
        db.commit()
        
        return jsonify({'success': True, 'message': 'Settlement marked as rejected'})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlements/<int:settlement_id>/payment', methods=['POST'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_record_payment(settlement_id):
    """Record payment received for settlement"""
    db = get_db()
    try:
        s = db.query(Settlement).filter_by(id=settlement_id).first()
        if not s:
            return jsonify({'success': False, 'error': 'Settlement not found'}), 404
        
        data = request.json
        payment_amount = data.get('amount')
        
        if not payment_amount:
            return jsonify({'success': False, 'error': 'Payment amount is required'}), 400
        
        s.payment_received = True
        s.payment_amount = payment_amount
        s.payment_date = datetime.utcnow()
        
        case = db.query(Case).filter_by(id=s.case_id).first()
        if case:
            contingency_percent = case.contingency_percent or 0
            s.contingency_earned = payment_amount * (contingency_percent / 100)
        
        if data.get('notes'):
            current_notes = s.settlement_notes or ''
            s.settlement_notes = f"[PAYMENT RECEIVED ${payment_amount:,.2f}] {data.get('notes')}\n{current_notes}"
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Payment recorded',
            'payment_amount': payment_amount,
            'contingency_earned': s.contingency_earned
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/settlements/stats', methods=['GET'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_settlement_stats():
    """Get settlement statistics for analytics"""
    db = get_db()
    try:
        from datetime import date, timedelta
        from sqlalchemy import func
        
        today = date.today()
        first_of_month = today.replace(day=1)
        first_of_last_month = (first_of_month - timedelta(days=1)).replace(day=1)
        
        all_settlements = db.query(Settlement).all()
        
        total_settled = 0
        total_pending = 0
        total_contingency = 0
        settled_amounts = []
        this_month_settled = 0
        last_month_settled = 0
        
        status_counts = {
            'pending': 0,
            'demand_sent': 0,
            'negotiating': 0,
            'accepted': 0,
            'rejected': 0,
            'litigated': 0
        }
        
        for s in all_settlements:
            status = s.status or 'pending'
            if status in status_counts:
                status_counts[status] += 1
            
            if status == 'accepted':
                if s.final_amount:
                    total_settled += s.final_amount
                    settled_amounts.append(s.final_amount)
                    
                    if s.settled_at and s.settled_at.date() >= first_of_month:
                        this_month_settled += s.final_amount
                    elif s.settled_at and s.settled_at.date() >= first_of_last_month and s.settled_at.date() < first_of_month:
                        last_month_settled += s.final_amount
            else:
                total_pending += s.target_amount or 0
            
            if s.contingency_earned:
                total_contingency += s.contingency_earned
        
        total_count = len(all_settlements)
        accepted_count = status_counts['accepted']
        success_rate = (accepted_count / total_count * 100) if total_count > 0 else 0
        avg_settlement = sum(settled_amounts) / len(settled_amounts) if settled_amounts else 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_settled': total_settled,
                'total_pending_value': total_pending,
                'total_contingency': total_contingency,
                'avg_settlement': avg_settlement,
                'success_rate': round(success_rate, 1),
                'total_count': total_count,
                'accepted_count': accepted_count,
                'status_counts': status_counts,
                'this_month_settled': this_month_settled,
                'last_month_settled': last_month_settled,
                'month_change': this_month_settled - last_month_settled
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/case/<int:case_id>/settlement', methods=['GET'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_get_case_settlement(case_id):
    """Get settlement for a specific case"""
    db = get_db()
    try:
        settlement = db.query(Settlement).filter_by(case_id=case_id).first()
        
        if not settlement:
            case = db.query(Case).filter_by(id=case_id).first()
            damages = None
            score = None
            
            if case and case.analysis_id:
                damages = db.query(Damages).filter_by(analysis_id=case.analysis_id).first()
                score = db.query(CaseScore).filter_by(analysis_id=case.analysis_id).first()
            
            return jsonify({
                'success': True,
                'exists': False,
                'can_create': score.total_score >= 6 if score else False,
                'suggested_target': damages.settlement_target if damages else 0,
                'suggested_minimum': damages.minimum_acceptable if damages else 0
            })
        
        return jsonify({
            'success': True,
            'exists': True,
            'settlement': {
                'id': settlement.id,
                'status': settlement.status,
                'target_amount': settlement.target_amount,
                'initial_demand': settlement.initial_demand,
                'counter_offer_1': settlement.counter_offer_1,
                'counter_offer_2': settlement.counter_offer_2,
                'final_amount': settlement.final_amount,
                'settled_at': settlement.settled_at.isoformat() if settlement.settled_at else None,
                'payment_received': settlement.payment_received,
                'contingency_earned': settlement.contingency_earned
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


# ============================================================
# FURNISHER INTELLIGENCE DATABASE API
# ============================================================

@app.route('/api/furnishers', methods=['GET'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_list_furnishers():
    """List all furnishers with optional filters"""
    db = get_db()
    try:
        query = db.query(Furnisher)
        
        industry = request.args.get('industry')
        if industry:
            query = query.filter(Furnisher.industry == industry)
        
        search = request.args.get('search', '').strip()
        if search:
            query = query.filter(Furnisher.name.ilike(f'%{search}%'))
        
        furnishers = query.order_by(Furnisher.name).all()
        
        result = []
        for f in furnishers:
            stats = f.stats
            result.append({
                'id': f.id,
                'name': f.name,
                'industry': f.industry,
                'parent_company': f.parent_company,
                'total_disputes': stats.total_disputes if stats else 0,
                'round_1_delete_rate': round((stats.round_1_deleted / stats.total_disputes * 100) if stats and stats.total_disputes > 0 else 0, 1),
                'round_2_delete_rate': round((stats.round_2_deleted / (stats.round_1_verified or 1) * 100) if stats and stats.round_1_verified > 0 else 0, 1),
                'avg_response_days': round(stats.avg_response_days, 1) if stats else 0,
                'settlement_count': stats.settlement_count if stats else 0,
                'settlement_avg': round(stats.settlement_avg, 2) if stats else 0,
                'created_at': f.created_at.isoformat() if f.created_at else None
            })
        
        return jsonify({'success': True, 'furnishers': result})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/furnishers', methods=['POST'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_create_furnisher():
    """Create a new furnisher"""
    db = get_db()
    try:
        data = request.get_json() or {}
        
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'success': False, 'error': 'Furnisher name is required'}), 400
        
        existing = db.query(Furnisher).filter(Furnisher.name.ilike(name)).first()
        if existing:
            return jsonify({'success': False, 'error': 'Furnisher with this name already exists', 'existing_id': existing.id}), 400
        
        furnisher = Furnisher(
            name=name,
            alternate_names=data.get('alternate_names', []),
            industry=data.get('industry'),
            parent_company=data.get('parent_company'),
            address=data.get('address'),
            phone=data.get('phone'),
            fax=data.get('fax'),
            email=data.get('email'),
            website=data.get('website'),
            dispute_address=data.get('dispute_address'),
            notes=data.get('notes')
        )
        db.add(furnisher)
        db.flush()
        
        stats = FurnisherStats(furnisher_id=furnisher.id)
        db.add(stats)
        db.commit()
        
        return jsonify({
            'success': True,
            'furnisher': {
                'id': furnisher.id,
                'name': furnisher.name,
                'industry': furnisher.industry
            }
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/furnishers/<int:furnisher_id>', methods=['GET'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_get_furnisher(furnisher_id):
    """Get furnisher details with stats"""
    db = get_db()
    try:
        furnisher = db.query(Furnisher).filter_by(id=furnisher_id).first()
        if not furnisher:
            return jsonify({'success': False, 'error': 'Furnisher not found'}), 404
        
        stats = furnisher.stats
        
        related_items = db.query(DisputeItem).filter(
            DisputeItem.creditor_name.ilike(f'%{furnisher.name}%')
        ).order_by(DisputeItem.created_at.desc()).limit(20).all()
        
        related_clients = []
        seen_clients = set()
        for item in related_items:
            if item.client_id not in seen_clients:
                client = db.query(Client).filter_by(id=item.client_id).first()
                if client:
                    related_clients.append({
                        'id': client.id,
                        'name': client.name,
                        'status': item.status,
                        'dispute_round': item.dispute_round
                    })
                    seen_clients.add(item.client_id)
        
        return jsonify({
            'success': True,
            'furnisher': {
                'id': furnisher.id,
                'name': furnisher.name,
                'alternate_names': furnisher.alternate_names or [],
                'industry': furnisher.industry,
                'parent_company': furnisher.parent_company,
                'address': furnisher.address,
                'phone': furnisher.phone,
                'fax': furnisher.fax,
                'email': furnisher.email,
                'website': furnisher.website,
                'dispute_address': furnisher.dispute_address,
                'notes': furnisher.notes,
                'created_at': furnisher.created_at.isoformat() if furnisher.created_at else None,
                'updated_at': furnisher.updated_at.isoformat() if furnisher.updated_at else None
            },
            'stats': {
                'total_disputes': stats.total_disputes if stats else 0,
                'round_1': {
                    'verified': stats.round_1_verified if stats else 0,
                    'deleted': stats.round_1_deleted if stats else 0,
                    'updated': stats.round_1_updated if stats else 0,
                    'delete_rate': round((stats.round_1_deleted / stats.total_disputes * 100) if stats and stats.total_disputes > 0 else 0, 1)
                },
                'round_2': {
                    'verified': stats.round_2_verified if stats else 0,
                    'deleted': stats.round_2_deleted if stats else 0,
                    'updated': stats.round_2_updated if stats else 0,
                    'delete_rate': round((stats.round_2_deleted / (stats.round_1_verified or 1) * 100) if stats and stats.round_1_verified > 0 else 0, 1)
                },
                'round_3': {
                    'verified': stats.round_3_verified if stats else 0,
                    'deleted': stats.round_3_deleted if stats else 0,
                    'updated': stats.round_3_updated if stats else 0,
                    'delete_rate': round((stats.round_3_deleted / (stats.round_2_verified or 1) * 100) if stats and stats.round_2_verified > 0 else 0, 1)
                },
                'mov': {
                    'requests_sent': stats.mov_requests_sent if stats else 0,
                    'provided': stats.mov_provided if stats else 0,
                    'failed': stats.mov_failed if stats else 0,
                    'failure_rate': round((stats.mov_failed / (stats.mov_requests_sent or 1) * 100) if stats and stats.mov_requests_sent > 0 else 0, 1)
                },
                'avg_response_days': round(stats.avg_response_days, 1) if stats else 0,
                'settlement': {
                    'count': stats.settlement_count if stats else 0,
                    'total': stats.settlement_total if stats else 0,
                    'avg': round(stats.settlement_avg, 2) if stats else 0
                },
                'violation_count': stats.violation_count if stats else 0,
                'reinsertion_count': stats.reinsertion_count if stats else 0
            },
            'related_clients': related_clients[:10]
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/furnishers/<int:furnisher_id>', methods=['PUT'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_update_furnisher(furnisher_id):
    """Update furnisher info"""
    db = get_db()
    try:
        furnisher = db.query(Furnisher).filter_by(id=furnisher_id).first()
        if not furnisher:
            return jsonify({'success': False, 'error': 'Furnisher not found'}), 404
        
        data = request.get_json() or {}
        
        if 'name' in data:
            name = data['name'].strip()
            existing = db.query(Furnisher).filter(Furnisher.name.ilike(name), Furnisher.id != furnisher_id).first()
            if existing:
                return jsonify({'success': False, 'error': 'Furnisher with this name already exists'}), 400
            furnisher.name = name
        
        if 'alternate_names' in data:
            furnisher.alternate_names = data['alternate_names']
        if 'industry' in data:
            furnisher.industry = data['industry']
        if 'parent_company' in data:
            furnisher.parent_company = data['parent_company']
        if 'address' in data:
            furnisher.address = data['address']
        if 'phone' in data:
            furnisher.phone = data['phone']
        if 'fax' in data:
            furnisher.fax = data['fax']
        if 'email' in data:
            furnisher.email = data['email']
        if 'website' in data:
            furnisher.website = data['website']
        if 'dispute_address' in data:
            furnisher.dispute_address = data['dispute_address']
        if 'notes' in data:
            furnisher.notes = data['notes']
        
        furnisher.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({'success': True, 'message': 'Furnisher updated'})
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/furnishers/<int:furnisher_id>/stats', methods=['GET'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_get_furnisher_stats(furnisher_id):
    """Get detailed stats for a furnisher"""
    db = get_db()
    try:
        furnisher = db.query(Furnisher).filter_by(id=furnisher_id).first()
        if not furnisher:
            return jsonify({'success': False, 'error': 'Furnisher not found'}), 404
        
        stats = furnisher.stats
        if not stats:
            return jsonify({
                'success': True,
                'stats': None,
                'message': 'No stats available for this furnisher'
            })
        
        total = stats.total_disputes or 1
        r1_total = stats.round_1_verified + stats.round_1_deleted + stats.round_1_updated
        r2_total = stats.round_2_verified + stats.round_2_deleted + stats.round_2_updated
        r3_total = stats.round_3_verified + stats.round_3_deleted + stats.round_3_updated
        
        overall_delete_rate = 0
        if total > 0:
            total_deleted = stats.round_1_deleted + stats.round_2_deleted + stats.round_3_deleted
            overall_delete_rate = round(total_deleted / total * 100, 1)
        
        strategy = "Standard dispute approach"
        if stats.round_1_deleted > stats.round_1_verified and overall_delete_rate > 30:
            strategy = "High success rate - Strong first-round dispute recommended"
        elif stats.mov_failed > stats.mov_provided:
            strategy = "Focus on MOV demands - This furnisher often fails to provide verification"
        elif stats.round_2_deleted > stats.round_1_deleted:
            strategy = "Push to Round 2 - Better success after initial dispute"
        elif stats.settlement_count > 0:
            strategy = f"Settlement possible - Average ${stats.settlement_avg:,.0f}"
        elif stats.violation_count > 0:
            strategy = "Document violations - History of FCRA violations detected"
        
        return jsonify({
            'success': True,
            'stats': {
                'total_disputes': stats.total_disputes,
                'round_1': {
                    'verified': stats.round_1_verified,
                    'deleted': stats.round_1_deleted,
                    'updated': stats.round_1_updated,
                    'total': r1_total,
                    'delete_rate': round((stats.round_1_deleted / r1_total * 100) if r1_total > 0 else 0, 1)
                },
                'round_2': {
                    'verified': stats.round_2_verified,
                    'deleted': stats.round_2_deleted,
                    'updated': stats.round_2_updated,
                    'total': r2_total,
                    'delete_rate': round((stats.round_2_deleted / r2_total * 100) if r2_total > 0 else 0, 1)
                },
                'round_3': {
                    'verified': stats.round_3_verified,
                    'deleted': stats.round_3_deleted,
                    'updated': stats.round_3_updated,
                    'total': r3_total,
                    'delete_rate': round((stats.round_3_deleted / r3_total * 100) if r3_total > 0 else 0, 1)
                },
                'mov': {
                    'requests_sent': stats.mov_requests_sent,
                    'provided': stats.mov_provided,
                    'failed': stats.mov_failed,
                    'failure_rate': round((stats.mov_failed / (stats.mov_requests_sent or 1) * 100) if stats.mov_requests_sent > 0 else 0, 1)
                },
                'avg_response_days': round(stats.avg_response_days, 1),
                'settlement': {
                    'count': stats.settlement_count,
                    'total': stats.settlement_total,
                    'avg': round(stats.settlement_avg, 2)
                },
                'violation_count': stats.violation_count,
                'reinsertion_count': stats.reinsertion_count,
                'overall_delete_rate': overall_delete_rate,
                'recommended_strategy': strategy
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/furnishers/<int:furnisher_id>/record-outcome', methods=['POST'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_record_furnisher_outcome(furnisher_id):
    """Record a dispute outcome and update furnisher stats"""
    db = get_db()
    try:
        furnisher = db.query(Furnisher).filter_by(id=furnisher_id).first()
        if not furnisher:
            return jsonify({'success': False, 'error': 'Furnisher not found'}), 404
        
        data = request.get_json() or {}
        outcome_type = data.get('outcome_type')
        dispute_round = data.get('dispute_round', 1)
        response_days = data.get('response_days')
        settlement_amount = data.get('settlement_amount')
        is_violation = data.get('is_violation', False)
        is_reinsertion = data.get('is_reinsertion', False)
        is_mov_request = data.get('is_mov_request', False)
        mov_provided = data.get('mov_provided')
        
        if not outcome_type:
            return jsonify({'success': False, 'error': 'outcome_type is required'}), 400
        
        stats = furnisher.stats
        if not stats:
            stats = FurnisherStats(furnisher_id=furnisher.id)
            db.add(stats)
        
        stats.total_disputes = (stats.total_disputes or 0) + 1
        
        if dispute_round == 1:
            if outcome_type == 'verified':
                stats.round_1_verified = (stats.round_1_verified or 0) + 1
            elif outcome_type == 'deleted':
                stats.round_1_deleted = (stats.round_1_deleted or 0) + 1
            elif outcome_type == 'updated':
                stats.round_1_updated = (stats.round_1_updated or 0) + 1
        elif dispute_round == 2:
            if outcome_type == 'verified':
                stats.round_2_verified = (stats.round_2_verified or 0) + 1
            elif outcome_type == 'deleted':
                stats.round_2_deleted = (stats.round_2_deleted or 0) + 1
            elif outcome_type == 'updated':
                stats.round_2_updated = (stats.round_2_updated or 0) + 1
        elif dispute_round >= 3:
            if outcome_type == 'verified':
                stats.round_3_verified = (stats.round_3_verified or 0) + 1
            elif outcome_type == 'deleted':
                stats.round_3_deleted = (stats.round_3_deleted or 0) + 1
            elif outcome_type == 'updated':
                stats.round_3_updated = (stats.round_3_updated or 0) + 1
        
        if response_days is not None:
            current_avg = stats.avg_response_days or 0
            current_count = stats.total_disputes - 1
            if current_count > 0:
                stats.avg_response_days = (current_avg * current_count + response_days) / stats.total_disputes
            else:
                stats.avg_response_days = response_days
        
        if is_mov_request:
            stats.mov_requests_sent = (stats.mov_requests_sent or 0) + 1
            if mov_provided is True:
                stats.mov_provided = (stats.mov_provided or 0) + 1
            elif mov_provided is False:
                stats.mov_failed = (stats.mov_failed or 0) + 1
        
        if settlement_amount and settlement_amount > 0:
            stats.settlement_count = (stats.settlement_count or 0) + 1
            stats.settlement_total = (stats.settlement_total or 0) + settlement_amount
            stats.settlement_avg = stats.settlement_total / stats.settlement_count
        
        if is_violation:
            stats.violation_count = (stats.violation_count or 0) + 1
        
        if is_reinsertion:
            stats.reinsertion_count = (stats.reinsertion_count or 0) + 1
        
        stats.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Outcome recorded',
            'stats': {
                'total_disputes': stats.total_disputes,
                'round_1_deleted': stats.round_1_deleted,
                'round_2_deleted': stats.round_2_deleted,
                'round_3_deleted': stats.round_3_deleted
            }
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/furnishers/leaderboard', methods=['GET'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_furnisher_leaderboard():
    """Get furnisher leaderboard - top/bottom performers"""
    db = get_db()
    try:
        metric = request.args.get('metric', 'deletion_rate')
        limit = int(request.args.get('limit', 10))
        order = request.args.get('order', 'desc')
        
        furnishers = db.query(Furnisher).join(FurnisherStats).filter(FurnisherStats.total_disputes >= 1).all()
        
        results = []
        for f in furnishers:
            stats = f.stats
            if not stats:
                continue
            
            total = stats.total_disputes or 1
            total_deleted = (stats.round_1_deleted or 0) + (stats.round_2_deleted or 0) + (stats.round_3_deleted or 0)
            deletion_rate = total_deleted / total * 100
            
            r1_total = (stats.round_1_verified or 0) + (stats.round_1_deleted or 0) + (stats.round_1_updated or 0)
            r1_delete_rate = (stats.round_1_deleted / r1_total * 100) if r1_total > 0 else 0
            
            mov_failure_rate = (stats.mov_failed / (stats.mov_requests_sent or 1) * 100) if (stats.mov_requests_sent or 0) > 0 else 0
            
            results.append({
                'id': f.id,
                'name': f.name,
                'industry': f.industry,
                'total_disputes': stats.total_disputes,
                'deletion_rate': round(deletion_rate, 1),
                'r1_delete_rate': round(r1_delete_rate, 1),
                'avg_response_days': round(stats.avg_response_days or 0, 1),
                'settlement_avg': round(stats.settlement_avg or 0, 2),
                'settlement_count': stats.settlement_count or 0,
                'mov_failure_rate': round(mov_failure_rate, 1),
                'violation_count': stats.violation_count or 0
            })
        
        sort_key = {
            'deletion_rate': lambda x: x['deletion_rate'],
            'r1_delete_rate': lambda x: x['r1_delete_rate'],
            'response_time': lambda x: x['avg_response_days'],
            'settlement_avg': lambda x: x['settlement_avg'],
            'total_disputes': lambda x: x['total_disputes'],
            'mov_failure_rate': lambda x: x['mov_failure_rate'],
            'violations': lambda x: x['violation_count']
        }.get(metric, lambda x: x['deletion_rate'])
        
        reverse_order = order == 'desc' if metric != 'response_time' else order == 'asc'
        results.sort(key=sort_key, reverse=reverse_order)
        
        return jsonify({
            'success': True,
            'leaderboard': results[:limit],
            'metric': metric,
            'order': order,
            'total_furnishers': len(results)
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/furnishers/populate', methods=['POST'])
@require_staff(roles=['admin'])
def api_populate_furnishers():
    """Populate furnisher database from existing dispute items"""
    db = get_db()
    try:
        from sqlalchemy import func
        
        creditor_counts = db.query(
            DisputeItem.creditor_name,
            func.count(DisputeItem.id).label('count')
        ).filter(
            DisputeItem.creditor_name != None,
            DisputeItem.creditor_name != ''
        ).group_by(DisputeItem.creditor_name).all()
        
        created = 0
        updated = 0
        
        for creditor_name, count in creditor_counts:
            if not creditor_name or len(creditor_name.strip()) < 2:
                continue
            
            name = creditor_name.strip()
            
            existing = db.query(Furnisher).filter(Furnisher.name.ilike(name)).first()
            
            if not existing:
                furnisher = Furnisher(name=name)
                db.add(furnisher)
                db.flush()
                
                stats = FurnisherStats(furnisher_id=furnisher.id)
                db.add(stats)
                created += 1
            else:
                furnisher = existing
                stats = furnisher.stats
                if not stats:
                    stats = FurnisherStats(furnisher_id=furnisher.id)
                    db.add(stats)
                updated += 1
            
            items = db.query(DisputeItem).filter(
                DisputeItem.creditor_name.ilike(name)
            ).all()
            
            stats.total_disputes = len(items)
            
            for item in items:
                round_num = item.dispute_round or 1
                status = item.status or ''
                
                if round_num == 1:
                    if status == 'deleted':
                        stats.round_1_deleted = (stats.round_1_deleted or 0) + 1
                    elif status == 'updated':
                        stats.round_1_updated = (stats.round_1_updated or 0) + 1
                    elif status in ['sent', 'no_change', 'no_answer']:
                        stats.round_1_verified = (stats.round_1_verified or 0) + 1
                elif round_num == 2:
                    if status == 'deleted':
                        stats.round_2_deleted = (stats.round_2_deleted or 0) + 1
                    elif status == 'updated':
                        stats.round_2_updated = (stats.round_2_updated or 0) + 1
                    elif status in ['sent', 'no_change', 'no_answer']:
                        stats.round_2_verified = (stats.round_2_verified or 0) + 1
                elif round_num >= 3:
                    if status == 'deleted':
                        stats.round_3_deleted = (stats.round_3_deleted or 0) + 1
                    elif status == 'updated':
                        stats.round_3_updated = (stats.round_3_updated or 0) + 1
                    elif status in ['sent', 'no_change', 'no_answer']:
                        stats.round_3_verified = (stats.round_3_verified or 0) + 1
            
            stats.updated_at = datetime.utcnow()
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': f'Populated furnisher database',
            'created': created,
            'updated': updated,
            'total': created + updated
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/furnishers/match', methods=['POST'])
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def api_match_furnisher():
    """Match a creditor name to an existing furnisher"""
    db = get_db()
    try:
        data = request.get_json() or {}
        creditor_name = data.get('creditor_name', '').strip()
        
        if not creditor_name:
            return jsonify({'success': False, 'error': 'creditor_name is required'}), 400
        
        exact = db.query(Furnisher).filter(Furnisher.name.ilike(creditor_name)).first()
        if exact:
            return jsonify({
                'success': True,
                'match_type': 'exact',
                'furnisher': {
                    'id': exact.id,
                    'name': exact.name,
                    'industry': exact.industry
                }
            })
        
        partial = db.query(Furnisher).filter(
            Furnisher.name.ilike(f'%{creditor_name}%')
        ).limit(5).all()
        
        if partial:
            return jsonify({
                'success': True,
                'match_type': 'partial',
                'matches': [{'id': f.id, 'name': f.name, 'industry': f.industry} for f in partial]
            })
        
        return jsonify({
            'success': True,
            'match_type': 'none',
            'message': 'No matching furnisher found. Consider creating a new one.'
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/dashboard/furnishers')
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def dashboard_furnishers():
    """Furnisher intelligence database dashboard"""
    db = get_db()
    try:
        furnishers = db.query(Furnisher).order_by(Furnisher.name).all()
        
        total_furnishers = len(furnishers)
        total_disputes = 0
        best_deletion = None
        best_deletion_rate = 0
        worst_response = None
        worst_response_days = 0
        most_common = None
        most_common_count = 0
        
        for f in furnishers:
            stats = f.stats
            if stats:
                total_disputes += stats.total_disputes or 0
                
                if stats.total_disputes and stats.total_disputes > most_common_count:
                    most_common = f.name
                    most_common_count = stats.total_disputes
                
                if stats.total_disputes and stats.total_disputes > 0:
                    del_rate = (stats.round_1_deleted or 0) / stats.total_disputes * 100
                    if del_rate > best_deletion_rate:
                        best_deletion = f.name
                        best_deletion_rate = del_rate
                
                if (stats.avg_response_days or 0) > worst_response_days:
                    worst_response = f.name
                    worst_response_days = stats.avg_response_days or 0
        
        industries = ['bank', 'collection_agency', 'credit_card', 'auto_loan', 'mortgage', 'medical', 'utility', 'student_loan', 'other']
        
        return render_template('furnishers.html',
            furnishers=furnishers,
            total_furnishers=total_furnishers,
            total_disputes=total_disputes,
            best_deletion=best_deletion,
            best_deletion_rate=round(best_deletion_rate, 1),
            worst_response=worst_response,
            worst_response_days=round(worst_response_days, 1),
            most_common=most_common,
            most_common_count=most_common_count,
            industries=industries
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error loading furnishers: {e}", 500
    finally:
        db.close()


@app.route('/dashboard/furnisher/<int:furnisher_id>')
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def dashboard_furnisher_detail(furnisher_id):
    """Furnisher profile page"""
    db = get_db()
    try:
        furnisher = db.query(Furnisher).filter_by(id=furnisher_id).first()
        if not furnisher:
            return render_template('error.html', error='Not Found', message='Furnisher not found'), 404
        
        stats = furnisher.stats
        
        related_items = db.query(DisputeItem).filter(
            DisputeItem.creditor_name.ilike(f'%{furnisher.name}%')
        ).order_by(DisputeItem.created_at.desc()).limit(50).all()
        
        related_clients = []
        seen_clients = set()
        for item in related_items:
            if item.client_id not in seen_clients:
                client = db.query(Client).filter_by(id=item.client_id).first()
                if client:
                    related_clients.append({
                        'id': client.id,
                        'name': client.name,
                        'status': item.status,
                        'dispute_round': item.dispute_round,
                        'created_at': item.created_at
                    })
                    seen_clients.add(item.client_id)
        
        strategy = "Standard dispute approach"
        if stats:
            total = stats.total_disputes or 1
            total_deleted = (stats.round_1_deleted or 0) + (stats.round_2_deleted or 0) + (stats.round_3_deleted or 0)
            overall_delete_rate = total_deleted / total * 100
            
            if stats.round_1_deleted and stats.round_1_deleted > (stats.round_1_verified or 0) and overall_delete_rate > 30:
                strategy = "High success rate - Strong first-round dispute recommended"
            elif (stats.mov_failed or 0) > (stats.mov_provided or 0):
                strategy = "Focus on MOV demands - This furnisher often fails to provide verification"
            elif (stats.round_2_deleted or 0) > (stats.round_1_deleted or 0):
                strategy = "Push to Round 2 - Better success after initial dispute"
            elif stats.settlement_count and stats.settlement_count > 0:
                strategy = f"Settlement possible - Average ${stats.settlement_avg:,.0f}"
            elif stats.violation_count and stats.violation_count > 0:
                strategy = "Document violations - History of FCRA violations detected"
        
        industries = ['bank', 'collection_agency', 'credit_card', 'auto_loan', 'mortgage', 'medical', 'utility', 'student_loan', 'other']
        
        return render_template('furnisher_detail.html',
            furnisher=furnisher,
            stats=stats,
            related_clients=related_clients[:20],
            strategy=strategy,
            industries=industries
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error loading furnisher: {e}", 500
    finally:
        db.close()


# ============================================================
# STATUTE OF LIMITATIONS (SOL) CALCULATOR API
# FCRA § 1681p: Earlier of 2 years from discovery or 5 years from occurrence
# ============================================================

from services.sol_calculator import (
    calculate_sol, get_remaining_days, is_expired, get_sol_warning_level,
    get_violations_with_sol_status, get_upcoming_expirations, get_expired_claims,
    get_sol_statistics, check_sol_deadlines, update_violation_sol_dates, format_sol_for_display
)


@app.route('/api/sol/calculate', methods=['POST'])
@require_staff()
def api_sol_calculate():
    """Calculate SOL for given violation/discovery dates"""
    data = request.get_json() or {}
    
    violation_date_str = data.get('violation_date')
    discovery_date_str = data.get('discovery_date')
    
    if not violation_date_str:
        return jsonify({
            'success': False,
            'error': 'violation_date is required'
        }), 400
    
    try:
        violation_date = datetime.fromisoformat(violation_date_str.replace('Z', '+00:00')).date()
        discovery_date = None
        if discovery_date_str:
            discovery_date = datetime.fromisoformat(discovery_date_str.replace('Z', '+00:00')).date()
        
        sol_info = calculate_sol(violation_date, discovery_date)
        formatted = format_sol_for_display(sol_info)
        
        return jsonify({
            'success': True,
            **formatted
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400


@app.route('/api/sol/client/<int:client_id>', methods=['GET'])
@require_staff()
def api_sol_client(client_id):
    """Get SOL status for all violations belonging to a client"""
    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if not client:
            return jsonify({
                'success': False,
                'error': 'Client not found'
            }), 404
        
        violations = get_violations_with_sol_status(db, client_id)
        
        formatted_violations = [format_sol_for_display(v) for v in violations]
        
        critical_count = sum(1 for v in violations if v.get('warning_level') == 'critical')
        warning_count = sum(1 for v in violations if v.get('warning_level') == 'warning')
        expired_count = sum(1 for v in violations if v.get('is_expired', False))
        
        return jsonify({
            'success': True,
            'client_id': client_id,
            'client_name': client.name,
            'violations': formatted_violations,
            'summary': {
                'total': len(violations),
                'critical': critical_count,
                'warning': warning_count,
                'expired': expired_count
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()


@app.route('/api/sol/upcoming', methods=['GET'])
@require_staff()
def api_sol_upcoming():
    """Get all violations with SOL expiring within the specified days"""
    days = request.args.get('days', 90, type=int)
    
    db = get_db()
    try:
        upcoming = get_upcoming_expirations(db, days)
        formatted = [format_sol_for_display(v) for v in upcoming]
        
        stats = get_sol_statistics(db)
        
        return jsonify({
            'success': True,
            'days': days,
            'violations': formatted,
            'stats': stats
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()


@app.route('/api/sol/statistics', methods=['GET'])
@require_staff()
def api_sol_statistics():
    """Get overall SOL statistics"""
    db = get_db()
    try:
        stats = get_sol_statistics(db)
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()


@app.route('/api/sol/violation/<int:violation_id>/update', methods=['POST'])
@require_staff()
def api_sol_violation_update(violation_id):
    """Update SOL dates for a specific violation"""
    data = request.get_json() or {}
    
    violation_date_str = data.get('violation_date')
    discovery_date_str = data.get('discovery_date')
    
    db = get_db()
    try:
        violation_date = None
        discovery_date = None
        
        if violation_date_str:
            violation_date = datetime.fromisoformat(violation_date_str.replace('Z', '+00:00')).date()
        if discovery_date_str:
            discovery_date = datetime.fromisoformat(discovery_date_str.replace('Z', '+00:00')).date()
        
        result = update_violation_sol_dates(db, violation_id, violation_date, discovery_date)
        
        if result.get('error'):
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400
        
        return jsonify({
            'success': True,
            **format_sol_for_display(result)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()


@app.route('/api/sol/check-deadlines', methods=['POST'])
@require_staff(roles=['admin'])
def api_sol_check_deadlines():
    """Manually trigger SOL deadline check (creates alerts)"""
    db = get_db()
    try:
        result = check_sol_deadlines(db)
        
        return jsonify({
            'success': True,
            **result
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        db.close()


@app.route('/dashboard/sol')
@require_staff()
def dashboard_sol():
    """SOL Tracker Dashboard"""
    db = get_db()
    try:
        stats = get_sol_statistics(db)
        
        upcoming_30 = get_upcoming_expirations(db, 30)
        upcoming_60 = get_upcoming_expirations(db, 60)
        upcoming_90 = get_upcoming_expirations(db, 90)
        expired = get_expired_claims(db)
        
        formatted_30 = [format_sol_for_display(v) for v in upcoming_30]
        formatted_60 = [format_sol_for_display(v) for v in upcoming_60]
        formatted_90 = [format_sol_for_display(v) for v in upcoming_90]
        formatted_expired = [format_sol_for_display(v) for v in expired[:20]]
        
        return render_template('sol_dashboard.html',
            stats=stats,
            upcoming_30=formatted_30,
            upcoming_60=formatted_60,
            upcoming_90=formatted_90,
            expired=formatted_expired
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error loading SOL dashboard: {e}", 500
    finally:
        db.close()


# ============================================================
# CFPB COMPLAINT GENERATOR
# ============================================================

CFPB_TEMPLATES = {
    'credit_reporting': {
        'product_type': 'Credit reporting, credit repair services, or other personal consumer reports',
        'issues': {
            'incorrect_info': {
                'label': 'Incorrect information on your report',
                'sub_issues': [
                    'Information belongs to someone else',
                    'Account status incorrect',
                    'Account information incorrect',
                    'Personal information incorrect',
                    'Public record information inaccurate',
                    'Information is outdated',
                    'Information is missing that should be on the report'
                ]
            },
            'investigation': {
                'label': 'Problem with a credit reporting company\'s investigation into an existing problem',
                'sub_issues': [
                    'Their investigation did not fix an error on your report',
                    'Investigation took more than 30 days',
                    'Was not notified of investigation status or results',
                    'Difficulty submitting a dispute or getting information about a dispute over the phone'
                ]
            },
            'improper_use': {
                'label': 'Improper use of your report',
                'sub_issues': [
                    'Report provided to employer without your written authorization',
                    'Credit inquiries on your report that you don\'t recognize',
                    'Received unsolicited financial product or insurance offers after opting out'
                ]
            },
            'fraud_alerts': {
                'label': 'Problem with a credit reporting company\'s fraud alerts or security freeze',
                'sub_issues': [
                    'Unable to place fraud alert',
                    'Unable to place security freeze',
                    'Unable to lift security freeze'
                ]
            },
            'credit_monitoring': {
                'label': 'Problem with credit report or credit score',
                'sub_issues': [
                    'Problem getting free annual credit report',
                    'Problem with credit score or credit report'
                ]
            }
        }
    },
    'debt_collection': {
        'product_type': 'Debt collection',
        'issues': {
            'not_owed': {
                'label': 'Attempts to collect debt not owed',
                'sub_issues': [
                    'Debt is not yours',
                    'Debt was paid',
                    'Debt was discharged in bankruptcy',
                    'Debt is result of identity theft'
                ]
            },
            'communication': {
                'label': 'Communication tactics',
                'sub_issues': [
                    'Frequent or repeated calls',
                    'Called after asked to stop',
                    'Used obscene, profane, or abusive language',
                    'Threatened arrest or jail if debt not paid'
                ]
            },
            'false_statements': {
                'label': 'False statements or representation',
                'sub_issues': [
                    'Attempted to collect wrong amount',
                    'Impersonated attorney, law enforcement, or government official',
                    'Indicated you committed crime by not paying debt',
                    'Indicated you would be arrested if debt not paid'
                ]
            },
            'threats': {
                'label': 'Threatened to take an action we can\'t legally take',
                'sub_issues': [
                    'Threatened to sue on debt older than the statute of limitations',
                    'Threatened to seize or garnish without court approval',
                    'Threatened to report incorrect debt info to credit bureaus'
                ]
            }
        }
    }
}

CRA_COMPANIES = {
    'equifax': {
        'name': 'Equifax Information Services LLC',
        'address': 'P.O. Box 740256, Atlanta, GA 30374'
    },
    'experian': {
        'name': 'Experian Information Solutions, Inc.',
        'address': 'P.O. Box 4500, Allen, TX 75013'
    },
    'transunion': {
        'name': 'TransUnion LLC',
        'address': 'P.O. Box 2000, Chester, PA 19016'
    }
}

os.makedirs("static/cfpb_complaints", exist_ok=True)


@app.route('/api/cfpb/templates', methods=['GET'])
@require_staff(['admin', 'attorney', 'paralegal'])
def api_cfpb_templates():
    """Get available CFPB complaint templates"""
    return jsonify({
        'success': True,
        'templates': CFPB_TEMPLATES,
        'cra_companies': CRA_COMPANIES
    })


@app.route('/api/cfpb/generate', methods=['POST'])
@require_staff(['admin', 'attorney', 'paralegal'])
def api_cfpb_generate():
    """Generate a CFPB complaint with AI-powered narrative"""
    data = request.get_json() or {}
    
    client_id = data.get('client_id')
    case_id = data.get('case_id')
    target_company = data.get('target_company')
    target_type = data.get('target_type')
    product_type = data.get('product_type')
    issue_type = data.get('issue_type')
    sub_issue_type = data.get('sub_issue_type')
    
    if not client_id or not target_company or not target_type or not product_type or not issue_type:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    db = get_db()
    try:
        client_record = db.query(Client).filter_by(id=client_id).first()
        if not client_record:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        violations_data = []
        standing_data = None
        dispute_history = []
        
        if case_id:
            case = db.query(Case).filter_by(id=case_id).first()
            if case and case.analysis_id:
                violations = db.query(Violation).filter_by(analysis_id=case.analysis_id).all()
                violations_data = [{
                    'bureau': v.bureau,
                    'account_name': v.account_name,
                    'fcra_section': v.fcra_section,
                    'violation_type': v.violation_type,
                    'description': v.description,
                    'is_willful': v.is_willful
                } for v in violations]
                
                standing = db.query(Standing).filter_by(analysis_id=case.analysis_id).first()
                if standing:
                    standing_data = {
                        'concrete_harm_type': standing.concrete_harm_type,
                        'concrete_harm_details': standing.concrete_harm_details,
                        'dissemination_details': standing.dissemination_details
                    }
        
        cra_responses = db.query(CRAResponse).filter_by(client_id=client_id).all()
        for resp in cra_responses:
            dispute_history.append({
                'bureau': resp.bureau,
                'round': resp.dispute_round,
                'response_type': resp.response_type,
                'date': resp.response_date.isoformat() if resp.response_date else None
            })
        
        narrative = generate_cfpb_narrative(
            client_record,
            target_company,
            target_type,
            product_type,
            issue_type,
            sub_issue_type,
            violations_data,
            standing_data,
            dispute_history
        )
        
        desired_resolution = generate_desired_resolution(target_type, issue_type)
        
        complaint = CFPBComplaint(
            client_id=client_id,
            case_id=case_id,
            target_company=target_company,
            target_type=target_type,
            product_type=product_type,
            issue_type=issue_type,
            sub_issue_type=sub_issue_type,
            narrative=narrative,
            desired_resolution=desired_resolution,
            status='draft'
        )
        db.add(complaint)
        db.commit()
        
        return jsonify({
            'success': True,
            'complaint': {
                'id': complaint.id,
                'client_id': complaint.client_id,
                'case_id': complaint.case_id,
                'target_company': complaint.target_company,
                'target_type': complaint.target_type,
                'product_type': complaint.product_type,
                'issue_type': complaint.issue_type,
                'sub_issue_type': complaint.sub_issue_type,
                'narrative': complaint.narrative,
                'desired_resolution': complaint.desired_resolution,
                'status': complaint.status,
                'created_at': complaint.created_at.isoformat()
            }
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


def generate_cfpb_narrative(client, target_company, target_type, product_type, issue_type, sub_issue_type, violations, standing, dispute_history):
    """Generate a compelling CFPB complaint narrative using Claude"""
    
    client_name = client.name
    client_address = f"{client.address_street or ''}, {client.address_city or ''}, {client.address_state or ''} {client.address_zip or ''}".strip(', ')
    
    violations_text = ""
    if violations:
        violations_text = "VIOLATIONS IDENTIFIED:\n"
        for v in violations:
            violations_text += f"- {v.get('account_name', 'Unknown Account')}: {v.get('description', 'No description')} (FCRA § {v.get('fcra_section', 'N/A')})\n"
    
    standing_text = ""
    if standing:
        standing_text = f"HARM SUFFERED:\n- Type: {standing.get('concrete_harm_type', 'Not specified')}\n- Details: {standing.get('concrete_harm_details', 'Not specified')}\n"
    
    dispute_text = ""
    if dispute_history:
        dispute_text = "DISPUTE HISTORY:\n"
        for d in dispute_history:
            dispute_text += f"- {d.get('bureau', 'Unknown')}: Round {d.get('round', 'N/A')} - {d.get('response_type', 'Unknown')} ({d.get('date', 'Unknown date')})\n"
    
    prompt = f"""Generate a professional, compelling CFPB complaint narrative for the following situation. The narrative should be written in first person from the consumer's perspective and follow CFPB guidelines.

CONSUMER INFORMATION:
- Name: {client_name}
- Address: {client_address}

COMPLAINT DETAILS:
- Target Company: {target_company}
- Company Type: {target_type}
- Product/Service: {product_type}
- Issue Type: {issue_type}
- Sub-Issue: {sub_issue_type or 'Not specified'}

{violations_text}
{standing_text}
{dispute_text}

Write a detailed narrative (400-600 words) that:
1. Clearly describes the problem in chronological order
2. Includes specific dates, account numbers (partially redacted), and amounts where applicable
3. Explains what attempts were made to resolve the issue directly with the company
4. Describes the impact on the consumer (financial harm, stress, denied credit, etc.)
5. References any relevant FCRA violations
6. Maintains a professional, factual tone

Output ONLY the narrative text, no additional formatting or explanations."""

    try:
        if client is None or 'invalid' in ANTHROPIC_API_KEY.lower():
            return f"""I am writing to file a formal complaint against {target_company} regarding {issue_type}.

On [DATE], I discovered that {target_company} has been reporting inaccurate information on my credit report. Despite my attempts to resolve this matter directly, the company has failed to correct these errors.

I have disputed this information through proper channels, but the issues remain unresolved. This has caused me significant financial harm and emotional distress.

I am requesting immediate investigation and correction of this matter.

[Note: This is a template narrative. Enable Claude API for AI-generated personalized narratives.]"""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text.strip()
    
    except Exception as e:
        print(f"Error generating narrative with Claude: {e}")
        return f"""I am writing to file a formal complaint against {target_company} regarding {issue_type}.

I have identified serious issues with how {target_company} has been handling my credit reporting information. Despite multiple attempts to resolve this matter directly with the company, the problems persist.

The specific issue involves {sub_issue_type or issue_type}. This has caused me financial harm and significant stress.

I have attempted to dispute this information through proper channels, sending written disputes and following up multiple times. However, {target_company} has failed to adequately investigate or correct the inaccurate information.

I am requesting that the CFPB investigate this matter and help me obtain a resolution.

[Detailed timeline and specific information would be included based on case documentation.]"""


def generate_desired_resolution(target_type, issue_type):
    """Generate appropriate desired resolution text"""
    if target_type == 'cra':
        return """I request the following resolution:

1. Conduct a thorough investigation of my dispute within 30 days as required by the FCRA
2. Correct or delete all inaccurate information from my credit report
3. Provide me with written confirmation of the investigation results
4. Provide a free updated copy of my credit report showing the corrections
5. Notify all parties who received my report in the past 6 months of the corrections
6. Implement procedures to prevent this error from recurring
7. Provide monetary compensation for the harm I have suffered"""
    else:
        return """I request the following resolution:

1. Cease all collection activities on this disputed account
2. Provide complete verification of the alleged debt including original creditor documentation
3. Remove all negative credit reporting related to this disputed account
4. Confirm deletion in writing to me and all credit reporting agencies
5. Cease all communication regarding this matter if debt cannot be verified
6. Provide monetary compensation for the harm caused by these practices"""


@app.route('/api/cfpb/complaints', methods=['GET'])
@require_staff(['admin', 'attorney', 'paralegal'])
def api_cfpb_complaints_list():
    """List all CFPB complaints"""
    status = request.args.get('status')
    client_id = request.args.get('client_id')
    
    db = get_db()
    try:
        query = db.query(CFPBComplaint)
        
        if status:
            query = query.filter(CFPBComplaint.status == status)
        if client_id:
            query = query.filter(CFPBComplaint.client_id == int(client_id))
        
        complaints = query.order_by(CFPBComplaint.created_at.desc()).all()
        
        result = []
        for c in complaints:
            client_record = db.query(Client).filter_by(id=c.client_id).first()
            result.append({
                'id': c.id,
                'client_id': c.client_id,
                'client_name': client_record.name if client_record else 'Unknown',
                'case_id': c.case_id,
                'target_company': c.target_company,
                'target_type': c.target_type,
                'product_type': c.product_type,
                'issue_type': c.issue_type,
                'status': c.status,
                'cfpb_complaint_id': c.cfpb_complaint_id,
                'submitted_at': c.submitted_at.isoformat() if c.submitted_at else None,
                'file_path': c.file_path,
                'created_at': c.created_at.isoformat()
            })
        
        return jsonify({
            'success': True,
            'complaints': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/cfpb/complaints/<int:complaint_id>', methods=['GET'])
@require_staff(['admin', 'attorney', 'paralegal'])
def api_cfpb_complaint_detail(complaint_id):
    """Get CFPB complaint details"""
    db = get_db()
    try:
        complaint = db.query(CFPBComplaint).filter_by(id=complaint_id).first()
        if not complaint:
            return jsonify({'success': False, 'error': 'Complaint not found'}), 404
        
        client_record = db.query(Client).filter_by(id=complaint.client_id).first()
        
        return jsonify({
            'success': True,
            'complaint': {
                'id': complaint.id,
                'client_id': complaint.client_id,
                'client_name': client_record.name if client_record else 'Unknown',
                'client_email': client_record.email if client_record else None,
                'client_phone': client_record.phone if client_record else None,
                'client_address': f"{client_record.address_street or ''}, {client_record.address_city or ''}, {client_record.address_state or ''} {client_record.address_zip or ''}" if client_record else '',
                'case_id': complaint.case_id,
                'target_company': complaint.target_company,
                'target_type': complaint.target_type,
                'product_type': complaint.product_type,
                'issue_type': complaint.issue_type,
                'sub_issue_type': complaint.sub_issue_type,
                'narrative': complaint.narrative,
                'desired_resolution': complaint.desired_resolution,
                'status': complaint.status,
                'cfpb_complaint_id': complaint.cfpb_complaint_id,
                'submitted_at': complaint.submitted_at.isoformat() if complaint.submitted_at else None,
                'response_received_at': complaint.response_received_at.isoformat() if complaint.response_received_at else None,
                'company_response': complaint.company_response,
                'file_path': complaint.file_path,
                'created_at': complaint.created_at.isoformat(),
                'updated_at': complaint.updated_at.isoformat() if complaint.updated_at else None
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/cfpb/complaints/<int:complaint_id>', methods=['PUT'])
@require_staff(['admin', 'attorney', 'paralegal'])
def api_cfpb_complaint_update(complaint_id):
    """Update CFPB complaint"""
    data = request.get_json() or {}
    
    db = get_db()
    try:
        complaint = db.query(CFPBComplaint).filter_by(id=complaint_id).first()
        if not complaint:
            return jsonify({'success': False, 'error': 'Complaint not found'}), 404
        
        if 'narrative' in data:
            complaint.narrative = data['narrative']
        if 'desired_resolution' in data:
            complaint.desired_resolution = data['desired_resolution']
        if 'status' in data:
            complaint.status = data['status']
        if 'cfpb_complaint_id' in data:
            complaint.cfpb_complaint_id = data['cfpb_complaint_id']
        if 'company_response' in data:
            complaint.company_response = data['company_response']
        if 'target_company' in data:
            complaint.target_company = data['target_company']
        if 'issue_type' in data:
            complaint.issue_type = data['issue_type']
        if 'sub_issue_type' in data:
            complaint.sub_issue_type = data['sub_issue_type']
        
        complaint.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Complaint updated successfully'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/cfpb/complaints/<int:complaint_id>/pdf', methods=['POST'])
@require_staff(['admin', 'attorney', 'paralegal'])
def api_cfpb_complaint_pdf(complaint_id):
    """Generate PDF for CFPB complaint"""
    db = get_db()
    try:
        complaint = db.query(CFPBComplaint).filter_by(id=complaint_id).first()
        if not complaint:
            return jsonify({'success': False, 'error': 'Complaint not found'}), 404
        
        client_record = db.query(Client).filter_by(id=complaint.client_id).first()
        if not client_record:
            return jsonify({'success': False, 'error': 'Client not found'}), 404
        
        pdf_path = generate_cfpb_pdf(complaint, client_record)
        
        complaint.file_path = pdf_path
        complaint.status = 'ready' if complaint.status == 'draft' else complaint.status
        complaint.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({
            'success': True,
            'file_path': pdf_path,
            'message': 'PDF generated successfully'
        })
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


def generate_cfpb_pdf(complaint, client_record):
    """Generate CFPB complaint PDF"""
    from fpdf import FPDF
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^\w\s-]', '', client_record.name).replace(' ', '_')
    filename = f"CFPB_Complaint_{safe_name}_{timestamp}.pdf"
    output_path = f"static/cfpb_complaints/{filename}"
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    if os.path.exists(BRIGHTPATH_LOGO_PATH):
        try:
            pdf.image(BRIGHTPATH_LOGO_PATH, 10, 8, 25)
        except:
            pass
    
    pdf.set_font("Arial", "B", 16)
    pdf.set_xy(40, 10)
    pdf.cell(0, 10, "CFPB COMPLAINT", ln=True, align='C')
    
    pdf.set_font("Arial", "", 10)
    pdf.set_xy(40, 20)
    pdf.cell(0, 5, "Consumer Financial Protection Bureau", ln=True, align='C')
    pdf.cell(0, 5, f"Generated: {datetime.now().strftime('%B %d, %Y')}", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_draw_color(49, 151, 149)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "CONSUMER INFORMATION", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Name: {client_record.name}", ln=True)
    address = f"{client_record.address_street or ''}, {client_record.address_city or ''}, {client_record.address_state or ''} {client_record.address_zip or ''}"
    pdf.cell(0, 6, f"Address: {address.strip(', ')}", ln=True)
    pdf.cell(0, 6, f"Phone: {client_record.phone or 'Not provided'}", ln=True)
    pdf.cell(0, 6, f"Email: {client_record.email or 'Not provided'}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "COMPANY BEING COMPLAINED ABOUT", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Company Name: {complaint.target_company}", ln=True)
    pdf.cell(0, 6, f"Company Type: {complaint.target_type.upper()}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "PRODUCT/SERVICE & ISSUE", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 6, f"Product/Service: {complaint.product_type}")
    pdf.cell(0, 6, f"Issue Type: {complaint.issue_type}", ln=True)
    if complaint.sub_issue_type:
        pdf.cell(0, 6, f"Sub-Issue: {complaint.sub_issue_type}", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "WHAT HAPPENED (NARRATIVE)", ln=True)
    pdf.set_font("Arial", "", 10)
    
    narrative = complaint.narrative or "No narrative provided."
    narrative = narrative.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, narrative)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "DESIRED RESOLUTION", ln=True)
    pdf.set_font("Arial", "", 10)
    
    resolution = complaint.desired_resolution or "No resolution specified."
    resolution = resolution.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, resolution)
    
    pdf.ln(10)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, "CONSUMER CERTIFICATION", ln=True)
    pdf.set_font("Arial", "", 9)
    pdf.multi_cell(0, 5, "I certify that the information provided above is true and correct to the best of my knowledge. I authorize the Consumer Financial Protection Bureau to share this complaint with the company identified above for resolution purposes.")
    
    pdf.ln(10)
    pdf.cell(0, 6, "_____________________________", ln=True)
    pdf.cell(0, 6, f"{client_record.name}", ln=True)
    pdf.cell(0, 6, f"Date: {datetime.now().strftime('%B %d, %Y')}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 4, "This complaint was prepared using the Brightpath Ascend FCRA Litigation Platform. For more information, visit consumerfinance.gov/complaint to file directly with the CFPB.")
    
    pdf.output(output_path)
    return output_path


@app.route('/api/cfpb/complaints/<int:complaint_id>/submit', methods=['POST'])
@require_staff(['admin', 'attorney', 'paralegal'])
def api_cfpb_complaint_submit(complaint_id):
    """Mark CFPB complaint as submitted"""
    data = request.get_json() or {}
    cfpb_complaint_id = data.get('cfpb_complaint_id')
    
    db = get_db()
    try:
        complaint = db.query(CFPBComplaint).filter_by(id=complaint_id).first()
        if not complaint:
            return jsonify({'success': False, 'error': 'Complaint not found'}), 404
        
        complaint.status = 'submitted'
        complaint.submitted_at = datetime.utcnow()
        if cfpb_complaint_id:
            complaint.cfpb_complaint_id = cfpb_complaint_id
        complaint.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Complaint marked as submitted'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/api/cfpb/complaints/<int:complaint_id>/response', methods=['POST'])
@require_staff(['admin', 'attorney', 'paralegal'])
def api_cfpb_complaint_response(complaint_id):
    """Record company response to CFPB complaint"""
    data = request.get_json() or {}
    company_response = data.get('company_response')
    
    if not company_response:
        return jsonify({'success': False, 'error': 'Company response required'}), 400
    
    db = get_db()
    try:
        complaint = db.query(CFPBComplaint).filter_by(id=complaint_id).first()
        if not complaint:
            return jsonify({'success': False, 'error': 'Complaint not found'}), 404
        
        complaint.status = 'response_received'
        complaint.response_received_at = datetime.utcnow()
        complaint.company_response = company_response
        complaint.updated_at = datetime.utcnow()
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Response recorded successfully'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()


@app.route('/dashboard/cfpb')
@require_staff(['admin', 'attorney', 'paralegal'])
def dashboard_cfpb():
    """CFPB Complaints Dashboard"""
    db = get_db()
    try:
        complaints = db.query(CFPBComplaint).order_by(CFPBComplaint.created_at.desc()).all()
        
        complaint_list = []
        for c in complaints:
            client_record = db.query(Client).filter_by(id=c.client_id).first()
            complaint_list.append({
                'id': c.id,
                'client_id': c.client_id,
                'client_name': client_record.name if client_record else 'Unknown',
                'target_company': c.target_company,
                'target_type': c.target_type,
                'issue_type': c.issue_type,
                'status': c.status,
                'cfpb_complaint_id': c.cfpb_complaint_id,
                'submitted_at': c.submitted_at,
                'file_path': c.file_path,
                'created_at': c.created_at
            })
        
        stats = {
            'total': len(complaints),
            'draft': sum(1 for c in complaints if c.status == 'draft'),
            'ready': sum(1 for c in complaints if c.status == 'ready'),
            'submitted': sum(1 for c in complaints if c.status == 'submitted'),
            'response_received': sum(1 for c in complaints if c.status == 'response_received')
        }
        
        clients = db.query(Client).filter(Client.status.in_(['active', 'signup'])).order_by(Client.name).all()
        client_list = [{'id': c.id, 'name': c.name} for c in clients]
        
        return render_template('cfpb_complaints.html',
            complaints=complaint_list,
            stats=stats,
            clients=client_list,
            templates=CFPB_TEMPLATES,
            cra_companies=CRA_COMPANIES
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error loading CFPB dashboard: {e}", 500
    finally:
        db.close()


@app.route('/dashboard/cfpb/generator')
@require_staff(['admin', 'attorney', 'paralegal'])
def dashboard_cfpb_generator():
    """CFPB Complaint Generator Wizard"""
    db = get_db()
    try:
        clients = db.query(Client).filter(Client.status.in_(['active', 'signup'])).order_by(Client.name).all()
        client_list = [{'id': c.id, 'name': c.name, 'email': c.email} for c in clients]
        
        return render_template('cfpb_generator.html',
            clients=client_list,
            templates=CFPB_TEMPLATES,
            cra_companies=CRA_COMPANIES
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error loading CFPB generator: {e}", 500
    finally:
        db.close()


@app.route('/dashboard/cfpb/complaint/<int:complaint_id>')
@require_staff(['admin', 'attorney', 'paralegal'])
def dashboard_cfpb_detail(complaint_id):
    """View/Edit CFPB Complaint"""
    db = get_db()
    try:
        complaint = db.query(CFPBComplaint).filter_by(id=complaint_id).first()
        if not complaint:
            return "Complaint not found", 404
        
        client_record = db.query(Client).filter_by(id=complaint.client_id).first()
        
        complaint_data = {
            'id': complaint.id,
            'client_id': complaint.client_id,
            'client_name': client_record.name if client_record else 'Unknown',
            'client_email': client_record.email if client_record else None,
            'client_address': f"{client_record.address_street or ''}, {client_record.address_city or ''}, {client_record.address_state or ''} {client_record.address_zip or ''}" if client_record else '',
            'case_id': complaint.case_id,
            'target_company': complaint.target_company,
            'target_type': complaint.target_type,
            'product_type': complaint.product_type,
            'issue_type': complaint.issue_type,
            'sub_issue_type': complaint.sub_issue_type,
            'narrative': complaint.narrative,
            'desired_resolution': complaint.desired_resolution,
            'status': complaint.status,
            'cfpb_complaint_id': complaint.cfpb_complaint_id,
            'submitted_at': complaint.submitted_at,
            'response_received_at': complaint.response_received_at,
            'company_response': complaint.company_response,
            'file_path': complaint.file_path,
            'created_at': complaint.created_at
        }
        
        return render_template('cfpb_generator.html',
            complaint=complaint_data,
            clients=[{'id': client_record.id, 'name': client_record.name}] if client_record else [],
            templates=CFPB_TEMPLATES,
            cra_companies=CRA_COMPANIES,
            edit_mode=True
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error loading complaint: {e}", 500
    finally:
        db.close()


# 🚨 GLOBAL ERROR HANDLER: Always return JSON, never HTML
@app.errorhandler(500)
def handle_500_error(error):
    """Handle any unhandled server errors and return JSON"""
    print(f"🚨 UNHANDLED 500 ERROR: {error}")
    import traceback
    traceback.print_exc()
    return jsonify({
        'success': False,
        'error': 'Internal server error (check server logs for details)'
    }), 500


@app.errorhandler(404)
def handle_404_error(error):
    """Handle 404 errors and return JSON"""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "🚀" * 30)
    print("FCRA AUTOMATION SERVER STARTING")
    print("🚀" * 30)
    print(f"\n📡 Listening on port {port}")
    print("✅ Ready to receive credit reports!\n")
    app.run(host='0.0.0.0', port=port, debug=True)
