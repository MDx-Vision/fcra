from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session, jsonify
from functools import wraps
from datetime import datetime, timedelta
import os

portal = Blueprint('portal', __name__, url_prefix='/portal')

# =============================================================================
# CLIENT STAGE ACCESS CONTROL
# =============================================================================
# Stages: lead, analysis_paid, onboarding, pending_payment, active, payment_failed, cancelled
#
# Access Matrix:
# - lead: NO portal access (only /analysis/<token>)
# - analysis_paid: NO portal access (must proceed to onboarding)
# - onboarding: Only onboarding, agreements, profile
# - pending_payment: Only onboarding, agreements, profile (waiting for day 3)
# - active: FULL access
# - payment_failed: Only onboarding, profile (must fix payment)
# - cancelled: NO access
# =============================================================================

# Pages accessible during onboarding (before full access)
ONBOARDING_ALLOWED_PAGES = [
    'portal.onboarding',
    'portal.agreements',
    'portal.profile',
    'portal.api_update_profile',
    'portal.api_croa_progress',
    'portal.api_croa_document',
    'portal.api_croa_current_document',
    'portal.api_croa_sign',
    'portal.api_croa_skip_optional',
    'portal.api_croa_cancellation_status',
    'portal.api_croa_cancel',
    'portal.api_croa_can_begin_services',
    'portal.api_onboarding_sync',
    'portal.api_onboarding_complete_step',
    'portal.api_onboarding_upload',
]

# Stages that have full portal access
FULL_ACCESS_STAGES = ['active']

# Stages that have limited (onboarding) access
LIMITED_ACCESS_STAGES = ['onboarding', 'pending_payment', 'payment_failed']

# Stages that have NO portal access
NO_ACCESS_STAGES = ['lead', 'analysis_paid', 'cancelled']


def get_client_stage():
    """Get the current client's stage from database"""
    from database import get_db, Client

    client_id = get_client_id()
    if not client_id:
        return None

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if client:
            # Default to 'active' for legacy clients without stage set
            return client.client_stage or 'active'
        return None
    finally:
        db.close()


