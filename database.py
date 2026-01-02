import os
from typing import Any
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, Time, Boolean, Float, ForeignKey, event, JSON, text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# CI mode: skip SSL (GitHub Actions uses local PostgreSQL)
# Production: require SSL for Replit/Neon Postgres
if os.getenv('CI') != 'true':
    if 'sslmode' not in DATABASE_URL:
        DATABASE_URL = DATABASE_URL + "?sslmode=require"

# Create engine with connection pooling + resilience for large text writes
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,  # Recycle every 30 min instead of 1 hour
    connect_args={
        # Note: connect_timeout removed - not supported by all PostgreSQL providers
        # Timeouts are handled via statement_timeout in the event listener below
        "keepalives": 1,
        "keepalives_idle": 10,  # Start keepalives after 10s idle
        "keepalives_interval": 5,  # Send keepalive every 5s
        "keepalives_count": 10,  # Need 10 failed keepalives to fail
    }
)

# Set aggressive timeouts on each connection
@event.listens_for(engine, "connect")
def set_timeouts(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("SET statement_timeout = 180000")  # 180 seconds
    cursor.execute("SET idle_in_transaction_session_timeout = 180000")
    cursor.execute("SET lock_timeout = 180000")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base: Any = declarative_base()

STAFF_ROLES = {
    'admin': {
        'name': 'Administrator',
        'description': 'Full access to everything including staff management',
        'permissions': ['*']
    },
    'attorney': {
        'name': 'Attorney',
        'description': 'View cases, approve analyses, view documents, edit legal documents',
        'permissions': ['view_dashboard', 'view_cases', 'view_clients', 'approve_analyses', 'view_documents', 'edit_legal_documents', 'view_analytics', 'view_settlements']
    },
    'paralegal': {
        'name': 'Paralegal',
        'description': 'Manage clients, upload documents, send letters, manage deadlines',
        'permissions': ['view_dashboard', 'view_cases', 'manage_clients', 'upload_documents', 'send_letters', 'manage_deadlines', 'view_analytics', 'manage_signups']
    },
    'viewer': {
        'name': 'Viewer',
        'description': 'Read-only access to dashboard and reports',
        'permissions': ['view_dashboard', 'view_cases', 'view_clients', 'view_analytics', 'view_documents']
    }
}

def check_staff_permission(role, permission):
    """Check if a role has a specific permission"""
    if role not in STAFF_ROLES:
        return False
    role_perms = STAFF_ROLES[role]['permissions']
    return '*' in role_perms or permission in role_perms


class Staff(Base):
    """Staff/team member accounts for platform access"""
    __tablename__ = 'staff'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(String(50), default='viewer')
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    password_reset_token = Column(String(100), unique=True, index=True)
    password_reset_expires = Column(DateTime)
    force_password_change = Column(Boolean, default=False)
    created_by_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    organization_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.email.split('@')[0]
    
    @property
    def initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.email[0].upper()
    
    def has_permission(self, permission):
        return check_staff_permission(self.role, permission)


class Client(Base):
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255))
    phone = Column(String(50))
    
    # Address fields
    address_street = Column(String(255))
    address_city = Column(String(100))
    address_state = Column(String(50))
    address_zip = Column(String(20))
    
    # Identity for disputes (NOTE: Encrypt in production)
    ssn_last_four = Column(String(4))
    date_of_birth = Column(Date)
    
    # Credit monitoring credentials (NOTE: Encrypt in production)
    credit_monitoring_service = Column(String(100))  # IdentityIQ, MyScoreIQ, etc.
    credit_monitoring_username = Column(String(255))
    credit_monitoring_password_encrypted = Column(Text)  # Encrypted credential
    
    # Dispute tracking
    current_dispute_round = Column(Integer, default=0)  # 0=new, 1-4=active rounds
    current_dispute_step = Column(String(100))  # For fine-grained tracking
    dispute_status = Column(String(50), default='new')  # new, active, waiting_response, complete
    round_started_at = Column(DateTime)
    last_bureau_response_at = Column(DateTime)
    
    # Import tracking (for existing clients)
    legacy_system_id = Column(String(100))  # ID from CMM or other system
    legacy_case_number = Column(String(100))
    imported_at = Column(DateTime)
    import_notes = Column(Text)
    
    # Referral tracking
    referred_by_client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    referred_by_affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=True)
    referral_code = Column(String(50), unique=True)
    
    # Client portal access
    portal_token = Column(String(100), unique=True, index=True)
    portal_password_hash = Column(String(255))  # For client login
    password_reset_token = Column(String(100), unique=True, index=True)
    password_reset_expires = Column(DateTime)
    
    # Status
    status = Column(String(50), default='signup')  # signup, active, paused, complete, cancelled
    signup_completed = Column(Boolean, default=False)
    agreement_signed = Column(Boolean, default=False)
    agreement_signed_at = Column(DateTime)
    
    # Legacy
    cmm_contact_id = Column(String(100))
    
    # Notes
    admin_notes = Column(Text)
    
    # Profile/Avatar
    avatar_filename = Column(String(255))  # Stored in static/avatars/
    
    # Payment/Stripe fields
    signup_plan = Column(String(50))  # free, tier1, tier2, tier3, tier4, tier5
    signup_amount = Column(Integer)  # Amount in cents
    stripe_customer_id = Column(String(255))
    stripe_checkout_session_id = Column(String(255))
    stripe_payment_intent_id = Column(String(255))
    payment_status = Column(String(50), default='pending')  # pending, paid, failed, refunded
    payment_received_at = Column(DateTime)
    payment_method = Column(String(50), default='pending')  # stripe, paypal, cashapp, venmo, zelle, pending, free
    payment_pending = Column(Boolean, default=False)  # True if waiting for manual confirmation
    
    # Contact management fields (CMM style)
    client_type = Column(String(1), default='L')  # L=Lead, C=Active Client, I=Inactive, O=Other, P=Provider, X=Cancelled
    status_2 = Column(String(100))  # Secondary status field
    company = Column(String(255))
    phone_2 = Column(String(50))
    mobile = Column(String(50))
    website = Column(String(255))
    is_affiliate = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    groups = Column(String(500))  # Comma-separated tags
    mark_1 = Column(Boolean, default=False)  # Color marking flag 1
    mark_2 = Column(Boolean, default=False)  # Color marking flag 2
    starred = Column(Boolean, default=False)  # Star/favorite toggle
    phone_verified = Column(Boolean, default=False)  # Phone verified checkbox
    portal_posted = Column(Boolean, default=False)  # Portal posted status

    # Communication preferences
    sms_opt_in = Column(Boolean, default=False)  # Client opted in for SMS notifications
    email_opt_in = Column(Boolean, default=True)  # Client opted in for email notifications (default on)

    # Lead scoring
    lead_score = Column(Integer, default=0)  # 0-100 priority score based on credit report analysis
    lead_score_factors = Column(JSON)  # Breakdown of scoring factors
    lead_scored_at = Column(DateTime)  # When the score was last calculated

    assigned_to = Column(Integer, ForeignKey('staff.id'), nullable=True)  # Assigned staff member
    employer_company = Column(String(255))  # Employer/company name for client

    # Client Journey Stage Tracking
    # Stages: lead, analysis_paid, onboarding, pending_payment, active, payment_failed, cancelled
    client_stage = Column(String(30), default='lead', index=True)

    # Free/Paid Analysis Tracking
    free_analysis_token = Column(String(64), unique=True, index=True)  # Token for /analysis/<token> page
    analysis_payment_id = Column(String(100))  # Stripe PaymentIntent ID for $199 analysis
    analysis_paid_at = Column(DateTime)  # When they paid for full analysis
    analysis_credit_applied = Column(Boolean, default=False)  # True when $199 credited to Round 1

    # Round Payment Tracking
    round_1_amount_due = Column(Integer)  # Amount due for Round 1 in cents (49700 - 19900 = 29800)
    current_round_payment_id = Column(String(100))  # Stripe PaymentIntent for current round
    last_round_paid_at = Column(DateTime)  # When the last round was paid
    total_paid = Column(Integer, default=0)  # Total amount paid in cents

    # Prepay Package Tracking
    prepay_package = Column(String(50))  # starter, standard, complete, unlimited
    prepay_rounds_remaining = Column(Integer)  # Rounds remaining if prepaid

    organization_id = Column(Integer, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClientTag(Base):
    """Tags for organizing and categorizing clients"""
    __tablename__ = 'client_tags'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(7), default='#6366f1')  # Hex color code
    created_at = Column(DateTime, default=datetime.utcnow)


class ClientTagAssignment(Base):
    """Many-to-many relationship between clients and tags"""
    __tablename__ = 'client_tag_assignments'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    tag_id = Column(Integer, ForeignKey('client_tags.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserQuickLink(Base):
    """Custom quick links for staff users (slots 1-8)"""
    __tablename__ = 'user_quick_links'

    id = Column(Integer, primary_key=True, index=True)
    staff_id = Column(Integer, ForeignKey('staff.id', ondelete='CASCADE'), nullable=False, index=True)
    slot_number = Column(Integer, nullable=False)  # 1-8
    label = Column(String(50), nullable=False)
    url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class CreditReport(Base):
    __tablename__ = 'credit_reports'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False)
    client_name = Column(String(255), nullable=False)
    credit_provider = Column(String(100))
    report_html = Column(Text)
    report_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True, index=True)
    credit_report_id = Column(Integer, nullable=False)
    client_id = Column(Integer, nullable=False)
    client_name = Column(String(255), nullable=False)
    dispute_round = Column(Integer, nullable=False)
    analysis_mode = Column(String(20))
    stage = Column(Integer, default=1)  # 1=violations/standing/damages, 2=documents/letters
    stage_1_analysis = Column(Text)  # Stage 1 results (violations + standing + damages)
    full_analysis = Column(Text)  # Stage 2 results (full report + letters)
    cost = Column(Float)
    tokens_used = Column(Integer)
    cache_read = Column(Boolean, default=False)
    approved_at = Column(DateTime, nullable=True)  # When user approves stage 1
    created_at = Column(DateTime, default=datetime.utcnow)

class DisputeLetter(Base):
    __tablename__ = 'dispute_letters'
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, nullable=False)
    client_id = Column(Integer, nullable=False)
    client_name = Column(String(255), nullable=False)
    bureau = Column(String(50))
    round_number = Column(Integer)
    letter_content = Column(Text)
    file_path = Column(String(500))
    sent_via_letterstream = Column(Boolean, default=False)
    letterstream_id = Column(String(100))
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Violation(Base):
    __tablename__ = 'violations'
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=False)
    client_id = Column(Integer, nullable=False)
    
    # Violation details
    bureau = Column(String(50))
    account_name = Column(String(255))
    fcra_section = Column(String(50))
    violation_type = Column(String(100))
    description = Column(Text)
    
    # Damages
    statutory_damages_min = Column(Float, default=0)
    statutory_damages_max = Column(Float, default=0)
    
    # Willfulness indicators
    is_willful = Column(Boolean, default=False)
    willfulness_notes = Column(Text)
    
    # Statute of Limitations (SOL) tracking - FCRA § 1681p
    violation_date = Column(Date)
    discovery_date = Column(Date)
    sol_expiration_date = Column(Date)
    sol_warning_sent = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Standing(Base):
    __tablename__ = 'standing'
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=False)
    client_id = Column(Integer, nullable=False)
    
    # Post-TransUnion standing elements
    has_concrete_harm = Column(Boolean, default=False)
    concrete_harm_type = Column(Text)
    concrete_harm_details = Column(Text)
    
    has_dissemination = Column(Boolean, default=False)
    dissemination_details = Column(Text)
    
    has_causation = Column(Boolean, default=False)
    causation_details = Column(Text)
    
    # Supporting documents
    denial_letters_count = Column(Integer, default=0)
    adverse_action_notices_count = Column(Integer, default=0)
    
    standing_verified = Column(Boolean, default=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Damages(Base):
    __tablename__ = 'damages'
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=False)
    client_id = Column(Integer, nullable=False)
    
    # Actual damages
    credit_denials_amount = Column(Float, default=0)
    higher_interest_amount = Column(Float, default=0)
    credit_monitoring_amount = Column(Float, default=0)
    time_stress_amount = Column(Float, default=0)
    other_actual_amount = Column(Float, default=0)
    actual_damages_total = Column(Float, default=0)
    
    # Statutory damages
    section_605b_count = Column(Integer, default=0)
    section_605b_amount = Column(Float, default=0)
    
    section_607b_count = Column(Integer, default=0)
    section_607b_amount = Column(Float, default=0)
    
    section_611_count = Column(Integer, default=0)
    section_611_amount = Column(Float, default=0)
    
    section_623_count = Column(Integer, default=0)
    section_623_amount = Column(Float, default=0)
    
    statutory_damages_total = Column(Float, default=0)
    
    # Punitive damages
    willfulness_multiplier = Column(Float, default=0)
    punitive_damages_amount = Column(Float, default=0)
    
    # Attorney fees
    estimated_hours = Column(Float, default=0)
    hourly_rate = Column(Float, default=0)
    attorney_fees_projection = Column(Float, default=0)
    
    # Settlement targets
    total_exposure = Column(Float, default=0)
    settlement_target = Column(Float, default=0)
    minimum_acceptable = Column(Float, default=0)
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class CaseScore(Base):
    __tablename__ = 'case_scores'
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=False)
    client_id = Column(Integer, nullable=False)
    
    # Scoring components (total 10 points)
    standing_score = Column(Integer, default=0)
    violation_quality_score = Column(Integer, default=0)
    willfulness_score = Column(Integer, default=0)
    documentation_score = Column(Integer, default=0)
    
    # Total score
    total_score = Column(Integer, default=0)
    
    # Settlement probability
    settlement_probability = Column(Float, default=0)
    case_strength = Column(String(50))
    
    # Recommendation
    recommendation = Column(String(50))
    recommendation_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# NEW TABLES FOR COMPLETE PLATFORM
# ============================================================

