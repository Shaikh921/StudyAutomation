from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from app.database.database import get_db
from app.models.user import User
from app.models.study import StudyPlan, StudySession
from app.services.planner_service import PlannerService

router = APIRouter(prefix="/focus", tags=["Focus Mode & Study Timer"])


class StartFocusRequest(BaseModel):
    category: str  # DSA, Aptitude, Core, Python, SQL, ML, Interview, Project
    topic_name: str
    target_duration_minutes: int  # 25, 45, 60, 90


class CompleteFocusRequest(BaseModel):
    session_id: int
    actual_duration_minutes: int
    notes: Optional[str] = None
    completion_status: Optional[str] = "completed"  # completed, partially_completed, skipped


@router.post("/start")
def start_focus_session(data: StartFocusRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    plan = PlannerService.generate_daily_plan(db, user)

    session = StudySession(
        study_plan_id=plan.id,
        category=data.category,
        topic_name=data.topic_name,
        status="pending",
        started_at=datetime.now(timezone.utc),
        duration_minutes=data.target_duration_minutes
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "status": "session_started",
        "session_id": session.id,
        "category": session.category,
        "topic_name": session.topic_name,
        "target_duration_minutes": session.duration_minutes
    }


@router.post("/complete")
def complete_focus_session(data: CompleteFocusRequest, db: Session = Depends(get_db)):
    session = db.query(StudySession).filter(StudySession.id == data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Focus session not found.")

    session.completed_at = datetime.now(timezone.utc)
    session.duration_minutes = data.actual_duration_minutes
    session.status = data.completion_status.lower()
    if data.notes:
        session.notes = data.notes

    # Mark topic completed on daily plan if completed
    if data.completion_status.lower() == "completed":
        plan = session.study_plan
        import json
        completed_tasks = json.loads(plan.completed_tasks or "[]")
        if session.category.lower() not in completed_tasks:
            completed_tasks.append(session.category.lower())
            plan.completed_tasks = json.dumps(completed_tasks)

    db.commit()
    return {
        "status": "session_recorded",
        "session_id": session.id,
        "completion_status": session.status,
        "actual_duration_minutes": session.duration_minutes
    }
