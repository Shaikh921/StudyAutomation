from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, Integer, String, Text, ForeignKey, Index
from app.database.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    channel = Column(String(50), nullable=False, index=True)  # console, email, whatsapp
    recipient = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="sent", index=True)  # pending, sent, failed, skipped
    execution_key = Column(String(100), unique=True, index=True, nullable=True)  # Idempotency key
    sent_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("idx_notif_user_sent", "user_id", "sent_at"),
    )
