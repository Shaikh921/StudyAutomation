from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List

from app.database.database import get_db
from app.models.user import User
from app.models.notification import NotificationLog
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class TestNotificationRequest(BaseModel):
    channel: Optional[str] = "console"
    subject: str = "Test Notification"
    body: str = "This is a test notification from the 60-Day CSE Prep Platform."


@router.get("/logs")
def get_notification_logs(db: Session = Depends(get_db)):
    return db.query(NotificationLog).order_by(NotificationLog.sent_at.desc()).limit(50).all()


@router.post("/test")
def send_test_notification(data: TestNotificationRequest, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    service = NotificationService()
    channels = [data.channel] if data.channel else ["console"]

    res = service.send_notification(
        db=db,
        user=user,
        message=data.body,
        title=data.subject,
        channels=channels,
        execution_key=None
    )

    return {"status": res["status"], "results": res.get("results", {}), "channels": channels}
