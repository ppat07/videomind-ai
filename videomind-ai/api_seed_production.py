#!/usr/bin/env python3
"""
Populate production VideoMind AI directory via API calls.
"""
import requests
import time
import json

def populate_via_api():
    """Add multiple content entries via the API to populate the directory."""
    
    base_url = "https://videomind-ai-tk84.onrender.com"
    
    print("🌱 Populating production directory via API...")
    
    # Sample content entries to add (diverse, high-quality content)
    content_entries = [
        {
            "title": "Complete OpenClaw Setup Guide for Beginners",
            "video_url": "https://www.youtube.com/watch?v=setup-guide-123",
            "creator_name": "OpenClaw Tutorial",
            "category_primary": "Setup & Onboarding",
            "difficulty": "Beginner",
            "tools_mentioned": "OpenClaw; CLI; Authentication; Models",
            "summary_5_bullets": "• Install OpenClaw CLI\n• Configure authentication\n• Connect AI models\n• Run first workflow\n• Basic troubleshooting",
            "best_for": "New users who want step-by-step setup guidance",
            "signal_score": 85,
        },
        {
            "title": "Advanced Automation Workflows with OpenClaw",
            "video_url": "https://www.youtube.com/watch?v=automation-advanced-456",
            "creator_name": "Automation Expert",
            "category_primary": "Automation Workflows", 
            "difficulty": "Advanced",
            "tools_mentioned": "OpenClaw; Python; APIs; Webhooks",
            "summary_5_bullets": "• Complex workflow design\n• API integrations\n• Error handling\n• Performance optimization\n• Production deployment",
            "best_for": "Experienced users building production workflows",
            "signal_score": 92,
        },
        {
            "title": "Business Use Cases: Revenue Generation with AI",
            "video_url": "https://www.youtube.com/watch?v=business-revenue-789", 
            "creator_name": "Business AI Coach",
            "category_primary": "Business Use Cases",
            "difficulty": "Intermediate",
            "tools_mentioned": "OpenClaw; CRM; Email automation; Analytics",
            "summary_5_bullets": "• Lead generation automation\n• Customer outreach\n• Revenue tracking\n• ROI measurement\n• Scaling strategies",
            "best_for": "Business owners wanting to monetize AI automation",
            "signal_score": 89,
        },
        {
            "title": "Debugging Common OpenClaw Issues",
            "video_url": "https://www.youtube.com/watch?v=debugging-common-101",
            "creator_name": "OpenClaw Support",
            "category_primary": "Debugging & Fixes",
            "difficulty": "Intermediate", 
            "tools_mentioned": "OpenClaw; Logs; Debug mode; Error handling",
            "summary_5_bullets": "• Reading error logs\n• Common failure modes\n• Debug configuration\n• Performance issues\n• Recovery strategies",
            "best_for": "Users encountering workflow problems",
            "signal_score": 88,
        },
        {
            "title": "Custom Prompt Templates for Better Results",
            "video_url": "https://www.youtube.com/watch?v=prompts-templates-202",
            "creator_name": "Prompt Engineer",
            "category_primary": "Prompts & Templates",
            "difficulty": "Advanced",
            "tools_mentioned": "OpenClaw; Prompt engineering; Templates; AI models",
            "summary_5_bullets": "• Prompt design principles\n• Template creation\n• Variable substitution\n• Testing and iteration\n• Best practices",
            "best_for": "Advanced users optimizing AI interactions",
            "signal_score": 91,
        },
        {
            "title": "Integrating OpenClaw with Popular Tools",
            "video_url": "https://www.youtube.com/watch?v=integrations-tools-303", 
            "creator_name": "Integration Specialist",
            "category_primary": "Tooling & Integrations",
            "difficulty": "Intermediate",
            "tools_mentioned": "OpenClaw; Slack; Google Sheets; Zapier; APIs",
            "summary_5_bullets": "• Popular integrations overview\n• Setup procedures\n• Authentication handling\n• Data flow design\n• Monitoring and maintenance",
            "best_for": "Users connecting OpenClaw to existing tools",
            "signal_score": 87,
        },
    ]
    
    # Add each entry via API
    success_count = 0
    total_entries = len(content_entries)
    
    for i, entry in enumerate(content_entries, 1):
        try:
            print(f"📝 {i}/{total_entries}: Adding '{entry['title'][:40]}...'")
            
            # Make API call to add entry  
            response = requests.post(f"{base_url}/api/directory", json=entry)
            
            if response.status_code in [200, 201]:
                success_count += 1
                print(f"   ✅ Added successfully")
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
            
            # Small delay to be nice to the server
            time.sleep(0.5)
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n🎉 API seeding complete!")
    print(f"✅ Successfully added: {success_count}/{total_entries}")
    
    # Check final count
    try:
        response = requests.get(f"{base_url}/api/directory?limit=1")
        if response.status_code == 200:
            data = response.json()
            final_count = data.get('total_count', 0)
            print(f"📊 Directory now has: {final_count} total entries")
        else:
            print(f"❌ Could not check final count: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking count: {e}")
    
    return success_count > 0

if __name__ == "__main__":
    populate_via_api()