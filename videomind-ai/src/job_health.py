"""
Job Health Monitoring API
Real-time system health and batch processing for customers
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
import json
import asyncio

router = APIRouter()

class BatchProcessRequest(BaseModel):
    urls: str  # Newline-separated URLs
    email: EmailStr
    enhancement_level: str = "standard"

# Simulated job counts for demonstration
# In production, these would query the actual job database
def get_job_count(status: str) -> int:
    """Get count of jobs in specific status"""
    # Mock data for demonstration
    mock_counts = {
        "pending": 12,
        "downloading": 3,
        "transcribing": 8,
        "enhancing": 5,
        "completed": 1847,
        "failed": 23
    }
    return mock_counts.get(status, 0)

def calculate_avg_processing_time() -> str:
    """Calculate average processing time"""
    return "2.3 min"

def calculate_success_rate() -> str:
    """Calculate success rate percentage"""
    total = get_job_count("completed") + get_job_count("failed")
    if total == 0:
        return "100%"
    success_rate = (get_job_count("completed") / total) * 100
    return f"{success_rate:.1f}%"

def get_videos_processed_today() -> int:
    """Get number of videos processed today"""
    return 847

def get_api_uptime() -> str:
    """Get API uptime percentage"""
    return "99.9%"

def get_current_processing_queue() -> List[Dict[str, Any]]:
    """Get list of currently processing videos"""
    # Mock queue for demonstration
    return [
        {
            "title": "OpenClaw Setup Tutorial: Complete Guide",
            "url": "https://www.youtube.com/watch?v=fcZMmP5dsl4",
            "status": "transcribing",
            "started_at": "2 min ago"
        },
        {
            "title": "Advanced OpenClaw Configuration",
            "url": "https://www.youtube.com/watch?v=Zo7Putdga_4", 
            "status": "downloading",
            "started_at": "30 sec ago"
        },
        {
            "title": "OpenClaw Security Best Practices",
            "url": "https://www.youtube.com/watch?v=YCD2FSvj35I",
            "status": "enhancing", 
            "started_at": "5 min ago"
        }
    ]

def create_batch_job(urls: List[str], email: str, enhancement_level: str) -> str:
    """Create a new batch processing job"""
    import time
    batch_id = f"batch_{int(time.time())}"
    # In production, this would create database records
    return batch_id

def estimate_completion_time(video_count: int) -> str:
    """Estimate when batch will complete"""
    avg_time_per_video = 2.3  # minutes
    total_minutes = video_count * avg_time_per_video
    
    if total_minutes < 60:
        return f"~{int(total_minutes)} minutes"
    else:
        hours = int(total_minutes // 60)
        minutes = int(total_minutes % 60)
        return f"~{hours}h {minutes}m"

@router.get("/api/job-health")
async def get_job_health():
    """Get current system health and job status"""
    
    # Get job status counts
    job_counts = {
        "pending": get_job_count("pending"),
        "downloading": get_job_count("downloading"), 
        "transcribing": get_job_count("transcribing"),
        "enhancing": get_job_count("enhancing"),
        "completed": get_job_count("completed"),
        "failed": get_job_count("failed")
    }
    
    # Calculate performance metrics
    metrics = {
        "avg_time": calculate_avg_processing_time(),
        "success_rate": calculate_success_rate(),
        "videos_today": get_videos_processed_today(),
        "uptime": get_api_uptime()
    }
    
    # Get current processing queue
    queue = get_current_processing_queue()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        **job_counts,
        "metrics": metrics,
        "queue": queue
    }

@router.post("/api/batch-process")
async def batch_process_videos(request: BatchProcessRequest):
    """Process multiple videos in batch"""
    
    # Parse URLs from newline-separated string
    urls = [url.strip() for url in request.urls.split('\n') if url.strip()]
    
    if not urls:
        raise HTTPException(status_code=400, detail="No valid URLs provided")
    
    if len(urls) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 videos per batch")
    
    # Validate URLs (basic check)
    invalid_urls = []
    for url in urls:
        if not url.startswith(('http://', 'https://')):
            invalid_urls.append(url)
    
    if invalid_urls:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid URLs found: {', '.join(invalid_urls[:3])}"
        )
    
    # Create batch job
    batch_id = create_batch_job(
        urls=urls,
        email=request.email,
        enhancement_level=request.enhancement_level
    )
    
    # In production, queue all videos for processing here
    # For now, simulate successful submission
    
    return {
        "success": True,
        "batch_id": batch_id,
        "video_count": len(urls),
        "estimated_completion": estimate_completion_time(len(urls)),
        "message": f"Successfully queued {len(urls)} videos for processing"
    }

@router.get("/api/batch-status/{batch_id}")
async def get_batch_status(batch_id: str):
    """Get status of a specific batch"""
    
    # In production, query actual batch status from database
    # For now, return mock status
    
    return {
        "batch_id": batch_id,
        "status": "processing", 
        "total_videos": 15,
        "completed": 12,
        "failed": 1,
        "remaining": 2,
        "progress_percentage": 80.0,
        "estimated_completion": "~15 minutes",
        "started_at": "2026-03-10T23:45:00Z"
    }