def portal_login_required(f):
    """Decorator to require portal login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # CI auth bypass for testing
        if os.environ.get('CI') == 'true':
            # Set a test client ID in session if not present
            if 'client_id' not in session and 'portal_client_id' not in session:
                from database import get_db, Client
                db = get_db()
                try:
                    # Get first client for testing, or create one if none exist
                    test_client = db.query(Client).first()
                    if not test_client:
                        # Create a test client for CI testing
                        test_client = Client(
                            name='Test Client',
                            first_name='Test',
                            last_name='Client',
                            email='testclient@example.com',
                            phone='555-555-5555',
                            current_dispute_round=2,
                            dispute_status='active',
                            client_stage='active'  # Full access for testing
                        )
                        db.add(test_client)
                        db.commit()
                        db.refresh(test_client)
                    session['portal_client_id'] = test_client.id
                finally:
                    db.close()
            return f(*args, **kwargs)

        # Check both possible session keys (client_id is from existing login system)
        if 'client_id' not in session and 'portal_client_id' not in session:
            flash('Please log in to access your portal', 'error')
            return redirect(url_for('portal_login'))
        return f(*args, **kwargs)
    return decorated_function


def require_stage(*allowed_stages):
    """
    Decorator to require specific client stages for access.

    Usage:
        @require_stage('active')  # Only active clients
        @require_stage('active', 'onboarding')  # Active or onboarding
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip stage check in CI mode
            if os.environ.get('CI') == 'true':
                return f(*args, **kwargs)

            stage = get_client_stage()

            if stage is None:
                flash('Please log in to access your portal', 'error')
                return redirect(url_for('portal_login'))

            if stage not in allowed_stages:
                # Redirect based on current stage
                if stage in NO_ACCESS_STAGES:
                    flash('Please complete your signup first', 'info')
                    return redirect(url_for('get_started'))
                elif stage in LIMITED_ACCESS_STAGES:
                    flash('Please complete your onboarding first', 'info')
                    return redirect(url_for('portal.onboarding'))
                else:
                    # Unknown stage, redirect to onboarding
                    return redirect(url_for('portal.onboarding'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_full_access(f):
    """Decorator to require full portal access (active stage only)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip stage check in CI mode
        if os.environ.get('CI') == 'true':
            return f(*args, **kwargs)

        stage = get_client_stage()

        if stage is None:
            flash('Please log in to access your portal', 'error')
            return redirect(url_for('portal_login'))

        if stage not in FULL_ACCESS_STAGES:
            if stage in NO_ACCESS_STAGES:
                flash('Please complete your signup first', 'info')
                return redirect(url_for('get_started'))
            else:
                flash('Please complete your onboarding to access this page', 'info')
                return redirect(url_for('portal.onboarding'))

        return f(*args, **kwargs)
    return decorated_function


def require_onboarding_access(f):
    """Decorator for pages accessible during onboarding"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip stage check in CI mode
        if os.environ.get('CI') == 'true':
            return f(*args, **kwargs)

        stage = get_client_stage()

        if stage is None:
            flash('Please log in to access your portal', 'error')
            return redirect(url_for('portal_login'))

        # Allow if active OR in limited access stages
        if stage in FULL_ACCESS_STAGES or stage in LIMITED_ACCESS_STAGES:
            return f(*args, **kwargs)

        # No access stages
        flash('Please complete your signup first', 'info')
        return redirect(url_for('get_started'))

    return decorated_function

def get_client_id():
    """Get the client ID from session (supports both old and new session keys)"""
    return session.get('client_id') or session.get('portal_client_id')

def get_current_user():
    """Get current logged-in client as a user-like object"""
    from database import get_db, Client

    client_id = get_client_id()
    if not client_id:
        return None

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=client_id).first()
        if client:
            # Create a user-like object with needed attributes
            class PortalUser:
                def __init__(self, client):
                    self.id = client.id
                    self.first_name = client.first_name or (client.name.split()[0] if client.name else 'Client')
                    self.last_name = client.last_name or (client.name.split()[-1] if client.name and len(client.name.split()) > 1 else '')
                    self.email = client.email
                    self.client = client
            return PortalUser(client)
        return None
    finally:
        db.close()

@portal.route('/offline')
def offline():
    """Offline fallback page for PWA"""
    return render_template('portal/offline.html')

@portal.route('/dashboard')
@portal.route('/')
@portal_login_required
@require_full_access
def dashboard():
    """Main dashboard/case overview page - requires ACTIVE stage"""
    from database import get_db, Client, DisputeItem, Violation, SecondaryBureauFreeze, Analysis, Damages

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    db = get_db()
    try:
        client_id = get_client_id()
        client = db.query(Client).filter_by(id=client_id).first()

        if not client:
            flash('Client not found. Please log in again.', 'error')
            return redirect(url_for('portal_login'))

        # Get dispute items/accounts
        accounts = []
        try:
            accounts = db.query(DisputeItem).filter_by(client_id=client.id).all()
        except:
            pass

        # Calculate total violations value - query through Analysis for more reliable data
        total_violations = 0
        violation_count = 0
        try:
            # First try direct client_id query
            violations = db.query(Violation).filter_by(client_id=client.id).all()

            # If no results, try through Analysis
            if not violations:
                analyses = db.query(Analysis).filter_by(client_id=client.id).all()
                analysis_ids = [a.id for a in analyses]
                if analysis_ids:
                    violations = db.query(Violation).filter(Violation.analysis_id.in_(analysis_ids)).all()

            violation_count = len(violations)

            # Calculate total from statutory damages
            for v in violations:
                # Use max statutory damages if available
                if v.statutory_damages_max:
                    total_violations += v.statutory_damages_max
                elif v.statutory_damages_min:
                    total_violations += v.statutory_damages_min

            # If no statutory damages, check Damages table
            if total_violations == 0:
                analyses = db.query(Analysis).filter_by(client_id=client.id).all()
                for analysis in analyses:
                    damages = db.query(Damages).filter_by(analysis_id=analysis.id).first()
                    if damages and damages.total_estimated:
                        total_violations += damages.total_estimated
        except Exception as e:
            print(f"Error fetching violations: {e}")
            pass

        disputed_accounts = len(accounts)
        bureau_count = len(set(getattr(a, 'bureau', '') for a in accounts if getattr(a, 'bureau', '')))
        if bureau_count == 0:
            bureau_count = 3  # Default to 3 bureaus

        current_round = getattr(client, 'current_round', 1) or 1
        progress_percent = int((current_round / 4) * 100)

        # Days until response
        days_until_response = 0
        if client and hasattr(client, 'last_letter_date') and client.last_letter_date:
            response_due = client.last_letter_date + timedelta(days=30)
            days_until_response = max(0, (response_due - datetime.now()).days)

        # Scores
        starting_score = getattr(client, 'starting_score', None)
        current_score = getattr(client, 'current_score', None)

        return render_template('portal/dashboard.html',
            current_user=current_user,
            client=client,
            accounts=accounts,
            total_violations=total_violations,
            disputed_accounts=disputed_accounts,
            bureau_count=bureau_count,
            current_round=current_round,
            progress_percent=progress_percent,
            days_until_response=days_until_response,
            starting_score=starting_score,
            current_score=current_score
        )
    finally:
        db.close()

@portal.route('/documents')
@portal_login_required
@require_full_access
def documents():
    """Documents page - requires ACTIVE stage"""
    from database import get_db, Client, ClientUpload

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=get_client_id()).first()

        documents = []
        if client:
            try:
                # Query ClientUpload for portal uploads
                uploads = db.query(ClientUpload).filter_by(client_id=client.id).order_by(ClientUpload.uploaded_at.desc()).all()
                # Create document-like objects for template compatibility
                for u in uploads:
                    class DocWrapper:
                        def __init__(self, upload):
                            self.id = upload.id
                            self.name = upload.file_name or 'Unnamed Document'
                            self.file_path = upload.file_path
                            self.document_type = upload.document_type
                            self.created_at = upload.uploaded_at
                    documents.append(DocWrapper(u))
            except Exception as e:
                print(f"Error fetching documents: {e}")
                pass

        return render_template('portal/documents.html',
            current_user=current_user,
            client=client,
            documents=documents
        )
    finally:
        db.close()

