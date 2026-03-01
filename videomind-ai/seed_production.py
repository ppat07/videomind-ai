#!/usr/bin/env python3
"""
Seed the production VideoMind AI directory via API call.
"""
import requests

def seed_production_directory():
    """Call the seed API endpoint to add starter entries."""
    url = "https://videomind-ai-tk84.onrender.com/api/directory/seed"
    
    try:
        print("🌱 Seeding production directory...")
        response = requests.post(url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Added {data.get('created', '?')} entries")
            return True
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    seed_production_directory()