class Case(Base):
    """Main case tracking - links client to analysis with status pipeline"""
    __tablename__ = 'cases'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    
    # Case identification
    case_number = Column(String(50), unique=True, index=True)
    
    # Status pipeline
    status = Column(String(50), default='intake')  # intake, stage1_pending, stage1_complete, stage2_pending, stage2_complete, delivered, settled
    
    # Pricing tier
    pricing_tier = Column(String(50), default='tier1')  # tier1, tier2, tier3
    base_fee = Column(Float, default=0)
    contingency_percent = Column(Float, default=0)
    
    # Client portal access
    portal_token = Column(String(100), unique=True, index=True)
    portal_expires = Column(DateTime)
    
    # Tracking
    intake_at = Column(DateTime)
    stage1_completed_at = Column(DateTime)
    stage2_completed_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Notes
    admin_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CaseEvent(Base):
    """Timeline log of all case activities"""
    __tablename__ = 'case_events'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    
    event_type = Column(String(50))  # intake, analysis_started, analysis_complete, approved, letter_sent, settlement_offer, etc.
    description = Column(Text)
    event_data = Column(Text)  # JSON for extra data
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    """Stores generated documents with download tracking"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    
    document_type = Column(String(50))  # credit_report, stage1_analysis, stage2_report, dispute_letter, settlement_demand, cfpb_complaint
    filename = Column(String(255))
    file_path = Column(String(500))
    file_size = Column(Integer)
    
    # For bureau-specific letters
    bureau = Column(String(50))
    
    # Tracking
    download_count = Column(Integer, default=0)
    last_downloaded_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    """Email/SMS notification history"""
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    notification_type = Column(String(50))  # email, sms
    template = Column(String(100))  # intake_confirmation, stage1_complete, stage2_ready, etc.
    recipient = Column(String(255))
    subject = Column(String(255))
    body = Column(Text)
    
    # Status
    status = Column(String(50), default='pending')  # pending, sent, failed
    sent_at = Column(DateTime)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Settlement(Base):
    """Track settlement negotiations"""
    __tablename__ = 'settlements'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=False)
    
    # Target based on analysis
    target_amount = Column(Float, default=0)
    minimum_acceptable = Column(Float, default=0)
    
    # Bureau breakdown
    transunion_target = Column(Float, default=0)
    experian_target = Column(Float, default=0)
    equifax_target = Column(Float, default=0)
    
    # Negotiation tracking
    status = Column(String(50), default='pending')  # pending, demand_sent, negotiating, accepted, rejected, litigated
    
    # Offers
    initial_demand = Column(Float, default=0)
    initial_demand_date = Column(DateTime)
    counter_offer_1 = Column(Float, default=0)
    counter_offer_1_date = Column(DateTime)
    counter_offer_2 = Column(Float, default=0)
    counter_offer_2_date = Column(DateTime)
    final_amount = Column(Float, default=0)
    
    # Outcome
    settled_at = Column(DateTime)
    settlement_notes = Column(Text)
    
    # Payment tracking
    payment_received = Column(Boolean, default=False)
    payment_amount = Column(Float, default=0)
    payment_date = Column(DateTime)
    contingency_earned = Column(Float, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisQueue(Base):
    """Batch processing queue"""
    __tablename__ = 'analysis_queue'
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    client_id = Column(Integer, nullable=False)
    
    # Queue details
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest
    stage = Column(Integer, default=1)  # 1 or 2
    
    # Status
    status = Column(String(50), default='queued')  # queued, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    
    # Credit report data
    credit_provider = Column(String(100))
    dispute_round = Column(Integer, default=1)
    credit_report_html = Column(Text)
    
    # Processing info
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    # Result
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CRAResponse(Base):
    """Track Credit Reporting Agency response letters"""
    __tablename__ = 'cra_responses'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    
    # Which bureau and round
    bureau = Column(String(50))  # Experian, TransUnion, Equifax
    dispute_round = Column(Integer, default=1)
    
    # Response details
    response_type = Column(String(50))  # verified, deleted, updated, investigating, no_response, frivolous
    response_date = Column(Date)
    received_date = Column(Date)
    
    # Uploaded letter/document
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    
    # Upload attribution
    uploaded_by_admin = Column(Boolean, default=True)  # True=admin, False=client
    uploaded_by_user_id = Column(Integer)  # Admin user ID if applicable
    
    # Parsed response content
    response_text = Column(Text)  # OCR or extracted text from PDF
    items_verified = Column(Integer, default=0)
    items_deleted = Column(Integer, default=0)
    items_updated = Column(Integer, default=0)
    structured_items = Column(JSON)  # Detailed breakdown for automation
    
    # Follow-up tracking
    requires_follow_up = Column(Boolean, default=False)
    follow_up_deadline = Column(DateTime)  # Usually 30 days from response
    follow_up_completed = Column(Boolean, default=False)
    
    # Analysis notes
    admin_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DisputeItem(Base):
    """Track individual account/item disputes with status"""
    __tablename__ = 'dispute_items'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    
    # Which bureau and round
    bureau = Column(String(50), nullable=False)  # Experian, TransUnion, Equifax
    dispute_round = Column(Integer, default=1)
    
    # Item details
    item_type = Column(String(50))  # inquiry, collection, late_payment, personal_info, public_record
    creditor_name = Column(String(255))
    account_id = Column(String(100))  # Masked account number
    
    # Status tracking
    status = Column(String(50), default='to_do')  # sent, deleted, updated, in_progress, to_do, no_change, no_answer, on_hold, positive, duplicate, other
    
    # FCRA Escalation Pathway (Credit Repair Warfare)
    # Stages: section_611 -> section_623 -> section_621 -> section_616_617
    escalation_stage = Column(String(50), default='section_611')  # section_611, section_623, section_621, section_616_617
    escalation_notes = Column(Text)  # Notes on escalation decisions
    furnisher_dispute_sent = Column(Boolean, default=False)  # §623 direct dispute sent
    furnisher_dispute_date = Column(Date)  # When §623 dispute was sent
    cfpb_complaint_filed = Column(Boolean, default=False)  # §621 CFPB complaint
    cfpb_complaint_date = Column(Date)
    cfpb_complaint_id = Column(String(100))  # CFPB complaint reference number
    attorney_referral = Column(Boolean, default=False)  # §§616-617 attorney involvement
    attorney_referral_date = Column(Date)
    method_of_verification_requested = Column(Boolean, default=False)  # §611(a)(6)(B)(iii)
    method_of_verification_received = Column(Boolean, default=False)
    
    # Dates
    follow_up_date = Column(Date)  # When to follow up
    sent_date = Column(Date)  # When dispute was sent
    response_date = Column(Date)  # When response received
    
    # Client/admin interaction
    reason = Column(Text)  # Reason for dispute or status
    comments = Column(Text)  # Client or admin comments
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LetterQueue(Base):
    """Queue for auto-suggested letters based on escalation triggers"""
    __tablename__ = 'letter_queue'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    dispute_item_id = Column(Integer, ForeignKey('dispute_items.id'), nullable=True)
    
    # Letter type (matches advanced letter templates)
    letter_type = Column(String(50), nullable=False)
    # Types: mov_request, fdcpa_validation, respa_qwr, reg_z_dispute, 
    #        section_605b_block, section_623_direct, reinsertion_challenge
    
    # Trigger info
    trigger_type = Column(String(100), nullable=False)
    # Triggers: cra_verified, no_cra_response_35_days, collection_disputed, 
    #           mortgage_late, item_reinserted, mov_inadequate, escalation_stage_change
    trigger_description = Column(Text)  # Human-readable trigger explanation
    trigger_date = Column(DateTime, default=datetime.utcnow)
    
    # Target info
    target_bureau = Column(String(50))  # Experian, TransUnion, Equifax
    target_creditor = Column(String(255))  # Creditor/furnisher name
    target_account = Column(String(100))  # Account number (masked)
    
    # Pre-filled letter data (JSON)
    letter_data = Column(JSON)  # Pre-populated fields for the letter
    
    # Priority and status
    priority = Column(String(20), default='normal')  # urgent, high, normal, low
    status = Column(String(50), default='pending')  # pending, approved, dismissed, generated, sent
    
    # Staff action tracking
    reviewed_by_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    reviewed_at = Column(DateTime)
    action_notes = Column(Text)  # Staff notes on approval/dismissal
    
    # Generated letter info
    generated_letter_id = Column(Integer, ForeignKey('dispute_letters.id'), nullable=True)
    generated_at = Column(DateTime)
    generated_pdf_path = Column(String(500))
    
    # Notification tracking
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SecondaryBureauFreeze(Base):
    """Track freeze status with secondary credit bureaus"""
    __tablename__ = 'secondary_bureau_freezes'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    # Secondary bureau info
    bureau_name = Column(String(100), nullable=False)  # Innovis, ChexSystems, Clarity, LexisNexis, etc.
    
    # Status
    status = Column(String(50), default='pending')  # pending, frozen, not_frozen, error
    
    # Dates
    follow_up_date = Column(Date)
    freeze_requested_at = Column(DateTime)
    freeze_confirmed_at = Column(DateTime)
    
    # Notes
    comments = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClientReferral(Base):
    """Track referrals between clients"""
    __tablename__ = 'client_referrals'
    
    id = Column(Integer, primary_key=True, index=True)
    referring_client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    referred_client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    
    # Referral info
    referred_name = Column(String(255))
    referred_email = Column(String(255))
    referred_phone = Column(String(50))
    
    # Status
    status = Column(String(50), default='pending')  # pending, contacted, signed_up, converted
    
    # Reward tracking
    reward_type = Column(String(50))  # discount, credit, cash
    reward_amount = Column(Float, default=0)
    reward_paid = Column(Boolean, default=False)
    reward_paid_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Affiliate(Base):
    """Affiliate partners for two-level commission tracking"""
    __tablename__ = 'affiliates'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50))
    company_name = Column(String(255))
    
    affiliate_code = Column(String(50), unique=True, nullable=False, index=True)
    parent_affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=True)
    
    commission_rate_1 = Column(Float, default=0.10)
    commission_rate_2 = Column(Float, default=0.05)
    
    status = Column(String(50), default='pending')

    # Authentication for affiliate portal
    password_hash = Column(String(255))
    last_login = Column(DateTime)
    login_count = Column(Integer, default=0)

    payout_method = Column(String(50))
    payout_details = Column(JSON)
    
    total_referrals = Column(Integer, default=0)
    total_earnings = Column(Float, default=0.0)
    pending_earnings = Column(Float, default=0.0)
    paid_out = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parent = relationship("Affiliate", remote_side=[id], backref="sub_affiliates")


class Commission(Base):
    """Commission records for affiliate referrals"""
    __tablename__ = 'commissions'
    
    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    level = Column(Integer, default=1)
    
    trigger_type = Column(String(50), nullable=False)
    trigger_amount = Column(Float, default=0.0)
    commission_rate = Column(Float, default=0.0)
    commission_amount = Column(Float, default=0.0)
    
    status = Column(String(50), default='pending')
    
    paid_at = Column(DateTime)
    payout_id = Column(Integer)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    affiliate = relationship("Affiliate", backref="commissions")


class AffiliatePayout(Base):
    """Track affiliate payout history"""
    __tablename__ = 'affiliate_payouts'

    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(Integer, ForeignKey('affiliates.id'), nullable=False)

    # Payout details
    amount = Column(Float, nullable=False)
    payout_method = Column(String(50))  # paypal, bank_transfer, check, venmo
    payout_reference = Column(String(255))  # Transaction ID, check number, etc.

    # Status
    status = Column(String(50), default='pending')  # pending, processing, completed, failed

    # Period covered
    period_start = Column(DateTime)
    period_end = Column(DateTime)

    # Commission IDs included in this payout
    commission_ids = Column(JSON)  # List of commission IDs

    notes = Column(Text)
    processed_by_id = Column(Integer, ForeignKey('staff.id'))
    processed_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    affiliate = relationship("Affiliate", backref="payouts")
    processed_by = relationship("Staff")


class SignupDraft(Base):
    """Store pre-payment signup data temporarily until payment is confirmed"""
    __tablename__ = 'signup_drafts'
    
    id = Column(Integer, primary_key=True, index=True)
    draft_uuid = Column(String(36), unique=True, index=True, nullable=False)
    
    # All form data stored as JSON
    form_data = Column(JSON, nullable=False)
    
    # Selected plan
    plan_tier = Column(String(50))  # tier1-tier5
    plan_amount = Column(Integer)  # Amount in cents
    
    # Stripe tracking
    stripe_checkout_session_id = Column(String(255))
    
    # Status tracking
    status = Column(String(50), default='pending')  # pending, paid, expired, cancelled
    
    # Expiration
    expires_at = Column(DateTime, nullable=False)
    
    # Promotion to full client
    promoted_client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    promoted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Task(Base):
    """Tasks/reminders for client management"""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    title = Column(String(255), nullable=False)
    task_type = Column(String(50))  # call, email, follow_up, document, dispute, other
    description = Column(Text)
    
    due_date = Column(Date)
    due_time = Column(String(10))  # HH:MM format
    
    status = Column(String(50), default='pending')  # pending, completed, cancelled
    assigned_to = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClientNote(Base):
    """Notes/comments for client records"""
    __tablename__ = 'client_notes'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    note_content = Column(Text, nullable=False)
    created_by = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class ClientDocument(Base):
    """Track document receipt status for clients"""
    __tablename__ = 'client_documents'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    document_type = Column(String(50), nullable=False)  # agreement, cr_login, drivers_license, ssn_card, utility_bill, poa, other
    file_path = Column(String(500))
    
    received = Column(Boolean, default=False)
    received_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClientUpload(Base):
    """Unified document uploads from clients"""
    __tablename__ = 'client_uploads'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    
    category = Column(String(50), nullable=False)
    document_type = Column(String(100), nullable=False)
    
    bureau = Column(String(50))
    dispute_round = Column(Integer)
    response_type = Column(String(50))
    
    sender_name = Column(String(200))
    account_number = Column(String(100))
    amount_claimed = Column(Float)
    
    file_path = Column(String(500))
    file_name = Column(String(255))
    file_size = Column(Integer)
    file_type = Column(String(50))
    
    document_date = Column(Date)
    received_date = Column(Date)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    notes = Column(Text)
    
    requires_action = Column(Boolean, default=False)
    action_deadline = Column(Date)
    priority = Column(String(20), default='normal')
    
    harm_amount = Column(Float)
    harm_description = Column(Text)
    creditor_name = Column(String(200))
    lender_name = Column(String(200))
    dispute_reference = Column(String(255))
    income_period = Column(String(50))
    call_duration = Column(Integer)
    call_date = Column(DateTime)
    ocr_extracted = Column(Boolean, default=False)
    ocr_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TimelineEvent(Base):
    """Track client journey events for visual timeline display"""
    __tablename__ = 'timeline_events'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)

    # Event details
    event_type = Column(String(50), nullable=False, index=True)  # signup, document_uploaded, analysis_complete, dispute_sent, response_received, etc.
    event_category = Column(String(50), default='general')  # onboarding, documents, disputes, responses, status
    title = Column(String(200), nullable=False)  # Human-readable title
    description = Column(Text)  # Optional detailed description
    icon = Column(String(50))  # Font Awesome icon class

    # Related entities
    related_type = Column(String(50))  # dispute_letter, client_upload, analysis, cra_response, etc.
    related_id = Column(Integer)  # ID of the related entity

    # Metadata
    metadata_json = Column(JSON)  # Extra event data (bureau, round, etc.)
    is_milestone = Column(Boolean, default=False)  # Major events shown prominently
    is_visible = Column(Boolean, default=True)  # Can hide system events

    # Timestamps
    event_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SignupSettings(Base):
    """Store configurable signup settings as key-value pairs"""
    __tablename__ = 'signup_settings'
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(Text)  # JSON for complex settings
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SMSLog(Base):
    """Log all SMS send attempts for tracking and debugging"""
    __tablename__ = 'sms_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    phone_number = Column(String(20))
    message = Column(Text)
    template_type = Column(String(50))
    status = Column(String(20))
    twilio_sid = Column(String(50))
    sent_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailLog(Base):
    """Log all email send attempts for tracking and debugging"""
    __tablename__ = 'email_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    email_address = Column(String(255))
    subject = Column(String(500))
    template_type = Column(String(50))
    status = Column(String(20))
    message_id = Column(String(100))
    sent_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class EmailTemplate(Base):
    """Store email templates for client communications"""
    __tablename__ = 'email_templates'

    id = Column(Integer, primary_key=True, index=True)
    template_type = Column(String(50), nullable=False, unique=True)  # e.g., 'welcome', 'dispute_sent'
    name = Column(String(200), nullable=False)  # Human-readable name
    category = Column(String(50), default='general')  # welcome, updates, reminders, notifications, etc.
    description = Column(Text)  # What this template is for
    subject = Column(String(500), nullable=False)
    html_content = Column(Text)
    plain_text_content = Column(Text)  # Plain text version for fallback
    design_json = Column(Text)  # For visual editor (Unlayer)
    variables = Column(JSON)  # Supported variables: [{name, description, example}]
    is_custom = Column(Boolean, default=False)  # True if user-created, False if system default
    is_active = Column(Boolean, default=True)  # Can be disabled without deleting
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SMSTemplate(Base):
    """Store SMS templates for client communications"""
    __tablename__ = 'sms_templates'

    id = Column(Integer, primary_key=True, index=True)
    template_type = Column(String(50), nullable=False, unique=True)  # e.g., 'welcome', 'dispute_sent'
    name = Column(String(200), nullable=False)  # Human-readable name
    category = Column(String(50), default='general')  # welcome, updates, reminders, notifications, etc.
    description = Column(Text)  # What this template is for
    message = Column(Text, nullable=False)  # The SMS message content
    variables = Column(JSON)  # Supported variables: [{name, description, example}]
    is_custom = Column(Boolean, default=False)  # True if user-created, False if system default
    is_active = Column(Boolean, default=True)  # Can be disabled without deleting
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DripCampaign(Base):
    """Automated email sequences for client follow-ups"""
    __tablename__ = 'drip_campaigns'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)

    # Trigger conditions
    trigger_type = Column(String(50), nullable=False)  # signup, status_change, manual, tag_added
    trigger_value = Column(String(100))  # e.g., status value, tag name

    # Campaign settings
    is_active = Column(Boolean, default=True)
    send_window_start = Column(Integer, default=9)  # Hour to start sending (9 AM)
    send_window_end = Column(Integer, default=17)  # Hour to stop sending (5 PM)
    send_on_weekends = Column(Boolean, default=False)

    # Stats
    total_enrolled = Column(Integer, default=0)
    total_completed = Column(Integer, default=0)

    created_by_id = Column(Integer, ForeignKey('staff.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    steps = relationship("DripStep", back_populates="campaign", cascade="all, delete-orphan", order_by="DripStep.step_order")
    enrollments = relationship("DripEnrollment", back_populates="campaign", cascade="all, delete-orphan")


class DripStep(Base):
    """Individual step in a drip campaign"""
    __tablename__ = 'drip_steps'

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('drip_campaigns.id', ondelete='CASCADE'), nullable=False)

    step_order = Column(Integer, nullable=False)  # 1, 2, 3, etc.
    name = Column(String(200))  # Optional step name

    # Timing
    delay_days = Column(Integer, default=1)  # Days after previous step (or enrollment)
    delay_hours = Column(Integer, default=0)  # Additional hours

    # Email content
    email_template_id = Column(Integer, ForeignKey('email_templates.id'))  # Use existing template
    subject = Column(String(500))  # Override subject if not using template
    html_content = Column(Text)  # Override content if not using template

    # Conditions
    condition_type = Column(String(50))  # none, if_opened, if_not_opened, if_clicked
    condition_value = Column(String(100))  # For if_clicked, the link to check

    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("DripCampaign", back_populates="steps")
    email_template = relationship("EmailTemplate")


class DripEnrollment(Base):
    """Track client enrollment in drip campaigns"""
    __tablename__ = 'drip_enrollments'

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey('drip_campaigns.id', ondelete='CASCADE'), nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)

    # Current progress
    current_step = Column(Integer, default=0)  # 0 = not started, 1 = first step sent, etc.
    status = Column(String(20), default='active')  # active, paused, completed, cancelled

    # Timing
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    next_send_at = Column(DateTime)  # When to send next step
    last_sent_at = Column(DateTime)  # When last step was sent
    completed_at = Column(DateTime)

    # Tracking
    emails_sent = Column(Integer, default=0)
    emails_opened = Column(Integer, default=0)
    emails_clicked = Column(Integer, default=0)

    # Metadata
    paused_reason = Column(String(200))
    cancelled_reason = Column(String(200))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    campaign = relationship("DripCampaign", back_populates="enrollments")
    client = relationship("Client")

    # Unique constraint - one enrollment per client per campaign
    __table_args__ = (
        UniqueConstraint('campaign_id', 'client_id', name='uq_drip_enrollment_campaign_client'),
    )


class DripEmailLog(Base):
    """Log of emails sent through drip campaigns"""
    __tablename__ = 'drip_email_logs'

    id = Column(Integer, primary_key=True, index=True)
    enrollment_id = Column(Integer, ForeignKey('drip_enrollments.id', ondelete='CASCADE'), nullable=False)
    step_id = Column(Integer, ForeignKey('drip_steps.id', ondelete='SET NULL'))

    subject = Column(String(500))
    sent_at = Column(DateTime, default=datetime.utcnow)

    # Tracking
    opened_at = Column(DateTime)
    clicked_at = Column(DateTime)
    click_url = Column(String(500))

    # Delivery status
    status = Column(String(20), default='sent')  # sent, delivered, opened, clicked, bounced, failed
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)


class CaseDeadline(Base):
    """Track deadlines for dispute responses and required actions"""
    __tablename__ = 'case_deadlines'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    
    deadline_type = Column(String(50), nullable=False)
    bureau = Column(String(50))
    dispute_round = Column(Integer)
    
    start_date = Column(Date, nullable=False)
    deadline_date = Column(Date, nullable=False)
    days_allowed = Column(Integer, default=30)
    
    status = Column(String(50), default='active')
    completed_at = Column(DateTime)
    
    reminder_sent_7_days = Column(Boolean, default=False)
    reminder_sent_3_days = Column(Boolean, default=False)
    reminder_sent_1_day = Column(Boolean, default=False)
    overdue_notice_sent = Column(Boolean, default=False)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotarizationOrder(Base):
    """Track remote online notarization orders via Proof.com or NotaryLive"""
    __tablename__ = 'notarization_orders'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    provider = Column(String(50), nullable=False)
    external_order_id = Column(String(255))
    external_transaction_id = Column(String(255))
    
    document_type = Column(String(100))
    document_name = Column(String(255))
    document_path = Column(String(500))
    
    signer_email = Column(String(255))
    signer_name = Column(String(255))
    
    session_link = Column(String(500))
    
    status = Column(String(50), default='pending')
    
    notarized_document_path = Column(String(500))
    audit_trail_path = Column(String(500))
    video_recording_path = Column(String(500))
    
    notarized_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    cost = Column(Float)
    
    webhook_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FreezeLetterBatch(Base):
    """Track bulk freeze letter generation batches"""
    __tablename__ = 'freeze_letter_batches'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    batch_uuid = Column(String(36), unique=True, index=True)
    
    bureaus_included = Column(JSON)
    total_bureaus = Column(Integer, default=12)
    
    generated_pdf_path = Column(String(500))
    generated_docx_path = Column(String(500))
    
    mail_method = Column(String(50))
    certified_mail_tracking = Column(JSON)
    
    status = Column(String(50), default='generated')
    mailed_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CertifiedMailOrder(Base):
    """Track certified mail orders via SendCertifiedMail.com"""
    __tablename__ = 'certified_mail_orders'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    external_order_id = Column(String(255))
    tracking_number = Column(String(100))
    
    recipient_name = Column(String(255))
    recipient_address = Column(Text)
    recipient_type = Column(String(50))
    
    document_type = Column(String(100))
    document_path = Column(String(500))
    
    letter_type = Column(String(50))
    dispute_round = Column(Integer)
    bureau = Column(String(50))
    
    status = Column(String(50), default='pending')
    
    cost = Column(Float)
    
    submitted_at = Column(DateTime)
    mailed_at = Column(DateTime)
    delivered_at = Column(DateTime)
    delivery_proof_path = Column(String(500))
    
    webhook_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SettlementEstimate(Base):
    """Store settlement calculations for cases"""
    __tablename__ = 'settlement_estimates'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    
    total_violations = Column(Integer, default=0)
    willful_violations = Column(Integer, default=0)
    negligent_violations = Column(Integer, default=0)
    
    statutory_damages_low = Column(Float, default=0)
    statutory_damages_high = Column(Float, default=0)
    
    actual_damages = Column(Float, default=0)
    actual_damages_breakdown = Column(JSON)
    
    punitive_multiplier = Column(Float, default=1.0)
    punitive_damages_low = Column(Float, default=0)
    punitive_damages_high = Column(Float, default=0)
    
    attorney_fees_estimate = Column(Float, default=0)
    
    total_low = Column(Float, default=0)
    total_high = Column(Float, default=0)
    
    settlement_likelihood = Column(String(50))
    recommended_demand = Column(Float)
    
    calculation_notes = Column(Text)
    calculation_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AttorneyReferral(Base):
    """Track attorney referrals for high-value cases"""
    __tablename__ = 'attorney_referrals'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    
    attorney_name = Column(String(255))
    attorney_firm = Column(String(255))
    attorney_email = Column(String(255))
    attorney_phone = Column(String(50))
    
    referral_reason = Column(Text)
    case_summary = Column(Text)
    estimated_value = Column(Float)
    
    status = Column(String(50), default='pending')
    
    referred_at = Column(DateTime)
    attorney_response_at = Column(DateTime)
    attorney_accepted = Column(Boolean)
    
    fee_arrangement = Column(String(100))
    referral_fee_percent = Column(Float)
    
    outcome = Column(Text)
    settlement_amount = Column(Float)
    referral_fee_received = Column(Float)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LimitedPOA(Base):
    """Track Limited Power of Attorney documents for clients"""
    __tablename__ = 'limited_poa'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    poa_type = Column(String(100), default='credit_dispute')
    
    document_path = Column(String(500))
    
    signed = Column(Boolean, default=False)
    signed_at = Column(DateTime)
    signature_method = Column(String(50))
    
    notarized = Column(Boolean, default=False)
    notarized_at = Column(DateTime)
    notarization_order_id = Column(Integer, ForeignKey('notarization_orders.id'), nullable=True)
    notarized_document_path = Column(String(500))
    
    effective_date = Column(Date)
    expiration_date = Column(Date)
    
    scope = Column(JSON)
    
    revoked = Column(Boolean, default=False)
    revoked_at = Column(DateTime)
    revocation_reason = Column(Text)
    
    status = Column(String(50), default='draft')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Metro2DisputeLog(Base):
    """Track Metro2 format violations detected during analysis"""
    __tablename__ = 'metro2_dispute_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    
    tradeline_identifier = Column(String(255))
    creditor_name = Column(String(255))
    account_number_masked = Column(String(50))
    
    violation_type = Column(String(100))
    violation_description = Column(Text)
    fcra_section = Column(String(50))
    severity = Column(String(20))
    
    evidence = Column(JSON)
    dispute_language = Column(Text)
    
    damage_estimate_low = Column(Integer, default=0)
    damage_estimate_high = Column(Integer, default=0)
    
    disputed = Column(Boolean, default=False)
    disputed_at = Column(DateTime)
    dispute_round = Column(Integer)
    
    resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime)
    resolution_type = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CRAResponseOCR(Base):
    """Store OCR extraction results from CRA response documents"""
    __tablename__ = 'cra_response_ocr'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    upload_id = Column(Integer, ForeignKey('client_uploads.id'), nullable=True)
    
    bureau = Column(String(50))
    document_type = Column(String(100))
    
    document_date = Column(Date)
    response_date = Column(Date)
    
    raw_text = Column(Text)
    structured_data = Column(JSON)
    
    items_verified = Column(JSON)
    items_deleted = Column(JSON)
    items_updated = Column(JSON)
    items_reinvestigated = Column(JSON)
    
    new_violations_detected = Column(JSON)
    
    reinvestigation_complete = Column(Boolean, default=False)
    frivolous_claim = Column(Boolean, default=False)
    
    ocr_confidence = Column(Float)
    extraction_method = Column(String(50), default='claude_vision')
    
    processed_at = Column(DateTime, default=datetime.utcnow)
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ESignatureRequest(Base):
    """Track e-signature requests for client agreements"""
    __tablename__ = 'esignature_requests'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    provider = Column(String(50))
    external_request_id = Column(String(255))
    
    document_type = Column(String(100))
    document_name = Column(String(255))
    document_path = Column(String(500))
    
    signer_email = Column(String(255))
    signer_name = Column(String(255))
    
    signing_link = Column(String(500))
    
    status = Column(String(50), default='pending')
    
    signed_at = Column(DateTime)
    signed_document_path = Column(String(500))
    
    expires_at = Column(DateTime)
    
    webhook_data = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocumentTemplate(Base):
    """CROA and other document templates for e-signature system"""
    __tablename__ = 'document_templates'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, nullable=False, index=True)  # e.g., "CROA_01_RIGHTS_DISCLOSURE"
    name = Column(String(255), nullable=False)  # Human-readable name
    description = Column(Text)  # Description of the document

    content_html = Column(Text, nullable=False)  # HTML content of the document

    must_sign_before_contract = Column(Boolean, default=False)  # CROA requirement
    is_croa_required = Column(Boolean, default=True)  # Part of CROA compliance
    signing_order = Column(Integer, default=0)  # Order in signing flow

    effective_date = Column(Date)  # When this version became effective
    version = Column(String(20), default='1.0')
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClientDocumentSignature(Base):
    """Track client signatures on document templates"""
    __tablename__ = 'client_document_signatures'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    document_template_id = Column(Integer, ForeignKey('document_templates.id'), nullable=False, index=True)

    signature_data = Column(Text)  # Base64 signature image or typed name
    signature_type = Column(String(50), default='typed')  # 'typed', 'drawn', 'uploaded'

    ip_address = Column(String(50))  # IP address at time of signing
    user_agent = Column(Text)  # Browser/device info

    signed_at = Column(DateTime, default=datetime.utcnow)
    signed_document_path = Column(String(500))  # Path to signed PDF

    created_at = Column(DateTime, default=datetime.utcnow)


class CROAProgress(Base):
    """Track client progress through CROA document signing workflow"""
    __tablename__ = 'croa_progress'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, unique=True, index=True)

    # Document signing timestamps (in order)
    rights_disclosure_signed_at = Column(DateTime)  # CROA_01 - MUST sign first
    lpoa_signed_at = Column(DateTime)  # CROA_02 - Limited Power of Attorney
    service_agreement_signed_at = Column(DateTime)  # CROA_03 - Main contract
    cancellation_notice_signed_at = Column(DateTime)  # CROA_04 - Right to cancel
    service_completion_signed_at = Column(DateTime)  # CROA_05 - Auth to begin work
    hipaa_signed_at = Column(DateTime)  # CROA_06 - Health info (optional)
    welcome_packet_signed_at = Column(DateTime)  # CROA_07 - Welcome info

    # Cancellation period tracking
    cancellation_period_starts_at = Column(DateTime)  # When contract was signed
    cancellation_period_ends_at = Column(DateTime)  # 3 business days after contract
    cancellation_waived = Column(Boolean, default=False)  # If client waived waiting period
    cancelled_at = Column(DateTime)  # If client cancelled during period

    # Overall progress
    current_document = Column(String(50), default='CROA_01_RIGHTS_DISCLOSURE')
    documents_completed = Column(Integer, default=0)
    total_documents = Column(Integer, default=7)
    is_complete = Column(Boolean, default=False)
    completed_at = Column(DateTime)

    # Metadata
    last_activity_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CaseTriage(Base):
    """AI-powered case triage for priority scoring and queue assignment"""
    __tablename__ = 'case_triage'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    
    priority_score = Column(Integer, default=3)
    estimated_value = Column(Float, default=0)
    complexity_level = Column(String(50), default='moderate')
    recommended_queue = Column(String(50), default='standard')
    
    key_violations = Column(JSON)
    risk_factors = Column(JSON)
    strengths = Column(JSON)
    
    triage_summary = Column(Text)
    ai_confidence = Column(Float, default=0.5)
    
    reviewed = Column(Boolean, default=False)
    reviewed_by = Column(String(100))
    reviewed_at = Column(DateTime)
    final_priority = Column(Integer)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditScoreSnapshot(Base):
    """Track credit scores over time for improvement analytics"""
    __tablename__ = 'credit_score_snapshots'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    equifax_score = Column(Integer)
    experian_score = Column(Integer)
    transunion_score = Column(Integer)
    average_score = Column(Integer)
    
    equifax_negatives = Column(Integer, default=0)
    experian_negatives = Column(Integer, default=0)
    transunion_negatives = Column(Integer, default=0)
    total_negatives = Column(Integer, default=0)
    
    equifax_removed = Column(Integer, default=0)
    experian_removed = Column(Integer, default=0)
    transunion_removed = Column(Integer, default=0)
    total_removed = Column(Integer, default=0)
    
    milestone = Column(String(100))
    dispute_round = Column(Integer, default=0)
    
    snapshot_type = Column(String(50), default='manual')
    
    notes = Column(Text)
    
    source = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditScoreProjection(Base):
    """Store projected score improvements based on negative removal"""
    __tablename__ = 'credit_score_projections'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    
    current_average = Column(Integer)
    projected_score = Column(Integer)
    potential_gain = Column(Integer)
    
    negatives_to_remove = Column(Integer)
    estimated_points_per_negative = Column(Integer, default=15)
    
    confidence_level = Column(String(20), default='medium')
    
    projection_details = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CFPBComplaint(Base):
    """Track CFPB complaints filed against CRAs and furnishers"""
    __tablename__ = 'cfpb_complaints'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    
    target_company = Column(String(255), nullable=False)
    target_type = Column(String(50), nullable=False)
    
    product_type = Column(String(100), nullable=False)
    issue_type = Column(String(100), nullable=False)
    sub_issue_type = Column(String(100))
    
    narrative = Column(Text)
    desired_resolution = Column(Text)
    
    status = Column(String(50), default='draft')
    cfpb_complaint_id = Column(String(100))
    
    submitted_at = Column(DateTime)
    response_received_at = Column(DateTime)
    company_response = Column(Text)
    
    file_path = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Furnisher(Base):
    """Track creditors/furnishers that report to credit bureaus for strategic intelligence"""
    __tablename__ = 'furnishers'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    alternate_names = Column(JSON)
    industry = Column(String(100))
    parent_company = Column(String(255))
    address = Column(Text)
    phone = Column(String(50))
    fax = Column(String(50))
    email = Column(String(255))
    website = Column(String(255))
    dispute_address = Column(Text)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    stats = relationship("FurnisherStats", back_populates="furnisher", uselist=False)


class FurnisherStats(Base):
    """Track furnisher behavior patterns across disputes"""
    __tablename__ = 'furnisher_stats'
    
    id = Column(Integer, primary_key=True, index=True)
    furnisher_id = Column(Integer, ForeignKey('furnishers.id'), nullable=False, unique=True)
    
    total_disputes = Column(Integer, default=0)
    
    round_1_verified = Column(Integer, default=0)
    round_1_deleted = Column(Integer, default=0)
    round_1_updated = Column(Integer, default=0)
    
    round_2_verified = Column(Integer, default=0)
    round_2_deleted = Column(Integer, default=0)
    round_2_updated = Column(Integer, default=0)
    
    round_3_verified = Column(Integer, default=0)
    round_3_deleted = Column(Integer, default=0)
    round_3_updated = Column(Integer, default=0)
    
    mov_requests_sent = Column(Integer, default=0)
    mov_provided = Column(Integer, default=0)
    mov_failed = Column(Integer, default=0)
    
    avg_response_days = Column(Float, default=0)
    
    settlement_count = Column(Integer, default=0)
    settlement_total = Column(Float, default=0)
    settlement_avg = Column(Float, default=0)
    
    violation_count = Column(Integer, default=0)
    reinsertion_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    furnisher = relationship("Furnisher", back_populates="stats")


class EscalationRecommendation(Base):
    """AI-powered escalation recommendations for dispute strategy"""
    __tablename__ = 'escalation_recommendations'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    
    dispute_round = Column(Integer, default=1)
    bureau = Column(String(50))
    creditor_name = Column(String(255))
    current_status = Column(String(50))
    
    recommended_action = Column(String(100), nullable=False)
    confidence_score = Column(Float, default=0.5)
    reasoning = Column(Text)
    
    supporting_factors = Column(JSON)
    alternative_actions = Column(JSON)
    
    expected_outcome = Column(String(100))
    success_probability = Column(Float, default=0.5)
    
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime)
    outcome_actual = Column(String(100))
    outcome_recorded_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'analysis_id': self.analysis_id,
            'dispute_round': self.dispute_round,
            'bureau': self.bureau,
            'creditor_name': self.creditor_name,
            'current_status': self.current_status,
            'recommended_action': self.recommended_action,
            'confidence_score': self.confidence_score,
            'reasoning': self.reasoning,
            'supporting_factors': self.supporting_factors or {},
            'alternative_actions': self.alternative_actions or [],
            'expected_outcome': self.expected_outcome,
            'success_probability': self.success_probability,
            'applied': self.applied,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'outcome_actual': self.outcome_actual,
            'outcome_recorded_at': self.outcome_recorded_at.isoformat() if self.outcome_recorded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CaseLawCitation(Base):
    """FCRA case law citations for legal reference and letter insertion"""
    __tablename__ = 'case_law_citations'
    
    id = Column(Integer, primary_key=True, index=True)
    case_name = Column(String(500), nullable=False, index=True)
    citation = Column(String(255), nullable=False)
    court = Column(String(100))
    year = Column(Integer, index=True)
    fcra_sections = Column(JSON)
    violation_types = Column(JSON)
    key_holding = Column(Text)
    full_summary = Column(Text)
    quote_snippets = Column(JSON)
    damages_awarded = Column(Float, nullable=True)
    plaintiff_won = Column(Boolean, nullable=True)
    relevance_score = Column(Integer, default=3)
    tags = Column(JSON)
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'case_name': self.case_name,
            'citation': self.citation,
            'court': self.court,
            'year': self.year,
            'fcra_sections': self.fcra_sections or [],
            'violation_types': self.violation_types or [],
            'key_holding': self.key_holding,
            'full_summary': self.full_summary,
            'quote_snippets': self.quote_snippets or [],
            'damages_awarded': self.damages_awarded,
            'plaintiff_won': self.plaintiff_won,
            'relevance_score': self.relevance_score,
            'tags': self.tags or [],
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def format_citation(self, format_type='short'):
        """Format citation for letter insertion"""
        if format_type == 'short':
            return f"{self.case_name}, {self.citation}"
        elif format_type == 'full':
            return f"{self.case_name}, {self.citation} ({self.court}, {self.year})"
        elif format_type == 'with_holding':
            return f"{self.case_name}, {self.citation} (\"{self.key_holding}\")"
        return f"{self.case_name}, {self.citation}"


# ============================================================
# PHASE 7: EXTERNAL INTEGRATIONS
# ============================================================

class IntegrationConnection(Base):
    """Store API credentials and connection status for external services"""
    __tablename__ = 'integration_connections'
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255))
    api_key_encrypted = Column(Text)
    api_secret_encrypted = Column(Text)
    webhook_secret_encrypted = Column(Text)
    base_url = Column(String(500))
    is_active = Column(Boolean, default=False)
    is_sandbox = Column(Boolean, default=True)
    last_connected_at = Column(DateTime)
    last_error = Column(Text)
    connection_status = Column(String(50), default='not_configured')
    config_json = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IntegrationEvent(Base):
    """Audit logging for all integration actions"""
    __tablename__ = 'integration_events'
    
    id = Column(Integer, primary_key=True, index=True)
    integration_id = Column(Integer, ForeignKey('integration_connections.id'), nullable=False)
    event_type = Column(String(100))
    event_data = Column(JSON)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    request_id = Column(String(100))
    response_status = Column(Integer)
    error_message = Column(Text)
    cost_cents = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class CertifiedMailingRecord(Base):
    """Track SendCertified mailings"""
    __tablename__ = 'certified_mailing_records'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    dispute_id = Column(Integer, ForeignKey('dispute_letters.id'), nullable=True)
    external_label_id = Column(String(255))
    tracking_number = Column(String(100))
    recipient_name = Column(String(255))
    recipient_address = Column(Text)
    document_type = Column(String(100))
    mail_class = Column(String(50), default='certified')
    status = Column(String(50), default='pending')
    cost_cents = Column(Integer, default=0)
    mailed_at = Column(DateTime)
    delivered_at = Column(DateTime)
    return_receipt_path = Column(String(500))
    signature_name = Column(String(255))
    tracking_history = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class NotarizeTransaction(Base):
    """Track Notarize.com transactions"""
    __tablename__ = 'notarize_transactions'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    document_id = Column(Integer, ForeignKey('client_documents.id'), nullable=True)
    external_transaction_id = Column(String(255))
    transaction_type = Column(String(100))
    status = Column(String(50), default='created')
    access_link = Column(Text)
    signer_email = Column(String(255))
    signer_name = Column(String(255))
    document_name = Column(String(500))
    original_document_path = Column(String(500))
    notarized_document_path = Column(String(500))
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
    cost_cents = Column(Integer, default=0)
    webhook_events = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CreditPullRequest(Base):
    """Track credit report pull requests"""
    __tablename__ = 'credit_pull_requests'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    provider = Column(String(100))
    external_request_id = Column(String(255))
    status = Column(String(50), default='pending')
    bureaus_requested = Column(JSON)
    report_type = Column(String(50), default='tri-merge')
    score_experian = Column(Integer, nullable=True)
    score_equifax = Column(Integer, nullable=True)
    score_transunion = Column(Integer, nullable=True)
    raw_response_path = Column(String(500))
    parsed_data = Column(JSON)
    cost_cents = Column(Integer, default=0)
    pulled_at = Column(DateTime)
    error_message = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


CREDIT_MONITORING_SERVICES = [
    'IdentityIQ.com',
    'MyScoreIQ.com',
    'SmartCredit.com',
    'MyFreeScoreNow.com',
    'HighScoreNow.com',
    'IdentityClub.com',
    'PrivacyGuard.com',
    'IDClub.com',
    'MyThreeScores.com',
    'MyScore750.com',
    'CreditHeroScore.com',
]


class CreditMonitoringCredential(Base):
    """Store encrypted credentials for credit monitoring service auto-import"""
    __tablename__ = 'credit_monitoring_credentials'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    service_name = Column(String(100), nullable=False)
    username = Column(String(255), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    ssn_last4_encrypted = Column(Text, nullable=True)  # Last 4 of SSN or security word
    is_active = Column(Boolean, default=True)
    last_import_at = Column(DateTime, nullable=True)
    last_import_status = Column(String(50), default='pending')
    last_import_error = Column(Text, nullable=True)
    last_report_path = Column(Text, nullable=True)  # Path to last imported report
    import_frequency = Column(String(50), default='manual')
    next_scheduled_import = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship('Client', backref='credit_monitoring_credentials')
    
    def to_dict(self):
        """Return dictionary representation (excluding sensitive data)"""
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None,
            'service_name': self.service_name,
            'username': self.username,
            'has_ssn_last4': bool(self.ssn_last4_encrypted),
            'is_active': self.is_active,
            'last_import_at': self.last_import_at.isoformat() if self.last_import_at else None,
            'last_import_status': self.last_import_status,
            'last_import_error': self.last_import_error,
            'last_report_path': self.last_report_path,
            'import_frequency': self.import_frequency,
            'next_scheduled_import': self.next_scheduled_import.isoformat() if self.next_scheduled_import else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class BillingPlan(Base):
    """Define subscription plans"""
    __tablename__ = 'billing_plans'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    display_name = Column(String(255))
    stripe_product_id = Column(String(255))
    stripe_price_id = Column(String(255))
    price_cents = Column(Integer)
    billing_interval = Column(String(50))
    features = Column(JSON)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ClientSubscription(Base):
    """Track client billing subscriptions"""
    __tablename__ = 'client_subscriptions'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), unique=True, nullable=False)
    plan_id = Column(Integer, ForeignKey('billing_plans.id'), nullable=True)
    stripe_subscription_id = Column(String(255))
    stripe_customer_id = Column(String(255))
    status = Column(String(50), default='pending')
    current_period_start = Column(DateTime)
    current_period_end = Column(DateTime)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)
    amount_paid_cents = Column(Integer, default=0)
    next_payment_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BackgroundTask(Base):
    """Background task queue for async job processing"""
    __tablename__ = 'background_tasks'
    
    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(100), nullable=False, index=True)
    payload = Column(JSON)
    status = Column(String(50), default='pending', index=True)
    priority = Column(Integer, default=5, index=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    created_by_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_type': self.task_type,
            'payload': self.payload,
            'status': self.status,
            'priority': self.priority,
            'scheduled_at': self.scheduled_at.isoformat() if self.scheduled_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
            'error_message': self.error_message,
            'retries': self.retries,
            'max_retries': self.max_retries,
            'client_id': self.client_id,
            'created_by_staff_id': self.created_by_staff_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ScheduledJob(Base):
    """Scheduled jobs with cron expressions for recurring tasks"""
    __tablename__ = 'scheduled_jobs'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    task_type = Column(String(100), nullable=False)
    payload = Column(JSON, default={})
    cron_expression = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    last_run = Column(DateTime, nullable=True)
    next_run = Column(DateTime, nullable=True, index=True)
    run_count = Column(Integer, default=0)
    last_status = Column(String(50), nullable=True)
    last_error = Column(Text, nullable=True)
    created_by_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'task_type': self.task_type,
            'payload': self.payload,
            'cron_expression': self.cron_expression,
            'is_active': self.is_active,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'run_count': self.run_count,
            'last_status': self.last_status,
            'last_error': self.last_error,
            'created_by_staff_id': self.created_by_staff_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CaseOutcome(Base):
    """ML Learning - Track completed case outcomes for prediction training"""
    __tablename__ = 'case_outcomes'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    case_type = Column(String(100), index=True)
    violation_types = Column(JSON)
    furnisher_id = Column(Integer, ForeignKey('furnishers.id'), nullable=True, index=True)
    initial_score = Column(Float, default=0)
    final_outcome = Column(String(50), nullable=False, index=True)
    settlement_amount = Column(Float, default=0)
    actual_damages = Column(Float, default=0)
    time_to_resolution_days = Column(Integer, default=0)
    attorney_id = Column(Integer, ForeignKey('staff.id'), nullable=True, index=True)
    key_factors = Column(JSON)
    dispute_rounds_completed = Column(Integer, default=0)
    bureaus_involved = Column(JSON)
    violation_count = Column(Integer, default=0)
    willfulness_score = Column(Float, default=0)
    documentation_quality = Column(Float, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'case_type': self.case_type,
            'violation_types': self.violation_types or [],
            'furnisher_id': self.furnisher_id,
            'initial_score': self.initial_score,
            'final_outcome': self.final_outcome,
            'settlement_amount': self.settlement_amount,
            'actual_damages': self.actual_damages,
            'time_to_resolution_days': self.time_to_resolution_days,
            'attorney_id': self.attorney_id,
            'key_factors': self.key_factors or {},
            'dispute_rounds_completed': self.dispute_rounds_completed,
            'bureaus_involved': self.bureaus_involved or [],
            'violation_count': self.violation_count,
            'willfulness_score': self.willfulness_score,
            'documentation_quality': self.documentation_quality,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class OutcomePrediction(Base):
    """ML Learning - Store predictions and compare with actual outcomes"""
    __tablename__ = 'outcome_predictions'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    prediction_type = Column(String(100), nullable=False, index=True)
    predicted_value = Column(Text)
    confidence_score = Column(Float, default=0.5)
    features_used = Column(JSON)
    actual_value = Column(Text, nullable=True)
    prediction_error = Column(Float, nullable=True)
    model_version = Column(String(50), default='v1.0')
    was_accurate = Column(Boolean, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'prediction_type': self.prediction_type,
            'predicted_value': self.predicted_value,
            'confidence_score': self.confidence_score,
            'features_used': self.features_used or {},
            'actual_value': self.actual_value,
            'prediction_error': self.prediction_error,
            'model_version': self.model_version,
            'was_accurate': self.was_accurate,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }


class FurnisherPattern(Base):
    """ML Learning - Track furnisher behavior patterns for strategic insights"""
    __tablename__ = 'furnisher_patterns'
    
    id = Column(Integer, primary_key=True, index=True)
    furnisher_id = Column(Integer, ForeignKey('furnishers.id'), nullable=True, index=True)
    furnisher_name = Column(String(255), index=True)
    pattern_type = Column(String(100), nullable=False, index=True)
    pattern_data = Column(JSON)
    sample_size = Column(Integer, default=0)
    confidence = Column(Float, default=0.5)
    insight_text = Column(Text)
    actionable_recommendation = Column(Text)
    
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'furnisher_id': self.furnisher_id,
            'furnisher_name': self.furnisher_name,
            'pattern_type': self.pattern_type,
            'pattern_data': self.pattern_data or {},
            'sample_size': self.sample_size,
            'confidence': self.confidence,
            'insight_text': self.insight_text,
            'actionable_recommendation': self.actionable_recommendation,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class RevenueForecast(Base):
    """Revenue forecasting for predictive analytics"""
    __tablename__ = 'revenue_forecasts'
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(Date, nullable=False, index=True)
    forecast_period = Column(String(50), nullable=False)
    predicted_revenue = Column(Float, default=0)
    actual_revenue = Column(Float, nullable=True)
    variance = Column(Float, nullable=True)
    confidence_interval_low = Column(Float, default=0)
    confidence_interval_high = Column(Float, default=0)
    factors = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'forecast_date': self.forecast_date.isoformat() if self.forecast_date else None,
            'forecast_period': self.forecast_period,
            'predicted_revenue': self.predicted_revenue,
            'actual_revenue': self.actual_revenue,
            'variance': self.variance,
            'confidence_interval_low': self.confidence_interval_low,
            'confidence_interval_high': self.confidence_interval_high,
            'factors': self.factors or {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ClientLifetimeValue(Base):
    """Client lifetime value estimation for predictive analytics"""
    __tablename__ = 'client_lifetime_values'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    ltv_estimate = Column(Float, default=0)
    probability_of_success = Column(Float, default=0.5)
    expected_settlement = Column(Float, default=0)
    expected_fees = Column(Float, default=0)
    acquisition_cost = Column(Float, default=0)
    churn_risk = Column(Float, default=0.5)
    risk_factors = Column(JSON)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'ltv_estimate': self.ltv_estimate,
            'probability_of_success': self.probability_of_success,
            'expected_settlement': self.expected_settlement,
            'expected_fees': self.expected_fees,
            'acquisition_cost': self.acquisition_cost,
            'churn_risk': self.churn_risk,
            'risk_factors': self.risk_factors or {},
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }


class AttorneyPerformance(Base):
    """Attorney/staff performance metrics for predictive analytics"""
    __tablename__ = 'attorney_performance'
    
    id = Column(Integer, primary_key=True, index=True)
    staff_user_id = Column(Integer, ForeignKey('staff.id'), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    cases_handled = Column(Integer, default=0)
    cases_won = Column(Integer, default=0)
    cases_lost = Column(Integer, default=0)
    cases_settled = Column(Integer, default=0)
    cases_pending = Column(Integer, default=0)
    total_settlements = Column(Float, default=0)
    avg_settlement_amount = Column(Float, default=0)
    avg_resolution_days = Column(Float, default=0)
    client_satisfaction = Column(Float, default=0)
    efficiency_score = Column(Float, default=0)
    strengths = Column(JSON)
    
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'staff_user_id': self.staff_user_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'cases_handled': self.cases_handled,
            'cases_won': self.cases_won,
            'cases_lost': self.cases_lost,
            'cases_settled': self.cases_settled,
            'cases_pending': self.cases_pending,
            'total_settlements': self.total_settlements,
            'avg_settlement_amount': self.avg_settlement_amount,
            'avg_resolution_days': self.avg_resolution_days,
            'client_satisfaction': self.client_satisfaction,
            'efficiency_score': self.efficiency_score,
            'strengths': self.strengths or [],
            'calculated_at': self.calculated_at.isoformat() if self.calculated_at else None
        }


class WorkflowTrigger(Base):
    """Automated workflow triggers for case events"""
    __tablename__ = 'workflow_triggers'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    trigger_type = Column(String(50), nullable=False, index=True)
    conditions = Column(JSON)
    actions = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=5)
    last_triggered = Column(DateTime)
    trigger_count = Column(Integer, default=0)
    created_by_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'trigger_type': self.trigger_type,
            'conditions': self.conditions or {},
            'actions': self.actions or [],
            'is_active': self.is_active,
            'priority': self.priority,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'trigger_count': self.trigger_count,
            'created_by_staff_id': self.created_by_staff_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class WorkflowExecution(Base):
    """Execution history for workflow triggers"""
    __tablename__ = 'workflow_executions'
    
    id = Column(Integer, primary_key=True, index=True)
    trigger_id = Column(Integer, ForeignKey('workflow_triggers.id'), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True, index=True)
    trigger_event = Column(JSON)
    actions_executed = Column(JSON)
    status = Column(String(50), default='pending', index=True)
    error_message = Column(Text)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'trigger_id': self.trigger_id,
            'client_id': self.client_id,
            'trigger_event': self.trigger_event or {},
            'actions_executed': self.actions_executed or [],
            'status': self.status,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WhiteLabelTenant(Base):
    """White-label tenant for partner law firms"""
    __tablename__ = 'white_label_tenants'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True, index=True)
    
    logo_url = Column(String(500))
    favicon_url = Column(String(500))
    primary_color = Column(String(7), default='#319795')
    secondary_color = Column(String(7), default='#1a1a2e')
    accent_color = Column(String(7), default='#84cc16')
    
    company_name = Column(String(255))
    company_address = Column(Text)
    company_phone = Column(String(50))
    company_email = Column(String(255))
    support_email = Column(String(255))
    
    terms_url = Column(String(500))
    privacy_url = Column(String(500))
    
    custom_css = Column(Text)
    custom_js = Column(Text)
    
    is_active = Column(Boolean, default=True, index=True)
    subscription_tier = Column(String(50), default='basic')
    max_users = Column(Integer, default=5)
    max_clients = Column(Integer, default=100)
    features_enabled = Column(JSON, default=dict)
    
    api_key = Column(String(100), unique=True, index=True)
    webhook_url = Column(String(500))

    # Partner portal authentication
    admin_email = Column(String(255), unique=True, index=True)
    admin_password_hash = Column(String(255))
    last_login = Column(DateTime)
    password_reset_token = Column(String(100), unique=True, index=True)
    password_reset_expires = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    users = relationship("TenantUser", back_populates="tenant", cascade="all, delete-orphan")
    clients = relationship("TenantClient", back_populates="tenant", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'domain': self.domain,
            'logo_url': self.logo_url,
            'favicon_url': self.favicon_url,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'company_name': self.company_name,
            'company_address': self.company_address,
            'company_phone': self.company_phone,
            'company_email': self.company_email,
            'support_email': self.support_email,
            'terms_url': self.terms_url,
            'privacy_url': self.privacy_url,
            'custom_css': self.custom_css,
            'custom_js': self.custom_js,
            'is_active': self.is_active,
            'subscription_tier': self.subscription_tier,
            'max_users': self.max_users,
            'max_clients': self.max_clients,
            'features_enabled': self.features_enabled or {},
            'api_key': self.api_key,
            'webhook_url': self.webhook_url,
            'admin_email': self.admin_email,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_branding_config(self):
        """Return CSS variables and branding configuration"""
        return {
            'primary_color': self.primary_color or '#319795',
            'secondary_color': self.secondary_color or '#1a1a2e',
            'accent_color': self.accent_color or '#84cc16',
            'logo_url': self.logo_url,
            'favicon_url': self.favicon_url,
            'company_name': self.company_name or self.name,
            'company_address': self.company_address,
            'company_phone': self.company_phone,
            'company_email': self.company_email,
            'support_email': self.support_email or self.company_email,
            'terms_url': self.terms_url,
            'privacy_url': self.privacy_url,
            'custom_css': self.custom_css,
            'custom_js': self.custom_js
        }


class TenantUser(Base):
    """Staff/user assignment to a tenant"""
    __tablename__ = 'tenant_users'
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('white_label_tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey('staff.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(50), default='user')
    is_primary_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("WhiteLabelTenant", back_populates="users")
    staff = relationship("Staff")
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'staff_id': self.staff_id,
            'role': self.role,
            'is_primary_admin': self.is_primary_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'staff': {
                'id': self.staff.id,
                'email': self.staff.email,
                'full_name': self.staff.full_name,
                'role': self.staff.role
            } if self.staff else None
        }


class TenantClient(Base):
    """Client assignment to a tenant"""
    __tablename__ = 'tenant_clients'
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('white_label_tenants.id', ondelete='CASCADE'), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    tenant = relationship("WhiteLabelTenant", back_populates="clients")
    client = relationship("Client")
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'client_id': self.client_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'client': {
                'id': self.client.id,
                'name': self.client.name,
                'email': self.client.email,
                'status': self.client.status
            } if self.client else None
        }


# ============================================================
# FRANCHISE MODE SYSTEM - Multi-Office Management
# ============================================================

FRANCHISE_ORG_TYPES = {
    'headquarters': {
        'name': 'Headquarters',
        'description': 'Main corporate office with full oversight',
        'level': 0
    },
    'regional': {
        'name': 'Regional Office',
        'description': 'Regional management office overseeing branches',
        'level': 1
    },
    'branch': {
        'name': 'Branch Office',
        'description': 'Local branch office',
        'level': 2
    }
}

FRANCHISE_MEMBER_ROLES = {
    'owner': {
        'name': 'Owner',
        'description': 'Full ownership and control of the organization',
        'permissions': ['*']
    },
    'manager': {
        'name': 'Manager',
        'description': 'Manages organization operations and staff',
        'permissions': ['view_org', 'edit_org', 'manage_members', 'manage_clients', 'view_revenue', 'approve_transfers']
    },
    'staff': {
        'name': 'Staff',
        'description': 'Standard staff member',
        'permissions': ['view_org', 'view_clients', 'manage_assigned_clients']
    }
}


class FranchiseOrganization(Base):
    """Franchise organization for multi-office law firm management"""
    __tablename__ = 'franchise_organizations'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    parent_org_id = Column(Integer, ForeignKey('franchise_organizations.id'), nullable=True, index=True)
    org_type = Column(String(50), default='branch', index=True)
    
    address = Column(String(500))
    city = Column(String(100))
    state = Column(String(50))
    zip_code = Column(String(20))
    phone = Column(String(50))
    email = Column(String(255))
    contact_name = Column(String(255))
    
    license_number = Column(String(100))
    max_users = Column(Integer, default=10)
    max_clients = Column(Integer, default=100)
    subscription_tier = Column(String(50), default='basic')
    billing_contact_email = Column(String(255))
    
    manager_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    settings = Column(JSON, default=dict)
    revenue_share_percent = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    parent = relationship("FranchiseOrganization", remote_side=[id], backref="children")
    manager = relationship("Staff", foreign_keys=[manager_staff_id])
    members = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")
    clients = relationship("OrganizationClient", back_populates="organization", cascade="all, delete-orphan")
    
    def to_dict(self, include_children=False):
        result = {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'parent_org_id': self.parent_org_id,
            'org_type': self.org_type,
            'org_type_name': FRANCHISE_ORG_TYPES.get(self.org_type, {}).get('name', self.org_type),
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'full_address': f"{self.address}, {self.city}, {self.state} {self.zip_code}" if self.address else None,
            'phone': self.phone,
            'email': self.email,
            'contact_name': self.contact_name,
            'license_number': self.license_number,
            'max_users': self.max_users,
            'max_clients': self.max_clients,
            'subscription_tier': self.subscription_tier,
            'billing_contact_email': self.billing_contact_email,
            'manager_staff_id': self.manager_staff_id,
            'manager_name': self.manager.full_name if self.manager else None,
            'is_active': self.is_active,
            'settings': self.settings or {},
            'revenue_share_percent': self.revenue_share_percent,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_children and self.children:
            result['children'] = [child.to_dict(include_children=True) for child in self.children]
        return result
    
    def get_full_hierarchy_path(self):
        """Get full path from root to this organization"""
        path = [self]
        current = self
        while current.parent:
            path.insert(0, current.parent)
            current = current.parent
        return path


class OrganizationMembership(Base):
    """Staff membership in a franchise organization"""
    __tablename__ = 'organization_memberships'
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('franchise_organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey('staff.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(50), default='staff', index=True)
    permissions = Column(JSON, default=list)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("FranchiseOrganization", back_populates="members")
    staff = relationship("Staff")
    
    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'organization_name': self.organization.name if self.organization else None,
            'staff_id': self.staff_id,
            'staff_name': self.staff.full_name if self.staff else None,
            'staff_email': self.staff.email if self.staff else None,
            'role': self.role,
            'role_name': FRANCHISE_MEMBER_ROLES.get(self.role, {}).get('name', self.role),
            'permissions': self.permissions or [],
            'is_primary': self.is_primary,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def has_permission(self, permission):
        """Check if member has a specific permission"""
        role_config = FRANCHISE_MEMBER_ROLES.get(self.role, {})
        role_perms = role_config.get('permissions', [])
        if '*' in role_perms:
            return True
        custom_perms = self.permissions or []
        return permission in role_perms or permission in custom_perms


class OrganizationClient(Base):
    """Client assignment to a franchise organization"""
    __tablename__ = 'organization_clients'
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('franchise_organizations.id', ondelete='CASCADE'), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    assigned_by_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("FranchiseOrganization", back_populates="clients")
    client = relationship("Client")
    assigned_by = relationship("Staff")
    
    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'organization_name': self.organization.name if self.organization else None,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None,
            'client_email': self.client.email if self.client else None,
            'client_status': self.client.status if self.client else None,
            'assigned_by_staff_id': self.assigned_by_staff_id,
            'assigned_by_name': self.assigned_by.full_name if self.assigned_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class InterOrgTransfer(Base):
    """Client transfer between franchise organizations"""
    __tablename__ = 'inter_org_transfers'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    from_org_id = Column(Integer, ForeignKey('franchise_organizations.id'), nullable=False, index=True)
    to_org_id = Column(Integer, ForeignKey('franchise_organizations.id'), nullable=False, index=True)
    transfer_type = Column(String(50), default='referral', index=True)
    reason = Column(Text)
    transferred_by_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=False)
    approved_by_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    status = Column(String(50), default='pending', index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    client = relationship("Client")
    from_org = relationship("FranchiseOrganization", foreign_keys=[from_org_id])
    to_org = relationship("FranchiseOrganization", foreign_keys=[to_org_id])
    transferred_by = relationship("Staff", foreign_keys=[transferred_by_staff_id])
    approved_by = relationship("Staff", foreign_keys=[approved_by_staff_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None,
            'from_org_id': self.from_org_id,
            'from_org_name': self.from_org.name if self.from_org else None,
            'to_org_id': self.to_org_id,
            'to_org_name': self.to_org.name if self.to_org else None,
            'transfer_type': self.transfer_type,
            'reason': self.reason,
            'transferred_by_staff_id': self.transferred_by_staff_id,
            'transferred_by_name': self.transferred_by.full_name if self.transferred_by else None,
            'approved_by_staff_id': self.approved_by_staff_id,
            'approved_by_name': self.approved_by.full_name if self.approved_by else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


# ============================================================
# WHITE-LABEL CONFIG - Partner Law Firm Branding System
# ============================================================

FONT_FAMILIES = {
    'inter': "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    'roboto': "'Roboto', Arial, sans-serif",
    'open-sans': "'Open Sans', Arial, sans-serif",
    'lato': "'Lato', Arial, sans-serif",
    'poppins': "'Poppins', Arial, sans-serif",
    'montserrat': "'Montserrat', Arial, sans-serif",
    'source-sans': "'Source Sans Pro', Arial, sans-serif",
    'nunito': "'Nunito', Arial, sans-serif",
    'raleway': "'Raleway', Arial, sans-serif",
    'system': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"
}


class WhiteLabelConfig(Base):
    """White-label configuration for partner law firms/organizations"""
    __tablename__ = 'white_label_configs'
    
    id = Column(Integer, primary_key=True, index=True)
    organization_id = Column(Integer, ForeignKey('franchise_organizations.id', ondelete='SET NULL'), nullable=True, index=True)
    organization_name = Column(String(255), nullable=False)
    
    subdomain = Column(String(100), unique=True, nullable=False, index=True)
    custom_domain = Column(String(255), unique=True, nullable=True, index=True)
    
    logo_url = Column(String(500))
    favicon_url = Column(String(500))
    
    primary_color = Column(String(7), default='#319795')
    secondary_color = Column(String(7), default='#1a1a2e')
    accent_color = Column(String(7), default='#84cc16')
    header_bg_color = Column(String(7), default='#1a1a2e')
    sidebar_bg_color = Column(String(7), default='#1a1a2e')
    
    font_family = Column(String(50), default='inter')
    custom_css = Column(Text)
    
    email_from_name = Column(String(255))
    email_from_address = Column(String(255))
    email_from_address_encrypted = Column(Text)
    
    company_address = Column(Text)
    company_phone = Column(String(50))
    company_email = Column(String(255))
    
    footer_text = Column(Text)
    terms_url = Column(String(500))
    privacy_url = Column(String(500))
    
    is_active = Column(Boolean, default=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("FranchiseOrganization", foreign_keys=[organization_id])
    
    def to_dict(self):
        return {
            'id': self.id,
            'organization_id': self.organization_id,
            'organization_name': self.organization_name,
            'subdomain': self.subdomain,
            'custom_domain': self.custom_domain,
            'logo_url': self.logo_url,
            'favicon_url': self.favicon_url,
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'header_bg_color': self.header_bg_color,
            'sidebar_bg_color': self.sidebar_bg_color,
            'font_family': self.font_family,
            'custom_css': self.custom_css,
            'email_from_name': self.email_from_name,
            'email_from_address': self.email_from_address,
            'company_address': self.company_address,
            'company_phone': self.company_phone,
            'company_email': self.company_email,
            'footer_text': self.footer_text,
            'terms_url': self.terms_url,
            'privacy_url': self.privacy_url,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_branding_dict(self):
        """Return branding configuration for templates"""
        font_css = FONT_FAMILIES.get(self.font_family, FONT_FAMILIES['inter'])
        return {
            'organization_name': self.organization_name,
            'subdomain': self.subdomain,
            'custom_domain': self.custom_domain,
            'logo_url': self.logo_url or '/static/images/logo.png',
            'favicon_url': self.favicon_url,
            'primary_color': self.primary_color or '#319795',
            'secondary_color': self.secondary_color or '#1a1a2e',
            'accent_color': self.accent_color or '#84cc16',
            'header_bg_color': self.header_bg_color or '#1a1a2e',
            'sidebar_bg_color': self.sidebar_bg_color or '#1a1a2e',
            'font_family': font_css,
            'font_family_key': self.font_family or 'inter',
            'custom_css': self.custom_css,
            'email_from_name': self.email_from_name,
            'email_from_address': self.email_from_address,
            'company_address': self.company_address,
            'company_phone': self.company_phone,
            'company_email': self.company_email,
            'footer_text': self.footer_text,
            'terms_url': self.terms_url,
            'privacy_url': self.privacy_url,
            'is_active': self.is_active
        }


API_SCOPES = {
    'read:clients': 'Read client information',
    'write:clients': 'Create and update clients',
    'read:cases': 'Read case information',
    'write:cases': 'Create and update cases',
    'read:disputes': 'Read dispute information',
    'write:disputes': 'Create and manage disputes',
    'analyze:reports': 'Submit credit reports for analysis',
    'manage:webhooks': 'Create and manage webhooks'
}


class APIKey(Base):
    """API keys for third-party integrations"""
    __tablename__ = 'api_keys'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, index=True)
    key_prefix = Column(String(8), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey('white_label_tenants.id', ondelete='SET NULL'), nullable=True, index=True)
    organization_id = Column(Integer, nullable=True, index=True)
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=False, index=True)
    scopes = Column(JSON, default=[])
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_day = Column(Integer, default=10000)
    is_active = Column(Boolean, default=True, index=True)
    last_used_at = Column(DateTime)
    last_used_ip = Column(String(45))
    usage_count = Column(Integer, default=0)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("WhiteLabelTenant")
    staff = relationship("Staff")
    requests = relationship("APIRequest", back_populates="api_key", cascade="all, delete-orphan")
    
    def to_dict(self, include_prefix=True):
        return {
            'id': self.id,
            'name': self.name,
            'key_prefix': self.key_prefix if include_prefix else '********',
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant.name if self.tenant else None,
            'organization_id': self.organization_id,
            'staff_id': self.staff_id,
            'staff_name': self.staff.full_name if self.staff else None,
            'scopes': self.scopes or [],
            'rate_limit_per_minute': self.rate_limit_per_minute,
            'rate_limit_per_day': self.rate_limit_per_day,
            'is_active': self.is_active,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'last_used_ip': self.last_used_ip,
            'usage_count': self.usage_count or 0,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def has_scope(self, scope):
        """Check if API key has a specific scope"""
        if not self.scopes:
            return False
        if '*' in self.scopes:
            return True
        return scope in self.scopes
    
    def has_any_scope(self, scopes):
        """Check if API key has any of the given scopes"""
        return any(self.has_scope(s) for s in scopes)


class APIRequest(Base):
    """Log of API requests for analytics and rate limiting"""
    __tablename__ = 'api_requests'
    
    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey('api_keys.id', ondelete='CASCADE'), nullable=False, index=True)
    endpoint = Column(String(500), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    request_ip = Column(String(45), index=True)
    request_headers = Column(JSON)
    request_body = Column(JSON)
    response_status = Column(Integer, index=True)
    response_time_ms = Column(Integer)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    api_key = relationship("APIKey", back_populates="requests")
    
    def to_dict(self):
        return {
            'id': self.id,
            'api_key_id': self.api_key_id,
            'endpoint': self.endpoint,
            'method': self.method,
            'request_ip': self.request_ip,
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class APIWebhook(Base):
    """Webhooks for event notifications"""
    __tablename__ = 'api_webhooks'
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey('white_label_tenants.id', ondelete='SET NULL'), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(100), nullable=False)
    events = Column(JSON, default=[])
    is_active = Column(Boolean, default=True, index=True)
    last_triggered = Column(DateTime)
    failure_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tenant = relationship("WhiteLabelTenant")
    
    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant.name if self.tenant else None,
            'name': self.name,
            'url': self.url,
            'events': self.events or [],
            'is_active': self.is_active,
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'failure_count': self.failure_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


WEBHOOK_EVENTS = [
    'client.created',
    'client.updated',
    'case.created',
    'case.status_changed',
    'dispute.created',
    'dispute.status_changed',
    'analysis.completed',
    'document.generated',
    'settlement.updated'
]


AUDIT_EVENT_TYPES = [
    'login', 'logout', 'login_failed',
    'create', 'read', 'update', 'delete',
    'export', 'import', 'api_call',
    'document_upload', 'document_download', 'document_view',
    'credit_report_access', 'phi_access',
    'settings_change', 'permission_change',
    'password_change', 'password_reset',
    'session_start', 'session_end'
]

AUDIT_RESOURCE_TYPES = [
    'client', 'dispute', 'document', 'case', 'staff', 'settings',
    'credit_report', 'analysis', 'settlement', 'letter',
    'cra_response', 'violation', 'affiliate', 'commission',
    'api_key', 'webhook', 'tenant', 'organization'
]

AUDIT_SEVERITY_LEVELS = ['info', 'warning', 'critical']


class AuditLog(Base):
    """Comprehensive audit log for SOC 2 and HIPAA compliance"""
    __tablename__ = 'audit_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    event_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(100), index=True)
    
    user_id = Column(Integer, index=True)
    user_type = Column(String(20), nullable=False, index=True)
    user_email = Column(String(255))
    user_name = Column(String(255))
    
    user_ip = Column(String(45), index=True)
    user_agent = Column(Text)
    
    action = Column(String(255), nullable=False)
    details = Column(JSON)
    
    old_values = Column(JSON)
    new_values = Column(JSON)
    
    severity = Column(String(20), default='info', index=True)
    
    session_id = Column(String(100), index=True)
    request_id = Column(String(100), index=True)
    
    duration_ms = Column(Integer)
    
    endpoint = Column(String(500))
    http_method = Column(String(10))
    http_status = Column(Integer)
    
    organization_id = Column(Integer, index=True)
    tenant_id = Column(Integer, index=True)
    
    is_phi_access = Column(Boolean, default=False, index=True)
    phi_fields_accessed = Column(JSON)
    
    compliance_flags = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'event_type': self.event_type,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'user_id': self.user_id,
            'user_type': self.user_type,
            'user_email': self.user_email,
            'user_name': self.user_name,
            'user_ip': self.user_ip,
            'user_agent': self.user_agent,
            'action': self.action,
            'details': self.details,
            'old_values': self.old_values,
            'new_values': self.new_values,
            'severity': self.severity,
            'session_id': self.session_id,
            'request_id': self.request_id,
            'duration_ms': self.duration_ms,
            'endpoint': self.endpoint,
            'http_method': self.http_method,
            'http_status': self.http_status,
            'organization_id': self.organization_id,
            'tenant_id': self.tenant_id,
            'is_phi_access': self.is_phi_access,
            'phi_fields_accessed': self.phi_fields_accessed,
            'compliance_flags': self.compliance_flags,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_severity_for_event(cls, event_type):
        """Determine severity level based on event type"""
        critical_events = ['login_failed', 'permission_change', 'password_reset', 'settings_change', 'delete']
        warning_events = ['export', 'phi_access', 'credit_report_access', 'password_change']
        
        if event_type in critical_events:
            return 'critical'
        elif event_type in warning_events:
            return 'warning'
        return 'info'


SUBSCRIPTION_TIERS = {
    'basic': {
        'name': 'Basic',
        'max_users': 5,
        'max_clients': 100,
        'features': ['branding', 'client_portal']
    },
    'professional': {
        'name': 'Professional',
        'max_users': 20,
        'max_clients': 500,
        'features': ['branding', 'client_portal', 'api_access', 'custom_domain']
    },
    'enterprise': {
        'name': 'Enterprise',
        'max_users': 100,
        'max_clients': 5000,
        'features': ['branding', 'client_portal', 'api_access', 'custom_domain', 'webhooks', 'white_label_emails', 'custom_css_js']
    }
}


class PerformanceMetric(Base):
    """Track aggregated performance metrics per endpoint"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(500), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    
    avg_response_time_ms = Column(Float, default=0)
    p50_time = Column(Float, default=0)
    p95_time = Column(Float, default=0)
    p99_time = Column(Float, default=0)
    min_response_time_ms = Column(Float, default=0)
    max_response_time_ms = Column(Float, default=0)
    
    request_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    cache_hit_count = Column(Integer, default=0)
    cache_hit_rate = Column(Float, default=0)
    
    period_start = Column(DateTime, nullable=False, index=True)
    period_end = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'endpoint': self.endpoint,
            'method': self.method,
            'avg_response_time_ms': self.avg_response_time_ms,
            'p50_time': self.p50_time,
            'p95_time': self.p95_time,
            'p99_time': self.p99_time,
            'min_response_time_ms': self.min_response_time_ms,
            'max_response_time_ms': self.max_response_time_ms,
            'request_count': self.request_count,
            'error_count': self.error_count,
            'cache_hit_count': self.cache_hit_count,
            'cache_hit_rate': self.cache_hit_rate,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CacheEntry(Base):
    """Track persistent cache entries for analysis"""
    __tablename__ = 'cache_entries'
    
    id = Column(Integer, primary_key=True, index=True)
    cache_key = Column(String(255), nullable=False, unique=True, index=True)
    cache_value = Column(JSON)
    
    ttl_seconds = Column(Integer, default=300)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, index=True)
    last_accessed = Column(DateTime)
    hit_count = Column(Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'cache_key': self.cache_key,
            'ttl_seconds': self.ttl_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'hit_count': self.hit_count,
            'is_expired': self.expires_at and datetime.utcnow() > self.expires_at if self.expires_at else False
        }
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at


