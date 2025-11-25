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
    referral_code = Column(String(50), unique=True)
    
    # Client portal access
    portal_token = Column(String(100), unique=True, index=True)
    portal_password_hash = Column(String(255))  # For client login
    
    # Status
    status = Column(String(50), default='signup')  # signup, active, paused, complete, cancelled
    signup_completed = Column(Boolean, default=False)
    agreement_signed = Column(Boolean, default=False)
    agreement_signed_at = Column(DateTime)
    
    # Legacy
    cmm_contact_id = Column(String(100))
    
    # Notes
    admin_notes = Column(Text)
    
    # Payment/Stripe fields
    signup_plan = Column(String(50))  # tier1, tier2, tier3, tier4, tier5
    signup_amount = Column(Integer)  # Amount in cents
    stripe_customer_id = Column(String(255))
    stripe_checkout_session_id = Column(String(255))
    stripe_payment_intent_id = Column(String(255))
    payment_status = Column(String(50), default='pending')  # pending, paid, failed, refunded
    payment_received_at = Column(DateTime)
    
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


def init_db():
    """Initialize database tables and run schema migrations"""
    Base.metadata.create_all(bind=engine)
    
    migrate_columns = [
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
