# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database and Security
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email SMTP Settings (Added to fix the attribute error)
    EMAIL_SENDER: str
    EMAIL_PASSWORD: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()