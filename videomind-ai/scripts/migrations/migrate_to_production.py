#!/usr/bin/env python3
"""
Migrate directory entries from local SQLite to production Supabase using direct database connection.
"""
import sqlite3
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import os
os.environ.setdefault("SECRET_KEY", "migration-key")
os.environ.setdefault("OPENAI_API_KEY", "migration-key")

def migrate_local_to_production():
    """Transfer all directory entries from local SQLite to production Supabase."""
    
    print("🚀 Starting migration from local SQLite to production Supabase...")
    
    # Import database modules after setting up path
    from database import SessionLocal
    from models.directory import DirectoryEntry, ContentType
    from datetime import datetime
    import uuid
    
    # Connect to local SQLite database
    try:
        conn = sqlite3.connect('videomind.db')
        cursor = conn.cursor()
        
        # Get all directory entries with proper column selection
        cursor.execute("""
            SELECT title, creator_name, category_primary, difficulty, 
                   tools_mentioned, summary_5_bullets, best_for, signal_score,
                   video_url, processing_status, teaches_agent_to, prompt_template,
                   execution_checklist, agent_training_script
            FROM directory_entries
        """)
        
        entries = cursor.fetchall()
        print(f"📊 Found {len(entries)} entries to migrate")
        conn.close()
        
    except Exception as e:
        print(f"❌ Error reading local database: {e}")
        return False
    
    # Connect to production database
    try:
        db = SessionLocal()
        
        success_count = 0
        error_count = 0
        
        for i, entry in enumerate(entries, 1):
            try:
                # Check if entry already exists (by title to avoid duplicates)
                existing = db.query(DirectoryEntry).filter(
                    DirectoryEntry.title == entry[0]
                ).first()
                
                if existing:
                    print(f"⏭️  {i}/{len(entries)}: Skipping existing - {entry[0][:50]}...")
                    continue
                
                # Create new directory entry
                new_entry = DirectoryEntry(
                    id=str(uuid.uuid4()),
                    title=entry[0] or "Untitled",
                    source_url=entry[8] or "",  # video_url as source_url
                    video_url=entry[8],
                    content_type=ContentType.VIDEO,
                    creator_name=entry[1] or "Unknown",
                    category_primary=entry[2] or "Automation Workflows", 
                    difficulty=entry[3] or "Beginner",
                    tools_mentioned=entry[4],
                    summary_5_bullets=entry[5],
                    best_for=entry[6],
                    signal_score=int(entry[7]) if entry[7] else 70,
                    processing_status=entry[9] or "processed",
                    teaches_agent_to=entry[10],
                    prompt_template=entry[11],
                    execution_checklist=entry[12],
                    agent_training_script=entry[13],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db.add(new_entry)
                db.commit()
                
                success_count += 1
                print(f"✅ {i}/{len(entries)}: {entry[0][:50]}...")
                
            except Exception as e:
                error_count += 1
                db.rollback()
                print(f"❌ {i}/{len(entries)}: Error - {e}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error connecting to production database: {e}")
        return False
    
    print(f"\n🏁 Migration complete!")
    print(f"✅ Success: {success_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total processed: {len(entries)}")
    
    return success_count > 0

if __name__ == "__main__":
    migrate_local_to_production()