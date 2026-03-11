#!/usr/bin/env python3
"""
Quick fix to populate directory without database issues
"""
import requests
import json

def populate_directory():
    """Use the API to add entries directly."""
    
    # Check current directory count
    response = requests.get("http://localhost:8000/api/directory")
    data = response.json()
    current_count = data.get("total_count", 0)
    
    print(f"Current directory entries: {current_count}")
    
    if current_count > 0:
        print("Directory already populated!")
        return True
    
    # Manually add entries via the frontend processing API
    test_videos = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll for testing
    ]
    
    for video_url in test_videos:
        print(f"\nProcessing: {video_url}")
        
        # Submit for processing
        payload = {
            "youtube_url": video_url,
            "email": "test@videomind.ai",
            "tier": "basic"
        }
        
        response = requests.post(
            "http://localhost:8000/api/process",
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Submitted: {result.get('job_id')}")
            print(f"🎯 Status: {result.get('message')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
    
    return True

if __name__ == "__main__":
    print("🚀 Quick Directory Population")
    print("="*40)
    
    try:
        success = populate_directory()
        
        if success:
            print("\n✅ Directory population initiated!")
            print("🔍 Check the /directory page in a few seconds")
        else:
            print("\n❌ Directory population failed")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()