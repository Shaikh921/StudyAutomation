from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)

    name = Column(String, nullable=False)
    program_status = Column(String, default="NOT_STARTED", index=True)  # NOT_STARTED, ACTIVE, PAUSED, COMPLETED
    program_start_date = Column(DateTime, nullable=True)
    program_started_at = Column(DateTime, nullable=True)
    program_end_date = Column(DateTime, nullable=True)
    paused_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    daily_study_hours = Column(Integer, default=6)
    target_roles = Column(String, default="Software Developer, ML Engineer, Python Developer")
    preferred_locations = Column(String, default="India, Remote, Pune, Bengaluru, Hyderabad")
    notification_channels = Column(String, default="console,email,telegram")
    
    # Preferences & Quiet Hours
    timezone = Column(String, default="Asia/Kolkata")
    quiet_hours_start = Column(String, default="23:00")
    quiet_hours_end = Column(String, default="06:00")
    custom_reminder_schedule = Column(Text, default="{}")  # JSON mapping of custom times
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    study_plans = relationship("StudyPlan", back_populates="user", cascade="all, delete-orphan")
    dsa_attempts = relationship("DSAAttempt", back_populates="user", cascade="all, delete-orphan")
    job_applications = relationship("JobApplication", back_populates="user", cascade="all, delete-orphan")
    reminders = relationship("StudyReminder", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_status", "program_status"),
    )