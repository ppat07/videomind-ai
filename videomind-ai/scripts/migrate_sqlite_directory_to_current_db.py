#!/usr/bin/env python3
"""
Migrate directory_entries from a source SQLite file into current configured DB.
Usage:
  python3 scripts/migrate_sqlite_directory_to_current_db.py \
    --source /path/to/old/videomind.db
"""
import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from database import SessionLocal  # noqa: E402
from models.directory import DirectoryEntry  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Path to source SQLite DB")
    args = parser.parse_args()

    src = Path(args.source).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Source DB not found: {src}")

    conn = sqlite3.connect(str(src))
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(directory_entries)")
    cols = [r[1] for r in cur.fetchall()]
    if not cols:
        raise SystemExit("Source DB has no directory_entries table")

    col_csv = ",".join(cols)
    cur.execute(f"SELECT {col_csv} FROM directory_entries")
    rows = cur.fetchall()

    db = SessionLocal()
    created, skipped = 0, 0

    try:
        for row in rows:
            item = dict(zip(cols, row))
            url = item.get("video_url")
            title = item.get("title")
            if not url or not title:
                skipped += 1
                continue

            exists = db.query(DirectoryEntry).filter(DirectoryEntry.video_url == url).first()
            if exists:
                skipped += 1
                continue

            payload = {
                "title": title,
                "video_url": url,
                "creator_name": item.get("creator_name"),
                "category_primary": item.get("category_primary") or "Automation Workflows",
                "difficulty": item.get("difficulty") or "Beginner",
                "tools_mentioned": item.get("tools_mentioned"),
                "summary_5_bullets": item.get("summary_5_bullets"),
                "best_for": item.get("best_for"),
                "signal_score": int(item.get("signal_score") or 70),
                "processing_status": item.get("processing_status") or "processed",
                "teaches_agent_to": item.get("teaches_agent_to"),
                "prompt_template": item.get("prompt_template"),
                "execution_checklist": item.get("execution_checklist"),
                "agent_training_script": item.get("agent_training_script"),
                "source_job_id": item.get("source_job_id"),
            }
            db.add(DirectoryEntry(**payload))
            created += 1

        db.commit()
        print({"success": True, "created": created, "skipped": skipped, "source": str(src)})
    finally:
        db.close()
        conn.close()


if __name__ == "__main__":
    main()
