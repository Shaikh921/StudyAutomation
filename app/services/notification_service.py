import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.config import settings
from app.notifications.console import ConsoleNotifier
from app.notifications.telegram import TelegramNotifier
from app.notifications.email import EmailNotifier
from app.models.notification import NotificationLog
from app.models.user import User

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Central Notification Routing Service supporting Telegram, Email, and Console providers.
    Does NOT require Twilio or WhatsApp.
    """

    def __init__(self):
        self.providers = {
            "console": ConsoleNotifier(),
            "telegram": TelegramNotifier(),
            "email": EmailNotifier()
        }

    @staticmethod
    def is_quiet_hours(user: User, dt: Optional[datetime] = None) -> bool:
        if not dt:
            dt = datetime.now(timezone.utc)
        
        q_start = getattr(user, "quiet_hours_start", "23:00") or "23:00"
        q_end = getattr(user, "quiet_hours_end", "06:00") or "06:00"

        try:
            sh, sm = map(int, q_start.split(":"))
            eh, em = map(int, q_end.split(":"))
            curr_h, curr_m = dt.hour, dt.minute

            curr_mins = curr_h * 60 + curr_m
            start_mins = sh * 60 + sm
            end_mins = eh * 60 + em

            if start_mins > end_mins:
                return curr_mins >= start_mins or curr_mins < end_mins
            else:
                return start_mins <= curr_mins < end_mins
        except Exception:
            return False

    def send_notification(
        self,
        db,
        user: User,
        message: str,
        title: Optional[str] = None,
        channels: Optional[List[str]] = None,
        execution_key: Optional[str] = None,
        inline_buttons: Optional[List[List[Dict[str, str]]]] = None
    ) -> Dict[str, Any]:
        """
        Sends notification across specified channels ('telegram', 'email', 'console' or 'both').
        Logs execution in NotificationLog table for idempotency.
        """
        if self.is_quiet_hours(user):
            logger.info(f"[NotificationService] Quiet hours active for user {user.email}. Skipping non-urgent send.")
            return {"status": "skipped", "reason": "quiet_hours_active"}

        if execution_key and db:
            existing = db.query(NotificationLog).filter(NotificationLog.execution_key == execution_key).first()
            if existing:
                logger.info(f"[NotificationService] Notification key '{execution_key}' already processed. Skipping duplicate.")
                return {"status": "skipped", "reason": "idempotency_key_exists"}

        if not channels:
            channels = ["console"]
            if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
                channels.append("telegram")
            if settings.EMAIL_SENDER and settings.EMAIL_APP_PASSWORD:
                channels.append("email")

        # Handle 'both' alias
        expanded_channels = []
        for ch in channels:
            if ch.lower() == "both":
                expanded_channels.extend(["telegram", "email"])
            else:
                expanded_channels.append(ch.lower())
        channels = list(set(expanded_channels))

        results = {}
        for ch in channels:
            provider = self.providers.get(ch)
            if provider:
                if ch == "telegram" and isinstance(provider, TelegramNotifier):
                    res = provider.send(message=message, title=title, recipient=user.email, inline_buttons=inline_buttons)
                else:
                    res = provider.send(message=message, title=title, recipient=user.email)
                results[ch] = res
            else:
                logger.warning(f"[NotificationService] Provider '{ch}' not supported.")
                results[ch] = False

        if db and execution_key:
            log_entry = NotificationLog(
                user_id=user.id,
                channel=",".join(channels),
                title=title or "Notification",
                message=message,
                status="sent" if any(results.values()) else "failed",
                sent_at=datetime.now(timezone.utc),
                execution_key=execution_key
            )
            db.add(log_entry)
            db.commit()

        return {"status": "sent", "results": results}

    def send_daily_plan(self, db, user: User, plan_summary: Dict[str, Any], channels: Optional[List[str]] = None) -> Dict[str, Any]:
        execution_key = f"daily_plan:{user.id}:{plan_summary.get('date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))}"
        
        # 1. Send Telegram if configured
        tg_provider: TelegramNotifier = self.providers["telegram"]
        if tg_provider.is_configured():
            tg_provider.send_daily_plan(user, plan_summary)

        # 2. Send Email if configured
        email_provider: EmailNotifier = self.providers["email"]
        if email_provider.is_configured():
            email_provider.send_daily_plan(user, plan_summary)

        # 3. Log Console
        console_provider: ConsoleNotifier = self.providers["console"]
        console_provider.send(message=f"DAY {plan_summary['day_number']} PLAN GENERATED: {plan_summary['objectives']}", title=f"Day {plan_summary['day_number']} Plan")

        return {"status": "sent", "execution_key": execution_key}

    def send_job_digest(self, db, user: User, jobs_digest: Dict[str, Any], channels: Optional[List[str]] = None) -> Dict[str, Any]:
        execution_key = f"job_digest:{user.id}:{jobs_digest.get('digest_date', datetime.now(timezone.utc).strftime('%Y-%m-%d'))}"
        
        tg_provider: TelegramNotifier = self.providers["telegram"]
        if tg_provider.is_configured():
            tg_provider.send_job_digest(user, jobs_digest)

        email_provider: EmailNotifier = self.providers["email"]
        if email_provider.is_configured():
            email_provider.send_job_digest(user, jobs_digest)

        return {"status": "sent", "execution_key": execution_key}
