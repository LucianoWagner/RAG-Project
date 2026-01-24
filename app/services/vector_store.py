"""
Vector store service using FAISS.

This module manages the FAISS vector index for storing and retrieving
document embeddings. FAISS provides efficient similarity search at scale.
"""

from typing import List, Dict, Optional
import numpy as np
import faiss
import pickle
from pathlib import Path

from app.utils.logger import logger


class VectorStore:
    """
    Vector store using FAISS for efficient similarity search.
    
    Manages:
    - FAISS index for vector similarity search
    - Metadata storage for chunk texts and sources
    - Persistence to disk
    """
    
    def __init__(self, dimension: int, index_path: Optional[Path] = None):
        """
        Initialize vector store with the specified embedding dimension.
        
        Args:
            dimension: Dimension of embeddings (e.g., 384 for all-MiniLM-L6-v2)
            index_path: Optional path to load existing index from
        """
        self.dimension = dimension
        self.index_path = index_path
        
        # Initialize FAISS index (L2 distance for similarity)
        self.index = faiss.IndexFlatL2(dimension)
        
        # Store metadata for each vector
        # List of dicts with keys: 'text', 'source', 'chunk_id'
        self.metadata: List[Dict] = []
        
        # Load existing index if path is provided and files exist
        if index_path and (index_path / "faiss.index").exists():
            self.load_index(index_path)
        else:
            logger.info(f"Initialized new FAISS index with dimension {dimension}")
    
    def add_documents(
        self,
        embeddings: np.ndarray,
        texts: List[str],
        source: str
    ) -> int:
        """
        Add document chunks to the vector store.
        
        Args:
            embeddings: NumPy array of embeddings, shape (n, dimension)
            texts: List of text chunks corresponding to embeddings
            source: Source document name/path
            
        Returns:
            Number of chunks added
            
        Raises:
            ValueError: If embeddings and texts have different lengths
        """
        if len(embeddings) != len(texts):
            logger.error(
                f"Mismatch: {len(embeddings)} embeddings but {len(texts)} texts"
            )
            raise ValueError("Number of embeddings must match number of texts")
        
        if embeddings.shape[1] != self.dimension:
            logger.error(
                f"Embedding dimension {embeddings.shape[1]} doesn't match "
                f"index dimension {self.dimension}"
            )
            raise ValueError(
                f"Embedding dimension must be {self.dimension}, "
                f"got {embeddings.shape[1]}"
            )
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        # Add metadata
        start_id = len(self.metadata)
        for i, text in enumerate(texts):
            self.metadata.append({
                'text': text,
                'source': source,
                'chunk_id': start_id + i
            })
        
        logger.info(
            f"Added {len(texts)} chunks from '{source}' to vector store. "
            f"Total vectors: {self.index.ntotal}"
        )
        
        return len(texts)
    
    def search(self, query_embedding: np.ndarray, k: int = 3) -> List[Dict]:
        """
        Search for the k most similar chunks to the query.
        
        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            
        Returns:
            List of dicts with keys: 'text', 'source', 'chunk_id', 'score'
            Sorted by similarity (lower score = more similar for L2 distance)
            
        Raises:
            ValueError: If vector store is empty
        """
        if self.index.ntotal == 0:
            logger.warning("Cannot search: vector store is empty")
            raise ValueError("Vector store is empty. Please upload documents first.")
        
        # Ensure query is the right shape and type
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        query_embedding = query_embedding.astype('float32')
        
        # Limit k to available vectors
        k = min(k, self.index.ntotal)
        
        logger.info(f"Searching for top {k} similar chunks")
        
        # Search FAISS index
        # distances: L2 distances (lower = more similar)
        # indices: indices of the nearest neighbors
        distances, indices = self.index.search(query_embedding, k)
        
        # Build results
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.metadata):  # Safety check
                result = {
                    **self.metadata[idx],  # Include all metadata
                    'score': float(distance)  # Add similarity score
                }
                results.append(result)
                logger.debug(
                    f"Result {i+1}: score={distance:.4f}, "
                    f"text='{result['text'][:50]}...'"
                )
        
        logger.info(f"Found {len(results)} results")
        
        return results
    
    def save_index(self, save_path: Path):
        """
        Save FAISS index and metadata to disk.
        
        Args:
            save_path: Directory path to save index files
        """
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = save_path / "faiss.index"
        faiss.write_index(self.index, str(index_file))
        
        # Save metadata
        metadata_file = save_path / "metadata.pkl"
        with open(metadata_file, 'wb') as f:
            pickle.dump(self.metadata, f)
        
        logger.info(
            f"Saved vector store with {self.index.ntotal} vectors to {save_path}"
        )
    
    def load_index(self, load_path: Path):
        """
        Load FAISS index and metadata from disk.
        
        Args:
            load_path: Directory path containing index files
            
        Raises:
            FileNotFoundError: If index files don't exist
        """
        index_file = load_path / "faiss.index"
        metadata_file = load_path / "metadata.pkl"
        
        if not index_file.exists() or not metadata_file.exists():
            logger.error(f"Index files not found in {load_path}")
            raise FileNotFoundError(f"Index files not found in {load_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(str(index_file))
        
        # Load metadata
        with open(metadata_file, 'rb') as f:
            self.metadata = pickle.load(f)
        
        logger.info(
            f"Loaded vector store with {self.index.ntotal} vectors from {load_path}"
        )
    
    def clear(self):
        """Clear all vectors and metadata from the store."""
        self.index.reset()
        self.metadata = []
        logger.info("Cleared vector store")
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with store statistics
        """
        stats = {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'total_chunks': len(self.metadata),
            'sources': list(set(m['source'] for m in self.metadata))
        }
        
        logger.debug(f"Vector store stats: {stats}")
        
        return stats