@portal.route('/documents/upload', methods=['POST'])
@portal_login_required
def upload_document():
    """Handle document upload"""
    from database import get_db, Client, ClientUpload
    from werkzeug.utils import secure_filename

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    doc_type = request.form.get('doc_type', 'other')
    notes = request.form.get('notes', '')

    # Get CRA response specific fields
    bureau_equifax = request.form.get('bureau_equifax')
    bureau_experian = request.form.get('bureau_experian')
    bureau_transunion = request.form.get('bureau_transunion')
    response_round = request.form.get('response_round')

    # Build bureau string from checkboxes
    bureaus = []
    if bureau_equifax:
        bureaus.append('Equifax')
    if bureau_experian:
        bureaus.append('Experian')
    if bureau_transunion:
        bureaus.append('TransUnion')
    bureau_str = ', '.join(bureaus) if bureaus else None

    # Parse round
    dispute_round = None
    if response_round and response_round.isdigit():
        dispute_round = int(response_round)

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=get_client_id()).first()
        if not client:
            flash('Client not found', 'error')
            return redirect(url_for('portal.documents'))

        # Create upload directory
        upload_dir = os.path.join('static', 'client_uploads', str(client.id))
        os.makedirs(upload_dir, exist_ok=True)

        files_uploaded = 0

        # Handle ID/Proof uploads (multiple files)
        if doc_type == 'id_proof':
            id_files = {
                'dl_front': ('Driver License Front', True),
                'dl_back': ('Driver License Back', False),
                'ssn_front': ('Social Security Card Front', True),
                'ssn_back': ('Social Security Card Back', False),
                'utility_bill': ('Utility Bill', True)
            }

            for field_name, (doc_label, required) in id_files.items():
                file = request.files.get(field_name)
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Add prefix to distinguish files
                    prefixed_filename = f"{field_name}_{filename}"
                    file_path = os.path.join(upload_dir, prefixed_filename)
                    file.save(file_path)
                    file_size = os.path.getsize(file_path)

                    doc = ClientUpload(
                        client_id=client.id,
                        category='id_verification',
                        document_type=field_name,
                        file_name=prefixed_filename,
                        file_path=file_path,
                        file_size=file_size,
                        file_type=file.content_type or 'application/octet-stream',
                        notes=f"{doc_label} - {notes}" if notes else doc_label,
                        uploaded_at=datetime.now()
                    )
                    db.add(doc)
                    files_uploaded += 1

            if files_uploaded > 0:
                db.commit()

                # Fire document_uploaded trigger for ID/proof uploads
                try:
                    from services.workflow_triggers_service import WorkflowTriggersService
                    WorkflowTriggersService.evaluate_triggers(
                        "document_uploaded",
                        {
                            "client_id": client.id,
                            "client_name": client.name,
                            "document_type": "id_proof",
                            "document_name": f"{files_uploaded} ID document(s)",
                            "uploaded_by": "client",
                        },
                    )
                except Exception as trigger_error:
                    print(f"⚠️  Workflow trigger error (non-fatal): {trigger_error}")

                flash(f'{files_uploaded} ID document(s) uploaded successfully!', 'success')
            else:
                flash('No ID files selected', 'error')

        else:
            # Standard single file upload
            file = request.files.get('document')
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_dir, filename)
                file.save(file_path)
                file_size = os.path.getsize(file_path)

                doc = ClientUpload(
                    client_id=client.id,
                    category='portal_upload',
                    document_type=doc_type,
                    file_name=filename,
                    file_path=file_path,
                    file_size=file_size,
                    file_type=file.content_type or 'application/octet-stream',
                    notes=notes,
                    bureau=bureau_str,
                    dispute_round=dispute_round,
                    uploaded_at=datetime.now()
                )
                db.add(doc)
                db.commit()

                # Fire response_received trigger for CRA responses
                if doc_type == 'cra_response' and bureau_str:
                    try:
                        from services.workflow_triggers_service import WorkflowTriggersService
                        for bureau in bureaus:
                            WorkflowTriggersService.evaluate_triggers(
                                "response_received",
                                {
                                    "client_id": client.id,
                                    "client_name": client.name,
                                    "bureau": bureau,
                                    "response_type": "mail",
                                    "round_number": dispute_round,
                                },
                            )
                            # Log timeline event for each bureau response
                            try:
                                from services.timeline_service import log_response_received
                                log_response_received(db, client.id, bureau, doc.id)
                            except Exception as timeline_error:
                                print(f"⚠️  Timeline event error (non-fatal): {timeline_error}")
                    except Exception as trigger_error:
                        print(f"⚠️  Workflow trigger error (non-fatal): {trigger_error}")

                # Fire document_uploaded trigger
                try:
                    from services.workflow_triggers_service import WorkflowTriggersService
                    WorkflowTriggersService.evaluate_triggers(
                        "document_uploaded",
                        {
                            "client_id": client.id,
                            "client_name": client.name,
                            "document_type": doc_type,
                            "document_name": filename,
                            "uploaded_by": "client",
                        },
                    )
                except Exception as trigger_error:
                    print(f"⚠️  Workflow trigger error (non-fatal): {trigger_error}")

                # Log timeline event
                try:
                    from services.timeline_service import log_document_uploaded
                    log_document_uploaded(db, client.id, doc_type, doc.id)
                except Exception as timeline_error:
                    print(f"⚠️  Timeline event error (non-fatal): {timeline_error}")

                flash('Document uploaded successfully!', 'success')
            else:
                flash('No file selected', 'error')

    except Exception as e:
        flash(f'Error uploading document: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('portal.documents'))

@portal.route('/documents/download/<int:doc_id>')
@portal_login_required
def download_document(doc_id):
    """Download a document"""
    from database import get_db, Client, ClientUpload

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    db = get_db()
    try:
        doc = db.query(ClientUpload).get(doc_id)
        client = db.query(Client).filter_by(id=get_client_id()).first()

        if not client or not doc or doc.client_id != client.id:
            flash('Unauthorized', 'error')
            return redirect(url_for('portal.documents'))

        if doc.file_path and os.path.exists(doc.file_path):
            return send_file(doc.file_path, as_attachment=True, download_name=doc.file_name or 'document')
        else:
            flash('File not found', 'error')
            return redirect(url_for('portal.documents'))
    finally:
        db.close()

@portal.route('/documents/preview/<int:doc_id>')
@portal_login_required
def preview_document(doc_id):
    """Preview a document inline (for document viewer)"""
    from database import get_db, Client, ClientUpload
    import mimetypes

    current_user = get_current_user()
    if not current_user:
        return jsonify({'error': 'Unauthorized'}), 401

    db = get_db()
    try:
        doc = db.query(ClientUpload).get(doc_id)
        client = db.query(Client).filter_by(id=get_client_id()).first()

        if not client or not doc or doc.client_id != client.id:
            return jsonify({'error': 'Unauthorized'}), 403

        if doc.file_path and os.path.exists(doc.file_path):
            # Determine mimetype
            mimetype, _ = mimetypes.guess_type(doc.file_path)
            if not mimetype:
                mimetype = 'application/octet-stream'

            # Serve file inline (not as attachment)
            return send_file(
                doc.file_path,
                mimetype=mimetype,
                as_attachment=False,
                download_name=doc.file_name or 'document'
            )
        else:
            return jsonify({'error': 'File not found'}), 404
    finally:
        db.close()

@portal.route('/learn')
@portal_login_required
@require_full_access
def learn():
    """Learn/Education page - requires ACTIVE stage"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    return render_template('portal/learn.html', current_user=current_user)

@portal.route('/profile')
@portal_login_required
@require_onboarding_access
def profile():
    """Profile page"""
    from database import get_db, Client

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=get_client_id()).first()
        return render_template('portal/profile.html',
            current_user=current_user,
            client=client
        )
    finally:
        db.close()

@portal.route('/profile/message', methods=['POST'])
@portal_login_required
def send_message():
    """Handle contact form submission"""
    subject = request.form.get('subject')
    message = request.form.get('message')

    # Here you would typically send an email or create a support ticket
    # For now, we'll just show a success message
    flash('Message sent successfully! We will respond within 24-48 hours.', 'success')
    return redirect(url_for('portal.profile'))

@portal.route('/profile/referral', methods=['POST'])
@portal_login_required
def submit_referral():
    """Handle referral form submission"""
    from database import get_db, Client, ClientReferral

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    referral_name = request.form.get('referral_name')
    referral_phone = request.form.get('referral_phone')
    referral_email = request.form.get('referral_email')

    if not referral_name or not (referral_phone or referral_email):
        flash('Please provide at least a name and phone or email', 'error')
        return redirect(url_for('portal.profile'))

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=get_client_id()).first()

        if client:
            try:
                referral = ClientReferral(
                    client_id=client.id,
                    referred_name=referral_name,
                    referred_phone=referral_phone,
                    referred_email=referral_email,
                    created_at=datetime.now()
                )
                db.add(referral)
                db.commit()
            except Exception as e:
                # Table might not exist, just log success anyway
                pass

        flash('Referral submitted! Thank you for spreading the word!', 'success')
    finally:
        db.close()

    return redirect(url_for('portal.profile'))


@portal.route('/subscription')
@portal_login_required
@require_full_access
def subscription():
    """Subscription management page - requires ACTIVE stage"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    return render_template('portal/subscription.html',
        current_user=current_user,
        active_page='subscription'
    )


