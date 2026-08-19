import json
import logging
import urllib.request
import urllib.parse
from typing import Optional, List, Dict, Any

from app.config import settings
from app.notifications.base import NotificationProvider
from app.database.database import SessionLocal
from app.models.user import User
from app.services.planner_service import PlannerService
from app.services.dsa_service import DSAService
from app.services.job_search_service import JobSearchService
from app.services.gemini_service import GeminiService
from app.services.mock_interview_service import MockInterviewService

logger = logging.getLogger(__name__)


class TelegramNotifier(NotificationProvider):
    """
    Telegram Notification Provider using standard HTTPS requests to Telegram Bot API.
    Does not depend on external third-party SDKs.
    """

    def __init__(self):
        self.enabled = settings.TELEGRAM_ENABLED
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.default_chat_id = settings.TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage" if self.bot_token else None

    def is_configured(self) -> bool:
        return bool(self.enabled and self.bot_token and self.default_chat_id)

    def send(
        self,
        message: str,
        title: Optional[str] = None,
        recipient: Optional[str] = None,
        inline_buttons: Optional[List[List[Dict[str, str]]]] = None
    ) -> bool:
        target_chat_id = recipient or self.default_chat_id

        if not self.is_configured() and not target_chat_id:
            logger.warning("[TelegramNotifier] Telegram Bot Token or Chat ID not configured. Skipping send.")
            return False

        if not self.api_url or not target_chat_id:
            logger.warning("[TelegramNotifier] Missing API URL or target chat ID. Skipping send.")
            return False

        full_text = f"<b>{title}</b>\n\n{message}" if title else message

        payload: Dict[str, Any] = {
            "chat_id": target_chat_id,
            "text": full_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }

        if inline_buttons:
            payload["reply_markup"] = json.dumps({"inline_keyboard": inline_buttons})

        try:
            req = urllib.request.Request(
                self.api_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    logger.info(f"[TelegramNotifier] Message sent successfully to Telegram chat {target_chat_id}.")
                    return True
                else:
                    logger.error(f"[TelegramNotifier] Failed to send message. HTTP status: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"[TelegramNotifier] Error sending Telegram message: {e}")
            return False

    def send_daily_plan(self, user, plan_summary: Dict[str, Any]) -> bool:
        title = f"🚀 DAY {plan_summary['day_number']} / 60 — TODAY'S MISSION"
        body = (
            f"<b>Phase:</b> {plan_summary['phase_name']} ({plan_summary['mode_name']})\n"
            f"<b>Progress:</b> {plan_summary['completion_percentage']}% ({plan_summary['days_completed']} Days Done, {plan_summary['days_remaining']} Left)\n"
            f"<b>Target Study Allocation:</b> {plan_summary['estimated_hours']} Hours\n\n"
            f"<b>Curriculum Objectives:</b>\n{plan_summary['objectives']}\n\n"
            f"🧠 <b>DSA Pattern:</b> {plan_summary['dsa']['topic']} ({plan_summary['dsa']['question_count']} Problems)\n"
            f"📐 <b>Aptitude:</b> {plan_summary['aptitude']['topic']} ({plan_summary['aptitude']['question_count']} Questions)\n"
            f"⚙️ <b>Core CSE:</b> {plan_summary['core']['subject']} — {plan_summary['core']['topics']}\n"
            f"🐍 <b>Python:</b> {plan_summary['python']['topic']}\n"
            f"🗄️ <b>SQL:</b> {plan_summary['sql']['topic']}\n"
            f"🤖 <b>Machine Learning:</b> {plan_summary['ml']['topic']}\n"
            f"💼 <b>Jobs Target:</b> Apply to 5 quality jobs today\n"
        )

        buttons = [
            [{"text": "🎯 START TODAY'S PLAN", "callback_data": "cmd_today"}, {"text": "💻 START DSA", "callback_data": "cmd_dsa"}],
            [{"text": "💼 VIEW JOBS", "callback_data": "cmd_jobs"}, {"text": "🗣️ MOCK INTERVIEW", "callback_data": "cmd_mock"}],
            [{"text": "🤖 ASK GEMINI", "callback_data": "cmd_ask"}, {"text": "📊 VIEW PROGRESS", "callback_data": "cmd_progress"}]
        ]
        return self.send(message=body, title=title, recipient=user.email if hasattr(user, 'email') else None, inline_buttons=buttons)

    def send_job_digest(self, user, jobs_digest: Dict[str, Any]) -> bool:
        title = f"💼 DAILY CSE JOB DIGEST — DAY {jobs_digest.get('day_number', 1)} / 60"
        jobs = jobs_digest.get("jobs", [])

        if not jobs:
            return self.send(message="No new verified job listings matching your profile today.", title=title)

        body_lines = [f"🔥 <b>TOP MATCHES ({len(jobs)} Verified CSE Jobs)</b>\n"]
        buttons = []

        for idx, job in enumerate(jobs[:5], 1):
            body_lines.append(
                f"<b>{idx}️⃣ {job['title']}</b>\n"
                f"Company: {job['company']}\n"
                f"Location: {job['location']} | Match: <b>{job['relevance_score']}%</b>\n"
                f"Skills: {job['skills']}\n"
            )
            buttons.append([{"text": f"🔗 Apply #{idx}: {job['company'][:15]}", "url": job['source_url']}])

        body_lines.append("\n🎯 <b>Recommended Action:</b> Apply to top 2-3 listings today!")
        buttons.append([{"text": "💼 VIEW ALL JOBS IN DASHBOARD", "callback_data": "cmd_jobs"}])

        return self.send(message="\n".join(body_lines), title=title, inline_buttons=buttons)


class TelegramCommandHandler:
    """
    Handles incoming Telegram bot commands and natural language Q&A.
    """

    @staticmethod
    def process_message(user_text: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        text = user_text.strip()
        db = SessionLocal()

        try:
            user = db.query(User).first()
            if not user:
                return {"reply": "No registered user found in platform database.", "buttons": []}

            # 1. /start command
            if text.startswith("/start"):
                reply = (
                    f"👋 Welcome {user.name} to your <b>60-Day AI-Powered CSE Career Coach</b>!\n\n"
                    "I am your autonomous placement coach. I schedule daily study plans, manage DSA spaced repetition, "
                    "digest live CSE job listings, and conduct mock interviews powered by Gemini 2.5."
                )
                buttons = [
                    [{"text": "🎯 TODAY'S MISSION", "callback_data": "cmd_today"}, {"text": "💻 DSA QUESTION", "callback_data": "cmd_dsa"}],
                    [{"text": "💼 LIVE JOBS", "callback_data": "cmd_jobs"}, {"text": "🗣️ MOCK INTERVIEW", "callback_data": "cmd_mock"}],
                    [{"text": "🤖 ASK GEMINI", "callback_data": "cmd_ask"}, {"text": "📊 PROGRESS", "callback_data": "cmd_progress"}]
                ]
                return {"reply": reply, "buttons": buttons}

            # 2. /help command
            elif text.startswith("/help"):
                reply = (
                    "<b>🤖 COMMAND LIST & INTERACTIVE HELP:</b>\n\n"
                    "• /today — Today's Day X mission objectives\n"
                    "• /dsa — Today's DSA question & hints\n"
                    "• /jobs — Top matched CSE job listings\n"
                    "• /progress — 60-day curriculum progress & DSA accuracy\n"
                    "• /mock — Start 7-Round Mock Interview\n"
                    "• /ask &lt;prompt&gt; — Ask Gemini AI Tutor anything\n\n"
                    "<i>You can also type any natural language technical question directly!</i>"
                )
                return {"reply": reply, "buttons": []}

            # 3. /today command
            elif text.startswith("/today"):
                summary = PlannerService.get_today_mission_summary(db, user)
                reply = (
                    f"🎯 <b>DAY {summary['day_number']} / 60 — {summary['phase_name']}</b> ({summary['mode_name']})\n\n"
                    f"<b>Curriculum Objectives:</b>\n{summary['objectives']}\n\n"
                    f"🧠 <b>DSA:</b> {summary['dsa']['topic']} ({summary['dsa']['question_count']} Qs)\n"
                    f"📐 <b>Aptitude:</b> {summary['aptitude']['topic']} ({summary['aptitude']['question_count']} Qs)\n"
                    f"⚙️ <b>Core CSE:</b> {summary['core']['subject']} — {summary['core']['topics']}\n"
                    f"🐍 <b>Python:</b> {summary['python']['topic']}\n"
                    f"🗄️ <b>SQL:</b> {summary['sql']['topic']}\n"
                    f"🤖 <b>ML:</b> {summary['ml']['topic']}\n"
                )
                buttons = [
                    [{"text": "💻 SOLVE DSA NOW", "callback_data": "cmd_dsa"}, {"text": "💼 APPLY TO JOBS", "callback_data": "cmd_jobs"}],
                    [{"text": "MARK TODAY COMPLETE", "callback_data": "cmd_complete_today"}]
                ]
                return {"reply": reply, "buttons": buttons}

            # 4. /dsa command
            elif text.startswith("/dsa"):
                summary = PlannerService.get_today_mission_summary(db, user)
                questions = summary['dsa'].get('questions', [])
                if not questions:
                    return {"reply": "No pending DSA questions for today!", "buttons": []}
                
                q = questions[0]
                q_text = q.get('question', q.get('question_text', ''))
                reply = (
                    f"💻 <b>TODAY'S DSA QUESTION:</b>\n\n"
                    f"<b>[{q['difficulty']}] {q['title']}</b>\n"
                    f"<b>Topic:</b> {q['topic']} | <b>Pattern:</b> {q.get('pattern', 'Standard')}\n\n"
                    f"<i>{q_text[:300]}...</i>"
                )

                buttons = [
                    [{"text": "💡 Hint 1 (Clue)", "callback_data": f"hint1_{q['id']}"}, {"text": "🔍 Hint 2 (Pattern)", "callback_data": f"hint2_{q['id']}"}],
                    [{"text": "📖 Full Solution", "callback_data": f"sol_{q['id']}"}, {"text": "🤖 Explain with Gemini", "callback_data": f"explain_{q['id']}"}]
                ]
                return {"reply": reply, "buttons": buttons}

            # 5. /jobs command
            elif text.startswith("/jobs"):
                job_search = JobSearchService()
                digest = job_search.generate_daily_digest(db, user, limit=5)
                jobs = digest.get("jobs", [])
                
                lines = [f"💼 <b>TOP CSE JOB MATCHES ({len(jobs)} Listings)</b>\n"]
                buttons = []
                for idx, j in enumerate(jobs, 1):
                    lines.append(f"<b>{idx}. {j['title']}</b> at {j['company']} ({j['location']}) — Match: <b>{j['relevance_score']}%</b>")
                    buttons.append([{"text": f"Apply #{idx}: {j['company'][:15]} ↗", "url": j['source_url']}])

                return {"reply": "\n".join(lines), "buttons": buttons}

            # 6. /progress command
            elif text.startswith("/progress"):
                dsa_prog = DSAService.get_progress(db, user.id)
                summary = PlannerService.get_today_mission_summary(db, user)
                reply = (
                    f"📊 <b>60-DAY CSE PREPARATION PROGRESS:</b>\n\n"
                    f"• <b>Day Progress:</b> Day {summary['day_number']} of 60 ({summary['completion_percentage']}% Done)\n"
                    f"• <b>DSA Solved:</b> {dsa_prog['total_solved_correctly']} / {dsa_prog['total_questions_in_bank']} ({dsa_prog['accuracy_percentage']}% Accuracy)\n"
                    f"• <b>Spaced Revisions Due:</b> {dsa_prog['due_for_revision']} Problems\n"
                )
                return {"reply": reply, "buttons": []}

            # 7. /mock command
            elif text.startswith("/mock"):
                mock_svc = MockInterviewService()
                round_data = mock_svc.get_round_question(1)
                reply = (
                    f"🗣️ <b>7-ROUND MOCK INTERVIEW MODE</b>\n\n"
                    f"<b>Round 1 of 7 — {round_data['round_name']}</b>\n\n"
                    f"<b>Interviewer Question:</b>\n{round_data['question']}\n\n"
                    f"<i>Type your answer or code directly to proceed to evaluation!</i>"
                )
                return {"reply": reply, "buttons": []}

            # 8. /ask or Natural Language Text -> Gemini AI
            else:
                prompt = text.replace("/ask", "").strip()
                if not prompt:
                    prompt = "Give me a quick 3-bullet tip on how to prepare for Technical Interviews today."
                
                gemini = GeminiService()
                ai_res = gemini.ask(prompt)
                reply = f"🤖 <b>GEMINI AI TUTOR RESPONSE:</b>\n\n{ai_res['reply']}"
                return {"reply": reply, "buttons": []}

        finally:
            db.close()
