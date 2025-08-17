# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional, Literal
from functools import lru_cache

class Settings(BaseSettings):
    # App Configuration
    app_name: str = "OffbeatWS"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: Literal["development", "staging", "production"] = "development"
    api_prefix: str = "/api/v2"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    secret_key: str = "your-secret-key-change-this"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    
    # Database Configuration
    db_provider: str = "sqlalchemy"
    
    # SQLAlchemy (PostgreSQL/MySQL/SQLite)
    database_url: Optional[str] = None
    db_host: Optional[str] = None
    db_port: Optional[int] = None
    db_name: Optional[str] = None
    db_user: Optional[str] = None
    db_password: Optional[str] = None
    db_driver: str = "postgresql"
    
    # Supabase
    supabase_url: Optional[str] = None
    supabase_key: Optional[str] = None
    supabase_service_key: Optional[str] = None
    
    # Prisma
    prisma_database_url: Optional[str] = None
    
    # Storage Configuration
    storage_provider: Literal["s3", "cloudinary", "supabase"]  = "supabase"
    
    # AWS S3
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: str = "us-east-1"
    s3_bucket_name: Optional[str] = None
    
    # Cloudinary
    cloudinary_cloud_name: Optional[str] = None
    cloudinary_api_key: Optional[str] = None
    cloudinary_api_secret: Optional[str] = None
    
    # Cache Configuration
    cache_provider: Literal["redis", "memory"] = "memory"
    redis_url: Optional[str] = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    # payment configuration
    payment_provider: Literal["stripe", "paypal"] = "stripe"
    stripe_secret_key: Optional[str] = None
    stripe_public_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_currency: str = "inr"
    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None

    # Logging Configuration
    log_level: str = "INFO"
    log_format: str = "detailed"
    log_file_enabled: bool = True
    log_file_path: str = "logs/app.log"
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    
    # File Upload Configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "text/plain", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # CORS Configuration
    # cors_origins: list[str] = ["*"]
    # cors_credentials: bool = True
    # cors_methods: list[str] = ["*"]
    # cors_headers: list[str] = ["*"]
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"
    
    @property
    def get_database_url(self) -> str:
        """Build SQLAlchemy database URL from components or use direct URL"""

        print("database_url: ", self.database_url)  
        if self.database_url:
            return self.database_url
        
        if not all([self.db_host, self.db_name, self.db_user, self.db_password]):
            raise ValueError("Database connection parameters are incomplete")
        
        return f"{self.db_driver}://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port or 5432}/{self.db_name}"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()