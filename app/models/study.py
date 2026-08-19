from datetime import datetime, date, timezone
from sqlalchemy import Column, DateTime, Date, Integer, String, Text, Float, ForeignKey, Boolean, Index
from sqlalchemy.orm import relationship

from app.database.database import Base


class StudyPlan(Base):
    __tablename__ = "study_plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_date = Column(Date, nullable=False, index=True)
    day_number = Column(Integer, nullable=False, index=True)
    phase = Column(Integer, nullable=False)  # Phase 1, 2, 3, 4
    
    objectives = Column(Text, nullable=True)
    dsa_topic = Column(String(100), nullable=True)
    dsa_question_ids = Column(Text, nullable=True)  # JSON or CSV list of IDs
    aptitude_topic = Column(String(100), nullable=True)
    aptitude_question_count = Column(Integer, nullable=False, default=15)
    core_subject = Column(String(100), nullable=True)
    core_topics = Column(Text, nullable=True)
    python_topic = Column(String(100), nullable=True)
    sql_topic = Column(String(100), nullable=True)
    ml_topic = Column(String(100), nullable=True)
    communication_task = Column(Text, nullable=True)
    project_task = Column(Text, nullable=True)
    interview_task = Column(Text, nullable=True)
    estimated_total_time = Column(Float, nullable=False, default=6.5)
    
    completed_tasks = Column(Text, nullable=True, default="[]")  # JSON list of completed task keys
    recovery_tasks = Column(Text, nullable=True, default="[]")   # JSON list of recovery items
    is_completed = Column(Boolean, nullable=False, default=False, index=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="study_plans")
    sessions = relationship("StudySession", back_populates="study_plan", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_study_user_date", "user_id", "plan_date"),
    )


class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    study_plan_id = Column(Integer, ForeignKey("study_plans.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # DSA, Aptitude, Core, Python, SQL, ML, Interview, Project
    topic_name = Column(String(150), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, completed, skipped, missed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    study_plan = relationship("StudyPlan", back_populates="sessions")


class StudyTopic(Base):
    __tablename__ = "study_topics"

    id = Column(Integer, primary_key=True, index=True)
    phase = Column(Integer, nullable=False, index=True)
    day_number = Column(Integer, nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    topic_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
