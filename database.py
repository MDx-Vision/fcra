import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Date, Boolean, Float, ForeignKey, event, JSON, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Add SSL parameter if not present (Replit Postgres requires SSL)
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
        "connect_timeout": 180,  # 180 seconds connection timeout
        "keepalives": 1,
        "keepalives_idle": 10,  # Start keepalives after 10s idle
        "keepalives_interval": 5,  # Send keepalive every 5s
        "keepalives_count": 10,  # Need 10 failed keepalives to fail
        "tcp_user_timeout": 180000,  # 180 seconds TCP user timeout (ms)
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
Base = declarative_base()

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
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    
    # Dates
    follow_up_date = Column(Date)  # When to follow up
    sent_date = Column(Date)  # When dispute was sent
    response_date = Column(Date)  # When response received
    
    # Client/admin interaction
    reason = Column(Text)  # Reason for dispute or status
    comments = Column(Text)  # Client or admin comments
    
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
    """Store custom email templates created with Unlayer visual editor"""
    __tablename__ = 'email_templates'
    
    id = Column(Integer, primary_key=True, index=True)
    template_type = Column(String(50), nullable=False, unique=True)
    subject = Column(String(500), nullable=False)
    html_content = Column(Text)
    design_json = Column(Text)
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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

def get_db():
    """Get database session - MUST call session.close() when done"""
    return SessionLocal()
