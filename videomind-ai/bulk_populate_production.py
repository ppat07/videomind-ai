#!/usr/bin/env python3
"""
Bulk populate production directory with quality YouTube content.
Uses the batch processing API to add real videos.
"""

import requests
import time
import random
from typing import List, Dict

# Production API base URL
BASE_URL = "https://videomind-ai-tk84.onrender.com"

# High-quality YouTube videos for AI/automation training
QUALITY_VIDEOS = [
    "https://www.youtube.com/watch?v=6p0mVo6T2zs",  # AI automation workflow
    "https://www.youtube.com/watch?v=F9Cu-trFp3s",  # OpenAI API tutorial
    "https://www.youtube.com/watch?v=kCc8FmEb1nY",  # Claude API guide
    "https://www.youtube.com/watch?v=M9jmdZBBn6M",  # AI agents tutorial
    "https://www.youtube.com/watch?v=jN4F-3mU6pw",  # Automation setup
    "https://www.youtube.com/watch?v=hYf6rEADOHg",  # AI workflow optimization
    "https://www.youtube.com/watch?v=2VKv6SLKP8g",  # Business automation
    "https://www.youtube.com/watch?v=vOjl8r1Y_WE",  # AI tool comparison
    "https://www.youtube.com/watch?v=QPQNDhOJ5s8",  # Advanced AI setup
    "https://www.youtube.com/watch?v=r4rIlUHZ2Ik",  # Workflow automation
    "https://www.youtube.com/watch?v=VkHWoTFGkjQ",  # AI productivity tips
    "https://www.youtube.com/watch?v=Tm2VhMFLIOQ",  # Claude 3 tutorial
    "https://www.youtube.com/watch?v=XJE4rHzKNJA",  # AI automation tools
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Test video (will likely fail)
    "https://www.youtube.com/watch?v=ScMzIvxBSi4",  # AI assistant setup
    "https://www.youtube.com/watch?v=oHg5SJYRHA0",  # Never gonna give you up (test)
    "https://www.youtube.com/watch?v=fBNz5xF-Kx4",  # AI workflow guide
    "https://www.youtube.com/watch?v=y_gEOoN6kDM",  # Automation patterns
    "https://www.youtube.com/watch?v=8OFpvTe8TO8",  # AI development
    "https://www.youtube.com/watch?v=H7cONtjIBrE",  # Business AI
]

def submit_batch_videos(videos: List[str], email: str = "paul.patlur@gmail.com") -> Dict:
    """Submit a batch of videos for processing."""
    try:
        url = f"{BASE_URL}/api/process/batch"
        payload = {
            "youtube_urls": videos,
            "email": email,
            "tier": "basic"
        }
        
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except requests.RequestException as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}

def check_directory_count() -> int:
    """Check current directory entry count."""
    try:
        url = f"{BASE_URL}/api/directory"
        response = requests.get(url, params={"limit": 1}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("total_count", 0)
        else:
            return 0
            
    except:
        return 0

def main():
    """Main execution function."""
    print("=" * 70)
    print("VideoMind AI Production Directory - Bulk Population")
    print("=" * 70)
    
    # Check current state
    initial_count = check_directory_count()
    print(f"\n📊 Current directory entries: {initial_count}")
    
    if initial_count >= 50:
        print("✅ Directory already has 50+ entries!")
        return
    
    # Process videos in batches
    batch_size = 5
    total_queued = 0
    
    print(f"\n🚀 Processing {len(QUALITY_VIDEOS)} videos in batches of {batch_size}...")
    
    for i in range(0, len(QUALITY_VIDEOS), batch_size):
        batch_num = (i // batch_size) + 1
        batch = QUALITY_VIDEOS[i:i + batch_size]
        
        print(f"\n📦 Batch {batch_num}: {len(batch)} videos")
        
        # Add delay between batches
        if batch_num > 1:
            delay = random.uniform(3, 8)
            print(f"   ⏱️  Waiting {delay:.1f}s between batches...")
            time.sleep(delay)
        
        # Submit batch
        result = submit_batch_videos(batch)
        
        if result["success"]:
            data = result["data"]
            created = data.get("created_count", 0)
            skipped = data.get("skipped_count", 0)
            
            print(f"   ✅ Queued: {created}, Skipped: {skipped}")
            
            if created > 0:
                total_queued += created
                print(f"   📈 Total queued so far: {total_queued}")
            
            # Show skip reasons for debugging
            if skipped > 0 and "skipped" in data:
                for skip in data["skipped"][:3]:  # Show first 3 skipped items
                    reason = skip.get("reason", "unknown")
                    print(f"      • Skipped: {reason}")
        else:
            print(f"   ❌ Batch failed: {result['error']}")
            break
        
        # Check if we've reached our target
        if total_queued >= 45:  # Buffer for processing
            print(f"\n✅ Queued enough videos ({total_queued}), stopping...")
            break
    
    print(f"\n🎉 Batch processing complete!")
    print(f"   Videos queued for processing: {total_queued}")
    print(f"   Processing will complete in background...")
    
    # Wait a moment, then check progress
    if total_queued > 0:
        print(f"\n⏳ Waiting 30 seconds for processing to start...")
        time.sleep(30)
        
        final_count = check_directory_count()
        print(f"📊 Directory entries after processing: {final_count}")
        
        if final_count > initial_count:
            print(f"✅ Added {final_count - initial_count} new entries!")
        else:
            print("⚠️  Processing in progress - check back in a few minutes")
    
    print("\n" + "=" * 70)
    print("Bulk population complete! 🚀")
    print("=" * 70)

if __name__ == "__main__":
    main()