"""
Health check routes for monitoring system health.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import structlog
import time

from core.database import get_db, health_check as db_health_check
from core.minio_client import health_check as minio_health_check

logger = structlog.get_logger()
router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "service": "Legal Intel Dashboard API"
    }


@router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """Detailed health check with all service statuses."""
    
    start_time = time.time()
    
    # Check database health
    db_healthy = await db_health_check()
    db_check_time = time.time() - start_time
    
    # Check MinIO health
    minio_start_time = time.time()
    minio_healthy = minio_health_check()
    minio_check_time = time.time() - minio_start_time
    
    # Overall health
    overall_healthy = db_healthy and minio_healthy
    
    # Response
    response = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": time.time(),
        "overall_check_time": time.time() - start_time,
        "services": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "check_time": db_check_time,
                "endpoint": "postgresql://legal_user:***@postgres:5432/legal_intel"
            },
            "storage": {
                "status": "healthy" if minio_healthy else "unhealthy",
                "check_time": minio_check_time,
                "endpoint": f"http://minio:9000"
            }
        }
    }
    
    # Log health check
    if overall_healthy:
        logger.info("Health check passed", response=response)
    else:
        logger.warning("Health check failed", response=response)
    
    return response


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes readiness probe."""
    
    # Check if all services are ready
    db_ready = await db_health_check()
    minio_ready = minio_health_check()
    
    ready = db_ready and minio_ready
    
    if ready:
        return {"status": "ready"}
    else:
        return {"status": "not_ready"}


@router.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes liveness probe."""
    
    # Simple check - if we can respond, we're alive
    return {"status": "alive"} 