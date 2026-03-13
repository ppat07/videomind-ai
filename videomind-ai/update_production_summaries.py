#!/usr/bin/env python3
"""
Update production VideoMind AI directory summaries via API calls
Direct fix for the messy transcript content in production
"""
import requests
import json
import time

# Videos that need summary fixes (the problematic ones we saw)
VIDEOS_TO_FIX = [
    {
        "url": "https://www.youtube.com/watch?v=3AtDnEC4zak",
        "title": "Quick OpenClaw Tips & Tricks", 
        "clean_summary": [
            "Essential OpenClaw shortcuts and optimizations",
            "Time-saving automation techniques", 
            "Common workflow improvements",
            "Pro tips for efficient usage",
            "Quick wins for daily productivity"
        ]
    },
    {
        "url": "https://www.youtube.com/watch?v=QH2-TGUlwu4", 
        "title": "OpenClaw Skills Development Tutorial",
        "clean_summary": [
            "Building custom OpenClaw skills from scratch",
            "Skill architecture and best practices", 
            "Testing and debugging workflows",
            "Publishing skills to the community",
            "Advanced skill development techniques"
        ]
    },
    {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "title": "OpenClaw Advanced Workflows Demo", 
        "clean_summary": [
            "Complex multi-agent orchestration patterns",
            "Enterprise-grade automation examples",
            "Advanced integration techniques", 
            "Scalable workflow architecture",
            "Production deployment strategies"
        ]
    },
    {
        "url": "https://www.youtube.com/watch?v=i13XK-uUOLQ",
        "title": "Making $$$ with OpenClaw",
        "clean_summary": [
            "Monetization strategies using AI automation", 
            "Building profitable OpenClaw businesses",
            "Client service automation workflows",
            "Revenue-generating use cases",
            "Scaling automation for profit"
        ]
    }
]

def reprocess_videos():
    """Reprocess specific videos to get clean summaries"""
    print("🔧 Reprocessing problematic videos for clean summaries...")
    
    processed = 0
    
    for video in VIDEOS_TO_FIX:
        try:
            print(f"\n📹 Reprocessing: {video['title']}")
            
            # Submit for reprocessing 
            response = requests.post(
                "https://videomind-ai.com/api/process",
                json={
                    "youtube_url": video["url"],
                    "email": "cleanup@videomind-ai.com",
                    "tier": "basic"
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get('job_id')
                print(f"  ✅ Submitted for reprocessing (Job: {job_id})")
                processed += 1
            else:
                print(f"  ❌ Failed to reprocess: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Rate limiting
        time.sleep(2)
    
    print(f"\n📊 Reprocessing Summary:")
    print(f"   • {processed}/{len(VIDEOS_TO_FIX)} videos resubmitted")
    print(f"   • Processing time: ~5-10 minutes")
    print(f"   • Directory will show clean summaries once complete")
    
    return processed

def check_current_directory():
    """Check current state of problematic videos"""
    print("🔍 Checking current directory state...")
    
    try:
        response = requests.get("https://videomind-ai.com/api/directory?limit=100")
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            
            print(f"📊 Directory Status: {len(items)} videos loaded")
            
            # Check for problematic videos
            problematic = 0
            for item in items:
                summary = item.get('summary_5_bullets', '')
                if (len(summary) > 500 or '♪' in summary or 
                    'we don\'t talk anymore' in summary.lower() or
                    'never gonna give you up' in summary.lower()):
                    problematic += 1
                    print(f"  ⚠️  Needs fix: {item.get('title', '')[:50]}...")
            
            print(f"📈 {problematic} videos still need summary cleanup")
            return problematic == 0
            
    except Exception as e:
        print(f"❌ Error checking directory: {e}")
        
    return False

def main():
    print("🧹 VideoMind AI Directory Cleanup")
    print("=" * 40)
    
    # Check current state
    clean_already = check_current_directory()
    
    if clean_already:
        print("✅ Directory summaries are already clean!")
        return
    
    # Reprocess problematic videos
    processed = reprocess_videos()
    
    if processed > 0:
        print("\n⏰ Processing in progress...")
        print("💡 Check the directory in 5-10 minutes to see clean summaries")
    else:
        print("\n❌ No videos were reprocessed successfully")

if __name__ == "__main__":
    main()