"""Configuration centralisée de l'application"""
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Paramètres de configuration de l'application"""
    
    # API Configuration
    app_name: str = "Bafoka Voice Banking Assistant"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # API Keys
    groq_api_key: str = ""
    hf_token: str = ""
    bafoka_api_key: str = ""
    bafoka_api_base_url: str = "https://api.bafoka.com"

    # Audio Configuration
    max_audio_size_mb: int = 10
    allowed_audio_formats: List[str] = ["mp3", "wav", "ogg", "m4a", "webm"]
    whisper_model_size: str = "large-v3"

    # Session Configuration
    session_timeout_minutes: int = 30
    redis_url: str = "redis://localhost:6379"

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_origins: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = False

    def validate_api_keys(self) -> dict[str, bool]:
        """Check which API keys are configured"""
        return {
            "groq_api_key": bool(self.groq_api_key),
            "hf_token": bool(self.hf_token),
            "bafoka_api_key": bool(self.bafoka_api_key),
        }


@lru_cache()
def get_settings() -> Settings:
    """Récupère les paramètres (singleton)"""
    return Settings()