@portal.route('/status')
@portal_login_required
@require_full_access
def status():
    """Detailed bureau status page - requires ACTIVE stage"""
    from database import get_db, Client, DisputeItem, SecondaryBureauFreeze, ClientUpload

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    # Initialize variables outside try block to ensure they're always defined
    accounts = []
    secondary_bureaus = []
    bureau_uploads = {}  # Map bureau_name -> has_upload
    client = None

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=get_client_id()).first()

        if client:
            try:
                accounts = db.query(DisputeItem).filter_by(client_id=client.id).all()
            except:
                pass

            try:
                secondary_bureaus = db.query(SecondaryBureauFreeze).filter_by(client_id=client.id).all()

                # Auto-create secondary bureau records if they don't exist
                if not secondary_bureaus:
                    default_bureaus = [
                        "Innovis",
                        "ChexSystems",
                        "Clarity Services Inc",
                        "LexisNexis",
                        "CoreLogic Teletrack",
                        "Factor Trust Inc",
                        "MicroBilt / PRBC",
                        "LexisNexis Risk Solutions",
                        "DataX Ltd",
                    ]
                    for bureau_name in default_bureaus:
                        freeze = SecondaryBureauFreeze(
                            client_id=client.id,
                            bureau_name=bureau_name,
                            status="PENDING",
                            freeze_requested_at=datetime.now()
                        )
                        db.add(freeze)
                    db.commit()
                    # Re-query after creation
                    secondary_bureaus = db.query(SecondaryBureauFreeze).filter_by(client_id=client.id).all()

                # Check which bureaus have uploaded confirmations
                uploads = db.query(ClientUpload).filter_by(
                    client_id=client.id,
                    category='freeze_confirmation'
                ).all()
                for u in uploads:
                    if u.sender_name:
                        bureau_uploads[u.sender_name] = True
            except:
                pass

        # Calculate expected dates for pending bureaus
        today = datetime.now()
        response_days = 30  # Expected response time in days

        # Find earliest pending request date and calculate expected date
        earliest_pending = None
        overdue_bureaus = []
        for b in secondary_bureaus:
            if b.status and b.status.upper() == 'PENDING' and b.freeze_requested_at:
                expected_date = b.freeze_requested_at + timedelta(days=response_days)
                if not earliest_pending or b.freeze_requested_at < earliest_pending:
                    earliest_pending = b.freeze_requested_at
                if today > expected_date:
                    overdue_bureaus.append(b.bureau_name)

        expected_by_date = (earliest_pending + timedelta(days=response_days)).strftime('%B %d, %Y') if earliest_pending else None

        return render_template('portal/status.html',
            current_user=current_user,
            client=client,
            accounts=accounts,
            secondary_bureaus=secondary_bureaus,
            bureau_uploads=bureau_uploads,
            today=today,
            response_days=response_days,
            expected_by_date=expected_by_date,
            overdue_bureaus=overdue_bureaus
        )
    finally:
        db.close()

