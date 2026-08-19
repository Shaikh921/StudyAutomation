import os
import sys
import unittest
import uuid
from datetime import date, datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import SessionLocal
from app.database.migrations import init_db
from app.models import User, DSAQuestion, DSAAttempt, DSARevisionSchedule, JobListing
from app.services.roadmap_service import RoadmapService
from app.services.planner_service import PlannerService
from app.services.dsa_service import DSAService
from app.services.job_search_service import JobSearchService
from app.services.job_service import JobApplicationService
from app.services.gemini_service import GeminiService
from app.services.mock_interview_service import MockInterviewService
from app.services.notification_service import NotificationService
from app.notifications.telegram import TelegramNotifier, TelegramCommandHandler
from app.notifications.email import EmailNotifier
from tools.import_dsa_bank import parse_dsa_markdown, DSA_FILE_PATH


class TestPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()
        cls.db = SessionLocal()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_program_start_logic_and_state_machine(self):
        user = self.db.query(User).first()
        self.assertIsNotNone(user)

        # 1. Test NOT_STARTED calculation
        user.program_status = "NOT_STARTED"
        user.program_start_date = None
        self.db.commit()

        calc_not_started = RoadmapService.calculate_current_day(user=user)
        self.assertEqual(calc_not_started["status"], "NOT_STARTED")
        self.assertFalse(calc_not_started["is_started"])
        self.assertEqual(calc_not_started["current_day"], 0)

        # 2. Test START program setting Day 1
        today_kolkata = RoadmapService.get_today_kolkata()
        start_dt = datetime.combine(today_kolkata, datetime.min.time())
        user.program_status = "ACTIVE"
        user.program_start_date = start_dt
        self.db.commit()

        calc_active = RoadmapService.calculate_current_day(user=user)
        self.assertEqual(calc_active["status"], "ACTIVE")
        self.assertTrue(calc_active["is_started"])
        self.assertEqual(calc_active["current_day"], 1)

        # 3. Test 10 days later calculation (Day 11)
        past_start = start_dt - timedelta(days=10)
        user.program_start_date = past_start
        self.db.commit()

        calc_11 = RoadmapService.calculate_current_day(user=user)
        self.assertEqual(calc_11["current_day"], 11)

        # 4. Test Day 46 (Sprint Mode) & Day 54 (Final Mode)
        sprint_start = start_dt - timedelta(days=45)
        user.program_start_date = sprint_start
        self.db.commit()

        calc_46 = RoadmapService.calculate_current_day(user=user)
        self.assertEqual(calc_46["current_day"], 46)
        self.assertTrue(calc_46["is_sprint_mode"])

        # Reset user to ACTIVE today
        user.program_status = "ACTIVE"
        user.program_start_date = start_dt
        self.db.commit()

    def test_dsa_bank_parser(self):
        parsed = parse_dsa_markdown(DSA_FILE_PATH)
        self.assertGreaterEqual(len(parsed), 250)
        self.assertIn(parsed[0]["difficulty"], ["Easy", "Medium", "Hard"])

    def test_dsa_spaced_repetition(self):
        user = self.db.query(User).first()
        self.assertIsNotNone(user)

        unique_id = f"test_q_{uuid.uuid4().hex[:8]}"
        question = DSAQuestion(
            source_id=unique_id,
            question_text="Two Sum Dynamic Test",
            topic="Arrays",
            difficulty="Easy"
        )
        self.db.add(question)
        self.db.commit()
        self.db.refresh(question)

        attempt1 = DSAService.record_attempt(self.db, user.id, question.id, "correct", confidence=5)
        self.assertEqual(attempt1["result"], "correct")
        self.assertEqual(attempt1["consecutive_correct"], 1)

        attempt2 = DSAService.record_attempt(self.db, user.id, question.id, "correct", confidence=5)
        self.assertEqual(attempt2["consecutive_correct"], 2)
        self.assertEqual(attempt2["interval_days"], 3.0)

    def test_job_relevance_score(self):
        score = JobSearchService.calculate_relevance_score(
            title="Python Developer (Fresher)",
            company="TechCorp",
            description="Entry level python developer with SQL and ML basics",
            skills_str="Python, SQL, ML"
        )
        self.assertGreaterEqual(score, 70.0)

    def test_job_prep_pack(self):
        job = JobListing(
            title="Machine Learning Intern",
            company="AI Labs",
            location="Remote",
            source_url="https://example.com/job1",
            duplicate_hash="hash123",
            relevance_score=85.0
        )
        pack = JobApplicationService.generate_prep_pack(job)
        self.assertEqual(pack["company"], "AI Labs")
        self.assertIn("python", pack["questions"])

    def test_gemini_service(self):
        gemini = GeminiService()
        res = gemini.ask("Explain TCP 3-way handshake.")
        self.assertIn("reply", res)

    def test_mock_interview_service(self):
        interview_svc = MockInterviewService()
        round_1 = interview_svc.get_round_question(1)
        self.assertEqual(round_1["round_num"], 1)

        eval_res = interview_svc.evaluate_round_answer(1, round_1["question"], "I am a CSE student passionate about software engineering.")
        self.assertIn("score", eval_res)

        report = interview_svc.generate_final_interview_report([eval_res])
        self.assertIn("overall_score", report)

    def test_quiet_hours_check(self):
        user = User(email="test_qh@example.com", name="Test User", quiet_hours_start="23:00", quiet_hours_end="06:00")
        dt_night = datetime(2026, 8, 19, 23, 30, tzinfo=timezone.utc)
        dt_day = datetime(2026, 8, 19, 14, 0, tzinfo=timezone.utc)

        self.assertTrue(NotificationService.is_quiet_hours(user, dt_night))
        self.assertFalse(NotificationService.is_quiet_hours(user, dt_day))

    def test_telegram_provider_and_command_handler(self):
        tg = TelegramNotifier()
        res = tg.send("Test Telegram Message", title="Test")
        self.assertIsInstance(res, bool)

        res_start = TelegramCommandHandler.process_message("/start")
        self.assertIn("reply", res_start)
        self.assertGreaterEqual(len(res_start["buttons"]), 2)

        res_today = TelegramCommandHandler.process_message("/today")
        self.assertIn("reply", res_today)

        res_dsa = TelegramCommandHandler.process_message("/dsa")
        self.assertIn("reply", res_dsa)

    def test_email_provider_fallback(self):
        email_notifier = EmailNotifier()
        res = email_notifier.send("Test Email Message", title="Test Email")
        self.assertIsInstance(res, bool)


if __name__ == "__main__":
    unittest.main()
