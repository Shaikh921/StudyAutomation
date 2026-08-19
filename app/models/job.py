from datetime import datetime, date, timezone
from sqlalchemy import Column, DateTime, Date, Integer, String, Text, Float, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database.database import Base


class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True, nullable=False)
    company = Column(String(150), index=True, nullable=False)
    location = Column(String(150), index=True, nullable=False)
    remote = Column(Boolean, nullable=False, default=False)
    experience_level = Column(String(100), nullable=False, default="Fresher / Entry Level")
    skills = Column(Text, nullable=True)  # JSON or CSV list of skills
    description = Column(Text, nullable=True)
    source = Column(String(100), nullable=False, default="Career Portal")
    source_url = Column(Text, nullable=False)
    posted_at = Column(DateTime, nullable=True)
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    relevance_score = Column(Float, nullable=False, default=0.0, index=True)
    duplicate_hash = Column(String(100), unique=True, index=True, nullable=False)
    fingerprint = Column(String(100), unique=True, index=True, nullable=True)
    status = Column(String(50), nullable=False, default="active", index=True)

    applications = relationship("JobApplication", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_job_comp_title", "company", "title"),
    )


class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("job_listings.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="saved", index=True)  # saved, applied, assessment, interview, rejected, selected, offer, withdrawn
    applied_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    resume_version = Column(String(100), nullable=True, default="V1_General_CSE")
    interview_date = Column(DateTime, nullable=True, index=True)
    follow_up_date = Column(DateTime, nullable=True, index=True)
    prep_pack = Column(Text, nullable=True)  # JSON prep pack generated for this job
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="job_applications")
    job = relationship("JobListing", back_populates="applications")

    __table_args__ = (
        Index("idx_app_user_status", "user_id", "status"),
    )


class JobPreference(Base):
    __tablename__ = "job_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    target_roles = Column(Text, nullable=False)
    locations = Column(Text, nullable=False)
    remote_preferred = Column(Boolean, nullable=False, default=True)
    min_experience_years = Column(Integer, nullable=False, default=0)
    max_experience_years = Column(Integer, nullable=False, default=2)


class DailyDigest(Base):
    __tablename__ = "daily_digests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    digest_date = Column(Date, nullable=False, index=True)
    job_ids = Column(Text, nullable=False)  # JSON array of job IDs
    status = Column(String(20), nullable=False, default="generated", index=True)  # generated, sent, failed
    sent_at = Column(DateTime, nullable=True)
