#!/usr/bin/env python3
"""
VideoMind AI - Simple Run Script
Direct execution of the FastAPI application.
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Set environment
os.environ.setdefault("PYTHONPATH", str(src_path))

if __name__ == "__main__":
    # Check if .env file exists (optional in production)
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists() and not os.environ.get("RAILWAY_ENVIRONMENT"):
        print("⚠️  Warning: .env file not found!")
        print("   Copy .env.example to .env and configure your settings.")
        sys.exit(1)
    
    try:
        print("🚀 Starting VideoMind AI...")
        print("   📱 Web Interface: http://localhost:8000")
        print("   📋 API Docs: http://localhost:8000/docs")
        print("   💚 Health Check: http://localhost:8000/health")
        print("   🛑 Press Ctrl+C to stop")
        print()
        
        import uvicorn
        # Get port from environment (Railway sets this)
        port = int(os.environ.get("PORT", 8000))
        # Import the app using the module path
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=port,
            reload=os.environ.get("RAILWAY_ENVIRONMENT") is None,  # Only reload in dev
            log_level="info",
            app_dir=str(src_path)
        )
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Run: pip3 install -r requirements.txt")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n👋 VideoMind AI stopped!")
        
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)