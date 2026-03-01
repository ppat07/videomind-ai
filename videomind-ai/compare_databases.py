#!/usr/bin/env python3
"""
Compare what we see locally vs what production sees in Supabase.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import os
os.environ.setdefault("SECRET_KEY", "compare-key")
os.environ.setdefault("OPENAI_API_KEY", "compare-key")

def compare_databases():
    """Compare local view vs production view of the same database."""
    
    from database import SessionLocal
    from models.directory import DirectoryEntry
    from sqlalchemy import text
    
    db = SessionLocal()
    
    try:
        print("🔍 Comparing local vs production database views...")
        
        # Get the first 5 entries from our local connection
        local_entries = db.query(DirectoryEntry).order_by(DirectoryEntry.created_at.desc()).limit(5).all()
        print(f"\n📊 LOCAL VIEW (Supabase connection):")
        print(f"   Total count: {db.query(DirectoryEntry).count()}")
        print(f"   First 5 entries:")
        for i, entry in enumerate(local_entries, 1):
            print(f"     {i}. ID: {entry.id}")
            print(f"        Title: {entry.title[:50]}...")
            print(f"        Created: {entry.created_at}")
        
        # Get database connection info
        result = db.execute(text("SELECT current_database(), current_user, version()"))
        db_info = result.fetchone()
        print(f"\n🔗 DATABASE INFO:")
        print(f"   Database: {db_info[0]}")
        print(f"   User: {db_info[1]}")
        print(f"   Version: {db_info[2][:50]}...")
        
        # Check table structure
        result = db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name='directory_entries' 
            ORDER BY ordinal_position LIMIT 10
        """))
        print(f"\n📋 TABLE SCHEMA (first 10 columns):")
        for row in result:
            print(f"   {row[0]}: {row[1]}")
        
        print(f"\n🌐 PRODUCTION API SEES:")
        print(f"   Total count: 3")
        print(f"   First item ID: 9dca150d-2b2e-4371-b720-c5bc49d1f7d1")
        print(f"   Created: 2026-02-20T15:45:47.456913")
        
        # Check if that specific ID exists in our local view
        production_id = "9dca150d-2b2e-4371-b720-c5bc49d1f7d1"
        local_has_prod_id = db.query(DirectoryEntry).filter(DirectoryEntry.id == production_id).first()
        print(f"\n🔍 Cross-check:")
        print(f"   Local database contains production's first ID: {'✅ YES' if local_has_prod_id else '❌ NO'}")
        
        if local_has_prod_id:
            print(f"   That entry title: {local_has_prod_id.title}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    compare_databases()