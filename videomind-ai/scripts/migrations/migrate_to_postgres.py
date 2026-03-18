#!/usr/bin/env python3
"""
Migration script to move data from SQLite to PostgreSQL
Run this once when switching to production PostgreSQL database
"""
import os
import sys
import sqlite3
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from models import VideoJob, DirectoryEntry
from database import Base


def migrate_sqlite_to_postgres():
    """Migrate data from SQLite to PostgreSQL."""
    
    # SQLite source
    sqlite_path = "./videomind.db"
    if not os.path.exists(sqlite_path):
        print("❌ No SQLite database found to migrate")
        return False
        
    # PostgreSQL target
    postgres_url = os.environ.get("DATABASE_URL")
    if not postgres_url:
        print("❌ No PostgreSQL DATABASE_URL found")
        return False
    
    print("🚀 STARTING SQLITE → POSTGRESQL MIGRATION")
    print(f"Source: {sqlite_path}")
    print(f"Target: {postgres_url[:50]}...")
    
    try:
        # Create PostgreSQL engine and tables
        pg_engine = create_engine(postgres_url)
        Base.metadata.create_all(bind=pg_engine)
        pg_session = sessionmaker(bind=pg_engine)()
        
        # Connect to SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row  # Dict-like access
        
        # Migrate VideoJob data
        print("📄 Migrating video jobs...")
        cursor = sqlite_conn.execute("SELECT * FROM video_jobs")
        video_jobs = cursor.fetchall()
        
        for job in video_jobs:
            pg_job = VideoJob(**dict(job))
            pg_session.add(pg_job)
        
        # Migrate DirectoryEntry data
        print("📚 Migrating directory entries...")
        try:
            cursor = sqlite_conn.execute("SELECT * FROM directory_entries")
            directory_entries = cursor.fetchall()
            
            for entry in directory_entries:
                pg_entry = DirectoryEntry(**dict(entry))
                pg_session.add(pg_entry)
        except sqlite3.OperationalError:
            print("⚠️ No directory_entries table found in SQLite")
        
        # Commit all changes
        pg_session.commit()
        
        # Verify migration
        job_count = pg_session.query(VideoJob).count()
        entry_count = pg_session.query(DirectoryEntry).count()
        
        print(f"✅ Migration complete!")
        print(f"   Video jobs: {job_count}")
        print(f"   Directory entries: {entry_count}")
        
        pg_session.close()
        sqlite_conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def seed_directory_after_migration():
    """Seed directory with OpenClaw videos after migration."""
    postgres_url = os.environ.get("DATABASE_URL")
    if not postgres_url:
        return False
        
    try:
        pg_engine = create_engine(postgres_url)
        pg_session = sessionmaker(bind=pg_engine)()
        
        # Check if directory is empty
        count = pg_session.query(DirectoryEntry).count()
        if count == 0:
            print("📚 Seeding OpenClaw directory...")
            
            # Add the 3 core OpenClaw videos
            seed_videos = [
                {
                    "title": "ClawdBot is the most powerful AI tool I've ever used in my life. Here's how to set it up",
                    "video_url": "https://www.youtube.com/watch?v=Qkqe-uRhQJE&t=42s",
                    "source_url": "https://www.youtube.com/watch?v=Qkqe-uRhQJE&t=42s",
                    "content_type": "VIDEO",
                    "creator_name": "Alex Finn",
                    "category_primary": "Setup & Onboarding",
                    "difficulty": "Beginner",
                    "tools_mentioned": "OpenClaw; CLI; OAuth/Auth setup",
                    "summary_5_bullets": "• Introduces OpenClaw value\\n• Walkthrough setup\\n• Connect auth/models\\n• Run first workflow\\n• Quick-win setup tips",
                    "best_for": "New users who want fast setup without mistakes",
                    "signal_score": 82,
                    "processing_status": "reviewed",
                    "teaches_agent_to": "Execute setup and onboarding workflows quickly.",
                    "prompt_template": "Implement a fast setup workflow for OpenClaw with clear commands and validation steps.",
                    "execution_checklist": "[ ] Confirm prerequisites\\n[ ] Configure auth\\n[ ] Verify model\\n[ ] Run first task\\n[ ] Validate output",
                    "agent_training_script": "TRAINING SCRIPT: Setup & onboarding workflow with clear commands and validation."
                },
                {
                    "title": "You NEED to do this with OpenClaw immediately!",
                    "video_url": "https://www.youtube.com/watch?v=Aj6hoC9JaLI",
                    "source_url": "https://www.youtube.com/watch?v=Aj6hoC9JaLI",
                    "content_type": "VIDEO",
                    "creator_name": "Alex Finn", 
                    "category_primary": "Automation Workflows",
                    "difficulty": "Beginner",
                    "tools_mentioned": "OpenClaw; workflow automation; model/session setup",
                    "summary_5_bullets": "• High-impact immediate action\\n• Practical first wins\\n• Repeatable workflow\\n• Set defaults early\\n• Foundation for advanced use",
                    "best_for": "Users who want fastest first ROI",
                    "signal_score": 80,
                    "processing_status": "reviewed",
                    "teaches_agent_to": "Execute repeatable automation workflows quickly.",
                    "prompt_template": "Build a repeatable automation workflow from this tutorial and include copy/paste commands.",
                    "execution_checklist": "[ ] Define objective\\n[ ] Configure tools\\n[ ] Run workflow\\n[ ] Validate result\\n[ ] Document reusable steps",
                    "agent_training_script": "TRAINING SCRIPT: Automation workflow execution with validation and documentation."
                },
                {
                    "title": "Making $$$ with OpenClaw",
                    "video_url": "https://www.youtube.com/watch?v=i13XK-uUOLQ&t=20s",
                    "source_url": "https://www.youtube.com/watch?v=i13XK-uUOLQ&t=20s", 
                    "content_type": "VIDEO",
                    "creator_name": "Greg Isenberg",
                    "category_primary": "Business Use Cases",
                    "difficulty": "Intermediate",
                    "tools_mentioned": "OpenClaw; automation workflows; lead/revenue systems",
                    "summary_5_bullets": "• Monetization opportunities\\n• Revenue workflows\\n• Outreach/ops patterns\\n• Implementation focus\\n• OpenClaw as business leverage",
                    "best_for": "Founders/solopreneurs turning automation into revenue",
                    "signal_score": 86,
                    "processing_status": "reviewed", 
                    "teaches_agent_to": "Implement business-focused AI workflows that drive revenue outcomes.",
                    "prompt_template": "Create a monetization-focused execution plan with steps, prompts, and KPI checks.",
                    "execution_checklist": "[ ] Define revenue objective\\n[ ] Build workflow\\n[ ] Launch test\\n[ ] Measure KPI\\n[ ] Iterate",
                    "agent_training_script": "TRAINING SCRIPT: Business workflow implementation focused on measurable outcomes."
                }
            ]
            
            for video_data in seed_videos:
                entry = DirectoryEntry(**video_data)
                pg_session.add(entry)
            
            pg_session.commit()
            print(f"✅ Seeded {len(seed_videos)} OpenClaw videos")
        
        pg_session.close()
        return True
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        return False


if __name__ == "__main__":
    success = migrate_sqlite_to_postgres()
    if success:
        seed_directory_after_migration()
        print("🎉 Migration and seeding complete!")
        print("🚀 VideoMind AI now has persistent PostgreSQL database")
    else:
        print("❌ Migration failed")
        sys.exit(1)