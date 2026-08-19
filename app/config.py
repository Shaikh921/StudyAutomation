import os
from dotenv import load_dotenv

load_dotenv(override=True)


class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "60-Day CSE Job Prep Automation Platform")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./automation_engine.db"
    )
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Kolkata")
    
    # Gemini API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Program Settings
    PROGRAM_START_DATE: str = os.getenv("PROGRAM_START_DATE", "")  # YYYY-MM-DD format
    DAILY_STUDY_HOURS: float = float(os.getenv("DAILY_STUDY_HOURS", "6.5"))

    # Telegram Bot Settings
    TELEGRAM_ENABLED: bool = os.getenv("TELEGRAM_ENABLED", "true").lower() == "true"
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Email SMTP Settings
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "true").lower() == "true"
    EMAIL_SMTP_SERVER: str = os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "587"))
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "")
    EMAIL_APP_PASSWORD: str = os.getenv("EMAIL_APP_PASSWORD", os.getenv("EMAIL_PASSWORD", ""))


settings = Settings()