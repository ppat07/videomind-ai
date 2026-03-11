#!/usr/bin/env python3
"""
Test VideoMind AI with Claude enhancement fallback
"""
import sys
sys.path.append('src')

def test_claude_enhancement():
    """Test Claude-based enhancement system."""
    try:
        from services.transcription_service import transcription_service
        from services.youtube_service import youtube_service
        from utils.helpers import generate_job_id
        
        print("🚀 Testing VideoMind AI with Claude Enhancement")
        print("="*55)
        
        # Test video - Rick Roll 
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = "dQw4w9WgXcQ"
        job_id = generate_job_id()
        
        print(f"📺 Test URL: {test_url}")
        print(f"🔍 Job ID: {job_id}")
        
        # Test YouTube Transcript API (should work without API costs)
        print(f"\n🎯 Step 1: Testing YouTube Transcript API")
        yt_success, yt_result = transcription_service.get_youtube_transcript(video_id)
        
        if yt_success:
            transcript_text = yt_result['full_text']
            word_count = yt_result['word_count']
            
            print(f"✅ YouTube transcript: {word_count} words")
            print(f"📝 Sample: {transcript_text[:100]}...")
            
            # Test Claude-based AI enhancement
            print(f"\n🤖 Step 2: Testing Claude AI Enhancement")
            ai_success, ai_result = transcription_service.enhance_with_ai(transcript_text, "basic")
            
            if ai_success:
                print(f"✅ Claude enhancement successful!")
                print(f"📊 Summary: {ai_result['summary'][:100]}...")
                print(f"🔑 Key points: {len(ai_result['key_points'])}")
                print(f"❓ Q&A pairs: {len(ai_result['qa_pairs'])}")
                print(f"🏷️ Topics: {', '.join(ai_result['topics'])}")
                print(f"🧠 Model: {ai_result['processing_model']}")
                
                print(f"\n🎉 FULL PROCESSING PIPELINE SUCCESS!")
                print(f"   • YouTube Transcript: ✅ Working")
                print(f"   • Claude Enhancement: ✅ Working") 
                print(f"   • Zero OpenAI API costs")
                return True
            else:
                print(f"⚠️ Claude enhancement failed: {ai_result.get('error')}")
                print(f"📋 Fallback data available: {ai_result['processing_model']}")
                return False
        else:
            print(f"❌ YouTube transcript failed: {yt_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_claude_enhancement()
    
    print("="*55)
    if success:
        print("🎉 VIDEOMIND AI: READY FOR PRODUCTION!")
        print("🚀 Claude enhancement working - no OpenAI quota issues")
        print("💰 Zero additional API costs")
    else:
        print("⚠️ Need to debug Claude enhancement system")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Deploy to production server")
    print(f"   2. Test with multiple video types") 
    print(f"   3. Monitor processing success rates")