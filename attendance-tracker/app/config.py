"""Application settings loaded from environment variables / .env file."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database ---
    # Example:
    #   postgresql+asyncpg://attendance:attendance_dev@localhost:5432/attendance
    database_url: str = (
        "postgresql+asyncpg://attendance:attendance_dev@localhost:5432/attendance"
    )

    # --- Security ---
    secret_key: str = "change-me-in-production-please-9f2c4b7a1d8e3f0a5b6c7d8e9f0a1b2c"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12  # 12 hours

    # --- App ---
    app_name: str = "Attendance Tracker"
    app_timezone: str = "Asia/Kolkata"
    # Allow self check-in/check-out for regular (non-admin) users
    allow_self_check: bool = True

    # --- Email (SMTP) ---
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    smtp_from_name: str = "Attendance Tracker"
    email_enabled: bool = False

    # --- Notification Settings ---
    late_check_in_minutes: int = 15  # minutes after shift start to trigger alert
    send_daily_reminder: bool = True
    send_late_alert: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
