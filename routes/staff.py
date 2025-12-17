"""
Staff Portal Routes - Redesigned 5-Tab Interface
Consolidates the old multi-section sidebar into a clean Apple-style navigation.
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
from datetime import datetime, timedelta
from database import get_db, Client, Case, Analysis, DisputeLetter, Document, ClientDocument, Staff, LetterQueue, ClientUpload, CRAResponse, AnalysisQueue, Violation, Standing, Damages, CaseScore, ClientNote, CaseDeadline, Settlement, SignupDraft, DisputeItem, LetterBatch, TradelineStatus, AutomationMetrics

staff_portal = Blueprint('staff_portal', __name__, url_prefix='/staff')


def require_staff(roles=None):
    """Decorator to require staff authentication and optional role check"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'staff_id' not in session:
                if request.is_json:
                    return jsonify({'success': False, 'error': 'Authentication required'}), 401
                return redirect('/staff/login')

            if roles and session.get('staff_role') not in roles:
                if 'admin' not in roles and session.get('staff_role') != 'admin':
                    if request.is_json:
                        return jsonify({'error': 'Insufficient permissions'}), 403
                    flash('You do not have permission to access this page.', 'error')
                    return redirect(url_for('staff_portal.dashboard'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================
# DASHBOARD TAB
# ============================================

@staff_portal.route('/')
@staff_portal.route('/dashboard')
@require_staff()
def dashboard():
    """Main dashboard with stats, pipeline, and recent activity"""
    db = get_db()
    try:
        # Get stats
        total_clients = db.query(Client).count()
        active_cases = db.query(Client).filter(Client.status.in_(['active', 'in_progress', 'pending_review'])).count()
        pending_review = db.query(Client).filter(Client.status == 'pending_review').count()

        # Letters this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        letters_sent = db.query(DisputeLetter).filter(DisputeLetter.created_at >= week_ago).count()

        # Success rate (simplified)
        completed = db.query(Client).filter(Client.status == 'completed').count()
        success_rate = round((completed / max(total_clients, 1)) * 100) if total_clients > 0 else 0

        # Letter queue count
        letter_queue_count = db.query(LetterQueue).filter(LetterQueue.status == 'pending').count()

        # VA approval count (simplified - using analysis queue)
        va_approval_count = db.query(AnalysisQueue).filter(AnalysisQueue.status == 'pending_approval').count()

        # New document uploads
        new_docs_count = db.query(ClientUpload).filter(ClientUpload.created_at >= week_ago).count()

        # New signups this week
        new_signups_count = db.query(Client).filter(Client.created_at >= week_ago).count()

        stats = {
            'active_cases': active_cases,
            'pending_review': pending_review,
            'letters_sent': letters_sent,
            'success_rate': success_rate,
            'cases_change': 12,  # Placeholder
            'letters_change': 8,  # Placeholder
            'success_change': 3,  # Placeholder
            'letter_queue_count': letter_queue_count,
            'va_approval_count': va_approval_count,
            'new_docs_count': new_docs_count,
            'new_signups_count': new_signups_count
        }

        # Pipeline stages
        pipeline = [
            {'status': 'new', 'label': 'New', 'count': db.query(Client).filter(Client.status == 'new').count()},
            {'status': 'analyzing', 'label': 'Analyzing', 'count': db.query(Client).filter(Client.status == 'analyzing').count()},
            {'status': 'in_progress', 'label': 'In Progress', 'count': db.query(Client).filter(Client.status == 'in_progress').count()},
            {'status': 'pending_review', 'label': 'Pending Review', 'count': pending_review},
            {'status': 'ready', 'label': 'Ready to Send', 'count': db.query(Client).filter(Client.status == 'ready').count()},
            {'status': 'completed', 'label': 'Completed', 'count': completed}
        ]

        # Recent cases
        recent_clients = db.query(Client).order_by(Client.updated_at.desc()).limit(5).all()
        recent_cases = []
        for c in recent_clients:
            status_class = 'info'
            if c.status in ['completed', 'success']:
                status_class = 'success'
            elif c.status in ['pending_review', 'ready']:
                status_class = 'warning'
            elif c.status in ['error', 'failed']:
                status_class = 'danger'

            recent_cases.append({
                'id': c.id,
                'client_name': c.name or f"{c.first_name} {c.last_name}",
                'email': c.email or '',
                'status': (c.status or 'new').replace('_', ' ').title(),
                'status_class': status_class,
                'updated': c.updated_at.strftime('%b %d, %H:%M') if c.updated_at else 'Never'
            })

        # Recent activity (simplified)
        activities = [
            {'icon': 'New', 'title': 'New signup: John Smith', 'time': '2 hours ago', 'bg_color': 'var(--apple-green)'},
            {'icon': 'Letter', 'title': 'Letter sent to Equifax', 'time': '3 hours ago', 'bg_color': 'var(--apple-teal)'},
            {'icon': 'Doc', 'title': 'Credit report uploaded', 'time': '5 hours ago', 'bg_color': 'var(--apple-navy)'},
        ]

        return render_template('staff/dashboard.html',
            active_tab='dashboard',
            stats=stats,
            pipeline=pipeline,
            recent_cases=recent_cases,
            activities=activities
        )
    finally:
        db.close()


# ============================================
# CLIENTS TAB
# ============================================

@staff_portal.route('/clients')
@require_staff()
def clients():
    """Client list with filtering and search"""
    db = get_db()
    try:
        filter_type = request.args.get('filter', '')
        search_query = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 20

        query = db.query(Client)

        # Apply search filter
        if search_query:
            search_term = f"%{search_query}%"
            from sqlalchemy import or_
            query = query.filter(or_(
                Client.name.ilike(search_term),
                Client.first_name.ilike(search_term),
                Client.last_name.ilike(search_term),
                Client.email.ilike(search_term),
                Client.phone.ilike(search_term)
            ))

        # Apply status filter
        if filter_type == 'active':
            query = query.filter(Client.status.in_(['active', 'in_progress', 'analyzing']))
        elif filter_type == 'pending':
            query = query.filter(Client.status == 'pending_review')
        elif filter_type == 'new':
            week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(Client.created_at >= week_ago)
        elif filter_type == 'completed':
            query = query.filter(Client.status == 'completed')

        total = query.count()
        total_pages = (total + per_page - 1) // per_page

        clients_list = query.order_by(Client.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

        # Format clients for template
        formatted_clients = []
        for c in clients_list:
            name = c.name or f"{c.first_name or ''} {c.last_name or ''}".strip() or 'Unknown'
            initials = ''.join([n[0].upper() for n in name.split()[:2]]) if name else 'U'

            status_class = 'info'
            if c.status in ['completed', 'success']:
                status_class = 'success'
            elif c.status in ['pending_review', 'ready']:
                status_class = 'warning'
            elif c.status in ['error', 'failed']:
                status_class = 'danger'

            # Get case score if available
            case_score = None
            if hasattr(c, 'case_scores') and c.case_scores:
                latest_score = max(c.case_scores, key=lambda x: x.created_at if x.created_at else datetime.min)
                case_score = latest_score.total_score if latest_score else None

            formatted_clients.append({
                'id': c.id,
                'name': name,
                'initials': initials,
                'email': c.email or '',
                'status': (c.status or 'new').replace('_', ' ').title(),
                'status_class': status_class,
                'case_score': case_score,
                'round': getattr(c, 'current_round', 1) or 1,
                'last_activity': c.updated_at.strftime('%b %d, %Y') if c.updated_at else 'Never'
            })

        # Counts for filters
        counts = {
            'all': db.query(Client).count(),
            'active': db.query(Client).filter(Client.status.in_(['active', 'in_progress', 'analyzing'])).count(),
            'pending': db.query(Client).filter(Client.status == 'pending_review').count(),
            'new': db.query(Client).filter(Client.created_at >= datetime.utcnow() - timedelta(days=7)).count(),
            'completed': db.query(Client).filter(Client.status == 'completed').count()
        }

        return render_template('staff/clients.html',
            active_tab='clients',
            clients=formatted_clients,
            filter=filter_type,
            search=search_query,
            page=page,
            total_pages=total_pages,
            counts=counts
        )
    finally:
        db.close()


@staff_portal.route('/clients/add', methods=['POST'])
@require_staff()
def add_client():
    """Add a new client"""
    db = get_db()
    try:
        client = Client(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=request.form.get('email'),
            phone=request.form.get('phone'),
            name=f"{request.form.get('first_name')} {request.form.get('last_name')}",
            status='new',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(client)
        db.commit()
        flash('Client added successfully!', 'success')
        return redirect(url_for('staff_portal.clients'))
    except Exception as e:
        db.rollback()
        flash(f'Error adding client: {str(e)}', 'error')
        return redirect(url_for('staff_portal.clients'))
    finally:
        db.close()


@staff_portal.route('/clients/export')
@require_staff()
def export_clients():
    """Export clients to CSV"""
    import csv
    from io import StringIO
    from flask import Response

    db = get_db()
    try:
        filter_type = request.args.get('filter', '')
        query = db.query(Client)

        if filter_type == 'active':
            query = query.filter(Client.status.in_(['active', 'in_progress']))
        elif filter_type == 'pending':
            query = query.filter(Client.status == 'pending_review')
        elif filter_type == 'completed':
            query = query.filter(Client.status == 'completed')

        clients = query.all()

        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Status', 'Created', 'Updated'])

        for c in clients:
            writer.writerow([
                c.id,
                c.name or f"{c.first_name} {c.last_name}",
                c.email,
                c.phone,
                c.status,
                c.created_at.strftime('%Y-%m-%d') if c.created_at else '',
                c.updated_at.strftime('%Y-%m-%d') if c.updated_at else ''
            ])

        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=clients_{datetime.now().strftime("%Y%m%d")}.csv'}
        )
    finally:
        db.close()


@staff_portal.route('/clients/<int:client_id>')
@require_staff()
def client_detail(client_id):
    """Client detail page with case information"""
    db = get_db()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            flash('Client not found', 'error')
            return redirect(url_for('staff_portal.clients'))

        name = client.name or f"{client.first_name or ''} {client.last_name or ''}".strip() or 'Unknown'
        initials = ''.join([n[0].upper() for n in name.split()[:2]]) if name else 'U'

        # Get latest analysis
        analysis = db.query(Analysis).filter(Analysis.client_id == client_id).order_by(Analysis.created_at.desc()).first()

        # Get case score
        case_score = None
        if hasattr(client, 'case_scores') and client.case_scores:
            case_score = max(client.case_scores, key=lambda x: x.created_at if x.created_at else datetime.min)

        # Get standing
        standing = db.query(Standing).filter(Standing.client_id == client_id).first()

        # Get damages
        damages = db.query(Damages).filter(Damages.client_id == client_id).first()

        # Get violations
        violations = db.query(Violation).filter(Violation.client_id == client_id).all()

        # Get letters
        letters = db.query(DisputeLetter).filter(DisputeLetter.client_id == client_id).order_by(DisputeLetter.created_at.desc()).all()

        # Get documents
        documents = db.query(ClientUpload).filter(ClientUpload.client_id == client_id).order_by(ClientUpload.created_at.desc()).all()

        # Get notes
        notes = []
        try:
            notes = db.query(ClientNote).filter(ClientNote.client_id == client_id).order_by(ClientNote.created_at.desc()).all()
        except:
            pass

        # Format client data
        client_data = {
            'id': client.id,
            'name': name,
            'initials': initials,
            'first_name': client.first_name,
            'last_name': client.last_name,
            'email': client.email or '',
            'phone': client.phone or '',
            'address': getattr(client, 'address', '') or '',
            'city': getattr(client, 'city', '') or '',
            'state': getattr(client, 'state', '') or '',
            'zip': getattr(client, 'zip', '') or '',
            'status': (client.status or 'new').replace('_', ' ').title(),
            'status_raw': client.status or 'new',
            'created_at': client.created_at.strftime('%B %d, %Y') if client.created_at else 'Unknown',
            'updated_at': client.updated_at.strftime('%B %d, %Y at %H:%M') if client.updated_at else 'Never',
            'round': getattr(client, 'current_round', 1) or 1
        }

        # Format analysis data
        analysis_data = None
        if analysis:
            analysis_data = {
                'id': analysis.id,
                'stage': analysis.stage,
                'dispute_round': getattr(analysis, 'dispute_round', 1),
                'created_at': analysis.created_at.strftime('%B %d, %Y') if analysis.created_at else '',
                'approved_at': analysis.approved_at.strftime('%B %d, %Y') if analysis.approved_at else None
            }

        # Format case score
        score_data = None
        if case_score:
            score_data = {
                'total_score': case_score.total_score,
                'standing_score': getattr(case_score, 'standing_score', 0),
                'violation_quality_score': getattr(case_score, 'violation_quality_score', 0),
                'willfulness_score': getattr(case_score, 'willfulness_score', 0),
                'documentation_score': getattr(case_score, 'documentation_score', 0),
                'case_strength': getattr(case_score, 'case_strength', 'Unknown')
            }

        # Format standing
        standing_data = None
        if standing:
            standing_data = {
                'has_concrete_harm': standing.has_concrete_harm,
                'concrete_harm_type': standing.concrete_harm_type,
                'has_dissemination': standing.has_dissemination,
                'dissemination_details': getattr(standing, 'dissemination_details', ''),
                'has_procedural_violation': getattr(standing, 'has_procedural_violation', False)
            }

        # Format damages
        damages_data = None
        if damages:
            damages_data = {
                'total_exposure': damages.total_exposure or 0,
                'actual_damages_total': damages.actual_damages_total or 0,
                'statutory_damages_total': damages.statutory_damages_total or 0,
                'punitive_damages_amount': damages.punitive_damages_amount or 0,
                'settlement_target': damages.settlement_target or 0
            }

        # Format violations
        violations_data = []
        for v in violations:
            violations_data.append({
                'id': v.id,
                'bureau': v.bureau or 'Unknown',
                'section': getattr(v, 'fcra_section', ''),
                'account_name': getattr(v, 'account_name', ''),
                'description': v.description or '',
                'severity': getattr(v, 'severity', 'medium')
            })

        # Format letters
        letters_data = []
        for l in letters:
            letters_data.append({
                'id': l.id,
                'letter_type': f'{l.bureau or "Dispute"} Letter',
                'bureau': l.bureau or '',
                'created_at': l.created_at.strftime('%b %d, %Y') if l.created_at else '',
                'sent_date': l.sent_at.strftime('%b %d, %Y') if l.sent_at else None,
                'status': 'Sent' if l.sent_at else 'Draft'
            })

        # Format documents
        documents_data = []
        for d in documents:
            documents_data.append({
                'id': d.id,
                'filename': d.filename or 'Unnamed',
                'document_type': getattr(d, 'document_type', 'other'),
                'created_at': d.created_at.strftime('%b %d, %Y') if d.created_at else ''
            })

        # Format notes
        notes_data = []
        for n in notes:
            notes_data.append({
                'id': n.id,
                'content': n.content or '',
                'created_at': n.created_at.strftime('%b %d, %Y at %H:%M') if n.created_at else '',
                'author': getattr(n, 'author', 'Staff')
            })

        return render_template('staff/client_detail.html',
            active_tab='clients',
            client=client_data,
            analysis=analysis_data,
            score=score_data,
            standing=standing_data,
            damages=damages_data,
            violations=violations_data,
            letters=letters_data,
            documents=documents_data,
            notes=notes_data
        )
    finally:
        db.close()


@staff_portal.route('/clients/<int:client_id>/note', methods=['POST'])
@require_staff()
def add_client_note(client_id):
    """Add a note to a client"""
    db = get_db()
    try:
        content = request.form.get('content', '').strip()
        if not content:
            flash('Note cannot be empty', 'error')
            return redirect(url_for('staff_portal.client_detail', client_id=client_id))

        note = ClientNote(
            client_id=client_id,
            content=content,
            created_at=datetime.utcnow()
        )
        db.add(note)
        db.commit()
        flash('Note added successfully', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error adding note: {str(e)}', 'error')
    finally:
        db.close()

    return redirect(url_for('staff_portal.client_detail', client_id=client_id))


# ============================================
# WORKFLOW TAB
# ============================================

@staff_portal.route('/workflow')
@require_staff()
def workflow():
    """Work queue with letters, approvals, and pending items"""
    db = get_db()
    try:
        filter_type = request.args.get('filter', '')

        items = []

        # Get pending letters
        if not filter_type or filter_type == 'letters':
            letters = db.query(LetterQueue).filter(LetterQueue.status == 'pending').limit(20).all()
            for l in letters:
                client = db.query(Client).filter(Client.id == l.client_id).first()
                items.append({
                    'id': l.id,
                    'type': 'Letter',
                    'type_class': 'info',
                    'client_id': l.client_id,
                    'client_name': client.name if client else 'Unknown',
                    'description': f'{l.letter_type or "Dispute"} letter ready for review',
                    'priority': 'normal',
                    'due_date': l.created_at.strftime('%b %d') if getattr(l, 'created_at', None) else 'No date',
                    'overdue': False
                })

        # Get VA approvals
        if not filter_type or filter_type == 'approvals':
            approvals = db.query(AnalysisQueue).filter(AnalysisQueue.status == 'pending_approval').limit(20).all()
            for a in approvals:
                client = db.query(Client).filter(Client.id == a.client_id).first()
                items.append({
                    'id': a.id,
                    'type': 'VA Approval',
                    'type_class': 'warning',
                    'client_id': a.client_id,
                    'client_name': client.name if client else 'Unknown',
                    'description': 'VA letter requires attorney approval',
                    'priority': 'high',
                    'due_date': a.created_at.strftime('%b %d') if a.created_at else 'No date',
                    'overdue': False
                })

        # Get pending analyses
        if not filter_type or filter_type == 'analyses':
            analyses = db.query(AnalysisQueue).filter(AnalysisQueue.status == 'pending').limit(20).all()
            for a in analyses:
                client = db.query(Client).filter(Client.id == a.client_id).first()
                items.append({
                    'id': a.id,
                    'type': 'Analysis',
                    'type_class': 'success',
                    'client_id': a.client_id,
                    'client_name': client.name if client else 'Unknown',
                    'description': 'Credit report needs analysis',
                    'priority': 'normal',
                    'due_date': a.created_at.strftime('%b %d') if a.created_at else 'No date',
                    'overdue': False
                })

        # Get CRA responses
        if not filter_type or filter_type == 'responses':
            responses = db.query(CRAResponse).filter(CRAResponse.response_type == 'investigating').limit(20).all()
            for r in responses:
                client = db.query(Client).filter(Client.id == r.client_id).first()
                items.append({
                    'id': r.id,
                    'type': 'CRA Response',
                    'type_class': 'danger',
                    'client_id': r.client_id,
                    'client_name': client.name if client else 'Unknown',
                    'description': f'Response from {r.bureau or "bureau"} needs review',
                    'priority': 'urgent',
                    'due_date': r.response_date.strftime('%b %d') if r.response_date else 'No date',
                    'overdue': True
                })

        # Counts
        counts = {
            'all': len(items) if not filter_type else db.query(LetterQueue).filter(LetterQueue.status == 'pending').count() +
                   db.query(AnalysisQueue).filter(AnalysisQueue.status.in_(['pending', 'pending_approval'])).count() +
                   db.query(CRAResponse).filter(CRAResponse.response_type == 'investigating').count(),
            'letters': db.query(LetterQueue).filter(LetterQueue.status == 'pending').count(),
            'approvals': db.query(AnalysisQueue).filter(AnalysisQueue.status == 'pending_approval').count(),
            'analyses': db.query(AnalysisQueue).filter(AnalysisQueue.status == 'pending').count(),
            'responses': db.query(CRAResponse).filter(CRAResponse.response_type == 'investigating').count()
        }

        # Stats
        today = datetime.utcnow().date()
        stats = {
            'due_today': sum(1 for i in items if i.get('overdue')),
            'due_week': len(items),
            'in_progress': db.query(AnalysisQueue).filter(AnalysisQueue.status == 'in_progress').count(),
            'completed_today': db.query(LetterQueue).filter(
                LetterQueue.status == 'completed',
                LetterQueue.updated_at >= datetime.combine(today, datetime.min.time())
            ).count()
        }

        # Recently completed
        completed_items = []
        completed_letters = db.query(LetterQueue).filter(LetterQueue.status == 'completed').order_by(LetterQueue.updated_at.desc()).limit(5).all()
        for l in completed_letters:
            client = db.query(Client).filter(Client.id == l.client_id).first()
            completed_items.append({
                'type': 'Letter',
                'type_class': 'info',
                'client_name': client.name if client else 'Unknown',
                'completed_at': l.updated_at.strftime('%b %d, %H:%M') if l.updated_at else '',
                'completed_by': session.get('staff_name', 'Staff')
            })

        return render_template('staff/workflow.html',
            active_tab='workflow',
            items=items,
            filter=filter_type,
            counts=counts,
            stats=stats,
            completed_items=completed_items
        )
    finally:
        db.close()


@staff_portal.route('/workflow/process', methods=['POST'])
@require_staff()
def process_items():
    """Process multiple workflow items"""
    data = request.get_json()
    items = data.get('items', [])

    if not items:
        return jsonify({'success': False, 'error': 'No items selected'})

    # In production, this would actually process the items
    return jsonify({'success': True, 'message': f'Processed {len(items)} items'})


# ============================================
# DOCUMENTS TAB
# ============================================

@staff_portal.route('/documents')
@require_staff()
def documents():
    """Document management with uploads and generated files"""
    db = get_db()
    try:
        filter_type = request.args.get('filter', '')
        page = int(request.args.get('page', 1))
        per_page = 24

        documents_list = []

        # Get client uploads
        if not filter_type or filter_type == 'uploads':
            uploads = db.query(ClientUpload).order_by(ClientUpload.created_at.desc()).limit(per_page).all()
            for u in uploads:
                client = db.query(Client).filter(Client.id == u.client_id).first()
                documents_list.append({
                    'id': u.id,
                    'filename': u.filename or 'Unnamed',
                    'client_name': client.name if client else 'Unknown',
                    'type': 'pdf' if u.filename and u.filename.endswith('.pdf') else 'image',
                    'size': f"{(u.file_size or 0) / 1024:.1f} KB" if hasattr(u, 'file_size') else 'Unknown',
                    'uploaded_at': u.created_at.strftime('%b %d, %Y') if u.created_at else '',
                    'status': 'New',
                    'status_class': 'info',
                    'download_url': f'/static/client_uploads/{u.filename}' if u.filename else '#',
                    'preview_url': f'/static/client_uploads/{u.filename}' if u.filename else '#'
                })

        # Get generated letters
        if not filter_type or filter_type == 'letters':
            letters = db.query(DisputeLetter).order_by(DisputeLetter.created_at.desc()).limit(per_page).all()
            for l in letters:
                client = db.query(Client).filter(Client.id == l.client_id).first()
                documents_list.append({
                    'id': l.id,
                    'filename': f"{l.bureau or 'Dispute'}_Letter_{client.name if client else 'Client'}.pdf",
                    'client_name': client.name if client else 'Unknown',
                    'type': 'pdf',
                    'size': 'Generated',
                    'uploaded_at': l.created_at.strftime('%b %d, %Y') if l.created_at else '',
                    'status': 'Sent' if l.sent_at else 'Draft',
                    'status_class': 'success' if l.sent_at else 'warning',
                    'download_url': f'/api/letter/{l.id}/download',
                    'preview_url': f'/api/letter/{l.id}/preview'
                })

        # Counts
        counts = {
            'all': db.query(ClientUpload).count() + db.query(DisputeLetter).count(),
            'uploads': db.query(ClientUpload).count(),
            'letters': db.query(DisputeLetter).count(),
            'reports': db.query(ClientUpload).filter(ClientUpload.document_type == 'credit_report').count() if hasattr(ClientUpload, 'document_type') else 0,
            'responses': db.query(CRAResponse).count()
        }

        # Get all clients for upload modal
        all_clients = db.query(Client).order_by(Client.name).all()
        all_clients_formatted = [{'id': c.id, 'name': c.name or f"{c.first_name} {c.last_name}"} for c in all_clients]

        total_pages = 1  # Simplified for now

        return render_template('staff/documents.html',
            active_tab='documents',
            documents=documents_list,
            filter=filter_type,
            page=page,
            total_pages=total_pages,
            counts=counts,
            all_clients=all_clients_formatted
        )
    finally:
        db.close()


@staff_portal.route('/documents/upload', methods=['POST'])
@require_staff()
def upload_document():
    """Upload a new document"""
    import os
    from werkzeug.utils import secure_filename

    db = get_db()
    try:
        client_id = request.form.get('client_id')
        doc_type = request.form.get('doc_type')
        file = request.files.get('file')

        if not file or not client_id:
            flash('Please select a client and file', 'error')
            return redirect(url_for('staff_portal.documents'))

        filename = secure_filename(file.filename)
        upload_path = os.path.join('static', 'client_uploads', filename)
        file.save(upload_path)

        upload = ClientUpload(
            client_id=int(client_id),
            filename=filename,
            document_type=doc_type,
            created_at=datetime.utcnow()
        )
        db.add(upload)
        db.commit()

        flash('Document uploaded successfully!', 'success')
        return redirect(url_for('staff_portal.documents'))
    except Exception as e:
        db.rollback()
        flash(f'Error uploading document: {str(e)}', 'error')
        return redirect(url_for('staff_portal.documents'))
    finally:
        db.close()


# ============================================
# ADMIN TAB
# ============================================

@staff_portal.route('/admin')
@require_staff(roles=['admin', 'attorney'])
def admin():
    """Admin panel with team, analytics, and settings"""
    db = get_db()
    try:
        section = request.args.get('section', '')

        # Overview stats
        overview = {
            'total_clients': db.query(Client).count(),
            'active_staff': db.query(Staff).filter(Staff.is_active == True).count(),
            'letters_month': db.query(DisputeLetter).filter(
                DisputeLetter.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count(),
            'revenue': 0  # Placeholder
        }

        # Team members
        team_members = []
        if section == 'team':
            staff = db.query(Staff).all()
            for s in staff:
                name = f"{s.first_name} {s.last_name}"
                initials = ''.join([n[0].upper() for n in name.split()[:2]]) if name else 'S'
                team_members.append({
                    'id': s.id,
                    'name': name,
                    'initials': initials,
                    'email': s.email,
                    'role': s.role or 'viewer',
                    'is_active': s.is_active,
                    'last_active': s.updated_at.strftime('%b %d, %Y') if s.updated_at else 'Never'
                })

        # Analytics
        analytics = {
            'cases_month': db.query(Client).filter(
                Client.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count(),
            'cases_change': 12,  # Placeholder
            'success_rate': 78,  # Placeholder
            'avg_resolution': 45,  # Placeholder
            'satisfaction': 92  # Placeholder
        }

        return render_template('staff/admin.html',
            active_tab='admin',
            section=section,
            overview=overview,
            team_members=team_members,
            analytics=analytics
        )
    finally:
        db.close()


# ============================================
# REDIRECTS FROM OLD ROUTES
# ============================================

@staff_portal.route('/contacts')
@require_staff()
def redirect_contacts():
    """Redirect old contacts page to clients"""
    return redirect(url_for('staff_portal.clients'))


@staff_portal.route('/cases')
@require_staff()
def redirect_cases():
    """Redirect old cases page to clients"""
    return redirect(url_for('staff_portal.clients'))


@staff_portal.route('/letter-queue')
@require_staff()
def redirect_letter_queue():
    """Redirect old letter queue to workflow"""
    return redirect(url_for('staff_portal.workflow', filter='letters'))


@staff_portal.route('/va-approval')
@require_staff()
def redirect_va_approval():
    """Redirect old VA approval to workflow"""
    return redirect(url_for('staff_portal.workflow', filter='approvals'))


@staff_portal.route('/analyses')
@require_staff()
def redirect_analyses():
    """Redirect old analyses to workflow"""
    return redirect(url_for('staff_portal.workflow', filter='analyses'))


@staff_portal.route('/settings')
@require_staff()
def redirect_settings():
    """Redirect old settings to admin"""
    return redirect(url_for('staff_portal.admin', section='settings'))


# ============================================
# CALENDAR
# ============================================

@staff_portal.route('/calendar')
@require_staff()
def calendar():
    """Calendar view showing all case deadlines"""
    from datetime import date
    db = get_db()
    try:
        today = date.today()
        week_from_now = today + timedelta(days=7)

        # Get stats
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

        stats = {
            'overdue': overdue_count,
            'upcoming': upcoming_this_week,
            'active': total_active,
            'completed': completed_this_month
        }

        return render_template('staff/calendar.html',
            active_tab='workflow',
            stats=stats
        )
    finally:
        db.close()


# ============================================
# SIGNUPS
# ============================================

@staff_portal.route('/signups')
@require_staff(roles=['admin', 'paralegal'])
def signups():
    """Admin view for signups and payment status"""
    db = get_db()
    try:
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
                'created_at': draft.created_at.strftime('%b %d, %Y') if draft.created_at else '',
                'expires_at': draft.expires_at.strftime('%b %d, %Y') if draft.expires_at else '',
                'contacted': form_data.get('contacted', False)
            })

        # Get Client records with payment info
        clients_query = db.query(Client).filter(Client.signup_plan != None).order_by(Client.created_at.desc())

        if status_filter == 'paid':
            clients_query = clients_query.filter(Client.payment_status == 'paid')
        elif status_filter == 'pending':
            clients_query = clients_query.filter(Client.payment_status == 'pending')
        elif status_filter == 'failed':
            clients_query = clients_query.filter(Client.payment_status == 'failed')
        elif status_filter == 'free':
            clients_query = clients_query.filter(Client.signup_plan == 'free')

        clients = []
        for client in clients_query.limit(100).all():
            clients.append({
                'id': client.id,
                'name': client.name or f"{client.first_name} {client.last_name}",
                'email': client.email,
                'signup_plan': client.signup_plan,
                'signup_amount': client.signup_amount or 0,
                'payment_status': client.payment_status or 'pending',
                'payment_method': getattr(client, 'payment_method', None) or 'pending',
                'created_at': client.created_at.strftime('%b %d, %Y') if client.created_at else '',
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

        # Counts for filters
        counts = {
            'all': db.query(Client).filter(Client.signup_plan != None).count() + len(drafts),
            'paid': db.query(Client).filter(Client.payment_status == 'paid').count(),
            'pending': pending_count,
            'failed': failed_count,
            'free': db.query(Client).filter(Client.signup_plan == 'free').count()
        }

        return render_template('staff/signups.html',
            active_tab='admin',
            drafts=drafts,
            clients=clients,
            stats=stats,
            counts=counts,
            filter=status_filter
        )
    finally:
        db.close()


# ============================================
# SETTLEMENTS
# ============================================

@staff_portal.route('/settlements')
@require_staff(roles=['admin', 'attorney', 'paralegal'])
def settlements():
    """Settlement tracking dashboard with pipeline view"""
    db = get_db()
    try:
        settlements_data = db.query(Settlement).order_by(Settlement.created_at.desc()).all()

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
        for s in settlements_data:
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
                'status_label': status.replace('_', ' ').title(),
                'settled_at': s.settled_at.strftime('%b %d, %Y') if s.settled_at else None,
                'payment_received': s.payment_received,
                'payment_amount': s.payment_amount,
                'contingency_earned': s.contingency_earned,
                'created_at': s.created_at.strftime('%b %d, %Y') if s.created_at else ''
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

        return render_template('staff/settlements.html',
            active_tab='workflow',
            settlements=settlement_list,
            status_counts=status_counts,
            stats=stats
        )
    finally:
        db.close()


# ============================================
# ANALYTICS
# ============================================

@staff_portal.route('/analytics')
@require_staff()
def analytics():
    """Analytics and Reporting Dashboard - Business Intelligence Metrics"""
    from sqlalchemy import func
    db = get_db()
    try:
        now = datetime.utcnow()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
        thirty_days_ago = now - timedelta(days=30)

        # Client stats
        total_clients = db.query(Client).count()
        new_this_month = db.query(Client).filter(Client.created_at >= start_of_month).count()
        active_clients = db.query(Client).filter(Client.status == 'active').count()
        complete_clients = db.query(Client).filter(Client.status == 'complete').count()

        client_stats = {
            'total': total_clients,
            'new_this_month': new_this_month,
            'active': active_clients,
            'complete': complete_clients
        }

        # Revenue stats
        total_revenue = db.query(func.sum(Client.signup_amount)).filter(
            Client.payment_status == 'paid',
            Client.signup_amount.isnot(None)
        ).scalar() or 0

        this_month_revenue = db.query(func.sum(Client.signup_amount)).filter(
            Client.payment_status == 'paid',
            Client.signup_amount.isnot(None),
            Client.payment_received_at >= start_of_month
        ).scalar() or 0

        last_month_revenue = db.query(func.sum(Client.signup_amount)).filter(
            Client.payment_status == 'paid',
            Client.signup_amount.isnot(None),
            Client.payment_received_at >= start_of_last_month,
            Client.payment_received_at < start_of_month
        ).scalar() or 0

        revenue_stats = {
            'total': total_revenue,
            'this_month': this_month_revenue,
            'last_month': last_month_revenue,
            'month_change': this_month_revenue - last_month_revenue
        }

        # Case stats
        total_analyses = db.query(Analysis).count()
        all_scores = db.query(CaseScore.total_score).filter(CaseScore.total_score.isnot(None)).all()
        avg_case_score = sum(s[0] for s in all_scores) / len(all_scores) if all_scores else 0
        high_score = len([s for s in all_scores if s[0] >= 8])
        medium_score = len([s for s in all_scores if 5 <= s[0] < 8])
        low_score = len([s for s in all_scores if s[0] < 5])

        case_stats = {
            'total_analyses': total_analyses,
            'avg_score': round(avg_case_score, 1),
            'high_score': high_score,
            'medium_score': medium_score,
            'low_score': low_score
        }

        # Dispute stats
        total_items = db.query(DisputeItem).count()
        items_deleted = db.query(DisputeItem).filter(DisputeItem.status == 'deleted').count()
        items_verified = db.query(DisputeItem).filter(DisputeItem.status == 'verified').count()
        items_in_progress = db.query(DisputeItem).filter(DisputeItem.status == 'in_progress').count()

        completed_items = items_deleted + items_verified
        success_rate = (items_deleted / completed_items * 100) if completed_items > 0 else 0

        dispute_stats = {
            'total_items': total_items,
            'deleted': items_deleted,
            'verified': items_verified,
            'in_progress': items_in_progress,
            'success_rate': round(success_rate, 1)
        }

        # CRA Response stats
        total_responses = db.query(CRAResponse).count()
        response_verified = db.query(CRAResponse).filter(CRAResponse.response_type == 'verified').count()
        response_deleted = db.query(CRAResponse).filter(CRAResponse.response_type == 'deleted').count()
        response_investigating = db.query(CRAResponse).filter(CRAResponse.response_type == 'investigating').count()

        cra_stats = {
            'total_responses': total_responses,
            'verified': response_verified,
            'deleted': response_deleted,
            'investigating': response_investigating
        }

        # Timeline data (last 14 days for simplicity)
        signup_data = []
        for i in range(14, -1, -1):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)

            day_signups = db.query(Client).filter(
                Client.created_at >= day_start,
                Client.created_at < day_end
            ).count()
            signup_data.append({
                'label': day_start.strftime('%b %d'),
                'count': day_signups
            })

        timeline_data = {
            'signups': signup_data
        }

        # Letter automation stats
        total_letters = db.query(func.sum(LetterBatch.letter_count)).scalar() or 0
        pending_approval = db.query(DisputeLetter).filter(
            DisputeLetter.sent_via_letterstream == False,
            DisputeLetter.file_path.isnot(None)
        ).count()

        automation_stats = {
            'total_letters': total_letters,
            'pending_approval': pending_approval
        }

        return render_template('staff/analytics.html',
            active_tab='admin',
            client_stats=client_stats,
            revenue_stats=revenue_stats,
            case_stats=case_stats,
            dispute_stats=dispute_stats,
            cra_stats=cra_stats,
            timeline_data=timeline_data,
            automation_stats=automation_stats
        )
    finally:
        db.close()


# ============================================
# CREDIT TRACKER
# ============================================

@staff_portal.route('/credit-tracker')
@require_staff()
def credit_tracker():
    """Credit tracker overview"""
    db = get_db()
    try:
        # Get clients with credit reports
        clients_with_reports = db.query(Client).filter(
            Client.status.in_(['active', 'in_progress', 'analyzing'])
        ).order_by(Client.updated_at.desc()).limit(50).all()

        clients_data = []
        for client in clients_with_reports:
            name = client.name or f"{client.first_name or ''} {client.last_name or ''}".strip() or 'Unknown'
            initials = ''.join([n[0].upper() for n in name.split()[:2]]) if name else 'U'

            # Get latest analysis
            analysis = db.query(Analysis).filter(Analysis.client_id == client.id).order_by(Analysis.created_at.desc()).first()

            # Get case score
            score = None
            if hasattr(client, 'case_scores') and client.case_scores:
                latest_score = max(client.case_scores, key=lambda x: x.created_at if x.created_at else datetime.min)
                score = latest_score.total_score if latest_score else None

            clients_data.append({
                'id': client.id,
                'name': name,
                'initials': initials,
                'email': client.email or '',
                'status': (client.status or 'new').replace('_', ' ').title(),
                'round': getattr(client, 'current_round', 1) or 1,
                'score': score,
                'updated_at': client.updated_at.strftime('%b %d, %Y') if client.updated_at else 'Never'
            })

        # Stats
        stats = {
            'total_tracked': len(clients_data),
            'in_progress': db.query(Client).filter(Client.status == 'in_progress').count(),
            'analyzing': db.query(Client).filter(Client.status == 'analyzing').count(),
            'complete': db.query(Client).filter(Client.status == 'complete').count()
        }

        return render_template('staff/credit_tracker.html',
            active_tab='clients',
            clients=clients_data,
            stats=stats
        )
    finally:
        db.close()


@staff_portal.route('/credit-import')
@require_staff()
def credit_import():
    """Credit report import page"""
    db = get_db()
    try:
        # Get recent imports - using CreditReport or a similar model
        # For now, we'll provide placeholder data
        recent_imports = []

        # Stats
        pending_count = 0
        processing_count = 0
        completed_today = 0
        total_imported = 0

        return render_template('staff/credit_import.html',
            active_tab='workflow',
            recent_imports=recent_imports,
            pending_count=pending_count,
            processing_count=processing_count,
            completed_today=completed_today,
            total_imported=total_imported
        )
    finally:
        db.close()


@staff_portal.route('/credit-import/upload', methods=['POST'])
@require_staff()
def credit_import_upload():
    """Handle credit report file uploads"""
    from werkzeug.utils import secure_filename
    import os

    if 'files' not in request.files:
        return jsonify({'success': False, 'error': 'No files provided'})

    files = request.files.getlist('files')
    imported = []

    upload_folder = os.path.join(os.getcwd(), 'uploads', 'credit_reports')
    os.makedirs(upload_folder, exist_ok=True)

    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            imported.append(filename)

    return jsonify({'success': True, 'imported': imported})
