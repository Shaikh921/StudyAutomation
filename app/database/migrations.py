from sqlalchemy import text
from app.database.database import Base, engine

# Import all models so SQLAlchemy registers them with Base.metadata
from app.models.user import User
from app.models.reminder import StudyReminder
from app.models.dsa import DSAQuestion, DSAAttempt, DSARevisionSchedule
from app.models.study import StudyPlan, StudySession, StudyTopic
from app.models.interview import InterviewSession, InterviewQuestion, InterviewAnswer
from app.models.job import JobListing, JobApplication, JobPreference, DailyDigest
from app.models.notification import NotificationLog


def safe_add_column(conn, table_name: str, column_def: str):
    try:
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_def}"))
        conn.commit()
    except Exception:
        pass


def init_db():
    Base.metadata.create_all(bind=engine)
    
    # Safe individual SQLite column migrations
    with engine.connect() as conn:
        # User columns
        safe_add_column(conn, "users", "program_status VARCHAR DEFAULT 'NOT_STARTED'")
        safe_add_column(conn, "users", "program_started_at DATETIME")
        safe_add_column(conn, "users", "program_end_date DATETIME")
        safe_add_column(conn, "users", "paused_at DATETIME")
        safe_add_column(conn, "users", "completed_at DATETIME")
        safe_add_column(conn, "users", "daily_study_hours INTEGER DEFAULT 6")
        safe_add_column(conn, "users", "target_roles VARCHAR DEFAULT 'Software Developer'")
        safe_add_column(conn, "users", "preferred_locations VARCHAR DEFAULT 'India, Remote'")
        safe_add_column(conn, "users", "notification_channels VARCHAR DEFAULT 'console,email,telegram'")
        safe_add_column(conn, "users", "timezone VARCHAR DEFAULT 'Asia/Kolkata'")
        safe_add_column(conn, "users", "quiet_hours_start VARCHAR DEFAULT '23:00'")
        safe_add_column(conn, "users", "quiet_hours_end VARCHAR DEFAULT '06:00'")
        safe_add_column(conn, "users", "custom_reminder_schedule TEXT DEFAULT '{}'")
        safe_add_column(conn, "users", "created_at DATETIME")
        safe_add_column(conn, "users", "updated_at DATETIME")

        # DSAQuestion columns
        safe_add_column(conn, "dsa_questions", "fingerprint VARCHAR(64)")

        # JobListing columns
        safe_add_column(conn, "job_listings", "fingerprint VARCHAR(100)")
        safe_add_column(conn, "job_listings", "status VARCHAR(50) DEFAULT 'active'")

        # JobApplication columns
        safe_add_column(conn, "job_applications", "prep_pack TEXT")

        # StudyReminder columns
        safe_add_column(conn, "study_reminders", "skip_count INTEGER DEFAULT 0")
        safe_add_column(conn, "study_reminders", "is_paused BOOLEAN DEFAULT 0")
        safe_add_column(conn, "study_reminders", "action_triggers TEXT")