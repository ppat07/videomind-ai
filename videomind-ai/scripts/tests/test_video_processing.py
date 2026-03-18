#!/usr/bin/env python3
"""
Test the complete video processing flow to see if videos get added to directory.
"""
import requests
import time
import json

BASE_URL = "http://localhost:8003"
TEST_VIDEO_URL = "https://youtu.be/NZ1mKAWJPr4"

def submit_video_for_processing():
    """Submit the test video for processing."""
    print(f"🎬 Submitting video for processing...")
    print(f"   URL: {TEST_VIDEO_URL}")
    
    data = {
        "youtube_url": TEST_VIDEO_URL,
        "email": "test@example.com",
        "tier": "basic"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/process", json=data)
        print(f"   Response: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Video submitted successfully!")
            print(f"   Job ID: {result.get('job_id')}")
            print(f"   Message: {result.get('message')}")
            return result.get('job_id')
        else:
            print(f"❌ Failed to submit: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error submitting video: {e}")
        return None

def check_directory_before():
    """Check current directory count."""
    try:
        response = requests.get(f"{BASE_URL}/api/directory?limit=5")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_count', 0)
            print(f"📊 Directory before processing: {total} items")
            return total
        return 0
    except Exception as e:
        print(f"❌ Error checking directory: {e}")
        return 0

def monitor_processing(job_id, max_wait_minutes=5):
    """Monitor the processing status."""
    if not job_id:
        return False
        
    print(f"\n⏳ Monitoring job {job_id} (max {max_wait_minutes} min)...")
    
    start_time = time.time()
    max_wait = max_wait_minutes * 60
    
    while (time.time() - start_time) < max_wait:
        try:
            # Check job status (if we had a job status endpoint)
            # For now, we'll check if it appears in directory
            response = requests.get(f"{BASE_URL}/api/directory?q=NZ1mKAWJPr4")
            
            if response.status_code == 200:
                data = response.json()
                if data.get('total_count', 0) > 0:
                    print(f"🎉 Video appeared in directory!")
                    return True
            
            print(f"   ⏱️ Still processing... ({int(time.time() - start_time)}s)")
            time.sleep(10)  # Check every 10 seconds
            
        except Exception as e:
            print(f"   ❌ Error monitoring: {e}")
            time.sleep(10)
    
    print(f"⏰ Timeout after {max_wait_minutes} minutes")
    return False

def check_directory_after():
    """Check directory count after processing."""
    try:
        response = requests.get(f"{BASE_URL}/api/directory?limit=5")
        if response.status_code == 200:
            data = response.json()
            total = data.get('total_count', 0)
            print(f"📊 Directory after processing: {total} items")
            return total
        return 0
    except Exception as e:
        print(f"❌ Error checking directory: {e}")
        return 0

def search_for_video():
    """Search for the specific video in the directory."""
    try:
        # Search by video ID
        response = requests.get(f"{BASE_URL}/api/directory?q=NZ1mKAWJPr4")
        if response.status_code == 200:
            data = response.json()
            if data.get('total_count', 0) > 0:
                video = data['items'][0]
                print(f"🎬 FOUND VIDEO IN DIRECTORY:")
                print(f"   Title: {video.get('title')}")
                print(f"   Creator: {video.get('creator_name')}")
                print(f"   Category: {video.get('category_primary')}")
                print(f"   Signal Score: {video.get('signal_score')}")
                print(f"   Video URL: {video.get('video_url')}")
                return True
            else:
                print(f"❌ Video not found in directory")
                return False
        return False
    except Exception as e:
        print(f"❌ Error searching for video: {e}")
        return False

def run_complete_test():
    """Run the complete integration test."""
    print("🚀 TESTING VIDEOMIND AI: Video Processing → Directory Integration")
    print("=" * 70)
    
    # Test server connectivity
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding: {response.status_code}")
            return
        print("✅ Server is healthy and ready")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Step 1: Check initial directory state
    initial_count = check_directory_before()
    
    # Step 2: Submit video for processing
    job_id = submit_video_for_processing()
    if not job_id:
        return
    
    # Step 3: Monitor processing (this is the key test)
    print(f"\n📝 NOTE: This will test if background processing automatically")
    print(f"         adds completed videos to the searchable directory.")
    
    success = monitor_processing(job_id, max_wait_minutes=3)  # Shorter wait for demo
    
    # Step 4: Check final state
    final_count = check_directory_after()
    found_video = search_for_video()
    
    # Results
    print(f"\n📊 TEST RESULTS:")
    print(f"=" * 40)
    print(f"Initial directory count: {initial_count}")
    print(f"Final directory count: {final_count}")
    print(f"Directory count increase: {final_count - initial_count}")
    print(f"Video found in directory: {'✅ YES' if found_video else '❌ NO'}")
    print(f"Auto-integration working: {'✅ YES' if found_video else '❌ NO'}")
    
    if found_video:
        print(f"\n🎉 SUCCESS: Videos DO get automatically added to directory!")
        print(f"   The complete flow works: Submit → Process → Directory Entry")
    else:
        print(f"\n⚠️ RESULT: Video processing may take longer than our test window")
        print(f"   Or there might be an issue with auto-directory integration")
        print(f"   Check the directory manually in a few minutes")

if __name__ == "__main__":
    run_complete_test()