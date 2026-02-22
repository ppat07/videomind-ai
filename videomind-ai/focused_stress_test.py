#!/usr/bin/env python3
"""
Focused stress test after fixing data issues.
"""
import requests
import time

BASE_URL = "http://localhost:8002"

def run_focused_tests():
    print("🔧 FOCUSED STRESS TEST - After Data Fix")
    print("=" * 50)
    
    tests = [
        ("Basic Load", "/api/directory"),
        ("Large Page", "/api/directory?limit=61"),
        ("All Videos", "/api/directory?content_type=video"),
        ("All Articles", "/api/directory?content_type=article"),
        ("High Signal", "/api/directory?min_signal=90"),
        ("Search Python", "/api/directory?q=Python"),
        ("Advanced Filter", "/api/directory?category=Web Development&difficulty=Advanced"),
    ]
    
    results = []
    
    for name, endpoint in tests:
        start = time.time()
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            end = time.time()
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {name}: {end-start:.3f}s - {data.get('total_count', 0)} items")
                results.append((name, True, end-start, data.get('total_count', 0)))
            else:
                print(f"❌ {name}: {response.status_code}")
                results.append((name, False, end-start, 0))
        except Exception as e:
            end = time.time()
            print(f"❌ {name}: {e}")
            results.append((name, False, end-start, 0))
    
    # Summary
    passed = sum(1 for r in results if r[1])
    avg_time = sum(r[2] for r in results) / len(results)
    total_items = max(r[3] for r in results)
    
    print(f"\n📊 SUMMARY:")
    print(f"   Tests Passed: {passed}/{len(results)}")
    print(f"   Average Response: {avg_time:.3f}s") 
    print(f"   Total Items in DB: {total_items}")
    print(f"   Performance: {'🚀 EXCELLENT' if avg_time < 0.1 else '⚠️ ACCEPTABLE' if avg_time < 0.5 else '❌ NEEDS WORK'}")
    
    return results

if __name__ == "__main__":
    run_focused_tests()