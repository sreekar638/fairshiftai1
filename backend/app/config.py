import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FairShift AI"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "fairshift-super-secret-key-promptwars-2026-sdg8")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./fairshift.db")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    class Config:
        case_sensitive = True

settings = Settings()
