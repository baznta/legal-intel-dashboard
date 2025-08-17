"""
Dashboard routes for analytics and metadata insights.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, case, and_
from sqlalchemy.orm import selectinload
from typing import Dict, Any, List
import structlog
from datetime import datetime, timedelta

from core.database import get_db
from models.document import Document, DocumentMetadata, DocumentContent

logger = structlog.get_logger()
router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    """Get comprehensive dashboard data."""
    
    try:
        # Get all analytics data
        agreement_types = await _get_agreement_type_counts(db)
        jurisdictions = await _get_jurisdiction_counts(db)
        industries = await _get_industry_counts(db)
        geography = await _get_geography_counts(db)
        document_stats = await _get_document_statistics(db)
        recent_uploads = await _get_recent_uploads(db)
        processing_stats = await _get_processing_statistics(db)
        
        dashboard_data = {
            "agreement_types": agreement_types,
            "jurisdictions": jurisdictions,
            "industries": industries,
            "geography": geography,
            "document_statistics": document_stats,
            "recent_uploads": recent_uploads,
            "processing_statistics": processing_stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Dashboard data generated successfully")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to generate dashboard data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate dashboard data: {str(e)}"
        )


async def _get_agreement_type_counts(db: AsyncSession) -> Dict[str, int]:
    """Get counts of documents by agreement type."""
    
    query = select(
        DocumentMetadata.agreement_type,
        func.count(DocumentMetadata.id).label("count")
    ).where(
        DocumentMetadata.agreement_type.isnot(None),
        DocumentMetadata.agreement_type != ''
    ).group_by(DocumentMetadata.agreement_type)
    
    result = await db.execute(query)
    rows = result.all()
    
    agreement_counts = {}
    for row in rows:
        if row.agreement_type and row.agreement_type.strip():  # Check for non-empty strings
            agreement_counts[row.agreement_type] = row.count
    
    # Add "Unknown" category for documents without metadata
    total_docs = await _get_total_document_count(db)
    docs_with_metadata = sum(agreement_counts.values())
    if docs_with_metadata < total_docs:
        agreement_counts["Unknown"] = total_docs - docs_with_metadata
    
    return agreement_counts


async def _get_jurisdiction_counts(db: AsyncSession) -> Dict[str, int]:
    """Get counts of documents by jurisdiction."""
    
    query = select(
        DocumentMetadata.jurisdiction,
        func.count(DocumentMetadata.id).label("count")
    ).where(
        DocumentMetadata.jurisdiction.isnot(None),
        DocumentMetadata.jurisdiction != ''
    ).group_by(DocumentMetadata.jurisdiction)
    
    result = await db.execute(query)
    rows = result.all()
    
    jurisdiction_counts = {}
    for row in rows:
        if row.jurisdiction and row.jurisdiction.strip():  # Check for non-empty strings
            jurisdiction_counts[row.jurisdiction] = row.count
    
    # Add "Unknown" category
    total_docs = await _get_total_document_count(db)
    docs_with_metadata = sum(jurisdiction_counts.values())
    if docs_with_metadata < total_docs:
        jurisdiction_counts["Unknown"] = total_docs - docs_with_metadata
    
    return jurisdiction_counts


async def _get_industry_counts(db: AsyncSession) -> Dict[str, int]:
    """Get counts of documents by industry sector."""
    
    query = select(
        DocumentMetadata.industry_sector,
        func.count(DocumentMetadata.id).label("count")
    ).where(
        DocumentMetadata.industry_sector.isnot(None),
        DocumentMetadata.industry_sector != ''
    ).group_by(DocumentMetadata.industry_sector)
    
    result = await db.execute(query)
    rows = result.all()
    
    industry_counts = {}
    for row in rows:
        if row.industry_sector and row.industry_sector.strip():  # Check for non-empty strings
            industry_counts[row.industry_sector] = row.count
    
    # Add "Unknown" category
    total_docs = await _get_total_document_count(db)
    docs_with_metadata = sum(industry_counts.values())
    if docs_with_metadata < total_docs:
        industry_counts["Unknown"] = total_docs - docs_with_metadata
    
    return industry_counts


async def _get_geography_counts(db: AsyncSession) -> Dict[str, int]:
    """Get counts of documents by geography."""
    
    query = select(
        DocumentMetadata.geography,
        func.count(DocumentMetadata.geography)
    ).where(
        DocumentMetadata.geography.isnot(None),
        DocumentMetadata.geography != ''
    ).group_by(DocumentMetadata.geography)
    
    result = await db.execute(query)
    rows = result.all()
    
    geography_counts = {}
    for row in rows:
        if row.geography and row.geography.strip():  # Check for non-empty strings
            geography_counts[row.geography] = row.count
    
    # Add "Unknown" category
    total_docs = await _get_total_document_count(db)
    docs_with_metadata = sum(geography_counts.values())
    if docs_with_metadata < total_docs:
        geography_counts["Unknown"] = total_docs - docs_with_metadata
    
    return geography_counts


async def _get_document_statistics(db: AsyncSession) -> Dict[str, Any]:
    """Get overall document statistics."""
    
    # Total document count
    total_docs = await _get_total_document_count(db)
    
    # Documents by status
    status_query = select(
        Document.status,
        func.count(Document.id).label("count")
    ).group_by(Document.status)
    
    status_result = await db.execute(status_query)
    status_counts = {row.status: row.count for row in status_result.all()}
    
    # File size statistics
    size_query = select(
        func.avg(Document.file_size).label("avg_size"),
        func.min(Document.file_size).label("min_size"),
        func.max(Document.file_size).label("max_size"),
        func.sum(Document.file_size).label("total_size")
    )
    
    size_result = await db.execute(size_query)
    size_stats = size_result.first()
    
    # Upload trends (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_uploads_query = select(
        func.count(Document.id).label("count")
    ).where(Document.uploaded_at >= thirty_days_ago)
    
    recent_result = await db.execute(recent_uploads_query)
    recent_count = recent_result.scalar()
    
    return {
        "total_documents": total_docs,
        "status_breakdown": status_counts,
        "file_size_statistics": {
            "average_size_bytes": float(size_stats.avg_size) if size_stats.avg_size else 0,
            "min_size_bytes": size_stats.min_size or 0,
            "max_size_bytes": size_stats.max_size or 0,
            "total_size_bytes": size_stats.total_size or 0,
            "average_size_mb": round((size_stats.avg_size or 0) / (1024 * 1024), 2),
            "total_size_mb": round((size_stats.total_size or 0) / (1024 * 1024), 2)
        },
        "recent_uploads_30_days": recent_count,
        "upload_rate_per_day": round(recent_count / 30, 2) if recent_count > 0 else 0
    }


async def _get_recent_uploads(db: AsyncSession, limit: int = 10) -> List[Dict[str, Any]]:
    """Get recent document uploads."""
    
    # Use proper eager loading to avoid greenlet errors
    query = select(Document).options(
        selectinload(Document.document_metadata)
    ).order_by(Document.uploaded_at.desc()).limit(limit)
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    recent_uploads = []
    for doc in documents:
        upload_data = {
            "id": str(doc.id),
            "filename": doc.original_filename,
            "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
            "status": doc.status,
            "file_size": doc.file_size,
            "file_extension": doc.file_extension
        }
        
        # Add metadata if available (handle list properly)
        if hasattr(doc, 'document_metadata') and doc.document_metadata:
            # Handle both single and list cases
            metadata = doc.document_metadata[0] if isinstance(doc.document_metadata, list) else doc.document_metadata
            if metadata:
                upload_data.update({
                    "agreement_type": metadata.agreement_type,
                    "jurisdiction": metadata.jurisdiction,
                    "industry_sector": metadata.industry_sector
                })
        
        recent_uploads.append(upload_data)
    
    return recent_uploads


async def _get_processing_statistics(db: AsyncSession) -> Dict[str, Any]:
    """Get document processing statistics."""
    
    # Processing job counts by status
    job_status_query = select(
        Document.processing_started_at.isnot(None).label("has_processing"),
        func.count(Document.id).label("count")
    ).group_by(Document.processing_started_at.isnot(None))
    
    job_result = await db.execute(job_status_query)
    processing_stats = {}
    
    for row in job_result.all():
        status = "processed" if row.has_processing else "not_processed"
        processing_stats[status] = row.count
    
    # Processing success rate
    total_processed = processing_stats.get("processed", 0)
    total_docs = await _get_total_document_count(db)
    
    success_rate = (total_processed / total_docs * 100) if total_docs > 0 else 0
    
    return {
        "processing_status": processing_stats,
        "success_rate_percentage": round(success_rate, 2),
        "total_processed": total_processed,
        "total_documents": total_docs
    }


async def _get_total_document_count(db: AsyncSession) -> int:
    """Get total document count (excluding deleted documents)."""
    
    query = select(func.count(Document.id)).where(Document.deleted_at.is_(None))
    result = await db.execute(query)
    return result.scalar() or 0


@router.get("/dashboard/agreement-types")
async def get_agreement_type_analytics(db: AsyncSession = Depends(get_db)):
    """Get detailed agreement type analytics."""
    
    try:
        agreement_types = await _get_agreement_type_counts(db)
        
        # Calculate percentages
        total = sum(agreement_types.values())
        agreement_analytics = {}
        
        for agreement_type, count in agreement_types.items():
            percentage = (count / total * 100) if total > 0 else 0
            agreement_analytics[agreement_type] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
        
        return {
            "agreement_types": agreement_analytics,
            "total_documents": total,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get agreement type analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agreement type analytics: {str(e)}"
        )


@router.get("/dashboard/jurisdictions")
async def get_jurisdiction_analytics(db: AsyncSession = Depends(get_db)):
    """Get detailed jurisdiction analytics."""
    
    try:
        jurisdictions = await _get_jurisdiction_counts(db)
        
        # Calculate percentages
        total = sum(jurisdictions.values())
        jurisdiction_analytics = {}
        
        for jurisdiction, count in jurisdictions.items():
            percentage = (count / total * 100) if total > 0 else 0
            jurisdiction_analytics[jurisdiction] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
        
        return {
            "jurisdictions": jurisdiction_analytics,
            "total_documents": total,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get jurisdiction analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get jurisdiction analytics: {str(e)}"
        )


@router.get("/dashboard/trends")
async def get_upload_trends(
    days: int = 30,
    db: AsyncSession = Depends(get_db)
):
    """Get document upload trends over time."""
    
    try:
        if days > 365:
            days = 365  # Limit to 1 year
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily upload counts
        daily_uploads_query = select(
            func.date(Document.uploaded_at).label("date"),
            func.count(Document.id).label("count")
        ).where(
            and_(
                Document.uploaded_at >= start_date,
                Document.uploaded_at <= end_date
            )
        ).group_by(func.date(Document.uploaded_at)).order_by(func.date(Document.uploaded_at))
        
        result = await db.execute(daily_uploads_query)
        daily_data = result.all()
        
        # Fill in missing dates with zero counts
        trends = []
        current_date = start_date.date()
        
        for row in daily_data:
            while current_date < row.date:
                trends.append({
                    "date": current_date.isoformat(),
                    "count": 0
                })
                current_date += timedelta(days=1)
            
            trends.append({
                "date": row.date.isoformat(),
                "count": row.count
            })
            current_date += timedelta(days=1)
        
        # Fill remaining dates
        while current_date <= end_date.date():
            trends.append({
                "date": current_date.isoformat(),
                "count": 0
            })
            current_date += timedelta(days=1)
        
        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "trends": trends,
            "total_uploads": sum(trend["count"] for trend in trends),
            "average_daily_uploads": round(sum(trend["count"] for trend in trends) / len(trends), 2)
        }
        
    except Exception as e:
        logger.error(f"Failed to get upload trends: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get upload trends: {str(e)}"
        ) 