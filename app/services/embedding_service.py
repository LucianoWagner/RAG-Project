"""
Embedding generation service.

This module handles generating vector embeddings for text using sentence-transformers.
The embeddings are used for semantic similarity search in the vector store.
"""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer

from app.utils.logger import logger


class EmbeddingService:
    """
    Service for generating text embeddings using sentence-transformers.
    
    Uses the specified model (default: all-MiniLM-L6-v2) which provides:
    - Good quality embeddings
    - Fast inference
    - Small model size (~80MB)
    - 384-dimensional vectors
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service with the specified model.
        
        Args:
            model_name: Name of the sentence-transformer model to use
        """
        self.model_name = model_name
        self.model = None
        logger.info(f"EmbeddingService initialized with model: {model_name}")
    
    def _ensure_model_loaded(self):
        """Lazy load the model on first use to save startup time."""
        if self.model is None:
            logger.info(f"Loading embedding model: {self.model_name}")
            try:
                self.model = SentenceTransformer(self.model_name)
                logger.info(
                    f"Model loaded successfully. "
                    f"Embedding dimension: {self.model.get_sentence_embedding_dimension()}"
                )
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                raise
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            NumPy array of embeddings, shape (len(texts), embedding_dim)
            
        Raises:
            ValueError: If texts list is empty
        """
        if not texts:
            logger.error("Cannot generate embeddings for empty text list")
            raise ValueError("texts list cannot be empty")
        
        self._ensure_model_loaded()
        
        logger.info(f"Generating embeddings for {len(texts)} texts")
        
        try:
            # Generate embeddings (batch processing for efficiency)
            embeddings = self.model.encode(
                texts,
                show_progress_bar=False,  # Disable for cleaner logs
                convert_to_numpy=True
            )
            
            logger.info(
                f"Generated {len(embeddings)} embeddings, "
                f"shape: {embeddings.shape}"
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query text.
        
        Args:
            query: Query text to embed
            
        Returns:
            NumPy array representing the query embedding
            
        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            logger.error("Cannot generate embedding for empty query")
            raise ValueError("Query cannot be empty")
        
        self._ensure_model_loaded()
        
        logger.info(f"Generating embedding for query: '{query[:50]}...'")
        
        try:
            embedding = self.model.encode(
                [query],  # Model expects a list
                show_progress_bar=False,
                convert_to_numpy=True
            )[0]  # Return first (and only) embedding
            
            logger.debug(f"Query embedding shape: {embedding.shape}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this model.
        
        Returns:
            Embedding dimension (e.g., 384 for all-MiniLM-L6-v2)
        """
        self._ensure_model_loaded()
        return self.model.get_sentence_embedding_dimension()
    
    def is_model_loaded(self) -> bool:
        """
        Check if the embedding model is currently loaded.
        
        Returns:
            True if model is loaded, False otherwise
        """
        return self.model is not None
