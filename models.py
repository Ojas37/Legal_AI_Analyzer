# models.py - Fixed Version
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum as PyEnum
import uuid

# Create the Base class properly
Base = declarative_base()

# Define enums first
class DocumentStatus(PyEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    QUEUED = "queued"

class DocumentType(PyEnum):
    CONTRACT = "contract"
    EMPLOYMENT = "employment" 
    LICENSE = "license"
    LEASE = "lease"
    NDA = "nda"
    TERMS_OF_SERVICE = "terms_of_service"
    PRIVACY_POLICY = "privacy_policy"
    OTHER = "other"

class User(Base):
    """User model for authentication and account management"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    job_title = Column(String(100), nullable=True)
    
    # Authentication
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    
    # Subscription and usage
    subscription_tier = Column(String(20), default="free")  # free, pro, enterprise
    monthly_uploads = Column(Integer, default=0)
    upload_limit = Column(Integer, default=10)  # per month
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

class APIKey(Base):
    """API keys for programmatic access"""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    key_name = Column(String(100), nullable=False)
    key_hash = Column(String(255), unique=True, nullable=False, index=True)
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for display
    
    # Usage tracking
    requests_made = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.key_name}')>"

class Document(Base):
    """Main document model for uploaded legal files"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)  # PDF, DOCX, TXT
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_hash = Column(String(64), nullable=False, index=True)  # SHA-256 of content
    storage_path = Column(String(500), nullable=True)  # Path to stored file
    
    # Processing status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False, index=True)
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_duration = Column(Float, nullable=True)  # seconds
    error_message = Column(Text, nullable=True)
    
    # Document content
    extracted_text = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    character_count = Column(Integer, nullable=True)
    
    # Upload info
    upload_ip = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(String(500), nullable=True)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="documents")
    analysis = relationship("DocumentAnalysis", back_populates="document", uselist=False, cascade="all, delete-orphan")
    entities = relationship("ExtractedEntity", back_populates="document", cascade="all, delete-orphan")
    clauses = relationship("ExtractedClause", back_populates="document", cascade="all, delete-orphan")
    risks = relationship("RiskAssessment", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.original_filename}')>"

class DocumentAnalysis(Base):
    """AI analysis results for documents"""
    __tablename__ = "document_analyses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    
    # Classification results
    predicted_type = Column(Enum(DocumentType), nullable=False, index=True)
    classification_confidence = Column(Float, nullable=False)
    classification_scores = Column(JSON, nullable=True)  # All model scores
    
    # AI-generated content
    executive_summary = Column(Text, nullable=True)
    key_points = Column(JSON, nullable=True)  # List of key points
    recommendations = Column(JSON, nullable=True)  # AI recommendations
    
    # Analysis info
    model_version = Column(String(50), default="legal-bert-v1.0")
    analysis_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    confidence_score = Column(Float, nullable=True)  # Overall confidence
    
    # Risk scoring
    overall_risk_score = Column(Float, nullable=True)  # 0-100
    complexity_score = Column(Float, nullable=True)  # 0-100
    
    # Relationships
    document = relationship("Document", back_populates="analysis")

    def __repr__(self):
        return f"<DocumentAnalysis(id={self.id}, type='{self.predicted_type.value}')>"

class ExtractedEntity(Base):
    """Extracted legal entities (people, organizations, dates, etc.)"""
    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Entity details
    entity_type = Column(String(50), nullable=False, index=True)  # PERSON, ORG, DATE, MONEY, etc.
    entity_text = Column(String(500), nullable=False)
    normalized_value = Column(String(500), nullable=True)  # Standardized form
    entity_category = Column(String(50), nullable=True)  # legal_entity, financial, temporal
    
    # Position and context
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    context_before = Column(String(200), nullable=True)
    context_after = Column(String(200), nullable=True)
    
    # Confidence and validation
    confidence_score = Column(Float, nullable=True)
    is_verified = Column(Boolean, default=False)
    extraction_method = Column(String(30), default="spacy_nlp")
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="entities")

    def __repr__(self):
        return f"<ExtractedEntity(id={self.id}, type='{self.entity_type}')>"

