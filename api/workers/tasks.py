"""
Celery tasks for document processing.
"""

from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import structlog
import asyncio
from typing import Dict, Any
from datetime import datetime
from sqlalchemy import select

from workers.celery_app import celery_app
from core.config import settings
from models.document import Document, DocumentProcessingJob
from services.document_service import DocumentService
from services.llm_service import LLMService

logger = structlog.get_logger()

# Create async engine for tasks with proper connection pooling
engine = create_async_engine(
    settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False
)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


@celery_app.task(bind=True)
def process_document(self, document_id: str):
    """Process uploaded document."""
    
    task_id = self.request.id
    logger.info(f"Starting document processing task: {task_id} for document: {document_id}")
    
    try:
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"current": 0, "total": 100, "status": "Processing document"}
        )
        
        # Run async function with proper event loop handling
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(_process_document_async(document_id, task_id))
        finally:
            loop.close()
        
        logger.info(f"Document processing completed: {document_id}")
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Document processing failed: {e}", document_id=document_id)
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True)
def extract_metadata(self, document_id: str):
    """Extract metadata from document."""
    
    task_id = self.request.id
    logger.info(f"Starting metadata extraction task: {task_id} for document: {document_id}")
    
    try:
        # Run async function with proper event loop handling
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(_extract_metadata_async(document_id, task_id))
        finally:
            loop.close()
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}", document_id=document_id)
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True)
def extract_text(self, document_id: str):
    """Extract text from document."""
    
    task_id = self.request.id
    logger.info(f"Starting text extraction task: {task_id} for document: {document_id}")
    
    try:
        # Run async function with proper event loop handling
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(_extract_text_async(document_id, task_id))
        finally:
            loop.close()
        return {"status": "success", "document_id": document_id}
        
    except Exception as e:
        logger.error(f"Text extraction failed: {e}", document_id=document_id)
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True)
def process_all_pending_documents(self):
    """Process all documents with 'pending' or 'uploaded' status automatically"""
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Starting batch processing'})
        
        # Create a new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_process_all_pending_documents_async(self))
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Failed to process all pending documents: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(bind=True)
def auto_process_pending_documents(self):
    """Automatically process pending documents (runs periodically)"""
    try:
        logger.info("Auto-processing pending documents...")
        
        # Create a new event loop for this task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(_process_all_pending_documents_async())
            logger.info(f"Auto-processing completed: {result}")
            return result
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"Auto-processing failed: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

async def _process_all_pending_documents_async(task=None):
    """Async function to process all pending and uploaded documents with progress updates"""
    # Create engine for this task
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
    
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autoflush=False
    )
    
    db = async_session()
    
    try:
        # Find all pending and uploaded documents (excluding deleted documents)
        stmt = select(Document).where(
            Document.status.in_(['pending', 'uploaded']),
            Document.deleted_at.is_(None)
        )
        result = await db.execute(stmt)
        documents_to_process = result.scalars().all()
        
        if not documents_to_process:
            logger.info("No documents to process")
            return {"message": "No documents to process", "processed": 0}
        
        logger.info(f"Found {len(documents_to_process)} documents to process")
        
        processed_count = 0
        failed_count = 0
        
        # Update task progress
        if task:
            task.update_state(
                state='PROGRESS', 
                meta={
                    'status': f'Processing {len(documents_to_process)} documents',
                    'current': 0,
                    'total': len(documents_to_process),
                    'processed': 0,
                    'failed': 0
                }
            )
        
        for i, doc in enumerate(documents_to_process):
            try:
                logger.info(f"Processing document: {doc.original_filename} (ID: {doc.id})")
                
                # Update status to processing
                doc.status = 'processing'
                doc.processing_started_at = datetime.utcnow()
                await db.commit()
                await db.refresh(doc)
                
                # Process the document using the existing service
                document_service = DocumentService()
                
                # Step 1: Extract text
                logger.info(f"Extracting text from {doc.original_filename}")
                content = await document_service.extract_text_from_document(db, doc.id)
                if not content:
                    raise Exception("Failed to extract text from document")
                
                # Step 2: Extract metadata
                logger.info(f"Extracting metadata from {doc.original_filename}")
                metadata = await document_service.extract_metadata_from_document(db, doc.id)
                if not metadata:
                    logger.warning(f"Failed to extract metadata from document: {doc.id}")
                
                # Update status to completed
                doc.status = 'completed'
                doc.processing_completed_at = datetime.utcnow()
                await db.commit()
                await db.refresh(doc)
                
                processed_count += 1
                logger.info(f"Successfully processed document: {doc.original_filename}")
                
                # Update task progress
                if task:
                    task.update_state(
                        state='PROGRESS', 
                        meta={
                            'status': f'Processed {doc.original_filename}',
                            'current': i + 1,
                            'total': len(documents_to_process),
                            'processed': processed_count,
                            'failed': failed_count
                        }
                    )
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to process document {doc.original_filename}: {str(e)}")
                
                # Mark document as failed
                doc.status = 'failed'
                doc.processing_error = str(e)
                await db.commit()
                await db.refresh(doc)
                
                # Update task progress
                if task:
                    task.update_state(
                        state='PROGRESS', 
                        meta={
                            'status': f'Failed to process {doc.original_filename}',
                            'current': i + 1,
                            'total': len(documents_to_process),
                            'processed': processed_count,
                            'failed': failed_count
                        }
                    )
                
                # Continue with next document
                continue
        
        # Final progress update
        if task:
            task.update_state(
                state='SUCCESS', 
                meta={
                    'status': 'Batch processing completed',
                    'current': len(documents_to_process),
                    'total': len(documents_to_process),
                    'processed': processed_count,
                    'failed': failed_count
                }
            )
        
        return {
            "message": f"Batch processing completed. Processed: {processed_count}, Failed: {failed_count}",
            "processed": processed_count,
            "failed": failed_count,
            "total": len(documents_to_process)
        }
        
    finally:
        await db.close()
        await engine.dispose()

