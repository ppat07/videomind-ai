#!/usr/bin/env python3
"""
Database initialization and persistence script
Runs on every startup to ensure data persistence
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def ensure_database_and_seed():
    """Ensure database exists and has seed data."""
    try:
        from database import create_tables, engine
        from models.directory import DirectoryEntry
        from sqlalchemy.orm import sessionmaker
        
        print("🔄 Initializing VideoMind AI database...")
        
        # Create all tables
        create_tables()
        print("   ✅ Database tables created/verified")
        
        # Check if directory entries exist
        Session = sessionmaker(bind=engine)
        session = Session()
        
        count = session.query(DirectoryEntry).count()
        if count == 0:
            print("   📚 Database empty, auto-seeding directory...")
            
            # Create seed data directly
            from models.directory import ContentType
            
            seed_videos = [
                {
                    "title": "ClawdBot is the most powerful AI tool I've ever used in my life. Here's how to set it up",
                    "source_url": "https://www.youtube.com/watch?v=Qkqe-uRhQJE&t=42s",
                    "video_url": "https://www.youtube.com/watch?v=Qkqe-uRhQJE&t=42s",
                    "content_type": ContentType.VIDEO,
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
                    "source_url": "https://www.youtube.com/watch?v=Aj6hoC9JaLI",
                    "video_url": "https://www.youtube.com/watch?v=Aj6hoC9JaLI",
                    "content_type": ContentType.VIDEO,
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
                    "source_url": "https://www.youtube.com/watch?v=i13XK-uUOLQ&t=20s",
                    "video_url": "https://www.youtube.com/watch?v=i13XK-uUOLQ&t=20s", 
                    "content_type": ContentType.VIDEO,
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
                session.add(entry)
            
            session.commit()
            print(f"   ✅ Auto-seeded directory with {len(seed_videos)} OpenClaw videos")
        else:
            print(f"   📚 Directory has {count} entries, no seeding needed")
            
        session.close()
        print("🎉 VideoMind AI database initialization complete!")
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    ensure_database_and_seed()