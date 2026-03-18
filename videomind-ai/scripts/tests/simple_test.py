#!/usr/bin/env python3
"""
Simple test to verify API connectivity
"""
import sys
import os
sys.path.append('src')

print("🔍 Testing basic API connectivity...")

try:
    # Test OpenAI API
    import openai
    from config import settings
    
    print(f"✅ OpenAI imported successfully")
    print(f"🔑 API key configured: {settings.openai_api_key[:20]}...")
    
    client = openai.OpenAI(api_key=settings.openai_api_key)
    print(f"✅ OpenAI client created")
    
    # Test simple completion
    print(f"🤖 Testing OpenAI connection...")
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'API working' in 2 words"}],
        max_tokens=10
    )
    print(f"✅ OpenAI API response: {response.choices[0].message.content}")
    
    # Test YouTube transcript API
    print(f"📺 Testing YouTube Transcript API...")
    from youtube_transcript_api import YouTubeTranscriptApi
    
    # Simple test - get transcript for Rick Roll
    video_id = "dQw4w9WgXcQ"
    transcript = YouTubeTranscriptApi.list_transcripts(video_id)
    print(f"✅ YouTube Transcript API working")
    
    print(f"🎉 ALL API TESTS PASSED - System ready for processing!")
    
except Exception as e:
    print(f"❌ API Test failed: {str(e)}")
    import traceback
    traceback.print_exc()