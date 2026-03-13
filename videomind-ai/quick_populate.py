#!/usr/bin/env python3
"""
Quick script to populate production directory with our key OpenClaw videos
Uses the /api/process endpoint to organically add videos to the system
"""
import time
import requests
import json

# Key OpenClaw videos that should be in the directory
priority_videos = [
    {
        "url": "https://www.youtube.com/watch?v=YRhGtHfs1Lw",
        "title": "How I Use Clawdbot to Run My Business and Life 24/7",
        "email": "populate@videomind-ai.com"
    },
    {
        "url": "https://www.youtube.com/watch?v=bzWI3Dil9Ig", 
        "title": "My Multi-Agent Team with OpenClaw",
        "email": "populate@videomind-ai.com"
    },
    {
        "url": "https://www.youtube.com/watch?v=8kNv3rjQaVA",
        "title": "21 INSANE Use Cases For OpenClaw...",
        "email": "populate@videomind-ai.com"
    },
    {
        "url": "https://www.youtube.com/watch?v=3GrG-dOmrLU",
        "title": "I figured out the best way to run OpenClaw",
        "email": "populate@videomind-ai.com"
    },
    {
        "url": "https://www.youtube.com/watch?v=Q7r--i9lLck",
        "title": "OpenClaw Use Cases that are actually helpful...",
        "email": "populate@videomind-ai.com"
    },
    {
        "url": "https://www.youtube.com/watch?v=11sxky4vTcs",
        "title": "Please don't install Clawdbot",
        "email": "populate@videomind-ai.com"
    },
    {
        "url": "https://www.youtube.com/watch?v=4xDc00EF_eY",
        "title": "We Used OpenClaw for a Week. This is the Harsh Truth.",
        "email": "populate@videomind-ai.com"
    },
    {
        "url": "https://www.youtube.com/watch?v=ev4iiGXlnh0",
        "title": "DO NOT use a VPS for OpenClaw (major warning)",
        "email": "populate@videomind-ai.com"
    },
    {
        "url": "https://www.youtube.com/watch?v=41_TNGDDnfQ",
        "title": "6 OpenClaw use cases I promise will change your life",
        "email": "populate@videomind-ai.com"
    },
    {
        "url": "https://youtu.be/NZ1mKAWJPr4",
        "title": "50 days with OpenClaw: The hype, the reality & what actually broke",
        "email": "populate@videomind-ai.com"
    }
]

def populate_directory():
    """Add videos to production directory via processing endpoint"""
    base_url = "https://videomind-ai.com"
    added = 0
    
    print(f"Adding {len(priority_videos)} videos to production directory...")
    
    for video in priority_videos:
        try:
            # Submit video for processing (this adds it to directory)
            response = requests.post(f"{base_url}/api/process", 
                                   json={
                                       "youtube_url": video["url"],
                                       "email": video["email"], 
                                       "tier": "basic"
                                   },
                                   timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Added: {video['title'][:50]}...")
                print(f"   Job ID: {data.get('job_id', 'N/A')}")
                added += 1
            else:
                print(f"❌ Failed: {video['title'][:50]}...")
                print(f"   Error: {response.status_code} - {response.text[:100]}")
            
            # Rate limit - don't overwhelm the server
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Error with {video['title'][:50]}: {e}")
    
    print(f"\nCompleted: {added}/{len(priority_videos)} videos added to directory")
    
    # Check final directory count
    try:
        response = requests.get(f"{base_url}/api/directory?limit=100", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"🎯 Directory now has {data.get('total_count', 0)} total videos")
        else:
            print("Could not verify final directory count")
    except Exception as e:
        print(f"Error checking directory: {e}")

if __name__ == "__main__":
    populate_directory()