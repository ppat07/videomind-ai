#!/usr/bin/env python3
"""
VideoMind AI - Setup Test
Quick test to verify everything is configured correctly.
"""
import sys
import os
from pathlib import Path

def test_dependencies():
    """Test if required dependencies are available."""
    print("🔍 Testing dependencies...")
    
    required_modules = [
        'fastapi',
        'uvicorn', 
        'openai',
        'yt_dlp',
        'sqlalchemy',
        'pydantic'
    ]
    
    missing = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module}")
            missing.append(module)
    
    if missing:
        print(f"\n❌ Missing modules: {', '.join(missing)}")
        print("   Run: pip3 install -r requirements.txt")
        return False
    else:
        print("\n✅ All dependencies installed!")
        return True

def test_env_config():
    """Test environment configuration."""
    print("\n🔍 Testing configuration...")
    
    env_file = Path(".env")
    if not env_file.exists():
        print("   ❌ .env file not found")
        return False
    
    print("   ✅ .env file found")
    
    # Test OpenAI API key
    sys.path.insert(0, 'src')
    try:
        from config import settings
        if settings.openai_api_key and settings.openai_api_key.startswith('sk-'):
            print("   ✅ OpenAI API key configured")
        else:
            print("   ❌ OpenAI API key missing or invalid")
            return False
    except Exception as e:
        print(f"   ❌ Config error: {e}")
        return False
    
    return True

def test_directories():
    """Test required directories exist."""
    print("\n🔍 Testing directories...")
    
    dirs = ['temp', 'static', 'templates']
    for dir_name in dirs:
        path = Path(dir_name)
        if path.exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ⚠️  {dir_name}/ missing - creating...")
            path.mkdir(exist_ok=True)
    
    return True

def test_openai_connection():
    """Test OpenAI API connection."""
    print("\n🔍 Testing OpenAI connection...")
    
    try:
        sys.path.insert(0, 'src')
        from config import settings
        import openai
        
        # Set API key
        openai.api_key = settings.openai_api_key
        
        # Test with a simple call (list models)
        models = openai.models.list()
        print("   ✅ OpenAI API connection successful")
        print(f"   📋 Available models: {len(models.data)} found")
        return True
        
    except Exception as e:
        print(f"   ❌ OpenAI API error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 VideoMind AI - Setup Test\n")
    
    all_good = True
    
    # Test 1: Dependencies
    if not test_dependencies():
        all_good = False
    
    # Test 2: Configuration
    if not test_env_config():
        all_good = False
    
    # Test 3: Directories
    if not test_directories():
        all_good = False
    
    # Test 4: OpenAI Connection (only if other tests pass)
    if all_good and not test_openai_connection():
        all_good = False
    
    print("\n" + "="*50)
    
    if all_good:
        print("🎉 ALL TESTS PASSED!")
        print("   VideoMind AI is ready to launch!")
        print("   Run: python3 start.py")
    else:
        print("❌ SETUP INCOMPLETE")
        print("   Fix the issues above and run this test again.")
    
    print("="*50)