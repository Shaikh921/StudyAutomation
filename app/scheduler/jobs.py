import logging
from datetime import datetime, timezone
from app.database.database import SessionLocal
from app.models.user import User
from app.services.planner_service import PlannerService
from app.services.job_search_service import JobSearchService
from app.services.notification_service import NotificationService
from app.services.dsa_service import DSAService
from app.services.gemini_service import GeminiService

logger = logging.getLogger(__name__)


def job_generate_daily_plan():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            if getattr(user, "program_status", "NOT_STARTED") != "ACTIVE":
                logger.info(f"[Scheduled Job] Program status is '{getattr(user, 'program_status', 'NOT_STARTED')}'. Skipping daily plan generation for user {user.id}.")
                continue
            plan = PlannerService.generate_daily_plan(db, user)
            if plan:
                logger.info(f"[Scheduled Job] Generated daily plan for user {user.id}, Day {plan.day_number}")
    except Exception as e:
        logger.error(f"Error in job_generate_daily_plan: {e}")
    finally:
        db.close()


def job_send_job_digest():
    db = SessionLocal()
    try:
        notifier = NotificationService()
        job_service = JobSearchService()

        users = db.query(User).all()
        for user in users:
            if getattr(user, "program_status", "NOT_STARTED") != "ACTIVE":
                logger.info(f"[Scheduled Job] Program status is '{getattr(user, 'program_status', 'NOT_STARTED')}'. Skipping job digest for user {user.id}.")
                continue
            digest = job_service.generate_daily_digest(db, user)
            notifier.send_job_digest(db, user, digest)
    except Exception as e:
        logger.error(f"Error in job_send_job_digest: {e}")
    finally:
        db.close()


def job_send_morning_reminder():
    db = SessionLocal()
    try:
        notifier = NotificationService()
        users = db.query(User).all()
        for user in users:
            if getattr(user, "program_status", "NOT_STARTED") != "ACTIVE":
                logger.info(f"[Scheduled Job] Program status is '{getattr(user, 'program_status', 'NOT_STARTED')}'. Skipping morning reminder for user {user.id}.")
                continue
            summary = PlannerService.get_today_mission_summary(db, user)
            notifier.send_daily_plan(db, user, summary)
    except Exception as e:
        logger.error(f"Error in job_send_morning_reminder: {e}")
    finally:
        db.close()


def job_send_revision_reminder():
    db = SessionLocal()
    try:
        notifier = NotificationService()
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        users = db.query(User).all()
        for user in users:
            if getattr(user, "program_status", "NOT_STARTED") != "ACTIVE":
                continue
            due_count = DSAService.get_due_revisions_count(db, user.id)
            if due_count > 0:
                exec_key = f"revision_reminder_{user.id}_{today_str}"
                body = f"Quick 1-Hour Revision Reminder!\n\nYou have {due_count} DSA questions due for spaced-repetition revision today."
                notifier.send_notification(
                    db=db,
                    user=user,
                    message=body,
                    title="⏰ Quick Revision Reminder",
                    channels=["telegram", "email", "console"],
                    execution_key=exec_key
                )
    except Exception as e:
        logger.error(f"Error in job_send_revision_reminder: {e}")
    finally:
        db.close()


def job_send_dsa_session_reminder():
    db = SessionLocal()
    try:
        notifier = NotificationService()
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        users = db.query(User).all()
        for user in users:
            if getattr(user, "program_status", "NOT_STARTED") != "ACTIVE":
                continue
            exec_key = f"dsa_session_{user.id}_{today_str}"
            body = "Evening DSA Focus Time (18:00)! Open your dashboard or Telegram and solve today's recommended DSA pattern problems."
            notifier.send_notification(
                db=db,
                user=user,
                message=body,
                title="💻 18:00 DSA Deep-Dive Time",
                channels=["telegram", "email", "console"],
                execution_key=exec_key
            )
    except Exception as e:
        logger.error(f"Error in job_send_dsa_session_reminder: {e}")
    finally:
        db.close()


def job_send_daily_review():
    db = SessionLocal()
    try:
        notifier = NotificationService()
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        users = db.query(User).all()
        for user in users:
            if getattr(user, "program_status", "NOT_STARTED") != "ACTIVE":
                continue
            exec_key = f"daily_review_{user.id}_{today_str}"
            progress = DSAService.get_progress(db, user.id)
            
            body = (
                f"🌙 Nightly Progress Review — {today_str}\n\n"
                f"DSA Questions Solved: {progress['total_solved_correctly']}\n"
                f"Overall Accuracy: {progress['accuracy_percentage']}%\n"
                f"Due Revisions: {progress['due_for_revision']}\n\n"
                f"Great work today! Log your completed tasks to keep your 60-day streak active."
            )
            notifier.send_notification(
                db=db,
                user=user,
                message=body,
                title="📊 22:30 Daily Review & Progress Report",
                channels=["telegram", "email", "console"],
                execution_key=exec_key
            )
    except Exception as e:
        logger.error(f"Error in job_send_daily_review: {e}")
    finally:
        db.close()
