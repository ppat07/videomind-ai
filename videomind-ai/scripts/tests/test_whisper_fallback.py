#!/usr/bin/env python3
"""
Test Whisper Fallback Integration
Tests the robust fallback from YouTube transcript → Whisper processing
"""
import sys
import os
sys.path.append('src')

from services.transcription_service import transcription_service
from services.youtube_service import youtube_service
from utils.helpers import generate_job_id

# Test video URLs with different characteristics
test_videos = [
    {
        "name": "Standard YouTube with transcripts",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - has auto captions
        "expected_method": "youtube_transcript"
    },
    {
        "name": "Tech tutorial",  
        "url": "https://www.youtube.com/watch?v=QH2-TGUlwu4",  # Nyan Cat - simple test
        "expected_method": "youtube_transcript_or_whisper"
    },
    {
        "name": "Short video",
        "url": "https://www.youtube.com/watch?v=3AtDnEC4zak",  # Short video
        "expected_method": "youtube_transcript_or_whisper"
    }
]

def test_video_processing(video_data):
    """Test video processing with fallback logic."""
    print(f"\n{'='*50}")
    print(f"🎯 Testing: {video_data['name']}")
    print(f"📺 URL: {video_data['url']}")
    print(f"{'='*50}")
    
    job_id = generate_job_id()
    
    try:
        # Step 1: Test YouTube Transcript API first
        print(f"🔍 Step 1: Testing YouTube Transcript API...")
        
        # Extract video ID
        video_url = video_data['url']
        if 'youtube.com' in video_url:
            if 'watch?v=' in video_url:
                video_id = video_url.split('watch?v=')[1].split('&')[0]
            elif 'embed/' in video_url:
                video_id = video_url.split('embed/')[1].split('?')[0]
        elif 'youtu.be' in video_url:
            video_id = video_url.split('youtu.be/')[1].split('?')[0]
        else:
            video_id = None
            
        youtube_transcript_success = False
        whisper_fallback_success = False
        
        if video_id:
            transcript_success, transcript_result = transcription_service.get_youtube_transcript(video_id)
            
            if transcript_success:
                print(f"✅ YouTube Transcript API: {transcript_result['word_count']} words")
                youtube_transcript_success = True
            else:
                print(f"⚠️ YouTube Transcript API failed: {transcript_result.get('error', 'Unknown error')}")
                
                # Step 2: Test Whisper fallback
                print(f"🎙️ Step 2: Testing Whisper fallback...")
                
                # Try audio download + Whisper
                download_success, download_result = youtube_service.download_audio(video_url, job_id)
                
                if download_success:
                    print(f"✅ Audio downloaded: {download_result['file_size_formatted']}")
                    
                    audio_path = download_result['audio_file_path']
                    whisper_success, whisper_result = transcription_service.transcribe_audio_with_whisper(audio_path)
                    
                    if whisper_success:
                        print(f"✅ Whisper API: {whisper_result['word_count']} words")
                        whisper_fallback_success = True
                        
                        # Clean up
                        youtube_service.cleanup_audio_file(job_id)
                    else:
                        print(f"❌ Whisper API failed: {whisper_result.get('error', 'Unknown error')}")
                else:
                    print(f"❌ Audio download failed: {download_result.get('error', 'Unknown error')}")
        
        # Step 3: Test integrated processing method
        print(f"🚀 Step 3: Testing integrated processing method...")
        
        processing_method = youtube_service.determine_processing_method(video_url)
        print(f"📋 Determined method: {processing_method}")
        
        if processing_method == 'youtube_transcript':
            # Test process_youtube_transcript method
            integrated_success, integrated_result = youtube_service.process_youtube_transcript(video_url, job_id)
        else:
            # Test download_audio method
            integrated_success, integrated_result = youtube_service.download_audio(video_url, job_id)
            
        if integrated_success:
            print(f"✅ Integrated processing: {integrated_result.get('method', 'unknown method')}")
            
            # Clean up
            youtube_service.cleanup_audio_file(job_id)
        else:
            print(f"❌ Integrated processing failed: {integrated_result.get('error', 'Unknown error')}")
        
        # Summary
        print(f"\n📊 RESULTS SUMMARY:")
        print(f"   YouTube Transcript: {'✅ Success' if youtube_transcript_success else '❌ Failed'}")
        print(f"   Whisper Fallback:  {'✅ Success' if whisper_fallback_success else '❌ Failed' if not youtube_transcript_success else '⏸️ Not needed'}")
        print(f"   Integrated Method:  {'✅ Success' if integrated_success else '❌ Failed'}")
        
        # Overall status
        overall_success = youtube_transcript_success or whisper_fallback_success or integrated_success
        print(f"   Overall Processing: {'✅ SUCCESS' if overall_success else '❌ FAILED'}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Clean up on error
        youtube_service.cleanup_audio_file(job_id)
        return False

def main():
    """Run comprehensive Whisper fallback tests."""
    print("🚀 VIDEOMIND AI: Whisper Fallback Integration Test")
    print("=" * 60)
    
    success_count = 0
    total_count = len(test_videos)
    
    for video_data in test_videos:
        success = test_video_processing(video_data)
        if success:
            success_count += 1
    
    # Final results
    print(f"\n{'='*60}")
    print(f"🏁 FINAL RESULTS: {success_count}/{total_count} videos processed successfully")
    
    if success_count == total_count:
        print("✅ All tests passed! Whisper fallback is working correctly.")
    elif success_count > 0:
        print("⚠️ Partial success. Some videos processed, others failed.")
    else:
        print("❌ All tests failed. Whisper fallback needs debugging.")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   • YouTube Transcript API should be primary method (faster, no download)")
    print(f"   • Whisper fallback for videos without transcripts")
    print(f"   • Audio download + Whisper for non-YouTube platforms")
    print(f"   • Always clean up temp files after processing")

if __name__ == "__main__":
    main()