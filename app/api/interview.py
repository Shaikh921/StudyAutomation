from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.database import get_db
from app.models.user import User
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interview", tags=["Interview Mode"])


class StartInterviewRequest(BaseModel):
    category: str = "DBMS"


class SubmitAnswerRequest(BaseModel):
    session_id: int
    question_text: str
    category: str
    user_answer: str


@router.post("/start")
def start_interview(data: StartInterviewRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="No user found.")

    session = InterviewService.start_interview_session(db, user.id, data.category)
    first_q = InterviewService.get_next_question(data.category)

    return {
        "session_id": session.id,
        "category": data.category,
        "question": first_q
    }


@router.post("/evaluate")
def evaluate_interview_answer(data: SubmitAnswerRequest, db: Session = Depends(get_db)):
    return InterviewService.submit_and_evaluate_answer(
        db=db,
        session_id=data.session_id,
        question_text=data.question_text,
        category=data.category,
        user_answer=data.user_answer
    )
