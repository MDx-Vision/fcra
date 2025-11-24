import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
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
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Test connections before use
    pool_recycle=300,    # Recycle connections every 5 min to prevent staleness
    connect_args={
        "connect_timeout": 120,  # 120 sec timeout for large writes
        "keepalives": 1,  # Enable TCP keepalives
        "keepalives_idle": 60,  # Start keepalives after 60 sec idle
        "keepalives_interval": 10,  # Send keepalive every 10 sec
        "keepalives_count": 5  # Fail after 5 failed keepalives
    }
)

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
    concrete_harm_type = Column(String(100))
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

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session - MUST call session.close() when done"""
    return SessionLocal()
