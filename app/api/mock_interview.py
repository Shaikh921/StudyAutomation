from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from app.database.database import get_db
from app.models.user import User
from app.services.mock_interview_service import MockInterviewService

router = APIRouter(prefix="/interview/mock", tags=["Mock Interview Mode"])

interview_service = MockInterviewService()


class EvaluateRoundRequest(BaseModel):
    round_num: int
    question: str
    candidate_answer: str


class GenerateReportRequest(BaseModel):
    round_evaluations: List[Dict[str, Any]]


@router.get("/round/{round_num}")
def get_round_question(round_num: int, project_name: Optional[str] = "SentinelShield"):
    return interview_service.get_round_question(round_num, project_name or "SentinelShield")


@router.post("/evaluate-round")
def evaluate_round(data: EvaluateRoundRequest):
    return interview_service.evaluate_round_answer(
        round_num=data.round_num,
        question=data.question,
        candidate_answer=data.candidate_answer
    )


@router.post("/generate-report")
def generate_interview_report(data: GenerateReportRequest):
    return interview_service.generate_final_interview_report(data.round_evaluations)
