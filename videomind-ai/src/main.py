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
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from api import health, process, directory, newsletter, auto_init, tasks, jobs, admin, leads as leads_api, demo as demo_api
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
    allow_origins=["*"] if settings.debug else ["https://videomind-ai.com"],
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

app.include_router(demo_api.router, prefix="/api", tags=["Demo"])
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


_nurture_scheduler = AsyncIOScheduler()


async def _run_nurture_emails():
    """Standalone nurture email job — creates its own DB session."""
    from database import SessionLocal
    from api.leads import send_nurture_emails as _send_nurture
    db = SessionLocal()
    try:
        result = await _send_nurture(db=db)
        print(f"📧 Nurture scheduler: sent={result.get('sent', 0)}, pending={result.get('total_pending', 0)}")
    except Exception as e:
        print(f"⚠️ Nurture scheduler error: {e}")
    finally:
        db.close()


async def _keep_alive_ping():
    """Self-ping /health every 10 min to prevent Render free-tier spin-down.
    Once the service is warm, this keeps it warm between user visits."""
    import os
    import asyncio
    port = os.environ.get("PORT", "8000")
    try:
        proc = await asyncio.create_subprocess_exec(
            "curl", "-sf", f"http://localhost:{port}/health",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
    except Exception:
        pass  # silent — keep-alive is best-effort


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    create_tables()
    print(f"🚀 {settings.app_name} v{settings.app_version} starting up!")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"💾 Database: {settings.database_url}")
    
    # Ensure directory has seed data — loads from src/data/seed_videos.json
    try:
        import json as _json
        from pathlib import Path as _Path
        from sqlalchemy.orm import sessionmaker
        from models.directory import DirectoryEntry

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()

        count = db.query(DirectoryEntry).count()
        seed_file = _Path(__file__).parent / "data" / "seed_videos.json"

        import uuid as _uuid, re as _re
        _DIR_NS = _uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
        def _stable_id(url: str) -> str:
            m = _re.search(r'[?&]v=([^&]+)', url)
            key = f"youtube:{m.group(1)}" if m else url.split('?')[0]
            return str(_uuid.uuid5(_DIR_NS, key))

        # Detect if entries have wrong (non-stable) IDs — wipe and reseed
        needs_reseed = False
        if count > 0 and seed_file.exists():
            with open(seed_file) as _f:
                seed_videos = _json.load(_f)
            first_src = seed_videos[0].get("source_url", "") if seed_videos else ""
            if first_src:
                expected_id = _stable_id(first_src)
                first_entry = db.query(DirectoryEntry).filter(
                    DirectoryEntry.source_url == first_src
                ).first()
                if first_entry and first_entry.id != expected_id:
                    print(f"⚠️ Entries have non-stable IDs (found {first_entry.id[:8]}..., expected {expected_id[:8]}...). Reseeding.")
                    db.query(DirectoryEntry).delete()
                    db.commit()
                    count = 0
                    needs_reseed = True

        if (count < 50 or needs_reseed) and seed_file.exists():
            if not needs_reseed:
                print(f"📚 Directory has {count} entries (< 50), loading seed videos...")
                with open(seed_file) as _f:
                    seed_videos = _json.load(_f)
            added = 0
            for video_data in seed_videos:
                src_url = video_data.get("source_url", "")
                existing = db.query(DirectoryEntry).filter(
                    DirectoryEntry.source_url == src_url
                ).first()
                if not existing:
                    fields = {k: v for k, v in video_data.items()
                              if hasattr(DirectoryEntry, k)}
                    if src_url and "id" not in fields:
                        fields["id"] = _stable_id(src_url)
                    entry = DirectoryEntry(**fields)
                    db.add(entry)
                    added += 1
            db.commit()
            print(f"✅ Startup seeding completed — added {added} videos ({db.query(DirectoryEntry).count()} total)")
        else:
            print(f"📚 Directory contains {count} stable-ID entries, no seeding needed")

        db.close()
    except Exception as e:
        print(f"⚠️ Startup seeding check failed: {e}")
        print("📝 Manual seeding via /api/directory/seed still available")

    # Ensure FOUNDING Stripe coupon exists ($20/month recurring discount off $49 = $29/month)
    try:
        from api.payments import stripe, stripe_ready
        if stripe and stripe_ready:
            try:
                stripe.Coupon.retrieve("FOUNDING")
                print("✅ FOUNDING Stripe coupon already exists")
            except Exception:
                stripe.Coupon.create(
                    id="FOUNDING",
                    name="Founding Member — $20/month off forever",
                    amount_off=2000,   # $20.00 off in cents
                    currency="usd",
                    duration="forever",
                )
                print("✅ FOUNDING Stripe coupon created ($20/month off forever)")
    except Exception as _e:
        print(f"⚠️ Could not create FOUNDING Stripe coupon: {_e}")

    # Ensure WEEK2 Stripe coupon exists (20% off, once — for nurture email campaign)
    try:
        from api.payments import stripe, stripe_ready
        if stripe and stripe_ready:
            coupon_exists = False
            try:
                stripe.Coupon.retrieve("WEEK2")
                coupon_exists = True
                print("✅ WEEK2 Stripe coupon already exists")
            except Exception as _retrieve_err:
                print(f"ℹ️ WEEK2 coupon not found ({type(_retrieve_err).__name__}: {_retrieve_err}), creating...")
            if not coupon_exists:
                try:
                    stripe.Coupon.create(
                        id="WEEK2",
                        name="Week 2 — 20% off",
                        percent_off=20,
                        duration="once",
                    )
                    print("✅ WEEK2 Stripe coupon created (20% off, once)")
                except Exception as _create_err:
                    print(f"❌ WEEK2 Stripe coupon creation FAILED: {type(_create_err).__name__}: {_create_err}")
    except Exception as _e:
        print(f"⚠️ WEEK2 coupon startup check error: {_e}")

    # Start nurture email scheduler — runs every 6 hours
    _nurture_scheduler.add_job(_run_nurture_emails, "interval", hours=6, id="nurture_emails")
    # Keep-alive: ping /health every 10 min so Render free tier doesn't spin down
    _nurture_scheduler.add_job(_keep_alive_ping, "interval", minutes=10, id="keep_alive")
    _nurture_scheduler.start()
    print("⏰ Nurture email scheduler started (every 6 hours)")
    print("💓 Keep-alive ping scheduled (every 10 minutes)")


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











