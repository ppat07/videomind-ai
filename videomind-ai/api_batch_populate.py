#!/usr/bin/env python3
"""
Use the batch processing endpoint to add real YouTube content.
"""
import requests
import time

def populate_via_batch():
    """Use batch processing to add multiple YouTube videos."""
    
    base_url = "https://videomind-ai-tk84.onrender.com"
    
    print("🚀 Adding content via batch processing...")
    
    # Real OpenClaw/AI tutorial videos from YouTube
    video_batches = [
        {
            "youtube_urls": [
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Sample URLs
                "https://www.youtube.com/watch?v=jNQXAC9IVRw",
                "https://www.youtube.com/watch?v=J---aiyznGQ",
            ],
            "email": "test@example.com", 
            "tier": "basic"
        },
        {
            "youtube_urls": [
                "https://www.youtube.com/watch?v=fcOA0qHGmMU", 
                "https://www.youtube.com/watch?v=iik25wqIuFo",
                "https://www.youtube.com/watch?v=oHg5SJYRHA0",
            ],
            "email": "test@example.com",
            "tier": "basic" 
        },
        {
            "youtube_urls": [
                "https://www.youtube.com/watch?v=RBumgq5yVrA",
                "https://www.youtube.com/watch?v=lTRiuFIWV54", 
                "https://www.youtube.com/watch?v=k85mRPqvMbE",
            ],
            "email": "test@example.com",
            "tier": "basic"
        },
    ]
    
    total_queued = 0
    
    for i, batch in enumerate(video_batches, 1):
        try:
            print(f"📦 Batch {i}/{len(video_batches)}: Processing {len(batch['youtube_urls'])} videos...")
            
            response = requests.post(f"{base_url}/api/process/batch", json=batch)
            
            if response.status_code in [200, 201]:
                data = response.json()
                created_count = data.get('created_count', 0)
                skipped_count = data.get('skipped_count', 0)
                
                print(f"   ✅ Queued: {created_count}, Skipped: {skipped_count}")
                total_queued += created_count
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
            
            # Delay between batches
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n🎉 Batch processing complete!")
    print(f"🎬 Total videos queued: {total_queued}")
    
    if total_queued > 0:
        print(f"⏳ Videos are now processing in background...")
        print(f"📝 Check back in a few minutes to see processed entries in directory")
        
        # Wait a bit and check processing status
        print(f"🔄 Checking processing status in 30 seconds...")
        time.sleep(30)
        
        try:
            response = requests.get(f"{base_url}/api/jobs/health")
            if response.status_code == 200:
                data = response.json()
                counts = data.get('counts', {})
                print(f"📊 Job status: {counts}")
        except Exception as e:
            print(f"❌ Could not check job status: {e}")
    
    return total_queued > 0

if __name__ == "__main__":
    populate_via_batch()