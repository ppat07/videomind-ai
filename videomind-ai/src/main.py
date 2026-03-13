"""
VideoMind AI - Main FastAPI Application
Turn any video into AI training data.
"""
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from config import settings
from database import create_tables, get_database, engine
from api import health, process, directory, tasks, newsletter, jobs, queue_management, admin, auto_init
from job_health import router as job_health_router
# Import PDF delivery system
import sys
sys.path.append('..')
try:
    from pdf_delivery import router as pdf_delivery_router
    PDF_DELIVERY_AVAILABLE = True
except ImportError:
    print("⚠️ PDF delivery system not found")
    PDF_DELIVERY_AVAILABLE = False
from models.video import VideoJob, ProcessingTier
from datetime import datetime
from sqlalchemy.orm import Session
import os

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Turn any video into AI training data",
    version=settings.app_version,
    debug=settings.debug
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("RENDER", "unknown")
    }

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://videomind.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
import os
from pathlib import Path

# Dynamic template path detection for both local and production
current_dir = Path(__file__).parent
if (current_dir / "templates").exists():
    template_dir = "templates"  # Production: we're in src/
else:
    template_dir = "src/templates"  # Local: we're in root/

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=template_dir)

# Include API routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(process.router, prefix="/api", tags=["Processing"])
app.include_router(directory.router, prefix="/api", tags=["Directory"])
app.include_router(tasks.router, prefix="/api", tags=["Tasks"])
app.include_router(newsletter.router, prefix="/api", tags=["Newsletter"])
app.include_router(jobs.router, prefix="/api", tags=["Job Management"])
app.include_router(queue_management.router, prefix="/api/queue", tags=["Queue Management"])
app.include_router(job_health_router, tags=["Job Health"])