@app.get("/training/{entry_id}", response_class=HTMLResponse, include_in_schema=False)
async def training_detail_page(request: Request, entry_id: str, db: Session = Depends(get_database)):
    """Individual training script page — SEO-optimized, one per directory entry."""
    from models.directory import DirectoryEntry
    entry = db.query(DirectoryEntry).filter(DirectoryEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Training script not found")

    # Extract YouTube video ID for thumbnail
    video_id = None
    url = entry.source_url or entry.video_url or ""
    import re
    m = re.search(r'(?:v=|youtu\.be/)([^&\s?]+)', url)
    if m:
        video_id = m.group(1)

    # Parse bullets into list
    bullets = [b.lstrip("• \t").strip() for b in (entry.summary_5_bullets or "").splitlines() if b.strip()]
    tools = [t.strip() for t in (entry.tools_mentioned or "").split(";") if t.strip()]

    # Related entries: same category, exclude self, up to 4
    related_entries = (
        db.query(DirectoryEntry)
        .filter(
            DirectoryEntry.category_primary == entry.category_primary,
            DirectoryEntry.id != entry.id,
        )
        .order_by(DirectoryEntry.signal_score.desc())
        .limit(4)
        .all()
    )
    # Extract video IDs for related thumbnails
    related = []
    for r in related_entries:
        r_url = r.source_url or r.video_url or ""
        r_m = re.search(r'(?:v=|youtu\.be/)([^&\s?]+)', r_url)
        related.append({
            "id": r.id,
            "title": r.title,
            "creator_name": r.creator_name,
            "difficulty": r.difficulty,
            "signal_score": r.signal_score,
            "video_id": r_m.group(1) if r_m else None,
        })

    return templates.TemplateResponse(
        "training_detail.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "entry": entry,
            "video_id": video_id,
            "bullets": bullets,
            "tools": tools,
            "related": related,
        }
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

    base = "https://videomind-ai.com"
    entries = db.query(DirectoryEntry).filter(
        DirectoryEntry.processing_status.in_(["completed", "processed", "reviewed"])
    ).all()

    urls = [
        f"<url><loc>{base}/</loc><changefreq>weekly</changefreq><priority>1.0</priority></url>",
        f"<url><loc>{base}/pricing</loc><changefreq>monthly</changefreq><priority>0.9</priority></url>",
        f"<url><loc>{base}/directory</loc><changefreq>daily</changefreq><priority>0.9</priority></url>",
    ]
    for entry in entries:
        urls.append(
            f"<url><loc>{base}/training/{entry.id}</loc>"
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
        "User-agent: *\nAllow: /\nDisallow: /admin\nDisallow: /api/\n\nSitemap: https://videomind-ai.com/sitemap.xml\n"
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