@portal.route('/status/update', methods=['POST'])
@portal_login_required
def update_secondary_status():
    """Update secondary bureau freeze status"""
    from database import get_db, Client, SecondaryBureauFreeze

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=get_client_id()).first()

        if client:
            try:
                secondary_bureaus = db.query(SecondaryBureauFreeze).filter_by(client_id=client.id).all()

                for bureau in secondary_bureaus:
                    new_status = request.form.get(f'status_{bureau.id}')
                    new_comment = request.form.get(f'comment_{bureau.id}')
                    if new_status:
                        bureau.status = new_status
                    if new_comment is not None:
                        bureau.comments = new_comment

                db.commit()
                flash('Status updated successfully!', 'success')
            except Exception as e:
                flash(f'Error updating status: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('portal.status'))

@portal.route('/status/upload/<int:bureau_id>', methods=['POST'])
@portal_login_required
def upload_freeze_confirmation(bureau_id):
    """Upload freeze confirmation letter for a specific secondary bureau"""
    from database import get_db, Client, SecondaryBureauFreeze, ClientUpload
    from werkzeug.utils import secure_filename

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    file = request.files.get('confirmation_file')

    if not file or not file.filename:
        flash('No file selected', 'error')
        return redirect(url_for('portal.status'))

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=get_client_id()).first()
        bureau = db.query(SecondaryBureauFreeze).filter_by(id=bureau_id, client_id=client.id).first()

        if not client or not bureau:
            flash('Bureau not found', 'error')
            return redirect(url_for('portal.status'))

        # Secure the filename
        filename = secure_filename(file.filename)

        # Create upload directory
        upload_dir = os.path.join('static', 'client_uploads', str(client.id), 'freeze_confirmations')
        os.makedirs(upload_dir, exist_ok=True)

        # Save file with bureau name in filename
        safe_bureau_name = secure_filename(bureau.bureau_name)
        final_filename = f"{safe_bureau_name}_{filename}"
        file_path = os.path.join(upload_dir, final_filename)
        file.save(file_path)

        # Get file size
        file_size = os.path.getsize(file_path)

        # Create upload record linked to this bureau
        upload = ClientUpload(
            client_id=client.id,
            category='freeze_confirmation',
            document_type='freeze_confirmation',
            file_name=final_filename,
            file_path=file_path,
            file_size=file_size,
            file_type=file.content_type or 'application/octet-stream',
            sender_name=bureau.bureau_name,  # Use sender_name to link to bureau
            notes=f'Freeze confirmation for {bureau.bureau_name}',
            uploaded_at=datetime.now()
        )
        db.add(upload)
        db.commit()

        flash(f'Confirmation uploaded for {bureau.bureau_name}!', 'success')
    except Exception as e:
        flash(f'Error uploading: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('portal.status'))

@portal.route('/status/download/<int:bureau_id>')
@portal_login_required
def download_freeze_confirmation(bureau_id):
    """Download freeze confirmation for a specific bureau"""
    from database import get_db, Client, SecondaryBureauFreeze, ClientUpload

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    db = get_db()
    try:
        client = db.query(Client).filter_by(id=get_client_id()).first()
        bureau = db.query(SecondaryBureauFreeze).filter_by(id=bureau_id, client_id=client.id).first()

        if not client or not bureau:
            flash('Bureau not found', 'error')
            return redirect(url_for('portal.status'))

        # Find the uploaded confirmation
        upload = db.query(ClientUpload).filter_by(
            client_id=client.id,
            category='freeze_confirmation',
            sender_name=bureau.bureau_name
        ).order_by(ClientUpload.uploaded_at.desc()).first()

        if upload and upload.file_path and os.path.exists(upload.file_path):
            return send_file(upload.file_path, as_attachment=True, download_name=upload.file_name)
        else:
            flash('No confirmation file found', 'error')
            return redirect(url_for('portal.status'))
    finally:
        db.close()

@portal.route('/booking')
@portal_login_required
@require_full_access
def booking():
    """Q&A Call booking page - requires ACTIVE stage"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    return render_template('portal/booking.html', current_user=current_user)

@portal.route('/messages')
@portal_login_required
@require_full_access
def messages():
    """Live support messaging page - requires ACTIVE stage"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    return render_template('portal/messages.html', current_user=current_user)


@portal.route('/communication')
@portal_login_required
@require_full_access
def communication():
    """Combined communication page with messages and booking"""
    current_user = get_current_user()
    return render_template('portal/communication.html', current_user=current_user)


@portal.route('/onboarding')
@portal_login_required
@require_onboarding_access
def onboarding():
    """Onboarding wizard page - accessible during onboarding"""
    from database import get_db
    from services.onboarding_service import get_onboarding_service

    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    db = get_db()
    try:
        service = get_onboarding_service(db)
        progress = service.get_progress_summary(get_client_id())
        return render_template('portal/onboarding.html',
                               current_user=current_user,
                               progress=progress)
    finally:
        db.close()


@portal.route('/api/onboarding/progress', methods=['GET'])
@portal_login_required
def api_onboarding_progress():
    """Get onboarding progress for current client"""
    from flask import jsonify
    from database import get_db
    from services.onboarding_service import get_onboarding_service

    db = get_db()
    try:
        service = get_onboarding_service(db)
        progress = service.get_progress_summary(get_client_id())
        return jsonify({'success': True, 'progress': progress})
    finally:
        db.close()


@portal.route('/api/onboarding/sync', methods=['POST'])
@portal_login_required
def api_onboarding_sync():
    """Sync onboarding progress based on actual data"""
    from flask import jsonify
    from database import get_db
    from services.onboarding_service import get_onboarding_service

    db = get_db()
    try:
        service = get_onboarding_service(db)
        result = service.sync_progress(get_client_id())
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/onboarding/complete-step', methods=['POST'])
@portal_login_required
def api_onboarding_complete_step():
    """Mark an onboarding step as complete"""
    from flask import jsonify
    from database import get_db
    from services.onboarding_service import get_onboarding_service

    step_key = request.json.get('step') if request.is_json else request.form.get('step')
    if not step_key:
        return jsonify({'success': False, 'error': 'Step key required'}), 400

    db = get_db()
    try:
        service = get_onboarding_service(db)
        result = service.complete_step(get_client_id(), step_key)
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/onboarding/next-step', methods=['GET'])
@portal_login_required
def api_onboarding_next_step():
    """Get the next incomplete onboarding step"""
    from flask import jsonify
    from database import get_db
    from services.onboarding_service import get_onboarding_service

    db = get_db()
    try:
        service = get_onboarding_service(db)
        next_step = service.get_next_step(get_client_id())
        return jsonify({'success': True, 'next_step': next_step})
    finally:
        db.close()


# ============================================================================
# Timeline Routes
# ============================================================================

@portal.route('/timeline')
@portal_login_required
@require_full_access
def timeline():
    """Timeline page showing client journey - requires ACTIVE stage"""
    return render_template(
        'portal/timeline.html',
        active_tab='timeline',
        current_user=get_current_user()
    )


@portal.route('/api/timeline', methods=['GET'])
@portal_login_required
@require_full_access
def api_get_timeline():
    """Get timeline events for the current client - requires ACTIVE stage"""
    from flask import jsonify, request
    from database import get_db
    from services.timeline_service import get_timeline_service

    db = get_db()
    try:
        service = get_timeline_service(db)

        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        category = request.args.get('category')
        milestones_only = request.args.get('milestones_only', 'false').lower() == 'true'

        result = service.get_timeline(
            client_id=get_client_id(),
            limit=limit,
            offset=offset,
            category=category,
            milestones_only=milestones_only
        )
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/timeline/recent', methods=['GET'])
@portal_login_required
@require_full_access
def api_get_recent_timeline():
    """Get most recent timeline events - requires ACTIVE stage"""
    from flask import jsonify, request
    from database import get_db
    from services.timeline_service import get_timeline_service

    db = get_db()
    try:
        service = get_timeline_service(db)
        limit = request.args.get('limit', 5, type=int)
        events = service.get_recent_events(get_client_id(), limit=limit)
        return jsonify({'success': True, 'events': events})
    finally:
        db.close()


@portal.route('/api/timeline/milestones', methods=['GET'])
@portal_login_required
@require_full_access
def api_get_milestones():
    """Get milestone events for progress display - requires ACTIVE stage"""
    from flask import jsonify
    from database import get_db
    from services.timeline_service import get_timeline_service

    db = get_db()
    try:
        service = get_timeline_service(db)
        milestones = service.get_milestones(get_client_id())
        return jsonify({'success': True, 'milestones': milestones})
    finally:
        db.close()


@portal.route('/api/timeline/progress', methods=['GET'])
@portal_login_required
@require_full_access
def api_get_timeline_progress():
    """Get progress summary for the client journey - requires ACTIVE stage"""
    from flask import jsonify
    from database import get_db
    from services.timeline_service import get_timeline_service

    db = get_db()
    try:
        service = get_timeline_service(db)
        progress = service.get_progress_summary(get_client_id())
        return jsonify(progress)
    finally:
        db.close()


@portal.route('/api/timeline/backfill', methods=['POST'])
@portal_login_required
@require_full_access
def api_backfill_timeline():
    """Backfill timeline events from existing client data - requires ACTIVE stage"""
    from flask import jsonify
    from database import get_db
    from services.timeline_service import get_timeline_service

    db = get_db()
    try:
        service = get_timeline_service(db)
        result = service.backfill_events(get_client_id())
        return jsonify(result)
    finally:
        db.close()


# ============================================================================
# CROA Signing Routes
# ============================================================================

@portal.route('/agreements')
@portal_login_required
@require_onboarding_access
def croa_agreements():
    """CROA document signing page - accessible during onboarding"""
    return render_template(
        'portal/agreements.html',
        active_tab='onboarding',
        current_user=get_current_user()
    )


@portal.route('/api/croa/progress', methods=['GET'])
@portal_login_required
@require_onboarding_access
def api_croa_progress():
    """Get CROA signing progress - accessible during onboarding"""
    from flask import jsonify
    from database import get_db
    from services.croa_signing_service import get_croa_signing_service

    db = get_db()
    try:
        service = get_croa_signing_service(db)
        result = service.get_progress_summary(get_client_id())
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/croa/document/<document_code>', methods=['GET'])
@portal_login_required
@require_onboarding_access
def api_croa_get_document(document_code):
    """Get a specific CROA document - accessible during onboarding"""
    from flask import jsonify
    from database import get_db
    from services.croa_signing_service import get_croa_signing_service

    db = get_db()
    try:
        service = get_croa_signing_service(db)
        result = service.get_document(document_code)
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/croa/current-document', methods=['GET'])
@portal_login_required
@require_onboarding_access
def api_croa_current_document():
    """Get the current document to sign - accessible during onboarding"""
    from flask import jsonify
    from database import get_db
    from services.croa_signing_service import get_croa_signing_service

    db = get_db()
    try:
        service = get_croa_signing_service(db)
        result = service.get_current_document(get_client_id())
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/croa/sign', methods=['POST'])
@portal_login_required
@require_onboarding_access
def api_croa_sign_document():
    """Sign a CROA document - accessible during onboarding"""
    from flask import jsonify, request
    from database import get_db
    from services.croa_signing_service import get_croa_signing_service

    data = request.get_json() or {}
    document_code = data.get('document_code')
    signature_data = data.get('signature_data')
    signature_type = data.get('signature_type', 'drawn')

    if not document_code:
        return jsonify({'success': False, 'error': 'Document code required'}), 400

    if not signature_data:
        return jsonify({'success': False, 'error': 'Signature required'}), 400

    db = get_db()
    try:
        service = get_croa_signing_service(db)
        result = service.sign_document(
            client_id=get_client_id(),
            document_code=document_code,
            signature_data=signature_data,
            signature_type=signature_type,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None
        )
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/croa/skip-optional', methods=['POST'])
@portal_login_required
@require_onboarding_access
def api_croa_skip_optional():
    """Skip an optional document - accessible during onboarding"""
    from flask import jsonify, request
    from database import get_db
    from services.croa_signing_service import get_croa_signing_service

    data = request.get_json() or {}
    document_code = data.get('document_code')

    if not document_code:
        return jsonify({'success': False, 'error': 'Document code required'}), 400

    db = get_db()
    try:
        service = get_croa_signing_service(db)
        result = service.skip_optional_document(get_client_id(), document_code)
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/croa/cancellation-status', methods=['GET'])
@portal_login_required
@require_onboarding_access
def api_croa_cancellation_status():
    """Get cancellation period status - accessible during onboarding"""
    from flask import jsonify
    from database import get_db
    from services.croa_signing_service import get_croa_signing_service

    db = get_db()
    try:
        service = get_croa_signing_service(db)
        result = service.get_cancellation_status(get_client_id())
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/croa/cancel', methods=['POST'])
@portal_login_required
@require_onboarding_access
def api_croa_cancel_service():
    """Cancel service during cancellation period - accessible during onboarding"""
    from flask import jsonify, request
    from database import get_db
    from services.croa_signing_service import get_croa_signing_service

    data = request.get_json() or {}
    reason = data.get('reason')

    db = get_db()
    try:
        service = get_croa_signing_service(db)
        result = service.cancel_service(get_client_id(), reason)
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/croa/can-begin-services', methods=['GET'])
@portal_login_required
@require_onboarding_access
def api_croa_can_begin_services():
    """Check if services can begin - accessible during onboarding"""
    from flask import jsonify
    from database import get_db
    from services.croa_signing_service import get_croa_signing_service

    db = get_db()
    try:
        service = get_croa_signing_service(db)
        result = service.can_begin_services(get_client_id())
        return jsonify(result)
    finally:
        db.close()


# ==============================================================================
# INVOICE PORTAL ENDPOINTS
# ==============================================================================


@portal.route('/invoices')
@portal_login_required
@require_full_access
def portal_invoices():
    """Client invoice history page"""
    current_user = get_current_user()
    return render_template('portal/invoices.html', current_user=current_user)


@portal.route('/api/invoices', methods=['GET'])
@portal_login_required
@require_full_access
def api_portal_invoices():
    """Get client's invoices"""
    from flask import jsonify
    from services.invoice_service import get_client_invoices

    result = get_client_invoices(get_client_id())
    return jsonify(result)


@portal.route('/api/invoices/<int:invoice_id>', methods=['GET'])
@portal_login_required
@require_full_access
def api_portal_invoice_detail(invoice_id):
    """Get invoice details"""
    from flask import jsonify
    from services.invoice_service import get_invoice
    from database import get_db, Invoice

    db = get_db()
    try:
        # Verify invoice belongs to this client
        invoice = db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.client_id == get_client_id()
        ).first()

        if not invoice:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404

        # Mark as viewed if sent
        from services.invoice_service import mark_viewed
        if invoice.status == 'sent':
            mark_viewed(invoice_id)

        result = get_invoice(invoice_id, include_payments=True)
        return jsonify(result)
    finally:
        db.close()


