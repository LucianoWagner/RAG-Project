"""
Hybrid Search Service combining BM25 and Vector Search with RRF.

This service orchestrates search across multiple retrieval methods:
- BM25: Keyword-based search (good for technical terms, proper nouns)
- Vector Search: Semantic similarity (good for synonyms, context)
- RRF: Reciprocal Rank Fusion to combine both rankings
"""

from typing import List, Dict
import numpy as np

from app.services.bm25_service import BM25Service
from app.services.vector_store import VectorStore
from app.services.embedding_service import EmbeddingService
from app.utils.fusion_helpers import reciprocal_rank_fusion_with_metadata
from app.utils.logger import logger


class HybridSearchService:
    """
    Orchestrates hybrid search combining BM25 and Vector Search.
    
    Workflow:
    1. BM25 Search: Get top-10 results by keyword matching
    2. Vector Search: Get top-10 results by semantic similarity
    3. RRF Fusion: Combine rankings using Reciprocal Rank Fusion
    4. Return: Top-K fused results
    """
    
    def __init__(
        self,
        bm25_service: BM25Service,
        vector_store: VectorStore,
        embedding_service: EmbeddingService,
        rrf_k: int = 60
    ):
        """
        Initialize hybrid search service.
        
        Args:
            bm25_service: BM25 keyword search service
            vector_store: FAISS vector store
            embedding_service: Service for generating query embeddings
            rrf_k: RRF algorithm parameter (default 60)
        """
        self.bm25 = bm25_service
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.rrf_k = rrf_k
        
        logger.info(f"Initialized HybridSearchService with RRF k={rrf_k}")
    
    def search(
        self,
        query: str,
        k: int = 3,
        bm25_candidates: int = 10,
        vector_candidates: int = 10
    ) -> List[Dict]:
        """
        Perform hybrid search combining BM25 and Vector Search.
        
        Args:
            query: Search query string
            k: Number of final results to return
            bm25_candidates: Number of BM25 results to retrieve (before fusion)
            vector_candidates: Number of vector results to retrieve (before fusion)
        
        Returns:
            List of dicts with keys: 'text', 'source', 'chunk_id', 'score', 'rrf_score'
            Sorted by RRF score (descending)
        
        Raises:
            ValueError: If both indices are empty
        """
        logger.info(
            f"Hybrid search: query='{query}', k={k}, "
            f"bm25_candidates={bm25_candidates}, vector_candidates={vector_candidates}"
        )
        
        # Check if indices are empty
        if self.vector_store.index.ntotal == 0 and len(self.bm25.documents) == 0:
            logger.error("Both BM25 and Vector indices are empty")
            raise ValueError("No documents indexed. Please upload documents first.")
        
        # 1. BM25 Search
        bm25_results = []
        if len(self.bm25.documents) > 0:
            try:
                bm25_results = self.bm25.search(query, k=bm25_candidates)
                logger.info(f"BM25 returned {len(bm25_results)} candidates")
            except Exception as e:
                logger.warning(f"BM25 search failed: {e}")
        else:
            logger.warning("BM25 index is empty, skipping BM25 search")
        
        # 2. Vector Search  
        vector_results = []
        if self.vector_store.index.ntotal > 0:
            try:
                # Generate query embedding
                query_embedding = self.embedding_service.embed_query(query)
                vector_results = self.vector_store.search(query_embedding, k=vector_candidates)
                logger.info(f"Vector search returned {len(vector_results)} candidates")
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        else:
            logger.warning("Vector store is empty, skipping vector search")
        
        # 3. Handle edge cases
        if not bm25_results and not vector_results:
            logger.error("Both searches returned no results")
            return []
        
        if not bm25_results:
            logger.info("Only vector results available, returning top-k from vector search")
            return vector_results[:k]
        
        if not vector_results:
            logger.info("Only BM25 results available, returning top-k from BM25")
            # Rename bm25_score to score for consistency
            for result in bm25_results:
                result['score'] = result.get('bm25_score', 0.0)
            return bm25_results[:k]
        
        # 4. Apply RRF Fusion
        logger.info("Applying RRF fusion to combine BM25 and Vector results")
        fused_results = reciprocal_rank_fusion_with_metadata(
            results_a=bm25_results,
            results_b=vector_results,
            id_key="chunk_id",
            k=self.rrf_k
        )
        
        # 5. Normalize score field
        # Keep both original scores and RRF score
        for result in fused_results:
            # Use RRF score as main score
            result['score'] = result.get('rrf_score', 0.0)
        
        # 6. Return top-k
        final_results = fused_results[:k]
        
        logger.info(
            f"Hybrid search complete: returned {len(final_results)} fused results "
            f"(from {len(bm25_results)} BM25 + {len(vector_results)} vector candidates)"
        )
        
        return final_results
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the hybrid search service.
        
        Returns:
            Dictionary with service statistics
        """
        stats = {
            'bm25': self.bm25.get_stats(),
            'vector': self.vector_store.get_stats(),
            'rrf_k': self.rrf_k
        }
        
        logger.debug(f"Hybrid search stats: {stats}")
        
        return stats
