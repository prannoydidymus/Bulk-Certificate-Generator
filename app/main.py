from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import APP_TITLE, APP_DESCRIPTION, APP_VERSION
from app.database import Base, engine
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for flexible integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", tags=["Health & Info"])
def root_info():
    """Root info endpoint providing service health and links to API docs."""
    return {
        "service": APP_TITLE,
        "version": APP_VERSION,
        "status": "healthy",
        "documentation": "/docs",
        "endpoints": {
            "create_job": "POST /api/v1/jobs",
            "get_job": "GET /api/v1/jobs/{job_id}",
            "list_jobs": "GET /api/v1/jobs",
            "get_certificate": "GET /api/v1/certificates/{certificate_id}",
            "download_certificate": "GET /api/v1/certificates/{certificate_id}/download",
            "download_all_certificates": "GET /api/v1/jobs/{job_id}/download-all",
        },
    }


@app.get("/health", tags=["Health & Info"])
def health_check():
    """Health check endpoint for container orchestrators and monitoring."""
    return {"status": "ok"}
