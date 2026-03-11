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
from database import create_tables, get_database
from api import health, process, directory, tasks, newsletter, jobs, queue_management
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


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    create_tables()
    print(f"🚀 {settings.app_name} v{settings.app_version} starting up!")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"💾 Database: {settings.database_url}")


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
async def admin_dashboard(request: Request):
    """Serve the admin dashboard with internal tools."""
    return templates.TemplateResponse("admin.html", {"request": request})

@app.get("/loading", response_class=HTMLResponse, include_in_schema=False)
async def loading_page(request: Request):
    """Serve a professional loading page during cold starts."""
    return templates.TemplateResponse("loading.html", {"request": request})

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
    """Serve the AI training directory page."""
    return templates.TemplateResponse(
        "directory.html",
        {"request": request, "app_name": settings.app_name}
    )


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
