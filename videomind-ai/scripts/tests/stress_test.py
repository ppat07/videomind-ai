#!/usr/bin/env python3
"""
Comprehensive stress test for VideoMind AI directory with 148+ items.
Tests performance, pagination, filtering, and user experience.
"""
import requests
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://localhost:8002"

def measure_time(func):
    """Decorator to measure execution time."""
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        return result, end - start
    return wrapper

@measure_time
def test_basic_directory_load():
    """Test basic directory loading performance."""
    response = requests.get(f"{BASE_URL}/api/directory")
    return response.status_code == 200, response.json()

@measure_time
def test_pagination_performance():
    """Test pagination with different page sizes."""
    results = {}
    
    # Test different page sizes
    page_sizes = [10, 24, 50, 100]
    for size in page_sizes:
        response = requests.get(f"{BASE_URL}/api/directory?limit={size}")
        if response.status_code == 200:
            data = response.json()
            results[f"page_size_{size}"] = {
                "total_count": data.get("total_count", 0),
                "items_returned": len(data.get("items", [])),
                "has_more": data.get("has_more", False)
            }
    
    return True, results

@measure_time
def test_filtering_performance():
    """Test various filtering options."""
    filters = [
        "?category=Web Development",
        "?category=AI Development", 
        "?difficulty=Intermediate",
        "?difficulty=Advanced",
        "?min_signal=80",
        "?min_signal=90",
        "?content_type=video",
        "?content_type=article",
        "?q=API",
        "?q=JavaScript",
        "?sort_by=signal_desc",
        "?sort_by=signal_asc"
    ]
    
    results = {}
    for filter_param in filters:
        response = requests.get(f"{BASE_URL}/api/directory{filter_param}")
        if response.status_code == 200:
            data = response.json()
            results[filter_param] = {
                "count": data.get("total_count", 0),
                "items": len(data.get("items", []))
            }
        else:
            results[filter_param] = {"error": response.status_code}
    
    return True, results

@measure_time  
def test_concurrent_requests():
    """Test handling concurrent requests."""
    def make_request(endpoint):
        response = requests.get(f"{BASE_URL}{endpoint}")
        return response.status_code == 200

    endpoints = [
        "/api/directory",
        "/api/directory?limit=50",
        "/api/directory?category=Web Development", 
        "/api/directory?difficulty=Advanced",
        "/api/directory?min_signal=85",
        "/api/directory?sort_by=signal_desc",
        "/api/directory?content_type=video",
        "/api/directory?q=development"
    ]
    
    success_count = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(make_request, endpoint) for endpoint in endpoints]
        for future in as_completed(futures):
            if future.result():
                success_count += 1
    
    return success_count == len(endpoints), {"successful_requests": success_count, "total_requests": len(endpoints)}

@measure_time
def test_search_performance():
    """Test search functionality with various queries."""
    search_terms = [
        "JavaScript", "Python", "API", "database", "frontend", 
        "automation", "machine learning", "development", "tutorial", "guide"
    ]
    
    results = {}
    for term in search_terms:
        response = requests.get(f"{BASE_URL}/api/directory?q={term}")
        if response.status_code == 200:
            data = response.json()
            results[term] = data.get("total_count", 0)
        else:
            results[term] = 0
    
    return True, results

@measure_time
def test_large_page_loads():
    """Test loading large pages."""
    response = requests.get(f"{BASE_URL}/api/directory?limit=148")
    if response.status_code == 200:
        data = response.json()
        return True, {
            "total_items_requested": 148,
            "items_returned": len(data.get("items", [])),
            "total_count": data.get("total_count", 0),
            "response_size_mb": len(response.content) / (1024 * 1024)
        }
    return False, {"error": response.status_code}