class KnowledgeContent(Base):
    """Training content from Credit Repair and Metro 2® courses"""
    __tablename__ = 'knowledge_content'
    
    id = Column(Integer, primary_key=True, index=True)
    course = Column(String(100), nullable=False, index=True)
    section_number = Column(Integer, nullable=False)
    section_title = Column(String(500), nullable=False)
    subsection = Column(String(100))
    content = Column(Text, nullable=False)
    content_type = Column(String(50), default='article')
    tags = Column(JSON)
    statute_references = Column(JSON)
    metro2_codes = Column(JSON)
    search_keywords = Column(Text)
    difficulty_level = Column(String(20), default='intermediate')
    estimated_read_time = Column(Integer)
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'course': self.course,
            'section_number': self.section_number,
            'section_title': self.section_title,
            'subsection': self.subsection,
            'content': self.content,
            'content_type': self.content_type,
            'tags': self.tags or [],
            'statute_references': self.statute_references or [],
            'metro2_codes': self.metro2_codes or [],
            'difficulty_level': self.difficulty_level,
            'estimated_read_time': self.estimated_read_time,
            'display_order': self.display_order
        }


class Metro2Code(Base):
    """Metro 2® code lookup tables for violations and reporting"""
    __tablename__ = 'metro2_codes'
    
    id = Column(Integer, primary_key=True, index=True)
    code_type = Column(String(50), nullable=False, index=True)
    code = Column(String(20), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    usage_guidance = Column(Text)
    common_violations = Column(JSON)
    dispute_language = Column(Text)
    fcra_reference = Column(String(100))
    crrg_reference = Column(String(100))
    is_derogatory = Column(Boolean, default=False)
    severity_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code_type': self.code_type,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'usage_guidance': self.usage_guidance,
            'common_violations': self.common_violations or [],
            'dispute_language': self.dispute_language,
            'fcra_reference': self.fcra_reference,
            'crrg_reference': self.crrg_reference,
            'is_derogatory': self.is_derogatory,
            'severity_score': self.severity_score
        }