async def _process_document_async(document_id: str, task_id: str):
    """Async document processing with detailed status tracking."""
    
    db = None
    try:
        db = AsyncSessionLocal()
        document_service = DocumentService()
        
        # Get the document to update its status
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()
        if not document:
            raise Exception(f"Document {document_id} not found")
        
        # Create processing job first
        job = await document_service.create_processing_job(
            db, document_id, "document_processing"
        )
        
        # Update document status to processing
        document.status = 'processing'
        document.processing_started_at = datetime.utcnow()
        await db.commit()
        await db.refresh(document)
        
        # Update job status to processing
        await document_service.update_processing_job(db, job.id, "processing")
        
        # Step 1: Extract text from document
        logger.info(f"Extracting text from document: {document_id}")
        content = await document_service.extract_text_from_document(db, document_id)
        if not content:
            raise Exception("Failed to extract text from document")
        
        # Step 2: Extract metadata from document
        logger.info(f"Extracting metadata from document: {document_id}")
        metadata = await document_service.extract_metadata_from_document(db, document_id)
        if not metadata:
            logger.warning(f"Failed to extract metadata from document: {document_id}")
        
        # Update document status to completed
        document.status = 'completed'
        document.processing_completed_at = datetime.utcnow()
        await db.commit()
        await db.refresh(document)
        
        # Update job status to completed
        await document_service.update_processing_job(
            db, job.id, "completed", {"task_id": task_id, "content_id": str(content.id)}
        )
        
        logger.info(f"Document processing completed successfully: {document_id}")
        
    except Exception as e:
        error_msg = f"Document processing failed: {str(e)}"
        logger.error(error_msg)
        
        # Update document status to failed
        if db and 'document' in locals():
            try:
                document.status = 'failed'
                document.processing_error = error_msg
                await db.commit()
                await db.refresh(document)
            except Exception as update_error:
                logger.error(f"Failed to update document status: {update_error}")
        
        # Try to update job status to failed
        if db and 'job' in locals():
            try:
                await document_service.update_processing_job(
                    db, job.id, "failed", error_message=error_msg
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {update_error}")
        
        raise
        
    finally:
        if db:
            try:
                await db.close()
            except Exception as e:
                logger.warning(f"Error closing database session: {e}")


async def _extract_metadata_async(document_id: str, task_id: str):
    """Async metadata extraction."""
    
    db = None
    try:
        db = AsyncSessionLocal()
        document_service = DocumentService()
        
        # Get document
        document = await document_service.get_document(db, document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        # Create processing job
        job = await document_service.create_processing_job(
            db, document_id, "metadata_extraction"
        )
        
        try:
            await document_service.update_processing_job(db, job.id, "processing")
            
            # Extract metadata from document
            metadata = await document_service.extract_metadata_from_document(db, document_id)
            if not metadata:
                raise Exception("Failed to extract metadata from document")
            
            await document_service.update_processing_job(
                db, job.id, "completed", {"metadata_id": str(metadata.id)}
            )
            
        except Exception as e:
            await document_service.update_processing_job(
                db, job.id, "failed", error_message=str(e)
            )
            raise
            
    except Exception as e:
        logger.error(f"Error in _extract_metadata_async: {e}")
        raise
    finally:
        if db:
            try:
                await db.close()
            except Exception as e:
                logger.warning(f"Error closing database session: {e}")


async def _extract_text_async(document_id: str, task_id: str):
    """Async text extraction."""
    
    db = None
    try:
        db = AsyncSessionLocal()
        document_service = DocumentService()
        
        # Get document
        document = await document_service.get_document(db, document_id)
        if not document:
            raise ValueError(f"Document not found: {document_id}")
        
        # Create processing job
        job = await document_service.create_processing_job(
            db, document_id, "text_extraction"
        )
        
        try:
            await document_service.update_processing_job(db, job.id, "processing")
            
            # Extract text from document
            content = await document_service.extract_text_from_document(db, document_id)
            if not content:
                raise Exception("Failed to extract text from document")
            
            await document_service.update_processing_job(
                db, job.id, "completed", {"content_id": str(content.id)}
            )
            
        except Exception as e:
            await document_service.update_processing_job(
                db, job.id, "failed", error_message=str(e)
            )
            raise
            
    except Exception as e:
        logger.error(f"Error in _extract_text_async: {e}")
        raise
    finally:
        if db:
            try:
                await db.close()
            except Exception as e:
                logger.warning(f"Error closing database session: {e}") 