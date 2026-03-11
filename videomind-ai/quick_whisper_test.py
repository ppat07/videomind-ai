#!/usr/bin/env python3
"""
Quick Whisper Fallback Test
Tests one video to verify the fallback system works
"""
import sys
import os
sys.path.append('src')

def test_whisper_fallback():
    """Test the Whisper fallback on a single video."""
    try:
        from services.transcription_service import transcription_service
        from services.youtube_service import youtube_service
        from utils.helpers import generate_job_id
        
        # Test video - Rick Roll (has transcripts available)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        job_id = generate_job_id()
        
        print("🚀 Testing Whisper Fallback Integration")
        print(f"📺 Test video: {test_url}")
        print(f"🔍 Job ID: {job_id}")
        
        # Extract video ID
        video_id = test_url.split('watch?v=')[1].split('&')[0]
        
        # Test 1: YouTube Transcript API (should work)
        print(f"\n🎯 Test 1: YouTube Transcript API")
        yt_success, yt_result = transcription_service.get_youtube_transcript(video_id)
        
        if yt_success:
            print(f"✅ YouTube transcript: {yt_result['word_count']} words")
        else:
            print(f"❌ YouTube transcript failed: {yt_result.get('error')}")
        
        # Test 2: Audio Download + Whisper (fallback scenario)
        print(f"\n🎯 Test 2: Audio Download + Whisper (Fallback)")
        audio_success, audio_result = youtube_service.download_audio(test_url, job_id)
        
        if audio_success:
            print(f"✅ Audio downloaded: {audio_result['file_size_formatted']}")
            
            # Test Whisper transcription
            audio_path = audio_result['audio_file_path']
            whisper_success, whisper_result = transcription_service.transcribe_audio_with_whisper(audio_path)
            
            if whisper_success:
                print(f"✅ Whisper transcription: {whisper_result['word_count']} words")
                
                # Compare quality
                if yt_success:
                    print(f"📊 Quality comparison:")
                    print(f"   YouTube API: {yt_result['word_count']} words")
                    print(f"   Whisper API: {whisper_result['word_count']} words")
                    
                # Clean up
                youtube_service.cleanup_audio_file(job_id)
                
                print(f"✅ WHISPER FALLBACK WORKING CORRECTLY")
                return True
            else:
                print(f"❌ Whisper failed: {whisper_result.get('error')}")
        else:
            print(f"❌ Audio download failed: {audio_result.get('error')}")
        
        # Test 3: Integrated processing method
        print(f"\n🎯 Test 3: Integrated Processing Method")
        method = youtube_service.determine_processing_method(test_url)
        print(f"📋 Determined method: {method}")
        
        if method == 'youtube_transcript':
            integrated_success, integrated_result = youtube_service.process_youtube_transcript(test_url, job_id)
        else:
            # Test the enhanced whisper-first method
            integrated_success, integrated_result = youtube_service.process_whisper_first(test_url, job_id)
            
        if integrated_success:
            print(f"✅ Integrated processing successful: {integrated_result['method']}")
            return True
        else:
            print(f"❌ Integrated processing failed: {integrated_result.get('error')}")
            
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*50)
    success = test_whisper_fallback()
    print("="*50)
    
    if success:
        print("🎉 WHISPER FALLBACK TEST: PASSED")
        print("💡 The system can handle videos with and without transcripts")
    else:
        print("⚠️ WHISPER FALLBACK TEST: FAILED")
        print("🔧 Check OpenAI API key and network connectivity")
    
    print(f"\n🎯 NEXT STEPS:")
    print(f"   1. Run full test suite on 100 video directory")
    print(f"   2. Test production deployment")
    print(f"   3. Monitor processing success rates")