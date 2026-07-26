# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Google Apps Script Webhook
    GOOGLE_EMAIL_WEBHOOK: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()