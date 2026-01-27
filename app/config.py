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
    app_version: str = "1.0.0"
    
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
    
    def __init__(self, **kwargs):
        """Initialize settings and ensure data directories exist."""
        super().__init__(**kwargs)
        self.pdf_upload_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
