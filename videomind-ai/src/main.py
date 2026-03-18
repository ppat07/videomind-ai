"""
VideoMind AI - Main FastAPI Application
Turn any video into AI training data.
"""
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from config import settings
from database import create_tables, get_database, engine

# Initialize Sentry error monitoring (only if DSN is configured)
_sentry_dsn = os.environ.get("SENTRY_DSN")
if _sentry_dsn:
    try:
        sentry_sdk.init(
            dsn=_sentry_dsn,
            integrations=[StarletteIntegration(), FastApiIntegration()],
            traces_sample_rate=0.1,
            environment="production" if not settings.debug else "development",
        )
        print("✅ Sentry error monitoring enabled")
    except Exception as _sentry_err:
        print(f"⚠️ Sentry init failed: {_sentry_err}")
from api import health, process, directory, newsletter, auto_init, tasks, jobs, admin, leads as leads_api
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

app.include_router(newsletter.router, prefix="/api", tags=["Newsletter"])
app.include_router(leads_api.router, prefix="/api", tags=["Leads"])


app.include_router(job_health_router, tags=["Job Health"])

# Import and include payments router
from api import payments
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])

app.include_router(auto_init.router, prefix="/api", tags=["Auto-Init"])

# Admin tools with password protection
app.include_router(tasks.router, prefix="/api", tags=["Tasks"])  
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(admin.router, prefix="/api", tags=["Admin"])


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

@app.get("/health-status", response_class=HTMLResponse, include_in_schema=False)
async def job_health_page(request: Request):
    """Serve the customer-facing job health dashboard."""
    return templates.TemplateResponse(
        "job_health.html",
        {"request": request, "app_name": settings.app_name}
    )


@app.get("/pricing", response_class=HTMLResponse, include_in_schema=False)
async def pricing_page(request: Request):
    """Serve the pricing page."""
    return templates.TemplateResponse(
        "pricing.html",
        {"request": request, "app_name": settings.app_name}
    )


@app.get("/directory", response_class=HTMLResponse, include_in_schema=False)
async def directory_page(request: Request):
    """Serve the AI training directory page."""
    return templates.TemplateResponse(
        "directory.html",
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


# Admin pages with password protection
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def verify_admin(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "videomind2026")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/sitemap.xml", include_in_schema=False)
async def sitemap(request: Request, db: Session = Depends(get_database)):
    """Dynamic sitemap.xml for all pages and directory entries."""
    from fastapi.responses import Response
    from models.directory import DirectoryEntry

    base = "https://videomind.ai"
    entries = db.query(DirectoryEntry).filter(
        DirectoryEntry.processing_status == "completed"
    ).all()

    urls = [
        f"<url><loc>{base}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>",
        f"<url><loc>{base}/pricing</loc><changefreq>monthly</changefreq><priority>0.9</priority></url>",
        f"<url><loc>{base}/directory</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
    ]
    for entry in entries:
        # Each directory entry gets its own URL slot in the sitemap
        video_id = entry.source_url.split("v=")[-1].split("&")[0] if "v=" in (entry.source_url or "") else entry.id
        urls.append(
            f"<url><loc>{base}/directory?v={video_id}</loc>"
            f"<changefreq>monthly</changefreq><priority>0.7</priority></url>"
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls)
        + "</urlset>"
    )
    return Response(content=xml, media_type="application/xml")


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    """robots.txt pointing crawlers to sitemap."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\n\nSitemap: https://videomind.ai/sitemap.xml\n"
    )


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_page(request: Request, username: str = Depends(verify_admin)):
    """Admin dashboard - password protected."""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False) 
async def dashboard_page(request: Request, username: str = Depends(verify_admin)):
    """Task dashboard - password protected."""
    return templates.TemplateResponse("dashboard.html", {"request": request, "app_name": settings.app_name})

@app.get("/jobs", response_class=HTMLResponse, include_in_schema=False)
async def jobs_page(request: Request, username: str = Depends(verify_admin)):
    """Job management - password protected."""
    return templates.TemplateResponse("jobs.html", {"request": request, "app_name": settings.app_name})


@app.get("/admin/analytics", response_class=HTMLResponse, include_in_schema=False)
async def analytics_page(request: Request, username: str = Depends(verify_admin), db: Session = Depends(get_database)):
    """Conversion funnel analytics dashboard - password protected."""
    from models.subscription import ProSubscriber, ConversionEvent, FreeTierUsage
    from sqlalchemy import func
    from datetime import timedelta

    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    # MRR: count active Pro subscribers * $49
    active_pro_count = db.query(func.count(ProSubscriber.id)).filter(
        ProSubscriber.active == True  # noqa: E712
    ).scalar() or 0
    mrr = active_pro_count * 49

    # Conversion funnel counts (last 30 days)
    def count_events(event_type, since=thirty_days_ago):
        return db.query(func.count(ConversionEvent.id)).filter(
            ConversionEvent.event == event_type,
            ConversionEvent.created_at >= since,
        ).scalar() or 0

    pricing_views = count_events("pricing_viewed")
    checkout_clicks = count_events("checkout_clicked")
    subscriptions = count_events("subscribed")
    limit_hits = count_events("limit_hit")
    pdf_purchases = count_events("pdf_purchased")

    # Daily signups last 7 days
    daily_signups = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        count = db.query(func.count(ConversionEvent.id)).filter(
            ConversionEvent.event == "subscribed",
            ConversionEvent.created_at >= day_start,
            ConversionEvent.created_at < day_end,
        ).scalar() or 0
        daily_signups.append({"date": day_start.strftime("%b %d"), "count": count})

    # Total subscribers ever
    total_subscribers = db.query(func.count(ProSubscriber.id)).scalar() or 0

    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "app_name": settings.app_name,
        "mrr": mrr,
        "active_pro_count": active_pro_count,
        "total_subscribers": total_subscribers,
        "pricing_views": pricing_views,
        "checkout_clicks": checkout_clicks,
        "subscriptions_30d": subscriptions,
        "limit_hits_30d": limit_hits,
        "pdf_purchases_30d": pdf_purchases,
        "daily_signups": daily_signups,
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
