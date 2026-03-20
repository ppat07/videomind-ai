#!/usr/bin/env python3
"""
Re-enrich training scripts for existing directory entries.

Targets entries where agent_training_script is short (<300 chars) or
contains placeholder text, then re-generates using the full AI pipeline.

Usage:
    python scripts/reenrich_training_scripts.py [--dry-run] [--limit N]
"""
import argparse
import os
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings
from models.directory import DirectoryEntry
from models.video import VideoJob
from services.claude_enhancement_service import ClaudeEnhancementService
from utils.directory_mapper import (
    make_5_bullets,
    build_teaches_agent_to,
    build_prompt_template,
    build_execution_checklist,
    build_agent_training_script,
    infer_category,
)

PLACEHOLDER_MARKERS = [
    "TRAINING: Basic video",
    "TRAINING: Advanced video",
    "placeholder",
    "AI enhancement coming soon",
    "This is a placeholder",
]


def is_stale(script: str) -> bool:
    if not script or len(script) < 300:
        return True
    low = script.lower()
    return any(m.lower() in low for m in PLACEHOLDER_MARKERS)


def reenrich_entry(entry: DirectoryEntry, job: VideoJob, enhancer: ClaudeEnhancementService, dry_run: bool) -> bool:
    """Re-generate training data for a single directory entry. Returns True if updated."""
    transcript_data = job.transcript if job else None
    existing_enhanced = job.ai_enhanced if job else None

    transcript_text = ""
    if transcript_data:
        transcript_text = transcript_data.get("full_text") or ""

    enhanced = existing_enhanced or {}

    # Re-run AI enhancement if we have transcript text and the existing AI data is poor
    existing_summary = enhanced.get("summary", "")
    needs_ai = (
        transcript_text
        and (
            not existing_summary
            or "placeholder" in existing_summary.lower()
            or "AI enhancement coming soon" in existing_summary
            or len(existing_summary) < 50
        )
    )

    if needs_ai:
        print(f"  → Running AI enhancement on transcript ({len(transcript_text)} chars)...")
        success, new_enhanced = enhancer.enhance_transcript(transcript_text, tier="detailed")
        if success:
            enhanced = new_enhanced
            # Persist improved ai_enhanced back to job
            if not dry_run and job:
                job.ai_enhanced = new_enhanced
            print(f"  ✓ AI enhanced: {len(enhanced.get('qa_pairs', []))} Q&As, {len(enhanced.get('key_points', []))} key points")
        else:
            print(f"  ✗ AI enhancement failed: {new_enhanced.get('error')}")

    summary = enhanced.get("summary") or entry.summary_5_bullets or ""
    key_points = enhanced.get("key_points") or []
    topics = enhanced.get("topics") or []
    full_summary = enhanced.get("full_summary") or summary
    qa_pairs = enhanced.get("qa_pairs") or []
    teaches_ai = enhanced.get("teaches_agent_to") or ""
    prerequisites = enhanced.get("prerequisites") or []
    implementation_steps = enhanced.get("implementation_steps") or []

    category = entry.category_primary or infer_category(entry.title or "", summary, topics)
    bullets = make_5_bullets(summary, key_points)
    tools = ", ".join(topics[:6]) if topics else "OpenClaw, VideoMind AI"

    teaches_agent_to = teaches_ai or build_teaches_agent_to(category)
    prompt_template = build_prompt_template(entry.title or "", category, tools)
    execution_checklist = build_execution_checklist(category)
    agent_training_script = build_agent_training_script(
        title=entry.title or "",
        summary_bullets=bullets,
        checklist=execution_checklist,
        full_summary=full_summary,
        key_points=key_points,
        qa_pairs=qa_pairs,
        teaches_agent_to=teaches_agent_to,
        prerequisites=prerequisites,
        implementation_steps=implementation_steps,
        topics=topics,
    )

    print(f"  → New training script: {len(agent_training_script)} chars")

    if not dry_run:
        entry.summary_5_bullets = bullets
        entry.teaches_agent_to = teaches_agent_to
        entry.prompt_template = prompt_template
        entry.execution_checklist = execution_checklist
        entry.agent_training_script = agent_training_script

    return True


def main():
    parser = argparse.ArgumentParser(description="Re-enrich training scripts for directory entries")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    parser.add_argument("--limit", type=int, default=None, help="Max entries to process")
    parser.add_argument("--all", action="store_true", help="Re-enrich all entries, not just stale ones")
    args = parser.parse_args()

    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    db = Session()

    enhancer = ClaudeEnhancementService()
    if not enhancer.available:
        print("ERROR: OPENAI_API_KEY not set. Cannot run AI enhancement.")
        sys.exit(1)

    entries = db.query(DirectoryEntry).all()
    targets = []
    for e in entries:
        if args.all or is_stale(e.agent_training_script):
            targets.append(e)

    if args.limit:
        targets = targets[:args.limit]

    print(f"Found {len(targets)} entries to re-enrich (dry_run={args.dry_run})")
    updated = 0

    for entry in targets:
        print(f"\n[{entry.id}] {entry.title}")
        job = None
        if entry.source_job_id:
            job = db.query(VideoJob).filter(VideoJob.id == entry.source_job_id).first()

        changed = reenrich_entry(entry, job, enhancer, args.dry_run)
        if changed:
            updated += 1

    if not args.dry_run and updated > 0:
        db.commit()
        print(f"\n✅ Committed {updated} updated entries.")
    elif args.dry_run:
        print(f"\n(dry-run) Would update {updated} entries.")
    else:
        print(f"\nNo entries needed updating.")

    db.close()


if __name__ == "__main__":
    main()
