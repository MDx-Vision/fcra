import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, event
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
    email = Column(String(255))
    phone = Column(String(50))
    cmm_contact_id = Column(String(100))
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


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session - MUST call session.close() when done"""
    return SessionLocal()
