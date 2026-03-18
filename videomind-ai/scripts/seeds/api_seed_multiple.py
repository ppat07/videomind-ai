#!/usr/bin/env python3
"""
Use the working seed endpoint multiple times to populate directory.
"""
import requests
import time

def seed_multiple_times():
    """Call the seed endpoint multiple times to populate directory."""
    
    base_url = "https://videomind-ai-tk84.onrender.com"
    
    print("🌱 Populating directory using seed endpoint...")
    
    success_count = 0
    total_calls = 10  # Make 10 seed calls
    
    for i in range(1, total_calls + 1):
        try:
            print(f"🌱 {i}/{total_calls}: Calling seed endpoint...")
            
            # Call the seed API that we know works
            response = requests.post(f"{base_url}/api/directory/seed")
            
            if response.status_code in [200, 201]:
                data = response.json()
                created = data.get('created', 0)
                print(f"   ✅ Created {created} entries")
                success_count += created
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text[:100]}")
            
            # Delay between calls
            time.sleep(1)
            
        except Exception as e:
            print(f"   ❌ Exception: {e}")
    
    print(f"\n🎉 Seeding complete!")
    print(f"✅ Total entries created: {success_count}")
    
    # Check final count
    try:
        response = requests.get(f"{base_url}/api/directory?limit=1")
        if response.status_code == 200:
            data = response.json()
            final_count = data.get('total_count', 0)
            print(f"📊 Directory now has: {final_count} total entries")
            
            if final_count > 10:
                print(f"🎯 SUCCESS! Directory now populated with content!")
            else:
                print(f"⚠️  Still low count - may need different approach")
        else:
            print(f"❌ Could not check final count: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking count: {e}")
    
    return success_count > 0

if __name__ == "__main__":
    seed_multiple_times()