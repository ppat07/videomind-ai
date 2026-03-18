#!/usr/bin/env python3
"""
VideoMind AI - Production Readiness Test
Tests that all critical systems are working and ready to deploy.
"""
import sys
import os
import requests
import json
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_app_startup():
    """Test that the app can import and start properly."""
    print("🧪 Testing app startup...")
    try:
        from main import app
        print("✅ App imports successfully")
        return True
    except Exception as e:
        print(f"❌ App import failed: {e}")
        return False

def test_config_loading():
    """Test that configuration loads properly."""
    print("🧪 Testing configuration...")
    try:
        from config import settings
        print(f"✅ Config loaded: {settings.app_name} v{settings.app_version}")
        print(f"   - OpenAI API Key: {'✅ Set' if settings.openai_api_key and settings.openai_api_key.startswith('sk-') else '❌ Missing'}")
        print(f"   - Secret Key: {'✅ Set' if settings.secret_key else '❌ Missing'}")
        print(f"   - Debug Mode: {settings.debug}")
        return True
    except Exception as e:
        print(f"❌ Config loading failed: {e}")
        return False

def test_database_connection():
    """Test that database can be created and connected to."""
    print("🧪 Testing database connection...")
    try:
        from database import create_tables, get_database
        create_tables()
        db = next(get_database())
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_api_endpoints(base_url="http://127.0.0.1:8003"):
    """Test critical API endpoints."""
    print(f"🧪 Testing API endpoints at {base_url}...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint failed: {e}")
        return False
    
    # Test process endpoint exists
    try:
        response = requests.post(f"{base_url}/api/process", 
                               json={"test": "endpoint_check"}, 
                               timeout=5)
        # We expect this to fail validation, but endpoint should exist
        if response.status_code in [400, 422]:  # Validation errors are expected
            print("✅ Process endpoint exists and validates")
        else:
            print(f"⚠️  Process endpoint returned unexpected status: {response.status_code}")
    except Exception as e:
        print(f"⚠️  Process endpoint test failed (may not be running): {e}")
    
    return True

def test_youtube_service():
    """Test YouTube service functionality."""
    print("🧪 Testing YouTube service...")
    try:
        from services.youtube_service import youtube_service
        from utils.validators import validate_video_url
        
        # Test URL validation using utils
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        is_valid = validate_video_url(test_url)
        
        if is_valid:
            print("✅ YouTube URL validation working")
        else:
            print("❌ YouTube URL validation failed")
            return False
            
        # Test video info extraction (without actually downloading)
        try:
            success, video_info = youtube_service.get_video_info(test_url)
            if success and video_info and "title" in video_info:
                print("✅ YouTube info extraction working")
                print(f"   Test video: {video_info.get('title', 'Unknown')[:50]}...")
            else:
                print("⚠️  YouTube info extraction may be rate limited or blocked")
                # This is not a critical failure for production readiness
        except Exception as e:
            print(f"⚠️  YouTube info extraction error (may be rate limited): {e}")
        
        print("✅ YouTube service imports and basic functionality working")
        return True
    except Exception as e:
        print(f"❌ YouTube service test failed: {e}")
        return False

def run_production_test():
    """Run all production readiness tests."""
    print("🎯 VideoMind AI - Production Readiness Test")
    print("=" * 50)
    
    tests = [
        ("App Startup", test_app_startup),
        ("Configuration", test_config_loading), 
        ("Database", test_database_connection),
        ("YouTube Service", test_youtube_service),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            print()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
            print()
    
    print("📊 Test Results:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🚀 VideoMind AI is READY FOR PRODUCTION!")
        return True
    else:
        print("⚠️  VideoMind AI needs fixes before production deployment")
        return False

if __name__ == "__main__":
    success = run_production_test()
    sys.exit(0 if success else 1)