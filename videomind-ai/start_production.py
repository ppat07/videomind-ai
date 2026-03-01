#!/usr/bin/env python3
"""
VideoMind AI - Production Startup Script
Fixed startup script for production deployment on Render.com
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """Start VideoMind AI in production mode."""
    
    # Ensure we're in the right directory
    app_root = Path(__file__).parent
    os.chdir(app_root)
    
    # Set PYTHONPATH to include src directory
    src_path = app_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Set environment variable for Python path
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{src_path}:{env.get('PYTHONPATH', '')}"
    
    # Get port from environment (Render sets this)
    port = os.environ.get("PORT", "8000")
    host = "0.0.0.0"  # Bind to all interfaces for production
    
    print(f"🚀 Starting VideoMind AI on {host}:{port}")
    print(f"📁 Working directory: {app_root}")
    print(f"🐍 Python path: {src_path}")
    
    # Start the application
    try:
        # Use uvicorn directly with proper module path
        cmd = [
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", host,
            "--port", port,
            "--workers", "1",
            "--log-level", "info"
        ]
        
        print(f"📋 Command: {' '.join(cmd)}")
        
        # Change to src directory and run
        os.chdir(src_path)
        subprocess.run(cmd, env=env, check=True)
        
    except KeyboardInterrupt:
        print("\n👋 Shutting down VideoMind AI...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()