import logging
from app.config import settings

logger = logging.getLogger(__name__)

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger.warning("APScheduler is not installed. Background scheduler running in manual trigger mode.")

from app.scheduler.jobs import (
    job_generate_daily_plan,
    job_send_job_digest,
    job_send_morning_reminder,
    job_send_revision_reminder,
    job_send_dsa_session_reminder,
    job_send_daily_review
)

if APSCHEDULER_AVAILABLE:
    scheduler = BackgroundScheduler(timezone=settings.TIMEZONE)
else:
    class DummyScheduler:
        running = False
        def add_job(self, *args, **kwargs): pass
        def start(self): self.running = True
        def shutdown(self): self.running = False
    scheduler = DummyScheduler()


def init_scheduler():
    if not APSCHEDULER_AVAILABLE:
        logger.info("APScheduler not available in environment. Manual API triggers enabled.")
        return

    if scheduler.running:
        logger.info("Scheduler is already running.")
        return

    # 06:30 Generate Daily Plan
    scheduler.add_job(job_generate_daily_plan, CronTrigger(hour=6, minute=30), id="generate_daily_plan", replace_existing=True)

    # 07:00 Send Morning Job Digest
    scheduler.add_job(job_send_job_digest, CronTrigger(hour=7, minute=0), id="send_job_digest", replace_existing=True)

    # 08:00 Morning Study Reminder
    scheduler.add_job(job_send_morning_reminder, CronTrigger(hour=8, minute=0), id="morning_reminder", replace_existing=True)

    # 13:00 Revision Reminder
    scheduler.add_job(job_send_revision_reminder, CronTrigger(hour=13, minute=0), id="revision_reminder", replace_existing=True)

    # 18:00 DSA Session
    scheduler.add_job(job_send_dsa_session_reminder, CronTrigger(hour=18, minute=0), id="dsa_session", replace_existing=True)

    # 22:30 Daily Review
    scheduler.add_job(job_send_daily_review, CronTrigger(hour=22, minute=30), id="daily_review", replace_existing=True)

    scheduler.start()
    logger.info("APScheduler successfully initialized and started with Asia/Kolkata timezone.")


def stop_scheduler():
    if APSCHEDULER_AVAILABLE and scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped.")