class SOP(Base):
    """Standard Operating Procedures for credit repair workflows"""
    __tablename__ = 'sops'
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100))
    description = Column(Text)
    content = Column(Text, nullable=False)
    steps = Column(JSON)
    checklist_items = Column(JSON)
    timeline_days = Column(Integer)
    difficulty = Column(String(20), default='standard')
    required_role = Column(String(50), default='paralegal')
    related_statutes = Column(JSON)
    related_templates = Column(JSON)
    tips = Column(JSON)
    warnings = Column(JSON)
    version = Column(String(20), default='1.0')
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_by_id = Column(Integer, ForeignKey('staff.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'category': self.category,
            'subcategory': self.subcategory,
            'description': self.description,
            'content': self.content,
            'steps': self.steps or [],
            'checklist_items': self.checklist_items or [],
            'timeline_days': self.timeline_days,
            'difficulty': self.difficulty,
            'required_role': self.required_role,
            'related_statutes': self.related_statutes or [],
            'related_templates': self.related_templates or [],
            'tips': self.tips or [],
            'warnings': self.warnings or [],
            'version': self.version,
            'display_order': self.display_order
        }


class ChexSystemsDispute(Base):
    """ChexSystems and Early Warning Services dispute tracking"""
    __tablename__ = 'chexsystems_disputes'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    bureau_type = Column(String(50), nullable=False)
    dispute_type = Column(String(100), nullable=False)
    account_type = Column(String(100))
    reported_by = Column(String(255))
    dispute_reason = Column(Text)
    dispute_details = Column(JSON)
    supporting_docs = Column(JSON)
    letter_sent_date = Column(DateTime)
    letter_type = Column(String(100))
    tracking_number = Column(String(100))
    response_due_date = Column(DateTime)
    response_received_date = Column(DateTime)
    response_outcome = Column(String(50))
    response_details = Column(Text)
    status = Column(String(50), default='pending', index=True)
    escalation_level = Column(Integer, default=1)
    next_action = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'bureau_type': self.bureau_type,
            'dispute_type': self.dispute_type,
            'account_type': self.account_type,
            'reported_by': self.reported_by,
            'dispute_reason': self.dispute_reason,
            'dispute_details': self.dispute_details or {},
            'letter_sent_date': self.letter_sent_date.isoformat() if self.letter_sent_date else None,
            'response_due_date': self.response_due_date.isoformat() if self.response_due_date else None,
            'response_received_date': self.response_received_date.isoformat() if self.response_received_date else None,
            'response_outcome': self.response_outcome,
            'status': self.status,
            'escalation_level': self.escalation_level,
            'next_action': self.next_action
        }


