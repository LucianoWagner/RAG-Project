"""
Text chunking service.

This module handles splitting large text documents into smaller, overlapping chunks
for efficient embedding and retrieval. The overlap ensures context is preserved
across chunk boundaries.
"""

from typing import List
from app.utils.logger import logger


class ChunkingService:
    """
    Service for splitting text into overlapping chunks.
    
    The chunking strategy uses character-based splitting with configurable
    chunk size and overlap to maintain context continuity.
    """
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Initialize chunking service with configuration.
        
        Args:
            chunk_size: Maximum number of characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        logger.info(
            f"ChunkingService initialized with chunk_size={chunk_size}, "
            f"overlap={chunk_overlap}"
        )
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: Text to split
            
        Returns:
            List of text chunks
            
        Raises:
            ValueError: If text is empty or chunk_size is invalid
        """
        if not text or not text.strip():
            logger.error("Cannot chunk empty text")
            raise ValueError("Text cannot be empty")
        
        if self.chunk_size <= 0:
            logger.error(f"Invalid chunk_size: {self.chunk_size}")
            raise ValueError("chunk_size must be positive")
        
        if self.chunk_overlap >= self.chunk_size:
            logger.error(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
            raise ValueError("chunk_overlap must be less than chunk_size")
        
        # Clean the text
        text = text.strip()
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Calculate end position for this chunk
            end = start + self.chunk_size
            
            # Extract chunk
            chunk = text[start:end].strip()
            
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
            
            # Move to next chunk with overlap
            # For last chunk, this will exceed text length and loop will exit
            start += self.chunk_size - self.chunk_overlap
        
        logger.info(
            f"Split text ({len(text)} chars) into {len(chunks)} chunks"
        )
        
        return chunks
    
    def get_chunk_stats(self, chunks: List[str]) -> dict:
        """
        Get statistics about a list of chunks.
        
        Args:
            chunks: List of text chunks
            
        Returns:
            Dictionary with chunk statistics
        """
        if not chunks:
            return {
                "total_chunks": 0,
                "avg_length": 0,
                "min_length": 0,
                "max_length": 0
            }
        
        lengths = [len(chunk) for chunk in chunks]
        
        stats = {
            "total_chunks": len(chunks),
            "avg_length": sum(lengths) / len(lengths),
            "min_length": min(lengths),
            "max_length": max(lengths)
        }
        
        logger.debug(f"Chunk statistics: {stats}")
        
        return stats
