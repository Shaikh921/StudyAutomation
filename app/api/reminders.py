from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone
import json

from app.database.database import get_db
from app.models.user import User
from app.models.reminder import StudyReminder

router = APIRouter(prefix="/reminders", tags=["Reminder Management"])


class CreateReminderRequest(BaseModel):
    topic: str
    remind_at: str  # ISO format string
    repeat_type: Optional[str] = "none"
    channel: Optional[str] = "console"


class RescheduleReminderRequest(BaseModel):
    new_remind_at: str  # ISO format string


@router.get("")
def list_reminders(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    reminders = db.query(StudyReminder).filter(StudyReminder.user_id == user.id).order_by(StudyReminder.remind_at.asc()).all()
    return [
        {
            "id": r.id,
            "topic": r.topic,
            "remind_at": r.remind_at.isoformat(),
            "repeat_type": r.repeat_type,
            "channel": r.channel,
            "status": r.status,
            "skip_count": r.skip_count,
            "is_paused": r.is_paused,
            "action_triggers": json.loads(r.action_triggers or "[]")
        }
        for r in reminders
    ]


@router.post("")
def create_reminder(data: CreateReminderRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    try:
        rem_dt = datetime.fromisoformat(data.remind_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format.")

    reminder = StudyReminder(
        user_id=user.id,
        topic=data.topic,
        remind_at=rem_dt,
        repeat_type=data.repeat_type or "none",
        channel=data.channel or "console",
        status="pending",
        action_triggers=json.dumps(["[START TASK]", "[OPEN TODAY'S PLAN]", "[ASK GEMINI]", "[MARK COMPLETE]", "[SKIP]", "[RESCHEDULE]"])
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return {"status": "created", "reminder_id": reminder.id}


@router.post("/{reminder_id}/pause")
def pause_reminder(reminder_id: int, db: Session = Depends(get_db)):
    r = db.query(StudyReminder).filter(StudyReminder.id == reminder_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    r.is_paused = True
    r.status = "paused"
    db.commit()
    return {"status": "paused", "reminder_id": r.id}


@router.post("/{reminder_id}/resume")
def resume_reminder(reminder_id: int, db: Session = Depends(get_db)):
    r = db.query(StudyReminder).filter(StudyReminder.id == reminder_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    r.is_paused = False
    r.status = "pending"
    db.commit()
    return {"status": "resumed", "reminder_id": r.id}


@router.post("/{reminder_id}/reschedule")
def reschedule_reminder(reminder_id: int, data: RescheduleReminderRequest, db: Session = Depends(get_db)):
    r = db.query(StudyReminder).filter(StudyReminder.id == reminder_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    try:
        new_dt = datetime.fromisoformat(data.new_remind_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ISO datetime format.")

    r.remind_at = new_dt
    r.status = "pending"
    r.skip_count += 1
    if r.skip_count >= 3:
        r.status = "needs_attention"
    db.commit()
    return {"status": "rescheduled", "new_remind_at": new_dt.isoformat(), "skip_count": r.skip_count}


@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    r = db.query(StudyReminder).filter(StudyReminder.id == reminder_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Reminder not found.")
    db.delete(r)
    db.commit()
    return {"status": "deleted", "reminder_id": reminder_id}
