#!/usr/bin/env python3
"""
Actually migrate data from local SQLite to production Supabase by forcing the connection.
"""
import sqlite3
import sys
from pathlib import Path
import os

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def migrate_sqlite_to_supabase():
    """Transfer all directory entries from SQLite to Supabase for real."""
    
    print("🚀 REAL migration from SQLite to Supabase...")
    
    # First, read from SQLite
    sqlite_entries = []
    try:
        conn = sqlite3.connect('videomind.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT title, creator_name, category_primary, difficulty, 
                   tools_mentioned, summary_5_bullets, best_for, signal_score,
                   video_url, processing_status, teaches_agent_to, prompt_template,
                   execution_checklist, agent_training_script
            FROM directory_entries
        """)
        sqlite_entries = cursor.fetchall()
        conn.close()
        print(f"📊 Read {len(sqlite_entries)} entries from SQLite")
    except Exception as e:
        print(f"❌ Error reading SQLite: {e}")
        return False
    
    # Now, connect to Supabase and add entries
    try:
        # Use the same DATABASE_URL that production uses
        print("🔗 Using production DATABASE_URL...")
        # The script will use whatever DATABASE_URL is set in the environment
        
        from database import SessionLocal
        from models.directory import DirectoryEntry, ContentType
        from datetime import datetime
        import uuid
        
        print("🔗 Connecting to Supabase...")
        db = SessionLocal()
        
        # Check current count in Supabase
        supabase_count = db.query(DirectoryEntry).count()
        print(f"📊 Current Supabase count: {supabase_count}")
        
        success_count = 0
        
        for i, entry in enumerate(sqlite_entries, 1):
            try:
                # Check if entry already exists
                existing = db.query(DirectoryEntry).filter(
                    DirectoryEntry.title == entry[0]
                ).first()
                
                if existing:
                    print(f"⏭️  {i}/{len(sqlite_entries)}: Skipping existing - {entry[0][:30]}...")
                    continue
                
                # Create new entry
                new_entry = DirectoryEntry(
                    id=str(uuid.uuid4()),
                    title=entry[0] or "Untitled",
                    source_url=entry[8] or "",
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
                print(f"✅ {i}/{len(sqlite_entries)}: Added - {entry[0][:50]}...")
                
            except Exception as e:
                db.rollback()
                print(f"❌ {i}/{len(sqlite_entries)}: Failed - {e}")
        
        final_count = db.query(DirectoryEntry).count()
        print(f"\n🏁 Migration complete!")
        print(f"📊 Final Supabase count: {final_count}")
        print(f"✅ Successfully added: {success_count}")
        
        db.close()
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Supabase connection error: {e}")
        return False

if __name__ == "__main__":
    migrate_sqlite_to_supabase()