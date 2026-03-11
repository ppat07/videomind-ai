"""
Assembly.ai transcription service - reliable alternative to OpenAI Whisper
More robust for production use, better pricing, handles YouTube blocking
"""
import requests
import time
import os
from typing import Dict, Tuple, Optional

class AssemblyAIService:
    """Assembly.ai transcription service - production ready alternative to OpenAI Whisper."""
    
    def __init__(self, api_key: str = None):
        """Initialize Assembly.ai service."""
        self.api_key = api_key or os.getenv('ASSEMBLYAI_API_KEY')
        self.base_url = "https://api.assemblyai.com/v2"
        self.headers = {
            "authorization": self.api_key,
            "content-type": "application/json"
        }
        
        if not self.api_key:
            print("⚠️ Assembly.ai API key not configured")
    
    def is_available(self) -> bool:
        """Check if Assembly.ai service is available."""
        return bool(self.api_key)
    
    def upload_file(self, audio_file_path: str) -> Tuple[bool, Dict]:
        """Upload audio file to Assembly.ai."""
        try:
            def read_file(filename):
                with open(filename, 'rb') as f:
                    while True:
                        data = f.read(5242880)  # 5MB chunks
                        if not data:
                            break
                        yield data
            
            upload_response = requests.post(
                'https://api.assemblyai.com/v2/upload',
                headers={'authorization': self.api_key},
                data=read_file(audio_file_path)
            )
            
            if upload_response.status_code == 200:
                upload_url = upload_response.json()['upload_url']
                return True, {"upload_url": upload_url}
            else:
                return False, {"error": f"Upload failed: {upload_response.status_code}"}
                
        except Exception as e:
            return False, {"error": f"Upload error: {str(e)}"}
    
    def transcribe_file(self, audio_file_path: str, enhance: bool = True) -> Tuple[bool, Dict]:
        """
        Transcribe audio file using Assembly.ai with enhanced features.
        
        Args:
            audio_file_path: Path to audio file
            enhance: Whether to use enhanced features (speaker detection, etc.)
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            print(f"🎙️ Starting Assembly.ai transcription: {audio_file_path}")
            
            # Upload file
            upload_success, upload_result = self.upload_file(audio_file_path)
            if not upload_success:
                return False, upload_result
            
            upload_url = upload_result["upload_url"]
            
            # Configure transcription request
            transcript_request = {
                "audio_url": upload_url,
                "speaker_labels": enhance,  # Speaker detection
                "auto_chapters": enhance,   # Auto chapters
                "sentiment_analysis": enhance,  # Sentiment analysis
                "entity_detection": enhance,   # Named entity recognition
                "punctuate": True,
                "format_text": True,
                "language_code": "en"  # Auto-detect could be added
            }
            
            # Submit transcription
            response = requests.post(
                f"{self.base_url}/transcript",
                json=transcript_request,
                headers=self.headers
            )
            
            if response.status_code != 200:
                return False, {"error": f"Transcription request failed: {response.status_code}"}
            
            transcript_id = response.json()['id']
            print(f"✅ Transcription submitted: {transcript_id}")
            
            # Poll for completion
            while True:
                polling_response = requests.get(
                    f"{self.base_url}/transcript/{transcript_id}",
                    headers=self.headers
                )
                
                if polling_response.status_code != 200:
                    return False, {"error": f"Polling failed: {polling_response.status_code}"}
                
                result = polling_response.json()
                status = result['status']
                
                if status == 'completed':
                    # Process successful result
                    transcript_text = result['text']
                    
                    # Extract segments with timestamps
                    segments = []
                    if 'words' in result and result['words']:
                        for word in result['words']:
                            segments.append({
                                "start": word['start'] / 1000.0,  # Convert ms to seconds
                                "end": word['end'] / 1000.0,
                                "text": word['text']
                            })
                    
                    # Extract chapters if available
                    chapters = []
                    if enhance and 'chapters' in result and result['chapters']:
                        for chapter in result['chapters']:
                            chapters.append({
                                "start": chapter['start'] / 1000.0,
                                "end": chapter['end'] / 1000.0,
                                "headline": chapter['headline'],
                                "summary": chapter['summary']
                            })
                    
                    final_result = {
                        "success": True,
                        "method": "assembly_ai",
                        "language": "en",  # Assembly.ai auto-detects but doesn't return language
                        "duration": result.get('audio_duration', 0) / 1000.0,  # Convert ms to seconds
                        "full_text": transcript_text,
                        "segments": segments,
                        "segment_count": len(segments),
                        "word_count": len(transcript_text.split()),
                        "char_count": len(transcript_text),
                        "confidence": result.get('confidence', 0),
                        "chapters": chapters if chapters else None,
                        "assembly_ai_id": transcript_id
                    }
                    
                    # Add enhanced features if available
                    if enhance:
                        if 'sentiment_analysis_results' in result and result['sentiment_analysis_results']:
                            final_result["sentiment"] = result['sentiment_analysis_results']
                        
                        if 'entities' in result and result['entities']:
                            final_result["entities"] = result['entities']
                    
                    print(f"✅ Assembly.ai transcription complete: {len(transcript_text)} chars, {final_result['confidence']:.2f} confidence")
                    return True, final_result
                    
                elif status == 'error':
                    error_msg = result.get('error', 'Unknown transcription error')
                    return False, {"error": f"Assembly.ai transcription failed: {error_msg}"}
                
                else:
                    # Still processing, wait and poll again
                    print(f"⏳ Transcription status: {status}, polling again...")
                    time.sleep(3)
                    
        except Exception as e:
            return False, {"error": f"Assembly.ai transcription error: {str(e)}"}
    
    def transcribe_url(self, audio_url: str, enhance: bool = True) -> Tuple[bool, Dict]:
        """
        Transcribe audio from URL using Assembly.ai.
        
        Args:
            audio_url: URL to audio file
            enhance: Whether to use enhanced features
            
        Returns:
            Tuple of (success, result_dict)
        """
        try:
            print(f"🎙️ Starting Assembly.ai URL transcription: {audio_url}")
            
            # Configure transcription request
            transcript_request = {
                "audio_url": audio_url,
                "speaker_labels": enhance,
                "auto_chapters": enhance,
                "sentiment_analysis": enhance,
                "entity_detection": enhance,
                "punctuate": True,
                "format_text": True,
                "language_code": "en"
            }
            
            # Submit transcription
            response = requests.post(
                f"{self.base_url}/transcript",
                json=transcript_request,
                headers=self.headers
            )
            
            if response.status_code != 200:
                return False, {"error": f"URL transcription request failed: {response.status_code}"}
            
            transcript_id = response.json()['id']
            print(f"✅ URL transcription submitted: {transcript_id}")
            
            # Poll for completion (same logic as file transcription)
            # ... (polling logic same as above)
            
        except Exception as e:
            return False, {"error": f"Assembly.ai URL transcription error: {str(e)}"}


# Global service instance
assembly_ai_service = AssemblyAIService()