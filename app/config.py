"""
Configuration management for RAG PDF System.

This module handles all application settings using Pydantic Settings,
loading configuration from environment variables with validation.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings have default values and can be overridden via .env file
    or environment variables.
    """
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral:7b"
    
    # Embedding Model
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Chunking Configuration
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Retrieval Configuration
    top_k_results: int = 3
    search_mode: str = "hybrid"  # "vector" or "hybrid"
    rrf_k: int = 60  # RRF fusion parameter
    
    # Application Settings
    app_name: str = "RAG PDF System"
    app_version: str = "2.0.0"
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    pdf_upload_dir: Path = data_dir / "uploaded_pdfs"
    vector_store_dir: Path = data_dir / "vector_store"
    
    # Redis Configuration
    redis_url: str  # Read from env
    cache_ttl_embeddings: int = 3600
    cache_ttl_wikipedia: int = 86400
    cache_ttl_search: int = 1800
    
    # MySQL Configuration
    mysql_host: str  # Read from env
    mysql_port: int  # Read from env
    mysql_user: str  # Read from env
    mysql_password: str  # Read from env
    mysql_database: str  # Read from env
    
    # Monitoring
    enable_metrics: bool = True
    enable_tracing: bool = True
    log_level: str = "INFO"
    metrics_port: int = 8000
    
    # Resilience
    ollama_timeout: int = 30
    ollama_retry_attempts: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # OCR Configuration
    tesseract_cmd: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    poppler_path: str = r"C:\Program Files\poppler-25.12.0\Library\bin"
    ocr_language: str = "spa+eng"
    ocr_enabled: bool = True
    
    # JWT Authentication
    jwt_secret_key: str  # Read from JWT_SECRET_KEY env
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Initial Admin User (for seeding)
    admin_email: str  # Read from ADMIN_EMAIL env
    admin_password: str  # Read from ADMIN_PASSWORD env
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    def __init__(self, **kwargs):
        """Initialize settings and ensure data directories exist."""
        super().__init__(**kwargs)
        self.pdf_upload_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def database_url(self) -> str:
        """Construct MySQL async connection URL from components."""
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )


# Global settings instance
settings = Settings()
