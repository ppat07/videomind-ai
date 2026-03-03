"""
Video processing service for VideoMind AI.
Orchestrates the full video processing pipeline after payment is confirmed.
"""
from sqlalchemy.orm import Session
from models.video import VideoJob, ProcessingStatus
from services.youtube_service import youtube_service
from services.transcription_service import transcription_service
from api.process import process_video_background

async def start_processing(job_id: str, db: Session):
    """
    Start video processing after payment confirmation.
    
    Args:
        job_id: Video job identifier
        db: Database session
    """
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        return
    
    # Update status to indicate processing has started
    job.status = ProcessingStatus.PENDING.value
    db.commit()
    
    # Start the background processing
    # Note: This will be called from an async context, so we'll import the function
    # and call it directly rather than using background tasks
    await process_video_background(job_id)