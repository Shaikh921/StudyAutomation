from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
import json

from app.database.database import get_db
from app.models.user import User
from app.services.planner_service import PlannerService
from app.services.roadmap_service import RoadmapService

router = APIRouter(prefix="/study", tags=["Study Planner"])


class TaskCompleteRequest(BaseModel):
    category: str


class SetStartDateRequest(BaseModel):
    start_date: str  # YYYY-MM-DD format


@router.get("/today")
def get_today_study_plan(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found. Please run seed script.")
    return PlannerService.get_today_mission_summary(db, user)


@router.get("/topic-detail")
def get_topic_detail(
    category: str = Query(..., description="Task category e.g. dsa, core, python, sql, ml, aptitude, interview"),
    topic: Optional[str] = Query("General", description="Topic name"),
    db: Session = Depends(get_db)
):
    return RoadmapService.get_topic_detail(category, topic or "General Topic")


@router.post("/set-start-date")
def set_program_start_date(data: SetStartDateRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found.")

    try:
        parsed_date = datetime.strptime(data.start_date, "%Y-%m-%d")
        user.program_start_date = parsed_date
        db.commit()
        db.refresh(user)

        # Regenerate daily plan with new start date calculation
        plan = PlannerService.generate_daily_plan(db, user, target_date=date.today())
        
        return {
            "status": "success",
            "message": f"Program start date updated to {data.start_date}",
            "current_day": plan.day_number,
            "phase": plan.phase,
            "today_plan": PlannerService.get_today_mission_summary(db, user)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")


@router.post("/generate-today")
def generate_today_plan(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found.")
    plan = PlannerService.generate_daily_plan(db, user)
    return {"status": "success", "plan_id": plan.id, "day_number": plan.day_number}


@router.post("/complete-task")
def mark_task_complete(data: TaskCompleteRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found.")
        
    summary = PlannerService.get_today_mission_summary(db, user)
    plan = PlannerService.generate_daily_plan(db, user)

    completed = json.loads(plan.completed_tasks or "[]")
    if data.category.lower() not in completed:
        completed.append(data.category.lower())
        plan.completed_tasks = json.dumps(completed)
        db.commit()

    return {"status": "task marked completed", "completed_tasks": completed}