@portal.route('/api/invoices/<int:invoice_id>/pdf', methods=['GET'])
@portal_login_required
@require_full_access
def api_portal_invoice_pdf(invoice_id):
    """Download invoice PDF"""
    from flask import send_file, jsonify
    from services.invoice_service import get_invoice, generate_invoice_pdf, INVOICE_PDF_DIR
    from database import get_db, Invoice
    import os

    db = get_db()
    try:
        # Verify invoice belongs to this client
        invoice = db.query(Invoice).filter(
            Invoice.id == invoice_id,
            Invoice.client_id == get_client_id()
        ).first()

        if not invoice:
            return jsonify({'success': False, 'error': 'Invoice not found'}), 404

        # Generate PDF if not exists
        if not invoice.pdf_filename:
            result = generate_invoice_pdf(invoice_id)
            if not result.get('success'):
                return jsonify(result), 500

        result = get_invoice(invoice_id)
        if not result.get('success'):
            return jsonify(result), 404

        inv = result['invoice']
        pdf_path = os.path.join(INVOICE_PDF_DIR, inv['pdf_filename'])

        if not os.path.exists(pdf_path):
            return jsonify({'success': False, 'error': 'PDF not found'}), 404

        return send_file(pdf_path, as_attachment=True, download_name=inv['pdf_filename'])
    finally:
        db.close()


