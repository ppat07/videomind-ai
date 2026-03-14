"""
Admin endpoints for VideoMind AI
Secure access for batch operations and admin functions
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
import secrets

from database import get_database
from config import settings

router = APIRouter()
security = HTTPBasic()

# Simple admin authentication
ADMIN_USERNAME = "videomind_admin"
ADMIN_PASSWORD = "vm_admin_2026!"  # Change in production

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify admin credentials."""
    is_correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@router.get("/admin/batch-access")
async def check_batch_access(admin_user: str = Depends(verify_admin)):
    """Check if user has admin access to batch features."""
    return {
        "success": True,
        "admin_user": admin_user,
        "batch_access": True,
        "message": "Admin access verified for batch operations"
    }

@router.post("/admin/directory-seed")
async def admin_directory_seed(
    admin_user: str = Depends(verify_admin),
    db: Session = Depends(get_database)
):
    """Admin-only directory seeding."""
    from api.directory import seed_directory_entries
    
    result = await seed_directory_entries(db)
    return {
        "admin_action": "directory_seed",
        "admin_user": admin_user,
        **result
    }

@router.post("/admin/enhance-training-scripts")
async def admin_enhance_training_scripts(
    admin_user: str = Depends(verify_admin),
    db: Session = Depends(get_database)
):
    """Admin-only: Enhance all existing training scripts with new format."""
    from models.directory import DirectoryEntry
    from utils.directory_mapper import build_agent_training_script, build_execution_checklist
    
    # Get all directory entries
    entries = db.query(DirectoryEntry).all()
    
    if not entries:
        return {
            "admin_action": "enhance_training_scripts",
            "admin_user": admin_user,
            "success": False,
            "message": "No directory entries found",
            "updated_count": 0
        }
    
    updated_count = 0
    for entry in entries:
        # Generate enhanced training script
        checklist = build_execution_checklist(entry.category_primary)
        enhanced_script = build_agent_training_script(
            entry.title,
            entry.summary_5_bullets,
            checklist
        )
        
        # Update if the new script is significantly longer (enhanced format)
        current_length = len(entry.agent_training_script or "")
        enhanced_length = len(enhanced_script)
        
        if enhanced_length > current_length * 1.5:  # At least 50% longer
            entry.agent_training_script = enhanced_script
            updated_count += 1
    
    # Commit all updates
    db.commit()
    
    return {
        "admin_action": "enhance_training_scripts",
        "admin_user": admin_user,
        "success": True,
        "message": f"Enhanced {updated_count} training scripts",
        "total_entries": len(entries),
        "updated_count": updated_count
    }