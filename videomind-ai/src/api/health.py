"""
Health check endpoints for VideoMind AI.
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from database import get_database
from config import settings

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_database)):
    """Detailed health check including database connectivity."""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "app_name": settings.app_name,
        "version": settings.app_version,
        "services": {}
    }
    
    # Check database connectivity
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check OpenAI API key presence
    if settings.openai_api_key:
        health_status["services"]["openai"] = "configured"
    else:
        health_status["services"]["openai"] = "not_configured"
        health_status["status"] = "degraded"
    
    # Check file storage paths
    try:
        import os
        if os.path.exists(settings.temp_storage_path):
            health_status["services"]["storage"] = "healthy"
        else:
            health_status["services"]["storage"] = "temp_path_missing"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["storage"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/metrics")
async def health_metrics(db: Session = Depends(get_database)):
    """Basic metrics for monitoring."""
    
    try:
        # Count total jobs
        total_jobs = db.execute(text("SELECT COUNT(*) FROM video_jobs")).scalar()
        
        # Count jobs by status
        pending_jobs = db.execute(
            text("SELECT COUNT(*) FROM video_jobs WHERE status = 'pending'")
        ).scalar()
        
        processing_jobs = db.execute(
            text("SELECT COUNT(*) FROM video_jobs WHERE status IN ('downloading', 'transcribing', 'enhancing')")
        ).scalar()
        
        completed_jobs = db.execute(
            text("SELECT COUNT(*) FROM video_jobs WHERE status = 'completed'")
        ).scalar()
        
        failed_jobs = db.execute(
            text("SELECT COUNT(*) FROM video_jobs WHERE status = 'failed'")
        ).scalar()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "jobs": {
                "total": total_jobs or 0,
                "pending": pending_jobs or 0,
                "processing": processing_jobs or 0,
                "completed": completed_jobs or 0,
                "failed": failed_jobs or 0
            }
        }
        
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": f"Could not retrieve metrics: {str(e)}",
            "jobs": {
                "total": 0,
                "pending": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0
            }
        }