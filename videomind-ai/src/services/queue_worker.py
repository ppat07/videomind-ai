"""
VideoMind AI: Queue Worker Service
High-performance worker for processing 100+ concurrent video jobs from Redis queue.
"""
import asyncio
import signal
import sys
import traceback
from datetime import datetime
from typing import Optional
from multiprocessing import Process, current_process

from job_queue import job_queue, QueueJob, JobPriority
from api.process import process_video_background


class QueueWorker:
    """High-performance worker for processing video jobs from Redis queue."""
    
    def __init__(self, worker_id: str = None):
        """Initialize worker with unique identifier."""
        process = current_process()
        self.worker_id = worker_id or f"worker_{process.pid}_{datetime.now().strftime('%H%M%S')}"
        self.running = False
        self.current_job: Optional[QueueJob] = None
        
        print(f"🚀 Initializing queue worker: {self.worker_id}")
    
    async def start(self):
        """Start the worker loop."""
        self.running = True
        print(f"▶️ Worker {self.worker_id} starting...")
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        while self.running:
            try:
                await self._process_next_job()
            except KeyboardInterrupt:
                print(f"⏹️ Worker {self.worker_id} received interrupt signal")
                break
            except Exception as e:
                print(f"❌ Worker {self.worker_id} unexpected error: {e}")
                traceback.print_exc()
                await asyncio.sleep(5)  # Brief pause before continuing
        
        print(f"🛑 Worker {self.worker_id} stopped")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"📡 Worker {self.worker_id} received signal {signum}")
        self.running = False
    
    async def _process_next_job(self):
        """Process the next available job from the queue."""
        try:
            # Check if Redis queue is available
            if not job_queue.available:
                print(f"⚠️ Redis queue not available, worker {self.worker_id} sleeping...")
                await asyncio.sleep(10)
                return
            
            # Get next job (blocking with timeout)
            job = await job_queue.dequeue_job(timeout=5)
            
            if not job:
                # No jobs available, brief pause
                await asyncio.sleep(1)
                return
            
            self.current_job = job
            print(f"🎯 Worker {self.worker_id} processing job {job.job_id}")
            
            # Process the video job
            start_time = datetime.utcnow()
            
            try:
                # Call the existing video processing function
                await process_video_background(job.job_id)
                
                # Mark job as completed
                processing_time = (datetime.utcnow() - start_time).total_seconds()
                result = {
                    "worker_id": self.worker_id,
                    "processing_time_seconds": processing_time,
                    "completed_at": datetime.utcnow().isoformat()
                }
                
                await job_queue.mark_job_completed(job.job_id, result)
                print(f"✅ Worker {self.worker_id} completed job {job.job_id} in {processing_time:.1f}s")
                
            except Exception as e:
                # Mark job as failed
                error_msg = f"Processing error: {str(e)}"
                print(f"❌ Worker {self.worker_id} failed job {job.job_id}: {error_msg}")
                
                await job_queue.mark_job_failed(job.job_id, error_msg, retry=True)
                
        except Exception as e:
            print(f"❌ Worker {self.worker_id} error in _process_next_job: {e}")
            traceback.print_exc()
            
        finally:
            self.current_job = None
    
    async def stop(self):
        """Stop the worker gracefully."""
        print(f"🛑 Stopping worker {self.worker_id}...")
        self.running = False
        
        if self.current_job:
            print(f"⏳ Waiting for current job {self.current_job.job_id} to complete...")
            # The job will continue processing and be marked appropriately
    
    def get_status(self) -> dict:
        """Get worker status information."""
        return {
            "worker_id": self.worker_id,
            "running": self.running,
            "current_job": self.current_job.job_id if self.current_job else None,
            "process_id": current_process().pid
        }


class WorkerPool:
    """Manages multiple worker processes for high-scale processing."""
    
    def __init__(self, num_workers: int = 5):
        """Initialize worker pool with specified number of workers."""
        self.num_workers = num_workers
        self.workers: list[Process] = []
        self.running = False
        
        print(f"🏗️ Initializing worker pool with {num_workers} workers")
    
    def start(self):
        """Start all workers in separate processes."""
        self.running = True
        
        for i in range(self.num_workers):
            worker_process = Process(
                target=self._run_worker_process,
                args=(f"worker_pool_{i}",),
                name=f"VideoMindWorker_{i}"
            )
            worker_process.start()
            self.workers.append(worker_process)
            print(f"🚀 Started worker process {i} (PID: {worker_process.pid})")
        
        print(f"✅ Worker pool started with {len(self.workers)} workers")
    
    def _run_worker_process(self, worker_id: str):
        """Run a single worker in its own process."""
        try:
            # Create worker instance
            worker = QueueWorker(worker_id)
            
            # Run the worker event loop
            asyncio.run(worker.start())
            
        except Exception as e:
            print(f"❌ Worker process {worker_id} failed: {e}")
            traceback.print_exc()
    
    def stop(self, timeout: int = 30):
        """Stop all workers gracefully."""
        print(f"🛑 Stopping worker pool...")
        self.running = False
        
        for i, worker in enumerate(self.workers):
            if worker.is_alive():
                print(f"⏹️ Terminating worker {i} (PID: {worker.pid})")
                worker.terminate()
                worker.join(timeout=timeout)
                
                if worker.is_alive():
                    print(f"💀 Force killing worker {i}")
                    worker.kill()
                    worker.join()
        
        self.workers.clear()
        print(f"✅ Worker pool stopped")
    
    def get_status(self) -> dict:
        """Get status of all workers in the pool."""
        alive_workers = sum(1 for w in self.workers if w.is_alive())
        
        return {
            "pool_running": self.running,
            "total_workers": len(self.workers),
            "alive_workers": alive_workers,
            "worker_pids": [w.pid for w in self.workers if w.is_alive()]
        }


# Worker management functions
async def run_single_worker(worker_id: str = None):
    """Run a single worker - useful for testing or single-worker mode."""
    worker = QueueWorker(worker_id)
    await worker.start()


def run_worker_pool(num_workers: int = 5):
    """Run a pool of workers - main production mode."""
    pool = WorkerPool(num_workers)
    
    try:
        pool.start()
        
        # Keep the main process alive
        while pool.running:
            import time
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("📡 Received interrupt signal")
    finally:
        pool.stop()


if __name__ == "__main__":
    """CLI entry point for running workers."""
    import argparse
    
    parser = argparse.ArgumentParser(description="VideoMind AI Queue Worker")
    parser.add_argument("--workers", type=int, default=5, help="Number of worker processes")
    parser.add_argument("--single", action="store_true", help="Run single worker instead of pool")
    parser.add_argument("--worker-id", type=str, help="Worker ID for single worker mode")
    
    args = parser.parse_args()
    
    if args.single:
        print(f"🚀 Starting single worker mode")
        asyncio.run(run_single_worker(args.worker_id))
    else:
        print(f"🚀 Starting worker pool with {args.workers} workers")
        run_worker_pool(args.workers)