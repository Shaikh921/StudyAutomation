from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.database import get_db
from app.models.user import User
from app.services.dsa_service import DSAService
from app.services.job_service import JobApplicationService
from app.services.planner_service import PlannerService
from app.services.gemini_service import GeminiService

router = APIRouter(prefix="/progress", tags=["Progress & Analytics"])


@router.get("/daily")
def get_daily_report(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    dsa_stats = DSAService.get_progress(db, user.id)
    app_stats = JobApplicationService.get_application_stats(db, user.id)
    plan_summary = PlannerService.get_today_mission_summary(db, user)
    weak_topics = DSAService.get_weak_topics(db, user.id)

    return {
        "day_number": plan_summary["day_number"],
        "phase": plan_summary["phase"],
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "dsa": dsa_stats,
        "job_applications": app_stats,
        "weak_topics": [t["topic"] for t in weak_topics],
        "tomorrow_priorities": [
            f"Master {plan_summary['dsa']['topic']} core pattern",
            f"Complete 5 quality job applications",
            f"Review weak topic: {weak_topics[0]['topic'] if weak_topics else 'SQL Window Functions'}"
        ]
    }


@router.get("/weekly")
def get_weekly_report(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    dsa_stats = DSAService.get_progress(db, user.id)
    app_stats = JobApplicationService.get_application_stats(db, user.id)

    gemini = GeminiService()
    analysis = gemini.generate_daily_review({
        "dsa": dsa_stats,
        "applications": app_stats
    })

    return {
        "report_type": "Weekly 7-Day Performance Analysis",
        "dsa_stats": dsa_stats,
        "application_stats": app_stats,
        "ai_coach_advice": analysis
    }
