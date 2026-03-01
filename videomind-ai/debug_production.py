#!/usr/bin/env python3
"""
Debug what's in the production database and why only 3 entries show.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import os
os.environ.setdefault("SECRET_KEY", "debug-key")
os.environ.setdefault("OPENAI_API_KEY", "debug-key")

def debug_production_database():
    """Check what's in production and why only 3 entries show."""
    
    from database import SessionLocal
    from models.directory import DirectoryEntry
    from sqlalchemy import text
    
    db = SessionLocal()
    
    try:
        print("🔍 Debugging production database...")
        
        # Count total entries
        total = db.query(DirectoryEntry).count()
        print(f"📊 Total entries in database: {total}")
        
        # Check for NULL or problematic content_type values
        null_content_type = db.query(DirectoryEntry).filter(DirectoryEntry.content_type.is_(None)).count()
        print(f"❓ Entries with NULL content_type: {null_content_type}")
        
        # Check content_type distribution
        result = db.execute(text("SELECT content_type, COUNT(*) FROM directory_entries GROUP BY content_type"))
        print("📊 Content type distribution:")
        for row in result:
            print(f"   {row[0]}: {row[1]} entries")
        
        # Get sample entries with their content_type values
        samples = db.query(DirectoryEntry).limit(10).all()
        print(f"📝 Sample entries (first 10):")
        for i, entry in enumerate(samples, 1):
            print(f"   {i}. '{entry.title[:50]}...' | content_type='{entry.content_type}' | signal_score={entry.signal_score}")
        
        # Check if there are entries that might be causing query issues
        problem_entries = db.query(DirectoryEntry).filter(
            (DirectoryEntry.source_url.is_(None)) &
            (DirectoryEntry.video_url.is_(None))
        ).count()
        print(f"⚠️  Entries with no URL: {problem_entries}")
        
        # Try the same query the API uses
        api_query = db.query(DirectoryEntry).order_by(DirectoryEntry.created_at.desc())
        api_count = api_query.count()
        print(f"🔎 API query count: {api_count}")
        
        api_results = api_query.limit(5).all()
        print("🔎 API query results (first 5):")
        for i, entry in enumerate(api_results, 1):
            print(f"   {i}. '{entry.title}' | {entry.content_type}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    debug_production_database()