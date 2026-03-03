"""
YouTube Data API v3 Service for VideoMind AI
Enriches video metadata with official YouTube API data including channel info, 
subscriber counts, engagement metrics, and enhanced video details.
"""
import os
import re
import requests
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timezone

from config import settings
from utils.validators import extract_video_id_from_url


class YouTubeDataService:
    """Service for interacting with YouTube Data API v3."""
    
    def __init__(self):
        """Initialize YouTube Data API service."""
        self.api_key = settings.youtube_data_api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    def is_available(self) -> bool:
        """Check if YouTube Data API is available (API key configured)."""
        return bool(self.api_key)
    
    def _make_api_request(self, endpoint: str, params: Dict) -> Tuple[bool, Dict]:
        """
        Make a request to YouTube Data API v3.
        
        Args:
            endpoint: API endpoint (videos, channels, etc.)
            params: Query parameters
            
        Returns:
            Tuple of (success, response_data or error_dict)
        """
        if not self.api_key:
            return False, {"error": "YouTube Data API key not configured"}
        
        # Add API key to params
        params["key"] = self.api_key
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 403:
                error_data = response.json()
                error_reason = error_data.get("error", {}).get("errors", [{}])[0].get("reason", "forbidden")
                
                if error_reason == "quotaExceeded":
                    return False, {"error": "YouTube Data API quota exceeded"}
                elif error_reason == "keyInvalid":
                    return False, {"error": "YouTube Data API key is invalid"}
                else:
                    return False, {"error": f"YouTube Data API access forbidden: {error_reason}"}
            elif response.status_code == 404:
                return False, {"error": "Video not found or is private"}
            else:
                return False, {"error": f"YouTube Data API error: {response.status_code}"}
                
        except requests.exceptions.RequestException as e:
            return False, {"error": f"Network error accessing YouTube Data API: {str(e)}"}
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}
    
    def get_video_details(self, video_id: str) -> Tuple[bool, Dict]:
        """
        Get comprehensive video details using YouTube Data API.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Tuple of (success, video_data or error_dict)
        """
        params = {
            "part": "snippet,statistics,contentDetails,status",
            "id": video_id
        }
        
        success, response = self._make_api_request("videos", params)
        
        if not success:
            return False, response
        
        items = response.get("items", [])
        if not items:
            return False, {"error": "Video not found"}
        
        video_data = items[0]
        snippet = video_data.get("snippet", {})
        statistics = video_data.get("statistics", {})
        content_details = video_data.get("contentDetails", {})
        status = video_data.get("status", {})
        
        # Parse duration from ISO 8601 format (PT4M13S -> 253 seconds)
        duration_iso = content_details.get("duration", "PT0S")
        duration_seconds = self._parse_iso_duration(duration_iso)
        
        # Parse publish date
        published_at = snippet.get("publishedAt")
        publish_date = None
        if published_at:
            try:
                publish_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            except:
                pass
        
        # Extract enriched metadata
        enriched_data = {
            "video_id": video_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "channel_id": snippet.get("channelId"),
            "channel_title": snippet.get("channelTitle"),
            "publish_date": publish_date,
            "publish_date_formatted": publish_date.strftime("%Y-%m-%d") if publish_date else None,
            "duration_seconds": duration_seconds,
            "duration_formatted": self._format_duration(duration_seconds),
            
            # Engagement metrics
            "view_count": int(statistics.get("viewCount", 0)),
            "like_count": int(statistics.get("likeCount", 0)),
            "comment_count": int(statistics.get("commentCount", 0)),
            "favorite_count": int(statistics.get("favoriteCount", 0)),
            
            # Content metadata
            "category_id": snippet.get("categoryId"),
            "default_language": snippet.get("defaultLanguage"),
            "default_audio_language": snippet.get("defaultAudioLanguage"),
            "tags": snippet.get("tags", []),
            
            # Thumbnails
            "thumbnail_default": snippet.get("thumbnails", {}).get("default", {}).get("url"),
            "thumbnail_medium": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
            "thumbnail_high": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            "thumbnail_maxres": snippet.get("thumbnails", {}).get("maxres", {}).get("url"),
            
            # Status and availability
            "privacy_status": status.get("privacyStatus"),
            "upload_status": status.get("uploadStatus"),
            "embeddable": status.get("embeddable", True),
            "license": status.get("license"),
            "made_for_kids": status.get("madeForKids", False),
            
            # Content details
            "definition": content_details.get("definition"),
            "caption": content_details.get("caption"),
            "licensed_content": content_details.get("licensedContent", False)
        }
        
        return True, enriched_data
    
    def get_channel_details(self, channel_id: str) -> Tuple[bool, Dict]:
        """
        Get channel details including subscriber count and channel metadata.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Tuple of (success, channel_data or error_dict)
        """
        params = {
            "part": "snippet,statistics,brandingSettings,status",
            "id": channel_id
        }
        
        success, response = self._make_api_request("channels", params)
        
        if not success:
            return False, response
        
        items = response.get("items", [])
        if not items:
            return False, {"error": "Channel not found"}
        
        channel_data = items[0]
        snippet = channel_data.get("snippet", {})
        statistics = channel_data.get("statistics", {})
        branding = channel_data.get("brandingSettings", {})
        status = channel_data.get("status", {})
        
        # Parse channel creation date
        published_at = snippet.get("publishedAt")
        creation_date = None
        if published_at:
            try:
                creation_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            except:
                pass
        
        channel_info = {
            "channel_id": channel_id,
            "title": snippet.get("title", ""),
            "description": snippet.get("description", ""),
            "custom_url": snippet.get("customUrl"),
            "creation_date": creation_date,
            "creation_date_formatted": creation_date.strftime("%Y-%m-%d") if creation_date else None,
            "country": snippet.get("country"),
            "default_language": snippet.get("defaultLanguage"),
            
            # Channel statistics
            "subscriber_count": int(statistics.get("subscriberCount", 0)),
            "video_count": int(statistics.get("videoCount", 0)),
            "view_count": int(statistics.get("viewCount", 0)),
            "hidden_subscriber_count": statistics.get("hiddenSubscriberCount", False),
            
            # Thumbnails
            "thumbnail_default": snippet.get("thumbnails", {}).get("default", {}).get("url"),
            "thumbnail_medium": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
            "thumbnail_high": snippet.get("thumbnails", {}).get("high", {}).get("url"),
            
            # Branding
            "keywords": branding.get("channel", {}).get("keywords"),
            "unsubscribed_trailer": branding.get("channel", {}).get("unsubscribedTrailer"),
            
            # Status
            "privacy_status": status.get("privacyStatus"),
            "is_linked": status.get("isLinked"),
            "made_for_kids": status.get("madeForKids", False)
        }
        
        return True, channel_info
    
    def get_basic_video_info(self, url: str) -> Tuple[bool, Dict]:
        """
        Get basic video information using YouTube Data API (compatible with yt-dlp format).
        This replaces the yt-dlp get_video_info call to avoid bot detection.
        
        Args:
            url: YouTube URL
            
        Returns:
            Tuple of (success, video_info_dict) in yt-dlp compatible format
        """
        try:
            video_id = extract_video_id_from_url(url)
            if not video_id:
                return False, {"error": "Could not extract video ID from URL"}
            
            success, video_data = self.get_video_details(video_id)
            if not success:
                return False, video_data
            
            # Convert to yt-dlp compatible format (video_data is already processed)
            video_info = {
                "id": video_data["video_id"],
                "title": video_data["title"],
                "description": video_data["description"],
                "duration": video_data["duration_seconds"],
                "view_count": video_data["view_count"],
                "upload_date": video_data["publish_date_formatted"].replace("-", "") if video_data.get("publish_date_formatted") else "",
                "uploader": video_data["channel_title"],
                "uploader_id": video_data["channel_id"],
                "channel_id": video_data["channel_id"],
                "thumbnail": video_data.get("thumbnail_high", ""),
                "webpage_url": url,
                "success": True
            }
            
            return True, video_info
            
        except Exception as e:
            return False, {"error": f"YouTube Data API error: {str(e)}"}

    def get_enriched_video_data(self, youtube_url: str) -> Tuple[bool, Dict]:
        """
        Get comprehensive video and channel data from YouTube Data API.
        
        Args:
            youtube_url: Full YouTube URL
            
        Returns:
            Tuple of (success, enriched_data or error_dict)
        """
        # Extract video ID
        video_id = extract_video_id_from_url(youtube_url)
        if not video_id:
            return False, {"error": "Could not extract video ID from URL"}
        
        # Get video details
        video_success, video_data = self.get_video_details(video_id)
        if not video_success:
            return False, video_data
        
        # Get channel details
        channel_id = video_data.get("channel_id")
        channel_success = False
        channel_data = {}
        
        if channel_id:
            channel_success, channel_data = self.get_channel_details(channel_id)
            if not channel_success:
                # Continue even if channel data fails - video data is more important
                channel_data = {"error": channel_data.get("error", "Channel data unavailable")}
        
        # Calculate engagement metrics
        view_count = video_data.get("view_count", 0)
        like_count = video_data.get("like_count", 0)
        comment_count = video_data.get("comment_count", 0)
        subscriber_count = channel_data.get("subscriber_count", 0) if channel_success else 0
        
        # Calculate engagement rates
        like_rate = (like_count / view_count * 100) if view_count > 0 else 0
        comment_rate = (comment_count / view_count * 100) if view_count > 0 else 0
        engagement_score = like_rate + comment_rate
        
        # Combine all data
        enriched_data = {
            "success": True,
            "video": video_data,
            "channel": channel_data if channel_success else None,
            "channel_error": None if channel_success else channel_data.get("error"),
            
            # Computed metrics
            "engagement_metrics": {
                "like_rate": round(like_rate, 2),
                "comment_rate": round(comment_rate, 2),
                "engagement_score": round(engagement_score, 2),
                "views_per_subscriber": round(view_count / subscriber_count, 2) if subscriber_count > 0 else 0
            },
            
            # Formatted summary
            "formatted_summary": self._format_video_summary(video_data, channel_data if channel_success else None),
            
            # API metadata
            "api_source": "youtube_data_api_v3",
            "enrichment_timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return True, enriched_data
    
    def _parse_iso_duration(self, duration_iso: str) -> int:
        """
        Parse ISO 8601 duration format (PT4M13S) to seconds.
        
        Args:
            duration_iso: ISO 8601 duration string
            
        Returns:
            Duration in seconds
        """
        if not duration_iso or duration_iso == "PT0S":
            return 0
        
        # Parse PT4M13S format using regex
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_iso)
        
        if not match:
            return 0
        
        hours, minutes, seconds = match.groups()
        
        total_seconds = 0
        if hours:
            total_seconds += int(hours) * 3600
        if minutes:
            total_seconds += int(minutes) * 60
        if seconds:
            total_seconds += int(seconds)
        
        return total_seconds
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration in seconds to human readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def _format_video_summary(self, video_data: Dict, channel_data: Optional[Dict]) -> str:
        """
        Format a human-readable video summary.
        
        Args:
            video_data: Video metadata
            channel_data: Channel metadata (optional)
            
        Returns:
            Formatted summary string
        """
        title = video_data.get("title", "Unknown Title")
        view_count = video_data.get("view_count", 0)
        duration = video_data.get("duration_formatted", "Unknown duration")
        publish_date = video_data.get("publish_date_formatted", "Unknown date")
        
        summary_parts = [
            f"📺 {title}",
            f"👀 {view_count:,} views",
            f"⏰ {duration}",
            f"📅 Published {publish_date}"
        ]
        
        if channel_data:
            channel_title = channel_data.get("title", "")
            subscriber_count = channel_data.get("subscriber_count", 0)
            if channel_title:
                summary_parts.append(f"📢 {channel_title}")
            if subscriber_count > 0:
                summary_parts.append(f"👥 {subscriber_count:,} subscribers")
        
        return " | ".join(summary_parts)
    
    def get_video_categories(self, region_code: str = "US") -> Tuple[bool, Dict]:
        """
        Get available video categories for a region.
        
        Args:
            region_code: ISO 3166-1 alpha-2 country code
            
        Returns:
            Tuple of (success, categories_data or error_dict)
        """
        params = {
            "part": "snippet",
            "regionCode": region_code
        }
        
        success, response = self._make_api_request("videoCategories", params)
        
        if not success:
            return False, response
        
        categories = {}
        for item in response.get("items", []):
            category_id = item.get("id")
            category_title = item.get("snippet", {}).get("title")
            if category_id and category_title:
                categories[category_id] = category_title
        
        return True, {"categories": categories, "region_code": region_code}


# Global service instance
youtube_data_service = YouTubeDataService()