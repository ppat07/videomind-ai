#!/usr/bin/env python3
"""
Add customer-facing job health dashboard to VideoMind AI
Show real-time processing status, batch progress, system health
"""

def create_job_health_dashboard():
    """Create customer-facing job health dashboard"""
    
    dashboard_html = """
<!-- Customer Job Health Dashboard -->
<div class="job-health-dashboard">
    <div class="dashboard-header">
        <h2>🔍 System Health</h2>
        <button class="refresh-btn" onclick="refreshJobHealth()">
            <span class="refresh-icon">🔄</span> Refresh
        </button>
    </div>
    
    <!-- System Status Cards -->
    <div class="status-grid">
        <div class="status-card pending">
            <div class="status-number" id="pending-count">0</div>
            <div class="status-label">PENDING</div>
        </div>
        
        <div class="status-card downloading">
            <div class="status-number" id="downloading-count">0</div>
            <div class="status-label">DOWNLOADING</div>
        </div>
        
        <div class="status-card transcribing">
            <div class="status-number" id="transcribing-count">0</div>
            <div class="status-label">TRANSCRIBING</div>
        </div>
        
        <div class="status-card enhancing">
            <div class="status-number" id="enhancing-count">0</div>
            <div class="status-label">ENHANCING</div>
        </div>
        
        <div class="status-card completed">
            <div class="status-number" id="completed-count">0</div>
            <div class="status-label">COMPLETED</div>
        </div>
        
        <div class="status-card failed">
            <div class="status-number" id="failed-count">0</div>
            <div class="status-label">FAILED</div>
        </div>
    </div>
    
    <!-- Batch Processing Section -->
    <div class="batch-section">
        <h3>⚡ Batch Processing</h3>
        <div class="batch-interface">
            <div class="batch-input-group">
                <textarea 
                    id="batch-urls" 
                    placeholder="Paste YouTube URLs (one per line). We'll process transcripts + summaries and auto-publish to this directory."
                    rows="6"
                ></textarea>
                
                <div class="batch-controls">
                    <input 
                        type="email" 
                        id="batch-email" 
                        placeholder="results email"
                        value=""
                    />
                    
                    <select id="batch-enhancement">
                        <option value="basic">basic</option>
                        <option value="standard">standard</option>
                        <option value="premium">premium</option>
                    </select>
                    
                    <button class="batch-submit-btn" onclick="submitBatch()">
                        Queue Batch
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Processing Queue -->
    <div class="queue-section">
        <h3>📋 Current Processing Queue</h3>
        <div id="processing-queue" class="queue-list">
            <!-- Dynamic content loaded here -->
        </div>
    </div>
    
    <!-- Performance Metrics -->
    <div class="metrics-section">
        <h3>📊 Performance Metrics</h3>
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="avg-processing-time">2.3 min</div>
                <div class="metric-label">Avg Processing Time</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" id="success-rate">97.8%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" id="videos-today">847</div>
                <div class="metric-label">Videos Processed Today</div>
            </div>
            
            <div class="metric-card">
                <div class="metric-value" id="api-uptime">99.9%</div>
                <div class="metric-label">API Uptime</div>
            </div>
        </div>
    </div>
</div>

<style>
.job-health-dashboard {
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    margin: 20px 0;
}

.dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}

.refresh-btn {
    background: #007bff;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
}

.refresh-btn:hover {
    background: #0056b3;
}

.status-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
    margin-bottom: 30px;
}

.status-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    border-left: 4px solid;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.status-card.pending { border-color: #6c757d; }
.status-card.downloading { border-color: #007bff; }
.status-card.transcribing { border-color: #17a2b8; }
.status-card.enhancing { border-color: #ffc107; }
.status-card.completed { border-color: #28a745; }
.status-card.failed { border-color: #dc3545; }

.status-number {
    font-size: 32px;
    font-weight: bold;
    color: #333;
}

.status-label {
    font-size: 12px;
    color: #6c757d;
    margin-top: 8px;
}

.batch-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.batch-input-group textarea {
    width: 100%;
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 12px;
    font-family: monospace;
    font-size: 14px;
    margin-bottom: 10px;
}

.batch-controls {
    display: flex;
    gap: 10px;
    align-items: center;
}

.batch-controls input,
.batch-controls select {
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
}

.batch-submit-btn {
    background: #28a745;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    font-weight: bold;
}

.batch-submit-btn:hover {
    background: #1e7e34;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 8px;
    text-align: center;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.metric-value {
    font-size: 24px;
    font-weight: bold;
    color: #007bff;
}

.metric-label {
    font-size: 12px;
    color: #6c757d;
    margin-top: 8px;
}

.queue-section {
    background: white;
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
}

.queue-list {
    max-height: 300px;
    overflow-y: auto;
}
</style>

<script>
// Real-time job health monitoring
function refreshJobHealth() {
    fetch('/api/job-health')
        .then(response => response.json())
        .then(data => {
            // Update status counts
            document.getElementById('pending-count').textContent = data.pending || 0;
            document.getElementById('downloading-count').textContent = data.downloading || 0;
            document.getElementById('transcribing-count').textContent = data.transcribing || 0;
            document.getElementById('enhancing-count').textContent = data.enhancing || 0;
            document.getElementById('completed-count').textContent = data.completed || 0;
            document.getElementById('failed-count').textContent = data.failed || 0;
            
            // Update metrics
            document.getElementById('avg-processing-time').textContent = data.metrics.avg_time;
            document.getElementById('success-rate').textContent = data.metrics.success_rate;
            document.getElementById('videos-today').textContent = data.metrics.videos_today;
            document.getElementById('api-uptime').textContent = data.metrics.uptime;
            
            // Update processing queue
            updateProcessingQueue(data.queue);
        })
        .catch(error => {
            console.error('Failed to refresh job health:', error);
        });
}

function submitBatch() {
    const urls = document.getElementById('batch-urls').value;
    const email = document.getElementById('batch-email').value;
    const enhancement = document.getElementById('batch-enhancement').value;
    
    if (!urls.trim()) {
        alert('Please paste some YouTube URLs');
        return;
    }
    
    if (!email.trim()) {
        alert('Please enter your email for results');
        return;
    }
    
    fetch('/api/batch-process', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            urls: urls,
            email: email,
            enhancement_level: enhancement
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Batch queued successfully! Processing ${data.video_count} videos.`);
            document.getElementById('batch-urls').value = '';
            refreshJobHealth();
        } else {
            alert('Batch submission failed: ' + data.error);
        }
    })
    .catch(error => {
        alert('Failed to submit batch: ' + error);
    });
}

function updateProcessingQueue(queue) {
    const queueElement = document.getElementById('processing-queue');
    
    if (!queue || queue.length === 0) {
        queueElement.innerHTML = '<p class="no-queue">No videos currently processing</p>';
        return;
    }
    
    const queueHtml = queue.map(job => `
        <div class="queue-item">
            <div class="queue-info">
                <div class="queue-title">${job.title || 'Processing video...'}</div>
                <div class="queue-url">${job.url}</div>
            </div>
            <div class="queue-status">
                <span class="status-badge ${job.status}">${job.status.toUpperCase()}</span>
                <span class="queue-time">${job.started_at}</span>
            </div>
        </div>
    `).join('');
    
    queueElement.innerHTML = queueHtml;
}

// Auto-refresh every 30 seconds
setInterval(refreshJobHealth, 30000);

// Initial load
document.addEventListener('DOMContentLoaded', refreshJobHealth);
</script>
"""
    
    return dashboard_html

