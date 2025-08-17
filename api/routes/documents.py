"""
Document management routes for uploading, listing, and managing legal documents.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
import structlog
import uuid
import os
from datetime import datetime

from core.database import get_db
from core.minio_client import upload_file_object, get_file_info
from core.config import settings
from models.document import Document, DocumentMetadata, DocumentContent, DocumentProcessingJob
from schemas.document import DocumentResponse, DocumentUploadResponse, BulkDeleteRequest, BulkDeleteResponse, DeleteResponse
from workers.tasks import process_all_pending_documents
from services.document_service import DocumentService

logger = structlog.get_logger()
router = APIRouter()


@router.post("/documents/upload", response_model=List[DocumentUploadResponse])
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """Upload multiple legal documents."""
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    if len(files) > 10:  # Limit to 10 files per request
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per request")
    
    uploaded_documents = []
    
    try:
        for file in files:
            try:
                # Validate file type
                file_extension = os.path.splitext(file.filename)[1].lower().lstrip('.')
                if file_extension not in settings.allowed_file_types:
                    logger.warning(f"Invalid file type: {file.filename}")
                    uploaded_documents.append(DocumentUploadResponse(
                        id="",
                        filename=file.filename,
                        status="failed",
                        file_size=file.size,
                        message=f"Invalid file type: {file_extension}"
                    ))
                    continue
                
                # Validate file size
                if file.size > settings.max_file_size:
                    logger.warning(f"File too large: {file.filename}")
                    uploaded_documents.append(DocumentUploadResponse(
                        id="",
                        filename=file.filename,
                        status="failed",
                        file_size=file.size,
                        message=f"File too large: {file.size} bytes"
                    ))
                    continue
                
                # Generate unique filename
                file_id = str(uuid.uuid4())
                object_name = f"documents/{file_id}/{file.filename}"
                
                # Upload to MinIO
                success = upload_file_object(
                    file_object=file.file,
                    object_name=object_name,
                    file_size=file.size,
                    content_type=file.content_type
                )
                
                if not success:
                    logger.error(f"Failed to upload file to MinIO: {file.filename}")
                    uploaded_documents.append(DocumentUploadResponse(
                        id="",
                        filename=file.filename,
                        status="failed",
                        file_size=file.size,
                        message="Failed to upload to storage"
                    ))
                    continue
                
                # Create document record in database
                document = Document(
                    filename=file_id,
                    original_filename=file.filename,
                    file_path=object_name,
                    file_size=file.size,
                    mime_type=file.content_type or "application/octet-stream",
                    file_extension=file_extension,
                    status="uploaded"
                )
                
                db.add(document)
                
                uploaded_documents.append(DocumentUploadResponse(
                    id=str(document.id),
                    filename=file.filename,
                    status="uploaded",
                    file_size=file.size,
                    message="Document uploaded successfully"
                ))
                
                logger.info(f"Document uploaded successfully: {file.filename}")
                
            except Exception as e:
                logger.error(f"Error uploading document {file.filename}: {e}")
                uploaded_documents.append(DocumentUploadResponse(
                    id="",
                    filename=file.filename,
                    status="failed",
                    file_size=file.size,
                    message=f"Upload failed: {str(e)}"
                ))
        
        # Commit all documents at once
        await db.commit()
        
    except Exception as e:
        logger.error(f"Database error during upload: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    return uploaded_documents


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    agreement_type: Optional[str] = None,
    jurisdiction: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List documents with optional filtering and pagination."""
    
    from sqlalchemy import select
    
    # Build query - exclude deleted documents
    query = select(Document).where(Document.deleted_at.is_(None))
    
    # Apply filters
    if status:
        query = query.where(Document.status == status)
    if agreement_type:
        query = query.join(DocumentMetadata).where(DocumentMetadata.agreement_type == agreement_type)
    if jurisdiction:
        query = query.join(DocumentMetadata).where(DocumentMetadata.jurisdiction == jurisdiction)
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    documents = result.scalars().all()
    return [DocumentResponse.from_orm(doc) for doc in documents]


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific document by ID."""
    
    from sqlalchemy import select
    
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return DocumentResponse.from_orm(document)


@router.delete("/documents/bulk", response_model=BulkDeleteResponse)
async def bulk_delete_documents(
    request: BulkDeleteRequest,
    db: AsyncSession = Depends(get_db)
):
    """Delete multiple documents at once."""
    
    document_ids = request.document_ids
    
    try:
        from sqlalchemy import select, delete
        
        deleted_count = 0
        failed_count = 0
        errors = []
        
        for doc_id in document_ids:
            try:
                # Get the document
                result = await db.execute(select(Document).where(Document.id == doc_id))
                document = result.scalar_one_or_none()
                
                if not document:
                    failed_count += 1
                    errors.append(f"Document {doc_id} not found")
                    continue
                
                # Check if document is currently being processed
                if document.status == "processing":
                    failed_count += 1
                    errors.append(f"Document {document.original_filename} is currently being processed")
                    continue
                
                # Delete related data first
                await db.execute(
                    delete(DocumentProcessingJob).where(DocumentProcessingJob.document_id == doc_id)
                )
                await db.execute(
                    delete(DocumentMetadata).where(DocumentMetadata.document_id == doc_id)
                )
                await db.execute(
                    delete(DocumentContent).where(DocumentContent.document_id == doc_id)
                )
                
                # Soft delete the document
                document.soft_delete()
                
                # Delete file from MinIO storage
                try:
                    from core.minio_client import delete_file
                    if document.file_path:
                        delete_file(document.file_path)
                        logger.info(f"File deleted from MinIO: {document.file_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file from MinIO: {e}")
                    # Don't fail the entire operation if MinIO deletion fails
                
                deleted_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append(f"Failed to delete document {doc_id}: {str(e)}")
                continue
        
        # Commit all changes
        await db.commit()
        
        return {
            "message": f"Bulk delete completed. Deleted: {deleted_count}, Failed: {failed_count}",
            "deleted_count": deleted_count,
            "failed_count": failed_count,
            "total_requested": len(document_ids),
            "errors": errors if failed_count > 0 else None
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Bulk delete failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Bulk delete failed: {str(e)}"
        )


@router.delete("/documents/{document_id}", response_model=DeleteResponse)
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a document (soft delete)."""
    
    from sqlalchemy import select, delete
    
    try:
        # Get the document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if document is currently being processed
        if document.status == "processing":
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete document while it is being processed"
            )
        
        # Delete related data first
        # Delete processing jobs
        await db.execute(
            delete(DocumentProcessingJob).where(DocumentProcessingJob.document_id == document_id)
        )
        
        # Delete metadata
        await db.execute(
            delete(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
        )
        
        # Delete content
        await db.execute(
            delete(DocumentContent).where(DocumentContent.document_id == document_id)
        )
        
        # Soft delete the document
        document.soft_delete()
        
        # Commit all changes
        await db.commit()
    
        # Optionally delete the file from MinIO storage
        try:
            from core.minio_client import delete_file
            if document.file_path:
                delete_file(document.file_path)
                logger.info(f"File deleted from MinIO: {document.file_path}")
        except Exception as e:
            logger.warning(f"Failed to delete file from MinIO: {e}")
            # Don't fail the entire operation if MinIO deletion fails
        
        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "filename": document.original_filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generate download URL for a document."""
    
    from sqlalchemy import select
    
    result = await db.execute(select(Document).where(Document.id == document_id))
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get file info from MinIO
    file_info = get_file_info(document.file_path)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found in storage")
    
    # Generate presigned URL for download
    from core.minio_client import generate_presigned_url
    download_url = generate_presigned_url(document.file_path, method="GET", expires=3600)
    
    if not download_url:
        raise HTTPException(status_code=500, detail="Failed to generate download URL")
    
    return {
        "download_url": download_url,
        "expires_in": 3600,
        "filename": document.original_filename,
        "file_size": document.file_size
    }


@router.get("/documents/{document_id}/metadata")
async def get_document_metadata(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get extracted metadata for a document."""
    
    from sqlalchemy import select
    from models.document import Document, DocumentMetadata
    
    # Use join to eagerly load metadata
    query = select(Document, DocumentMetadata).join(
        DocumentMetadata, Document.id == DocumentMetadata.document_id, isouter=True
    ).where(Document.id == document_id)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document, metadata = row
    
    if not metadata:
        raise HTTPException(status_code=404, detail="No metadata found for document")
    
    return {
        "document_id": str(document.id),
        "filename": document.original_filename,
            "agreement_type": metadata.agreement_type,
            "jurisdiction": metadata.jurisdiction,
            "governing_law": metadata.governing_law,
            "geography": metadata.geography,
            "industry_sector": metadata.industry_sector,
            "parties": metadata.parties,
            "effective_date": metadata.effective_date.isoformat() if metadata.effective_date else None,
            "expiration_date": metadata.expiration_date.isoformat() if metadata.expiration_date else None,
            "contract_value": metadata.contract_value,
            "currency": metadata.currency,
            "keywords": metadata.keywords,
            "tags": metadata.tags,
        "summary": metadata.summary,
            "extraction_confidence": metadata.extraction_confidence,
            "extraction_method": metadata.extraction_method
    }


@router.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get extracted text content for a document."""
    
    from sqlalchemy import select
    from models.document import Document, DocumentContent
    
    # Use join to eagerly load content
    query = select(Document, DocumentContent).join(
        DocumentContent, Document.id == DocumentContent.document_id, isouter=True
    ).where(Document.id == document_id)
    
    result = await db.execute(query)
    row = result.first()
    
    if not row:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document, content = row
    
    if not content:
        raise HTTPException(status_code=404, detail="No content found for document")
    
    return {
        "document_id": str(document.id),
        "filename": document.original_filename,
            "text_content": content.text_content,
            "word_count": content.word_count,
            "character_count": content.character_count,
            "sections": content.sections,
            "paragraphs": content.paragraphs,
            "extraction_method": content.extraction_method,
            "extraction_timestamp": content.extraction_timestamp.isoformat() if content.extraction_timestamp else None,
            "confidence_score": content.confidence_score,
            "language_detected": content.language_detected
    }


@router.post("/documents/{document_id}/process")
async def process_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Process a document to extract text and metadata."""
    
    from sqlalchemy import select
    from models.document import Document
    from workers.tasks import process_document as celery_process_document_task
    
    # Check if document exists and is not deleted
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.deleted_at.is_(None)
        )
    )
    document = result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Check if document is already processed
    if document.status == "completed":
        return {"message": "Document already processed", "status": "completed"}
    
    if document.status == "processing":
        return {"message": "Document is already being processed", "status": "processing"}
    
    try:
        # Trigger Celery task
        task = celery_process_document_task.delay(document_id)
        
        return {
            "message": "Document processing started",
            "task_id": task.id,
            "document_id": document_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Failed to start document processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to start document processing")


@router.get("/documents/{document_id}/status")
async def get_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the current status of a document and its processing jobs."""
    
    from sqlalchemy import select
    from models.document import Document, DocumentProcessingJob
    
    # Get document with processing jobs (excluding deleted documents)
    query = select(Document, DocumentProcessingJob).join(
        DocumentProcessingJob, Document.id == DocumentProcessingJob.document_id, isouter=True
    ).where(
        Document.id == document_id,
        Document.deleted_at.is_(None)
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    if not rows:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document = rows[0][0]  # First row, first column is the document
    
    # Get processing jobs
    processing_jobs = []
    for row in rows:
        if row[1]:  # If there's a processing job
            job = row[1]
            processing_jobs.append({
                "job_id": str(job.id),
                "job_type": job.job_type,
                "status": job.status,
                "priority": job.priority,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message
            })
    
    # Check if document has content and metadata
    content_query = select(DocumentContent).where(DocumentContent.document_id == document_id)
    content_result = await db.execute(content_query)
    has_content = content_result.scalar_one_or_none() is not None
    
    metadata_query = select(DocumentMetadata).where(DocumentMetadata.document_id == document_id)
    metadata_result = await db.execute(metadata_query)
    has_metadata = metadata_result.scalar_one_or_none() is not None
    
    return {
        "document_id": str(document.id),
        "filename": document.original_filename,
        "status": document.status,
        "uploaded_at": document.uploaded_at.isoformat() if document.uploaded_at else None,
        "processing_started_at": document.processing_started_at.isoformat() if document.processing_started_at else None,
        "processing_completed_at": document.processing_completed_at.isoformat() if document.processing_completed_at else None,
        "processing_error": document.processing_error,
        "processing_jobs": processing_jobs,
        "has_content": has_content,
        "has_metadata": has_metadata
    }


@router.get("/documents/{document_id}/processing-jobs")
async def get_document_processing_jobs(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all processing jobs for a document."""
    
    from sqlalchemy import select
    from models.document import DocumentProcessingJob
    
    # Check if document exists first
    doc_query = select(Document).where(Document.id == document_id)
    doc_result = await db.execute(doc_query)
    document = doc_result.scalar_one_or_none()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get processing jobs
    jobs_query = select(DocumentProcessingJob).where(
        DocumentProcessingJob.document_id == document_id
    ).order_by(DocumentProcessingJob.created_at.desc())
    
    result = await db.execute(jobs_query)
    jobs = result.scalars().all()
    
    processing_jobs = []
    for job in jobs:
        processing_jobs.append({
            "job_id": str(job.id),
            "job_type": job.job_type,
            "status": job.status,
            "priority": job.priority,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
            "result_data": job.result_data
        })
    
    return {
        "document_id": str(document_id),
        "filename": document.original_filename,
        "total_jobs": len(processing_jobs),
        "processing_jobs": processing_jobs
    }


@router.get("/processing/status")
async def get_processing_status():
    """Get overall processing system status."""
    
    try:
        # Check Celery worker status
        from workers.celery_app import celery_app
        
        # Get active workers
        active_workers = celery_app.control.inspect().active()
        registered_workers = celery_app.control.inspect().registered()
        
        # Check Redis connection
        from core.config import settings
        import redis
        
        redis_client = redis.from_url(settings.redis_url)
        redis_ping = redis_client.ping()
        
        return {
            "system_status": "healthy",
            "celery": {
                "active_workers": len(active_workers) if active_workers else 0,
                "registered_workers": len(registered_workers) if registered_workers else 0,
                "worker_status": "running" if active_workers else "stopped"
            },
            "redis": {
                "status": "connected" if redis_ping else "disconnected",
                "url": settings.redis_url
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing status: {e}")
        return {
            "system_status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/tasks/{task_id}/status")
async def get_task_status(task_id: str):
    """Get the status of a specific Celery task."""
    
    try:
        from workers.celery_app import celery_app
        
        # Get task result
        task_result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": task_result.status,
            "ready": task_result.ready(),
            "successful": task_result.successful(),
            "failed": task_result.failed(),
            "result": task_result.result if task_result.ready() else None,
            "info": task_result.info,
            "traceback": task_result.traceback if task_result.failed() else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        return {
            "task_id": task_id,
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.post("/documents/{document_id}/reset")
async def reset_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Reset document status for reprocessing."""
    
    try:
        from sqlalchemy import select
        from models.document import Document
        from services.document_service import DocumentService
        
        # Check if document exists
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Reset document status
        document_service = DocumentService()
        success = await document_service.reset_document_status(db, document_id, "pending")
        
        if success:
            return {
                "message": "Document status reset successfully",
                "document_id": document_id,
                "new_status": "pending",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reset document status")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset document status: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Reprocess a document by clearing existing metadata and content, then re-extracting everything."""
    
    try:
        document_service = DocumentService()
        result = await document_service.reprocess_document(db, document_id)
        
        return {
            "message": "Document reprocessing started successfully",
            "document_id": document_id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Failed to start document reprocessing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start document reprocessing: {str(e)}"
        )


@router.get("/dashboard/processing-overview")
async def get_processing_overview(db: AsyncSession = Depends(get_db)):
    """Get comprehensive processing overview and statistics."""
    
    try:
        from sqlalchemy import select, func, and_
        from models.document import Document, DocumentProcessingJob, DocumentContent, DocumentMetadata
        
        # Get document counts by status (excluding deleted documents)
        status_counts = await db.execute(
            select(Document.status, func.count(Document.id))
            .where(Document.deleted_at.is_(None))
            .group_by(Document.status)
        )
        status_breakdown = {row[0]: row[1] for row in status_counts.all()}
        
        # Get processing job counts by status
        job_status_counts = await db.execute(
            select(DocumentProcessingJob.status, func.count(DocumentProcessingJob.id)).group_by(DocumentProcessingJob.status)
        )
        job_status_breakdown = {row[0]: row[1] for row in job_status_counts.all()}
        
        # Get recent processing jobs
        recent_jobs = await db.execute(
            select(DocumentProcessingJob).order_by(DocumentProcessingJob.created_at.desc()).limit(10)
        )
        recent_jobs_list = []
        for job in recent_jobs.scalars().all():
            recent_jobs_list.append({
                "job_id": str(job.id),
                "document_id": job.document_id,
                "job_type": job.job_type,
                "status": job.status,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None
            })
        
        # Get processing success rate
        total_jobs = sum(job_status_breakdown.values())
        successful_jobs = job_status_breakdown.get("completed", 0)
        failed_jobs = job_status_breakdown.get("failed", 0)
        success_rate = (successful_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # Get system health
        from workers.celery_app import celery_app
        active_workers = celery_app.control.inspect().active()
        worker_count = len(active_workers) if active_workers else 0
        
        return {
            "system_overview": {
                "total_documents": sum(status_breakdown.values()),
                "total_processing_jobs": total_jobs,
                "active_workers": worker_count,
                "success_rate_percentage": round(success_rate, 2)
            },
            "document_status_breakdown": status_breakdown,
            "job_status_breakdown": job_status_breakdown,
            "recent_processing_jobs": recent_jobs_list,
            "processing_metrics": {
                "successful_jobs": successful_jobs,
                "failed_jobs": failed_jobs,
                "pending_jobs": job_status_breakdown.get("pending", 0),
                "processing_jobs": job_status_breakdown.get("processing", 0)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get processing overview: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        } 


@router.post("/process-all", response_model=Dict[str, Any])
async def process_all_documents(
    db: AsyncSession = Depends(get_db)
):
    """Process all documents with 'pending' or 'uploaded' status"""
    try:
        # Check if there are any documents to process (excluding deleted documents)
        from sqlalchemy import select, func
        documents_to_process = await db.execute(
            select(func.count(Document.id)).where(
                Document.status.in_(['pending', 'uploaded']),
                Document.deleted_at.is_(None)
            )
        )
        count = documents_to_process.scalar()
        
        if count == 0:
            return {
                "message": "No documents to process",
                "task_id": None,
                "status": "NO_DOCUMENTS_TO_PROCESS",
                "pending_count": 0
            }
        
        # Trigger the Celery task
        task = process_all_pending_documents.delay()
        
        return {
            "message": "Batch processing started",
            "task_id": task.id,
            "status": "PENDING",
            "pending_count": count
        }
    except Exception as e:
        logger.error(f"Failed to start batch processing: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start batch processing: {str(e)}"
        ) 