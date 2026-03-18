#!/usr/bin/env python3
"""
Test all three fixes:
1. Datetime formatting fix
2. Enhanced categorization for non-AI content  
3. Smart deduplication (VideoJob + DirectoryEntry)
"""
import requests
import time
import sys
from pathlib import Path

# Add src to path for direct testing
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

BASE_URL = "http://localhost:8004"

def test_datetime_fix():
    """Test that newly processed videos can be retrieved via API without datetime errors."""
    print("🕐 Testing datetime formatting fix...")
    
    try:
        # Try to get our previously processed video that had datetime issues
        response = requests.get(f"{BASE_URL}/api/directory?q=OpenClaw")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API call successful: {data.get('total_count', 0)} results")
            if data.get('total_count', 0) > 0:
                print(f"   ✅ Found video: {data['items'][0].get('title', 'Unknown')}")
                return True
        else:
            print(f"   ❌ API call failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_categorization_logic():
    """Test categorization logic for different types of content."""
    print("\n📂 Testing enhanced categorization...")
    
    try:
        # Import categorization function directly
        from utils.directory_mapper import infer_category
        
        test_cases = [
            ("AI Automation Setup Tutorial", "", [], "Setup & Onboarding"),
            ("Funny Cat Videos Compilation", "Entertainment content", [], "Entertainment"),  
            ("Breaking: New iPhone Released", "Latest tech news", [], "News & Updates"),
            ("My Honest Review of Tesla Model 3", "Review and opinions", [], "Reviews & Opinions"),
            ("Python Programming Tutorial", "Learn programming basics", [], "Educational"),
            ("OpenClaw Integration Guide", "Workflow automation", ["api", "integration"], "Tooling & Integrations"),
            ("Random Video About Nothing", "Just some content", [], "General Content"),
        ]
        
        passed = 0
        for title, summary, topics, expected in test_cases:
            result = infer_category(title, summary, topics)
            status = "✅" if result == expected else "❌"
            print(f"   {status} '{title}' → {result} (expected: {expected})")
            if result == expected:
                passed += 1
        
        print(f"   📊 Categorization tests: {passed}/{len(test_cases)} passed")
        return passed == len(test_cases)
        
    except Exception as e:
        print(f"   ❌ Error testing categorization: {e}")
        return False

def test_deduplication():
    """Test that deduplication works for both VideoJob and DirectoryEntry checks."""
    print("\n🔄 Testing smart deduplication...")
    
    # Test with the video we already processed
    test_video_url = "https://youtu.be/NZ1mKAWJPr4"
    
    try:
        # Try to submit the same video again - should be caught by deduplication
        data = {
            "youtube_url": test_video_url,
            "email": "test@example.com", 
            "tier": "basic"
        }
        
        response = requests.post(f"{BASE_URL}/api/process", json=data)
        
        if response.status_code == 200:
            result = response.json()
            if "already" in result.get("message", "").lower():
                print(f"   ✅ Deduplication working: {result.get('message')}")
                print(f"   ✅ Status: {result.get('status')}")
                return True
            else:
                print(f"   ⚠️ Unexpected response: {result}")
                return False
        else:
            print(f"   ❌ API call failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing deduplication: {e}")
        return False

def run_comprehensive_test():
    """Run all tests to verify fixes."""
    print("🧪 COMPREHENSIVE TEST: All Three Fixes")
    print("=" * 60)
    
    # Check server health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding: {response.status_code}")
            return
        print("✅ Server is healthy")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    # Run all tests
    tests = [
        ("Datetime Fix", test_datetime_fix),
        ("Enhanced Categorization", test_categorization_logic),
        ("Smart Deduplication", test_deduplication)
    ]
    
    results = {}
    for name, test_func in tests:
        results[name] = test_func()
    
    # Summary
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n📊 FINAL RESULTS:")
    print("=" * 40)
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL FIXES WORKING PERFECTLY!")
        print("   • Datetime formatting: No more API crashes")
        print("   • Categorization: Handles all content types intelligently") 
        print("   • Deduplication: Prevents duplicate processing efficiently")
    else:
        print(f"\n⚠️ Some issues remain - check failed tests above")

if __name__ == "__main__":
    run_comprehensive_test()