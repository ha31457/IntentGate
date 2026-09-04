import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "IntentGate"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./intentgate.db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = True
    
    # Razorpay Test Mode Credentials
    RAZORPAY_KEY_ID: str = "rzp_test_mock_key_id"
    RAZORPAY_KEY_SECRET: str = "rzp_test_mock_secret"
    RAZORPAY_WEBHOOK_SECRET: str = "rzp_webhook_secret_key"
    
    # Gemini AI
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-3.5-flash"
    
    # Security Defaults
    DEFAULT_INTENT_EXPIRY_SECONDS: int = 300  # 5 minutes
    MAX_PRICE_DATA_AGE_SECONDS: int = 120    # 2 minutes
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 3
    CIRCUIT_BREAKER_RECOVERY_TIME_SECONDS: int = 30
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
