"""
Validation utilities for VideoMind AI.
"""
import re
from typing import Optional, Tuple, Union
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse


def sanitize_video_url(url: str) -> str:
    """
    Sanitize video URL by removing unnecessary parameters.
    
    Args:
        url: Original video URL
        
    Returns:
        Cleaned URL with only essential parameters
    """
    try:
        parsed = urlparse(url.strip())
        
        # YouTube URL cleaning
        if 'youtube.com' in parsed.netloc or 'youtu.be' in parsed.netloc:
            query_params = parse_qs(parsed.query)
            
            # Keep only essential YouTube parameters
            essential_params = {}
            if 'v' in query_params:
                essential_params['v'] = query_params['v']
            if 'list' in query_params and 'playlist' not in url.lower():
                # Only keep playlist if it's explicitly a playlist URL
                pass
            
            # Remove timestamp parameters (t, start) - they're not needed for full video processing
            # Remove tracking parameters (feature, si, etc.)
            
            # Rebuild clean URL
            clean_query = urlencode(essential_params, doseq=True)
            clean_url = urlunparse((
                parsed.scheme or 'https',
                parsed.netloc,
                parsed.path,
                parsed.params,
                clean_query,
                ''  # Remove fragment
            ))
            
            return clean_url
        
        # Rumble URL cleaning
        elif 'rumble.com' in parsed.netloc:
            # Rumble URLs are usually clean, just remove fragments
            return urlunparse((
                parsed.scheme or 'https',
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                ''  # Remove fragment
            ))

        # X/Twitter URL cleaning — normalise x.com / twitter.com and strip tracking params
        elif parsed.netloc in ('twitter.com', 'www.twitter.com', 'x.com', 'www.x.com'):
            # Keep only the status path, drop query & fragment
            return urlunparse((
                parsed.scheme or 'https',
                parsed.netloc,
                parsed.path,
                '',
                '',
                ''
            ))

        # Vimeo URL cleaning
        elif 'vimeo.com' in parsed.netloc:
            return urlunparse((
                parsed.scheme or 'https',
                parsed.netloc,
                parsed.path,
                parsed.params,
                '',   # Drop query params (tracking)
                ''    # Drop fragment
            ))

        # Generic URL cleaning — strip fragment, keep everything else
        return urlunparse((
            parsed.scheme or 'https',
            parsed.netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            ''
        ))
        
    except Exception:
        # If parsing fails, return original URL
        return url.strip()


def validate_video_url(url: str) -> Tuple[bool, Union[dict, str]]:
    """
    Validate video URL from supported platforms and extract video info.

    Supported: YouTube, Rumble, X/Twitter, Vimeo, Dailymotion.
    Unknown HTTPS URLs are accepted as 'generic' (validated at download time by yt-dlp).

    Args:
        url: Video URL to validate

    Returns:
        Tuple of (is_valid, platform_info_dict or error_message)
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

        # X/Twitter URL patterns
        twitter_patterns = [
            r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/\w+/status/(\d+)',
            r'(?:https?://)?(?:www\.)?(?:twitter\.com|x\.com)/i/status/(\d+)',
        ]

        # Vimeo URL patterns
        vimeo_patterns = [
            r'(?:https?://)?(?:www\.)?vimeo\.com/(\d+)',
            r'(?:https?://)?player\.vimeo\.com/video/(\d+)',
        ]

        # Dailymotion URL patterns
        dailymotion_patterns = [
            r'(?:https?://)?(?:www\.)?dailymotion\.com/video/([a-zA-Z0-9]+)',
            r'(?:https?://)?dai\.ly/([a-zA-Z0-9]+)',
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
                if len(video_id) > 2:
                    return True, {"platform": "rumble", "video_id": video_id}
                else:
                    return False, "Invalid Rumble video ID format"

        # Check X/Twitter patterns
        for pattern in twitter_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                tweet_id = match.group(1)
                if len(tweet_id) >= 10:
                    return True, {"platform": "twitter", "video_id": tweet_id}
                else:
                    return False, "Invalid X/Twitter status ID format"

        # Check Vimeo patterns
        for pattern in vimeo_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                video_id = match.group(1)
                if len(video_id) >= 1:
                    return True, {"platform": "vimeo", "video_id": video_id}
                else:
                    return False, "Invalid Vimeo video ID format"

        # Check Dailymotion patterns
        for pattern in dailymotion_patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                video_id = match.group(1)
                if len(video_id) >= 2:
                    return True, {"platform": "dailymotion", "video_id": video_id}
                else:
                    return False, "Invalid Dailymotion video ID format"

        # Generic HTTPS fallback — accept any HTTPS URL and let yt-dlp validate at extraction time
        if url.startswith('https://'):
            parsed = urlparse(url.strip())
            if parsed.netloc and '.' in parsed.netloc:
                return True, {"platform": "generic", "video_id": None}

        if url.startswith('http://'):
            return False, "Only HTTPS URLs are supported for security. Please use an https:// URL."

        return False, "Invalid URL format. Please enter a valid video URL (YouTube, X, Vimeo, etc.)."

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


def extract_video_id_from_url(url: str) -> Optional[str]:
    """
    Extract video ID from a YouTube URL.
    
    Args:
        url: YouTube URL
        
    Returns:
        Video ID if found, None otherwise
    """
    is_valid, result = validate_video_url(url)
    if is_valid and isinstance(result, dict) and result.get("platform") == "youtube":
        return result.get("video_id")
    return None


def extract_video_info(url: str) -> dict:
    """
    Extract basic info from supported video platform URLs.

    Args:
        url: Video URL

    Returns:
        Dictionary with video info
    """
    is_valid, result = validate_video_url(url)

    if not is_valid:
        return {"valid": False, "error": result}

    platform = result["platform"]
    video_id = result["video_id"]

    if platform == "youtube":
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
        url_type = "watch" if "/v" in url else "embed"
        return {
            "valid": True,
            "platform": "rumble",
            "video_id": video_id,
            "url_type": url_type,
            "watch_url": f"https://rumble.com/v{video_id}",
            "embed_url": f"https://rumble.com/embed/v{video_id}",
            "thumbnail_url": None
        }

    elif platform == "twitter":
        return {
            "valid": True,
            "platform": "twitter",
            "video_id": video_id,
            "url_type": "status",
            "watch_url": f"https://x.com/i/status/{video_id}",
            "embed_url": None,
            "thumbnail_url": None
        }

    elif platform == "vimeo":
        return {
            "valid": True,
            "platform": "vimeo",
            "video_id": video_id,
            "url_type": "watch",
            "watch_url": f"https://vimeo.com/{video_id}",
            "embed_url": f"https://player.vimeo.com/video/{video_id}",
            "thumbnail_url": None  # Vimeo thumbnails require API call
        }

    elif platform == "dailymotion":
        return {
            "valid": True,
            "platform": "dailymotion",
            "video_id": video_id,
            "url_type": "watch",
            "watch_url": f"https://www.dailymotion.com/video/{video_id}",
            "embed_url": f"https://www.dailymotion.com/embed/video/{video_id}",
            "thumbnail_url": f"https://www.dailymotion.com/thumbnail/video/{video_id}"
        }

    elif platform == "generic":
        return {
            "valid": True,
            "platform": "generic",
            "video_id": None,
            "url_type": "generic",
            "watch_url": url.strip(),
            "embed_url": None,
            "thumbnail_url": None
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