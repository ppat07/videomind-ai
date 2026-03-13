#!/usr/bin/env python3
"""
Fix production directory cards using the new update-summaries endpoint
"""
import requests
import json

# Clean summaries for problematic videos
SUMMARY_FIXES = [
    {
        "source_url": "https://www.youtube.com/watch?v=3AtDnEC4zak",
        "summary_5_bullets": "• Essential OpenClaw shortcuts and optimizations\n• Time-saving automation techniques\n• Common workflow improvements\n• Pro tips for efficient usage\n• Quick wins for daily productivity",
        "best_for": "Users wanting to optimize their OpenClaw workflows"
    },
    {
        "source_url": "https://www.youtube.com/watch?v=QH2-TGUlwu4", 
        "summary_5_bullets": "• Building custom OpenClaw skills from scratch\n• Skill architecture and best practices\n• Testing and debugging workflows\n• Publishing skills to the community\n• Advanced skill development techniques",
        "best_for": "Developers creating custom OpenClaw skills"
    },
    {
        "source_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "summary_5_bullets": "• Complex multi-agent orchestration patterns\n• Enterprise-grade automation examples\n• Advanced integration techniques\n• Scalable workflow architecture\n• Production deployment strategies", 
        "best_for": "Advanced users building enterprise workflows"
    },
    {
        "source_url": "https://www.youtube.com/watch?v=i13XK-uUOLQ",
        "summary_5_bullets": "• Monetization strategies using AI automation\n• Building profitable OpenClaw businesses\n• Client service automation workflows\n• Revenue-generating use cases\n• Scaling automation for profit",
        "best_for": "Entrepreneurs monetizing AI automation"
    }
]

def fix_directory_cards():
    """Update production directory with clean summaries"""
    print("🧹 Fixing VideoMind AI directory cards...")
    
    try:
        response = requests.post(
            "https://videomind-ai.com/api/directory/update-summaries",
            json={"updates": SUMMARY_FIXES},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            updated = result.get("updated", 0)
            not_found = result.get("not_found", 0)
            
            print(f"✅ Summary update successful!")
            print(f"   • Updated: {updated} entries")
            print(f"   • Not found: {not_found} entries")
            
            if updated > 0:
                print("\n🎯 Directory cards should now be clean and uniform!")
                print("🔄 Refresh the directory page to see the changes")
                return True
            else:
                print("⚠️  No entries were updated")
                return False
                
        else:
            print(f"❌ Update failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error updating summaries: {e}")
        return False

if __name__ == "__main__":
    fix_directory_cards()