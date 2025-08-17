"""
Configuration settings for the Legal Intel Dashboard API.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Legal Intel Dashboard API"
    app_version: str = "1.0.0"
    debug: bool = True  # Enable debug mode for development
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql://legal_user:legal_pass123@localhost:5432/legal_intel"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_external_url: str = "redis://localhost:3030"
    redis_db: int = 0
    
    # MinIO/S3
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket_name: str = "legal-documents"
    minio_secure: bool = False
    
    # File upload
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_file_types: List[str] = ["pdf", "docx", "doc"]
    upload_folder: str = "uploads"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # LLM (OpenAI GPT-4o Mini)
    llm_provider: str = "openai"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_max_tokens: int = 4000
    openai_temperature: float = 0.1
    anthropic_api_key: Optional[str] = None
    
    # Processing
    max_concurrent_uploads: int = 5
    document_processing_timeout: int = 300  # 5 minutes
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance."""
    return settings 