"""
Free demo endpoint — no auth required.
Lets visitors preview AI output without signing up.
Rate limited to 3 requests/IP/hour.

Transcript fallback chain:
  1. YouTube captions (instant, free)
  2. yt-dlp audio download + local faster-whisper (45s timeout)
  3. Friendly error with sign-up CTA
"""
import os
import re
import asyncio
import tempfile
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


def _download_and_transcribe(youtube_url: str, video_id: str) -> tuple:
    """
    Fallback: download audio with yt-dlp and transcribe with local faster-whisper.
    Returns (success: bool, result: dict).
    Saves to a temp file and cleans up after.
    """
    tmp_dir = None
    try:
        import yt_dlp
        from faster_whisper import WhisperModel
    except ImportError as e:
        return False, {"error": f"Missing dependency: {e}"}

    try:
        tmp_dir = tempfile.mkdtemp(prefix="videomind_demo_")
        audio_path = os.path.join(tmp_dir, f"{video_id}.%(ext)s")
        final_path = os.path.join(tmp_dir, f"{video_id}.mp3")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": audio_path,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "64",
            }],
            "quiet": True,
            "no_warnings": True,
            "socket_timeout": 15,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])

        # Find the downloaded file
        candidates = [f for f in os.listdir(tmp_dir) if f.endswith(".mp3")]
        if not candidates:
            return False, {"error": "Audio download produced no file"}

        audio_file = os.path.join(tmp_dir, candidates[0])
        file_size = os.path.getsize(audio_file)
        if file_size == 0:
            return False, {"error": "Downloaded audio file is empty"}

        # Transcribe with faster-whisper (tiny model — fastest, ~75MB)
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_file, beam_size=3)
        full_text = " ".join(seg.text.strip() for seg in segments)

        if not full_text.strip():
            return False, {"error": "Transcription produced no text"}

        return True, {
            "success": True,
            "method": "yt_dlp_whisper_fallback",
            "language": info.language,
            "full_text": full_text,
            "word_count": len(full_text.split()),
        }

    except Exception as e:
        return False, {"error": f"Audio transcription failed: {str(e)}"}

    finally:
        # Always clean up temp files
        if tmp_dir and os.path.exists(tmp_dir):
            import shutil
            try:
                shutil.rmtree(tmp_dir)
            except Exception:
                pass


def _generate_qa_from_entry(entry: "DirectoryEntry") -> list:
    """
    Generate 3 synthetic Q&A training pairs from DirectoryEntry structured fields.
    Used when no completed VideoJob exists for the cached entry.
    """
    pairs = []

    # Q1: What will you learn?
    objective = entry.teaches_agent_to or ""
    if not objective and entry.agent_training_script:
        m = re.search(r'Training Objective\n.*?(?:be able to:?\s*)(.+)', entry.agent_training_script)
        if m:
            objective = m.group(1).strip().strip("**")
    if objective:
        pairs.append({
            "question": "What will an AI agent learn from this video?",
            "answer": objective,
        })

    # Q2: Key tools / technologies
    if entry.tools_mentioned:
        tools = [t.strip() for t in entry.tools_mentioned.replace(";", ",").split(",") if t.strip()][:4]
        if tools:
            pairs.append({
                "question": "What tools and technologies are covered in this tutorial?",
                "answer": ", ".join(tools),
            })

    # Q3: Top learning point from bullets
    if entry.summary_5_bullets:
        bullets = [b.lstrip("•- \t").strip() for b in entry.summary_5_bullets.splitlines() if b.strip()]
        if bullets:
            pairs.append({
                "question": "What is the most important concept explained in this video?",
                "answer": bullets[0],
            })

    # Q4: Best for (if still need more)
    if len(pairs) < 3 and entry.best_for:
        pairs.append({
            "question": "Who is this video best suited for?",
            "answer": entry.best_for,
        })

    return pairs[:3]


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

        # If no Q&A pairs from VideoJob, generate from DirectoryEntry structured data
        qa_source = "job"
        if not qa_pairs:
            qa_pairs = _generate_qa_from_entry(existing_entry)
            qa_source = "entry" if qa_pairs else "none"

        thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None

        return {
            "success": True,
            "cached": True,
            "title": existing_entry.title,
            "thumbnail": thumbnail,
            "summary": summary,
            "qa_pairs": qa_pairs,
            "qa_source": qa_source,
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
        # Fallback: attempt audio download + local Whisper (timeout: 90s)
        try:
            fallback_success, fallback_result = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, _download_and_transcribe, youtube_url, video_id
                ),
                timeout=90.0,
            )
        except asyncio.TimeoutError:
            fallback_success = False
            fallback_result = {"error": "timeout"}

        if not fallback_success:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "no_transcript",
                    "message": "This video doesn't have auto-captions and couldn't be transcribed in time. Sign up free to process it with our full audio pipeline — results delivered to your inbox.",
                    "cta": "Sign up free",
                    "cta_url": "/",
                },
            )
        transcript_text = fallback_result["full_text"]
    else:
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
