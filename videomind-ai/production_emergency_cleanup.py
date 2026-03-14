#!/usr/bin/env python3
"""
PRODUCTION EMERGENCY CLEANUP
Clean the production database directly via API calls
"""
import requests
import time

# Known FAKE URLs that MUST be removed from production
FAKE_URLS_TO_REMOVE = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Roll - CRITICAL
    "https://www.youtube.com/watch?v=3AtDnEC4zak",  # Random fake
    "https://www.youtube.com/watch?v=QH2-TGUlwu4",  # Random fake
    "https://training.videomind-ai.com/",           # Non-existent training URLs
    "https://www.youtube.com/watch?v=demo",          # All demo URLs
]

# VERIFIED real videos to keep
REAL_VIDEOS_TO_KEEP = [
    "https://www.youtube.com/watch?v=Qkqe-uRhQJE",  # Alex Finn setup
    "https://www.youtube.com/watch?v=i13XK-uUOLQ",  # Greg Isenberg money
    "https://www.youtube.com/watch?v=Aj6hoC9JaLI",  # Alex Finn immediate
]

def get_all_production_videos():
    """Get all videos from production"""
    try:
        response = requests.get("https://videomind-ai.com/api/directory?limit=100", timeout=30)
        if response.status_code == 200:
            data = response.json()
            return data.get('items', [])
        else:
            print(f"❌ Failed to fetch directory: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error fetching directory: {e}")
        return []

def identify_fake_videos(videos):
    """Identify which videos are fake and need removal"""
    fake_videos = []
    real_videos = []
    
    for video in videos:
        source_url = video.get('source_url', '')
        title = video.get('title', '')
        
        # Check if this is a known fake URL
        is_fake = False
        for fake_pattern in FAKE_URLS_TO_REMOVE:
            if fake_pattern in source_url:
                is_fake = True
                break
        
        # Check for obviously fake content
        if ('demo' in source_url.lower() and 
            ('demo1_' in source_url or 'demo2_' in source_url)):
            is_fake = True
        
        # Check if it's a non-existent training URL
        if 'training.videomind-ai.com' in source_url:
            is_fake = True
        
        if is_fake:
            fake_videos.append({
                'id': video.get('id'),
                'title': title,
                'source_url': source_url
            })
        else:
            real_videos.append({
                'id': video.get('id'), 
                'title': title,
                'source_url': source_url
            })
    
    return fake_videos, real_videos

def analyze_production_integrity():
    """Analyze production directory integrity"""
    print("🔍 PRODUCTION DIRECTORY INTEGRITY ANALYSIS")
    print("=" * 55)
    
    videos = get_all_production_videos()
    if not videos:
        print("❌ Could not fetch production directory")
        return
    
    fake_videos, real_videos = identify_fake_videos(videos)
    
    print(f"📊 Analysis Results:")
    print(f"   • Total videos: {len(videos)}")
    print(f"   • FAKE videos: {len(fake_videos)}")
    print(f"   • Real videos: {len(real_videos)}")
    
    print(f"\n🚨 FAKE VIDEOS FOUND:")
    for fake in fake_videos[:10]:  # Show first 10
        print(f"   • {fake['title'][:60]}...")
        print(f"     URL: {fake['source_url']}")
    
    if len(fake_videos) > 10:
        print(f"   ... and {len(fake_videos) - 10} more fake videos")
    
    print(f"\n✅ REAL VIDEOS:")
    for real in real_videos[:5]:  # Show first 5
        print(f"   • {real['title'][:60]}...")
    
    if len(fake_videos) > 0:
        print(f"\n🚨 CRITICAL: Production contains {len(fake_videos)} fake videos!")
        print(f"   This includes the RICK ROLL video described as OpenClaw tutorial!")
        print(f"   Customer trust will be destroyed if they see this!")
        
        return True  # Needs emergency cleanup
    else:
        print(f"\n✅ Production directory is clean!")
        return False

def recommend_action():
    """Recommend immediate action"""
    print(f"\n🎯 EMERGENCY ACTION REQUIRED:")
    print(f"   1. Contact Render.com to reset PostgreSQL database")
    print(f"   2. Or create database deletion endpoint")
    print(f"   3. Or take directory offline until cleaned")
    print(f"\n🔥 THIS IS A CUSTOMER TRUST CRISIS!")
    print(f"   Rick Astley music video labeled as 'OpenClaw Advanced Workflows'")
    print(f"   Must be fixed immediately before customers see it!")

if __name__ == "__main__":
    needs_cleanup = analyze_production_integrity()
    
    if needs_cleanup:
        recommend_action()
    
    print(f"\n💡 NUCLEAR OPTION: Take directory completely offline")
    print(f"   Better to have NO directory than fake Rick Roll content!")