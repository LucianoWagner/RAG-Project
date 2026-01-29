"""
Structured logging configuration using loguru.

Provides JSON-formatted logs with context, tracing, and automatic rotation.
Best practices for production observability.
"""

import sys
from pathlib import Path
from loguru import logger
from app.config import settings


def setup_logging():
    """
    Configure structured logging with loguru.
    
    Features:
    - JSON output for log aggregation (ELK, Datadog, etc.)
    - Contextualized logs with trace_id
    - Log rotation (10MB per file, 7 days retention)
    - Different log levels per environment
    - Console + file output
    """
    
    # Remove default handler
    logger.remove()
    
    # Console handler with colored output (development)
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )
    
    # File handler with JSON output (production)
    log_dir = settings.base_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "rag_system_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=settings.log_level,
        rotation="10 MB",  # Rotate when file reaches 10MB
        retention="7 days",  # Keep logs for 7 days
        compression="zip",  # Compress rotated logs
        serialize=False,  # Set to True for JSON output
        enqueue=True,  # Thread-safe
    )
    
    # JSON file handler for structured logging (machine-readable)
    logger.add(
        log_dir / "rag_system_json_{time:YYYY-MM-DD}.log",
        format="{message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        serialize=True,  # JSON output
        enqueue=True,
    )
    
    logger.info(f"Logging configured: level={settings.log_level}, dir={log_dir}")
    return logger


# Create and configure logger instance
log = setup_logging()


def get_logger(name: str = None):
    """
    Get a logger instance with optional module name.
    
    Args:
        name: Module name for contextualized logging
        
    Returns:
        Logger instance
        
    Example:
        >>> log = get_logger(__name__)
        >>> log.info("Processing query", query="test", user_id=123)
    """
    if name:
        return logger.bind(module=name)
    return logger
