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
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_embeddings: int = 3600  # 1 hour
    cache_ttl_wikipedia: int = 86400  # 24 hours
    cache_ttl_search: int = 1800  # 30 minutes
    
    # MySQL Configuration
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "rag_user"
    mysql_password: str = "ragpassword"
    mysql_database: str = "rag_metadata"
    mysql_root_password: str = "rootpassword"
    
    # Monitoring & Observability
    enable_metrics: bool = True
    enable_tracing: bool = True
    log_level: str = "INFO"
    metrics_port: int = 8000
    
    # Resilience Patterns
    ollama_timeout: int = 30
    ollama_retry_attempts: int = 3
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    
    # OCR Configuration
    tesseract_cmd: str = "tesseract"  # Path to tesseract executable
    poppler_path: str = ""  # Path to poppler bin directory
    ocr_language: str = "spa+eng"  # Languages for OCR (Spanish + English)
    ocr_enabled: bool = True  # Enable OCR fallback for scanned PDFs
    
    # Paths
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    pdf_upload_dir: Path = data_dir / "uploaded_pdfs"
    vector_store_dir: Path = data_dir / "vector_store"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    
    @property
    def database_url(self) -> str:
        """Construct async MySQL database URL for SQLAlchemy."""
        return f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
    
    def __init__(self, **kwargs):
        """Initialize settings and ensure data directories exist."""
        super().__init__(**kwargs)
        self.pdf_upload_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
