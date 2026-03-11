"""
Auto-initialization endpoint for reliable database setup
This provides a bulletproof way to ensure database is seeded
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_database
from models.directory import DirectoryEntry
from api.directory import seed_directory_entries

router = APIRouter()


@router.get("/auto-init")
async def auto_initialize_database(db: Session = Depends(get_database)):
    """
    Auto-initialize database if empty. Safe to call multiple times.
    This is called automatically but can be triggered manually if needed.
    """
    try:
        # Check if directory has content
        count = db.query(DirectoryEntry).count()
        
        if count == 0:
            # Database is empty, seed it
            result = await seed_directory_entries(db)
            return {
                "status": "initialized",
                "action": "seeded_directory",
                "entries_created": 3,
                "message": "Database was empty, auto-seeded with OpenClaw videos"
            }
        else:
            # Database has content, no action needed
            return {
                "status": "already_initialized", 
                "action": "none",
                "current_entries": count,
                "message": f"Database already contains {count} entries"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "action": "failed",
            "error": str(e),
            "message": "Auto-initialization failed"
        }