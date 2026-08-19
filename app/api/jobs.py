from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database.database import get_db
from app.models.user import User
from app.models.job import JobListing, DailyDigest
from app.services.job_search_service import JobSearchService
from app.services.job_service import JobApplicationService

router = APIRouter(prefix="/jobs", tags=["Job Engine & Search"])


class SaveJobRequest(BaseModel):
    notes: Optional[str] = None


@router.get("")
def get_job_listings(db: Session = Depends(get_db)):
    return db.query(JobListing).order_by(JobListing.relevance_score.desc()).all()


@router.get("/digest")
def get_daily_job_digest(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    job_service = JobSearchService()
    digest = job_service.generate_daily_digest(db, user)
    return digest


@router.post("/{job_id}/save")
def save_job(job_id: int, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return JobApplicationService.save_job(db, user.id, job_id)


@router.post("/{job_id}/apply")
def apply_job(job_id: int, data: Optional[SaveJobRequest] = None, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    notes = data.notes if data else None
    return JobApplicationService.apply_job(db, user.id, job_id, notes=notes)
