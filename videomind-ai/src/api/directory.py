"""
Directory endpoints for browsing training entries.
"""
from typing import Optional
import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_database
from src.models.directory import DirectoryEntry
from utils.directory_mapper import (
    build_teaches_agent_to,
    build_prompt_template,
    build_execution_checklist,
    build_agent_training_script,
)

router = APIRouter()


@router.get("/directory")
async def list_directory_entries(
    q: Optional[str] = Query(default=None),
    content_type: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    difficulty: Optional[str] = Query(default=None),
    creator: Optional[str] = Query(default=None),
    min_signal: Optional[int] = Query(default=None, ge=1, le=100),
    sort_by: str = Query(default="newest", pattern="^(newest|oldest|signal_desc|signal_asc)$"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=24, ge=1, le=200),
    db: Session = Depends(get_database),
):
    query = db.query(DirectoryEntry)

    if q:
        q_like = f"%{q}%"
        query = query.filter(
            (DirectoryEntry.title.ilike(q_like)) |
            (DirectoryEntry.summary_5_bullets.ilike(q_like)) |
            (DirectoryEntry.tools_mentioned.ilike(q_like))
        )

    if content_type:
        from models.directory import ContentType
        if content_type == "video":
            query = query.filter(DirectoryEntry.content_type == ContentType.VIDEO)
        elif content_type == "article":
            query = query.filter(DirectoryEntry.content_type == ContentType.ARTICLE)

    if category:
        query = query.filter(DirectoryEntry.category_primary == category)

    if difficulty:
        query = query.filter(DirectoryEntry.difficulty == difficulty)

    if creator:
        query = query.filter(DirectoryEntry.creator_name.ilike(f"%{creator}%"))

    if min_signal is not None:
        query = query.filter(DirectoryEntry.signal_score >= min_signal)

    total_count = query.with_entities(func.count(DirectoryEntry.id)).scalar() or 0

    if sort_by == "oldest":
        query = query.order_by(DirectoryEntry.created_at.asc())
    elif sort_by == "signal_desc":
        query = query.order_by(DirectoryEntry.signal_score.desc(), DirectoryEntry.created_at.desc())
    elif sort_by == "signal_asc":
        query = query.order_by(DirectoryEntry.signal_score.asc(), DirectoryEntry.created_at.desc())
    else:
        query = query.order_by(DirectoryEntry.created_at.desc())

    offset = (page - 1) * limit
    rows = query.offset(offset).limit(limit).all()

    return {
        "count": len(rows),
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "has_more": (offset + len(rows)) < total_count,
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "video_url": r.video_url,  # Legacy field
                "source_url": r.source_url or r.video_url,  # New unified URL field
                "content_type": r.content_type.value if r.content_type else "video",
                "creator_name": r.creator_name,
                "category_primary": r.category_primary,
                "difficulty": r.difficulty,
                "tools_mentioned": r.tools_mentioned,
                "summary_5_bullets": r.summary_5_bullets,
                "best_for": r.best_for,
                "word_count": r.word_count,
                "reading_time_minutes": r.reading_time_minutes,
                "signal_score": r.signal_score,
                "processing_status": r.processing_status,
                "teaches_agent_to": r.teaches_agent_to,
                "prompt_template": r.prompt_template,
                "execution_checklist": r.execution_checklist,
                "agent_training_script": r.agent_training_script,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


@router.get("/directory/export/csv")
async def export_directory_csv(
    q: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    difficulty: Optional[str] = Query(default=None),
    creator: Optional[str] = Query(default=None),
    min_signal: Optional[int] = Query(default=None, ge=1, le=100),
    sort_by: str = Query(default="signal_desc", pattern="^(newest|oldest|signal_desc|signal_asc)$"),
    limit: int = Query(default=1000, ge=1, le=5000),
    db: Session = Depends(get_database),
):
    """Export filtered directory entries as CSV for offline review/outreach."""
    query = db.query(DirectoryEntry)

    if q:
        q_like = f"%{q}%"
        query = query.filter(
            (DirectoryEntry.title.ilike(q_like)) |
            (DirectoryEntry.summary_5_bullets.ilike(q_like)) |
            (DirectoryEntry.tools_mentioned.ilike(q_like))
        )

    if category:
        query = query.filter(DirectoryEntry.category_primary == category)

    if difficulty:
        query = query.filter(DirectoryEntry.difficulty == difficulty)

    if creator:
        query = query.filter(DirectoryEntry.creator_name.ilike(f"%{creator}%"))

    if min_signal is not None:
        query = query.filter(DirectoryEntry.signal_score >= min_signal)

    if sort_by == "oldest":
        query = query.order_by(DirectoryEntry.created_at.asc())
    elif sort_by == "signal_desc":
        query = query.order_by(DirectoryEntry.signal_score.desc(), DirectoryEntry.created_at.desc())
    elif sort_by == "signal_asc":
        query = query.order_by(DirectoryEntry.signal_score.asc(), DirectoryEntry.created_at.desc())
    else:
        query = query.order_by(DirectoryEntry.created_at.desc())

    rows = query.limit(limit).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "title",
        "video_url",
        "creator_name",
        "category_primary",
        "difficulty",
        "signal_score",
        "tools_mentioned",
        "summary_5_bullets",
        "best_for",
        "teaches_agent_to",
        "prompt_template",
        "execution_checklist",
        "created_at",
    ])

    for r in rows:
        writer.writerow([
            r.title,
            r.video_url,
            r.creator_name,
            r.category_primary,
            r.difficulty,
            r.signal_score,
            r.tools_mentioned,
            r.summary_5_bullets,
            r.best_for,
            r.teaches_agent_to,
            r.prompt_template,
            r.execution_checklist,
            r.created_at.isoformat() if r.created_at else "",
        ])

    csv_data = output.getvalue()
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="videomind-directory-{timestamp}.csv"'
        },
    )


