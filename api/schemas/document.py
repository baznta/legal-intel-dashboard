"""
Pydantic schemas for document API requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class DocumentBase(BaseModel):
    """Base document schema."""
    
    filename: str = Field(..., description="Document filename")
    original_filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type")
    file_extension: str = Field(..., description="File extension")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""
    
    file_path: str = Field(..., description="Storage path")
    
    @validator('file_size')
    def validate_file_size(cls, v):
        if v <= 0:
            raise ValueError('File size must be positive')
        if v > 50 * 1024 * 1024:  # 50MB
            raise ValueError('File size must be less than 50MB')
        return v


class DocumentResponse(DocumentBase):
    """Schema for document response."""
    
    id: str = Field(..., description="Document ID")
    status: str = Field(..., description="Document status")
    uploaded_at: datetime = Field(..., description="Upload timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    """Schema for document upload response."""
    
    id: str = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    status: str = Field(..., description="Upload status")
    file_size: int = Field(..., description="File size in bytes")
    message: str = Field(..., description="Status message")


class DocumentMetadataResponse(BaseModel):
    """Schema for document metadata response."""
    
    id: str = Field(..., description="Metadata ID")
    document_id: str = Field(..., description="Document ID")
    
    # Core metadata
    agreement_type: Optional[str] = Field(None, description="Type of agreement")
    jurisdiction: Optional[str] = Field(None, description="Legal jurisdiction")
    governing_law: Optional[str] = Field(None, description="Governing law")
    geography: Optional[str] = Field(None, description="Geographic region")
    industry_sector: Optional[str] = Field(None, description="Industry sector")
    
    # Additional metadata
    parties: Optional[List[str]] = Field(None, description="Contracting parties")
    effective_date: Optional[datetime] = Field(None, description="Effective date")
    expiration_date: Optional[datetime] = Field(None, description="Expiration date")
    contract_value: Optional[float] = Field(None, description="Contract value")
    currency: Optional[str] = Field(None, description="Currency")
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    
    # Extraction info
    extraction_confidence: Optional[float] = Field(None, description="Extraction confidence score")
    extraction_method: Optional[str] = Field(None, description="Extraction method used")
    extracted_at: datetime = Field(..., description="Extraction timestamp")
    
    class Config:
        from_attributes = True


class DocumentContentResponse(BaseModel):
    """Schema for document content response."""
    
    id: str = Field(..., description="Content ID")
    document_id: str = Field(..., description="Document ID")
    
    # Content
    text_content: str = Field(..., description="Extracted text content")
    word_count: int = Field(..., description="Word count")
    character_count: int = Field(..., description="Character count")
    
    # Structured content
    sections: Optional[List[Dict[str, Any]]] = Field(None, description="Document sections")
    paragraphs: Optional[List[str]] = Field(None, description="Document paragraphs")
    tables: Optional[List[Dict[str, Any]]] = Field(None, description="Extracted tables")
    
    # Extraction info
    extraction_method: Optional[str] = Field(None, description="Extraction method used")
    extraction_timestamp: datetime = Field(..., description="Extraction timestamp")
    confidence_score: Optional[float] = Field(None, description="Extraction confidence")
    language_detected: Optional[str] = Field(None, description="Detected language")
    
    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Schema for document list response with pagination."""
    
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class DocumentFilter(BaseModel):
    """Schema for document filtering."""
    
    status: Optional[str] = Field(None, description="Filter by status")
    agreement_type: Optional[str] = Field(None, description="Filter by agreement type")
    jurisdiction: Optional[str] = Field(None, description="Filter by jurisdiction")
    industry_sector: Optional[str] = Field(None, description="Filter by industry sector")
    uploaded_after: Optional[datetime] = Field(None, description="Uploaded after date")
    uploaded_before: Optional[datetime] = Field(None, description="Uploaded before date")
    min_file_size: Optional[int] = Field(None, description="Minimum file size")
    max_file_size: Optional[int] = Field(None, description="Maximum file size")


class DocumentProcessingJobResponse(BaseModel):
    """Schema for document processing job response."""
    
    id: str = Field(..., description="Job ID")
    document_id: str = Field(..., description="Document ID")
    job_type: str = Field(..., description="Type of processing job")
    status: str = Field(..., description="Job status")
    priority: int = Field(..., description="Job priority")
    
    # Timing
    created_at: datetime = Field(..., description="Job creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    
    # Results
    result_data: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(..., description="Number of retry attempts")
    max_retries: int = Field(..., description="Maximum retry attempts")
    
    class Config:
        from_attributes = True


class DocumentUploadRequest(BaseModel):
    """Schema for document upload request."""
    
    files: List[str] = Field(..., description="List of file paths to upload")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    tags: Optional[List[str]] = Field(None, description="Document tags")
    priority: Optional[int] = Field(0, description="Processing priority")


class DocumentQueryRequest(BaseModel):
    """Schema for document query request."""
    
    query: str = Field(..., description="Natural language query")
    filters: Optional[DocumentFilter] = Field(None, description="Document filters")
    limit: Optional[int] = Field(100, description="Maximum number of results")
    offset: Optional[int] = Field(0, description="Result offset")


class DocumentQueryResponse(BaseModel):
    """Schema for document query response."""
    
    query: str = Field(..., description="Original query")
    results: List[Dict[str, Any]] = Field(..., description="Query results")
    total_results: int = Field(..., description="Total number of results")
    processing_time: float = Field(..., description="Query processing time in seconds")
    confidence_score: Optional[float] = Field(None, description="Overall confidence score")


class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete request."""
    
    document_ids: List[str] = Field(..., description="List of document IDs to delete", min_items=1, max_items=50)
    
    @validator('document_ids')
    def validate_document_ids(cls, v):
        if not v:
            raise ValueError('At least one document ID must be provided')
        if len(v) > 50:
            raise ValueError('Maximum 50 documents can be deleted at once')
        return v


class BulkDeleteResponse(BaseModel):
    """Schema for bulk delete response."""
    
    message: str = Field(..., description="Result message")
    deleted_count: int = Field(..., description="Number of successfully deleted documents")
    failed_count: int = Field(..., description="Number of failed deletions")
    total_requested: int = Field(..., description="Total number of documents requested for deletion")
    errors: Optional[List[str]] = Field(None, description="List of error messages for failed deletions")


class DeleteResponse(BaseModel):
    """Schema for delete response."""
    
    message: str = Field(..., description="Result message")
    document_id: str = Field(..., description="ID of the deleted document")
    filename: str = Field(..., description="Filename of the deleted document") 