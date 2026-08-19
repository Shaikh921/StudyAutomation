from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database.database import get_db
from app.models.user import User
from app.models.job import JobApplication
from app.services.job_service import JobApplicationService

router = APIRouter(prefix="/applications", tags=["Application Tracker"])


class UpdateStatusRequest(BaseModel):
    status: str  # saved, applied, assessment, interview, rejected, selected, offer, withdrawn
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None


@router.get("")
def get_user_applications(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return db.query(JobApplication).filter(JobApplication.user_id == user.id).all()


@router.get("/stats")
def get_application_stats(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return JobApplicationService.get_application_stats(db, user.id)


@router.patch("/{application_id}")
def update_application_status(application_id: int, data: UpdateStatusRequest, db: Session = Depends(get_db)):
    try:
        return JobApplicationService.update_application_status(
            db=db,
            application_id=application_id,
            status=data.status,
            notes=data.notes,
            interview_date=data.interview_date
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
