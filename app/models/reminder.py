from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Boolean, Text, Index
from sqlalchemy.orm import relationship

from app.database.database import Base


class StudyReminder(Base):
    __tablename__ = "study_reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    topic = Column(String(255), nullable=False)
    remind_at = Column(DateTime, nullable=False, index=True)
    repeat_type = Column(String(20), nullable=False, default="none")  # none, daily, weekly
    channel = Column(String(20), nullable=False, default="console")   # console, email, whatsapp
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, sent, skipped, paused, needs_attention
    
    skip_count = Column(Integer, nullable=False, default=0)
    is_paused = Column(Boolean, nullable=False, default=False)
    action_triggers = Column(Text, nullable=True)  # JSON list of actions e.g. ["START DSA", "MARK COMPLETE", "SKIP", "RESCHEDULE"]
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="reminders")

    __table_args__ = (
        Index("idx_rem_user_remind", "user_id", "remind_at", "status"),
    )