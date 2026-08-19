import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

from app.config import settings
from app.notifications.base import NotificationProvider

logger = logging.getLogger(__name__)


class EmailNotifier(NotificationProvider):
    """
    Email Notification Provider using standard Python smtplib with TLS.
    Configured for Gmail SMTP by default.
    """

    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED
        self.smtp_server = settings.EMAIL_SMTP_SERVER or "smtp.gmail.com"
        self.smtp_port = settings.EMAIL_SMTP_PORT or 587
        self.sender_email = settings.EMAIL_SENDER
        self.password = settings.EMAIL_APP_PASSWORD

    def is_configured(self) -> bool:
        return bool(self.enabled and self.sender_email and self.password)

    def send(
        self,
        message: str,
        title: Optional[str] = None,
        recipient: Optional[str] = None,
        html_content: Optional[str] = None
    ) -> bool:
        target_email = recipient or self.sender_email

        if not self.is_configured() or not target_email:
            logger.warning("[EmailNotifier] Email SMTP credentials not configured (EMAIL_SENDER or EMAIL_APP_PASSWORD missing). Skipping email send.")
            return False

        subject = title or "60-Day CSE Placement Platform Update"

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.sender_email
        msg["To"] = target_email

        # Attach Plain Text part
        msg.attach(MIMEText(message, "plain"))

        # Attach HTML part if provided
        if html_content:
            msg.attach(MIMEText(html_content, "html"))
        else:
            formatted_html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #041312; color: #f0fdf4; padding: 24px;">
                <div style="max-width: 600px; margin: 0 auto; background: #0d2320; border: 1px solid #10b981; padding: 24px; border-radius: 12px;">
                    <h2 style="color: #34d399; margin-top: 0;">{subject}</h2>
                    <p style="white-space: pre-wrap; line-height: 1.6; color: #e2e8f0;">{message}</p>
                    <hr style="border-color: rgba(16, 185, 129, 0.2); margin-top: 24px;">
                    <p style="font-size: 0.8rem; color: #94a3b8;">Sent by 60-Day AI-Powered CSE Job Preparation Platform</p>
                </div>
            </body>
            </html>
            """
            msg.attach(MIMEText(formatted_html, "html"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(self.sender_email, self.password)
                server.sendmail(self.sender_email, target_email, msg.as_string())
            logger.info(f"[EmailNotifier] Email sent successfully to {target_email}.")
            return True
        except Exception as e:
            logger.error(f"[EmailNotifier] Failed to send email via SMTP: {e}")
            return False

    def send_daily_plan(self, user, plan_summary: Dict[str, Any]) -> bool:
        subject = f"Day {plan_summary['day_number']}/60 — Today's CSE Placement Mission"
        
        plain_text = (
            f"Day {plan_summary['day_number']} of 60 Curriculum\n\n"
            f"Objectives:\n{plan_summary['objectives']}\n\n"
            f"DSA: {plan_summary['dsa']['topic']}\n"
            f"Aptitude: {plan_summary['aptitude']['topic']}\n"
            f"Core CSE: {plan_summary['core']['subject']} — {plan_summary['core']['topics']}\n"
            f"Python: {plan_summary['python']['topic']}\n"
            f"SQL: {plan_summary['sql']['topic']}\n"
            f"ML: {plan_summary['ml']['topic']}\n"
        )

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #041312; color: #f0fdf4; padding: 24px;">
            <div style="max-width: 640px; margin: 0 auto; background: #0d2320; border: 1px solid #10b981; padding: 28px; border-radius: 16px;">
                <h2 style="color: #34d399; margin-top: 0;">🚀 DAY {plan_summary['day_number']} / 60 — TODAY'S CSE MISSION</h2>
                <p style="color: #fbbf24; font-weight: bold;">{plan_summary['phase_name']} ({plan_summary['mode_name']})</p>
                <div style="background: rgba(0,0,0,0.3); padding: 16px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 20px;">
                    <strong>Objectives:</strong><br>{plan_summary['objectives']}
                </div>
                <table style="width: 100%; border-collapse: collapse; color: #f0fdf4; font-size: 0.95rem;">
                    <tr><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>💻 DSA Focus</strong></td><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">{plan_summary['dsa']['topic']}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>📐 Aptitude</strong></td><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">{plan_summary['aptitude']['topic']}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>⚙️ Core CSE</strong></td><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">{plan_summary['core']['subject']} — {plan_summary['core']['topics']}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>🐍 Python</strong></td><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">{plan_summary['python']['topic']}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>🗄️ SQL</strong></td><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">{plan_summary['sql']['topic']}</td></tr>
                    <tr><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);"><strong>🤖 Machine Learning</strong></td><td style="padding: 8px; border-bottom: 1px solid rgba(255,255,255,0.1);">{plan_summary['ml']['topic']}</td></tr>
                </table>
            </div>
        </body>
        </html>
        """
        return self.send(message=plain_text, title=subject, recipient=user.email if hasattr(user, 'email') else None, html_content=html_body)

    def send_job_digest(self, user, jobs_digest: Dict[str, Any]) -> bool:
        subject = f"Daily CSE Job Digest — {jobs_digest.get('digest_date', 'Today')}"
        jobs = jobs_digest.get("jobs", [])

        plain_text = f"Top CSE Jobs Digest ({len(jobs)} jobs match your profile).\nCheck dashboard for full details."
        
        job_rows = "".join([
            f"<div style='margin-bottom: 16px; padding: 14px; background: rgba(6,20,18,0.7); border: 1px solid rgba(16,185,129,0.3); border-radius: 10px;'>"
            f"<h4 style='margin: 0; color: #34d399;'>{idx}. {j['title']}</h4>"
            f"<p style='margin: 4px 0; font-size: 0.88rem; color: #cbd5e1;'>Company: <strong>{j['company']}</strong> | Location: {j['location']} | Match: <span style='color: #fbbf24;'>{j['relevance_score']}%</span></p>"
            f"<a href='{j['source_url']}' style='display: inline-block; margin-top: 6px; background: #10b981; color: white; padding: 6px 14px; border-radius: 6px; text-decoration: none; font-weight: bold; font-size: 0.82rem;'>Apply Now ↗</a>"
            f"</div>"
            for idx, j in enumerate(jobs[:5], 1)
        ])

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #041312; color: #f0fdf4; padding: 24px;">
            <div style="max-width: 640px; margin: 0 auto; background: #0d2320; border: 1px solid #10b981; padding: 28px; border-radius: 16px;">
                <h2 style="color: #34d399; margin-top: 0;">💼 DAILY CSE JOB DIGEST</h2>
                <p style="color: #cbd5e1;">Top verified jobs matched to your Software & ML Engineer goals:</p>
                {job_rows}
            </div>
        </body>
        </html>
        """
        return self.send(message=plain_text, title=subject, recipient=user.email if hasattr(user, 'email') else None, html_content=html_body)
