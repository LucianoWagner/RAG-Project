"""
LLM service for generating answers using Ollama.

This module handles communication with a local Ollama instance to generate
answers based on retrieved context from documents.
"""

import httpx
from typing import Optional

from app.utils.logger import logger


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

CONTEXT:
{context}

QUESTION: {question}

ANSWER:"""
        
        return prompt
    
    async def generate_answer(self, question: str, context: str) -> str:
        """
        Generate an answer using Ollama based on the provided context.
        
        Args:
            question: User's question
            context: Retrieved context from documents
            
        Returns:
            Generated answer text
            
        Raises:
            Exception: If Ollama request fails
        """
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