# ============================================================
# SPECIALTY BUREAU DISPUTES (All 9 Secondary CRAs)
# ============================================================

SPECIALTY_BUREAUS = [
    'Innovis',
    'ChexSystems', 
    'Clarity Services Inc',
    'LexisNexis',
    'CoreLogic Teletrack',
    'Factor Trust Inc',
    'MicroBilt/PRBC',
    'LexisNexis Risk Solutions',
    'DataX Ltd'
]

SPECIALTY_DISPUTE_TYPES = [
    'inaccurate_info',
    'identity_theft',
    'obsolete_data',
    'not_mine',
    'paid_account',
    'other'
]

SPECIALTY_LETTER_TYPES = [
    'initial_dispute',
    'follow_up',
    'intent_to_sue'
]

SPECIALTY_RESPONSE_OUTCOMES = [
    'deleted',
    'verified',
    'modified',
    'frivolous',
    'pending',
    'no_response'
]

class SpecialtyBureauDispute(Base):
    """Unified dispute tracking for all 9 specialty consumer reporting agencies"""
    __tablename__ = 'specialty_bureau_disputes'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    bureau_name = Column(String(100), nullable=False, index=True)
    dispute_type = Column(String(100), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_number = Column(String(100), nullable=True)
    dispute_reason = Column(Text, nullable=False)
    dispute_details = Column(JSON)
    supporting_docs = Column(JSON)
    letter_sent_date = Column(DateTime)
    letter_type = Column(String(100))
    tracking_number = Column(String(100))
    response_due_date = Column(DateTime)
    response_received_date = Column(DateTime)
    response_outcome = Column(String(50))
    status = Column(String(50), default='pending', index=True)
    escalation_level = Column(Integer, default=1)
    next_action = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'bureau_name': self.bureau_name,
            'dispute_type': self.dispute_type,
            'account_name': self.account_name,
            'account_number': self.account_number,
            'dispute_reason': self.dispute_reason,
            'dispute_details': self.dispute_details or {},
            'supporting_docs': self.supporting_docs or [],
            'letter_sent_date': self.letter_sent_date.isoformat() if self.letter_sent_date else None,
            'letter_type': self.letter_type,
            'tracking_number': self.tracking_number,
            'response_due_date': self.response_due_date.isoformat() if self.response_due_date else None,
            'response_received_date': self.response_received_date.isoformat() if self.response_received_date else None,
            'response_outcome': self.response_outcome,
            'status': self.status,
            'escalation_level': self.escalation_level,
            'next_action': self.next_action,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# ============================================================
# FRIVOLOUSNESS DEFENSE TRACKER
# ============================================================

class FrivolousDefense(Base):
    """Track CRA frivolous claims and defense evidence requirements"""
    __tablename__ = 'frivolous_defenses'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    cra_response_id = Column(Integer, ForeignKey('cra_responses.id'), nullable=True, index=True)
    dispute_item_id = Column(Integer, ForeignKey('dispute_items.id'), nullable=True, index=True)
    
    # Which bureau made the frivolous claim
    bureau = Column(String(50), nullable=False)  # Equifax, Experian, TransUnion
    dispute_round = Column(Integer, default=1)
    
    # Frivolous claim details
    claim_date = Column(Date)  # When CRA claimed frivolous
    claim_reason = Column(Text)  # CRA's stated reason for frivolous determination
    claim_citation = Column(String(255))  # CRA's legal citation if provided
    
    # Required evidence/theory for re-dispute
    required_evidence = Column(JSON)  # List of evidence types needed
    new_legal_theory = Column(Text)  # New legal theory or argument required
    new_facts_required = Column(Text)  # New factual basis needed
    
    # Status tracking
    status = Column(String(50), default='pending')  # pending, evidence_gathering, ready_to_redispute, redisputed, resolved
    defense_strategy = Column(Text)  # Planned strategy for overcoming frivolous claim
    
    # Evidence collected
    evidence_collected = Column(JSON)  # List of evidence documents collected
    evidence_sufficient = Column(Boolean, default=False)
    
    # Re-dispute tracking
    redispute_date = Column(Date)
    redispute_letter_id = Column(Integer, ForeignKey('dispute_letters.id'), nullable=True)
    redispute_outcome = Column(String(50))  # accepted, rejected, deleted, verified
    
    # Follow-up
    follow_up_due = Column(Date)
    escalation_notes = Column(Text)
    
    # Admin notes
    admin_notes = Column(Text)
    assigned_to_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'bureau': self.bureau,
            'dispute_round': self.dispute_round,
            'claim_date': self.claim_date.isoformat() if self.claim_date else None,
            'claim_reason': self.claim_reason,
            'required_evidence': self.required_evidence or [],
            'new_legal_theory': self.new_legal_theory,
            'status': self.status,
            'evidence_collected': self.evidence_collected or [],
            'evidence_sufficient': self.evidence_sufficient,
            'follow_up_due': self.follow_up_due.isoformat() if self.follow_up_due else None,
            'redispute_outcome': self.redispute_outcome
        }


class FrivolousDefenseEvidence(Base):
    """Evidence documents for frivolous defense cases"""
    __tablename__ = 'frivolous_defense_evidence'
    
    id = Column(Integer, primary_key=True, index=True)
    defense_id = Column(Integer, ForeignKey('frivolous_defenses.id'), nullable=False, index=True)
    
    # Evidence details
    evidence_type = Column(String(100))  # id_document, utility_bill, bank_statement, affidavit, etc.
    file_path = Column(String(500))
    file_name = Column(String(255))
    description = Column(Text)
    
    # Verification
    verified = Column(Boolean, default=False)
    verified_by_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    verified_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# SUSPENSE ACCOUNT DETECTION
# ============================================================

class MortgagePaymentLedger(Base):
    """Track mortgage payment history for suspense account detection"""
    __tablename__ = 'mortgage_payment_ledgers'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    
    # Account identification
    creditor_name = Column(String(255), nullable=False)
    account_number_masked = Column(String(100))  # Last 4 digits
    loan_type = Column(String(50))  # conventional, FHA, VA, USDA
    
    # Payment details
    payment_date = Column(Date, nullable=False)
    payment_amount = Column(Float)
    due_date = Column(Date)
    
    # How payment was applied
    applied_to_principal = Column(Float, default=0)
    applied_to_interest = Column(Float, default=0)
    applied_to_escrow = Column(Float, default=0)
    applied_to_fees = Column(Float, default=0)
    held_in_suspense = Column(Float, default=0)
    
    # Suspense flags
    is_suspense = Column(Boolean, default=False)
    suspense_reason = Column(String(255))  # partial_payment, misapplied, escrow_shortage, etc.
    suspense_resolved = Column(Boolean, default=False)
    suspense_resolved_date = Column(Date)
    
    # Reporting impact
    reported_as_late = Column(Boolean, default=False)
    days_late_reported = Column(Integer, default=0)
    actual_days_late = Column(Integer, default=0)  # Calculated based on when full payment received
    
    # Source document
    source_doc_path = Column(String(500))
    source_doc_type = Column(String(50))  # statement, ledger, payment_history
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SuspenseAccountFinding(Base):
    """Identified suspense account issues that may be FCRA violations"""
    __tablename__ = 'suspense_account_findings'
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    ledger_id = Column(Integer, ForeignKey('mortgage_payment_ledgers.id'), nullable=True)
    violation_id = Column(Integer, ForeignKey('violations.id'), nullable=True)
    
    # Finding details
    creditor_name = Column(String(255))
    account_number_masked = Column(String(100))
    
    # Suspense issue
    finding_type = Column(String(100))  # false_late, misapplied_payment, escrow_mishandling, payment_held
    finding_description = Column(Text)
    
    # Payment analysis
    total_suspense_amount = Column(Float, default=0)
    months_affected = Column(Integer, default=0)
    false_lates_count = Column(Integer, default=0)
    
    # Evidence
    evidence_summary = Column(Text)
    payment_timeline = Column(JSON)  # Timeline of payments and suspense activity
    
    # FCRA violation potential
    is_fcra_violation = Column(Boolean, default=False)
    fcra_section = Column(String(50))  # e.g., 1681e(b), 1681s-2(a)
    violation_description = Column(Text)
    estimated_damages = Column(Float, default=0)
    
    # Status
    status = Column(String(50), default='identified')  # identified, disputed, resolved, litigation
    dispute_sent_date = Column(Date)
    resolution_date = Column(Date)
    resolution_outcome = Column(String(100))
    
    # Remediation
    remediation_requested = Column(Boolean, default=False)
    credit_correction_requested = Column(Boolean, default=False)
    damages_claimed = Column(Float)
    
    admin_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'creditor_name': self.creditor_name,
            'finding_type': self.finding_type,
            'finding_description': self.finding_description,
            'total_suspense_amount': self.total_suspense_amount,
            'months_affected': self.months_affected,
            'false_lates_count': self.false_lates_count,
            'is_fcra_violation': self.is_fcra_violation,
            'fcra_section': self.fcra_section,
            'estimated_damages': self.estimated_damages,
            'status': self.status
        }


# ============================================================
# PATTERN DOCUMENTATION (Systemic Violations)
# ============================================================

class ViolationPattern(Base):
    """Track patterns of violations across multiple clients for systemic claims"""
    __tablename__ = 'violation_patterns'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Pattern identification
    pattern_name = Column(String(255), nullable=False)
    pattern_type = Column(String(100))  # furnisher_practice, cra_procedure, industry_wide
    
    # Target entity
    target_type = Column(String(50))  # furnisher, cra, both
    furnisher_name = Column(String(255), index=True)
    cra_name = Column(String(50), index=True)  # Equifax, Experian, TransUnion
    
    # Violation pattern details
    violation_code = Column(String(50))  # FCRA section
    violation_type = Column(String(255))
    violation_description = Column(Text)
    
    # Pattern metrics
    occurrences_count = Column(Integer, default=0)
    clients_affected = Column(Integer, default=0)
    total_damages_estimate = Column(Float, default=0)
    avg_damages_per_client = Column(Float, default=0)
    
    # Date range
    earliest_occurrence = Column(Date)
    latest_occurrence = Column(Date)
    
    # Evidence packaging
    evidence_packet_path = Column(String(500))  # PDF evidence packet
    evidence_summary = Column(Text)
    evidence_strength = Column(String(50))  # weak, moderate, strong, compelling
    
    # Legal strategy
    recommended_strategy = Column(String(100))  # class_action, individual_suits, regulatory_complaint
    strategy_notes = Column(Text)
    case_law_citations = Column(JSON)  # Relevant case citations
    
    # Status
    status = Column(String(50), default='monitoring')  # monitoring, documenting, ready_for_action, active_litigation
    priority = Column(String(20), default='medium')  # low, medium, high, critical
    
    # Actions taken
    cfpb_complaint_filed = Column(Boolean, default=False)
    cfpb_complaint_date = Column(Date)
    cfpb_complaint_id = Column(String(100))
    litigation_filed = Column(Boolean, default=False)
    litigation_date = Column(Date)
    litigation_case_number = Column(String(100))
    
    admin_notes = Column(Text)
    created_by_staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'pattern_name': self.pattern_name,
            'pattern_type': self.pattern_type,
            'target_type': self.target_type,
            'furnisher_name': self.furnisher_name,
            'cra_name': self.cra_name,
            'violation_code': self.violation_code,
            'violation_type': self.violation_type,
            'occurrences_count': self.occurrences_count,
            'clients_affected': self.clients_affected,
            'total_damages_estimate': self.total_damages_estimate,
            'evidence_strength': self.evidence_strength,
            'recommended_strategy': self.recommended_strategy,
            'status': self.status,
            'priority': self.priority
        }


