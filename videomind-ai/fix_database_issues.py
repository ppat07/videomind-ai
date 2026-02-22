#!/usr/bin/env python3
"""
Fix database integrity issues that are preventing proper API responses.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import os
os.environ.setdefault("SECRET_KEY", "demo-key")
os.environ.setdefault("OPENAI_API_KEY", "demo-key")

from database import SessionLocal
from models.directory import DirectoryEntry, ContentType
from datetime import datetime
from sqlalchemy import text

def fix_database_issues():
    """Fix all database integrity issues."""
    db = SessionLocal()
    
    try:
        print("🔧 Fixing database integrity issues...")
        
        # 1. Fix content_type enum values
        print("1. Fixing content_type values...")
        result = db.execute(text("UPDATE directory_entries SET content_type = 'VIDEO' WHERE content_type NOT IN ('VIDEO', 'ARTICLE')"))
        print(f"   Fixed {result.rowcount} content_type values")
        
        # 2. Fix NULL datetime fields
        print("2. Fixing datetime fields...")
        current_time = datetime.utcnow().isoformat()
        
        result1 = db.execute(text(f"UPDATE directory_entries SET created_at = '{current_time}' WHERE created_at IS NULL"))
        result2 = db.execute(text(f"UPDATE directory_entries SET updated_at = '{current_time}' WHERE updated_at IS NULL"))
        print(f"   Fixed {result1.rowcount} created_at and {result2.rowcount} updated_at values")
        
        # 3. Fix signal_score out of range values
        print("3. Fixing signal_score values...")
        result = db.execute(text("UPDATE directory_entries SET signal_score = 70 WHERE signal_score IS NULL OR signal_score < 1 OR signal_score > 100"))
        print(f"   Fixed {result.rowcount} signal_score values")
        
        # 4. Fix NULL video_url for video entries
        print("4. Fixing video_url values...")
        result = db.execute(text("UPDATE directory_entries SET video_url = source_url WHERE video_url IS NULL AND content_type = 'VIDEO'"))
        print(f"   Fixed {result.rowcount} video_url values")
        
        # 5. Set source_url from video_url if missing
        print("5. Fixing source_url values...")
        result = db.execute(text("UPDATE directory_entries SET source_url = video_url WHERE source_url IS NULL AND video_url IS NOT NULL"))
        print(f"   Fixed {result.rowcount} source_url values")
        
        db.commit()
        print("✅ Database integrity fixes applied successfully!")
        
        # Verify the fixes
        print("\n📊 Verification:")
        
        # Check total count
        total = db.execute(text("SELECT COUNT(*) FROM directory_entries")).scalar()
        print(f"   Total entries: {total}")
        
        # Check content types
        content_types = db.execute(text("SELECT content_type, COUNT(*) FROM directory_entries GROUP BY content_type")).fetchall()
        for ct, count in content_types:
            print(f"   {ct}: {count}")
        
        # Check for any remaining issues
        issues = db.execute(text("SELECT COUNT(*) FROM directory_entries WHERE created_at IS NULL OR signal_score IS NULL")).scalar()
        print(f"   Remaining data issues: {issues}")
        
        if issues == 0:
            print("🎉 All data integrity issues resolved!")
        else:
            print(f"⚠️ {issues} issues remain")
            
    except Exception as e:
        print(f"❌ Error fixing database: {e}")
        db.rollback()
        
    finally:
        db.close()

if __name__ == "__main__":
    fix_database_issues()