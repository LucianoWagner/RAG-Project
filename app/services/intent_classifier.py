"""
Intent Classification Service for RAG System.

Provides intelligent query intent classification using a hybrid approach
combining regex patterns and semantic similarity.
"""

import numpy as np
from typing import Optional
from app.utils.logger import logger
from app.utils.intent_helpers import classify_intent_hybrid


class IntentClassifier:
    """
    Classifies user intents using pre-computed greeting embeddings.
    
    Supported intents:
    - GREETING: Casual greetings, introductions
    - DOCUMENT_QUERY: Questions about documents
    """
    
    # Example greetings for embedding (multiple languages & variations)
    GREETING_EXAMPLES = [
        "Hola",
        "Hi",
        "Hey",
        "Hello",
        "Buenos días",
        "Buenas tardes",
        "Buenas noches",
        "Good morning",
        "Good afternoon",
        "¿Cómo estás?",
        "¿Qué tal?",
        "How are you?",
        "What's up?",
        "Hey there",
        "Buenas",
    ]
    
    def __init__(self, embedding_service):
        """
        Initialize intent classifier with embedding service.
        
        Args:
            embedding_service: EmbeddingService instance for generating embeddings
        """
        self.embedding_service = embedding_service
        self.greeting_centroid: Optional[np.ndarray] = None
        self.similarity_threshold = 0.7  # Industry standard for semantic similarity
        
        logger.info("IntentClassifier initialized")
    
    def _ensure_greeting_centroid_loaded(self):
        """Lazy load greeting centroid embedding."""
        if self.greeting_centroid is None:
            logger.info(f"Computing greeting centroid from {len(self.GREETING_EXAMPLES)} examples")
            
            # Generate embeddings for all greeting examples
            greeting_embeddings = self.embedding_service.embed_texts(self.GREETING_EXAMPLES)
            
            # Compute centroid (mean) of all greeting embeddings
            self.greeting_centroid = np.mean(greeting_embeddings, axis=0)
            
            logger.info("Greeting centroid computed successfully")
    
    def classify(self, question: str, question_embedding: Optional[np.ndarray] = None) -> str:
        """
        Classify user intent using hybrid approach.
        
        Args:
            question: User's question text
            question_embedding: Optional pre-computed embedding (for performance)
        
        Returns:
            Intent string: "GREETING" or "DOCUMENT_QUERY"
        """
        # Ensure greeting centroid is loaded
        self._ensure_greeting_centroid_loaded()
        
        # Generate question embedding if not provided
        if question_embedding is None:
            question_embedding = self.embedding_service.embed_query(question)
        
        # Use hybrid classification
        intent = classify_intent_hybrid(
            question=question,
            question_embedding=question_embedding,
            greeting_centroid=self.greeting_centroid,
            similarity_threshold=self.similarity_threshold
        )
        
        logger.debug(f"Classified intent: '{intent}' for question: '{question[:50]}...'")
        
        return intent
    
    def is_greeting(self, question: str, question_embedding: Optional[np.ndarray] = None) -> bool:
        """
        Check if question is a greeting.
        
        Args:
            question: User's question
            question_embedding: Optional pre-computed embedding
            
        Returns:
            True if intent is GREETING
        """
        intent = self.classify(question, question_embedding)
        return intent == "GREETING"