# ==============================================================================
# PAYMENT PLANS PORTAL ENDPOINTS
# ==============================================================================


@portal.route('/payment-plans')
@portal_login_required
@require_full_access
def portal_payment_plans():
    """Client payment plans page"""
    current_user = get_current_user()
    return render_template('portal/payment_plans.html', current_user=current_user)


@portal.route('/api/payment-plans', methods=['GET'])
@portal_login_required
@require_full_access
def api_portal_payment_plans():
    """Get client's payment plans"""
    from flask import jsonify
    from services.payment_plan_service import PaymentPlanService

    client_id = get_client_id()
    service = PaymentPlanService()
    plans = service.get_client_plans(client_id)

    # Calculate summary stats
    active_count = len([p for p in plans if p.get('status') == 'active'])
    total_paid = sum(p.get('amount_paid', 0) for p in plans)
    total_remaining = sum(p.get('amount_remaining', 0) for p in plans)

    return jsonify({
        'success': True,
        'plans': plans,
        'active_count': active_count,
        'total_paid': total_paid,
        'total_remaining': total_remaining
    })


@portal.route('/api/payment-plans/<int:plan_id>', methods=['GET'])
@portal_login_required
@require_full_access
def api_portal_payment_plan_detail(plan_id):
    """Get payment plan details"""
    from flask import jsonify
    from services.payment_plan_service import PaymentPlanService
    from database import get_db, PaymentPlan

    client_id = get_client_id()
    db = get_db()
    try:
        # Verify plan belongs to this client
        plan = db.query(PaymentPlan).filter(
            PaymentPlan.id == plan_id,
            PaymentPlan.client_id == client_id
        ).first()

        if not plan:
            return jsonify({'success': False, 'error': 'Payment plan not found'}), 404

        service = PaymentPlanService()
        plan_data = service.get_plan(plan_id)

        if not plan_data:
            return jsonify({'success': False, 'error': 'Payment plan not found'}), 404

        return jsonify({
            'success': True,
            'plan': plan_data
        })
    finally:
        db.close()
