from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import os

from app.config import settings
from app.database.database import get_db
from app.models.user import User
from app.models.dsa import DSAQuestion
from app.scheduler.jobs import (
    job_generate_daily_plan,
    job_send_job_digest,
    job_send_morning_reminder,
    job_send_revision_reminder
)
from app.scheduler.scheduler import scheduler
from app.services.gemini_service import GeminiService

router = APIRouter(tags=["System & Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    # 1. Database Check
    try:
        db.query(User).first()
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    # 2. Scheduler Check
    scheduler_status = "healthy" if (scheduler and scheduler.running) else "running_manual_mode"

    # 3. Gemini Check
    gemini = GeminiService()
    gemini_status = "configured" if gemini.is_available() else "fallback_mode"

    # 4. Telegram Check
    telegram_status = "configured" if (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID) else "unavailable"

    # 5. Email Check
    email_status = "configured" if (settings.EMAIL_SENDER and settings.EMAIL_APP_PASSWORD) else "console_fallback"

    overall_status = "healthy" if db_status == "healthy" else "degraded"

    return {
        "status": overall_status,
        "database": db_status,
        "scheduler": scheduler_status,
        "gemini": gemini_status,
        "telegram": telegram_status,
        "email": email_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "60-Day CSE Job Preparation Automation Platform"
    }


@router.get("/system/status")
def system_status(db: Session = Depends(get_db)):
    user = db.query(User).first()
    dsa_count = db.query(DSAQuestion).count()
    scheduler_running = scheduler.running if scheduler else False

    return {
        "status": "operational",
        "user_registered": user is not None,
        "user_email": user.email if user else None,
        "dsa_questions_loaded": dsa_count,
        "scheduler_running": scheduler_running,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.post("/scheduler/test")
def test_scheduler_trigger():
    job_generate_daily_plan()
    return {"status": "success", "message": "Daily plan generation job executed successfully."}


@router.post("/digest/test")
def test_digest_trigger():
    job_send_job_digest()
    return {"status": "success", "message": "Job digest generation and notification job executed."}
