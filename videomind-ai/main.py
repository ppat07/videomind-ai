"""
VideoMind AI - Production Entry Point
Railway deployment entry point that imports the actual FastAPI app from src/
"""
import os
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import the actual FastAPI app from src/main.py
try:
    from main import app
except ImportError as e:
    print(f"Failed to import app from src/main.py: {e}")
    sys.exit(1)

# Export the app for uvicorn
__all__ = ["app"]