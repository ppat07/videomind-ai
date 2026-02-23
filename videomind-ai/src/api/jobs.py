"""
VideoMind AI: Job Management & Recovery System
Built to handle stuck downloads, failed jobs, and system reliability at scale.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from database import get_database
from models.video import VideoJob, ProcessingStatus
from services.youtube_service import youtube_service
from services.transcription_service import transcription_service
from utils.helpers import generate_job_id

router = APIRouter()


class JobStats(BaseModel):
    """System-wide job statistics."""
    total_jobs: int
    completed: int
    failed: int
    pending: int
    downloading: int
    transcribing: int
    enhancing: int
    stuck_downloads: int
    recent_failures: int


class JobSummary(BaseModel):
    """Lightweight job information."""
    id: str
    youtube_url: str
    status: str
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    retry_count: int = 0


class RetryResult(BaseModel):
    """Result of retry operation."""
    job_id: str
    success: bool
    message: str
    new_status: str


class BulkRetryResult(BaseModel):
    """Result of bulk retry operation."""
    total_attempted: int
    successful_retries: int
    failed_retries: int
    details: List[RetryResult]


@router.get("/jobs/stats", response_model=JobStats)
async def get_job_statistics(db: Session = Depends(get_database)):
    """Get comprehensive job statistics for system health monitoring."""
    
    # Basic counts by status
    total_jobs = db.query(VideoJob).count()
    completed = db.query(VideoJob).filter(VideoJob.status == ProcessingStatus.COMPLETED.value).count()
    failed = db.query(VideoJob).filter(VideoJob.status == ProcessingStatus.FAILED.value).count()
    pending = db.query(VideoJob).filter(VideoJob.status == ProcessingStatus.PENDING.value).count()
    downloading = db.query(VideoJob).filter(VideoJob.status == ProcessingStatus.DOWNLOADING.value).count()
    transcribing = db.query(VideoJob).filter(VideoJob.status == ProcessingStatus.TRANSCRIBING.value).count()
    enhancing = db.query(VideoJob).filter(VideoJob.status == ProcessingStatus.ENHANCING.value).count()
    
    # Advanced health checks
    # Stuck downloads: downloading status for >30 minutes
    thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
    stuck_downloads = db.query(VideoJob).filter(
        and_(
            VideoJob.status == ProcessingStatus.DOWNLOADING.value,
            VideoJob.updated_at < thirty_minutes_ago
        )
    ).count()
    
    # Recent failures: failed in last 24 hours
    twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
    recent_failures = db.query(VideoJob).filter(
        and_(
            VideoJob.status == ProcessingStatus.FAILED.value,
            VideoJob.updated_at > twenty_four_hours_ago
        )
    ).count()
    
    return JobStats(
        total_jobs=total_jobs,
        completed=completed,
        failed=failed,
        pending=pending,
        downloading=downloading,
        transcribing=transcribing,
        enhancing=enhancing,
        stuck_downloads=stuck_downloads,
        recent_failures=recent_failures
    )


@router.get("/jobs/failed", response_model=List[JobSummary])
async def get_failed_jobs(
    limit: int = 20,
    db: Session = Depends(get_database)
):
    """Get list of failed jobs for review and retry."""
    
    failed_jobs = db.query(VideoJob).filter(
        VideoJob.status == ProcessingStatus.FAILED.value
    ).order_by(desc(VideoJob.updated_at)).limit(limit).all()
    
    return [
        JobSummary(
            id=job.id,
            youtube_url=job.youtube_url,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error_message=job.error_message,
            retry_count=job.retry_count or 0
        )
        for job in failed_jobs
    ]


@router.get("/jobs/stuck", response_model=List[JobSummary])
async def get_stuck_jobs(db: Session = Depends(get_database)):
    """Get jobs that appear to be stuck in processing states."""
    
    # Jobs stuck in downloading (>30 minutes)
    # Jobs stuck in transcribing/enhancing (>15 minutes)
    thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
    fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
    
    stuck_jobs = db.query(VideoJob).filter(
        or_(
            and_(
                VideoJob.status == ProcessingStatus.DOWNLOADING.value,
                VideoJob.updated_at < thirty_minutes_ago
            ),
            and_(
                VideoJob.status.in_([
                    ProcessingStatus.TRANSCRIBING.value,
                    ProcessingStatus.ENHANCING.value
                ]),
                VideoJob.updated_at < fifteen_minutes_ago
            )
        )
    ).order_by(desc(VideoJob.updated_at)).all()
    
    return [
        JobSummary(
            id=job.id,
            youtube_url=job.youtube_url,
            status=job.status,
            created_at=job.created_at,
            updated_at=job.updated_at,
            error_message=job.error_message,
            retry_count=job.retry_count or 0
        )
        for job in stuck_jobs
    ]


@router.post("/jobs/{job_id}/retry", response_model=RetryResult)
async def retry_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """Retry a failed or stuck job."""
    
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Only retry failed jobs or stuck jobs
    if job.status not in [
        ProcessingStatus.FAILED.value,
        ProcessingStatus.DOWNLOADING.value,
        ProcessingStatus.TRANSCRIBING.value,
        ProcessingStatus.ENHANCING.value
    ]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot retry job with status: {job.status}"
        )
    
    # Increment retry count
    job.retry_count = (job.retry_count or 0) + 1
    
    # Reset job to pending for retry
    job.status = ProcessingStatus.PENDING.value
    job.error_message = None
    job.updated_at = datetime.utcnow()
    
    # Clear any partial data to ensure clean retry
    if job.status == ProcessingStatus.FAILED.value:
        job.audio_file_path = None
        job.transcript = None
        job.ai_enhanced = None
    
    db.commit()
    
    # Queue for background processing
    from api.process import process_video_job_background
    background_tasks.add_task(process_video_job_background, job.id, db)
    
    return RetryResult(
        job_id=job_id,
        success=True,
        message=f"Job queued for retry (attempt #{job.retry_count})",
        new_status=job.status
    )


@router.post("/jobs/retry-failed", response_model=BulkRetryResult)
async def retry_all_failed_jobs(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database),
    max_retries: int = 3
):
    """Retry all failed jobs that haven't exceeded max retry attempts."""
    
    # Get failed jobs that haven't exceeded retry limit
    failed_jobs = db.query(VideoJob).filter(
        and_(
            VideoJob.status == ProcessingStatus.FAILED.value,
            or_(
                VideoJob.retry_count.is_(None),
                VideoJob.retry_count < max_retries
            )
        )
    ).all()
    
    results = []
    successful_retries = 0
    
    for job in failed_jobs:
        try:
            # Increment retry count
            job.retry_count = (job.retry_count or 0) + 1
            
            # Reset for retry
            job.status = ProcessingStatus.PENDING.value
            job.error_message = None
            job.updated_at = datetime.utcnow()
            job.audio_file_path = None
            job.transcript = None
            job.ai_enhanced = None
            
            db.commit()
            
            # Queue for processing
            from api.process import process_video_job_background
            background_tasks.add_task(process_video_job_background, job.id, db)
            
            results.append(RetryResult(
                job_id=job.id,
                success=True,
                message=f"Queued for retry (attempt #{job.retry_count})",
                new_status=job.status
            ))
            successful_retries += 1
            
        except Exception as e:
            results.append(RetryResult(
                job_id=job.id,
                success=False,
                message=f"Failed to queue retry: {str(e)}",
                new_status=job.status
            ))
    
    return BulkRetryResult(
        total_attempted=len(failed_jobs),
        successful_retries=successful_retries,
        failed_retries=len(failed_jobs) - successful_retries,
        details=results
    )


