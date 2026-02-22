"""
Helper utilities for VideoMind AI.
"""
import os
import json
import hashlib
import tempfile
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from pathlib import Path

from config import settings


def generate_job_id() -> str:
    """Generate a unique job ID."""
    import uuid
    return str(uuid.uuid4())


def get_temp_file_path(job_id: str, extension: str) -> str:
    """
    Generate temporary file path for a job.
    
    Args:
        job_id: Unique job identifier
        extension: File extension (with or without dot)
        
    Returns:
        Full path to temporary file
    """
    if not extension.startswith('.'):
        extension = '.' + extension
    
    temp_dir = Path(settings.temp_storage_path)
    temp_dir.mkdir(exist_ok=True)
    
    filename = f"{job_id}{extension}"
    return str(temp_dir / filename)


def cleanup_temp_files(job_id: str) -> int:
    """
    Clean up temporary files for a job.
    
    Args:
        job_id: Job ID to clean up
        
    Returns:
        Number of files deleted
    """
    temp_dir = Path(settings.temp_storage_path)
    deleted_count = 0
    
    for file_path in temp_dir.glob(f"{job_id}*"):
        try:
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    
    return deleted_count


def cleanup_old_files(days_old: int = None) -> int:
    """
    Clean up files older than specified days.
    
    Args:
        days_old: Number of days (defaults to settings.file_cleanup_days)
        
    Returns:
        Number of files deleted
    """
    if days_old is None:
        days_old = settings.file_cleanup_days
    
    cutoff_date = datetime.now() - timedelta(days=days_old)
    temp_dir = Path(settings.temp_storage_path)
    deleted_count = 0
    
    for file_path in temp_dir.glob("*"):
        try:
            if file_path.is_file():
                # Check file modification time
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1
        except Exception as e:
            print(f"Error cleaning up {file_path}: {e}")
    
    return deleted_count


def save_json_file(data: Dict[Any, Any], file_path: str) -> bool:
    """
    Save data as JSON file.
    
    Args:
        data: Data to save
        file_path: Path to save file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving JSON to {file_path}: {e}")
        return False


def load_json_file(file_path: str) -> Optional[Dict[Any, Any]]:
    """
    Load JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded data or None if error
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON from {file_path}: {e}")
        return None


def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> Optional[str]:
    """
    Calculate hash of a file.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm (md5, sha256)
        
    Returns:
        File hash or None if error
    """
    try:
        hash_func = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        print(f"Error calculating hash for {file_path}: {e}")
        return None


def format_bytes(bytes_count: int) -> str:
    """
    Format bytes to human readable format.
    
    Args:
        bytes_count: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"


def get_file_size(file_path: str) -> Optional[int]:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes or None if error
    """
    try:
        return os.path.getsize(file_path)
    except Exception:
        return None


def ensure_directory(directory_path: str) -> bool:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {directory_path}: {e}")
        return False


def generate_download_token(job_id: str, format_type: str) -> str:
    """
    Generate secure download token.
    
    Args:
        job_id: Job identifier
        format_type: File format type
        
    Returns:
        Secure download token
    """
    data = f"{job_id}:{format_type}:{datetime.now().isoformat()}"
    return hashlib.sha256(f"{data}:{settings.secret_key}".encode()).hexdigest()[:32]


def verify_download_token(job_id: str, format_type: str, token: str) -> bool:
    """
    Verify download token (simplified version for MVP).
    
    Args:
        job_id: Job identifier
        format_type: File format type
        token: Token to verify
        
    Returns:
        True if token is valid
    """
    # For MVP, we'll use a simple token system
    # In production, you'd want time-based tokens with expiration
    expected_token = generate_download_token(job_id, format_type)
    return token == expected_token