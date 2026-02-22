#!/usr/bin/env python
"""
VideoMind AI - Start Script
Simple script to launch the FastAPI application.
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    # Check if .env file exists
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("⚠️  Warning: .env file not found!")
        print("   Copy .env.example to .env and configure your settings.")
        print("   Continuing with default settings...")
    
    # Import and run the app
    try:
        import uvicorn
        from main import app
        
        print("🚀 Starting VideoMind AI...")
        print("   📱 Web Interface: http://localhost:8000")
        print("   📋 API Docs: http://localhost:8000/docs")
        print("   💚 Health Check: http://localhost:8000/health")
        print("   🛑 Press Ctrl+C to stop")
        print()
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure you've installed all requirements:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)