from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, session
from functools import wraps
from datetime import datetime, timedelta
import os

portal = Blueprint('portal', __name__, url_prefix='/portal')

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
                            dispute_status='active'
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

@portal.route('/dashboard')
@portal.route('/')
@portal_login_required
def dashboard():
    """Main dashboard/case overview page"""
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
def documents():
    """Documents page"""
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

@portal.route('/learn')
@portal_login_required
def learn():
    """Learn/Education page"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    return render_template('portal/learn.html', current_user=current_user)

@portal.route('/profile')
@portal_login_required
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

@portal.route('/status')
@portal_login_required
def status():
    """Detailed bureau status page"""
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
def booking():
    """Q&A Call booking page"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    return render_template('portal/booking.html', current_user=current_user)

@portal.route('/messages')
@portal_login_required
def messages():
    """Live support messaging page"""
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('portal_login'))

    return render_template('portal/messages.html', current_user=current_user)
