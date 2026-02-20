"""
Main processing endpoints for VideoMind AI.
Handles video submission and processing orchestration.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import List

from database import get_database
from models.video import VideoJob, VideoJobCreate, VideoJobResponse, VideoJobStatus, ProcessingStatus
from models.directory import DirectoryEntry
from services.youtube_service import youtube_service
from services.transcription_service import transcription_service
from utils.validators import validate_video_url, validate_email
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

router = APIRouter()


class BatchVideoJobCreate(BaseModel):
    """Schema for batch video submission."""
    youtube_urls: List[str]
    email: EmailStr
    tier: str = "basic"


def upsert_directory_entry_from_job(db: Session, job: VideoJob):
    """Create/update a searchable directory entry from a completed job."""
    video_meta = job.video_metadata or {}
    transcript = job.transcript or {}
    enhanced = job.ai_enhanced or {}

    title = video_meta.get("title") or f"Training Video ({job.id[:8]})"
    creator = video_meta.get("uploader") or "Unknown Creator"
    summary = enhanced.get("summary") or "Transcript processed and ready for training use."
    key_points = enhanced.get("key_points") or []
    topics = enhanced.get("topics") or []

    category = infer_category(title, summary, topics)
    difficulty = infer_difficulty(transcript.get("word_count") or 0)
    bullets = make_5_bullets(summary, key_points)
    tools = ", ".join(topics[:6]) if topics else "OpenClaw, VideoMind AI"
    score = infer_signal_score(enhanced, transcript)
    teaches_agent_to = build_teaches_agent_to(category)
    prompt_template = build_prompt_template(title, category, tools)
    execution_checklist = build_execution_checklist(category)
    agent_training_script = build_agent_training_script(title, bullets, execution_checklist)

    existing = db.query(DirectoryEntry).filter(DirectoryEntry.video_url == job.youtube_url).first()
    payload = {
        "source_job_id": job.id,
        "title": title,
        "video_url": job.youtube_url,
        "creator_name": creator,
        "category_primary": category,
        "difficulty": difficulty,
        "tools_mentioned": tools,
        "summary_5_bullets": bullets,
        "best_for": f"People learning {category.lower()} workflows",
        "signal_score": score,
        "processing_status": "processed",
        "teaches_agent_to": teaches_agent_to,
        "prompt_template": prompt_template,
        "execution_checklist": execution_checklist,
        "agent_training_script": agent_training_script,
    }

    if existing:
        for k, v in payload.items():
            setattr(existing, k, v)
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
        
        # Get video information first
        success, video_info = youtube_service.get_video_info(str(job_data.youtube_url))
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
        
        # Start background processing
        background_tasks.add_task(process_video_background, job_id)
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Video submitted for processing",
            "video_info": {
                "title": video_info.get("title"),
                "duration": video_info.get("duration_formatted"),
                "uploader": video_info.get("uploader")
            },
            "estimated_cost": estimated_cost,
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

        is_valid, result = validate_video_url(url)
        if not is_valid:
            skipped.append({"youtube_url": url, "reason": f"invalid_url: {result}"})
            continue

        existing = db.query(VideoJob).filter(VideoJob.youtube_url == url).first()
        if existing and existing.status in [ProcessingStatus.PENDING.value, ProcessingStatus.DOWNLOADING.value, ProcessingStatus.TRANSCRIBING.value, ProcessingStatus.ENHANCING.value, ProcessingStatus.COMPLETED.value]:
            skipped.append({"youtube_url": url, "reason": f"already_exists:{existing.status}", "job_id": existing.id})
            continue

        success, video_info = youtube_service.get_video_info(url)
        if not success:
            skipped.append({"youtube_url": url, "reason": video_info.get("error", "video_info_failed")})
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

    for item in created:
        background_tasks.add_task(process_video_background, item["job_id"])

    return {
        "success": True,
        "created_count": len(created),
        "skipped_count": len(skipped),
        "created": created,
        "skipped": skipped,
        "message": "Batch submitted. Directory entries will auto-publish when jobs complete."
    }


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
    
    Args:
        job_id: Unique job identifier
    """
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # Get job from database
        job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
        if not job:
            return
        
        print(f"🚀 Starting real processing for job {job_id}")
        
        # Determine processing method
        processing_method = youtube_service.determine_processing_method(job.youtube_url)
        print(f"📋 Processing method: {processing_method} (ENHANCED: Whisper PRIMARY)")
        
        # Step 1: Get video content (FIXED: Back to working YouTube Transcript API)
        if processing_method == 'youtube_transcript':
            # Use YouTube Transcript API (PROVEN WORKING)
            job.status = ProcessingStatus.TRANSCRIBING.value
            db.commit()
            
            success, result = youtube_service.process_youtube_transcript(job.youtube_url, job_id)
            
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
            
        elif processing_method == 'whisper_first':
            # ENHANCED: Use Whisper first for superior quality (disabled due to YouTube blocking)
            job.status = ProcessingStatus.DOWNLOADING.value
            db.commit()
            
            success, result = youtube_service.process_whisper_first(job.youtube_url, job_id)
            
        elif processing_method == 'whisper_primary':
            # Handle legacy processing method name
            job.status = ProcessingStatus.DOWNLOADING.value
            db.commit()
            
            success, result = youtube_service.process_whisper_first(job.youtube_url, job_id)
            
            if success:
                # Extract transcript data
                transcript_data = result["transcript_data"]
                job.transcript = {
                    "method": result.get("method", "whisper_primary"),
                    "language": transcript_data.get("language", "auto"),
                    "duration": transcript_data.get("duration", 0),
                    "full_text": transcript_data["full_text"],
                    "segments": transcript_data.get("segments", []),
                    "word_count": transcript_data["word_count"],
                    "fallback_used": "youtube_transcript" in result.get("method", ""),
                    "fallback_reason": result.get("fallback_reason", None)
                }
                
                # Use the transcript text for AI enhancement
                transcript_text = transcript_data["full_text"]
                
                # Update status based on method used
                if "whisper" in result.get("method", ""):
                    job.status = ProcessingStatus.TRANSCRIBING.value
                    print(f"✅ Used Whisper for high-quality transcription")
                else:
                    job.status = ProcessingStatus.TRANSCRIBING.value
                    print(f"⚠️ Used YouTube API fallback: {result.get('fallback_reason', 'Unknown')}")
                
                db.commit()
                
            else:
                # All methods failed
                job.status = ProcessingStatus.FAILED.value
                job.error_message = result.get("error", "All transcription methods failed")
                job.completed_at = datetime.utcnow()
                db.commit()
                return
        
        else:
            # Non-YouTube video: download audio and use Whisper
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
        upsert_directory_entry_from_job(db, job)

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