import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.seed_data import seed_database
from app import models
from app.routers import (
    auth_router,
    attendance_router,
    payslips_router,
    reports_router,
    feedback_router,
    skills_router,
    fatigue_router,
    analytics_router,
    ai_router
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is created
    Base.metadata.create_all(bind=engine)
    # Check if database has organizations; if not, seed realistic data
    db = SessionLocal()
    try:
        org_count = db.query(models.Organization).count()
        if org_count == 0:
            seed_database(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FairShift AI — Empowering workers with transparency and voice while delivering proactive workforce health insights for SDG 8: Decent Work & Economic Growth.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router.router, prefix=settings.API_V1_STR)
app.include_router(attendance_router.router, prefix=settings.API_V1_STR)
app.include_router(payslips_router.router, prefix=settings.API_V1_STR)
app.include_router(reports_router.router, prefix=settings.API_V1_STR)
app.include_router(feedback_router.router, prefix=settings.API_V1_STR)
app.include_router(skills_router.router, prefix=settings.API_V1_STR)
app.include_router(fatigue_router.router, prefix=settings.API_V1_STR)
app.include_router(analytics_router.router, prefix=settings.API_V1_STR)
app.include_router(ai_router.router, prefix=settings.API_V1_STR)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "FairShift AI Backend",
        "sdg_target": "SDG 8: Decent Work and Economic Growth",
        "version": "1.0.0"
    }

# Mount static frontend build if present (for single container Cloud Run deployment)
frontend_dist_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.isdir(frontend_dist_path):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist_path, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(frontend_dist_path, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist_path, "index.html"))
else:
    @app.get("/")
    def root():
        return {
            "message": "Welcome to FairShift AI API",
            "docs_url": "/docs",
            "health_check": "/health",
            "version": "1.0.0"
        }