class PatternInstance(Base):
    """Link individual violations to pattern groups"""
    __tablename__ = 'pattern_instances'
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(Integer, ForeignKey('violation_patterns.id'), nullable=False, index=True)
    violation_id = Column(Integer, ForeignKey('violations.id'), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    
    # Instance details
    occurrence_date = Column(Date)
    instance_description = Column(Text)
    damages_for_instance = Column(Float, default=0)
    
    # Evidence
    evidence_docs = Column(JSON)  # List of document paths
    evidence_notes = Column(Text)
    
    # Status
    included_in_packet = Column(Boolean, default=False)
    included_date = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class AutomationMetrics(Base):
    """Track automation metrics and costs per client"""
    __tablename__ = 'automation_metrics'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)

    # Letter counts by round
    round_0_letters = Column(Integer, default=0)
    round_1_letters = Column(Integer, default=0)
    round_2_letters = Column(Integer, default=0)
    round_3_letters = Column(Integer, default=0)
    round_4_letters = Column(Integer, default=0)
    total_letters = Column(Integer, default=0)

    # Cost tracking (in cents)
    mail_cost_cents = Column(Integer, default=0)
    ai_cost_cents = Column(Integer, default=0)
    total_cost_cents = Column(Integer, default=0)

    # Time tracking
    intake_to_analysis_minutes = Column(Integer, default=0)
    total_va_minutes = Column(Integer, default=0)

    # Dispute outcomes
    items_disputed = Column(Integer, default=0)
    items_deleted = Column(Integer, default=0)
    items_verified = Column(Integer, default=0)
    reinsertion_count = Column(Integer, default=0)

    # Resolution
    resolved_round = Column(Integer, nullable=True)
    final_status = Column(String(50), nullable=True)
    settlement_amount_cents = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LetterBatch(Base):
    """Track SFTP batch uploads to SendCertifiedMail.com"""
    __tablename__ = 'letter_batches'

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(100), unique=True, nullable=False, index=True)

    # Batch details
    letter_count = Column(Integer, nullable=False)
    cost_cents = Column(Integer, nullable=False)

    # Status tracking
    status = Column(String(50), default='uploaded')  # uploaded/processing/complete/failed
    uploaded_at = Column(DateTime, nullable=False)
    tracking_received_at = Column(DateTime, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class TradelineStatus(Base):
    """Track tradeline status across all three credit bureaus"""
    __tablename__ = 'tradeline_statuses'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)

    # Account identification
    account_name = Column(String(255), nullable=False)
    account_number_masked = Column(String(50), nullable=True)
    account_type = Column(String(50), nullable=True)

    # Status per bureau
    equifax_status = Column(String(50), default='not_disputed')
    experian_status = Column(String(50), default='not_disputed')
    transunion_status = Column(String(50), default='not_disputed')

    # Dispute tracking
    first_disputed_round = Column(Integer, nullable=True)
    deleted_round = Column(Integer, nullable=True)
    reinserted_round = Column(Integer, nullable=True)

    # Current overall status
    current_status = Column(String(50), default='active')  # active/disputed/deleted/reinserted

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BookingSlot(Base):
    """Available time slots for Q&A calls - created by staff"""
    __tablename__ = 'booking_slots'

    id = Column(Integer, primary_key=True, index=True)

    # Slot timing
    slot_date = Column(Date, nullable=False, index=True)
    slot_time = Column(Time, nullable=False)  # Start time
    duration_minutes = Column(Integer, default=15)  # Fixed 15-min slots

    # Availability
    is_available = Column(Boolean, default=True)  # Staff can disable slots
    is_booked = Column(Boolean, default=False)

    # Staff who created/owns this slot
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    booking = relationship("Booking", back_populates="slot", uselist=False)


class Booking(Base):
    """Client bookings for Q&A calls"""
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True, index=True)

    # Link to slot and client
    slot_id = Column(Integer, ForeignKey('booking_slots.id'), nullable=False, unique=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)

    # Booking details
    booking_type = Column(String(50), default='qa_call')  # qa_call, consultation, etc.
    notes = Column(Text, nullable=True)  # Client's questions/notes

    # Status tracking
    status = Column(String(20), default='confirmed')  # confirmed, cancelled, completed, no_show

    # Confirmation tracking
    confirmation_sent = Column(Boolean, default=False)
    confirmation_sent_at = Column(DateTime, nullable=True)
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)

    # Timestamps
    booked_at = Column(DateTime, default=datetime.utcnow)
    cancelled_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    slot = relationship("BookingSlot", back_populates="booking")
    client = relationship("Client", backref="bookings")


class ClientMessage(Base):
    """Messages between clients and staff for live support"""
    __tablename__ = 'client_messages'

    id = Column(Integer, primary_key=True, index=True)

    # Conversation participants
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, index=True)
    staff_id = Column(Integer, ForeignKey('staff.id'), nullable=True, index=True)  # Null for client messages

    # Message content
    message = Column(Text, nullable=False)
    sender_type = Column(String(20), nullable=False)  # 'client' or 'staff'

    # Status tracking
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", backref="messages")
    staff = relationship("Staff", backref="client_messages")


class OnboardingProgress(Base):
    """Track client onboarding wizard progress"""
    __tablename__ = 'onboarding_progress'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False, unique=True, index=True)

    # Step completion status
    personal_info_completed = Column(Boolean, default=False)
    personal_info_completed_at = Column(DateTime, nullable=True)

    id_documents_completed = Column(Boolean, default=False)
    id_documents_completed_at = Column(DateTime, nullable=True)

    ssn_card_completed = Column(Boolean, default=False)
    ssn_card_completed_at = Column(DateTime, nullable=True)

    proof_of_address_completed = Column(Boolean, default=False)
    proof_of_address_completed_at = Column(DateTime, nullable=True)

    credit_monitoring_completed = Column(Boolean, default=False)
    credit_monitoring_completed_at = Column(DateTime, nullable=True)

    agreement_completed = Column(Boolean, default=False)
    agreement_completed_at = Column(DateTime, nullable=True)

    payment_completed = Column(Boolean, default=False)
    payment_completed_at = Column(DateTime, nullable=True)

    # Overall progress
    current_step = Column(String(50), default='personal_info')
    completion_percentage = Column(Integer, default=0)
    is_complete = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    client = relationship("Client", backref="onboarding_progress")


