from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    IS_RUNNING_LOCALLY: bool = False
    SWIT_CLIENT_ID: str
    SWIT_CLIENT_SECRET: str
    OPERATION_AUTH_KEY: str

    PORT: int = 5000

    # In case of using a daily scheduler
    SCHEDULE_TIME: Optional[str] = None  # example: '20:00'. If you don't want to use scheduler, set None.

    # New user's default settings
    DEFAULT_USER_LANGUAGE: str = 'en'

    # Logger
    SWIT_WEBHOOK_URL: Optional[str] = None

    # For API
    SWIT_BASE_URL: str = 'https://openapi.swit.io'

    # For provisioning
    TEAMS_TO_EXCLUDE: str = ''


settings = Settings()
