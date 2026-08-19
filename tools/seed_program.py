import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import SessionLocal
from app.database.migrations import init_db
from app.models.user import User
from app.models.job import JobPreference
from app.services.planner_service import PlannerService
from app.services.job_search_service import JobSearchService


def seed_program():
    init_db()
    db = SessionLocal()

    try:
        print("Seeding initial 60-Day Program data...")
        
        # Check if default user exists
        user = db.query(User).filter(User.email == "cse_student@example.com").first()
        if not user:
            user = User(
                name="CSE Student",
                email="cse_student@example.com",
                timezone="Asia/Kolkata",
                program_status="NOT_STARTED",
                daily_study_hours=6,
                target_roles="ML Engineer,Python Developer,Software Engineer,Backend Developer",
                preferred_locations="India,Remote,Pune,Bengaluru,Hyderabad",
                notification_channels="console,email,telegram"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Created default User ID: {user.id} ({user.email})")

        # Create Job Preference
        pref = db.query(JobPreference).filter(JobPreference.user_id == user.id).first()
        if not pref:
            pref = JobPreference(
                user_id=user.id,
                target_roles=user.target_roles,
                locations=user.preferred_locations,
                remote_preferred=True,
                min_experience_years=0,
                max_experience_years=2
            )
            db.add(pref)

        # Ingest initial fresh jobs
        job_service = JobSearchService()
        jobs = job_service.discover_and_ingest_jobs(db, user)
        print(f"Ingested {len(jobs)} initial job listings.")

        db.commit()
        print("Seeding completed successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_program()