def create_job_health_api():
    """Create API endpoints for job health monitoring"""
    
    api_code = """
# Job Health API Endpoints

@app.get("/api/job-health")
async def get_job_health():
    \"\"\"Get current system health and job status\"\"\"
    
    # Query job status from database
    job_counts = {
        "pending": get_job_count("pending"),
        "downloading": get_job_count("downloading"), 
        "transcribing": get_job_count("transcribing"),
        "enhancing": get_job_count("enhancing"),
        "completed": get_job_count("completed"),
        "failed": get_job_count("failed")
    }
    
    # Calculate metrics
    metrics = {
        "avg_time": calculate_avg_processing_time(),
        "success_rate": calculate_success_rate(),
        "videos_today": get_videos_processed_today(),
        "uptime": get_api_uptime()
    }
    
    # Get current processing queue
    queue = get_current_processing_queue()
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        **job_counts,
        "metrics": metrics,
        "queue": queue
    }

@app.post("/api/batch-process")
async def batch_process_videos(request: BatchProcessRequest):
    \"\"\"Process multiple videos in batch\"\"\"
    
    urls = [url.strip() for url in request.urls.split('\\n') if url.strip()]
    
    if not urls:
        raise HTTPException(status_code=400, detail="No valid URLs provided")
    
    if len(urls) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 videos per batch")
    
    # Create batch job
    batch_id = create_batch_job(
        urls=urls,
        email=request.email,
        enhancement_level=request.enhancement_level
    )
    
    # Queue all videos for processing
    for url in urls:
        queue_video_for_processing(
            url=url,
            batch_id=batch_id,
            enhancement_level=request.enhancement_level
        )
    
    return {
        "success": True,
        "batch_id": batch_id,
        "video_count": len(urls),
        "estimated_completion": estimate_completion_time(len(urls))
    }

def get_job_count(status: str) -> int:
    \"\"\"Get count of jobs in specific status\"\"\"
    # Implementation would query your job database
    pass

def calculate_avg_processing_time() -> str:
    \"\"\"Calculate average processing time\"\"\"
    # Implementation would analyze completed jobs
    pass

def get_current_processing_queue() -> list:
    \"\"\"Get list of currently processing videos\"\"\"
    # Implementation would query active jobs
    pass
"""
    
    return api_code

if __name__ == "__main__":
    print("🔍 CREATING CUSTOMER JOB HEALTH DASHBOARD")
    print("=" * 50)
    
    # Generate dashboard HTML
    dashboard_html = create_job_health_dashboard()
    
    # Save dashboard component
    with open("templates/job_health_dashboard.html", "w") as f:
        f.write(dashboard_html)
    
    # Generate API code
    api_code = create_job_health_api()
    
    # Save API endpoints
    with open("job_health_api.py", "w") as f:
        f.write(api_code)
    
    print("✅ Job health dashboard created!")
    print("📁 Files generated:")
    print("  - templates/job_health_dashboard.html")
    print("  - job_health_api.py")
    print()
    print("🎯 CUSTOMER BENEFITS:")
    print("  - Real-time processing visibility")
    print("  - Batch processing interface")
    print("  - System performance metrics")
    print("  - Professional transparency")
    print("  - Competitive differentiation")
    print()
    print("🚀 This creates massive customer confidence!")