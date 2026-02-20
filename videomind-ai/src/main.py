"""
VideoMind AI - Main FastAPI Application
Turn any video into AI training data.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from config import settings
from database import create_tables
from api import health, process, directory

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Turn any video into AI training data",
    version=settings.app_version,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://videomind.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include API routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(process.router, prefix="/api", tags=["Processing"])
app.include_router(directory.router, prefix="/api", tags=["Directory"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    create_tables()
    print(f"🚀 {settings.app_name} v{settings.app_version} starting up!")
    print(f"🔧 Debug mode: {settings.debug}")
    print(f"💾 Database: {settings.database_url}")


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


@app.get("/directory", response_class=HTMLResponse, include_in_schema=False)
async def directory_page(request: Request):
    """Serve the AI training directory page."""
    return templates.TemplateResponse(
        "directory.html",
        {"request": request, "app_name": settings.app_name}
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