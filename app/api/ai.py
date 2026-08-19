from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.database import get_db
from app.models.user import User
from app.services.gemini_service import GeminiService
from app.services.planner_service import PlannerService

router = APIRouter(prefix="/ai", tags=["Gemini AI Tutor"])


class ChatRequest(BaseModel):
    message: str
    context: Optional[str] = None


class ModifyPlanRequest(BaseModel):
    user_prompt: str


class ProjectPrepRequest(BaseModel):
    project_name: str
    description: Optional[str] = None


@router.post("/chat")
@router.post("/ask")
def chat_with_tutor(data: ChatRequest):
    gemini = GeminiService()
    return gemini.chat_with_tutor(data.message, data.context)


@router.post("/modify-plan")
def modify_plan_with_ai(data: ModifyPlanRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    current_summary = PlannerService.get_today_mission_summary(db, user)
    plan = PlannerService.generate_daily_plan(db, user)

    gemini = GeminiService()
    updates = gemini.adapt_study_plan(current_summary, data.user_prompt)

    if "objectives" in updates and updates["objectives"]:
        plan.objectives = str(updates["objectives"])
    if "dsa_topic" in updates and updates["dsa_topic"]:
        plan.dsa_topic = str(updates["dsa_topic"])
    if "python_topic" in updates and updates["python_topic"]:
        plan.python_topic = str(updates["python_topic"])
    if "sql_topic" in updates and updates["sql_topic"]:
        plan.sql_topic = str(updates["sql_topic"])
    if "ml_topic" in updates and updates["ml_topic"]:
        plan.ml_topic = str(updates["ml_topic"])
    if "estimated_total_time" in updates and updates["estimated_total_time"]:
        try:
            plan.estimated_total_time = float(updates["estimated_total_time"])
        except ValueError:
            pass

    db.commit()
    db.refresh(plan)

    return {
        "status": "success",
        "message": "Study plan successfully modified by Gemini AI!",
        "updated_plan": PlannerService.get_today_mission_summary(db, user)
    }


@router.post("/project-prep")
def generate_project_questions(data: ProjectPrepRequest):
    gemini = GeminiService()
    return gemini.generate_project_interview_questions(data.project_name, data.description)
