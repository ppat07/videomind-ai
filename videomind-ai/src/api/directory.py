"""
Directory endpoints for browsing training entries.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_database
from models.directory import DirectoryEntry

router = APIRouter()


@router.get("/directory")
async def list_directory_entries(
    q: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    difficulty: Optional[str] = Query(default=None),
    creator: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
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

    if category:
        query = query.filter(DirectoryEntry.category_primary == category)

    if difficulty:
        query = query.filter(DirectoryEntry.difficulty == difficulty)

    if creator:
        query = query.filter(DirectoryEntry.creator_name.ilike(f"%{creator}%"))

    rows = query.order_by(DirectoryEntry.created_at.desc()).limit(limit).all()

    return {
        "count": len(rows),
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "video_url": r.video_url,
                "creator_name": r.creator_name,
                "category_primary": r.category_primary,
                "difficulty": r.difficulty,
                "tools_mentioned": r.tools_mentioned,
                "summary_5_bullets": r.summary_5_bullets,
                "best_for": r.best_for,
                "signal_score": r.signal_score,
                "processing_status": r.processing_status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
    }


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
