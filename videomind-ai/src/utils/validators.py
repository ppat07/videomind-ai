"""
Validation utilities for VideoMind AI.
"""
import re
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs


def validate_video_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate video URL from supported platforms (YouTube, Rumble) and extract video info.
    
    Args:
        url: Video URL to validate
        
    Returns:
        Tuple of (is_valid, platform_info or error_message)
    """
    try:
        # YouTube URL patterns
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^&\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([^&\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([^&\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^&\n?#]+)'
        ]
        
        # Rumble URL patterns
        rumble_patterns = [
            r'(?:https?://)?(?:www\.)?rumble\.com/v([^/\n?#]+?)(?:\.html)?(?:[/?#]|$)',
            r'(?:https?://)?(?:www\.)?rumble\.com/embed/v([^/\n?#]+?)(?:\.html)?(?:[/?#]|$)',
        ]
        
        # Check YouTube patterns
        for pattern in youtube_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                video_id = match.group(1)
                # Validate YouTube video ID format (11 characters)
                if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
                    return True, {"platform": "youtube", "video_id": video_id}
                else:
                    return False, "Invalid YouTube video ID format"
        
        # Check Rumble patterns
        for pattern in rumble_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                video_id = match.group(1)
                # Rumble video IDs are more flexible
                if len(video_id) > 2:
                    return True, {"platform": "rumble", "video_id": video_id}
                else:
                    return False, "Invalid Rumble video ID format"
        
        # Check if it's a valid URL but unsupported platform
        if url.startswith(('http://', 'https://')) or '.' in url:
            return False, "Unsupported platform. Please use YouTube or Rumble URLs."
        
        return False, "Invalid URL format. Please enter a valid YouTube or Rumble URL."
        
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


def validate_youtube_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Legacy function for backwards compatibility.
    Now uses the new validate_video_url function.
    """
    is_valid, result = validate_video_url(url)
    if is_valid and isinstance(result, dict):
        return True, result.get("video_id")
    return False, result


def extract_video_info(url: str) -> dict:
    """
    Extract basic info from supported video platform URLs.
    
    Args:
        url: Video URL (YouTube or Rumble)
        
    Returns:
        Dictionary with video info
    """
    is_valid, result = validate_video_url(url)
    
    if not is_valid:
        return {"valid": False, "error": result}
    
    platform = result["platform"]
    video_id = result["video_id"]
    
    if platform == "youtube":
        # Determine YouTube URL type
        url_type = "unknown"
        if "youtu.be" in url:
            url_type = "short"
        elif "youtube.com/watch" in url:
            url_type = "watch"
        elif "youtube.com/embed" in url:
            url_type = "embed"
        elif "youtube.com/shorts" in url:
            url_type = "shorts"
        
        return {
            "valid": True,
            "platform": "youtube",
            "video_id": video_id,
            "url_type": url_type,
            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
            "embed_url": f"https://www.youtube.com/embed/{video_id}",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        }
    
    elif platform == "rumble":
        # Determine Rumble URL type
        url_type = "watch" if "/v" in url else "embed"
        
        return {
            "valid": True,
            "platform": "rumble",
            "video_id": video_id,
            "url_type": url_type,
            "watch_url": f"https://rumble.com/v{video_id}",
            "embed_url": f"https://rumble.com/embed/v{video_id}",
            "thumbnail_url": None  # Rumble doesn't have predictable thumbnail URLs
        }
    
    return {"valid": False, "error": "Unsupported platform"}


def extract_youtube_video_info(url: str) -> dict:
    """
    Legacy function for backwards compatibility.
    Now uses the new extract_video_info function.
    """
    return extract_video_info(url)


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    safe_filename = re.sub(r'[^\w\s.-]', '_', filename)
    # Remove multiple spaces and replace with single underscore
    safe_filename = re.sub(r'\s+', '_', safe_filename)
    # Remove multiple underscores
    safe_filename = re.sub(r'_+', '_', safe_filename)
    # Trim underscores from start and end
    safe_filename = safe_filename.strip('_')
    
    return safe_filename[:100]  # Limit length


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string (e.g., "5m 30s", "1h 23m")
    """
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s" if secs > 0 else f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m" if minutes > 0 else f"{hours}h"


def estimate_processing_cost(duration_seconds: int, tier: str) -> float:
    """
    Estimate processing cost based on video duration and tier.
    
    Args:
        duration_seconds: Video duration in seconds
        tier: Processing tier (basic, detailed, bulk)
        
    Returns:
        Estimated cost in dollars
    """
    # Base costs per minute
    base_costs = {
        "basic": 0.05,    # $0.05 per minute
        "detailed": 0.08, # $0.08 per minute
        "bulk": 0.03      # $0.03 per minute
    }
    
    duration_minutes = max(1, duration_seconds // 60)  # Minimum 1 minute
    cost_per_minute = base_costs.get(tier, base_costs["basic"])
    
    return round(duration_minutes * cost_per_minute, 2)