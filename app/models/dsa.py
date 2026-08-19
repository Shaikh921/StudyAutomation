from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, Float, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database.database import Base


class DSAQuestion(Base):
    __tablename__ = "dsa_questions"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(String(100), unique=True, index=True, nullable=False)
    fingerprint = Column(String(64), unique=True, index=True, nullable=True)  # SHA256(topic + title)
    question_text = Column(Text, nullable=False)
    topic = Column(String(100), index=True, nullable=False)
    subtopic = Column(String(100), nullable=True)
    difficulty = Column(String(20), index=True, nullable=False)  # Easy, Medium, Hard
    pattern = Column(String(100), nullable=True)
    source_file = Column(String(255), nullable=True)
    original_order = Column(Integer, nullable=True)
    inferred_metadata = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    attempts = relationship("DSAAttempt", back_populates="question", cascade="all, delete-orphan")
    revision_schedules = relationship("DSARevisionSchedule", back_populates="question", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_dsa_topic_diff", "topic", "difficulty"),
    )


class DSAAttempt(Base):
    __tablename__ = "dsa_attempts"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("dsa_questions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    attempted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    answer_text = Column(Text, nullable=True)
    result = Column(String(20), nullable=False, index=True)  # correct, incorrect, partial, skipped
    time_taken_seconds = Column(Integer, nullable=True)
    confidence = Column(Integer, nullable=True)  # 1 to 5
    notes = Column(Text, nullable=True)

    question = relationship("DSAQuestion", back_populates="attempts")
    user = relationship("User", back_populates="dsa_attempts")

    __table_args__ = (
        Index("idx_dsa_attempt_user_q", "user_id", "question_id"),
    )


class DSARevisionSchedule(Base):
    __tablename__ = "dsa_revision_schedule"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("dsa_questions.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    last_attempted = Column(DateTime, nullable=True)
    next_revision = Column(DateTime, nullable=False, index=True)
    interval_days = Column(Float, nullable=False, default=1.0)
    ease_score = Column(Float, nullable=False, default=2.5)
    consecutive_correct = Column(Integer, nullable=False, default=0)
    priority = Column(Integer, nullable=False, default=1)

    question = relationship("DSAQuestion", back_populates="revision_schedules")

    __table_args__ = (
        Index("idx_dsa_rev_user_next", "user_id", "next_revision"),
    )
