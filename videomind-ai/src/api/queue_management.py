"""
VideoMind AI: Queue Management API
Real-time monitoring and control of the Redis job queue system.
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any
from pydantic import BaseModel

from database import get_database
from services.job_queue import job_queue, JobPriority
from models.video import VideoJob, ProcessingStatus

router = APIRouter()


class QueueStatsResponse(BaseModel):
    """Queue statistics response schema."""
    available: bool
    total_queued: int
    active_jobs: int
    completed_jobs: int
    failed_jobs: int
    queues: Dict[str, int]
    performance_metrics: Dict[str, Any]


class WorkerStatusResponse(BaseModel):
    """Worker status information."""
    redis_available: bool
    recommended_workers: int
    estimated_wait_time_minutes: float
    throughput_jobs_per_hour: float


@router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_stats():
    """Get comprehensive queue statistics."""
    try:
        stats = await job_queue.get_queue_stats()
        
        # Calculate performance metrics
        total_queued = stats.get("total_queued", 0)
        active_jobs = stats.get("active_jobs", 0)
        
        # Estimated throughput (jobs per hour) - based on average 5 minutes per video
        avg_processing_time_minutes = 5
        max_concurrent_workers = 10  # Conservative estimate
        throughput_per_hour = min(active_jobs, max_concurrent_workers) * (60 / avg_processing_time_minutes)
        
        # Estimated wait time
        estimated_wait_minutes = 0
        if total_queued > 0 and throughput_per_hour > 0:
            estimated_wait_minutes = (total_queued / (throughput_per_hour / 60))
        
        performance_metrics = {
            "estimated_wait_time_minutes": round(estimated_wait_minutes, 1),
            "throughput_jobs_per_hour": round(throughput_per_hour, 1),
            "avg_processing_time_minutes": avg_processing_time_minutes,
            "queue_health": "healthy" if stats.get("available") else "unavailable"
        }
        
        return QueueStatsResponse(
            available=stats.get("available", False),
            total_queued=total_queued,
            active_jobs=active_jobs,
            completed_jobs=stats.get("completed_jobs", 0),
            failed_jobs=stats.get("failed_jobs", 0),
            queues=stats.get("queues", {}),
            performance_metrics=performance_metrics
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")


@router.get("/worker-status", response_model=WorkerStatusResponse)
async def get_worker_status():
    """Get worker recommendations and status."""
    try:
        stats = await job_queue.get_queue_stats()
        
        if not stats.get("available"):
            return WorkerStatusResponse(
                redis_available=False,
                recommended_workers=0,
                estimated_wait_time_minutes=0,
                throughput_jobs_per_hour=0
            )
        
        total_queued = stats.get("total_queued", 0)
        active_jobs = stats.get("active_jobs", 0)
        
        # Recommend workers based on queue size
        if total_queued == 0:
            recommended_workers = 1  # Minimum 1 worker
        elif total_queued <= 10:
            recommended_workers = 2
        elif total_queued <= 50:
            recommended_workers = 5
        elif total_queued <= 100:
            recommended_workers = 10
        else:
            recommended_workers = 15  # Maximum recommended
        
        # Calculate throughput and wait time
        avg_processing_time_minutes = 5
        throughput_per_hour = recommended_workers * (60 / avg_processing_time_minutes)
        
        estimated_wait_minutes = 0
        if total_queued > 0:
            estimated_wait_minutes = (total_queued / (throughput_per_hour / 60))
        
        return WorkerStatusResponse(
            redis_available=True,
            recommended_workers=recommended_workers,
            estimated_wait_time_minutes=round(estimated_wait_minutes, 1),
            throughput_jobs_per_hour=round(throughput_per_hour, 1)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get worker status: {str(e)}")


@router.post("/cleanup")
async def cleanup_expired_jobs():
    """Manually trigger cleanup of expired/stuck jobs."""
    try:
        if not job_queue.available:
            raise HTTPException(status_code=503, detail="Queue service unavailable")
        
        expired_count = await job_queue.cleanup_expired_jobs()
        
        return {
            "success": True,
            "expired_jobs_cleaned": expired_count,
            "message": f"Cleaned up {expired_count} expired jobs"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup jobs: {str(e)}")


@router.post("/jobs/{job_id}/retry")
async def retry_job(job_id: str, priority: JobPriority = JobPriority.NORMAL):
    """Manually retry a failed job with specified priority."""
    try:
        if not job_queue.available:
            raise HTTPException(status_code=503, detail="Queue service unavailable")
        
        # Queue the job for retry
        success = await job_queue.enqueue_job(
            job_id=job_id,
            priority=priority,
            metadata={"manual_retry": True}
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to queue job for retry")
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"Job queued for retry with priority {priority.value}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry job: {str(e)}")


@router.get("/jobs/stuck")
async def get_stuck_jobs(db: Session = Depends(get_database)):
    """Find jobs that might be stuck in processing."""
    try:
        from datetime import datetime, timedelta
        
        # Find jobs that have been processing for too long (> 30 minutes)
        thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
        
        stuck_jobs = db.query(VideoJob).filter(
            VideoJob.status.in_([
                ProcessingStatus.DOWNLOADING.value,
                ProcessingStatus.TRANSCRIBING.value,
                ProcessingStatus.ENHANCING.value
            ]),
            VideoJob.updated_at < thirty_minutes_ago
        ).all()
        
        stuck_job_info = []
        for job in stuck_jobs:
            time_stuck = datetime.utcnow() - job.updated_at
            stuck_job_info.append({
                "job_id": job.id,
                "youtube_url": job.youtube_url,
                "status": job.status,
                "stuck_for_minutes": int(time_stuck.total_seconds() / 60),
                "updated_at": job.updated_at.isoformat(),
                "email": job.email
            })
        
        return {
            "success": True,
            "stuck_jobs_count": len(stuck_job_info),
            "stuck_jobs": stuck_job_info,
            "recommendation": "Consider requeuing these jobs if they've been stuck for over 30 minutes"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find stuck jobs: {str(e)}")


@router.post("/jobs/stuck/requeue")
async def requeue_stuck_jobs(db: Session = Depends(get_database)):
    """Automatically requeue all stuck jobs."""
    try:
        from datetime import datetime, timedelta
        
        if not job_queue.available:
            raise HTTPException(status_code=503, detail="Queue service unavailable")
        
        # Find stuck jobs (> 30 minutes in processing state)
        thirty_minutes_ago = datetime.utcnow() - timedelta(minutes=30)
        
        stuck_jobs = db.query(VideoJob).filter(
            VideoJob.status.in_([
                ProcessingStatus.DOWNLOADING.value,
                ProcessingStatus.TRANSCRIBING.value,
                ProcessingStatus.ENHANCING.value
            ]),
            VideoJob.updated_at < thirty_minutes_ago
        ).all()
        
        requeued_count = 0
        for job in stuck_jobs:
            # Reset job status to pending
            job.status = ProcessingStatus.PENDING.value
            job.error_message = None
            
            # Requeue with high priority
            success = await job_queue.enqueue_job(
                job_id=job.id,
                priority=JobPriority.HIGH,
                metadata={
                    "requeued_from_stuck": True,
                    "original_status": job.status,
                    "stuck_duration_minutes": int((datetime.utcnow() - job.updated_at).total_seconds() / 60)
                }
            )
            
            if success:
                requeued_count += 1
        
        db.commit()
        
        return {
            "success": True,
            "stuck_jobs_found": len(stuck_jobs),
            "jobs_requeued": requeued_count,
            "message": f"Requeued {requeued_count} stuck jobs with high priority"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to requeue stuck jobs: {str(e)}")


@router.get("/health")
async def queue_health_check():
    """Simple health check for the queue system."""
    try:
        stats = await job_queue.get_queue_stats()
        
        health_status = {
            "queue_available": stats.get("available", False),
            "total_queued": stats.get("total_queued", 0),
            "active_jobs": stats.get("active_jobs", 0),
            "system_health": "healthy" if stats.get("available") else "degraded"
        }
        
        status_code = 200 if stats.get("available") else 503
        
        return health_status
        
    except Exception as e:
        return {
            "queue_available": False,
            "system_health": "error",
            "error": str(e)
        }