@router.post("/jobs/cleanup-stuck", response_model=BulkRetryResult)
async def cleanup_stuck_jobs(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """Reset stuck jobs back to pending for retry."""
    
    thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
    fifteen_minutes_ago = datetime.utcnow() - timedelta(minutes=15)
    
    # Find stuck jobs
    stuck_jobs = db.query(VideoJob).filter(
        or_(
            and_(
                VideoJob.status == ProcessingStatus.DOWNLOADING.value,
                VideoJob.updated_at < thirty_minutes_ago
            ),
            and_(
                VideoJob.status.in_([
                    ProcessingStatus.TRANSCRIBING.value,
                    ProcessingStatus.ENHANCING.value
                ]),
                VideoJob.updated_at < fifteen_minutes_ago
            )
        )
    ).all()
    
    results = []
    successful_resets = 0
    
    for job in stuck_jobs:
        try:
            # Increment retry count and reset status
            job.retry_count = (job.retry_count or 0) + 1
            old_status = job.status
            job.status = ProcessingStatus.PENDING.value
            job.error_message = f"Reset from stuck {old_status} status"
            job.updated_at = datetime.utcnow()
            
            db.commit()
            
            # Queue for processing
            from api.process import process_video_job_background
            background_tasks.add_task(process_video_job_background, job.id, db)
            
            results.append(RetryResult(
                job_id=job.id,
                success=True,
                message=f"Reset from stuck {old_status} status",
                new_status=job.status
            ))
            successful_resets += 1
            
        except Exception as e:
            results.append(RetryResult(
                job_id=job.id,
                success=False,
                message=f"Failed to reset: {str(e)}",
                new_status=job.status
            ))
    
    return BulkRetryResult(
        total_attempted=len(stuck_jobs),
        successful_retries=successful_resets,
        failed_retries=len(stuck_jobs) - successful_resets,
        details=results
    )


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: str,
    db: Session = Depends(get_database)
):
    """Delete a job and its associated files (use with caution)."""
    
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Clean up any temp files if they exist
    if job.audio_file_path:
        try:
            import os
            if os.path.exists(job.audio_file_path):
                os.remove(job.audio_file_path)
        except Exception:
            pass  # Non-critical cleanup failure
    
    db.delete(job)
    db.commit()
    
    return {"success": True, "message": f"Job {job_id} deleted"}


@router.get("/jobs/health-check")
async def job_system_health_check(db: Session = Depends(get_database)):
    """Comprehensive health check for the job processing system."""
    
    stats = await get_job_statistics(db)
    
    # Calculate health scores
    total_active = stats.pending + stats.downloading + stats.transcribing + stats.enhancing
    success_rate = stats.completed / max(1, stats.total_jobs) * 100
    stuck_rate = stats.stuck_downloads / max(1, total_active) * 100 if total_active > 0 else 0
    
    health_status = "healthy"
    warnings = []
    
    # Health checks
    if stuck_rate > 20:
        health_status = "warning"
        warnings.append(f"High stuck job rate: {stuck_rate:.1f}%")
    
    if success_rate < 80:
        health_status = "critical"
        warnings.append(f"Low success rate: {success_rate:.1f}%")
    
    if stats.recent_failures > 10:
        health_status = "warning"
        warnings.append(f"High recent failure count: {stats.recent_failures}")
    
    return {
        "status": health_status,
        "success_rate": f"{success_rate:.1f}%",
        "stuck_rate": f"{stuck_rate:.1f}%",
        "warnings": warnings,
        "stats": stats,
        "recommendations": [
            "Run /jobs/cleanup-stuck to reset stuck jobs" if stats.stuck_downloads > 0 else None,
            "Run /jobs/retry-failed to retry recent failures" if stats.recent_failures > 5 else None,
            "Consider investigating error patterns in failed jobs" if stats.failed > 10 else None
        ]
    }