#!/usr/bin/env python3
"""
Simple test to check if the FastAPI app can start without errors.
"""
import sys
import os
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test if all imports work."""
    try:
        print("🔍 Testing basic imports...")
        import config
        print("   ✅ config")
        
        import database
        print("   ✅ database")
        
        from models.video import VideoJob
        print("   ✅ models.video")
        
        from api import health
        print("   ✅ api.health")
        
        from services.youtube_service import youtube_service
        print("   ✅ services.youtube_service")
        
        print("✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False

def test_database():
    """Test database connection."""
    try:
        print("\n🔍 Testing database...")
        from database import create_tables, engine
        
        # Try to create tables
        create_tables()
        print("   ✅ Database tables created")
        
        # Test connection
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("   ✅ Database connection successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        return False

def test_app_creation():
    """Test FastAPI app creation."""
    try:
        print("\n🔍 Testing FastAPI app creation...")
        import main
        
        app = main.app
        print("   ✅ FastAPI app created")
        
        # Check if routes are loaded
        routes = [route.path for route in app.routes]
        print(f"   📋 Routes loaded: {len(routes)} routes")
        
        return True
        
    except Exception as e:
        print(f"   ❌ App creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 VideoMind AI - App Test\n")
    
    success = True
    
    # Test imports
    if not test_imports():
        success = False
    
    # Test database
    if success and not test_database():
        success = False
    
    # Test app creation
    if success and not test_app_creation():
        success = False
    
    print("\n" + "="*50)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("   The app should be able to start successfully.")
        print("   Run: python3 run.py")
    else:
        print("❌ SOME TESTS FAILED")
        print("   Fix the issues above before starting the app.")
    print("="*50)