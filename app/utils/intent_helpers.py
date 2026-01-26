"""
Intent detection utilities for query classification.

This module provides fast intent classification using a hybrid approach:
1. Regex patterns for common/obvious greetings (fast path)
2. Semantic similarity with sentence embeddings (precise path)
"""

import re
from typing import Optional
import numpy as np

# Greeting patterns for fast detection (multiple languages)
GREETING_PATTERNS = [
    r'\b(hola|hi|hello|hey|buenos días|buenas tardes|buenas noches|buenas)\b',
    r'^(qué tal|cómo estás|cómo va|how are you|what\'s up|sup)',
    r'\b(good morning|good afternoon|good evening|buen día)\b',
]

# Pre-compiled patterns for performance
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in GREETING_PATTERNS]


def is_short_greeting_regex(text: str) -> bool:
    """
    Fast regex-based greeting detection for obvious cases.
    
    Only checks short phrases (<=5 words) to avoid false positives.
    
    Args:
        text: User input text
        
    Returns:
        True if text matches greeting patterns
    """
    text_clean = text.strip()
    word_count = len(text_clean.split())
    
    # Only apply regex to short phrases
    if word_count > 5:
        return False
    
    text_lower = text_clean.lower()
    
    # Check against compiled patterns
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text_lower):
            return True
    
    return False


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Similarity score between 0 and 1
    """
    dot_product = np.dot(vec1, vec2)
    norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
    
    if norm_product == 0:
        return 0.0
    
    return float(dot_product / norm_product)


def classify_intent_hybrid(
    question: str,
    question_embedding: np.ndarray,
    greeting_centroid: np.ndarray,
    similarity_threshold: float = 0.7
) -> str:
    """
    Hybrid intent classification using regex + semantic similarity.
    
    Process:
    1. Fast path: Check regex patterns (0ms)
    2. Semantic path: Compare with greeting embeddings (already computed)
    3. Default: Assume document query
    
    Args:
        question: User's question
        question_embedding: Pre-computed embedding of the question
        greeting_centroid: Pre-computed centroid of greeting examples
        similarity_threshold: Threshold for greeting similarity (default: 0.7)
        
    Returns:
        Intent string: "GREETING" or "DOCUMENT_QUERY"
    """
    # FAST PATH: Regex for obvious greetings
    if is_short_greeting_regex(question):
        return "GREETING"
    
    # SEMANTIC PATH: Similarity with greeting examples
    similarity = cosine_similarity(question_embedding, greeting_centroid)
    
    if similarity >= similarity_threshold:
        return "GREETING"
    
    # DEFAULT: Assume document query
    return "DOCUMENT_QUERY"
