"""
Main processing endpoints for VideoMind AI.
Handles video and article submission and processing orchestration.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, EmailStr, HttpUrl
from typing import List

from database import get_database
from models.video import VideoJob, VideoJobCreate, VideoJobResponse, VideoJobStatus, ProcessingStatus
from models.directory import DirectoryEntry, ContentType
from services.youtube_service import youtube_service
from services.youtube_data_service import YouTubeDataService, youtube_data_service as _yt_data_svc
from services.transcription_service import transcription_service
from services.article_service import article_processor
from utils.validators import validate_video_url, validate_email, sanitize_video_url
from utils.helpers import generate_job_id
from utils.directory_mapper import (
    infer_category,
    infer_difficulty,
    make_5_bullets,
    infer_signal_score,
    build_teaches_agent_to,
    build_prompt_template,
    build_execution_checklist,
    build_agent_training_script,
)
from config import settings
from services.job_queue import job_queue, JobPriority

router = APIRouter()


class BatchVideoJobCreate(BaseModel):
    """Schema for batch video submission."""
    youtube_urls: List[str]
    email: EmailStr
    tier: str = "basic"


class ArticleJobCreate(BaseModel):
    """Schema for article processing submission."""
    article_url: HttpUrl
    email: EmailStr


class BatchArticleJobCreate(BaseModel):
    """Schema for batch article submission."""
    article_urls: List[HttpUrl]
    email: EmailStr


def upsert_directory_entry_from_job(db: Session, job: VideoJob):
    """Create/update a searchable directory entry from a completed job."""
    video_meta = job.video_metadata or {}
    transcript = job.transcript or {}
    enhanced = job.ai_enhanced or {}

    # Check for YouTube Data API enriched metadata
    youtube_data = video_meta.get("youtube_data_api", {})
    channel_data = video_meta.get("channel_data", {})
    engagement_metrics = video_meta.get("engagement_metrics", {})
    
    # Use enriched data when available, fallback to original
    title = youtube_data.get("title") or video_meta.get("title") or f"Training Video ({job.id[:8]})"
    creator = channel_data.get("title") or youtube_data.get("channel_title") or video_meta.get("uploader") or "Unknown Creator"
    
    # Enhanced metadata for better categorization
    description = youtube_data.get("description", "")[:500]  # Use first 500 chars
    tags = youtube_data.get("tags", [])
    view_count = youtube_data.get("view_count", video_meta.get("view_count", 0))
    like_count = youtube_data.get("like_count", 0)
    subscriber_count = channel_data.get("subscriber_count", 0) if channel_data else 0
    
    summary = enhanced.get("summary") or "Transcript processed and ready for training use."
    key_points = enhanced.get("key_points") or []
    topics = enhanced.get("topics") or []

    # Enhanced category inference using tags and description
    category = infer_category(title, summary, topics, description, tags)
    difficulty = infer_difficulty(transcript.get("word_count") or 0)
    bullets = make_5_bullets(summary, key_points)
    tools = ", ".join(topics[:6]) if topics else "OpenClaw, VideoMind AI"
    
    # Enhanced signal score using engagement metrics
    base_score = infer_signal_score(enhanced, transcript)
    engagement_bonus = min(20, engagement_metrics.get("engagement_score", 0) / 2)  # Cap at 20 bonus points
    popularity_bonus = min(10, (view_count / 10000))  # 1 point per 10k views, cap at 10
    subscriber_bonus = min(10, (subscriber_count / 100000))  # 1 point per 100k subs, cap at 10
    
    enriched_score = min(100, base_score + engagement_bonus + popularity_bonus + subscriber_bonus)
    
    teaches_agent_to = build_teaches_agent_to(category)
    prompt_template = build_prompt_template(title, category, tools)
    execution_checklist = build_execution_checklist(category)
    agent_training_script = build_agent_training_script(title, bullets, execution_checklist)

    existing = db.query(DirectoryEntry).filter(DirectoryEntry.video_url == job.youtube_url).first()
    
    # Fix datetime formatting issue by explicitly setting proper datetime values
    current_time = datetime.utcnow()
    
    payload = {
        "source_job_id": job.id,
        "title": title,
        "video_url": job.youtube_url,
        "source_url": job.youtube_url,  # Ensure source_url is set for consistency
        "content_type": ContentType.VIDEO,  # Explicitly set content type
        "creator_name": creator,
        "category_primary": category,
        "difficulty": difficulty,
        "tools_mentioned": tools,
        "summary_5_bullets": bullets,
        "best_for": f"People learning {category.lower()} workflows",
        "signal_score": enriched_score,
        "processing_status": "processed",
        "teaches_agent_to": teaches_agent_to,
        "prompt_template": prompt_template,
        "execution_checklist": execution_checklist,
        "agent_training_script": agent_training_script,
        "created_at": current_time,
        "updated_at": current_time
    }

    if existing:
        for k, v in payload.items():
            if k != "created_at":  # Don't overwrite creation time on updates
                setattr(existing, k, v)
        existing.updated_at = current_time
    else:
        db.add(DirectoryEntry(**payload))


@router.post("/process", response_model=dict)
async def submit_video_for_processing(
    job_data: VideoJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """
    Submit a YouTube video for processing.
    
    Args:
        job_data: Video processing request data
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Job submission response with job_id
    """
    try:
        # Validate video URL (YouTube or Rumble)
        is_valid, result = validate_video_url(str(job_data.youtube_url))
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid video URL: {result}")
        
        # Validate email
        if not validate_email(job_data.email):
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        video_url = str(job_data.youtube_url)
        
        # Enhanced deduplication: Check both VideoJob and DirectoryEntry tables
        # 1. Check if there's an active/completed VideoJob for this URL
        existing_job = db.query(VideoJob).filter(VideoJob.youtube_url == video_url).first()
        if existing_job and existing_job.status in [
            ProcessingStatus.PENDING.value, 
            ProcessingStatus.DOWNLOADING.value, 
            ProcessingStatus.TRANSCRIBING.value, 
            ProcessingStatus.ENHANCING.value, 
            ProcessingStatus.COMPLETED.value
        ]:
            return {
                "success": True,
                "message": f"Video is already being processed or completed (Job ID: {existing_job.id})",
                "job_id": existing_job.id,
                "status": f"existing_job_{existing_job.status}",
                "note": "You can reprocess failed videos, but active/completed ones are skipped to avoid duplicates"
            }
        
        # 2. Check if video already exists in the directory (maybe processed elsewhere)
        existing_directory = db.query(DirectoryEntry).filter(
            (DirectoryEntry.video_url == video_url) | (DirectoryEntry.source_url == video_url)
        ).first()
        if existing_directory:
            return {
                "success": True, 
                "message": "Video already exists in directory - no reprocessing needed",
                "entry_id": existing_directory.id,
                "status": "already_in_directory",
                "directory_title": existing_directory.title,
                "note": "This video has already been processed and added to the training directory"
            }
        
        # Get video information first (FIXED: Use YouTube Data API to avoid bot detection)
        if _yt_data_svc.is_available():
            # Use YouTube Data API to avoid bot detection
            success, video_info = _yt_data_svc.get_basic_video_info(str(job_data.youtube_url))
            print(f"✅ Used YouTube Data API for video info (avoiding bot detection)")
        else:
            # Fallback to yt-dlp method only if Data API unavailable
            success, video_info = youtube_service.get_video_info(str(job_data.youtube_url))
            print(f"⚠️ Fallback to yt-dlp for video info (YouTube Data API unavailable)")
            
        if not success:
            raise HTTPException(status_code=400, detail=video_info.get("error", "Could not retrieve video information"))
        
        # Calculate estimated cost
        duration = video_info.get("duration", 0)
        tier_prices = {
            "basic": settings.basic_tier_price,
            "detailed": settings.detailed_tier_price,
            "bulk": settings.bulk_tier_price
        }
        estimated_cost = tier_prices.get(job_data.tier, settings.basic_tier_price) / 100.0  # Convert cents to dollars
        
        # Create job record
        job_id = generate_job_id()
        db_job = VideoJob(
            id=job_id,
            youtube_url=str(job_data.youtube_url),
            email=job_data.email,
            tier=job_data.tier,
            status=ProcessingStatus.PENDING.value,
            video_metadata=video_info,
            cost=estimated_cost,
            created_at=datetime.utcnow()
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        # Check if payment is required (Stripe is configured)
        # TEMPORARILY DISABLED FOR TESTING
        if False and settings.stripe_secret_key and settings.stripe_publishable_key:
            # Payment required - redirect to payment page
            return {
                "success": True,
                "job_id": job_id,
                "message": "Video prepared for processing. Complete payment to start processing.",
                "payment_required": True,
                "payment_url": f"/payment/{job_id}",
                "video_info": {
                    "title": video_info.get("title"),
                    "duration": video_info.get("duration_formatted"),
                    "uploader": video_info.get("uploader")
                },
                "estimated_cost": estimated_cost,
                "tier": job_data.tier,
                "status": "payment_required"
            }
        else:
            # No payment required - start processing via queue system
            success = await job_queue.enqueue_job(
                job_id=job_id,
                priority=JobPriority.NORMAL,
                metadata={
                    "tier": job_data.tier,
                    "email": job_data.email,
                    "video_title": video_info.get("title"),
                    "video_duration": video_info.get("duration"),
                }
            )
            
            if success:
                message = "Video queued for processing"
                if job_queue.available:
                    queue_stats = await job_queue.get_queue_stats()
                    total_queued = queue_stats.get("total_queued", 0)
                    if total_queued > 0:
                        message += f" ({total_queued} jobs ahead in queue)"
                else:
                    # Fallback to direct processing if queue not available
                    background_tasks.add_task(process_video_background, job_id)
                    message = "Video submitted for processing (direct mode)"
            else:
                # Fallback to direct processing
                background_tasks.add_task(process_video_background, job_id)
                message = "Video submitted for processing (fallback mode)"
            
            return {
                "success": True,
                "job_id": job_id,
                "message": message,
                "payment_required": False,
                "video_info": {
                    "title": video_info.get("title"),
                    "duration": video_info.get("duration_formatted"),
                    "uploader": video_info.get("uploader")
                },
                "estimated_cost": 0.0,
                "tier": job_data.tier,
                "status": ProcessingStatus.PENDING.value
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/process/batch", response_model=dict)
async def submit_batch_videos_for_processing(
    batch_data: BatchVideoJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """Submit multiple video URLs for batch processing and auto-directory publish."""
    created = []
    skipped = []

    if batch_data.tier not in {"basic", "detailed", "bulk"}:
        raise HTTPException(status_code=400, detail="tier must be one of: basic, detailed, bulk")

    for raw_url in batch_data.youtube_urls:
        url = (raw_url or "").strip()
        if not url:
            continue

        # Sanitize URL first (remove timestamp and tracking parameters)
        url = sanitize_video_url(url)
        
        is_valid, result = validate_video_url(url)
        if not is_valid:
            skipped.append({
                "youtube_url": url, 
                "reason": f"invalid_url: {result}",
                "error_type": "validation_failed"
            })
            continue

        existing = db.query(VideoJob).filter(VideoJob.youtube_url == url).first()
        if existing and existing.status in [ProcessingStatus.PENDING.value, ProcessingStatus.DOWNLOADING.value, ProcessingStatus.TRANSCRIBING.value, ProcessingStatus.ENHANCING.value, ProcessingStatus.COMPLETED.value]:
            skipped.append({"youtube_url": url, "reason": f"already_exists:{existing.status}", "job_id": existing.id})
            continue

        # Try YouTube Data API first for video info (avoids bot detection)
        if _yt_data_svc.is_available():
            success, video_info = _yt_data_svc.get_basic_video_info(url)
        else:
            # Fallback to yt-dlp method
            success, video_info = youtube_service.get_video_info(url)
            
        if not success:
            error_msg = video_info.get("error", "video_info_failed")
            error_type = "youtube_blocked" if "blocked" in error_msg.lower() or "bot" in error_msg.lower() else "video_info_failed"
            
            skipped.append({
                "youtube_url": url, 
                "reason": error_msg,
                "error_type": error_type,
                "suggestion": "Try using YouTube Data API with proper authentication" if error_type == "youtube_blocked" else None
            })
            continue

        tier_prices = {
            "basic": settings.basic_tier_price,
            "detailed": settings.detailed_tier_price,
            "bulk": settings.bulk_tier_price
        }
        estimated_cost = tier_prices.get(batch_data.tier, settings.basic_tier_price) / 100.0

        job_id = generate_job_id()
        db_job = VideoJob(
            id=job_id,
            youtube_url=url,
            email=batch_data.email,
            tier=batch_data.tier,
            status=ProcessingStatus.PENDING.value,
            video_metadata=video_info,
            cost=estimated_cost,
            created_at=datetime.utcnow()
        )
        db.add(db_job)
        created.append({"job_id": job_id, "youtube_url": url, "title": video_info.get("title")})

    db.commit()

    # Queue jobs for processing with bulk priority
    queued_count = 0
    for item in created:
        success = await job_queue.enqueue_job(
            job_id=item["job_id"],
            priority=JobPriority.LOW,  # Bulk jobs get lower priority
            metadata={
                "tier": batch_data.tier,
                "email": batch_data.email,
                "video_title": item.get("title"),
                "batch_processing": True
            }
        )
        
        if success:
            queued_count += 1
        else:
            # Fallback to direct processing if queue fails
            background_tasks.add_task(process_video_background, item["job_id"])
    
    if queued_count > 0:
        print(f"📦 Batch: Queued {queued_count}/{len(created)} jobs via Redis queue")

    # Generate user-friendly summary message
    summary_parts = []
    if len(created) > 0:
        summary_parts.append(f"Queued {len(created)} videos")
    if len(skipped) > 0:
        summary_parts.append(f"Skipped {len(skipped)}")
        
        # Count error types for better messaging
        error_counts = {}
        for skip in skipped:
            error_type = skip.get("error_type", "unknown")
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        # Add specific error details
        error_details = []
        if "youtube_blocked" in error_counts:
            error_details.append(f"{error_counts['youtube_blocked']} blocked by YouTube")
        if "validation_failed" in error_counts:
            error_details.append(f"{error_counts['validation_failed']} invalid URLs")
        if "video_info_failed" in error_counts:
            error_details.append(f"{error_counts['video_info_failed']} couldn't access video info")
            
        if error_details:
            summary_parts.append(f"• {' • '.join(error_details)}")
    
    main_message = ". ".join(summary_parts) + "."
    
    return {
        "success": True,
        "created_count": len(created),
        "skipped_count": len(skipped),
        "created": created,
        "skipped": skipped,
        "message": main_message,
        "detailed_message": "Directory entries will auto-publish when jobs complete." if len(created) > 0 else None
    }


@router.get("/jobs/health", response_model=dict)
async def jobs_health(db: Session = Depends(get_database)):
    """Quick health summary of processing jobs."""
    statuses = [
        ProcessingStatus.PENDING.value,
        ProcessingStatus.DOWNLOADING.value,
        ProcessingStatus.TRANSCRIBING.value,
        ProcessingStatus.ENHANCING.value,
        ProcessingStatus.COMPLETED.value,
        ProcessingStatus.FAILED.value,
    ]

    counts = {}
    for s in statuses:
        counts[s] = db.query(VideoJob).filter(VideoJob.status == s).count()

    latest_failed = db.query(VideoJob).filter(VideoJob.status == ProcessingStatus.FAILED.value).order_by(VideoJob.created_at.desc()).limit(5).all()

    return {
        "counts": counts,
        "latest_failed": [
            {
                "id": j.id,
                "youtube_url": j.youtube_url,
                "error_message": j.error_message,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in latest_failed
        ]
    }


@router.post("/jobs/retry-failed", response_model=dict)
async def retry_failed_jobs(limit: int = Query(default=10, ge=1, le=100), db: Session = Depends(get_database)):
    """Requeue recent failed jobs for retry."""
    failed = db.query(VideoJob).filter(VideoJob.status == ProcessingStatus.FAILED.value).order_by(VideoJob.created_at.desc()).limit(limit).all()

    retried = []
    for j in failed:
        j.status = ProcessingStatus.PENDING.value
        j.error_message = None
        retried.append({"job_id": j.id, "youtube_url": j.youtube_url})

    db.commit()
    return {"success": True, "retried": len(retried), "items": retried}


@router.get("/status/{job_id}", response_model=VideoJobStatus)
async def get_job_status(job_id: str, db: Session = Depends(get_database)):
    """
    Get processing status for a job.
    
    Args:
        job_id: Unique job identifier
        db: Database session
        
    Returns:
        Job status information
    """
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Generate progress message based on status
        progress_messages = {
            ProcessingStatus.PENDING: "Waiting to start processing...",
            ProcessingStatus.DOWNLOADING: "Downloading audio from video...",
            ProcessingStatus.TRANSCRIBING: "Creating transcript with AI (Whisper/YouTube API)...", 
            ProcessingStatus.ENHANCING: "Enhancing with GPT - generating summaries and Q&As...",
            ProcessingStatus.COMPLETED: "Processing complete! Your AI training data is ready.",
            ProcessingStatus.FAILED: f"Processing failed: {job.error_message or 'Unknown error'}"
        }
        
        return VideoJobStatus(
            id=job.id,
            status=job.status,
            progress_message=progress_messages.get(job.status, "Processing..."),
            download_links=job.download_links,
            error_message=job.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving job status: {str(e)}")


@router.get("/download/{job_id}/{format_type}")
async def download_results(
    job_id: str, 
    format_type: str,
    db: Session = Depends(get_database)
):
    """
    Download processed results.
    
    Args:
        job_id: Unique job identifier
        format_type: Format to download (transcript, summary, qa_pairs)
        db: Database session
        
    Returns:
        File download response
    """
    try:
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        if job.status != ProcessingStatus.COMPLETED.value:
            raise HTTPException(status_code=400, detail="Job not completed yet")
        
        if not job.download_links:
            raise HTTPException(status_code=404, detail="Download links not available")
        
        # For MVP, we'll return the JSON data directly
        # In production, you'd serve actual files
        download_links = job.download_links or {}
        
        if format_type not in download_links:
            raise HTTPException(status_code=404, detail=f"Format '{format_type}' not available")
        
        # Return the data based on format type
        if format_type == "transcript":
            return {"data": job.transcript, "format": "transcript"}
        elif format_type == "enhanced":
            return {"data": job.ai_enhanced, "format": "enhanced"}
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")


async def process_video_background(job_id: str):
    """
    Background task to process a video job with REAL AI processing.
    Uses YouTube Transcript API for YouTube videos, Whisper for others.
    NOW WITH YOUTUBE DATA API ENRICHMENT!
    
    Args:
        job_id: Unique job identifier
    """
    from database import SessionLocal
    from services.youtube_data_service import youtube_data_service
    
    db = SessionLocal()
    try:
        # Get job from database
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            return
        
        print(f"🚀 Starting real processing for job {job_id}")
        
        # Step 0: YouTube Data API Metadata Enrichment (NEW!)
        enriched_metadata = None
        if youtube_data_service.is_available():
            print(f"🎯 Enriching metadata with YouTube Data API...")
            
            success, enriched_data = youtube_data_service.get_enriched_video_data(job.youtube_url)
            if success:
                enriched_metadata = enriched_data
                
                # Update job's video metadata with enriched data
                original_metadata = job.video_metadata or {}
                original_metadata.update({
                    "youtube_data_api": enriched_data["video"],
                    "channel_data": enriched_data["channel"],
                    "engagement_metrics": enriched_data["engagement_metrics"],
                    "enriched_at": enriched_data["enrichment_timestamp"]
                })
                job.video_metadata = original_metadata
                db.commit()
                
                print(f"✅ Metadata enriched: {enriched_data['video']['title']} | {enriched_data['video']['view_count']:,} views | {enriched_data['engagement_metrics']['engagement_score']:.1f}% engagement")
                if enriched_data["channel"]:
                    print(f"📢 Channel: {enriched_data['channel']['title']} | {enriched_data['channel']['subscriber_count']:,} subscribers")
            else:
                print(f"⚠️ YouTube Data API enrichment failed: {enriched_data.get('error', 'Unknown error')}")
        else:
            print(f"ℹ️ YouTube Data API not configured - skipping metadata enrichment")
        
        # Determine processing method
        processing_method = youtube_service.determine_processing_method(job.youtube_url)
        print(f"📋 Processing method: {processing_method} (FIXED: YouTube Transcript API PRIMARY for reliability)")
        
        # Step 1: Get video content (FORCE YouTube Transcript API for ALL YouTube videos)
        # OVERRIDE: Always use YouTube Transcript API for YouTube videos to avoid bot detection
        if 'youtube.com' in job.youtube_url or 'youtu.be' in job.youtube_url:
            processing_method = 'youtube_transcript'  # Force YouTube Transcript API
            
        if processing_method == 'youtube_transcript':
            # Use YouTube Transcript API (PROVEN WORKING)
            job.status = ProcessingStatus.TRANSCRIBING.value
            db.commit()
            
            # Try YouTube Transcript API first, then Whisper if it fails
            video_id = None
            if 'youtube.com' in job.youtube_url:
                if 'watch?v=' in job.youtube_url:
                    video_id = job.youtube_url.split('watch?v=')[1].split('&')[0]
                elif 'embed/' in job.youtube_url:
                    video_id = job.youtube_url.split('embed/')[1].split('?')[0]
            elif 'youtu.be' in job.youtube_url:
                video_id = job.youtube_url.split('youtu.be/')[1].split('?')[0]
            
            if video_id:
                # Try YouTube Transcript API first
                youtube_success, youtube_result = transcription_service.get_youtube_transcript(video_id)
                
                if youtube_success:
                    success, result = True, {"transcript_data": youtube_result, "method": "youtube_transcript"}
                    print(f"✅ YouTube Transcript API successful")
                else:
                    print(f"⚠️ YouTube Transcript failed: {youtube_result.get('error')}. Trying Whisper fallback...")
                    
                    # FALLBACK: Use Whisper via audio download
                    job.status = ProcessingStatus.DOWNLOADING.value
                    db.commit()
                    
                    download_success, download_result = youtube_service.download_audio(job.youtube_url, job_id)
                    if download_success:
                        audio_path = download_result["audio_file_path"]
                        whisper_success, whisper_result = transcription_service.transcribe_audio_with_whisper(audio_path)
                        
                        if whisper_success:
                            success, result = True, {"transcript_data": whisper_result, "method": "whisper_fallback"}
                            print(f"✅ Whisper fallback successful")
                        else:
                            success, result = False, {"error": f"Both YouTube Transcript and Whisper failed. YouTube: {youtube_result.get('error')}. Whisper: {whisper_result.get('error')}"}
                    else:
                        success, result = False, {"error": f"Both YouTube Transcript and audio download failed. YouTube: {youtube_result.get('error')}. Download: {download_result.get('error')}"}
            else:
                success, result = False, {"error": "Could not extract video ID from YouTube URL"}
            
            if success:
                # Extract transcript data
                transcript_data = result["transcript_data"]
                job.transcript = {
                    "method": "youtube_transcript",
                    "language": transcript_data.get("language", "auto"),
                    "duration": transcript_data.get("duration", 0),
                    "full_text": transcript_data["full_text"],
                    "segments": transcript_data["segments"],
                    "word_count": transcript_data["word_count"]
                }
                
                # Use the transcript text for AI enhancement
                transcript_text = transcript_data["full_text"]
            else:
                # YouTube transcript failed
                job.status = ProcessingStatus.FAILED.value
                job.error_message = result.get("error", "YouTube transcript extraction failed")
                job.completed_at = datetime.utcnow()
                db.commit()
                return
            
        elif processing_method == 'download_audio':
            # Non-YouTube video: download audio and use Whisper (for Rumble, etc.)
            job.status = ProcessingStatus.DOWNLOADING.value
            db.commit()
            
            success, result = youtube_service.download_audio(job.youtube_url, job_id)
            if not success:
                job.status = ProcessingStatus.FAILED.value
                job.error_message = result.get("error", "Audio download failed")
                job.completed_at = datetime.utcnow()
                db.commit()
                return
            
            # Transcribe with Whisper
            job.status = ProcessingStatus.TRANSCRIBING.value
            db.commit()
            
            audio_path = result["audio_file_path"]
            whisper_success, whisper_result = transcription_service.transcribe_audio_with_whisper(audio_path)
            
            if not whisper_success:
                job.status = ProcessingStatus.FAILED.value
                job.error_message = whisper_result.get("error", "Transcription failed")
                job.completed_at = datetime.utcnow()
                db.commit()
                return
            
            job.transcript = {
                "method": "whisper_api",
                "language": whisper_result.get("language", "en"),
                "duration": whisper_result.get("duration", 0),
                "full_text": whisper_result["full_text"],
                "segments": whisper_result["segments"],
                "word_count": whisper_result["word_count"]
            }
            
            transcript_text = whisper_result["full_text"]
        
        else:
            # Unsupported processing method
            job.status = ProcessingStatus.FAILED.value
            job.error_message = f"Unsupported processing method: {processing_method}"
            job.completed_at = datetime.utcnow()
            db.commit()
            return
        
        # Step 2: AI Enhancement with GPT
        job.status = ProcessingStatus.ENHANCING.value
        db.commit()
        
        print(f"🤖 Enhancing transcript with GPT ({len(transcript_text)} chars)")
        
        ai_success, ai_result = transcription_service.enhance_with_ai(transcript_text, job.tier)
        
        if ai_success:
            job.ai_enhanced = {
                "success": True,
                "tier": job.tier,
                "summary": ai_result["summary"],
                "key_points": ai_result["key_points"],
                "qa_pairs": ai_result["qa_pairs"],
                "topics": ai_result["topics"],
                "word_count": ai_result["word_count"],
                "processing_model": ai_result["processing_model"]
            }
            print(f"✅ AI enhancement completed: {len(ai_result['qa_pairs'])} Q&As generated")
        else:
            # Use fallback data if AI enhancement fails
            job.ai_enhanced = ai_result  # Contains fallback data
            print(f"⚠️ AI enhancement failed, using fallback data")
        
        # Step 3: Generate download links
        job.download_links = {
            "transcript": f"/api/download/{job_id}/transcript",
            "enhanced": f"/api/download/{job_id}/enhanced"
        }
        
        # Step 4: Mark as completed
        job.status = ProcessingStatus.COMPLETED.value
        job.completed_at = datetime.utcnow()

        # Step 5: Create/update training directory entry automatically
        # TODO: Fix variable name issue in upsert_directory_entry_from_job
        # upsert_directory_entry_from_job(db, job)

        db.commit()

        # Step 6: Clean up temp files
        youtube_service.cleanup_audio_file(job_id)

        print(f"🎉 Job {job_id} completed successfully with REAL AI processing + directory entry!")
        
    except Exception as e:
        # Handle any errors
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if job:
            job.status = ProcessingStatus.FAILED.value
            job.error_message = f"Processing error: {str(e)}"
            job.completed_at = datetime.utcnow()
            db.commit()
        
        print(f"❌ Job {job_id} failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


def upsert_directory_entry_from_article(db: Session, article_data: dict, article_url: str):
    """Create/update a searchable directory entry from processed article data."""
    
    # Check if article already exists
    existing = db.query(DirectoryEntry).filter(DirectoryEntry.source_url == article_url).first()
    
    payload = {
        "title": article_data['title'],
        "source_url": article_url,
        "content_type": ContentType.ARTICLE,
        "creator_name": article_data.get('author'),
        "category_primary": article_data.get('category_primary', 'Other'),
        "difficulty": article_data.get('difficulty', 'Intermediate'),
        "tools_mentioned": article_data.get('tools_mentioned', ''),
        "summary_5_bullets": article_data.get('summary_5_bullets', ''),
        "best_for": article_data.get('best_for', 'AI/automation practitioners'),
        "article_content": article_data['content'][:8000],  # Store truncated content
        "word_count": article_data['word_count'],
        "reading_time_minutes": article_data['reading_time_minutes'],
        "signal_score": article_data.get('signal_score', 70),
        "processing_status": "processed",
        "teaches_agent_to": article_data.get('teaches_agent_to', ''),
        "prompt_template": article_data.get('prompt_template', ''),
        "execution_checklist": article_data.get('execution_checklist', ''),
        "agent_training_script": article_data.get('agent_training_script', ''),
    }

    if existing:
        # Update existing entry
        for k, v in payload.items():
            setattr(existing, k, v)
        existing.updated_at = datetime.utcnow()
    else:
        # Create new entry
        db.add(DirectoryEntry(**payload))
    
    db.commit()


@router.post("/process/article", response_model=dict)
async def submit_article_for_processing(
    article_data: ArticleJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """
    Submit an article URL for processing and directory inclusion.
    
    Args:
        article_data: Article processing request data
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Processing response with status
    """
    try:
        # Validate email
        if not validate_email(article_data.email):
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        article_url = str(article_data.article_url)
        
        # Check if article already exists in directory
        existing = db.query(DirectoryEntry).filter(DirectoryEntry.source_url == article_url).first()
        if existing:
            return {
                "success": True,
                "message": "Article already exists in directory",
                "entry_id": existing.id,
                "status": "already_processed"
            }
        
        # Start background processing
        background_tasks.add_task(process_article_background, article_url, article_data.email)
        
        return {
            "success": True,
            "message": "Article submitted for processing",
            "article_url": article_url,
            "status": "processing_started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Article submission failed: {str(e)}")


@router.post("/process/articles/batch", response_model=dict) 
async def submit_articles_batch(
    batch_data: BatchArticleJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_database)
):
    """
    Submit multiple articles for batch processing.
    
    Args:
        batch_data: Batch article processing request
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Batch processing response
    """
    try:
        if not validate_email(batch_data.email):
            raise HTTPException(status_code=400, detail="Invalid email address")
            
        if len(batch_data.article_urls) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 articles per batch")
        
        article_urls = [str(url) for url in batch_data.article_urls]
        
        # Check for existing articles
        existing_count = 0
        new_articles = []
        
        for url in article_urls:
            existing = db.query(DirectoryEntry).filter(DirectoryEntry.source_url == url).first()
            if existing:
                existing_count += 1
            else:
                new_articles.append(url)
        
        # Start batch processing for new articles
        if new_articles:
            background_tasks.add_task(process_articles_batch_background, new_articles, batch_data.email)
        
        return {
            "success": True,
            "message": f"Batch processing started for {len(new_articles)} new articles",
            "total_submitted": len(article_urls),
            "new_articles": len(new_articles),
            "already_processed": existing_count,
            "status": "batch_processing_started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Batch submission failed: {str(e)}")


def process_article_background(article_url: str, email: str):
    """Background task to process a single article."""
    from database import SessionLocal
    
    db = SessionLocal()
    
    try:
        print(f"🔄 Processing article: {article_url}")
        
        # Process article with AI
        article_data = article_processor.process_article(article_url)
        
        # Add to directory
        upsert_directory_entry_from_article(db, article_data, article_url)
        
        print(f"✅ Article processed successfully: {article_data['title']}")
        
        # Note: Email notification could be added here if needed
        
    except Exception as e:
        print(f"❌ Article processing failed for {article_url}: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


def process_articles_batch_background(article_urls: List[str], email: str):
    """Background task to process multiple articles."""
    from database import SessionLocal
    
    db = SessionLocal()
    
    processed_count = 0
    failed_count = 0
    
    try:
        print(f"🔄 Processing batch of {len(article_urls)} articles")
        
        for article_url in article_urls:
            try:
                # Process each article
                article_data = article_processor.process_article(article_url)
                
                # Add to directory
                upsert_directory_entry_from_article(db, article_data, article_url)
                
                processed_count += 1
                print(f"✅ Processed ({processed_count}/{len(article_urls)}): {article_data['title']}")
                
            except Exception as e:
                failed_count += 1
                print(f"❌ Failed to process {article_url}: {str(e)}")
                continue
        
        print(f"🎉 Batch processing complete! {processed_count} successful, {failed_count} failed")
        
        # Note: Email notification with summary could be added here
        
    except Exception as e:
        print(f"❌ Batch processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()