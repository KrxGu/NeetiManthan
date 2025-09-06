from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/neetimanthan"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin123"
    minio_bucket: str = "neetimanthan"
    
    # Security
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # AI Models
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    sentiment_model: str = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
    
    # Services
    ingest_tool_url: str = "http://localhost:8001"
    classify_tool_url: str = "http://localhost:8002"
    clause_linker_url: str = "http://localhost:8003"
    summarize_tool_url: str = "http://localhost:8004"
    
    # Processing
    confidence_threshold: float = 0.7
    similarity_threshold: float = 0.92
    max_clause_candidates: int = 5
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
