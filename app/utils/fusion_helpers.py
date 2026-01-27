"""
Fusion algorithms for combining multiple search rankings.

This module implements Reciprocal Rank Fusion (RRF) for merging results
from different retrieval methods (e.g., BM25 and Vector Search).
"""

from typing import List, Tuple, Dict
from app.utils.logger import logger


def reciprocal_rank_fusion(
    results_a: List[Tuple[str, float]],
    results_b: List[Tuple[str, float]],
    k: int = 60
) -> List[Tuple[str, float]]:
    """
    Combine two ranked lists using Reciprocal Rank Fusion (RRF).
    
    RRF is a simple yet effective algorithm for merging rankings from different
    retrieval methods. It assigns a score to each document based on its rank
    position in each list, then sums these scores.
    
    Formula:
        RRF_score(doc) = sum(1 / (rank_i + k)) for all lists i
    
    Where:
        - rank_i: Position of document in list i (0-indexed)
        - k: Constant (default 60, based on academic research)
    
    Args:
        results_a: First ranking as list of (doc_id, score) tuples
        results_b: Second ranking as list of (doc_id, score) tuples
        k: RRF constant parameter (default 60)
    
    Returns:
        List of (doc_id, rrf_score) tuples, sorted by RRF score (descending)
    
    Example:
        >>> bm25_results = [("doc_A", 0.95), ("doc_B", 0.67), ("doc_C", 0.10)]
        >>> vector_results = [("doc_C", 0.88), ("doc_A", 0.82), ("doc_B", 0.45)]
        >>> fused = reciprocal_rank_fusion(bm25_results, vector_results, k=60)
        >>> print(fused)
        [("doc_A", 0.03252), ("doc_C", 0.03226), ("doc_B", 0.03200)]
        # doc_A wins because it's top in BM25 and 2nd in Vector (consistent)
    
    References:
        - Cormack, G. V., Clarke, C. L., & Buettcher, S. (2009). "Reciprocal rank
          fusion outperforms condorcet and individual rank learning methods."
          SIGIR '09.
    """
    logger.debug(f"Applying RRF with k={k} to {len(results_a)} and {len(results_b)} results")
    
    # Dictionary to accumulate RRF scores
    rrf_scores: Dict[str, float] = {}
    
    # Process first ranking (results_a)
    for rank, (doc_id, _) in enumerate(results_a):
        # RRF contribution: 1 / (rank + k)
        # rank starts at 0, so position 1 is rank 0
        contribution = 1.0 / (rank + k)
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + contribution
        logger.debug(f"  List A: doc={doc_id}, rank={rank}, contribution={contribution:.5f}")
    
    # Process second ranking (results_b)
    for rank, (doc_id, _) in enumerate(results_b):
        contribution = 1.0 / (rank + k)
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + contribution
        logger.debug(f"  List B: doc={doc_id}, rank={rank}, contribution={contribution:.5f}")
    
    # Sort by RRF score (descending)
    sorted_results = sorted(
        rrf_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    logger.info(f"RRF fusion complete: {len(sorted_results)} unique documents ranked")
    
    return sorted_results


def reciprocal_rank_fusion_with_metadata(
    results_a: List[Dict],
    results_b: List[Dict],
    id_key: str = "chunk_id",
    k: int = 60
) -> List[Dict]:
    """
    RRF variant that preserves document metadata.
    
    Similar to reciprocal_rank_fusion() but works with full document
    dictionaries instead of simple (id, score) tuples.
    
    Args:
        results_a: First ranking as list of document dicts
        results_b: Second ranking as list of document dicts
        id_key: Key in dict to use as document ID (default: "chunk_id")
        k: RRF constant parameter (default 60)
    
    Returns:
        List of document dicts with added "rrf_score" field, sorted by RRF score
    
    Example:
        >>> bm25_results = [
        ...     {"chunk_id": 1, "text": "...", "bm25_score": 0.95},
        ...     {"chunk_id": 2, "text": "...", "bm25_score": 0.67}
        ... ]
        >>> vector_results = [
        ...     {"chunk_id": 2, "text": "...", "vector_score": 0.88},
        ...     {"chunk_id": 1, "text": "...", "vector_score": 0.82}
        ... ]
        >>> fused = reciprocal_rank_fusion_with_metadata(bm25_results, vector_results)
        >>> print(fused[0])
        {"chunk_id": 1, "text": "...", "rrf_score": 0.03252, ...}
    """
    logger.debug(f"Applying RRF with metadata preservation (id_key={id_key})")
    
    # Build mapping from doc_id to full metadata
    metadata_map: Dict[str, Dict] = {}
    
    # Collect metadata from both lists
    for doc in results_a + results_b:
        doc_id = doc.get(id_key)
        if doc_id is not None and doc_id not in metadata_map:
            metadata_map[doc_id] = doc.copy()
    
    # Extract simple (id, score) tuples for RRF
    tuples_a = [(doc.get(id_key), 0.0) for doc in results_a if doc.get(id_key) is not None]
    tuples_b = [(doc.get(id_key), 0.0) for doc in results_b if doc.get(id_key) is not None]
    
    # Apply RRF
    fused_scores = reciprocal_rank_fusion(tuples_a, tuples_b, k=k)
    
    # Reconstruct full documents with RRF scores
    results = []
    for doc_id, rrf_score in fused_scores:
        if doc_id in metadata_map:
            doc = metadata_map[doc_id].copy()
            doc["rrf_score"] = rrf_score
            results.append(doc)
    
    logger.info(f"RRF with metadata complete: {len(results)} documents")
    
    return results
