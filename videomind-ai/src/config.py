"""
VideoMind AI Configuration
Handles all environment variables and application settings.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # App Configuration
    app_name: str = "VideoMind AI"
    app_version: str = "0.1.0"
    debug: bool = False
    secret_key: str
    
    # OpenAI / YouTube Configuration
    openai_api_key: str
    youtube_data_api_key: Optional[str] = None
    
    # Database Configuration
    database_url: str = "sqlite:///./videomind.db"
    
    # File Storage
    temp_storage_path: str = "./temp/"
    static_files_path: str = "./static/"
    download_base_url: str = "http://localhost:8000/api/download"
    
    # Email / Newsletter Configuration
    sendgrid_api_key: Optional[str] = None
    from_email: str = "noreply@videomind.ai"
    mailchimp_api_key: Optional[str] = None
    mailchimp_audience_id: Optional[str] = None
    mailchimp_server_prefix: Optional[str] = None
    mailchimp_tag: str = "videomind"
    
    # Payment Processing
    stripe_publishable_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Processing Limits
    max_video_duration_minutes: int = 120
    max_concurrent_jobs: int = 5
    file_cleanup_days: int = 7
    
    # Pricing Configuration (in cents)
    basic_tier_price: int = 300  # $3.00
    detailed_tier_price: int = 500  # $5.00
    bulk_discount_threshold: int = 5
    bulk_tier_price: int = 200  # $2.00
    
    @validator('temp_storage_path', 'static_files_path')
    def create_directories(cls, v):
        """Ensure directories exist."""
        os.makedirs(v, exist_ok=True)
        return v
    


# Global settings instance
settings = Settings()