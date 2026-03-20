"""
Free demo endpoint — no auth required.
Lets visitors preview AI output without signing up.
Rate limited to 3 requests/IP/hour.
"""
import re
import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_database
from models.video import VideoJob, ProcessingStatus
from models.directory import DirectoryEntry
from services.transcription_service import transcription_service
from services.youtube_data_service import youtube_data_service as _yt_data_svc
from utils.validators import validate_video_url

router = APIRouter()

# In-memory rate limiting: IP -> list of request timestamps
_rate_limit_store: dict = defaultdict(list)
DEMO_RATE_LIMIT = 3
DEMO_RATE_WINDOW_HOURS = 1


def _check_rate_limit(ip: str) -> bool:
    """Returns True if request is allowed, False if rate limited."""
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=DEMO_RATE_WINDOW_HOURS)
    _rate_limit_store[ip] = [t for t in _rate_limit_store[ip] if t > cutoff]
    if len(_rate_limit_store[ip]) >= DEMO_RATE_LIMIT:
        return False
    _rate_limit_store[ip].append(now)
    return True


def _extract_video_id(url: str) -> Optional[str]:
    """Extract YouTube video ID from URL."""
    patterns = [
        r'youtube\.com/watch\?v=([^&\s]+)',
        r'youtu\.be/([^?\s]+)',
        r'youtube\.com/embed/([^?\s]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def _truncate_to_sentences(text: str, max_sentences: int = 3) -> str:
    """Truncate text to approximately max_sentences sentences."""
    if not text:
        return ""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:max_sentences])


class DemoRequest(BaseModel):
    youtube_url: str


@router.post("/demo/process", response_model=dict)
async def demo_process(
    request: Request,
    data: DemoRequest,
    db: Session = Depends(get_database),
):
    """
    Free demo endpoint — no auth required.
    Returns AI preview: summary (3 sentences) + 3 Q&A pairs.
    Rate limited to 3 requests/IP/hour.
    Instantly returns cached results for previously-processed videos.
    """
    # Determine client IP (support reverse proxy)
    ip = request.client.host
    x_forwarded = request.headers.get("x-forwarded-for")
    if x_forwarded:
        ip = x_forwarded.split(",")[0].strip()

    # Rate limit check
    if not _check_rate_limit(ip):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limited",
                "message": "You've used your 3 free previews this hour. Try again later or sign up for full access.",
            },
        )

    # Validate URL
    is_valid, validation_result = validate_video_url(data.youtube_url)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid video URL: {validation_result}")

    youtube_url = data.youtube_url.strip()
    video_id = _extract_video_id(youtube_url)

    # --- Cache: check for already-processed video (match by video ID, not exact URL) ---
    existing_entry = None
    if video_id:
        # Build all canonical forms of this video URL for matching
        canonical_urls = [
            youtube_url,
            f"https://www.youtube.com/watch?v={video_id}",
            f"https://youtu.be/{video_id}",
        ]
        for candidate in canonical_urls:
            existing_entry = db.query(DirectoryEntry).filter(
                (DirectoryEntry.video_url.contains(video_id)) |
                (DirectoryEntry.source_url.contains(video_id))
            ).first()
            if existing_entry:
                break

    if existing_entry:
        # Try to get rich AI data from corresponding completed VideoJob (match by video ID)
        existing_job = db.query(VideoJob).filter(
            VideoJob.youtube_url.contains(video_id),
            VideoJob.status == ProcessingStatus.COMPLETED.value,
        ).first()

        summary = ""
        qa_pairs = []
        if existing_job and existing_job.ai_enhanced:
            ai_data = existing_job.ai_enhanced
            raw_summary = ai_data.get("summary", "")
            # Skip generic fallback summaries
            if raw_summary and "unavailable" not in raw_summary.lower() and len(raw_summary) > 40:
                summary = _truncate_to_sentences(raw_summary, 3)
            qa_pairs = (ai_data.get("qa_pairs") or [])[:3]

        if not summary:
            # Fall back to bullets or first sentences of the agent training script
            bullets = existing_entry.summary_5_bullets or ""
            summary = _truncate_to_sentences(bullets.replace("•", "").replace("\n", " "), 3)
        if not summary:
            summary = _truncate_to_sentences(existing_entry.agent_training_script or "", 3)

        thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None

        return {
            "success": True,
            "cached": True,
            "title": existing_entry.title,
            "thumbnail": thumbnail,
            "summary": summary,
            "qa_pairs": qa_pairs,
            "source_url": youtube_url,
        }

    # --- Fresh processing ---
    if not video_id:
        raise HTTPException(status_code=400, detail="Could not extract YouTube video ID from URL")

    # Step 1: Get transcript (timeout: 8s)
    try:
        transcript_success, transcript_result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, transcription_service.get_youtube_transcript, video_id
            ),
            timeout=8.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Video processing timed out. Try a shorter video or sign up for full access.",
        )

    if not transcript_success:
        error_msg = transcript_result.get("error", "Could not get transcript for this video")
        raise HTTPException(status_code=422, detail=error_msg)

    transcript_text = transcript_result["full_text"]

    # Step 2: Get video title from YouTube Data API (best effort)
    title = "YouTube Video"
    if _yt_data_svc.is_available():
        try:
            ok, info = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, _yt_data_svc.get_basic_video_info, youtube_url
                ),
                timeout=3.0,
            )
            if ok:
                title = info.get("title", title)
        except (asyncio.TimeoutError, Exception):
            pass  # Non-critical, keep default title

    # Step 3: AI enhancement (timeout: 60s — local Ollama may need up to 30s)
    try:
        ai_success, ai_result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None, transcription_service.enhance_with_ai, transcript_text, "basic"
            ),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="AI processing timed out. Try a shorter video or sign up for full access.",
        )

    if not ai_success:
        raise HTTPException(status_code=500, detail="Could not generate AI preview. Please try again.")

    summary = _truncate_to_sentences(ai_result.get("summary", ""), 3)
    qa_pairs = (ai_result.get("qa_pairs") or [])[:3]
    thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

    return {
        "success": True,
        "cached": False,
        "title": title,
        "thumbnail": thumbnail,
        "summary": summary,
        "qa_pairs": qa_pairs,
        "source_url": youtube_url,
    }