@router.post("/directory/seed")
async def seed_directory_entries(db: Session = Depends(get_database)):
    """Seed starter entries quickly for MVP demo."""
    seeds = [
        {
            "title": "ClawdBot is the most powerful AI tool I’ve ever used in my life. Here’s how to set it up",
            "video_url": "https://www.youtube.com/watch?v=Qkqe-uRhQJE&t=42s",
            "creator_name": "Alex Finn",
            "category_primary": "Setup & Onboarding",
            "difficulty": "Beginner",
            "tools_mentioned": "OpenClaw; CLI; OAuth/Auth setup",
            "summary_5_bullets": "• Introduces OpenClaw value\n• Walkthrough setup\n• Connect auth/models\n• Run first workflow\n• Quick-win setup tips",
            "best_for": "New users who want fast setup without mistakes",
            "signal_score": 82,
            "processing_status": "reviewed",
            "teaches_agent_to": "Execute setup and onboarding workflows quickly.",
            "prompt_template": "Implement a fast setup workflow for OpenClaw with clear commands and validation steps.",
            "execution_checklist": "[ ] Confirm prerequisites\n[ ] Configure auth\n[ ] Verify model\n[ ] Run first task\n[ ] Validate output",
            "agent_training_script": "TRAINING SCRIPT: Setup & onboarding workflow with clear commands and validation.",
        },
        {
            "title": "You NEED to do this with OpenClaw immediately!",
            "video_url": "https://www.youtube.com/watch?v=Aj6hoC9JaLI",
            "creator_name": "Alex Finn",
            "category_primary": "Automation Workflows",
            "difficulty": "Beginner",
            "tools_mentioned": "OpenClaw; workflow automation; model/session setup",
            "summary_5_bullets": "• High-impact immediate action\n• Practical first wins\n• Repeatable workflow\n• Set defaults early\n• Foundation for advanced use",
            "best_for": "Users who want fastest first ROI",
            "signal_score": 80,
            "processing_status": "reviewed",
            "teaches_agent_to": "Execute repeatable automation workflows quickly.",
            "prompt_template": "Build a repeatable automation workflow from this tutorial and include copy/paste commands.",
            "execution_checklist": "[ ] Define objective\n[ ] Configure tools\n[ ] Run workflow\n[ ] Validate result\n[ ] Document reusable steps",
            "agent_training_script": "TRAINING SCRIPT: Automation workflow execution with validation and documentation.",
        },
        {
            "title": "Making $$$ with OpenClaw",
            "video_url": "https://www.youtube.com/watch?v=i13XK-uUOLQ&t=20s",
            "creator_name": "Greg Isenberg",
            "category_primary": "Business Use Cases",
            "difficulty": "Intermediate",
            "tools_mentioned": "OpenClaw; automation workflows; lead/revenue systems",
            "summary_5_bullets": "• Monetization opportunities\n• Revenue workflows\n• Outreach/ops patterns\n• Implementation focus\n• OpenClaw as business leverage",
            "best_for": "Founders/solopreneurs turning automation into revenue",
            "signal_score": 86,
            "processing_status": "reviewed",
            "teaches_agent_to": "Implement business-focused AI workflows that drive revenue outcomes.",
            "prompt_template": "Create a monetization-focused execution plan with steps, prompts, and KPI checks.",
            "execution_checklist": "[ ] Define revenue objective\n[ ] Build workflow\n[ ] Launch test\n[ ] Measure KPI\n[ ] Iterate",
            "agent_training_script": "TRAINING SCRIPT: Business workflow implementation focused on measurable outcomes.",
        },
    ]

    created = 0
    for seed in seeds:
        exists = db.query(DirectoryEntry).filter(DirectoryEntry.video_url == seed["video_url"]).first()
        if exists:
            continue
        db.add(DirectoryEntry(**seed))
        created += 1

    db.commit()
    return {"success": True, "created": created}


