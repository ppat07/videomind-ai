#!/usr/bin/env python3
"""
API-based directory population script.
Uses the working /api/directory/seed endpoint to populate production database.
"""

import requests
import time
import random
from typing import List, Dict

# Production API base URL
BASE_URL = "https://videomind-ai-tk84.onrender.com"

def call_seed_api() -> Dict:
    """Call the seed API endpoint to add 3 starter entries."""
    try:
        url = f"{BASE_URL}/api/directory/seed"
        response = requests.post(url, timeout=30)
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except requests.RequestException as e:
        return {"success": False, "error": f"Request failed: {str(e)}"}

def populate_directory_multiple_calls(target_entries: int = 50) -> Dict:
    """
    Populate directory by making multiple API calls.
    Each call adds ~3 entries, so we need multiple calls for 50+ entries.
    """
    print(f"🚀 Starting API-based directory population (target: {target_entries} entries)")
    
    total_created = 0
    call_count = 0
    max_calls = target_entries // 3 + 5  # Extra calls to handle duplicates
    
    while total_created < target_entries and call_count < max_calls:
        call_count += 1
        
        print(f"📞 API call #{call_count}...")
        
        # Add random delay between calls to avoid rate limiting
        if call_count > 1:
            delay = random.uniform(2, 5)
            print(f"   Waiting {delay:.1f}s...")
            time.sleep(delay)
        
        # Call the seed API
        result = call_seed_api()
        
        if result["success"]:
            data = result["data"]
            created_this_call = data.get("created", 0)
            total_created += created_this_call
            
            print(f"   ✅ Added {created_this_call} entries (total: {total_created})")
            
            if created_this_call == 0:
                print(f"   ℹ️ No new entries added (likely duplicates)")
                # If we're not adding new entries, try a different approach
                break
        else:
            print(f"   ❌ API call failed: {result['error']}")
            break
    
    print(f"\n🎉 Population complete!")
    print(f"   Total API calls: {call_count}")
    print(f"   Entries added: {total_created}")
    
    return {
        "success": True,
        "calls_made": call_count,
        "entries_added": total_created,
        "target_reached": total_created >= target_entries
    }

def verify_directory_population() -> Dict:
    """Check the current directory entry count."""
    try:
        url = f"{BASE_URL}/api/directory"
        response = requests.get(url, params={"limit": 1}, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            total_count = data.get("total_count", 0)
            return {"success": True, "total_entries": total_count}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
            
    except requests.RequestException as e:
        return {"success": False, "error": str(e)}

def main():
    """Main execution function."""
    print("=" * 60)
    print("VideoMind AI Directory Population via API")
    print("=" * 60)
    
    # Check current state
    print("\n📊 Checking current directory state...")
    verification = verify_directory_population()
    
    if verification["success"]:
        current_count = verification["total_entries"]
        print(f"   Current entries: {current_count}")
        
        if current_count >= 50:
            print("   ✅ Directory already has 50+ entries - population not needed")
            return
        else:
            print(f"   📈 Need {50 - current_count} more entries to reach target")
    else:
        print(f"   ⚠️ Could not verify current state: {verification['error']}")
        current_count = 0
    
    # Populate directory
    print(f"\n🚀 Starting population process...")
    result = populate_directory_multiple_calls(target_entries=50)
    
    # Final verification
    print(f"\n📊 Final verification...")
    final_verification = verify_directory_population()
    
    if final_verification["success"]:
        final_count = final_verification["total_entries"]
        print(f"   Final count: {final_count} entries")
        
        if final_count >= 50:
            print("   🎉 SUCCESS! Directory has 50+ entries")
        else:
            print(f"   ⚠️ Still need {50 - final_count} more entries")
    else:
        print(f"   ❌ Could not verify final state: {final_verification['error']}")
    
    print("\n" + "=" * 60)
    print("Population process complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()