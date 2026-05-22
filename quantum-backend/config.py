"""
Configuration management using Pydantic Settings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Vexa AI Configuration
    vexa_api_key: str = ""
    vexa_base_url: str = "https://api.cloud.vexa.ai"
    
    # Google Gemini AI Configuration
    gemini_api_key: str = ""
    
    # Database Configuration
    database_url: str = "sqlite:///./quantum.db"
    database_name: str = "quantum_meetings"
    
    # JWT Configuration
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_days: int = 7
    
    # CORS Configuration
    frontend_url: str = "http://localhost:3000"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Google Calendar Configuration
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""
    google_calendar_redirect_uri: str = ""
    
    # SMTP Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    # AI Model Configuration
    model_path: str = "Sales_emotion_module/model.h5"
    model_type_prod: str = "keras"
    device_type: str = "auto"
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


# Global settings instance
settings = Settings()