# Import and include payments router
from api import payments
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])
app.include_router(auto_init.router, prefix="/api", tags=["Auto-Init"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    create_tables()
    print(f"🚀 {settings.app_name} v{settings.app_version} starting up!")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"💾 Database: {settings.database_url}")
    
    # Ensure directory has seed data (fallback safety net)
    try:
        from sqlalchemy.orm import sessionmaker
        from models.directory import DirectoryEntry, ContentType
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        count = db.query(DirectoryEntry).count()
        if count == 0:
            print("📚 Directory empty, auto-seeding with OpenClaw videos...")
            
            # Create seed data directly (sync version)
            seed_videos = [
                {
                    "title": "ClawdBot is the most powerful AI tool I've ever used in my life. Here's how to set it up",
                    "source_url": "https://www.youtube.com/watch?v=Qkqe-uRhQJE&t=42s",
                    "video_url": "https://www.youtube.com/watch?v=Qkqe-uRhQJE&t=42s",
                    "content_type": ContentType.VIDEO,
                    "creator_name": "Alex Finn",
                    "category_primary": "Setup & Onboarding",
                    "difficulty": "Beginner",
                    "tools_mentioned": "OpenClaw; CLI; OAuth/Auth setup",
                    "summary_5_bullets": "• Introduces OpenClaw value\\n• Walkthrough setup\\n• Connect auth/models\\n• Run first workflow\\n• Quick-win setup tips",
                    "best_for": "New users who want fast setup without mistakes",
                    "signal_score": 82,
                    "processing_status": "reviewed",
                    "teaches_agent_to": "Execute setup and onboarding workflows quickly.",
                    "prompt_template": "Implement a fast setup workflow for OpenClaw with clear commands and validation steps.",
                    "execution_checklist": "[ ] Confirm prerequisites\\n[ ] Configure auth\\n[ ] Verify model\\n[ ] Run first task\\n[ ] Validate output",
                    "agent_training_script": "TRAINING SCRIPT: Setup & onboarding workflow with clear commands and validation."
                },
                {
                    "title": "You NEED to do this with OpenClaw immediately!",
                    "source_url": "https://www.youtube.com/watch?v=Aj6hoC9JaLI",
                    "video_url": "https://www.youtube.com/watch?v=Aj6hoC9JaLI",
                    "content_type": ContentType.VIDEO,
                    "creator_name": "Alex Finn", 
                    "category_primary": "Automation Workflows",
                    "difficulty": "Beginner",
                    "tools_mentioned": "OpenClaw; workflow automation; model/session setup",
                    "summary_5_bullets": "• High-impact immediate action\\n• Practical first wins\\n• Repeatable workflow\\n• Set defaults early\\n• Foundation for advanced use",
                    "best_for": "Users who want fastest first ROI",
                    "signal_score": 80,
                    "processing_status": "reviewed",
                    "teaches_agent_to": "Execute repeatable automation workflows quickly.",
                    "prompt_template": "Build a repeatable automation workflow from this tutorial and include copy/paste commands.",
                    "execution_checklist": "[ ] Define objective\\n[ ] Configure tools\\n[ ] Run workflow\\n[ ] Validate result\\n[ ] Document reusable steps",
                    "agent_training_script": "TRAINING SCRIPT: Automation workflow execution with validation and documentation."
                },
                {
                    "title": "Making $$$ with OpenClaw",
                    "source_url": "https://www.youtube.com/watch?v=i13XK-uUOLQ&t=20s",
                    "video_url": "https://www.youtube.com/watch?v=i13XK-uUOLQ&t=20s", 
                    "content_type": ContentType.VIDEO,
                    "creator_name": "Greg Isenberg",
                    "category_primary": "Business Use Cases",
                    "difficulty": "Intermediate",
                    "tools_mentioned": "OpenClaw; automation workflows; lead/revenue systems",
                    "summary_5_bullets": "• Monetization opportunities\\n• Revenue workflows\\n• Outreach/ops patterns\\n• Implementation focus\\n• OpenClaw as business leverage",
                    "best_for": "Founders/solopreneurs turning automation into revenue",
                    "signal_score": 86,
                    "processing_status": "reviewed", 
                    "teaches_agent_to": "Implement business-focused AI workflows that drive revenue outcomes.",
                    "prompt_template": "Create a monetization-focused execution plan with steps, prompts, and KPI checks.",
                    "execution_checklist": "[ ] Define revenue objective\\n[ ] Build workflow\\n[ ] Launch test\\n[ ] Measure KPI\\n[ ] Iterate",
                    "agent_training_script": "TRAINING SCRIPT: Business workflow implementation focused on measurable outcomes."
                }
            ]
            
            for video_data in seed_videos:
                entry = DirectoryEntry(**video_data)
                db.add(entry)
            
            db.commit()
            print(f"✅ Startup auto-seeding completed - added {len(seed_videos)} OpenClaw videos")
        else:
            print(f"📚 Directory contains {count} entries, no seeding needed")
            
        db.close()
    except Exception as e:
        print(f"⚠️ Startup seeding check failed: {e}")
        print("📝 Manual seeding via /api/directory/seed still available")


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_dashboard(request: Request):
    """Serve the admin dashboard with internal tools."""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/loading", response_class=HTMLResponse, include_in_schema=False)
async def loading_page(request: Request):
    """Serve a professional loading page during cold starts."""
    return templates.TemplateResponse("loading_professional.html", {"request": request})

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage(request: Request):
    """Serve the main homepage."""
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "app_name": settings.app_name}
    )


@app.get("/status/{job_id}", response_class=HTMLResponse, include_in_schema=False)
async def job_status_page(request: Request, job_id: str):
    """Serve the job status page."""
    return templates.TemplateResponse(
        "status.html", 
        {"request": request, "job_id": job_id, "app_name": settings.app_name}
    )

@app.get("/health", response_class=HTMLResponse, include_in_schema=False)
async def job_health_page(request: Request):
    """Serve the customer-facing job health dashboard."""
    return templates.TemplateResponse(
        "job_health.html", 
        {"request": request, "app_name": settings.app_name}
    )