def init_db():
    """Initialize database tables and run schema migrations"""
    Base.metadata.create_all(bind=engine)
    
    migrate_columns = [
        ("staff", "id", "SERIAL PRIMARY KEY"),
        ("staff", "email", "VARCHAR(255) UNIQUE NOT NULL"),
        ("staff", "password_hash", "VARCHAR(255) NOT NULL"),
        ("staff", "first_name", "VARCHAR(100)"),
        ("staff", "last_name", "VARCHAR(100)"),
        ("staff", "role", "VARCHAR(50) DEFAULT 'viewer'"),
        ("staff", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("staff", "last_login", "TIMESTAMP"),
        ("staff", "password_reset_token", "VARCHAR(100)"),
        ("staff", "password_reset_expires", "TIMESTAMP"),
        ("staff", "force_password_change", "BOOLEAN DEFAULT FALSE"),
        ("staff", "created_by_id", "INTEGER REFERENCES staff(id)"),
        ("staff", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("staff", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("clients", "first_name", "VARCHAR(100)"),
        ("clients", "last_name", "VARCHAR(100)"),
        ("clients", "address_street", "VARCHAR(255)"),
        ("clients", "address_city", "VARCHAR(100)"),
        ("clients", "address_state", "VARCHAR(50)"),
        ("clients", "address_zip", "VARCHAR(20)"),
        ("clients", "date_of_birth", "DATE"),
        ("clients", "ssn_last_four", "VARCHAR(4)"),
        ("clients", "credit_monitoring_service", "VARCHAR(100)"),
        ("clients", "credit_monitoring_username", "VARCHAR(255)"),
        ("clients", "credit_monitoring_password_encrypted", "TEXT"),
        ("clients", "current_dispute_round", "INTEGER DEFAULT 0"),
        ("clients", "current_dispute_step", "VARCHAR(100)"),
        ("clients", "dispute_status", "VARCHAR(50) DEFAULT 'new'"),
        ("clients", "round_started_at", "TIMESTAMP"),
        ("clients", "last_bureau_response_at", "TIMESTAMP"),
        ("clients", "legacy_system_id", "VARCHAR(100)"),
        ("clients", "legacy_case_number", "VARCHAR(100)"),
        ("clients", "imported_at", "TIMESTAMP"),
        ("clients", "import_notes", "TEXT"),
        ("clients", "referred_by_client_id", "INTEGER"),
        ("clients", "referral_code", "VARCHAR(50)"),
        ("clients", "portal_token", "VARCHAR(100)"),
        ("clients", "portal_password_hash", "VARCHAR(255)"),
        ("clients", "status", "VARCHAR(50) DEFAULT 'signup'"),
        ("clients", "signup_completed", "BOOLEAN DEFAULT FALSE"),
        ("clients", "agreement_signed", "BOOLEAN DEFAULT FALSE"),
        ("clients", "agreement_signed_at", "TIMESTAMP"),
        ("clients", "cmm_contact_id", "VARCHAR(100)"),
        ("clients", "admin_notes", "TEXT"),
        ("clients", "signup_plan", "VARCHAR(50)"),
        ("clients", "signup_amount", "INTEGER"),
        ("clients", "stripe_customer_id", "VARCHAR(255)"),
        ("clients", "stripe_checkout_session_id", "VARCHAR(255)"),
        ("clients", "stripe_payment_intent_id", "VARCHAR(255)"),
        ("clients", "payment_status", "VARCHAR(50) DEFAULT 'pending'"),
        ("clients", "payment_received_at", "TIMESTAMP"),
        ("clients", "client_type", "VARCHAR(1) DEFAULT 'L'"),
        ("clients", "status_2", "VARCHAR(100)"),
        ("clients", "company", "VARCHAR(255)"),
        ("clients", "phone_2", "VARCHAR(50)"),
        ("clients", "mobile", "VARCHAR(50)"),
        ("clients", "website", "VARCHAR(255)"),
        ("clients", "is_affiliate", "BOOLEAN DEFAULT FALSE"),
        ("clients", "follow_up_date", "DATE"),
        ("clients", "groups", "VARCHAR(500)"),
        ("clients", "mark_1", "BOOLEAN DEFAULT FALSE"),
        ("clients", "mark_2", "BOOLEAN DEFAULT FALSE"),
        ("clients", "payment_method", "VARCHAR(50) DEFAULT 'pending'"),
        ("clients", "payment_pending", "BOOLEAN DEFAULT FALSE"),
        ("clients", "avatar_filename", "VARCHAR(255)"),
        ("clients", "referred_by_affiliate_id", "INTEGER"),
        ("violations", "violation_date", "DATE"),
        ("violations", "discovery_date", "DATE"),
        ("violations", "sol_expiration_date", "DATE"),
        ("violations", "sol_warning_sent", "BOOLEAN DEFAULT FALSE"),
        ("affiliates", "id", "SERIAL PRIMARY KEY"),
        ("affiliates", "user_id", "INTEGER"),
        ("affiliates", "name", "VARCHAR(255) NOT NULL"),
        ("affiliates", "email", "VARCHAR(255) UNIQUE NOT NULL"),
        ("affiliates", "phone", "VARCHAR(50)"),
        ("affiliates", "company_name", "VARCHAR(255)"),
        ("affiliates", "affiliate_code", "VARCHAR(50) UNIQUE NOT NULL"),
        ("affiliates", "parent_affiliate_id", "INTEGER"),
        ("affiliates", "commission_rate_1", "FLOAT DEFAULT 0.10"),
        ("affiliates", "commission_rate_2", "FLOAT DEFAULT 0.05"),
        ("affiliates", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("affiliates", "payout_method", "VARCHAR(50)"),
        ("affiliates", "payout_details", "JSON"),
        ("affiliates", "total_referrals", "INTEGER DEFAULT 0"),
        ("affiliates", "total_earnings", "FLOAT DEFAULT 0.0"),
        ("affiliates", "pending_earnings", "FLOAT DEFAULT 0.0"),
        ("affiliates", "paid_out", "FLOAT DEFAULT 0.0"),
        ("affiliates", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("affiliates", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("commissions", "id", "SERIAL PRIMARY KEY"),
        ("commissions", "affiliate_id", "INTEGER NOT NULL"),
        ("commissions", "client_id", "INTEGER NOT NULL"),
        ("commissions", "level", "INTEGER DEFAULT 1"),
        ("commissions", "trigger_type", "VARCHAR(50) NOT NULL"),
        ("commissions", "trigger_amount", "FLOAT DEFAULT 0.0"),
        ("commissions", "commission_rate", "FLOAT DEFAULT 0.0"),
        ("commissions", "commission_amount", "FLOAT DEFAULT 0.0"),
        ("commissions", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("commissions", "paid_at", "TIMESTAMP"),
        ("commissions", "payout_id", "INTEGER"),
        ("commissions", "notes", "TEXT"),
        ("commissions", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("affiliate_payouts", "id", "SERIAL PRIMARY KEY"),
        ("affiliate_payouts", "affiliate_id", "INTEGER NOT NULL REFERENCES affiliates(id)"),
        ("affiliate_payouts", "amount", "FLOAT NOT NULL"),
        ("affiliate_payouts", "payout_method", "VARCHAR(50)"),
        ("affiliate_payouts", "payout_reference", "VARCHAR(255)"),
        ("affiliate_payouts", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("affiliate_payouts", "period_start", "TIMESTAMP"),
        ("affiliate_payouts", "period_end", "TIMESTAMP"),
        ("affiliate_payouts", "commission_ids", "JSON"),
        ("affiliate_payouts", "notes", "TEXT"),
        ("affiliate_payouts", "processed_by_id", "INTEGER REFERENCES staff(id)"),
        ("affiliate_payouts", "processed_at", "TIMESTAMP"),
        ("affiliate_payouts", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("affiliate_payouts", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Affiliate portal authentication columns
        ("affiliates", "password_hash", "VARCHAR(255)"),
        ("affiliates", "last_login", "TIMESTAMP"),
        ("affiliates", "login_count", "INTEGER DEFAULT 0"),
        ("case_triage", "id", "SERIAL PRIMARY KEY"),
        ("case_triage", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("case_triage", "analysis_id", "INTEGER REFERENCES analyses(id)"),
        ("case_triage", "priority_score", "INTEGER DEFAULT 3"),
        ("case_triage", "estimated_value", "FLOAT DEFAULT 0"),
        ("case_triage", "complexity_level", "VARCHAR(50) DEFAULT 'moderate'"),
        ("case_triage", "recommended_queue", "VARCHAR(50) DEFAULT 'standard'"),
        ("case_triage", "key_violations", "JSON"),
        ("case_triage", "risk_factors", "JSON"),
        ("case_triage", "strengths", "JSON"),
        ("case_triage", "triage_summary", "TEXT"),
        ("case_triage", "ai_confidence", "FLOAT DEFAULT 0.5"),
        ("case_triage", "reviewed", "BOOLEAN DEFAULT FALSE"),
        ("case_triage", "reviewed_by", "VARCHAR(100)"),
        ("case_triage", "reviewed_at", "TIMESTAMP"),
        ("case_triage", "final_priority", "INTEGER"),
        ("case_triage", "notes", "TEXT"),
        ("case_triage", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("case_triage", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("case_law_citations", "id", "SERIAL PRIMARY KEY"),
        ("case_law_citations", "case_name", "VARCHAR(500) NOT NULL"),
        ("case_law_citations", "citation", "VARCHAR(255) NOT NULL"),
        ("case_law_citations", "court", "VARCHAR(100)"),
        ("case_law_citations", "year", "INTEGER"),
        ("case_law_citations", "fcra_sections", "JSON"),
        ("case_law_citations", "violation_types", "JSON"),
        ("case_law_citations", "key_holding", "TEXT"),
        ("case_law_citations", "full_summary", "TEXT"),
        ("case_law_citations", "quote_snippets", "JSON"),
        ("case_law_citations", "damages_awarded", "FLOAT"),
        ("case_law_citations", "plaintiff_won", "BOOLEAN"),
        ("case_law_citations", "relevance_score", "INTEGER DEFAULT 3"),
        ("case_law_citations", "tags", "JSON"),
        ("case_law_citations", "notes", "TEXT"),
        ("case_law_citations", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("case_law_citations", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("escalation_recommendations", "id", "SERIAL PRIMARY KEY"),
        ("escalation_recommendations", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("escalation_recommendations", "analysis_id", "INTEGER REFERENCES analyses(id)"),
        ("escalation_recommendations", "dispute_round", "INTEGER DEFAULT 1"),
        ("escalation_recommendations", "bureau", "VARCHAR(50)"),
        ("escalation_recommendations", "creditor_name", "VARCHAR(255)"),
        ("escalation_recommendations", "current_status", "VARCHAR(50)"),
        ("escalation_recommendations", "recommended_action", "VARCHAR(100) NOT NULL"),
        ("escalation_recommendations", "confidence_score", "FLOAT DEFAULT 0.5"),
        ("escalation_recommendations", "reasoning", "TEXT"),
        ("escalation_recommendations", "supporting_factors", "JSON"),
        ("escalation_recommendations", "alternative_actions", "JSON"),
        ("escalation_recommendations", "expected_outcome", "VARCHAR(100)"),
        ("escalation_recommendations", "success_probability", "FLOAT DEFAULT 0.5"),
        ("escalation_recommendations", "applied", "BOOLEAN DEFAULT FALSE"),
        ("escalation_recommendations", "applied_at", "TIMESTAMP"),
        ("escalation_recommendations", "outcome_actual", "VARCHAR(100)"),
        ("escalation_recommendations", "outcome_recorded_at", "TIMESTAMP"),
        ("escalation_recommendations", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("escalation_recommendations", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("integration_connections", "id", "SERIAL PRIMARY KEY"),
        ("integration_connections", "service_name", "VARCHAR(100) UNIQUE NOT NULL"),
        ("integration_connections", "display_name", "VARCHAR(255)"),
        ("integration_connections", "api_key_encrypted", "TEXT"),
        ("integration_connections", "api_secret_encrypted", "TEXT"),
        ("integration_connections", "webhook_secret_encrypted", "TEXT"),
        ("integration_connections", "base_url", "VARCHAR(500)"),
        ("integration_connections", "is_active", "BOOLEAN DEFAULT FALSE"),
        ("integration_connections", "is_sandbox", "BOOLEAN DEFAULT TRUE"),
        ("integration_connections", "last_connected_at", "TIMESTAMP"),
        ("integration_connections", "last_error", "TEXT"),
        ("integration_connections", "connection_status", "VARCHAR(50) DEFAULT 'not_configured'"),
        ("integration_connections", "config_json", "JSON"),
        ("integration_connections", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("integration_connections", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("integration_events", "id", "SERIAL PRIMARY KEY"),
        ("integration_events", "integration_id", "INTEGER NOT NULL REFERENCES integration_connections(id)"),
        ("integration_events", "event_type", "VARCHAR(100)"),
        ("integration_events", "event_data", "JSON"),
        ("integration_events", "client_id", "INTEGER REFERENCES clients(id)"),
        ("integration_events", "request_id", "VARCHAR(100)"),
        ("integration_events", "response_status", "INTEGER"),
        ("integration_events", "error_message", "TEXT"),
        ("integration_events", "cost_cents", "INTEGER DEFAULT 0"),
        ("integration_events", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("certified_mailing_records", "id", "SERIAL PRIMARY KEY"),
        ("certified_mailing_records", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("certified_mailing_records", "dispute_id", "INTEGER REFERENCES dispute_letters(id)"),
        ("certified_mailing_records", "external_label_id", "VARCHAR(255)"),
        ("certified_mailing_records", "tracking_number", "VARCHAR(100)"),
        ("certified_mailing_records", "recipient_name", "VARCHAR(255)"),
        ("certified_mailing_records", "recipient_address", "TEXT"),
        ("certified_mailing_records", "document_type", "VARCHAR(100)"),
        ("certified_mailing_records", "mail_class", "VARCHAR(50) DEFAULT 'certified'"),
        ("certified_mailing_records", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("certified_mailing_records", "cost_cents", "INTEGER DEFAULT 0"),
        ("certified_mailing_records", "mailed_at", "TIMESTAMP"),
        ("certified_mailing_records", "delivered_at", "TIMESTAMP"),
        ("certified_mailing_records", "return_receipt_path", "VARCHAR(500)"),
        ("certified_mailing_records", "signature_name", "VARCHAR(255)"),
        ("certified_mailing_records", "tracking_history", "JSON"),
        ("certified_mailing_records", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("certified_mailing_records", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("notarize_transactions", "id", "SERIAL PRIMARY KEY"),
        ("notarize_transactions", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("notarize_transactions", "document_id", "INTEGER REFERENCES client_documents(id)"),
        ("notarize_transactions", "external_transaction_id", "VARCHAR(255)"),
        ("notarize_transactions", "transaction_type", "VARCHAR(100)"),
        ("notarize_transactions", "status", "VARCHAR(50) DEFAULT 'created'"),
        ("notarize_transactions", "access_link", "TEXT"),
        ("notarize_transactions", "signer_email", "VARCHAR(255)"),
        ("notarize_transactions", "signer_name", "VARCHAR(255)"),
        ("notarize_transactions", "document_name", "VARCHAR(500)"),
        ("notarize_transactions", "original_document_path", "VARCHAR(500)"),
        ("notarize_transactions", "notarized_document_path", "VARCHAR(500)"),
        ("notarize_transactions", "completed_at", "TIMESTAMP"),
        ("notarize_transactions", "expires_at", "TIMESTAMP"),
        ("notarize_transactions", "cost_cents", "INTEGER DEFAULT 0"),
        ("notarize_transactions", "webhook_events", "JSON"),
        ("notarize_transactions", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("notarize_transactions", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("credit_pull_requests", "id", "SERIAL PRIMARY KEY"),
        ("credit_pull_requests", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("credit_pull_requests", "provider", "VARCHAR(100)"),
        ("credit_pull_requests", "external_request_id", "VARCHAR(255)"),
        ("credit_pull_requests", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("credit_pull_requests", "bureaus_requested", "JSON"),
        ("credit_pull_requests", "report_type", "VARCHAR(50) DEFAULT 'tri-merge'"),
        ("credit_pull_requests", "score_experian", "INTEGER"),
        ("credit_pull_requests", "score_equifax", "INTEGER"),
        ("credit_pull_requests", "score_transunion", "INTEGER"),
        ("credit_pull_requests", "raw_response_path", "VARCHAR(500)"),
        ("credit_pull_requests", "parsed_data", "JSON"),
        ("credit_pull_requests", "cost_cents", "INTEGER DEFAULT 0"),
        ("credit_pull_requests", "pulled_at", "TIMESTAMP"),
        ("credit_pull_requests", "error_message", "TEXT"),
        ("credit_pull_requests", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("credit_pull_requests", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("credit_monitoring_credentials", "id", "SERIAL PRIMARY KEY"),
        ("credit_monitoring_credentials", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("credit_monitoring_credentials", "service_name", "VARCHAR(100) NOT NULL"),
        ("credit_monitoring_credentials", "username", "VARCHAR(255) NOT NULL"),
        ("credit_monitoring_credentials", "password_encrypted", "TEXT NOT NULL"),
        ("credit_monitoring_credentials", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("credit_monitoring_credentials", "last_import_at", "TIMESTAMP"),
        ("credit_monitoring_credentials", "last_import_status", "VARCHAR(50) DEFAULT 'pending'"),
        ("credit_monitoring_credentials", "last_import_error", "TEXT"),
        ("credit_monitoring_credentials", "import_frequency", "VARCHAR(50) DEFAULT 'manual'"),
        ("credit_monitoring_credentials", "next_scheduled_import", "TIMESTAMP"),
        ("credit_monitoring_credentials", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("credit_monitoring_credentials", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("billing_plans", "id", "SERIAL PRIMARY KEY"),
        ("billing_plans", "name", "VARCHAR(100)"),
        ("billing_plans", "display_name", "VARCHAR(255)"),
        ("billing_plans", "stripe_product_id", "VARCHAR(255)"),
        ("billing_plans", "stripe_price_id", "VARCHAR(255)"),
        ("billing_plans", "price_cents", "INTEGER"),
        ("billing_plans", "billing_interval", "VARCHAR(50)"),
        ("billing_plans", "features", "JSON"),
        ("billing_plans", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("billing_plans", "sort_order", "INTEGER DEFAULT 0"),
        ("billing_plans", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("billing_plans", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("client_subscriptions", "id", "SERIAL PRIMARY KEY"),
        ("client_subscriptions", "client_id", "INTEGER UNIQUE NOT NULL REFERENCES clients(id)"),
        ("client_subscriptions", "plan_id", "INTEGER REFERENCES billing_plans(id)"),
        ("client_subscriptions", "stripe_subscription_id", "VARCHAR(255)"),
        ("client_subscriptions", "stripe_customer_id", "VARCHAR(255)"),
        ("client_subscriptions", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("client_subscriptions", "current_period_start", "TIMESTAMP"),
        ("client_subscriptions", "current_period_end", "TIMESTAMP"),
        ("client_subscriptions", "cancel_at_period_end", "BOOLEAN DEFAULT FALSE"),
        ("client_subscriptions", "canceled_at", "TIMESTAMP"),
        ("client_subscriptions", "amount_paid_cents", "INTEGER DEFAULT 0"),
        ("client_subscriptions", "next_payment_date", "TIMESTAMP"),
        ("client_subscriptions", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("client_subscriptions", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("background_tasks", "id", "SERIAL PRIMARY KEY"),
        ("background_tasks", "task_type", "VARCHAR(100) NOT NULL"),
        ("background_tasks", "payload", "JSON"),
        ("background_tasks", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("background_tasks", "priority", "INTEGER DEFAULT 5"),
        ("background_tasks", "scheduled_at", "TIMESTAMP"),
        ("background_tasks", "started_at", "TIMESTAMP"),
        ("background_tasks", "completed_at", "TIMESTAMP"),
        ("background_tasks", "result", "JSON"),
        ("background_tasks", "error_message", "TEXT"),
        ("background_tasks", "retries", "INTEGER DEFAULT 0"),
        ("background_tasks", "max_retries", "INTEGER DEFAULT 3"),
        ("background_tasks", "client_id", "INTEGER REFERENCES clients(id)"),
        ("background_tasks", "created_by_staff_id", "INTEGER REFERENCES staff(id)"),
        ("background_tasks", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("background_tasks", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("scheduled_jobs", "id", "SERIAL PRIMARY KEY"),
        ("scheduled_jobs", "name", "VARCHAR(255) UNIQUE NOT NULL"),
        ("scheduled_jobs", "task_type", "VARCHAR(100) NOT NULL"),
        ("scheduled_jobs", "payload", "JSON"),
        ("scheduled_jobs", "cron_expression", "VARCHAR(100) NOT NULL"),
        ("scheduled_jobs", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("scheduled_jobs", "last_run", "TIMESTAMP"),
        ("scheduled_jobs", "next_run", "TIMESTAMP"),
        ("scheduled_jobs", "run_count", "INTEGER DEFAULT 0"),
        ("scheduled_jobs", "last_status", "VARCHAR(50)"),
        ("scheduled_jobs", "last_error", "TEXT"),
        ("scheduled_jobs", "created_by_staff_id", "INTEGER REFERENCES staff(id)"),
        ("scheduled_jobs", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("scheduled_jobs", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("case_outcomes", "id", "SERIAL PRIMARY KEY"),
        ("case_outcomes", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("case_outcomes", "case_type", "VARCHAR(100)"),
        ("case_outcomes", "violation_types", "JSON"),
        ("case_outcomes", "furnisher_id", "INTEGER REFERENCES furnishers(id)"),
        ("case_outcomes", "initial_score", "FLOAT DEFAULT 0"),
        ("case_outcomes", "final_outcome", "VARCHAR(50) NOT NULL"),
        ("case_outcomes", "settlement_amount", "FLOAT DEFAULT 0"),
        ("case_outcomes", "actual_damages", "FLOAT DEFAULT 0"),
        ("case_outcomes", "time_to_resolution_days", "INTEGER DEFAULT 0"),
        ("case_outcomes", "attorney_id", "INTEGER REFERENCES staff(id)"),
        ("case_outcomes", "key_factors", "JSON"),
        ("case_outcomes", "dispute_rounds_completed", "INTEGER DEFAULT 0"),
        ("case_outcomes", "bureaus_involved", "JSON"),
        ("case_outcomes", "violation_count", "INTEGER DEFAULT 0"),
        ("case_outcomes", "willfulness_score", "FLOAT DEFAULT 0"),
        ("case_outcomes", "documentation_quality", "FLOAT DEFAULT 0"),
        ("case_outcomes", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("case_outcomes", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("outcome_predictions", "id", "SERIAL PRIMARY KEY"),
        ("outcome_predictions", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("outcome_predictions", "prediction_type", "VARCHAR(100) NOT NULL"),
        ("outcome_predictions", "predicted_value", "TEXT"),
        ("outcome_predictions", "confidence_score", "FLOAT DEFAULT 0.5"),
        ("outcome_predictions", "features_used", "JSON"),
        ("outcome_predictions", "actual_value", "TEXT"),
        ("outcome_predictions", "prediction_error", "FLOAT"),
        ("outcome_predictions", "model_version", "VARCHAR(50) DEFAULT 'v1.0'"),
        ("outcome_predictions", "was_accurate", "BOOLEAN"),
        ("outcome_predictions", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("outcome_predictions", "resolved_at", "TIMESTAMP"),
        ("furnisher_patterns", "id", "SERIAL PRIMARY KEY"),
        ("furnisher_patterns", "furnisher_id", "INTEGER REFERENCES furnishers(id)"),
        ("furnisher_patterns", "furnisher_name", "VARCHAR(255)"),
        ("furnisher_patterns", "pattern_type", "VARCHAR(100) NOT NULL"),
        ("furnisher_patterns", "pattern_data", "JSON"),
        ("furnisher_patterns", "sample_size", "INTEGER DEFAULT 0"),
        ("furnisher_patterns", "confidence", "FLOAT DEFAULT 0.5"),
        ("furnisher_patterns", "insight_text", "TEXT"),
        ("furnisher_patterns", "actionable_recommendation", "TEXT"),
        ("furnisher_patterns", "last_updated", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("furnisher_patterns", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("revenue_forecasts", "id", "SERIAL PRIMARY KEY"),
        ("revenue_forecasts", "forecast_date", "DATE NOT NULL"),
        ("revenue_forecasts", "forecast_period", "VARCHAR(50) NOT NULL"),
        ("revenue_forecasts", "predicted_revenue", "FLOAT DEFAULT 0"),
        ("revenue_forecasts", "actual_revenue", "FLOAT"),
        ("revenue_forecasts", "variance", "FLOAT"),
        ("revenue_forecasts", "confidence_interval_low", "FLOAT DEFAULT 0"),
        ("revenue_forecasts", "confidence_interval_high", "FLOAT DEFAULT 0"),
        ("revenue_forecasts", "factors", "JSON"),
        ("revenue_forecasts", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("client_lifetime_values", "id", "SERIAL PRIMARY KEY"),
        ("client_lifetime_values", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("client_lifetime_values", "ltv_estimate", "FLOAT DEFAULT 0"),
        ("client_lifetime_values", "probability_of_success", "FLOAT DEFAULT 0.5"),
        ("client_lifetime_values", "expected_settlement", "FLOAT DEFAULT 0"),
        ("client_lifetime_values", "expected_fees", "FLOAT DEFAULT 0"),
        ("client_lifetime_values", "acquisition_cost", "FLOAT DEFAULT 0"),
        ("client_lifetime_values", "churn_risk", "FLOAT DEFAULT 0.5"),
        ("client_lifetime_values", "risk_factors", "JSON"),
        ("client_lifetime_values", "calculated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("attorney_performance", "id", "SERIAL PRIMARY KEY"),
        ("attorney_performance", "staff_user_id", "INTEGER NOT NULL REFERENCES staff(id)"),
        ("attorney_performance", "period_start", "DATE NOT NULL"),
        ("attorney_performance", "period_end", "DATE NOT NULL"),
        ("attorney_performance", "cases_handled", "INTEGER DEFAULT 0"),
        ("attorney_performance", "cases_won", "INTEGER DEFAULT 0"),
        ("attorney_performance", "cases_lost", "INTEGER DEFAULT 0"),
        ("attorney_performance", "cases_settled", "INTEGER DEFAULT 0"),
        ("attorney_performance", "cases_pending", "INTEGER DEFAULT 0"),
        ("attorney_performance", "total_settlements", "FLOAT DEFAULT 0"),
        ("attorney_performance", "avg_settlement_amount", "FLOAT DEFAULT 0"),
        ("attorney_performance", "avg_resolution_days", "FLOAT DEFAULT 0"),
        ("attorney_performance", "client_satisfaction", "FLOAT DEFAULT 0"),
        ("attorney_performance", "efficiency_score", "FLOAT DEFAULT 0"),
        ("attorney_performance", "strengths", "JSON"),
        ("attorney_performance", "calculated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("workflow_triggers", "id", "SERIAL PRIMARY KEY"),
        ("workflow_triggers", "name", "VARCHAR(255) NOT NULL"),
        ("workflow_triggers", "description", "TEXT"),
        ("workflow_triggers", "trigger_type", "VARCHAR(50) NOT NULL"),
        ("workflow_triggers", "conditions", "JSON"),
        ("workflow_triggers", "actions", "JSON NOT NULL"),
        ("workflow_triggers", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("workflow_triggers", "priority", "INTEGER DEFAULT 5"),
        ("workflow_triggers", "last_triggered", "TIMESTAMP"),
        ("workflow_triggers", "trigger_count", "INTEGER DEFAULT 0"),
        ("workflow_triggers", "created_by_staff_id", "INTEGER REFERENCES staff(id)"),
        ("workflow_triggers", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("workflow_triggers", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("workflow_executions", "id", "SERIAL PRIMARY KEY"),
        ("workflow_executions", "trigger_id", "INTEGER NOT NULL REFERENCES workflow_triggers(id)"),
        ("workflow_executions", "client_id", "INTEGER REFERENCES clients(id)"),
        ("workflow_executions", "trigger_event", "JSON"),
        ("workflow_executions", "actions_executed", "JSON"),
        ("workflow_executions", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("workflow_executions", "error_message", "TEXT"),
        ("workflow_executions", "execution_time_ms", "INTEGER"),
        ("workflow_executions", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("white_label_tenants", "id", "SERIAL PRIMARY KEY"),
        ("white_label_tenants", "name", "VARCHAR(255) NOT NULL"),
        ("white_label_tenants", "slug", "VARCHAR(100) UNIQUE NOT NULL"),
        ("white_label_tenants", "domain", "VARCHAR(255) UNIQUE"),
        ("white_label_tenants", "logo_url", "VARCHAR(500)"),
        ("white_label_tenants", "favicon_url", "VARCHAR(500)"),
        ("white_label_tenants", "primary_color", "VARCHAR(7) DEFAULT '#319795'"),
        ("white_label_tenants", "secondary_color", "VARCHAR(7) DEFAULT '#1a1a2e'"),
        ("white_label_tenants", "accent_color", "VARCHAR(7) DEFAULT '#84cc16'"),
        ("white_label_tenants", "company_name", "VARCHAR(255)"),
        ("white_label_tenants", "company_address", "TEXT"),
        ("white_label_tenants", "company_phone", "VARCHAR(50)"),
        ("white_label_tenants", "company_email", "VARCHAR(255)"),
        ("white_label_tenants", "support_email", "VARCHAR(255)"),
        ("white_label_tenants", "terms_url", "VARCHAR(500)"),
        ("white_label_tenants", "privacy_url", "VARCHAR(500)"),
        ("white_label_tenants", "custom_css", "TEXT"),
        ("white_label_tenants", "custom_js", "TEXT"),
        ("white_label_tenants", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("white_label_tenants", "subscription_tier", "VARCHAR(50) DEFAULT 'basic'"),
        ("white_label_tenants", "max_users", "INTEGER DEFAULT 5"),
        ("white_label_tenants", "max_clients", "INTEGER DEFAULT 100"),
        ("white_label_tenants", "features_enabled", "JSON"),
        ("white_label_tenants", "api_key", "VARCHAR(100) UNIQUE"),
        ("white_label_tenants", "webhook_url", "VARCHAR(500)"),
        ("white_label_tenants", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("white_label_tenants", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("tenant_users", "id", "SERIAL PRIMARY KEY"),
        ("tenant_users", "tenant_id", "INTEGER NOT NULL REFERENCES white_label_tenants(id) ON DELETE CASCADE"),
        ("tenant_users", "staff_id", "INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE"),
        ("tenant_users", "role", "VARCHAR(50) DEFAULT 'user'"),
        ("tenant_users", "is_primary_admin", "BOOLEAN DEFAULT FALSE"),
        ("tenant_users", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("tenant_clients", "id", "SERIAL PRIMARY KEY"),
        ("tenant_clients", "tenant_id", "INTEGER NOT NULL REFERENCES white_label_tenants(id) ON DELETE CASCADE"),
        ("tenant_clients", "client_id", "INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE"),
        ("tenant_clients", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("franchise_organizations", "id", "SERIAL PRIMARY KEY"),
        ("franchise_organizations", "name", "VARCHAR(255) NOT NULL"),
        ("franchise_organizations", "slug", "VARCHAR(100) UNIQUE NOT NULL"),
        ("franchise_organizations", "parent_org_id", "INTEGER REFERENCES franchise_organizations(id)"),
        ("franchise_organizations", "org_type", "VARCHAR(50) DEFAULT 'branch'"),
        ("franchise_organizations", "address", "VARCHAR(500)"),
        ("franchise_organizations", "city", "VARCHAR(100)"),
        ("franchise_organizations", "state", "VARCHAR(50)"),
        ("franchise_organizations", "zip_code", "VARCHAR(20)"),
        ("franchise_organizations", "phone", "VARCHAR(50)"),
        ("franchise_organizations", "email", "VARCHAR(255)"),
        ("franchise_organizations", "manager_staff_id", "INTEGER REFERENCES staff(id)"),
        ("franchise_organizations", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("franchise_organizations", "settings", "JSON"),
        ("franchise_organizations", "revenue_share_percent", "FLOAT DEFAULT 0.0"),
        ("franchise_organizations", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("franchise_organizations", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("organization_memberships", "id", "SERIAL PRIMARY KEY"),
        ("organization_memberships", "organization_id", "INTEGER NOT NULL REFERENCES franchise_organizations(id) ON DELETE CASCADE"),
        ("organization_memberships", "staff_id", "INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE"),
        ("organization_memberships", "role", "VARCHAR(50) DEFAULT 'staff'"),
        ("organization_memberships", "permissions", "JSON"),
        ("organization_memberships", "is_primary", "BOOLEAN DEFAULT FALSE"),
        ("organization_memberships", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("organization_clients", "id", "SERIAL PRIMARY KEY"),
        ("organization_clients", "organization_id", "INTEGER NOT NULL REFERENCES franchise_organizations(id) ON DELETE CASCADE"),
        ("organization_clients", "client_id", "INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE"),
        ("organization_clients", "assigned_by_staff_id", "INTEGER REFERENCES staff(id)"),
        ("organization_clients", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("inter_org_transfers", "id", "SERIAL PRIMARY KEY"),
        ("inter_org_transfers", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("inter_org_transfers", "from_org_id", "INTEGER NOT NULL REFERENCES franchise_organizations(id)"),
        ("inter_org_transfers", "to_org_id", "INTEGER NOT NULL REFERENCES franchise_organizations(id)"),
        ("inter_org_transfers", "transfer_type", "VARCHAR(50) DEFAULT 'referral'"),
        ("inter_org_transfers", "reason", "TEXT"),
        ("inter_org_transfers", "transferred_by_staff_id", "INTEGER NOT NULL REFERENCES staff(id)"),
        ("inter_org_transfers", "approved_by_staff_id", "INTEGER REFERENCES staff(id)"),
        ("inter_org_transfers", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("inter_org_transfers", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("inter_org_transfers", "completed_at", "TIMESTAMP"),
        ("api_keys", "id", "SERIAL PRIMARY KEY"),
        ("api_keys", "name", "VARCHAR(255) NOT NULL"),
        ("api_keys", "key_hash", "VARCHAR(255) NOT NULL"),
        ("api_keys", "key_prefix", "VARCHAR(8) NOT NULL"),
        ("api_keys", "tenant_id", "INTEGER REFERENCES white_label_tenants(id) ON DELETE SET NULL"),
        ("api_keys", "organization_id", "INTEGER"),
        ("api_keys", "staff_id", "INTEGER NOT NULL REFERENCES staff(id)"),
        ("api_keys", "scopes", "JSON"),
        ("api_keys", "rate_limit_per_minute", "INTEGER DEFAULT 60"),
        ("api_keys", "rate_limit_per_day", "INTEGER DEFAULT 10000"),
        ("api_keys", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("api_keys", "last_used_at", "TIMESTAMP"),
        ("api_keys", "last_used_ip", "VARCHAR(45)"),
        ("api_keys", "usage_count", "INTEGER DEFAULT 0"),
        ("api_keys", "expires_at", "TIMESTAMP"),
        ("api_keys", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("api_keys", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("api_requests", "id", "SERIAL PRIMARY KEY"),
        ("api_requests", "api_key_id", "INTEGER NOT NULL REFERENCES api_keys(id) ON DELETE CASCADE"),
        ("api_requests", "endpoint", "VARCHAR(500) NOT NULL"),
        ("api_requests", "method", "VARCHAR(10) NOT NULL"),
        ("api_requests", "request_ip", "VARCHAR(45)"),
        ("api_requests", "request_headers", "JSON"),
        ("api_requests", "request_body", "JSON"),
        ("api_requests", "response_status", "INTEGER"),
        ("api_requests", "response_time_ms", "INTEGER"),
        ("api_requests", "error_message", "TEXT"),
        ("api_requests", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("api_webhooks", "id", "SERIAL PRIMARY KEY"),
        ("api_webhooks", "tenant_id", "INTEGER REFERENCES white_label_tenants(id) ON DELETE SET NULL"),
        ("api_webhooks", "name", "VARCHAR(255) NOT NULL"),
        ("api_webhooks", "url", "VARCHAR(500) NOT NULL"),
        ("api_webhooks", "secret", "VARCHAR(100) NOT NULL"),
        ("api_webhooks", "events", "JSON"),
        ("api_webhooks", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("api_webhooks", "last_triggered", "TIMESTAMP"),
        ("api_webhooks", "failure_count", "INTEGER DEFAULT 0"),
        ("api_webhooks", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("api_webhooks", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("white_label_configs", "id", "SERIAL PRIMARY KEY"),
        ("white_label_configs", "organization_id", "INTEGER REFERENCES franchise_organizations(id) ON DELETE SET NULL"),
        ("white_label_configs", "organization_name", "VARCHAR(255) NOT NULL"),
        ("white_label_configs", "subdomain", "VARCHAR(100) UNIQUE NOT NULL"),
        ("white_label_configs", "custom_domain", "VARCHAR(255) UNIQUE"),
        ("white_label_configs", "logo_url", "VARCHAR(500)"),
        ("white_label_configs", "favicon_url", "VARCHAR(500)"),
        ("white_label_configs", "primary_color", "VARCHAR(7) DEFAULT '#319795'"),
        ("white_label_configs", "secondary_color", "VARCHAR(7) DEFAULT '#1a1a2e'"),
        ("white_label_configs", "accent_color", "VARCHAR(7) DEFAULT '#84cc16'"),
        ("white_label_configs", "header_bg_color", "VARCHAR(7) DEFAULT '#1a1a2e'"),
        ("white_label_configs", "sidebar_bg_color", "VARCHAR(7) DEFAULT '#1a1a2e'"),
        ("white_label_configs", "font_family", "VARCHAR(50) DEFAULT 'inter'"),
        ("white_label_configs", "custom_css", "TEXT"),
        ("white_label_configs", "email_from_name", "VARCHAR(255)"),
        ("white_label_configs", "email_from_address", "VARCHAR(255)"),
        ("white_label_configs", "email_from_address_encrypted", "TEXT"),
        ("white_label_configs", "company_address", "TEXT"),
        ("white_label_configs", "company_phone", "VARCHAR(50)"),
        ("white_label_configs", "company_email", "VARCHAR(255)"),
        ("white_label_configs", "footer_text", "TEXT"),
        ("white_label_configs", "terms_url", "VARCHAR(500)"),
        ("white_label_configs", "privacy_url", "VARCHAR(500)"),
        ("white_label_configs", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("white_label_configs", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("white_label_configs", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("audit_logs", "id", "SERIAL PRIMARY KEY"),
        ("audit_logs", "timestamp", "TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP"),
        ("audit_logs", "event_type", "VARCHAR(50) NOT NULL"),
        ("audit_logs", "resource_type", "VARCHAR(50) NOT NULL"),
        ("audit_logs", "resource_id", "VARCHAR(100)"),
        ("audit_logs", "user_id", "INTEGER"),
        ("audit_logs", "user_type", "VARCHAR(20) NOT NULL"),
        ("audit_logs", "user_email", "VARCHAR(255)"),
        ("audit_logs", "user_name", "VARCHAR(255)"),
        ("audit_logs", "user_ip", "VARCHAR(45)"),
        ("audit_logs", "user_agent", "TEXT"),
        ("audit_logs", "action", "VARCHAR(255) NOT NULL"),
        ("audit_logs", "details", "JSON"),
        ("audit_logs", "old_values", "JSON"),
        ("audit_logs", "new_values", "JSON"),
        ("audit_logs", "severity", "VARCHAR(20) DEFAULT 'info'"),
        ("audit_logs", "session_id", "VARCHAR(100)"),
        ("audit_logs", "request_id", "VARCHAR(100)"),
        ("audit_logs", "duration_ms", "INTEGER"),
        ("audit_logs", "endpoint", "VARCHAR(500)"),
        ("audit_logs", "http_method", "VARCHAR(10)"),
        ("audit_logs", "http_status", "INTEGER"),
        ("audit_logs", "organization_id", "INTEGER"),
        ("audit_logs", "tenant_id", "INTEGER"),
        ("audit_logs", "is_phi_access", "BOOLEAN DEFAULT FALSE"),
        ("audit_logs", "phi_fields_accessed", "JSON"),
        ("audit_logs", "compliance_flags", "JSON"),
        ("audit_logs", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("performance_metrics", "id", "SERIAL PRIMARY KEY"),
        ("performance_metrics", "endpoint", "VARCHAR(500) NOT NULL"),
        ("performance_metrics", "method", "VARCHAR(10) NOT NULL"),
        ("performance_metrics", "avg_response_time_ms", "FLOAT DEFAULT 0"),
        ("performance_metrics", "p50_time", "FLOAT DEFAULT 0"),
        ("performance_metrics", "p95_time", "FLOAT DEFAULT 0"),
        ("performance_metrics", "p99_time", "FLOAT DEFAULT 0"),
        ("performance_metrics", "min_response_time_ms", "FLOAT DEFAULT 0"),
        ("performance_metrics", "max_response_time_ms", "FLOAT DEFAULT 0"),
        ("performance_metrics", "request_count", "INTEGER DEFAULT 0"),
        ("performance_metrics", "error_count", "INTEGER DEFAULT 0"),
        ("performance_metrics", "cache_hit_count", "INTEGER DEFAULT 0"),
        ("performance_metrics", "cache_hit_rate", "FLOAT DEFAULT 0"),
        ("performance_metrics", "period_start", "TIMESTAMP NOT NULL"),
        ("performance_metrics", "period_end", "TIMESTAMP NOT NULL"),
        ("performance_metrics", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("cache_entries", "id", "SERIAL PRIMARY KEY"),
        ("cache_entries", "cache_key", "VARCHAR(255) UNIQUE NOT NULL"),
        ("cache_entries", "cache_value", "JSON"),
        ("cache_entries", "ttl_seconds", "INTEGER DEFAULT 300"),
        ("cache_entries", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("cache_entries", "expires_at", "TIMESTAMP"),
        ("cache_entries", "last_accessed", "TIMESTAMP"),
        ("cache_entries", "hit_count", "INTEGER DEFAULT 0"),
        ("dispute_items", "escalation_stage", "VARCHAR(50) DEFAULT 'section_611'"),
        ("dispute_items", "escalation_date", "TIMESTAMP"),
        ("dispute_items", "fcra_section_violated", "VARCHAR(50)"),
        ("dispute_items", "furnisher_dispute_sent", "BOOLEAN DEFAULT FALSE"),
        ("dispute_items", "furnisher_dispute_date", "TIMESTAMP"),
        ("dispute_items", "cfpb_complaint_filed", "BOOLEAN DEFAULT FALSE"),
        ("dispute_items", "cfpb_complaint_date", "TIMESTAMP"),
        ("dispute_items", "cfpb_complaint_id", "VARCHAR(100)"),
        ("dispute_items", "attorney_referral", "BOOLEAN DEFAULT FALSE"),
        ("dispute_items", "method_of_verification_requested", "BOOLEAN DEFAULT FALSE"),
        ("dispute_items", "method_of_verification_received", "BOOLEAN DEFAULT FALSE"),
        ("dispute_items", "dofd", "DATE"),
        ("dispute_items", "obsolescence_date", "DATE"),
        ("letter_queue", "id", "SERIAL PRIMARY KEY"),
        ("letter_queue", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("letter_queue", "dispute_item_id", "INTEGER REFERENCES dispute_items(id)"),
        ("letter_queue", "letter_type", "VARCHAR(50) NOT NULL"),
        ("letter_queue", "trigger_type", "VARCHAR(100) NOT NULL"),
        ("letter_queue", "trigger_description", "TEXT"),
        ("letter_queue", "trigger_date", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("letter_queue", "target_bureau", "VARCHAR(50)"),
        ("letter_queue", "target_creditor", "VARCHAR(255)"),
        ("letter_queue", "target_account", "VARCHAR(100)"),
        ("letter_queue", "letter_data", "JSON"),
        ("letter_queue", "priority", "VARCHAR(20) DEFAULT 'normal'"),
        ("letter_queue", "status", "VARCHAR(50) DEFAULT 'pending'"),
        ("letter_queue", "reviewed_by_staff_id", "INTEGER REFERENCES staff(id)"),
        ("letter_queue", "reviewed_at", "TIMESTAMP"),
        ("letter_queue", "action_notes", "TEXT"),
        ("letter_queue", "generated_letter_id", "INTEGER REFERENCES dispute_letters(id)"),
        ("letter_queue", "generated_at", "TIMESTAMP"),
        ("letter_queue", "generated_pdf_path", "VARCHAR(500)"),
        ("letter_queue", "notification_sent", "BOOLEAN DEFAULT FALSE"),
        ("letter_queue", "notification_sent_at", "TIMESTAMP"),
        ("letter_queue", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("letter_queue", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Phase 8: BAG CRM Feature Parity - Tags and Quick Links
        ("clients", "employer_company", "VARCHAR(255)"),
        # Communication preferences for automation
        ("clients", "sms_opt_in", "BOOLEAN DEFAULT FALSE"),
        ("clients", "email_opt_in", "BOOLEAN DEFAULT TRUE"),
        # Lead scoring
        ("clients", "lead_score", "INTEGER DEFAULT 0"),
        ("clients", "lead_score_factors", "JSONB"),
        ("clients", "lead_scored_at", "TIMESTAMP"),
        ("client_tags", "id", "SERIAL PRIMARY KEY"),
        ("client_tags", "name", "VARCHAR(100) UNIQUE NOT NULL"),
        ("client_tags", "color", "VARCHAR(7) DEFAULT '#6366f1'"),
        ("client_tags", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("client_tag_assignments", "id", "SERIAL PRIMARY KEY"),
        ("client_tag_assignments", "client_id", "INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE"),
        ("client_tag_assignments", "tag_id", "INTEGER NOT NULL REFERENCES client_tags(id) ON DELETE CASCADE"),
        ("client_tag_assignments", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("user_quick_links", "id", "SERIAL PRIMARY KEY"),
        ("user_quick_links", "staff_id", "INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE"),
        ("user_quick_links", "slot_number", "INTEGER NOT NULL"),
        ("user_quick_links", "label", "VARCHAR(50) NOT NULL"),
        ("user_quick_links", "url", "VARCHAR(500) NOT NULL"),
        ("user_quick_links", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # CROA Document Templates for E-Signature
        ("document_templates", "id", "SERIAL PRIMARY KEY"),
        ("document_templates", "code", "VARCHAR(100) UNIQUE NOT NULL"),
        ("document_templates", "name", "VARCHAR(255) NOT NULL"),
        ("document_templates", "description", "TEXT"),
        ("document_templates", "content_html", "TEXT NOT NULL"),
        ("document_templates", "must_sign_before_contract", "BOOLEAN DEFAULT FALSE"),
        ("document_templates", "is_croa_required", "BOOLEAN DEFAULT TRUE"),
        ("document_templates", "signing_order", "INTEGER DEFAULT 0"),
        ("document_templates", "effective_date", "DATE"),
        ("document_templates", "version", "VARCHAR(20) DEFAULT '1.0'"),
        ("document_templates", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("document_templates", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("document_templates", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Client Document Signatures
        ("client_document_signatures", "id", "SERIAL PRIMARY KEY"),
        ("client_document_signatures", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("client_document_signatures", "document_template_id", "INTEGER NOT NULL REFERENCES document_templates(id)"),
        ("client_document_signatures", "signature_data", "TEXT"),
        ("client_document_signatures", "signature_type", "VARCHAR(50) DEFAULT 'typed'"),
        ("client_document_signatures", "ip_address", "VARCHAR(50)"),
        ("client_document_signatures", "user_agent", "TEXT"),
        ("client_document_signatures", "signed_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("client_document_signatures", "signed_document_path", "VARCHAR(500)"),
        ("client_document_signatures", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Booking system for Q&A calls
        ("booking_slots", "id", "SERIAL PRIMARY KEY"),
        ("booking_slots", "slot_date", "DATE NOT NULL"),
        ("booking_slots", "slot_time", "TIME NOT NULL"),
        ("booking_slots", "duration_minutes", "INTEGER DEFAULT 15"),
        ("booking_slots", "is_available", "BOOLEAN DEFAULT TRUE"),
        ("booking_slots", "is_booked", "BOOLEAN DEFAULT FALSE"),
        ("booking_slots", "staff_id", "INTEGER REFERENCES staff(id)"),
        ("booking_slots", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("booking_slots", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("bookings", "id", "SERIAL PRIMARY KEY"),
        ("bookings", "slot_id", "INTEGER NOT NULL REFERENCES booking_slots(id) UNIQUE"),
        ("bookings", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("bookings", "booking_type", "VARCHAR(50) DEFAULT 'qa_call'"),
        ("bookings", "notes", "TEXT"),
        ("bookings", "status", "VARCHAR(20) DEFAULT 'confirmed'"),
        ("bookings", "confirmation_sent", "BOOLEAN DEFAULT FALSE"),
        ("bookings", "confirmation_sent_at", "TIMESTAMP"),
        ("bookings", "reminder_sent", "BOOLEAN DEFAULT FALSE"),
        ("bookings", "reminder_sent_at", "TIMESTAMP"),
        ("bookings", "booked_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("bookings", "cancelled_at", "TIMESTAMP"),
        ("bookings", "completed_at", "TIMESTAMP"),
        ("bookings", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("bookings", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Client Messages (Live Support)
        ("client_messages", "id", "SERIAL PRIMARY KEY"),
        ("client_messages", "client_id", "INTEGER NOT NULL REFERENCES clients(id)"),
        ("client_messages", "staff_id", "INTEGER REFERENCES staff(id)"),
        ("client_messages", "message", "TEXT NOT NULL"),
        ("client_messages", "sender_type", "VARCHAR(20) NOT NULL"),
        ("client_messages", "is_read", "BOOLEAN DEFAULT FALSE"),
        ("client_messages", "read_at", "TIMESTAMP"),
        ("client_messages", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("client_messages", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Email Templates Library
        ("email_templates", "id", "SERIAL PRIMARY KEY"),
        ("email_templates", "template_type", "VARCHAR(50) UNIQUE NOT NULL"),
        ("email_templates", "name", "VARCHAR(200) NOT NULL"),
        ("email_templates", "category", "VARCHAR(50) DEFAULT 'general'"),
        ("email_templates", "description", "TEXT"),
        ("email_templates", "subject", "VARCHAR(500) NOT NULL"),
        ("email_templates", "html_content", "TEXT"),
        ("email_templates", "plain_text_content", "TEXT"),
        ("email_templates", "design_json", "TEXT"),
        ("email_templates", "variables", "JSONB"),
        ("email_templates", "is_custom", "BOOLEAN DEFAULT FALSE"),
        ("email_templates", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("email_templates", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("email_templates", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Drip Campaigns
        ("drip_campaigns", "id", "SERIAL PRIMARY KEY"),
        ("drip_campaigns", "name", "VARCHAR(200) NOT NULL"),
        ("drip_campaigns", "description", "TEXT"),
        ("drip_campaigns", "trigger_type", "VARCHAR(50) NOT NULL"),
        ("drip_campaigns", "trigger_value", "VARCHAR(100)"),
        ("drip_campaigns", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("drip_campaigns", "send_window_start", "INTEGER DEFAULT 9"),
        ("drip_campaigns", "send_window_end", "INTEGER DEFAULT 17"),
        ("drip_campaigns", "send_on_weekends", "BOOLEAN DEFAULT FALSE"),
        ("drip_campaigns", "total_enrolled", "INTEGER DEFAULT 0"),
        ("drip_campaigns", "total_completed", "INTEGER DEFAULT 0"),
        ("drip_campaigns", "created_by_id", "INTEGER REFERENCES staff(id)"),
        ("drip_campaigns", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("drip_campaigns", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Drip Steps
        ("drip_steps", "id", "SERIAL PRIMARY KEY"),
        ("drip_steps", "campaign_id", "INTEGER NOT NULL REFERENCES drip_campaigns(id) ON DELETE CASCADE"),
        ("drip_steps", "step_order", "INTEGER NOT NULL"),
        ("drip_steps", "name", "VARCHAR(200)"),
        ("drip_steps", "delay_days", "INTEGER DEFAULT 1"),
        ("drip_steps", "delay_hours", "INTEGER DEFAULT 0"),
        ("drip_steps", "email_template_id", "INTEGER REFERENCES email_templates(id)"),
        ("drip_steps", "subject", "VARCHAR(500)"),
        ("drip_steps", "html_content", "TEXT"),
        ("drip_steps", "condition_type", "VARCHAR(50)"),
        ("drip_steps", "condition_value", "VARCHAR(100)"),
        ("drip_steps", "is_active", "BOOLEAN DEFAULT TRUE"),
        ("drip_steps", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("drip_steps", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Drip Enrollments
        ("drip_enrollments", "id", "SERIAL PRIMARY KEY"),
        ("drip_enrollments", "campaign_id", "INTEGER NOT NULL REFERENCES drip_campaigns(id) ON DELETE CASCADE"),
        ("drip_enrollments", "client_id", "INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE"),
        ("drip_enrollments", "current_step", "INTEGER DEFAULT 0"),
        ("drip_enrollments", "status", "VARCHAR(20) DEFAULT 'active'"),
        ("drip_enrollments", "enrolled_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("drip_enrollments", "next_send_at", "TIMESTAMP"),
        ("drip_enrollments", "last_sent_at", "TIMESTAMP"),
        ("drip_enrollments", "completed_at", "TIMESTAMP"),
        ("drip_enrollments", "emails_sent", "INTEGER DEFAULT 0"),
        ("drip_enrollments", "emails_opened", "INTEGER DEFAULT 0"),
        ("drip_enrollments", "emails_clicked", "INTEGER DEFAULT 0"),
        ("drip_enrollments", "paused_reason", "VARCHAR(200)"),
        ("drip_enrollments", "cancelled_reason", "VARCHAR(200)"),
        ("drip_enrollments", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("drip_enrollments", "updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Drip Email Logs
        ("drip_email_logs", "id", "SERIAL PRIMARY KEY"),
        ("drip_email_logs", "enrollment_id", "INTEGER NOT NULL REFERENCES drip_enrollments(id) ON DELETE CASCADE"),
        ("drip_email_logs", "step_id", "INTEGER REFERENCES drip_steps(id) ON DELETE SET NULL"),
        ("drip_email_logs", "subject", "VARCHAR(500)"),
        ("drip_email_logs", "sent_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("drip_email_logs", "opened_at", "TIMESTAMP"),
        ("drip_email_logs", "clicked_at", "TIMESTAMP"),
        ("drip_email_logs", "click_url", "VARCHAR(500)"),
        ("drip_email_logs", "status", "VARCHAR(20) DEFAULT 'sent'"),
        ("drip_email_logs", "error_message", "TEXT"),
        ("drip_email_logs", "created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # Partner portal authentication for WhiteLabelTenant
        ("white_label_tenants", "admin_email", "VARCHAR(255) UNIQUE"),
        ("white_label_tenants", "admin_password_hash", "VARCHAR(255)"),
        ("white_label_tenants", "last_login", "TIMESTAMP"),
        ("white_label_tenants", "password_reset_token", "VARCHAR(100) UNIQUE"),
        ("white_label_tenants", "password_reset_expires", "TIMESTAMP"),
    ]

    conn = engine.connect()
    try:
        for table, column, column_type in migrate_columns:
            try:
                sql = text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {column_type}")
                conn.execute(sql)
                conn.commit()
            except Exception as e:
                pass
    except Exception as e:
        print(f"Migration warning: {e}")
    finally:
        conn.close()
    
    create_performance_indices()

def create_performance_indices():
    """Create indices for common query patterns to optimize performance"""
    indices = [
        ("idx_clients_email", "clients", "email"),
        ("idx_clients_phone", "clients", "phone"),
        ("idx_dispute_items_status", "dispute_items", "status"),
        ("idx_audit_logs_timestamp", "audit_logs", "timestamp"),
        ("idx_cases_attorney_id", "cases", "attorney_id"),
        ("idx_cases_status", "cases", "status"),
        ("idx_analyses_client_id", "analyses", "client_id"),
        ("idx_credit_reports_client_id", "credit_reports", "client_id"),
        ("idx_performance_metrics_endpoint", "performance_metrics", "endpoint"),
        ("idx_performance_metrics_period", "performance_metrics", "period_start"),
        ("idx_cache_entries_key", "cache_entries", "cache_key"),
        ("idx_cache_entries_expires", "cache_entries", "expires_at"),
    ]
    
    conn = engine.connect()
    try:
        for idx_name, table, column in indices:
            try:
                check_sql = text(f"""
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = :idx_name
                """)
                result = conn.execute(check_sql, {"idx_name": idx_name}).fetchone()
                
                if not result:
                    create_sql = text(f"CREATE INDEX {idx_name} ON {table}({column})")
                    conn.execute(create_sql)
                    conn.commit()
                    print(f"✅ Created index {idx_name}")
            except Exception as e:
                pass
    except Exception as e:
        print(f"Index creation warning: {e}")
    finally:
        conn.close()

def get_db():
    """Get database session - MUST call session.close() when done"""
    return SessionLocal()