@router.get("/directory/export/agent-training")
async def export_agent_training(
    category: Optional[str] = Query(default=None),
    difficulty: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_database),
):
    """Export training-ready payloads for agent teaching."""
    query = db.query(DirectoryEntry)

    if category:
        query = query.filter(DirectoryEntry.category_primary == category)
    if difficulty:
        query = query.filter(DirectoryEntry.difficulty == difficulty)

    rows = query.order_by(DirectoryEntry.signal_score.desc(), DirectoryEntry.created_at.desc()).limit(limit).all()

    return {
        "count": len(rows),
        "items": [
            {
                "title": r.title,
                "video_url": r.video_url,
                "creator_name": r.creator_name,
                "category_primary": r.category_primary,
                "difficulty": r.difficulty,
                "teaches_agent_to": r.teaches_agent_to,
                "prompt_template": r.prompt_template,
                "execution_checklist": r.execution_checklist,
                "agent_training_script": r.agent_training_script,
                "signal_score": r.signal_score,
            }
            for r in rows
        ]
    }


@router.post("/directory/backfill-agent-scripts")
async def backfill_agent_scripts(db: Session = Depends(get_database)):
    """Fill agent-training fields for existing entries."""
    rows = db.query(DirectoryEntry).all()
    updated = 0

    for r in rows:
        if r.teaches_agent_to and r.prompt_template and r.execution_checklist and r.agent_training_script:
            continue

        category = r.category_primary or "Automation Workflows"
        tools = r.tools_mentioned or "OpenClaw, VideoMind AI"
        bullets = r.summary_5_bullets or "• Review source video"

        r.teaches_agent_to = build_teaches_agent_to(category)
        r.prompt_template = build_prompt_template(r.title, category, tools)
        r.execution_checklist = build_execution_checklist(category)
        r.agent_training_script = build_agent_training_script(r.title, bullets, r.execution_checklist)
        updated += 1

    db.commit()
    return {"success": True, "updated": updated}
