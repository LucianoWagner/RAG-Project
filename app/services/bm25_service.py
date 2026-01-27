"""
BM25 search service for keyword-based document retrieval.

This module implements BM25 (Best Matching 25), a ranking function used by search
engines to estimate the relevance of documents based on keyword frequency and
document statistics.
"""

from typing import List, Dict, Optional
import pickle
from pathlib import Path
from rank_bm25 import BM25Okapi

from app.utils.logger import logger


class BM25Service:
    """
    BM25-based keyword search service.
    
    BM25 is a probabilistic ranking function that ranks documents based on:
    - Term frequency (TF): How often query terms appear in the document
    - Inverse document frequency (IDF): How rare/common terms are across corpus
    - Document length normalization: Prevents bias towards longer documents
    
    Use cases:
    - Exact keyword matching (e.g., "function_name", "error code")
    - Technical terms and proper nouns
    - Complement to semantic/vector search
    """
    
    def __init__(self, index_path: Optional[Path] = None):
        """
        Initialize BM25 service.
        
        Args:
            index_path: Optional path to load existing index from
        """
        self.index: Optional[BM25Okapi] = None
        self.documents: List[str] = []  # Store original document texts
        self.metadata: List[Dict] = []  # Store document metadata
        self.index_path = index_path
        
        # Load existing index if available
        if index_path and (index_path / "bm25.pkl").exists():
            self.load_index(index_path)
        else:
            logger.info("Initialized empty BM25 service")
    
    def add_documents(
        self,
        texts: List[str],
        metadata: List[Dict]
    ) -> int:
        """
        Add documents to the BM25 index.
        
        Args:
            texts: List of document texts
            metadata: List of metadata dicts corresponding to texts
        
        Returns:
            Number of documents added
        
        Raises:
            ValueError: If texts and metadata have different lengths
        """
        if len(texts) != len(metadata):
            logger.error(f"Mismatch: {len(texts)} texts but {len(metadata)} metadata entries")
            raise ValueError("Number of texts must match number of metadata entries")
        
        # Store documents and metadata
        self.documents.extend(texts)
        self.metadata.extend(metadata)
        
        # Tokenize documents (simple split by whitespace)
        # For production, consider: lowercasing, stemming, stopword removal
        tokenized_corpus = [doc.lower().split() for doc in self.documents]
        
        # Create BM25 index
        self.index = BM25Okapi(tokenized_corpus)
        
        logger.info(
            f"Added {len(texts)} documents to BM25 index. "
            f"Total documents: {len(self.documents)}"
        )
        
        return len(texts)
    
    def search(self, query: str, k: int = 10) -> List[Dict]:
        """
        Search for top-k documents using BM25 scoring.
        
        Args:
            query: Search query string
            k: Number of top results to return
        
        Returns:
            List of dicts with keys: original metadata + 'bm25_score'
            Sorted by BM25 score (descending, higher = more relevant)
        
        Raises:
            ValueError: If index is empty
        """
        if self.index is None or len(self.documents) == 0:
            logger.warning("Cannot search: BM25 index is empty")
            raise ValueError("BM25 index is empty. Please add documents first.")
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        logger.info(f"BM25 search for query: '{query}' (top {k})")
        
        # Get BM25 scores for all documents
        scores = self.index.get_scores(tokenized_query)
        
        # Get top-k indices
        top_k = min(k, len(scores))
        top_indices = scores.argsort()[-top_k:][::-1]  # Descending order
        
        # Build results with metadata
        results = []
        for idx in top_indices:
            result = self.metadata[idx].copy()  # Copy metadata
            result['bm25_score'] = float(scores[idx])  # Add BM25 score
            results.append(result)
            logger.debug(
                f"  BM25 result: score={scores[idx]:.4f}, "
                f"text='{self.documents[idx][:50]}...'"
            )
        
        logger.info(f"BM25 search complete: returned {len(results)} results")
        
        return results
    
    def save_index(self, save_path: Path):
        """
        Save BM25 index and metadata to disk.
        
        Args:
            save_path: Directory path to save index files
        """
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save everything in a single pickle file
        index_data = {
            'index': self.index,
            'documents': self.documents,
            'metadata': self.metadata
        }
        
        index_file = save_path / "bm25.pkl"
        with open(index_file, 'wb') as f:
            pickle.dump(index_data, f)
        
        logger.info(
            f"Saved BM25 index with {len(self.documents)} documents to {save_path}"
        )
    
    def load_index(self, load_path: Path):
        """
        Load BM25 index and metadata from disk.
        
        Args:
            load_path: Directory path containing index files
        
        Raises:
            FileNotFoundError: If index file doesn't exist
        """
        index_file = load_path / "bm25.pkl"
        
        if not index_file.exists():
            logger.error(f"BM25 index file not found: {index_file}")
            raise FileNotFoundError(f"BM25 index file not found: {index_file}")
        
        # Load from pickle
        with open(index_file, 'rb') as f:
            index_data = pickle.load(f)
        
        self.index = index_data['index']
        self.documents = index_data['documents']
        self.metadata = index_data['metadata']
        
        logger.info(
            f"Loaded BM25 index with {len(self.documents)} documents from {load_path}"
        )
    
    def clear(self):
        """Clear all documents and index."""
        self.index = None
        self.documents = []
        self.metadata = []
        logger.info("Cleared BM25 index")
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the BM25 index.
        
        Returns:
            Dictionary with index statistics
        """
        stats = {
            'total_documents': len(self.documents),
            'indexed': self.index is not None,
            'average_doc_length': (
                sum(len(doc.split()) for doc in self.documents) / len(self.documents)
                if self.documents else 0
            )
        }
        
        logger.debug(f"BM25 stats: {stats}")
        
        return stats
