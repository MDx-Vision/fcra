import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")
engine = create_engine(DATABASE_URL)
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
    full_analysis = Column(Text)
    cost = Column(Float)
    tokens_used = Column(Integer)
    cache_read = Column(Boolean, default=False)
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

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session - MUST call session.close() when done"""
    return SessionLocal()
