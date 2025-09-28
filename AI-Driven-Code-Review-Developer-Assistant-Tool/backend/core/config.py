from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    debug: bool = True
    environment: str = "development"

    # Database
    database_url: str = "postgresql://username:password@localhost:5432/codereviewer"

    # LLM APIs
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # GitHub
    github_token: str = ""
    github_webhook_secret: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Stripe / billing
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    # JWT
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24

    # Security notifications
    security_email_recipients: List[str] = []
    slack_webhook_url: Optional[str] = None
    strict_ip_validation: bool = False

    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    class Config:
        env_file = ".env"
        case_sensitive = False

def get_settings() -> Settings:
    return Settings()
