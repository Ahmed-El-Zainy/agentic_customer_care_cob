# app/core/config.py
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # API Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./chatbot.db")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Gemini Configuration
    GEMINI_MODEL: str = "gemini-flash-1.5"
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_MAX_TOKENS: int = 2048
    
    # Application Settings
    MAX_CONVERSATION_HISTORY: int = 10
    INTENT_CONFIDENCE_THRESHOLD: float = 0.6
    ESCALATION_THRESHOLD: float = 0.4
    
    class Config:
        env_file = ".env"

settings = Settings()

