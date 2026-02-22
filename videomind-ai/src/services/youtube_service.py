"""
Enhanced video processing service with advanced anti-detection.
Handles downloading audio from supported platforms (YouTube, Rumble) with robust bypass techniques.
"""
import os
import yt_dlp
import shutil
import subprocess
import glob
import time
import random
from typing import Dict, Optional, Tuple
from pathlib import Path

from config import settings
from utils.helpers import get_temp_file_path, format_bytes
from utils.validators import validate_video_url, format_duration
from .transcription_service import transcription_service


class YouTubeService:
    """Enhanced service for downloading and processing YouTube videos with anti-detection."""
    
    def __init__(self):
        """Initialize YouTube service with enhanced capabilities."""
        self.temp_dir = Path(settings.temp_storage_path)
        self.temp_dir.mkdir(exist_ok=True)
        self.ffmpeg_location = self._find_ffmpeg_location()
        
        # Anti-detection user agents (rotate randomly)
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
    
    def _find_ffmpeg_location(self) -> Optional[str]:
        """Find ffmpeg installation location."""
        # Try common locations
        possible_locations = [
            '/opt/homebrew/bin/',  # Homebrew on Apple Silicon
            '/usr/local/bin/',     # Homebrew on Intel Mac
            '/usr/bin/',           # System installation
            None                   # Let yt-dlp find it
        ]
        
        for location in possible_locations:
            if location is None:
                continue
            ffmpeg_path = os.path.join(location, 'ffmpeg')
            if os.path.isfile(ffmpeg_path) and os.access(ffmpeg_path, os.X_OK):
                print(f"Found ffmpeg at: {location}")
                return location
        
        # Try using 'which' command
        try:
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            if result.returncode == 0:
                ffmpeg_path = result.stdout.strip()
                location = os.path.dirname(ffmpeg_path) + '/'
                print(f"Found ffmpeg via 'which': {location}")
                return location
        except Exception:
            pass
        
        print("⚠️  Warning: Could not find ffmpeg location")
        return None
    
    def _get_enhanced_ydl_opts(self, for_download: bool = False) -> Dict:
        """Get enhanced yt-dlp options with latest anti-detection techniques."""
        
        # Rotate user agent randomly
        user_agent = random.choice(self.user_agents)
        
        base_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            
            # Enhanced anti-detection headers
            'http_headers': {
                'User-Agent': user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Sec-CH-UA': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'Sec-CH-UA-Mobile': '?0',
                'Sec-CH-UA-Platform': '"macOS"',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
            },
            
            # Enhanced extractor arguments
            'extractor_args': {
                'youtube': {
                    'skip': ['hls', 'dash'],  # Skip problematic formats
                    'player_skip': ['configs', 'webpage'],
                    'player_client': ['android', 'web'],  # Use multiple clients
                },
                'youtubetab': {
                    'skip': ['webpage']
                }
            },
            
            # Throttling and delays for anti-detection
            'sleep_interval_requests': random.uniform(1, 3),  # Random delay between requests
            'sleep_interval': random.uniform(0.5, 2),         # Random delay between operations
            'sleep_interval_subtitles': random.uniform(1, 2),
            
            # Additional anti-bot measures
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            
            # Network settings
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'retry_sleep': 2,
            
            # Avoid problematic options
            'no_check_certificate': False,
        }
        
        # Add ffmpeg location if found
        if self.ffmpeg_location:
            base_opts['ffmpeg_location'] = self.ffmpeg_location
        
        # Download-specific options
        if for_download:
            base_opts.update({
                # Prefer audio-only formats that work well with Whisper
                'format': (
                    # Try audio-only first (best quality, less detection)
                    'bestaudio[ext=m4a][filesize<?25M]/'
                    'bestaudio[ext=webm][filesize<?25M]/'
                    'bestaudio[ext=mp4][filesize<?25M]/'
                    # Fallback to video with audio extraction
                    'best[height<=720][filesize<?50M]/best[filesize<?50M]'
                ),
                
                # Output template
                'outtmpl': '%(title).100s.%(ext)s',
                
                # Post-processing for audio extraction if needed
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                    'preferredquality': '128',
                    'nopostoverwrites': False,
                }] if not self._is_audio_only_format_available() else [],
                
                # Additional download options
                'writeinfojson': False,
                'writethumbnail': False,
                'writesubtitles': False,
                'writeautomaticsub': False,
                'noplaylist': True,
                
                # Throttling for downloads
                'ratelimit': 1000000,  # 1MB/s limit to appear less automated
            })
        
        return base_opts
    
    def _is_audio_only_format_available(self) -> bool:
        """Check if audio-only formats are likely available."""
        # This is a heuristic - in practice, most YouTube videos have audio-only streams
        return True
    
    def _retry_with_backoff(self, func, max_retries: int = 3, base_delay: float = 1.0):
        """Retry function with exponential backoff."""
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Attempt {attempt + 1} failed, retrying in {delay:.1f}s: {str(e)}")
                time.sleep(delay)
    
    def get_video_info(self, url: str) -> Tuple[bool, Dict]:
        """
        Get video information without downloading with enhanced anti-detection.
        
        Args:
            url: YouTube URL
            
        Returns:
            Tuple of (success, info_dict or error_dict)
        """
        try:
            # Validate URL first
            is_valid, result = validate_video_url(url)
            if not is_valid:
                return False, {"error": result}
            
            def _extract_info():
                ydl_opts = self._get_enhanced_ydl_opts(for_download=False)
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    return info
            
            # Use retry with backoff
            info = self._retry_with_backoff(_extract_info, max_retries=2)
            
            # Extract relevant metadata
            video_info = {
                "success": True,
                "video_id": info.get('id'),
                "title": info.get('title'),
                "description": info.get('description', '')[:500] + '...' if info.get('description') and len(info.get('description', '')) > 500 else info.get('description', ''),
                "duration": info.get('duration', 0),
                "duration_formatted": format_duration(info.get('duration', 0)),
                "view_count": info.get('view_count'),
                "upload_date": info.get('upload_date'),
                "uploader": info.get('uploader'),
                "uploader_id": info.get('uploader_id'),
                "channel_id": info.get('channel_id'),
                "thumbnail": info.get('thumbnail'),
                "webpage_url": info.get('webpage_url'),
                "language": info.get('language'),
                "subtitles_available": bool(info.get('subtitles')),
                "auto_captions_available": bool(info.get('automatic_captions')),
            }
            
            # Check duration limits
            max_duration = settings.max_video_duration_minutes * 60
            if video_info["duration"] > max_duration:
                return False, {
                    "error": f"Video is too long. Maximum duration is {settings.max_video_duration_minutes} minutes.",
                    "duration": video_info["duration"],
                    "max_duration": max_duration
                }
            
            return True, video_info
            
        except yt_dlp.DownloadError as e:
            error_msg = str(e)
            # Handle specific error cases
            if "HTTP Error 403" in error_msg or "Forbidden" in error_msg:
                return False, {
                    "error": "YouTube blocked access to this video (403 Forbidden). This may be due to region restrictions or YouTube's anti-bot measures.",
                    "error_type": "youtube_blocked",
                    "suggestion": "Try a different video or wait a few minutes and try again."
                }
            elif "Private video" in error_msg or "Video unavailable" in error_msg:
                return False, {
                    "error": "This video is private or unavailable. Please use a public YouTube video.",
                    "error_type": "video_unavailable"
                }
            else:
                return False, {"error": f"YouTube error: {error_msg}"}
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}
    
    def download_audio(self, url: str, job_id: str) -> Tuple[bool, Dict]:
        """
        Download audio from YouTube video with enhanced anti-detection.
        
        Args:
            url: YouTube URL
            job_id: Unique job identifier
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            # Get video info first
            success, info = self.get_video_info(url)
            if not success:
                return False, info
            
            # Prepare output directory and path
            output_dir = self.temp_dir / f"job_{job_id}"
            output_dir.mkdir(exist_ok=True)
            
            # Random delay to appear more human-like
            time.sleep(random.uniform(0.5, 2))
            
            def _download_audio():
                ydl_opts = self._get_enhanced_ydl_opts(for_download=True)
                
                # Set output template with job-specific directory
                ydl_opts['outtmpl'] = str(output_dir / 'audio.%(ext)s')
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                # Find the downloaded file
                possible_files = list(output_dir.glob('audio.*'))
                if not possible_files:
                    # Try alternative patterns
                    possible_files = list(output_dir.glob('*.m4a')) + list(output_dir.glob('*.webm')) + list(output_dir.glob('*.mp3'))
                
                return possible_files
            
            # Download with retry and backoff
            possible_files = self._retry_with_backoff(_download_audio, max_retries=3, base_delay=2)
            
            if not possible_files:
                return False, {"error": "Audio file was not created successfully"}
            
            # Use the first (and hopefully only) matching file
            actual_audio_path = str(possible_files[0])
            
            # Check if we got an .mhtml file (YouTube blocking)
            if actual_audio_path.endswith('.mhtml') or actual_audio_path.endswith('.html'):
                return False, {
                    "error": "YouTube blocked the download (received HTML instead of audio). This video may be restricted or YouTube is detecting automated access.",
                    "error_type": "youtube_blocked",
                    "suggestion": "Try a different video or wait before retrying."
                }
            
            # Verify the file is actually audio (check size and extension)
            file_size = os.path.getsize(actual_audio_path)
            if file_size < 1024:  # Less than 1KB is suspicious
                return False, {
                    "error": "Downloaded file is too small to be valid audio",
                    "error_type": "invalid_download"
                }
            
            # Check file extension
            valid_extensions = ['.m4a', '.webm', '.mp3', '.mp4', '.wav', '.ogg']
            if not any(actual_audio_path.lower().endswith(ext) for ext in valid_extensions):
                return False, {
                    "error": f"Downloaded file has invalid extension: {os.path.splitext(actual_audio_path)[1]}",
                    "error_type": "invalid_format"
                }
            
            print(f"✅ Audio downloaded successfully: {actual_audio_path} ({format_bytes(file_size)})")
            
            result = {
                "success": True,
                "audio_file_path": actual_audio_path,
                "file_size": file_size,
                "file_size_formatted": format_bytes(file_size),
                "video_info": info,
                "actual_format": os.path.splitext(actual_audio_path)[1]
            }
            
            return True, result
            
        except yt_dlp.DownloadError as e:
            error_msg = str(e)
            # Handle specific error cases
            if "HTTP Error 403" in error_msg or "Forbidden" in error_msg:
                return False, {
                    "error": "YouTube blocked the download (403 Forbidden). Enhanced anti-detection failed for this video.",
                    "error_type": "youtube_blocked",
                    "retry_suggestion": "Try using a different YouTube video or wait 5-10 minutes before retrying."
                }
            elif "Private video" in error_msg or "Video unavailable" in error_msg:
                return False, {
                    "error": "This video is private or unavailable. Please use a public YouTube video.",
                    "error_type": "video_unavailable"
                }
            elif "age-restricted" in error_msg.lower():
                return False, {
                    "error": "This video is age-restricted and cannot be processed.",
                    "error_type": "age_restricted"
                }
            elif "Sign in to confirm your age" in error_msg:
                return False, {
                    "error": "This video requires age verification. Please use a different video.",
                    "error_type": "age_verification_required"
                }
            else:
                return False, {"error": f"Download failed: {error_msg}"}
        except Exception as e:
            return False, {"error": f"Unexpected error during download: {str(e)}"}
    
    def cleanup_audio_file(self, job_id: str) -> bool:
        """
        Clean up downloaded audio file(s) and job directory.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cleaned up successfully
        """
        try:
            # Clean up job-specific directory
            job_dir = self.temp_dir / f"job_{job_id}"
            if job_dir.exists():
                shutil.rmtree(job_dir)
                print(f"Cleaned up job directory: {job_dir}")
            
            # Also clean up any legacy files (from old format)
            audio_file_base = get_temp_file_path(job_id, 'audio').replace('.audio', '')
            audio_files = glob.glob(f'{audio_file_base}.*')
            
            cleaned_count = len(audio_files)
            for audio_file in audio_files:
                if os.path.exists(audio_file):
                    os.remove(audio_file)
            
            if cleaned_count > 0:
                print(f"Cleaned up {cleaned_count} legacy audio files for job {job_id}")
            
            return True
        except Exception as e:
            print(f"Error cleaning up files for job {job_id}: {e}")
            return False
    
    def estimate_download_time(self, duration_seconds: int) -> int:
        """
        Estimate download time based on video duration.
        
        Args:
            duration_seconds: Video duration in seconds
            
        Returns:
            Estimated download time in seconds
        """
        # More conservative estimate with anti-detection delays
        base_time = max(15, duration_seconds * 0.2)  # Minimum 15 seconds, slower due to throttling
        return int(base_time)
    
    def process_with_whisper_primary(self, url: str, job_id: str) -> Tuple[bool, Dict]:
        """
        Process video with Whisper as PRIMARY method, YouTube API as fallback.
        
        Args:
            url: YouTube URL
            job_id: Unique job identifier
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            # Get video info first
            success, video_info = self.get_video_info(url)
            if not success:
                return False, video_info
            
            print(f"🎯 Processing with Whisper PRIMARY: {video_info.get('title', 'Unknown')}")
            
            # Try Whisper first (higher quality)
            print(f"🎙️ Step 1: Attempting Whisper transcription...")
            
            # Download audio
            download_success, download_result = self.download_audio(url, job_id)
            
            if download_success:
                # Transcribe with Whisper
                audio_path = download_result["audio_file_path"]
                whisper_success, whisper_result = transcription_service.transcribe_audio_with_whisper(audio_path)
                
                if whisper_success:
                    print(f"✅ Whisper transcription successful: {whisper_result['word_count']} words")
                    
                    result = {
                        "success": True,
                        "method": "whisper_primary",
                        "video_info": video_info,
                        "transcript_data": whisper_result,
                        "file_size": download_result["file_size"],
                        "file_size_formatted": download_result["file_size_formatted"],
                        "processing_time": "whisper_api"
                    }
                    
                    return True, result
                else:
                    print(f"⚠️ Whisper failed: {whisper_result.get('error', 'Unknown error')}")
            else:
                print(f"⚠️ Audio download failed: {download_result.get('error', 'Unknown error')}")
            
            # Fallback to YouTube Transcript API
            print(f"🔄 Step 2: Falling back to YouTube Transcript API...")
            
            # Extract YouTube video ID
            video_id = video_info.get("video_id")
            if not video_id:
                return False, {"error": "Could not extract video ID for transcript fallback"}
            
            # Get transcript using YouTube Transcript API
            transcript_success, transcript_data = transcription_service.get_youtube_transcript(video_id)
            
            if transcript_success:
                print(f"✅ YouTube transcript fallback successful: {transcript_data['word_count']} words")
                
                result = {
                    "success": True,
                    "method": "youtube_transcript_fallback",
                    "video_info": video_info,
                    "transcript_data": transcript_data,
                    "file_size": 0,
                    "file_size_formatted": "0 B",
                    "processing_time": "fallback",
                    "fallback_reason": download_result.get("error", "Audio download failed") if not download_success else whisper_result.get("error", "Whisper failed")
                }
                
                return True, result
            else:
                # Both methods failed
                return False, {
                    "error": f"Both Whisper and YouTube transcript methods failed. Whisper: {download_result.get('error', 'Audio download failed') if not download_success else whisper_result.get('error', 'Whisper failed')}. YouTube API: {transcript_data.get('error', 'Transcript unavailable')}",
                    "error_type": "all_methods_failed"
                }
                
        except Exception as e:
            return False, {"error": f"Processing failed: {str(e)}"}
    
    def process_youtube_transcript(self, url: str, job_id: str) -> Tuple[bool, Dict]:
        """
        Process YouTube video using transcript API (legacy method, now fallback).
        
        Args:
            url: YouTube URL
            job_id: Unique job identifier
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            # Get video info first
            success, video_info = self.get_video_info(url)
            if not success:
                return False, video_info
            
            # Extract YouTube video ID
            video_id = video_info.get("video_id")
            if not video_id:
                return False, {"error": "Could not extract video ID from YouTube URL"}
            
            print(f"🎯 Processing YouTube video: {video_id} using transcript API (fallback)")
            
            # Get transcript using YouTube Transcript API
            transcript_success, transcript_data = transcription_service.get_youtube_transcript(video_id)
            
            if not transcript_success:
                return False, transcript_data
            
            print(f"✅ Got YouTube transcript: {transcript_data['word_count']} words")
            
            result = {
                "success": True,
                "method": "youtube_transcript",
                "video_info": video_info,
                "transcript_data": transcript_data,
                "file_size": 0,  # No file downloaded
                "file_size_formatted": "0 B",
                "processing_time": "instant"
            }
            
            return True, result
            
        except Exception as e:
            return False, {"error": f"YouTube transcript processing failed: {str(e)}"}
    
    def determine_processing_method(self, url: str) -> str:
        """
        Determine the best processing method for a given URL.
        
        Args:
            url: Video URL
            
        Returns:
            Processing method: 'whisper_primary', 'download_audio'
        """
        try:
            # Validate and get platform info
            is_valid, result = validate_video_url(url)
            if not is_valid:
                return 'whisper_primary'  # Default to enhanced method
            
            platform = result.get('platform', 'unknown')
            
            if platform == 'youtube':
                # For YouTube, use YouTube API directly (audio download blocked by YouTube)
                return 'youtube_transcript'
            else:
                # For other platforms (Rumble, etc.), use audio download with Whisper
                return 'download_audio'
                
        except Exception:
            return 'whisper_primary'  # Safe fallback to enhanced method

    def process_whisper_first(self, url: str, job_id: str) -> Tuple[bool, Dict]:
        """
        NEW ENHANCED METHOD: Process with Whisper FIRST for superior quality.
        Falls back to YouTube API if audio download fails.
        
        Args:
            url: YouTube URL
            job_id: Unique job identifier
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            # Get video info first
            success, video_info = self.get_video_info(url)
            if not success:
                return False, video_info
            
            print(f"🚀 ENHANCED: Whisper-first processing for superior quality")
            
            # Try Whisper via audio download first
            audio_success, audio_result = self.download_audio(url, job_id)
            
            if audio_success:
                print(f"✅ Audio downloaded: {audio_result['file_size_formatted']}")
                
                # Transcribe with Whisper for higher quality
                audio_path = audio_result["audio_file_path"]
                whisper_success, whisper_result = transcription_service.transcribe_audio_with_whisper(audio_path)
                
                if whisper_success:
                    print(f"🎙️ HIGH-QUALITY Whisper transcription: {whisper_result['word_count']} words")
                    
                    # Clean up audio file
                    self.cleanup_audio_file(job_id)
                    
                    result = {
                        "success": True,
                        "method": "whisper_enhanced",
                        "video_info": video_info,
                        "transcript_data": whisper_result,
                        "file_size": audio_result['file_size'],
                        "file_size_formatted": audio_result['file_size_formatted'],
                        "processing_time": "whisper_enhanced"
                    }
                    
                    return True, result
                
                else:
                    print(f"⚠️ Whisper failed: {whisper_result.get('error')}")
                    self.cleanup_audio_file(job_id)
            
            else:
                print(f"⚠️ Audio download blocked: {audio_result.get('error')}")
            
            # Fallback to YouTube Transcript API
            print(f"🔄 Falling back to YouTube Transcript API")
            return self.process_youtube_transcript(url, job_id)
            
        except Exception as e:
            self.cleanup_audio_file(job_id)
            return False, {"error": f"Enhanced processing failed: {str(e)}"}


# Global service instance
youtube_service = YouTubeService()