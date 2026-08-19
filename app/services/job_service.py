from datetime import datetime, date, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import json

from app.models.job import JobListing, JobApplication
from app.models.reminder import StudyReminder


class JobApplicationService:
    @staticmethod
    def generate_prep_pack(job: JobListing) -> Dict[str, Any]:
        """
        Generates a custom Job Preparation Pack based on listing title & skills.
        """
        skills_str = (job.skills or "").lower()
        title_str = (job.title or "").lower()
        
        pack = {
            "company": job.company,
            "role": job.title,
            "priority": "HIGH" if job.relevance_score >= 80 else "MEDIUM",
            "questions": {
                "python": [
                    f"Explain key Python features required for {job.title}.",
                    "How do decorators and generators work under the hood?"
                ],
                "sql": [
                    "Write a query to find department top earners using DENSE_RANK().",
                    "Explain index performance trade-offs."
                ],
                "dsa": [
                    "Solve 2 pointer / sliding window problem for array processing.",
                    "Optimize time complexity from O(N^2) to O(N)."
                ],
                "rest_api": [
                    "Explain REST API error codes (200, 201, 400, 401, 404, 500).",
                    "How do you secure API endpoints?"
                ],
                "hr": [
                    f"Why do you want to join {job.company} as a {job.title}?",
                    "Walk me through your background and key portfolio project."
                ]
            }
        }
        
        if "machine learning" in title_str or "ml" in skills_str:
            pack["questions"]["ml"] = [
                "Explain the Bias-Variance tradeoff and L1 vs L2 regularization.",
                "How do you evaluate an imbalanced dataset?"
            ]
            
        return pack

    @staticmethod
    def save_job(db: Session, user_id: int, job_id: int) -> JobApplication:
        existing = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.job_id == job_id
        ).first()

        if existing:
            return existing

        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        prep_pack_json = json.dumps(JobApplicationService.generate_prep_pack(job)) if job else "{}"

        app = JobApplication(
            user_id=user_id,
            job_id=job_id,
            status="saved",
            prep_pack=prep_pack_json
        )
        db.add(app)
        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def apply_job(db: Session, user_id: int, job_id: int, notes: Optional[str] = None) -> JobApplication:
        app = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.job_id == job_id
        ).first()

        now = datetime.now(timezone.utc)
        if not app:
            job = db.query(JobListing).filter(JobListing.id == job_id).first()
            prep_pack_json = json.dumps(JobApplicationService.generate_prep_pack(job)) if job else "{}"
            app = JobApplication(
                user_id=user_id,
                job_id=job_id,
                status="applied",
                applied_at=now,
                notes=notes,
                prep_pack=prep_pack_json
            )
            db.add(app)
        else:
            app.status = "applied"
            app.applied_at = now
            if notes:
                app.notes = notes

        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def update_application_status(
        db: Session,
        application_id: int,
        status: str,
        notes: Optional[str] = None,
        interview_date: Optional[datetime] = None
    ) -> JobApplication:
        app = db.query(JobApplication).filter(JobApplication.id == application_id).first()
        if not app:
            raise ValueError(f"Application with ID {application_id} not found")

        app.status = status.lower()
        if notes:
            app.notes = notes
        if interview_date:
            app.interview_date = interview_date
            # Auto-schedule D-7, D-3, D-1 prep reminders
            JobApplicationService._schedule_interview_reminders(db, app)

        db.commit()
        db.refresh(app)
        return app

    @staticmethod
    def _schedule_interview_reminders(db: Session, app: JobApplication):
        if not app.interview_date:
            return

        company = app.job.company if app.job else "Target Company"
        int_dt = app.interview_date

        reminders_to_create = [
            {"days": 7, "label": f"D-7 INTERVIEW PREP: Deep dive for {company}"},
            {"days": 3, "label": f"D-3 MOCK INTERVIEW: Complete full technical mock for {company}"},
            {"days": 1, "label": f"D-1 REVISION: Review weak topics & {company} prep pack"},
            {"days": 0, "label": f"🚨 INTERVIEW DAY: Checklist & final review for {company}"}
        ]

        for r in reminders_to_create:
            rem_time = int_dt - timedelta(days=r["days"])
            # Avoid scheduling during quiet hours (e.g. set to 08:00 AM)
            rem_time = rem_time.replace(hour=8, minute=0, second=0, microsecond=0)
            if rem_time >= datetime.now(timezone.utc):
                rem_obj = StudyReminder(
                    user_id=app.user_id,
                    topic=r["label"],
                    remind_at=rem_time,
                    repeat_type="none",
                    channel="console",
                    status="pending",
                    action_triggers=json.dumps(["[START PREP]", "[ASK GEMINI]", "[MARK COMPLETE]"])
                )
                db.add(rem_obj)

    @staticmethod
    def get_application_stats(db: Session, user_id: int) -> Dict[str, Any]:
        total_discovered = db.query(JobListing).count()
        total_saved = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.status == "saved"
        ).count()
        total_applied = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.status == "applied"
        ).count()
        total_interviews = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.status.in_(["assessment", "interview"])
        ).count()
        total_offers = db.query(JobApplication).filter(
            JobApplication.user_id == user_id,
            JobApplication.status == "offer"
        ).count()

        return {
            "daily_target": 5,
            "total_jobs_discovered": total_discovered,
            "jobs_saved": total_saved,
            "jobs_applied": total_applied,
            "interviews": total_interviews,
            "offers": total_offers,
            "target_met": total_applied >= 5
        }
