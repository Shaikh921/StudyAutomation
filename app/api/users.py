from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List

from app.database.database import get_db
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    whatsapp_number: Optional[str] = None
    timezone: str = "Asia/Kolkata"
    available_hours_per_day: float = 6.5
    target_roles: Optional[str] = "Software Engineer,ML Engineer,Python Developer"
    preferred_locations: Optional[str] = "India,Remote,Pune,Bengaluru"


class UserUpdateConfig(BaseModel):
    name: Optional[str] = None
    timezone: Optional[str] = None
    available_hours_per_day: Optional[float] = None
    target_roles: Optional[str] = None
    preferred_locations: Optional[str] = None
    notification_channels: Optional[str] = None


@router.post("")
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        return existing
    
    user = User(**data.dict())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/me")
def get_current_user(db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/me/config")
def update_user_config(data: UserUpdateConfig, db: Session = Depends(get_db)):
    user = db.query(User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, val in data.dict(exclude_unset=True).items():
        setattr(user, key, val)

    db.commit()
    db.refresh(user)
    return user