def run_stress_test():
    """Run comprehensive stress test."""
    print("🚀 VIDEOMIND AI STRESS TEST - 148+ Content Items")
    print("=" * 60)
    
    # Test server connectivity
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ Server health check failed: {health_response.status_code}")
            return
        print("✅ Server is healthy and responsive")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        return
    
    tests = [
        ("📊 Basic Directory Load", test_basic_directory_load),
        ("📄 Pagination Performance", test_pagination_performance),
        ("🔍 Filtering Performance", test_filtering_performance),
        ("🔍 Search Performance", test_search_performance),
        ("⚡ Concurrent Requests", test_concurrent_requests),
        ("📈 Large Page Load", test_large_page_loads)
    ]
    
    results = {}
    total_time = 0
    
    for test_name, test_func in tests:
        print(f"\n{test_name}...")
        try:
            (success, data), exec_time = test_func()
            total_time += exec_time
            
            if success:
                print(f"  ✅ Passed in {exec_time:.3f}s")
                if isinstance(data, dict) and len(str(data)) < 200:
                    print(f"     {data}")
                elif isinstance(data, dict):
                    # Show key metrics for large responses
                    if "total_count" in str(data):
                        print(f"     Sample: {list(data.items())[:3]}")
            else:
                print(f"  ❌ Failed in {exec_time:.3f}s")
                print(f"     {data}")
                
            results[test_name] = {"success": success, "time": exec_time, "data": data}
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results[test_name] = {"success": False, "error": str(e)}
    
    # Performance Summary
    print(f"\n{'='*60}")
    print("📈 PERFORMANCE SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for r in results.values() if r.get("success", False))
    total_tests = len(results)
    
    print(f"Tests Passed: {passed}/{total_tests}")
    print(f"Total Test Time: {total_time:.2f}s")
    
    # Performance thresholds
    performance_issues = []
    for test_name, result in results.items():
        if result.get("time", 0) > 2.0:  # Slower than 2 seconds
            performance_issues.append(f"{test_name}: {result['time']:.2f}s")
    
    if performance_issues:
        print(f"\n⚠️  PERFORMANCE WARNINGS (>2s):")
        for issue in performance_issues:
            print(f"   • {issue}")
    else:
        print(f"\n🚀 ALL TESTS UNDER 2 SECONDS - EXCELLENT PERFORMANCE!")
    
    # Content analysis
    basic_load_result = results.get("📊 Basic Directory Load", {}).get("data")
    if basic_load_result and isinstance(basic_load_result, tuple):
        _, directory_data = basic_load_result
        if isinstance(directory_data, dict):
            total_items = directory_data.get("total_count", 0)
            print(f"\n📊 CONTENT STATS:")
            print(f"   • Total Items in Directory: {total_items}")
            print(f"   • Items per Default Page: {len(directory_data.get('items', []))}")
            print(f"   • Pagination Working: {'✅' if directory_data.get('has_more') else '❌'}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if total_time < 10:
        print("   ✅ Performance is excellent for production use")
    elif total_time < 20:
        print("   ⚠️  Performance is acceptable but monitor under load")
    else:
        print("   ❌ Performance needs optimization before heavy traffic")
    
    print("   • Consider adding database indexing for popular filters")
    print("   • Monitor response times with real user traffic")
    print("   • Consider caching for static content")
    
    return results

if __name__ == "__main__":
    results = run_stress_test()
    
    print(f"\n🏁 STRESS TEST COMPLETE")
    print("=" * 60)
    
    # Save results for analysis
    with open("stress_test_results.json", "w") as f:
        # Convert results to JSON-serializable format
        json_results = {}
        for k, v in results.items():
            json_results[k] = {
                "success": v.get("success", False),
                "time": v.get("time", 0),
                "error": v.get("error"),
                # Skip complex data objects for JSON
                "has_data": bool(v.get("data"))
            }
        json.dump(json_results, f, indent=2)
    
    print("📊 Results saved to stress_test_results.json")
    print(f"🌐 Test VideoMind AI at: {BASE_URL}/directory")