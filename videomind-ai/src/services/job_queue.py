"""
VideoMind AI: High-Scale Job Queue System
Redis-based distributed queue for processing 100+ concurrent video jobs.
"""
import redis
import json
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from models.video import VideoJob, ProcessingStatus


class JobPriority(str, Enum):
    """Job processing priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class QueueJob(BaseModel):
    """Job data for queue processing."""
    job_id: str
    job_type: str = "video_processing"
    priority: JobPriority = JobPriority.NORMAL
    queued_at: float
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: int = 1800  # 30 minutes
    metadata: Dict[str, Any] = {}


class JobQueueService:
    """Redis-based job queue for high-scale video processing."""
    
    def __init__(self):
        """Initialize Redis connection and queue configuration."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            self.available = True
            print("✅ Redis connection established for job queue")
        except Exception as e:
            print(f"⚠️ Redis not available, falling back to direct processing: {e}")
            self.redis_client = None
            self.available = False
    
    # Queue names for different priority levels
    QUEUE_URGENT = "queue:video:urgent"
    QUEUE_HIGH = "queue:video:high"
    QUEUE_NORMAL = "queue:video:normal"
    QUEUE_LOW = "queue:video:low"
    QUEUE_RETRY = "queue:video:retry"
    
    # Active jobs tracking
    ACTIVE_JOBS = "active_jobs"
    FAILED_JOBS = "failed_jobs"
    COMPLETED_JOBS = "completed_jobs"
    JOB_METADATA = "job_meta"
    
    def get_queue_name(self, priority: JobPriority) -> str:
        """Get Redis queue name for priority level."""
        queue_map = {
            JobPriority.URGENT: self.QUEUE_URGENT,
            JobPriority.HIGH: self.QUEUE_HIGH,
            JobPriority.NORMAL: self.QUEUE_NORMAL,
            JobPriority.LOW: self.QUEUE_LOW
        }
        return queue_map.get(priority, self.QUEUE_NORMAL)
    
    async def enqueue_job(
        self, 
        job_id: str, 
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: int = 1800,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add job to processing queue.
        
        Args:
            job_id: Unique job identifier
            priority: Job processing priority
            max_retries: Maximum retry attempts
            timeout_seconds: Job timeout (default 30 minutes)
            metadata: Additional job metadata
            
        Returns:
            bool: Success status
        """
        if not self.available:
            return False
        
        try:
            queue_job = QueueJob(
                job_id=job_id,
                priority=priority,
                queued_at=time.time(),
                max_retries=max_retries,
                timeout_seconds=timeout_seconds,
                metadata=metadata or {}
            )
            
            queue_name = self.get_queue_name(priority)
            
            # Add to queue with timestamp for FIFO within priority
            self.redis_client.zadd(
                queue_name,
                {json.dumps(queue_job.dict()): time.time()}
            )
            
            # Store job metadata
            self.redis_client.hset(
                f"{self.JOB_METADATA}:{job_id}",
                mapping=queue_job.dict()
            )
            
            # Set expiration for metadata (24 hours)
            self.redis_client.expire(f"{self.JOB_METADATA}:{job_id}", 86400)
            
            print(f"📤 Job {job_id} enqueued with priority {priority.value}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to enqueue job {job_id}: {e}")
            return False
    
    async def dequeue_job(self, timeout: int = 5) -> Optional[QueueJob]:
        """
        Get next job from highest priority queue.
        
        Args:
            timeout: Blocking timeout in seconds
            
        Returns:
            QueueJob or None if no jobs available
        """
        if not self.available:
            return None
        
        try:
            # Check queues in priority order
            queue_priority_order = [
                self.QUEUE_URGENT,
                self.QUEUE_HIGH,
                self.QUEUE_NORMAL,
                self.QUEUE_LOW,
                self.QUEUE_RETRY
            ]
            
            for queue_name in queue_priority_order:
                # Get oldest job from this priority queue (FIFO)
                result = self.redis_client.bzpopmin(queue_name, timeout=timeout)
                
                if result:
                    _, job_data, _ = result
                    queue_job = QueueJob(**json.loads(job_data))
                    
                    # Move to active jobs
                    self.redis_client.hset(
                        self.ACTIVE_JOBS,
                        queue_job.job_id,
                        json.dumps({
                            "started_at": time.time(),
                            "worker_id": f"worker_{time.time()}",
                            "timeout_at": time.time() + queue_job.timeout_seconds
                        })
                    )
                    
                    print(f"📥 Dequeued job {queue_job.job_id} from {queue_name}")
                    return queue_job
            
            return None
            
        except Exception as e:
            print(f"❌ Failed to dequeue job: {e}")
            return None
    
    async def mark_job_completed(self, job_id: str, result: Dict[str, Any] = None) -> bool:
        """Mark job as completed and clean up."""
        if not self.available:
            return False
        
        try:
            # Remove from active jobs
            self.redis_client.hdel(self.ACTIVE_JOBS, job_id)
            
            # Add to completed jobs with result
            self.redis_client.hset(
                self.COMPLETED_JOBS,
                job_id,
                json.dumps({
                    "completed_at": time.time(),
                    "result": result or {}
                })
            )
            
            # Clean up metadata after 1 hour
            self.redis_client.expire(f"{self.JOB_METADATA}:{job_id}", 3600)
            
            print(f"✅ Job {job_id} marked as completed")
            return True
            
        except Exception as e:
            print(f"❌ Failed to mark job {job_id} as completed: {e}")
            return False
    
    async def mark_job_failed(self, job_id: str, error: str, retry: bool = True) -> bool:
        """Mark job as failed and optionally retry."""
        if not self.available:
            return False
        
        try:
            # Get job metadata
            job_meta = self.redis_client.hgetall(f"{self.JOB_METADATA}:{job_id}")
            if not job_meta:
                print(f"⚠️ No metadata found for job {job_id}")
                return False
            
            retry_count = int(job_meta.get('retry_count', 0))
            max_retries = int(job_meta.get('max_retries', 3))
            
            # Remove from active jobs
            self.redis_client.hdel(self.ACTIVE_JOBS, job_id)
            
            if retry and retry_count < max_retries:
                # Retry job with increased retry count
                retry_count += 1
                job_meta['retry_count'] = str(retry_count)
                
                # Update metadata
                self.redis_client.hset(f"{self.JOB_METADATA}:{job_id}", mapping=job_meta)
                
                # Add to retry queue with delay (exponential backoff)
                delay = min(2 ** retry_count * 60, 1800)  # Max 30 minutes
                retry_time = time.time() + delay
                
                self.redis_client.zadd(
                    self.QUEUE_RETRY,
                    {json.dumps(job_meta): retry_time}
                )
                
                print(f"🔄 Job {job_id} scheduled for retry #{retry_count} in {delay}s")
                
                # Update database status
                self._update_db_job_status(job_id, ProcessingStatus.PENDING, f"Retry #{retry_count} scheduled")
                
            else:
                # Mark as permanently failed
                self.redis_client.hset(
                    self.FAILED_JOBS,
                    job_id,
                    json.dumps({
                        "failed_at": time.time(),
                        "error": error,
                        "retry_count": retry_count
                    })
                )
                
                print(f"❌ Job {job_id} permanently failed after {retry_count} retries")
                
                # Update database status
                self._update_db_job_status(job_id, ProcessingStatus.FAILED, error)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to handle job failure {job_id}: {e}")
            return False
    
    def _update_db_job_status(self, job_id: str, status: ProcessingStatus, error_msg: str = None):
        """Update job status in database."""
        try:
            db = SessionLocal()
            job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
            if job:
                job.status = status.value
                if error_msg:
                    job.error_message = error_msg
                if status == ProcessingStatus.FAILED:
                    job.completed_at = datetime.utcnow()
                db.commit()
        except Exception as e:
            print(f"⚠️ Failed to update database for job {job_id}: {e}")
        finally:
            db.close()
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics."""
        if not self.available:
            return {"available": False}
        
        try:
            stats = {
                "available": True,
                "queues": {
                    "urgent": self.redis_client.zcard(self.QUEUE_URGENT),
                    "high": self.redis_client.zcard(self.QUEUE_HIGH),
                    "normal": self.redis_client.zcard(self.QUEUE_NORMAL),
                    "low": self.redis_client.zcard(self.QUEUE_LOW),
                    "retry": self.redis_client.zcard(self.QUEUE_RETRY),
                },
                "active_jobs": self.redis_client.hlen(self.ACTIVE_JOBS),
                "completed_jobs": self.redis_client.hlen(self.COMPLETED_JOBS),
                "failed_jobs": self.redis_client.hlen(self.FAILED_JOBS),
                "total_queued": sum([
                    self.redis_client.zcard(self.QUEUE_URGENT),
                    self.redis_client.zcard(self.QUEUE_HIGH),
                    self.redis_client.zcard(self.QUEUE_NORMAL),
                    self.redis_client.zcard(self.QUEUE_LOW),
                    self.redis_client.zcard(self.QUEUE_RETRY),
                ])
            }
            
            return stats
            
        except Exception as e:
            print(f"❌ Failed to get queue stats: {e}")
            return {"available": False, "error": str(e)}
    
    async def cleanup_expired_jobs(self) -> int:
        """Clean up timed out jobs from active queue."""
        if not self.available:
            return 0
        
        try:
            current_time = time.time()
            active_jobs = self.redis_client.hgetall(self.ACTIVE_JOBS)
            expired_count = 0
            
            for job_id, job_data in active_jobs.items():
                try:
                    active_data = json.loads(job_data)
                    timeout_at = active_data.get("timeout_at", current_time + 3600)
                    
                    if current_time > timeout_at:
                        # Job has expired
                        await self.mark_job_failed(
                            job_id, 
                            "Job timeout - exceeded maximum processing time", 
                            retry=True
                        )
                        expired_count += 1
                        print(f"⏰ Expired job {job_id} moved to retry queue")
                        
                except json.JSONDecodeError:
                    # Invalid JSON, remove the job
                    self.redis_client.hdel(self.ACTIVE_JOBS, job_id)
                    expired_count += 1
            
            if expired_count > 0:
                print(f"🧹 Cleaned up {expired_count} expired jobs")
            
            return expired_count
            
        except Exception as e:
            print(f"❌ Failed to cleanup expired jobs: {e}")
            return 0


# Global job queue service instance
job_queue = JobQueueService()