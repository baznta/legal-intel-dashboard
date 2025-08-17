"""
Database models for document management.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid

Base = declarative_base()


class Document(Base):
    """Main document model."""
    
    __tablename__ = "documents"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String(255), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_extension = Column(String(10), nullable=False)
    status = Column(String(50), default="uploaded", index=True)
    
    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Processing info
    processing_started_at = Column(DateTime(timezone=True), nullable=True)
    processing_completed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Status values: uploaded -> extracting_text -> text_extracted -> extracting_metadata -> completed/failed
    
    # Relationships
    document_metadata = relationship("DocumentMetadata", back_populates="document", uselist=False)
    content = relationship("DocumentContent", back_populates="document", uselist=False)
    processing_jobs = relationship("DocumentProcessingJob", back_populates="document")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename='{self.filename}', status='{self.status}')>"
    
    def soft_delete(self):
        """Soft delete the document."""
        self.deleted_at = datetime.utcnow()
        self.status = "deleted"
    
    def is_deleted(self) -> bool:
        """Check if document is soft deleted."""
        return self.deleted_at is not None


class DocumentMetadata(Base):
    """Extracted metadata from documents."""
    
    __tablename__ = "document_metadata"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, unique=True)
    
    # Core metadata
    agreement_type = Column(String(100), nullable=True, index=True)
    jurisdiction = Column(String(100), nullable=True, index=True)
    governing_law = Column(String(100), nullable=True, index=True)
    geography = Column(String(100), nullable=True, index=True)
    industry_sector = Column(String(100), nullable=True, index=True)
    
    # Additional metadata
    parties = Column(JSON, nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    contract_value = Column(Float, nullable=True)
    currency = Column(String(10), nullable=True)
    keywords = Column(JSON, nullable=True)
    tags = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)  # AI-generated document summary
    
    # Extraction info
    extraction_confidence = Column(Float, nullable=True)
    extraction_method = Column(String(100), nullable=True)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="document_metadata")
    
    def __repr__(self):
        return f"<DocumentMetadata(id={self.id}, document_id={self.document_id})>"


class DocumentContent(Base):
    """Extracted text content from documents."""
    
    __tablename__ = "document_content"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False, unique=True)
    
    # Content
    text_content = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)
    character_count = Column(Integer, nullable=False)
    
    # Structured content
    sections = Column(JSON, nullable=True)
    paragraphs = Column(JSON, nullable=True)
    tables = Column(JSON, nullable=True)
    
    # Extraction info
    extraction_method = Column(String(100), nullable=True)
    extraction_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    confidence_score = Column(Float, nullable=True)
    language_detected = Column(String(10), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="content")
    
    def __repr__(self):
        return f"<DocumentContent(id={self.id}, document_id={self.document_id})>"


class DocumentProcessingJob(Base):
    """Document processing job tracking."""
    
    __tablename__ = "document_processing_jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    
    # Job info
    job_type = Column(String(100), nullable=False)  # text_extraction, metadata_extraction, etc.
    status = Column(String(50), default="pending", index=True)
    priority = Column(Integer, default=0)
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Results
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Relationships
    document = relationship("Document", back_populates="processing_jobs")
    
    def __repr__(self):
        return f"<DocumentProcessingJob(id={self.id}, document_id={self.document_id}, status='{self.status}')>"
    
    def start(self):
        """Mark job as started."""
        self.status = "processing"
        self.started_at = datetime.utcnow()
    
    def complete(self, result_data: dict = None):
        """Mark job as completed."""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        if result_data:
            self.result_data = result_data
    
    def fail(self, error_message: str):
        """Mark job as failed."""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error_message
    
    def retry(self):
        """Increment retry count."""
        self.retry_count += 1
        if self.retry_count >= self.max_retries:
            self.status = "failed"
        else:
            self.status = "pending"
            self.started_at = None
            self.completed_at = None
            self.error_message = None 