from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.database.database import get_db
from app.models.user import User
from app.services.roadmap_service import RoadmapService
from app.services.planner_service import PlannerService
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/program", tags=["Program Management"])


class RestartProgramRequest(BaseModel):
    confirm_restart: bool = False


@router.get("/status")
def get_program_status(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not initialized.")

    day_calc = RoadmapService.calculate_current_day(user=user)
    start_str = user.program_start_date.strftime("%Y-%m-%d") if user.program_start_date else None
    end_str = user.program_end_date.strftime("%Y-%m-%d") if user.program_end_date else None

    return {
        "status": getattr(user, "program_status", "NOT_STARTED") or "NOT_STARTED",
        "is_started": day_calc["is_started"],
        "current_day": day_calc["current_day"],
        "total_days": 60,
        "start_date": start_str,
        "end_date": end_str,
        "days_completed": day_calc["days_completed"],
        "days_remaining": day_calc["days_remaining"],
        "progress_percent": day_calc["completion_percentage"],
        "phase_name": day_calc["phase_name"],
        "mode_name": day_calc["mode_name"]
    }


@router.post("/start")
def start_program(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found. Run seed script first.")

    current_status = getattr(user, "program_status", "NOT_STARTED") or "NOT_STARTED"
    if current_status == "ACTIVE":
        day_calc = RoadmapService.calculate_current_day(user=user)
        start_str = user.program_start_date.strftime("%Y-%m-%d") if user.program_start_date else "Today"
        return {
            "status": "already_active",
            "message": f"Your 60-Day Program is already active (Day {day_calc['current_day']} / 60). Started on {start_str}.",
            "current_day": day_calc["current_day"]
        }

    today_kolkata = RoadmapService.get_today_kolkata()
    start_dt = datetime.combine(today_kolkata, datetime.min.time())
    end_dt = start_dt + timedelta(days=59)

    user.program_status = "ACTIVE"
    user.program_start_date = start_dt
    user.program_started_at = datetime.now(timezone.utc)
    user.program_end_date = end_dt
    user.paused_at = None
    user.completed_at = None

    db.commit()
    db.refresh(user)

    # Generate Day 1 plan
    plan = PlannerService.generate_daily_plan(db, user, target_date=today_kolkata)
    summary = PlannerService.get_today_mission_summary(db, user)

    # Send Welcome Notification
    notif_service = NotificationService()
    welcome_text = (
        f"🚀 <b>60-DAY CSE CAREER COACH OFFICIALLY STARTED!</b>\n\n"
        f"Today is: <b>DAY 1 / 60</b>\n"
        f"Your 60-day preparation program officially begins today ({today_kolkata.strftime('%d %b %Y')})!\n\n"
        f"<b>Day 1 Objectives:</b>\n{summary['objectives']}\n\n"
        f"🧠 DSA: {summary['dsa']['topic']}\n"
        f"📐 Aptitude: {summary['aptitude']['topic']}\n"
        f"⚙️ Core CSE: {summary['core']['subject']}\n"
        f"🐍 Python: {summary['python']['topic']}\n"
        f"🗄️ SQL: {summary['sql']['topic']}\n"
        f"🤖 ML: {summary['ml']['topic']}\n"
    )
    notif_service.send_notification(
        db=db,
        user=user,
        message=welcome_text,
        title="🚀 DAY 1 / 60 — PROGRAM STARTED",
        channels=["telegram", "email", "console"],
        execution_key=f"program_started:{user.id}:{today_kolkata.isoformat()}"
    )

    return {
        "status": "active",
        "message": f"60-Day Program successfully started! Day 1 initialized for {today_kolkata.strftime('%Y-%m-%d')}.",
        "start_date": start_dt.strftime("%Y-%m-%d"),
        "end_date": end_dt.strftime("%Y-%m-%d"),
        "current_day": 1
    }


@router.post("/pause")
def pause_program(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found.")

    if user.program_status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Program is not currently active.")

    user.program_status = "PAUSED"
    user.paused_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "paused", "message": "Program notifications paused. Program calendar continues based on start date."}


@router.post("/resume")
def resume_program(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found.")

    if user.program_status != "PAUSED":
        raise HTTPException(status_code=400, detail="Program is not currently paused.")

    user.program_status = "ACTIVE"
    user.paused_at = None
    db.commit()
    return {"status": "resumed", "message": "Program notifications resumed!"}


@router.post("/restart")
def restart_program(req: RestartProgramRequest, db: Session = Depends(get_db)):
    if not req.confirm_restart:
        raise HTTPException(
            status_code=400,
            detail="To restart your 60-Day Program, you must pass {'confirm_restart': true}. Warning: This will reset Day 1 to today!"
        )

    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User profile not found.")

    today_kolkata = RoadmapService.get_today_kolkata()
    start_dt = datetime.combine(today_kolkata, datetime.min.time())
    end_dt = start_dt + timedelta(days=59)

    user.program_status = "ACTIVE"
    user.program_start_date = start_dt
    user.program_started_at = datetime.now(timezone.utc)
    user.program_end_date = end_dt
    user.paused_at = None
    user.completed_at = None

    db.commit()
    db.refresh(user)

    PlannerService.generate_daily_plan(db, user, target_date=today_kolkata)
    return {
        "status": "restarted",
        "message": f"Program restarted! Day 1 now set to today ({today_kolkata.strftime('%Y-%m-%d')}).",
        "current_day": 1
    }
