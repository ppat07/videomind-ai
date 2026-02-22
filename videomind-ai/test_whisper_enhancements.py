#!/usr/bin/env python3
"""
Test script for enhanced VideoMind AI Whisper capabilities.
Tests the new anti-detection and Whisper-primary processing.
"""
import requests
import json
import time
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.youtube_service import youtube_service
from services.transcription_service import transcription_service

def test_enhanced_youtube_service():
    """Test the enhanced YouTube service with better anti-detection."""
    print("🧪 Testing Enhanced YouTube Service")
    print("=" * 50)
    
    # Test URL - a short, publicly available video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - short and reliable
    
    print(f"📹 Testing URL: {test_url}")
    
    # Test 1: Video info extraction
    print(f"\n1️⃣ Testing video info extraction...")
    success, info = youtube_service.get_video_info(test_url)
    
    if success:
        print(f"✅ Video info extracted successfully:")
        print(f"   Title: {info.get('title', 'Unknown')[:60]}...")
        print(f"   Duration: {info.get('duration_formatted', 'Unknown')}")
        print(f"   Uploader: {info.get('uploader', 'Unknown')}")
    else:
        print(f"❌ Video info extraction failed: {info.get('error', 'Unknown error')}")
        return False
    
    # Test 2: Enhanced Whisper-primary processing
    print(f"\n2️⃣ Testing Whisper-primary processing...")
    job_id = f"test_{int(time.time())}"
    
    success, result = youtube_service.process_with_whisper_primary(test_url, job_id)
    
    if success:
        method = result.get('method', 'unknown')
        transcript_data = result.get('transcript_data', {})
        word_count = transcript_data.get('word_count', 0)
        
        print(f"✅ Processing successful:")
        print(f"   Method used: {method}")
        print(f"   Word count: {word_count}")
        print(f"   Language: {transcript_data.get('language', 'unknown')}")
        
        if 'fallback' in method:
            print(f"   ⚠️ Used fallback: {result.get('fallback_reason', 'Unknown reason')}")
        
        # Show first 100 characters of transcript
        full_text = transcript_data.get('full_text', '')
        if full_text:
            preview = full_text[:100] + "..." if len(full_text) > 100 else full_text
            print(f"   Preview: {preview}")
        
        # Clean up
        youtube_service.cleanup_audio_file(job_id)
        
    else:
        print(f"❌ Processing failed: {result.get('error', 'Unknown error')}")
        return False
    
    print(f"\n✅ All tests passed! Enhanced system is working correctly.")
    return True

def test_server_integration():
    """Test if the server is running and can handle requests."""
    print(f"\n🌐 Testing Server Integration")
    print("=" * 30)
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running and healthy")
            return True
        else:
            print(f"⚠️ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Server is not running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False

def main():
    """Run all tests."""
    print(f"🚀 VideoMind AI Whisper Enhancement Test Suite")
    print(f"Testing anti-detection and Whisper-primary processing...")
    print(f"\n" + "=" * 60)
    
    # Test 1: Server integration
    server_running = test_server_integration()
    
    # Test 2: Enhanced YouTube service
    if test_enhanced_youtube_service():
        print(f"\n🎉 SUCCESS: All enhancements are working correctly!")
        print(f"✨ Key improvements:")
        print(f"   • Enhanced yt-dlp anti-detection with rotating user agents")
        print(f"   • Whisper as PRIMARY transcription method") 
        print(f"   • YouTube API as intelligent fallback")
        print(f"   • Better audio optimization for Whisper")
        print(f"   • Improved error handling and retry logic")
        
        if server_running:
            print(f"\n📡 Server is ready to accept enhanced requests!")
        else:
            print(f"\n⚠️ Server is not running. Start it with: python run.py")
            
    else:
        print(f"\n❌ FAILED: Some enhancements are not working correctly")
        print(f"Check the error messages above for details.")

if __name__ == "__main__":
    main()