#!/usr/bin/env python3
"""
VideoMind AI: Worker Startup Script
Start Redis queue workers for high-scale video processing.
"""
import sys
import os
import subprocess
import signal
import time
from pathlib import Path
from typing import List

# Add src directory to path so workers can import modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from services.queue_worker import run_worker_pool, run_single_worker
from services.job_queue import job_queue
import asyncio


def check_redis_connection():
    """Check if Redis is available."""
    try:
        import redis
        client = redis.from_url("redis://localhost:6379/0", socket_connect_timeout=2)
        client.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        print("💡 Make sure Redis is running: brew services start redis")
        return False


def check_dependencies():
    """Check if all required dependencies are available."""
    try:
        import redis
        import fastapi
        import sqlalchemy
        print("✅ All dependencies available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Run: pip install -r requirements.txt")
        return False


def start_redis_if_needed():
    """Start Redis if it's not running (macOS with Homebrew)."""
    if check_redis_connection():
        return True
    
    print("🚀 Attempting to start Redis...")
    try:
        # Try to start Redis with Homebrew
        result = subprocess.run(
            ["brew", "services", "start", "redis"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Redis started via Homebrew")
            time.sleep(2)  # Give Redis time to start
            return check_redis_connection()
        else:
            print(f"⚠️ Homebrew Redis start failed: {result.stderr}")
            
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("⚠️ Homebrew not available or Redis start timed out")
    
    # Try manual Redis start
    try:
        print("🔧 Trying to start Redis manually...")
        subprocess.Popen(["redis-server"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        return check_redis_connection()
    except FileNotFoundError:
        print("❌ Redis not found. Install with: brew install redis")
        return False


def main():
    """Main worker startup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VideoMind AI Worker Manager")
    parser.add_argument("--workers", type=int, default=5, help="Number of worker processes (default: 5)")
    parser.add_argument("--single", action="store_true", help="Run single worker for debugging")
    parser.add_argument("--check-only", action="store_true", help="Only check dependencies and Redis")
    parser.add_argument("--start-redis", action="store_true", help="Attempt to start Redis if not running")
    
    args = parser.parse_args()
    
    print("🎯 VideoMind AI - Queue Worker Manager")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check/start Redis
    if args.start_redis or not check_redis_connection():
        if not start_redis_if_needed():
            print("\n❌ Redis is required for queue workers")
            print("💡 Install Redis: brew install redis")
            print("💡 Start Redis: brew services start redis")
            return 1
    
    if args.check_only:
        print("\n✅ All systems ready for worker deployment")
        return 0
    
    # Validate worker count
    if args.workers < 1:
        print("❌ Worker count must be at least 1")
        return 1
    elif args.workers > 20:
        print("⚠️ More than 20 workers not recommended - limiting to 20")
        args.workers = 20
    
    print(f"\n🚀 Starting VideoMind AI queue workers...")
    
    try:
        if args.single:
            print("🔧 Single worker mode (for debugging)")
            asyncio.run(run_single_worker("debug_worker"))
        else:
            print(f"🏭 Pool mode with {args.workers} workers")
            run_worker_pool(args.workers)
            
    except KeyboardInterrupt:
        print("\n⏹️ Shutdown requested")
    except Exception as e:
        print(f"\n❌ Worker startup failed: {e}")
        return 1
    
    print("👋 Workers stopped")
    return 0


if __name__ == "__main__":
    sys.exit(main())