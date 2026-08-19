import pytest
import os
import sys
from datetime import datetime, date, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.database import Base, engine, SessionLocal
from app.database.migrations import init_db
from app.models import User, DSAQuestion, DSAAttempt, DSARevisionSchedule, StudyPlan, JobListing, JobApplication
from app.services.roadmap_service import RoadmapService
from app.services.planner_service import PlannerService
from app.services.dsa_service import DSAService
from app.services.job_search_service import JobSearchService
from app.services.gemini_service import GeminiService
from tools.import_dsa_bank import parse_dsa_markdown, DSA_FILE_PATH


@pytest.fixture(scope="module")
def setup_db():
    init_db()
    db = SessionLocal()
    yield db
    db.close()


def test_roadmap_calculations():
    day_1 = RoadmapService.calculate_current_day(date.today())
    assert day_1["current_day"] == 1
    assert day_1["current_phase"] == 1

    curr_1 = RoadmapService.get_day_curriculum(1)
    assert curr_1["dsa_topic"] == "Arrays"

    curr_20 = RoadmapService.get_day_curriculum(20)
    assert curr_20["phase"] == 2

    curr_50 = RoadmapService.get_day_curriculum(50)
    assert curr_50["phase"] == 4


def test_parse_dsa_markdown():
    if os.path.exists(DSA_FILE_PATH):
        parsed = parse_dsa_markdown(DSA_FILE_PATH)
        assert len(parsed) >= 200
        assert parsed[0]["topic"] is not None
        assert parsed[0]["difficulty"] in ["Easy", "Medium", "Hard"]


def test_dsa_attempt_and_spaced_repetition(setup_db):
    db = setup_db
    # Create test user
    user = db.query(User).filter(User.email == "test@example.com").first()
    if not user:
        user = User(name="Test User", email="test@example.com")
        db.add(user)
        db.commit()

    # Create test question
    q = db.query(DSAQuestion).filter(DSAQuestion.source_id == "test_q1").first()
    if not q:
        q = DSAQuestion(
            source_id="test_q1",
            question_text="Two Sum",
            topic="Arrays",
            difficulty="Easy"
        )
        db.add(q)
        db.commit()

    res = DSAService.record_attempt(db, user.id, q.id, result="correct", confidence=5)
    assert res["result"] == "correct"
    assert res["consecutive_correct"] == 1

    # Second correct attempt
    res2 = DSAService.record_attempt(db, user.id, q.id, result="correct", confidence=5)
    assert res2["consecutive_correct"] == 2
    assert res2["interval_days"] == 3.0


def test_job_relevance_scoring():
    raw_job = {
        "title": "Python Backend Developer (Fresher)",
        "experience_level": "0-1 years / Fresher",
        "skills": "Python, SQL, FastAPI",
        "location": "Pune, India",
        "remote": True
    }
    score = JobSearchService.calculate_relevance_score(raw_job)
    assert score >= 70.0


def test_gemini_service_fallback():
    gemini = GeminiService()
    res = gemini.ask_question("What is polymorphism?")
    assert "answer" in res
    assert "follow_up_question" in res
