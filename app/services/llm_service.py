"""
LLM service for generating answers using Ollama.

This module handles communication with a local Ollama instance to generate
answers based on retrieved context from documents.

NEW: Integrated resilience patterns:
- Circuit breaker: Fail-fast when Ollama is down
- Retry with exponential backoff: Handle transient failures
- Timeout: Prevent hanging requests
"""

import httpx
from typing import Optional

from app.utils.logger import logger
from app.utils.resilience import (
    with_circuit_breaker,
    with_retry,
    with_timeout,
    ollama_breaker
)


class LLMService:
    """
    Service for generating answers using Ollama LLM.
    
    Communicates with Ollama's HTTP API to generate contextual answers.
    Uses careful prompt engineering to prevent hallucinations.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "mistral:7b"):
        """
        Initialize LLM service with Ollama configuration.
        
        Args:
            base_url: Base URL of Ollama API
            model: Model name to use (e.g., "mistral:7b", "llama3.2")
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.generate_url = f"{self.base_url}/api/generate"
        
        logger.info(f"LLMService initialized with base_url={base_url}, model={model}")
    
    async def check_health(self) -> bool:
        """
        Check if Ollama service is available.
        
        Returns:
            True if Ollama is accessible, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                is_healthy = response.status_code == 200
                
                if is_healthy:
                    logger.info("Ollama service is healthy")
                else:
                    logger.warning(f"Ollama returned status {response.status_code}")
                
                return is_healthy
                
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    def _build_prompt(self, question: str, context: str) -> str:
        """
        Build a prompt that instructs the LLM to use only the provided context.
        
        Args:
            question: User's question
            context: Retrieved context from documents
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided context from documents.

IMPORTANT RULES:
1. Only use information from the CONTEXT below to answer the question
2. If the context does not contain enough information to answer the question, say "I cannot answer this question based on the provided documents."
3. Do not use external knowledge or make assumptions
4. Be concise and direct
5. Quote relevant parts of the context when appropriate
6. If the user's question includes a greeting (like "hola", "buenos días", "hi", etc.), start your response with a polite greeting as well (e.g., "¡Hola! ..." or "¡Buenos días! ...")

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
        
        return prompt
    
    @with_retry(max_attempts=3, min_wait=1, max_wait=5, exceptions=(httpx.RequestError, httpx.TimeoutException))
    @with_timeout(30)  # 30s timeout for LLM generation
    async def generate_answer(self, question: str, context: str) -> str:
        """
        Generate an answer using Ollama based on the provided context.
        
        Resilience patterns applied:
        - Circuit breaker: Fails fast if Ollama is consistently down
        - Retry: Up to 3 attempts with exponential backoff (1s, 2s, 4s)
        - Timeout: Cancels after 30 seconds
        
        Args:
            question: User's question
            context: Retrieved context from documents
            
        Returns:
            Generated answer text
            
        Raises:
            CircuitBreakerError: If circuit breaker is open
            TimeoutError: If request exceeds 30s
            Exception: If all retry attempts fail
        """
        # Check circuit breaker state first
        from pybreaker import CircuitBreakerError
        if ollama_breaker.current_state == "open":
            logger.error(f"Circuit breaker {ollama_breaker.name} is OPEN")
            raise CircuitBreakerError(ollama_breaker)
        
        prompt = self._build_prompt(question, context)
        
        logger.info(f"Generating answer for question: '{question[:50]}...'")
        logger.debug(f"Context length: {len(context)} characters")
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,  # Get complete response at once
            "options": {
                "temperature": 0.1,  # Low temperature for more factual responses
                "top_p": 0.9,
                "num_predict": 256  # Max tokens to generate
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    self.generate_url,
                    json=payload
                )
                
                if response.status_code != 200:
                    error_msg = f"Ollama API returned status {response.status_code}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                
                result = response.json()
                answer = result.get("response", "").strip()
                
                logger.info(f"Generated answer: '{answer[:100]}...'")
                logger.debug(
                    f"Ollama stats: "
                    f"total_duration={result.get('total_duration', 0) / 1e9:.2f}s, "
                    f"eval_count={result.get('eval_count', 0)}"
                )
                
                return answer
                
        except httpx.TimeoutException:
            logger.error("Ollama request timed out")
            raise Exception("LLM request timed out. Please try again.")
        except httpx.RequestError as e:
            logger.error(f"Ollama request failed: {e}")
            raise Exception(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            raise
    
    async def generate_answer_no_context(self) -> str:
        """
        Generate a standard response when no relevant context is found.
        
        Returns:
            Standard "no information" message
        """
        return (
            "I cannot answer this question based on the provided documents. "
            "The documents do not contain relevant information about your query. "
            "Please try rephrasing your question or upload additional documents."
        )
    
    @with_retry(max_attempts=2, min_wait=1, max_wait=3, exceptions=(httpx.RequestError,))
    @with_timeout(15)  # Shorter timeout for greetings
    async def generate_greeting_response(self, greeting_text: str) -> str:
        """
        Generate a personalized, friendly greeting response using LLM.
        
        Resilience patterns applied:
        - Circuit breaker: Shares state with generate_answer
        - Retry: 2 attempts (less critical than answers)
        - Timeout: 15s (greetings should be fast)
        
        Args:
            greeting_text: The user's greeting message
            
        Returns:
            Friendly, natural greeting response
        """
        # Check circuit breaker state first - fallback if open
        if ollama_breaker.current_state == "open":
            logger.warning(f"Circuit breaker is OPEN, using fallback greeting")
            return "¡Hola! ¿En qué puedo ayudarte hoy?"
        
        prompt = f"""You are a friendly AI assistant. Respond to this greeting in a natural, warm way.
Keep your response brief (1-2 sentences) and helpful.

User: {greeting_text}

Assistant:"""
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,  # Higher temperature for more natural greetings
                "top_p": 0.9,
                "num_predict": 50  # Short response
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.generate_url,
                    json=payload
                )
                
                if response.status_code != 200:
                    # Fallback to static greeting if LLM fails
                    return "¡Hola! ¿En qué puedo ayudarte hoy?"
                
                result = response.json()
                answer = result.get("response", "").strip()
                
                return answer if answer else "¡Hola! ¿En qué puedo ayudarte hoy?"
                
        except Exception as e:
            logger.warning(f"Greeting generation failed, using fallback: {e}")
            return "¡Hola! ¿En qué puedo ayudarte hoy?"
