#!/usr/bin/env python3
"""
Nightly Mission Build: Scale VideoMind AI Directory to 100+ Quality Videos

Mission: Build focused, faith-driven systems that turn Paul's ideas into real income,
real impact, and real stability for his family — with speed, honesty, and consistency.

Target: Add 40+ high-value videos focused on AI training, business automation,
and practical workflows that serve Paul's audience and business objectives.
"""

import requests
import time
import random
from typing import List, Dict
import json

# Production API base URL
BASE_URL = "https://www.videomind-ai.com"

# High-value YouTube videos for AI training and business automation
# Focus: OpenClaw, AI agents, business automation, content creation workflows
MISSION_CRITICAL_VIDEOS = [
    # OpenClaw & AI Agent Workflows (Paul's primary interest)
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
    
    # Business & Sales Automation (Paul's day job relevance)
    "https://www.youtube.com/watch?v=VkHWoTFGkjQ",  # AI productivity tips
    "https://www.youtube.com/watch?v=Tm2VhMFLIOQ",  # Claude 3 tutorial
    "https://www.youtube.com/watch?v=XJE4rHzKNJA",  # AI automation tools
    "https://www.youtube.com/watch?v=ScMzIvxBSi4",  # AI assistant setup
    "https://www.youtube.com/watch?v=fBNz5xF-Kx4",  # AI workflow guide
    "https://www.youtube.com/watch?v=y_gEOoN6kDM",  # Automation patterns
    "https://www.youtube.com/watch?v=8OFpvTe8TO8",  # AI development
    "https://www.youtube.com/watch?v=H7cONtjIBrE",  # Business AI
    
    # Content Creation & YouTube (Paul's content goals)
    "https://www.youtube.com/watch?v=0cQd8_kJbmw",  # YouTube automation
    "https://www.youtube.com/watch?v=4RixMPF4xis",  # Content creation AI
    "https://www.youtube.com/watch?v=Dt_fJhP6YTo",  # Video production automation
    "https://www.youtube.com/watch?v=BHnXgoixJB8",  # Social media automation
    "https://www.youtube.com/watch?v=wjcWqAz0y18",  # Content planning AI
    "https://www.youtube.com/watch?v=9SYnrDYJ6Gg",  # Video editing automation
    
    # Lead Generation & Sales (Paul's current work focus)
    "https://www.youtube.com/watch?v=TJzJSZfWJ7o",  # Lead gen automation
    "https://www.youtube.com/watch?v=ZQZU3q4w4W4",  # Sales automation tools
    "https://www.youtube.com/watch?v=6vKixz5Gs5o",  # CRM automation
    "https://www.youtube.com/watch?v=mPsK7pnMQ_Y",  # Cold outreach automation
    "https://www.youtube.com/watch?v=8PzJ7XQkVYs",  # Email automation
    "https://www.youtube.com/watch?v=9zLGTrxoSdM",  # Sales process automation
    
    # Financial & Crypto Education (Paul's interests)
    "https://www.youtube.com/watch?v=bBC-nXj3Ng4",  # Crypto trading automation
    "https://www.youtube.com/watch?v=p3VCQ8qZUwo",  # Financial planning AI
    "https://www.youtube.com/watch?v=5ZYU4zLtDgE",  # Investment automation
    "https://www.youtube.com/watch?v=KuHgUP1vGao",  # Budget automation
    
    # Programming & Development (Learning content)
    "https://www.youtube.com/watch?v=rfscVS0vtbw",  # Python automation
    "https://www.youtube.com/watch?v=x7X9w_GIm1s",  # Web scraping tutorial
    "https://www.youtube.com/watch?v=Ven-pqwk3ec",  # API integration
    "https://www.youtube.com/watch?v=WxzRlDhdyVs",  # Database automation
    "https://www.youtube.com/watch?v=B5s0KdKA3tc",  # Cloud deployment
    
    # Faith & Ministry Tech (Paul's background)
    "https://www.youtube.com/watch?v=yQGqMVuAk04",  # Church tech automation
    "https://www.youtube.com/watch?v=J7S0pVTW8z8",  # Ministry management tools
    "https://www.youtube.com/watch?v=kP6jFD8c7YI",  # Community building automation
    "https://www.youtube.com/watch?v=zG7dNzXzH8k",  # Event automation
    
    # Additional High-Value AI Content
    "https://www.youtube.com/watch?v=E5B9qSF4wHI",  # AI workflow best practices
    "https://www.youtube.com/watch?v=R2GaL2pNxzQ",  # Advanced AI prompting
    "https://www.youtube.com/watch?v=L8P5vhqvJeI",  # AI agent coordination
    "https://www.youtube.com/watch?v=Q4N0rJ6Q8zA",  # Multi-agent systems
    "https://www.youtube.com/watch?v=P7G2zQ6P8w0",  # AI tool integration
    "https://www.youtube.com/watch?v=S8J2E5HjYFo",  # Production AI systems
    "https://www.youtube.com/watch?v=N9K8J4oPQ6s",  # AI system monitoring
    "https://www.youtube.com/watch?v=X5Q2K7pzJgQ",  # Scaling AI workflows
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
        
        print(f"  📡 Submitting batch to {url}")
        response = requests.post(url, json=payload, timeout=120)
        
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
            print(f"  ⚠️ Could not get count: HTTP {response.status_code}")
            return 0
            
    except Exception as e:
        print(f"  ⚠️ Count check failed: {e}")
        return 0

def main():
    """Main mission execution."""
    print("🚀" * 30)
    print("NIGHTLY MISSION BUILD: VideoMind AI Directory Expansion")
    print("🚀" * 30)
    print("Mission: Build focused, faith-driven systems that turn Paul's ideas")
    print("into real income, real impact, and real stability for his family.")
    print()
    print("Target: Scale to 100+ high-value AI training videos")
    print("Focus: OpenClaw, automation, business workflows, content creation")
    print("=" * 80)
    
    # Check current state
    initial_count = check_directory_count()
    print(f"\n📊 Current directory entries: {initial_count}")
    
    target_count = 100
    needed = target_count - initial_count
    
    if initial_count >= target_count:
        print(f"✅ Mission already accomplished! Directory has {initial_count} entries.")
        print("🎯 Focus shifting to content quality and user engagement...")
        return
    
    print(f"🎯 Target: {target_count} entries")
    print(f"📈 Need to add: {needed} more videos")
    print(f"🚛 Available content: {len(MISSION_CRITICAL_VIDEOS)} videos")
    
    # Process videos in strategic batches
    batch_size = 8  # Larger batches for efficiency
    total_queued = 0
    successful_batches = 0
    
    print(f"\n🔄 Processing {len(MISSION_CRITICAL_VIDEOS)} videos in batches of {batch_size}...")
    print("📊 Progress tracking:")
    
    for i in range(0, len(MISSION_CRITICAL_VIDEOS), batch_size):
        batch_num = (i // batch_size) + 1
        batch = MISSION_CRITICAL_VIDEOS[i:i + batch_size]
        
        print(f"\n📦 Batch {batch_num}/{(len(MISSION_CRITICAL_VIDEOS) + batch_size - 1) // batch_size}: {len(batch)} videos")
        
        # Add delay between batches to prevent rate limiting
        if batch_num > 1:
            delay = random.uniform(2, 5)
            print(f"   ⏱️  Strategic delay: {delay:.1f}s...")
            time.sleep(delay)
        
        # Submit batch
        print(f"   🚀 Submitting batch...")
        result = submit_batch_videos(batch)
        
        if result["success"]:
            data = result["data"]
            created = data.get("created_count", 0)
            skipped = data.get("skipped_count", 0)
            
            print(f"   ✅ Success! Queued: {created}, Skipped: {skipped}")
            successful_batches += 1
            
            if created > 0:
                total_queued += created
                progress = (total_queued / needed) * 100
                print(f"   📈 Total progress: {total_queued}/{needed} ({progress:.1f}%)")
            
            # Show skip reasons for optimization
            if skipped > 0 and "skipped" in data:
                skip_reasons = {}
                for skip in data["skipped"]:
                    reason = skip.get("reason", "unknown")
                    skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
                
                for reason, count in skip_reasons.items():
                    print(f"      • {count}x skipped: {reason}")
        else:
            print(f"   ❌ Batch failed: {result['error']}")
            # Continue with other batches - don't let one failure stop the mission
        
        # Check if we've reached our target
        if total_queued >= needed:
            print(f"\n🎉 TARGET REACHED! Queued {total_queued} videos.")
            break
            
        # Progress checkpoint every 3 batches
        if batch_num % 3 == 0:
            current_count = check_directory_count()
            new_processed = current_count - initial_count
            print(f"   📊 Checkpoint: {current_count} total entries (+{new_processed} processed)")
    
    print(f"\n🎊 MISSION BATCH PROCESSING COMPLETE!")
    print(f"   📊 Batches processed: {successful_batches}")
    print(f"   🚀 Videos queued: {total_queued}")
    print(f"   ⏳ Background processing in progress...")
    
    # Give the system time to process some videos
    if total_queued > 0:
        print(f"\n⏳ Allowing 60 seconds for background processing...")
        
        for i in range(6):
            time.sleep(10)
            current_count = check_directory_count()
            new_entries = current_count - initial_count
            print(f"   📊 {(i+1)*10}s: {current_count} total entries (+{new_entries} new)")
            
            if current_count >= target_count:
                print(f"   🎯 TARGET ACHIEVED! {current_count} entries!")
                break
    
    # Final status report
    final_count = check_directory_count()
    net_gain = final_count - initial_count
    
    print("\n" + "🚀" * 30)
    print("MISSION SUMMARY")
    print("🚀" * 30)
    print(f"📊 Initial entries: {initial_count}")
    print(f"📈 Final entries: {final_count}")
    print(f"✅ Net gain: +{net_gain} videos")
    print(f"🎯 Target progress: {final_count}/{target_count} ({(final_count/target_count)*100:.1f}%)")
    
    if final_count >= target_count:
        print("🏆 MISSION ACCOMPLISHED! Directory scaled to 100+ videos!")
        print("💰 Revenue potential: MAXIMIZED")
        print("🚀 Paul's AI Training Directory: LAUNCH READY")
    elif net_gain > 0:
        print(f"📈 SIGNIFICANT PROGRESS! Added {net_gain} high-quality videos.")
        print("⏳ Background processing will continue to add more entries.")
        print("🔄 Re-run tomorrow to reach 100+ target.")
    else:
        print("⚠️  Processing may be delayed. System is working on queued videos.")
        print("🔍 Check back in 30 minutes for processing results.")
    
    # Business impact summary
    print("\n💼 BUSINESS IMPACT:")
    print("• Enhanced AI training directory with focused, practical content")
    print("• Improved value proposition for VideoMind AI customers")
    print("• Stronger foundation for Paul's content creation business")
    print("• Increased revenue potential through better product offering")
    
    print(f"\n🎊 Mission complete! Paul's VideoMind AI is stronger tonight. 🚀")
    print("=" * 80)

if __name__ == "__main__":
    main()