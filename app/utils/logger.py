"""
Logging configuration for RAG PDF System.

Provides a centralized logger with formatted output for debugging and monitoring.
"""

import logging
import sys


def setup_logger(name: str = "rag_system") -> logging.Logger:
    """
    Configure and return a logger instance with formatted output.
    
    Args:
        name: Logger name, defaults to "rag_system"
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler with formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Format: timestamp - name - level - message
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger()
