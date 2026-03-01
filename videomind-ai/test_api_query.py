#!/usr/bin/env python3
"""
Test the exact API query to see where entries are lost.
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import os
os.environ.setdefault("SECRET_KEY", "test-key")
os.environ.setdefault("OPENAI_API_KEY", "test-key")

def test_api_query():
    """Test the exact API query logic."""
    
    from database import SessionLocal
    from models.directory import DirectoryEntry
    from sqlalchemy import func
    
    db = SessionLocal()
    
    try:
        print("🔍 Testing API query logic...")
        
        # Replicate the exact API query
        query = db.query(DirectoryEntry)
        
        total_count = query.with_entities(func.count(DirectoryEntry.id)).scalar() or 0
        print(f"📊 Query count: {total_count}")
        
        # Default sorting (newest first)
        query = query.order_by(DirectoryEntry.created_at.desc())
        
        # Default pagination
        limit = 24
        offset = 0
        rows = query.offset(offset).limit(limit).all()
        
        print(f"📝 Retrieved {len(rows)} rows from query")
        
        # Try to serialize like the API does
        items = []
        for i, r in enumerate(rows):
            try:
                item = {
                    "id": r.id,
                    "title": r.title,
                    "video_url": r.video_url,
                    "source_url": r.source_url or r.video_url,
                    "content_type": r.content_type.value if r.content_type else "video",
                    "creator_name": r.creator_name,
                    "category_primary": r.category_primary,
                    "difficulty": r.difficulty,
                    "tools_mentioned": r.tools_mentioned,
                    "summary_5_bullets": r.summary_5_bullets,
                    "best_for": r.best_for,
                    "signal_score": r.signal_score,
                    "processing_status": r.processing_status,
                }
                items.append(item)
                print(f"✅ {i+1}. Serialized: {r.title[:30]}...")
            except Exception as e:
                print(f"❌ {i+1}. Failed to serialize: {e}")
                print(f"   Entry: {r.title[:30]}...")
                print(f"   content_type: {r.content_type}")
                print(f"   source_url: {r.source_url}")
                print(f"   video_url: {r.video_url}")
        
        print(f"🏁 Successfully serialized {len(items)} out of {len(rows)} entries")
        
    except Exception as e:
        print(f"❌ Query error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_api_query()