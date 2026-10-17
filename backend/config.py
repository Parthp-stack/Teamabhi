import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AdaptIQ"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./adaptive_learning.db")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "adaptive-learning-secret-key-hackathon-2026-production-grade")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_MINUTES: int = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440")) # 24 hours

    # Supabase Settings (Optional API access alongside DATABASE_URL)
    SUPABASE_URL: Optional[str] = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: Optional[str] = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # OpenRouter AI
    OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Sandbox execution limits
    SANDBOX_TIMEOUT: int = 5 # seconds
    SANDBOX_MEMORY_MB: int = 128 # MB
    SANDBOX_MODE: str = os.getenv("SANDBOX_MODE", "auto") # auto, docker, or isolated_proc

    # Integrity Audit Retention
    INTEGRITY_DATA_RETENTION_DAYS: int = int(os.getenv("INTEGRITY_DATA_RETENTION_DAYS", "90"))

    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
