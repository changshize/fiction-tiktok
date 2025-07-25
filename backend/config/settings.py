from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Application
    app_name: str = "Fiction TikTok"
    version: str = "1.0.0"
    environment: str = "development"
    debug: bool = True
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/fiction_tiktok"
    redis_url: str = "redis://localhost:6379"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    jwt_secret_key: str = "your-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Services
    openai_api_key: Optional[str] = None
    stable_diffusion_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    
    # Social Media APIs
    tiktok_client_key: Optional[str] = None
    tiktok_client_secret: Optional[str] = None
    youtube_api_key: Optional[str] = None
    instagram_access_token: Optional[str] = None
    
    # File Storage
    upload_dir: str = "./data"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    # Video Processing
    ffmpeg_path: str = "/usr/bin/ffmpeg"
    video_quality: str = "high"
    max_video_duration: int = 300  # 5 minutes
    default_video_resolution: str = "1080x1920"
    
    # Novel Scraping
    user_agent: str = "Mozilla/5.0 (compatible; FictionTikTok/1.0)"
    request_delay: float = 1.0
    max_concurrent_requests: int = 5
    
    # Content Generation
    default_language: str = "en"
    supported_languages: List[str] = ["en", "zh", "ja"]
    default_voice_speed: float = 1.0
    
    # Monitoring
    log_level: str = "INFO"
    sentry_dsn: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


# Ensure data directories exist
def create_data_directories():
    """Create necessary data directories if they don't exist."""
    directories = [
        settings.upload_dir,
        f"{settings.upload_dir}/novels",
        f"{settings.upload_dir}/illustrations",
        f"{settings.upload_dir}/audio",
        f"{settings.upload_dir}/videos",
        f"{settings.upload_dir}/temp",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)


# Initialize directories on import
create_data_directories()
