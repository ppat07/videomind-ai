#!/usr/bin/env python3
"""
Fix content_type enum values in production database.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import os
os.environ.setdefault("SECRET_KEY", "fix-key")
os.environ.setdefault("OPENAI_API_KEY", "fix-key")

def fix_content_types():
    """Fix content_type enum values in production."""
    
    from database import SessionLocal
    from models.directory import DirectoryEntry, ContentType
    
    db = SessionLocal()
    
    try:
        print("🔧 Fixing content_type enum values...")
        
        # Get all entries
        entries = db.query(DirectoryEntry).all()
        print(f"📊 Processing {len(entries)} entries...")
        
        fixed_count = 0
        
        for entry in entries:
            # Fix content_type to proper enum value
            if entry.content_type != ContentType.VIDEO and entry.content_type != ContentType.ARTICLE:
                # Default to VIDEO for existing entries
                entry.content_type = ContentType.VIDEO
                fixed_count += 1
        
        if fixed_count > 0:
            db.commit()
            print(f"✅ Fixed {fixed_count} content_type values")
        else:
            print("✅ All content_type values are already correct")
        
        # Verify the fix
        sample = db.query(DirectoryEntry).first()
        print(f"🔍 Sample content_type after fix: {sample.content_type}")
        print(f"🔍 Type: {type(sample.content_type)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_content_types()