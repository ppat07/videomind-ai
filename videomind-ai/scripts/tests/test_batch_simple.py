#!/usr/bin/env python3
"""
Simple test of batch processing API.
"""

import requests

BASE_URL = "https://videomind-ai-tk84.onrender.com"

def test_single_batch():
    """Test with a single batch of 3 videos."""
    print("🧪 Testing batch API with 3 videos...")
    
    videos = [
        "https://www.youtube.com/watch?v=ScMzIvxBSi4",  # Should work
        "https://www.youtube.com/watch?v=fBNz5xF-Kx4",  # Should work
        "https://www.youtube.com/watch?v=invalid123",    # Should fail validation
    ]
    
    payload = {
        "youtube_urls": videos,
        "email": "paul.patlur@gmail.com",
        "tier": "basic"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/process/batch", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_single_batch()