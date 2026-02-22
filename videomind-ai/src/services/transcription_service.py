"""
Real transcription and AI enhancement services.
Handles YouTube transcript extraction, Whisper API, and GPT enhancement.
"""
import openai
import os
import subprocess
import time
from youtube_transcript_api import YouTubeTranscriptApi
from typing import Dict, List, Optional, Tuple
import re

from config import settings
from utils.helpers import format_bytes
from utils.helpers import format_bytes


class TranscriptionService:
    """Service for handling transcription and AI enhancement."""
    
    def __init__(self):
        """Initialize transcription service."""
        # Initialize OpenAI client with new API
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
    
    def get_youtube_transcript(self, video_id: str) -> Tuple[bool, Dict]:
        """
        Get transcript from YouTube video using YouTube's caption data.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Tuple of (success, transcript_data or error_dict)
        """
        try:
            # Create API instance and fetch transcript
            api = YouTubeTranscriptApi()
            fetched_transcript = api.fetch(video_id)
            
            # Extract the transcript data using the correct method
            transcript_list = fetched_transcript.to_raw_data()
            
            if not transcript_list:
                return False, {"error": "No transcript available for this video"}
            
            # Create formatted transcript directly from the raw data
            formatted_transcript = ' '.join([entry.get('text', '').strip() for entry in transcript_list])
            
            # Also keep the timestamped version for more detailed processing
            timestamped_segments = []
            for entry in transcript_list:
                timestamped_segments.append({
                    "start": entry.get('start', 0),
                    "duration": entry.get('duration', 0),
                    "text": entry.get('text', '').strip()
                })
            
            # Calculate total duration from transcript
            total_duration = 0
            if timestamped_segments:
                last_segment = timestamped_segments[-1]
                total_duration = last_segment['start'] + last_segment.get('duration', 0)
            
            result = {
                "success": True,
                "method": "youtube_transcript",
                "language": "auto-detected",  # YouTube API doesn't provide language info
                "duration": int(total_duration),
                "full_text": formatted_transcript,
                "segments": timestamped_segments,
                "segment_count": len(timestamped_segments),
                "word_count": len(formatted_transcript.split()),
                "char_count": len(formatted_transcript)
            }
            
            return True, result
            
        except Exception as e:
            error_message = str(e)
            
            # Handle specific YouTube transcript errors
            if "No transcript" in error_message or "transcript" in error_message.lower():
                return False, {
                    "error": "No transcript available for this video. The video may not have captions enabled.",
                    "error_type": "no_transcript",
                    "suggestion": "Try a different video that has captions, or the video owner needs to enable captions."
                }
            elif "disabled" in error_message.lower():
                return False, {
                    "error": "Transcripts are disabled for this video.",
                    "error_type": "transcripts_disabled"
                }
            else:
                return False, {"error": f"Failed to get YouTube transcript: {error_message}"}
    
    def convert_audio_for_whisper(self, input_path: str, output_path: str = None) -> Tuple[bool, str]:
        """
        Convert audio file to Whisper-optimized format using ffmpeg.
        
        Args:
            input_path: Path to input audio file
            output_path: Optional output path, defaults to input_path with .m4a extension
            
        Returns:
            Tuple of (success, output_path or error_message)
        """
        try:
            # Generate output path if not provided (use .m4a for better quality)
            if output_path is None:
                base_path = os.path.splitext(input_path)[0]
                output_path = f"{base_path}_whisper.m4a"
            
            # Get input file info first
            probe_cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                input_path
            ]
            
            try:
                probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                if probe_result.returncode == 0:
                    import json
                    probe_data = json.loads(probe_result.stdout)
                    audio_stream = next((s for s in probe_data.get('streams', []) if s.get('codec_type') == 'audio'), None)
                    if audio_stream:
                        print(f"📊 Input audio: {audio_stream.get('codec_name')} at {audio_stream.get('sample_rate')}Hz")
            except:
                # Probe failed, continue anyway
                pass
            
            # Enhanced ffmpeg command optimized for Whisper
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-i', input_path,  # Input file
                
                # Audio processing optimized for speech recognition
                '-vn',              # No video
                '-acodec', 'aac',   # AAC codec (better than MP3 for speech)
                '-ar', '22050',     # 22.05kHz sample rate (good balance of quality/size for speech)
                '-ac', '1',         # Mono channel
                '-ab', '128k',      # 128kbps bitrate
                
                # Audio filters for better speech recognition
                '-af', 'highpass=f=80,lowpass=f=8000,volume=1.2',  # Remove low-freq noise, boost volume slightly
                
                # Format settings
                '-f', 'mp4',        # MP4 container for .m4a
                '-movflags', '+faststart',  # Optimize for streaming/quick start
                
                output_path
            ]
            
            print(f"🔄 Converting audio for Whisper optimization...")
            
            # Run ffmpeg with longer timeout for large files
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout for large files
            )
            
            if result.returncode == 0:
                # Check if output file was created and has reasonable size
                if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                    output_size = os.path.getsize(output_path)
                    input_size = os.path.getsize(input_path)
                    compression_ratio = output_size / input_size if input_size > 0 else 1
                    
                    print(f"✅ Audio optimized for Whisper: {output_path}")
                    print(f"📊 Size: {input_size:,} → {output_size:,} bytes ({compression_ratio:.2%} of original)")
                    return True, output_path
                else:
                    return False, "Converted file was not created or is too small"
            else:
                error_msg = result.stderr or "ffmpeg conversion failed"
                print(f"❌ ffmpeg error: {error_msg}")
                
                # Try fallback with simpler conversion
                print(f"🔄 Trying fallback conversion...")
                fallback_cmd = [
                    'ffmpeg', '-y', '-i', input_path,
                    '-ar', '16000', '-ac', '1', '-ab', '96k',
                    '-f', 'mp4', output_path
                ]
                
                fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True, timeout=120)
                if fallback_result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
                    print(f"✅ Fallback conversion successful")
                    return True, output_path
                
                return False, f"Audio conversion failed: {error_msg}"
                
        except subprocess.TimeoutExpired:
            return False, "Audio conversion timed out (file too large or corrupted)"
        except FileNotFoundError:
            return False, "ffmpeg/ffprobe not found - audio conversion requires FFmpeg"
        except Exception as e:
            return False, f"Audio conversion error: {str(e)}"
    
    def transcribe_audio_with_whisper(self, audio_file_path: str) -> Tuple[bool, Dict]:
        """
        ENHANCED: Transcribe audio file using OpenAI Whisper API with advanced processing.
        Automatically converts to compatible format and validates file quality.
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Tuple of (success, transcript_data or error_dict)
        """
        whisper_compatible_path = None
        try:
            # ENHANCED: Validate input file first
            if not os.path.exists(audio_file_path):
                return False, {"error": "Audio file does not exist"}
            
            file_size = os.path.getsize(audio_file_path)
            if file_size == 0:
                return False, {"error": "Audio file is empty"}
            
            if file_size > 25 * 1024 * 1024:  # 25MB limit for Whisper API
                return False, {"error": "Audio file too large (>25MB). Try a shorter video."}
            
            print(f"🎙️ ENHANCED Whisper processing: {format_bytes(file_size)}")
            
            # Check if the file is actually audio (not HTML/text)
            with open(audio_file_path, 'rb') as f:
                file_header = f.read(512)
                if b'<html' in file_header.lower() or b'<!doctype' in file_header.lower():
                    return False, {"error": "Downloaded file is HTML, not audio. YouTube blocked the download."}
            
            # Check if file format is already Whisper-compatible
            file_extension = os.path.splitext(audio_file_path)[1].lower()
            whisper_formats = ['.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm']
            
            if file_extension not in whisper_formats:
                print(f"🔄 Converting {file_extension} to MP3 for Whisper compatibility")
                
                # Convert to Whisper-compatible format
                convert_success, convert_result = self.convert_audio_for_whisper(audio_file_path)
                if not convert_success:
                    return False, {"error": f"Audio conversion failed: {convert_result}"}
                
                whisper_compatible_path = convert_result
            else:
                whisper_compatible_path = audio_file_path
                print(f"✅ Audio format {file_extension} is Whisper-compatible")
            
            # Open and transcribe the audio file with enhanced settings
            with open(whisper_compatible_path, 'rb') as audio_file:
                print(f"🎙️ Transcribing with Whisper API (enhanced settings)...")
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",  # Get timestamps and detailed info
                    language=None,  # Auto-detect language for better accuracy
                    prompt="This is a video transcript. Please transcribe accurately with proper punctuation.",
                    temperature=0.0  # Most deterministic output
                )
            
            # Extract the transcript data
            segments = []
            if hasattr(transcript, 'segments') and transcript.segments:
                for segment in transcript.segments:
                    segments.append({
                        "start": segment.get('start', 0),
                        "end": segment.get('end', 0),
                        "text": segment.get('text', '').strip()
                    })
            
            full_text = transcript.text if hasattr(transcript, 'text') else ""
            
            result = {
                "success": True,
                "method": "whisper_api",
                "language": transcript.language if hasattr(transcript, 'language') else "en",
                "duration": transcript.duration if hasattr(transcript, 'duration') else 0,
                "full_text": full_text,
                "segments": segments,
                "segment_count": len(segments),
                "word_count": len(full_text.split()),
                "char_count": len(full_text)
            }
            
            return True, result
            
        except Exception as e:
            return False, {"error": f"Whisper transcription failed: {str(e)}"}
        
        finally:
            # Clean up converted file if it was created
            if whisper_compatible_path and whisper_compatible_path != audio_file_path:
                try:
                    if os.path.exists(whisper_compatible_path):
                        os.remove(whisper_compatible_path)
                        print(f"🧹 Cleaned up converted file: {whisper_compatible_path}")
                except Exception as e:
                    print(f"⚠️ Could not clean up converted file: {e}")
    
    def enhance_with_ai(self, transcript_text: str, tier: str = "basic") -> Tuple[bool, Dict]:
        """
        Enhance transcript with AI-generated summaries, Q&As, etc.
        
        Args:
            transcript_text: Raw transcript text
            tier: Processing tier (basic, detailed, bulk)
            
        Returns:
            Tuple of (success, enhanced_data or error_dict)
        """
        try:
            # Determine enhancement level based on tier
            if tier == "basic":
                qa_count = 5
                key_points_count = 5
            elif tier == "detailed":
                qa_count = 10
                key_points_count = 8
            else:  # bulk
                qa_count = 5
                key_points_count = 5
            
            # Create enhancement prompt
            enhancement_prompt = f"""
Analyze the following transcript and provide structured output in JSON format:

TRANSCRIPT:
{transcript_text[:3000]}{"..." if len(transcript_text) > 3000 else ""}

Please provide:
1. A concise summary (2-3 sentences)
2. {key_points_count} key points or main topics
3. {qa_count} question-and-answer pairs for training
4. 3-5 relevant topic tags

Format as JSON with keys: summary, key_points, qa_pairs, topics
"""
            
            # Call GPT API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at analyzing video transcripts and creating structured training data for AI models. Always respond with valid JSON."},
                    {"role": "user", "content": enhancement_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Extract and parse the response
            ai_response = response.choices[0].message.content.strip()
            
            # Try to extract JSON from the response
            import json
            
            # Sometimes GPT includes markdown formatting, clean it
            if "```json" in ai_response:
                ai_response = ai_response.split("```json")[1].split("```")[0].strip()
            elif "```" in ai_response:
                ai_response = ai_response.split("```")[1].split("```")[0].strip()
            
            try:
                enhanced_data = json.loads(ai_response)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                enhanced_data = {
                    "summary": "AI analysis completed but structured data parsing failed.",
                    "key_points": ["Content analysis", "Transcript processing", "AI enhancement"],
                    "qa_pairs": [{"question": "What was discussed?", "answer": "The content covers various topics from the video transcript."}],
                    "topics": ["video", "content", "analysis"]
                }
            
            # Ensure all required fields are present
            result = {
                "success": True,
                "tier": tier,
                "summary": enhanced_data.get("summary", "Summary not available"),
                "key_points": enhanced_data.get("key_points", [])[:key_points_count],
                "qa_pairs": enhanced_data.get("qa_pairs", [])[:qa_count],
                "topics": enhanced_data.get("topics", [])[:5],
                "word_count": len(transcript_text.split()),
                "processing_model": "gpt-3.5-turbo"
            }
            
            return True, result
            
        except Exception as e:
            # Return basic fallback data if AI enhancement fails
            fallback_data = {
                "success": False,
                "error": f"AI enhancement failed: {str(e)}",
                "tier": tier,
                "summary": "AI enhancement temporarily unavailable. Raw transcript available.",
                "key_points": ["Transcript processed", "Content available", "AI enhancement pending"],
                "qa_pairs": [
                    {"question": "What content is available?", "answer": "The video transcript has been processed and is available for download."}
                ],
                "topics": ["video", "transcript", "processing"],
                "word_count": len(transcript_text.split()),
                "processing_model": "fallback"
            }
            
            return False, fallback_data


# Global service instance
transcription_service = TranscriptionService()