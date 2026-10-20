from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.api.v1.auth.change_password import (
    router as change_password_router,
)
from backend.app.api.v1.auth.forgot_password import (
    router as forgot_password_router,
)
from backend.app.api.v1.auth.google_oauth import router as google_oauth_router
from backend.app.api.v1.auth.login import router as login_router
from backend.app.api.v1.auth.logout import router as logout_router
from backend.app.api.v1.auth.me import router as me_router
from backend.app.api.v1.auth.register import router as register_router
from backend.app.api.v1.auth.resend_otp import router as resend_otp_router
from backend.app.api.v1.auth.reset_password import (
    router as reset_password_router,
)
from backend.app.api.v1.auth.verify_otp import router as verify_otp_router
from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.analyses import router as analyses_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.assistant import router as assistant_router
from backend.app.api.v1.reports import router as reports_router
from backend.app.api.v1.benchmarks import router as benchmarks_router
from backend.app.api.v1.admin import router as admin_router
from backend.app.core.config import settings
from backend.app.db.database import get_db


app = FastAPI(
    title="CFAP API",
    description="Cognitive Feedback Analytics Platform API",
    version="1.0.0",
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Routers ----
for _router in [
    register_router,
    verify_otp_router,
    resend_otp_router,
    login_router,
    me_router,
    logout_router,
    forgot_password_router,
    reset_password_router,
    google_oauth_router,
    change_password_router,
    datasets_router,
    analyses_router,
    analytics_router,
    assistant_router,
    reports_router,
    benchmarks_router,
    admin_router,
]:
    app.include_router(_router, prefix="/api/v1")




@app.get("/")
def root():
    return {
        "message": "CFAP API is running",
        "status": "healthy",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "CFAP Backend",
    }


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception:
        return {
            "status": "unhealthy",
            "error": "database_connection_failed",
        }