@app.get("/directory", response_class=HTMLResponse, include_in_schema=False)
async def directory_page(request: Request):
    """Directory temporarily offline for maintenance."""
    from fastapi.responses import HTMLResponse
    
    maintenance_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Directory Maintenance - VideoMind AI</title>
        <style>
            body {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
            }
            .container {
                text-align: center;
                max-width: 500px;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 16px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            h1 {
                font-size: 2.5rem;
                margin-bottom: 1rem;
                font-weight: 700;
            }
            p {
                font-size: 1.1rem;
                margin-bottom: 2rem;
                opacity: 0.9;
                line-height: 1.6;
            }
            .status {
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                background: rgba(34, 197, 94, 0.2);
                padding: 0.5rem 1rem;
                border-radius: 8px;
                font-weight: 500;
            }
            .back-link {
                display: inline-block;
                margin-top: 2rem;
                padding: 0.75rem 1.5rem;
                background: rgba(255, 255, 255, 0.2);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 500;
                transition: all 0.3s ease;
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            .back-link:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 Directory Under Maintenance</h1>
            <p>We're currently enhancing our AI training directory to provide you with the highest quality content. The directory is temporarily offline while we verify and improve our video collection.</p>
            
            <div class="status">
                <span>🚀</span>
                <span>Quality improvements in progress</span>
            </div>
            
            <p style="margin-top: 2rem; font-size: 0.9rem; opacity: 0.8;">
                VideoMind AI's core video processing features remain fully operational. 
                The directory will return shortly with verified, high-quality content.
            </p>
            
            <a href="/" class="back-link">← Back to VideoMind AI</a>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=maintenance_html)


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard_page(request: Request):
    """Serve task dashboard page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "app_name": settings.app_name}
    )


@app.get("/jobs", response_class=HTMLResponse, include_in_schema=False)
async def jobs_page(request: Request):
    """Serve job management page."""
    return templates.TemplateResponse(
        "jobs.html",
        {"request": request, "app_name": settings.app_name}
    )


@app.get("/queue", response_class=HTMLResponse, include_in_schema=False)
async def queue_dashboard_page(request: Request):
    """Serve queue monitoring dashboard."""
    return templates.TemplateResponse(
        "queue_dashboard.html",
        {"request": request, "app_name": settings.app_name}
    )


@app.get("/checkout", response_class=HTMLResponse, include_in_schema=False)
async def checkout_page(request: Request):
    """Serve the checkout page with products."""
    return templates.TemplateResponse(
        "checkout.html",
        {"request": request, "app_name": settings.app_name}
    )


@app.get("/success", response_class=HTMLResponse, include_in_schema=False)
async def success_page(request: Request):
    """Serve the success page after payment."""
    session_id = request.query_params.get('session_id')
    return templates.TemplateResponse(
        "success.html",
        {"request": request, "app_name": settings.app_name, "session_id": session_id}
    )


@app.get("/payment/{job_id}", response_class=HTMLResponse, include_in_schema=False)
async def payment_page(request: Request, job_id: str, db: Session = Depends(get_database)):
    """Serve the payment page for a specific job."""
    # Get job details
    job = db.query(VideoJob).filter(VideoJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Get pricing for tier
    from api.payments import PRICING_TIERS
    amount_cents = PRICING_TIERS.get(ProcessingTier(job.tier), PRICING_TIERS[ProcessingTier.BASIC])
    amount_dollars = amount_cents / 100
    
    return templates.TemplateResponse(
        "payment.html",
        {
            "request": request, 
            "app_name": settings.app_name,
            "job_id": job_id,
            "video_url": job.youtube_url,
            "tier": job.tier,
            "email": job.email,
            "amount": amount_dollars,
            "stripe_publishable_key": settings.stripe_publishable_key or ""
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
