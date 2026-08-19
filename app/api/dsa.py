from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import json

from app.database.database import get_db
from app.models.user import User
from app.models.dsa import DSAQuestion
from app.services.dsa_service import DSAService
from app.services.gemini_service import GeminiService
from app.services.planner_service import PlannerService

router = APIRouter(prefix="/dsa", tags=["DSA Question Bank & Revision"])


class AttemptRequest(BaseModel):
    result: str  # correct, incorrect, partial, skipped
    answer_text: Optional[str] = None
    time_taken_seconds: Optional[int] = None
    confidence: Optional[int] = None
    notes: Optional[str] = None


class EvaluateRequest(BaseModel):
    answer_text: str


@router.get("/today")
def get_today_dsa_questions(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found.")

    plan = PlannerService.generate_daily_plan(db, user)
    q_ids = json.loads(plan.dsa_question_ids or "[]")
    questions = db.query(DSAQuestion).filter(DSAQuestion.id.in_(q_ids)).all() if q_ids else []

    return {
        "topic": plan.dsa_topic,
        "count": len(questions),
        "questions": [
            {
                "id": q.id,
                "title": q.question_text,
                "difficulty": q.difficulty,
                "topic": q.topic,
                "pattern": q.pattern
            } for q in questions
        ]
    }


@router.get("/progress")
def get_dsa_progress(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found.")
    return DSAService.get_progress(db, user.id)


@router.get("/weak-topics")
def get_weak_topics(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found.")
    return DSAService.get_weak_topics(db, user.id)


@router.post("/{question_id}/attempt")
def record_dsa_attempt(question_id: int, data: AttemptRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found.")
    
    question = db.query(DSAQuestion).filter(DSAQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="DSA Question not found")

    return DSAService.record_attempt(
        db=db,
        user_id=user.id,
        question_id=question_id,
        result=data.result,
        answer_text=data.answer_text,
        time_taken_seconds=data.time_taken_seconds,
        confidence=data.confidence,
        notes=data.notes
    )


@router.post("/{question_id}/hint")
def get_dsa_hint(question_id: int, level: int = 1, db: Session = Depends(get_db)):
    question = db.query(DSAQuestion).filter(DSAQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="DSA Question not found")

    gemini = GeminiService()
    hint = gemini.generate_hint(question.question_text, hint_level=level)
    return {"question_id": question_id, "hint_level": level, "hint": hint}


@router.post("/{question_id}/evaluate")
def evaluate_dsa_solution(question_id: int, data: EvaluateRequest, db: Session = Depends(get_db)):
    question = db.query(DSAQuestion).filter(DSAQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="DSA Question not found")

    gemini = GeminiService()
    evaluation = gemini.evaluate_dsa_answer(question.question_text, data.answer_text)
    return evaluation
