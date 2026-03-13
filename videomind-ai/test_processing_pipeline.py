#!/usr/bin/env python3
"""
COMPREHENSIVE PROCESSING PIPELINE TEST
Test all core VideoMind AI components to ensure they work end-to-end
"""
import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_youtube_data_extraction():
    """Test YouTube data extraction service."""
    print("\n🧪 TEST 1: YouTube Data Extraction")
    print("-" * 50)
    
    try:
        from services.youtube_data_service import YouTubeDataService
        
        service = YouTubeDataService()
        
        # Test with a short public video
        test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"  # Big Buck Bunny
        print(f"Testing URL: {test_url}")
        
        # Extract basic info
        video_info = await service.get_video_info(test_url)
        
        if video_info and video_info.get("title"):
            print(f"✅ Video title: {video_info.get('title')}")
            print(f"✅ Duration: {video_info.get('duration', 'Unknown')}")
            print(f"✅ Channel: {video_info.get('uploader', 'Unknown')}")
            return True
        else:
            print(f"❌ Failed to extract video info: {video_info}")
            return False
            
    except Exception as e:
        print(f"❌ YouTube data extraction failed: {str(e)}")
        return False

async def test_transcription_service():
    """Test transcription capabilities."""
    print("\n🧪 TEST 2: Transcription Service")
    print("-" * 50)
    
    try:
        from services.transcription_service import get_transcript_with_fallback
        
        # Test with a short video that likely has captions
        test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
        print(f"Testing transcription for: {test_url}")
        
        # Try to get transcript
        result = await get_transcript_with_fallback(test_url)
        
        if result and result.get('transcript'):
            transcript_text = result.get('transcript', '')
            print(f"✅ Transcript extracted successfully")
            print(f"✅ Length: {len(transcript_text)} characters")
            print(f"✅ Source: {result.get('source', 'Unknown')}")
            print(f"✅ Preview: {transcript_text[:200]}...")
            return True
        else:
            print(f"❌ Transcription failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Transcription service failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_ai_enhancement():
    """Test AI enhancement service."""
    print("\n🧪 TEST 3: AI Enhancement Service")
    print("-" * 50)
    
    try:
        from services.claude_enhancement_service import enhance_video_content
        
        # Test data
        test_transcript = """
        Hello and welcome to this tutorial about artificial intelligence. 
        Today we'll explore how machine learning works and why it's important for businesses.
        We'll cover neural networks, data processing, and practical applications.
        This is a basic introduction suitable for beginners.
        """
        
        test_metadata = {
            "title": "AI Tutorial for Beginners",
            "duration": 300,
            "uploader": "Tech Channel"
        }
        
        print("Testing AI enhancement with sample content...")
        
        # Test enhancement
        result = await enhance_video_content(
            transcript=test_transcript,
            video_metadata=test_metadata,
            tier="basic"
        )
        
        if result and result.get('summary'):
            print(f"✅ AI enhancement successful")
            print(f"✅ Generated summary: {len(result.get('summary', ''))} characters")
            print(f"✅ Q&A pairs: {len(result.get('qa_pairs', []))}")
            print(f"✅ Summary preview: {result.get('summary', '')[:150]}...")
            return True
        else:
            print(f"❌ AI enhancement failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ AI enhancement failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_full_pipeline():
    """Test the complete processing pipeline."""
    print("\n🧪 TEST 4: Full Pipeline Integration")
    print("-" * 50)
    
    try:
        # Import all needed services
        from services.youtube_data_service import YouTubeDataService
        from services.transcription_service import get_transcript_with_fallback
        from services.claude_enhancement_service import enhance_video_content
        
        test_url = "https://www.youtube.com/watch?v=aqz-KE-bpKQ"
        
        print("Step 1: Extract video metadata...")
        youtube_service = YouTubeDataService()
        video_info = await youtube_service.get_video_info(test_url)
        
        if not video_info or not video_info.get("title"):
            print("❌ Failed at step 1: Video metadata extraction")
            return False
        
        print(f"✅ Step 1 complete: {video_info.get('title')}")
        
        print("Step 2: Extract transcript...")
        transcript_result = await get_transcript_with_fallback(test_url)
        
        if not transcript_result or not transcript_result.get('transcript'):
            print("❌ Failed at step 2: Transcript extraction")
            return False
        
        transcript_text = transcript_result.get('transcript')
        print(f"✅ Step 2 complete: {len(transcript_text)} characters")
        
        print("Step 3: AI enhancement...")
        enhancement_result = await enhance_video_content(
            transcript=transcript_text,
            video_metadata=video_info,
            tier="basic"
        )
        
        if not enhancement_result or not enhancement_result.get('summary'):
            print("❌ Failed at step 3: AI enhancement")
            return False
        
        print(f"✅ Step 3 complete: Generated summary and {len(enhancement_result.get('qa_pairs', []))} Q&A pairs")
        
        # Create final result
        final_result = {
            "video_info": video_info,
            "transcript": transcript_result,
            "enhancement": enhancement_result,
            "processing_successful": True
        }
        
        print("\n🎉 FULL PIPELINE TEST: SUCCESS!")
        print(f"✅ Video: {video_info.get('title')}")
        print(f"✅ Transcript: {len(transcript_text)} chars from {transcript_result.get('source')}")
        print(f"✅ Summary: {len(enhancement_result.get('summary', ''))} chars")
        print(f"✅ Q&A pairs: {len(enhancement_result.get('qa_pairs', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run comprehensive testing suite."""
    print("🎯 VIDEOMIND AI COMPREHENSIVE TESTING")
    print("=" * 60)
    print("Testing all core components to verify functionality...")
    
    results = {
        "youtube_extraction": False,
        "transcription": False,
        "ai_enhancement": False,
        "full_pipeline": False
    }
    
    # Run individual tests
    results["youtube_extraction"] = await test_youtube_data_extraction()
    results["transcription"] = await test_transcription_service()
    results["ai_enhancement"] = await test_ai_enhancement()
    
    # Run full integration test if components work
    if all(results.values()):
        results["full_pipeline"] = await test_full_pipeline()
    
    # Final report
    print("\n" + "=" * 60)
    print("🎯 FINAL TEST RESULTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print(f"\nSUMMARY: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("🎉 ALL TESTS PASSED - VIDEOMIND AI CORE PIPELINE IS WORKING!")
        print("✅ Ready for end-to-end customer testing")
    else:
        print("🚨 SOME TESTS FAILED - REQUIRES INVESTIGATION")
        print("❌ Product not ready for customers")
    
    return total_passed == total_tests

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nCritical testing error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)