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
    
    # JWT Configuration
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Configuration
    frontend_url: str = "http://localhost:3000"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)


# Global settings instance
settings = Settings()