class ExtractedClause(Base):
    """Key legal clauses extracted from documents"""
    __tablename__ = "extracted_clauses"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Clause information
    clause_type = Column(String(100), nullable=False, index=True)  # termination, payment, liability, etc.
    clause_title = Column(String(200), nullable=True)
    clause_text = Column(Text, nullable=False)
    clause_summary = Column(Text, nullable=True)  # AI-generated summary
    
    # Classification
    clause_category = Column(String(50), nullable=True)  # financial, legal, operational, etc.
    importance_level = Column(String(20), default="medium")  # low, medium, high, critical
    
    # Position information
    section_number = Column(String(20), nullable=True)
    page_number = Column(Integer, nullable=True)
    start_position = Column(Integer, nullable=True)
    end_position = Column(Integer, nullable=True)
    
    # AI analysis
    extraction_method = Column(String(30), default="qa_pipeline")
    confidence_score = Column(Float, nullable=True)
    question_used = Column(String(300), nullable=True)  # Question for QA extraction
    
    # Risk and compliance
    risk_indicators = Column(JSON, nullable=True)  # List of potential risks
    compliance_notes = Column(Text, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="clauses")

    def __repr__(self):
        return f"<ExtractedClause(id={self.id}, type='{self.clause_type}')>"

class RiskAssessment(Base):
    """Risk assessment results for legal documents"""
    __tablename__ = "risk_assessments"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Risk categories
    financial_risk = Column(Float, nullable=True)  # 0-100
    legal_risk = Column(Float, nullable=True)      # 0-100
    operational_risk = Column(Float, nullable=True) # 0-100
    compliance_risk = Column(Float, nullable=True)  # 0-100
    
    # Overall assessment
    overall_risk = Column(Float, nullable=False)    # 0-100
    risk_level = Column(String(20), nullable=False) # low, medium, high, critical
    
    # Risk details
    risk_factors = Column(JSON, nullable=True)      # List of identified risks
    mitigation_suggestions = Column(JSON, nullable=True) # AI suggestions
    flags = Column(JSON, nullable=True)             # Important flags/warnings
    
    # Analysis info
    assessment_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    model_version = Column(String(50), default="risk-analyzer-v1.0")
    
    # Relationships
    document = relationship("Document", back_populates="risks")

    def __repr__(self):
        return f"<RiskAssessment(id={self.id}, level='{self.risk_level}')>"

class SystemLog(Base):
    """System-wide logging for monitoring and debugging"""
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Log details
    level = Column(String(10), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    message = Column(Text, nullable=False)
    component = Column(String(100), nullable=True)         # api, processor, extractor, etc.
    operation = Column(String(100), nullable=True)         # upload, analyze, extract, etc.
    
    # Context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True, index=True)
    request_id = Column(String(36), nullable=True, index=True)  # For tracing requests
    
    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    
    # Additional data
    extra_data = Column(JSON, nullable=True)  # Additional context as JSON
    stack_trace = Column(Text, nullable=True)  # For errors
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SystemLog(id={self.id}, level='{self.level}')>"

# Utility functions for working with models
def create_user(email: str, full_name: str, hashed_password: str, **kwargs) -> User:
    """Create a new user record"""
    return User(
        email=email,
        full_name=full_name,
        hashed_password=hashed_password,
        **kwargs
    )

def create_document_record(user_id: int, filename: str, file_type: str, 
                          file_size: int, file_hash: str, **kwargs) -> Document:
    """Create a new document record"""
    return Document(
        user_id=user_id,
        original_filename=filename,
        file_type=file_type,
        file_size=file_size,
        file_hash=file_hash,
        status=DocumentStatus.UPLOADED,
        **kwargs
    )
