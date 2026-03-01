#!/usr/bin/env python3
"""
Debug what DATABASE_URL the production API is actually using.
"""
import requests

def debug_render_environment():
    """Check what database the production API thinks it's using."""
    
    print("🔍 Debugging production environment...")
    
    try:
        # Try to get some debug info from the API
        response = requests.get("https://videomind-ai-tk84.onrender.com/api/directory?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 API total_count: {data.get('total_count', 'missing')}")
            print(f"📝 Items returned: {len(data.get('items', []))}")
            
            # Look at the first item's database ID pattern
            if data.get('items'):
                first_item = data['items'][0]
                print(f"🆔 First item ID: {first_item.get('id', 'missing')}")
                print(f"📅 First item created_at: {first_item.get('created_at', 'missing')}")
        else:
            print(f"❌ API error: {response.status_code}")
            
        # Also try the health endpoint
        health_response = requests.get("https://videomind-ai-tk84.onrender.com/health")
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"🏥 Health status: {health_data.get('status', 'unknown')}")
            print(f"🌍 Environment: {health_data.get('environment', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_render_environment()