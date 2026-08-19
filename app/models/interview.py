from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from app.database.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False)  # DSA, Python, SQL, DBMS, OS, CN, OOP, ML, Projects, HR, Mixed
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime, nullable=True)
    overall_score = Column(Float, nullable=True)
    feedback_summary = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="in_progress")  # in_progress, completed

    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), index=True, nullable=False)
    topic = Column(String(100), index=True, nullable=False)
    question_text = Column(Text, nullable=False)
    difficulty = Column(String(20), nullable=False, default="Medium")
    sample_answer = Column(Text, nullable=True)
    key_points = Column(Text, nullable=True)  # JSON or bullet list of evaluation points
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    user_answer = Column(Text, nullable=True)
    evaluation_score = Column(Float, nullable=True)  # 0 to 10 scale
    correctness = Column(Text, nullable=True)
    completeness = Column(Text, nullable=True)
    communication = Column(Text, nullable=True)
    missing_points = Column(Text, nullable=True)
    follow_up_question = Column(Text, nullable=True)
    answered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("InterviewSession", back_populates="answers")
