"""
Web Search Service for RAG System using Wikipedia.

Provides web search fallback using Wikipedia API when documents don't contain
relevant information. Results are summarized using the LLM for coherent answers.

NEW: Integrated resilience patterns:
- Timeout: Prevent hanging Wikipedia API calls
- Retry: Handle transient network failures
"""

from typing import List, Dict, Optional
import wikipedia
from app.utils.logger import logger
from app.utils.resilience import with_timeout, with_retry


class WebSearchService:
    """
    Service for searching Wikipedia and summarizing results.
    
    Uses Wikipedia API (free, no rate limits) for searches and integrates
    with LLM service for result summarization.
    """
    
    def __init__(self, llm_service):
        """
        Initialize web search service.
        
        Args:
            llm_service: LLMService instance for summarizing search results
        """
        self.llm_service = llm_service
        # Set language to Spanish for better results
        wikipedia.set_lang("es")
        logger.info("WebSearchService initialized with Wikipedia API")
    
    @with_timeout(20)  # Wikipedia should respond in 20s max
    @with_retry(max_attempts=2, min_wait=1, max_wait=3, exceptions=(Exception,))
    def search(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        """
        Search Wikipedia for relevant articles.
        
        Resilience patterns:
        - Timeout: 20s max for Wikipedia API
        - Retry: 2 attempts for network failures
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 2 for speed)
            
        Returns:
            List of search results with title, snippet, and link
        """
        try:
            logger.info(f"Searching Wikipedia for: '{query}'")
            
            # Search for pages
            search_results = wikipedia.search(query, results=max_results)
            
            if not search_results:
                logger.warning(f"No Wikipedia results found for: '{query}'")
                # Try in English as fallback
                wikipedia.set_lang("en")
                search_results = wikipedia.search(query, results=max_results)
                wikipedia.set_lang("es")  # Reset to Spanish
                
                if not search_results:
                    return []
            
            logger.info(f"Found {len(search_results)} Wikipedia articles")
            
            # Get summaries for each result
            formatted_results = []
            for title in search_results:
                try:
                    # Get page summary (3 sentences for better coverage)
                    summary = wikipedia.summary(title, sentences=3, auto_suggest=False)
                    page = wikipedia.page(title, auto_suggest=False)
                    
                    # Clean summary from special characters
                    summary = summary.replace('\u200b', '').replace('\xa0', ' ')
                    
                    formatted_results.append({
                        'title': title,
                        'snippet': summary,
                        'link': page.url
                    })
                    
                    logger.debug(f"Retrieved article: {title}")
                    
                except UnicodeEncodeError as ue:
                    # Handle encoding issues
                    logger.warning(f"Encoding error for '{title}', trying alternative method")
                    try:
                        # Try getting content directly
                        page = wikipedia.page(title, auto_suggest=False)
                        # Take first paragraph from content
                        content = page.content.replace('\u200b', '').replace('\xa0', ' ')
                        paragraphs = content.split('\n\n')
                        snippet = paragraphs[0] if paragraphs else content[:300]
                        
                        formatted_results.append({
                            'title': title,
                            'snippet': snippet,
                            'link': page.url
                        })
                        logger.debug(f"Retrieved article (alternative): {title}")
                    except Exception:
                        continue
                    
                except wikipedia.exceptions.DisambiguationError as e:
                    # Multiple options exist, take the first one
                    logger.debug(f"Disambiguation for '{title}', using first option")
                    try:
                        first_option = e.options[0]
                        summary = wikipedia.summary(first_option, sentences=2, auto_suggest=False)
                        page = wikipedia.page(first_option, auto_suggest=False)
                        
                        formatted_results.append({
                            'title': first_option,
                            'snippet': summary,
                            'link': page.url
                        })
                    except Exception:
                        continue
                        
                except wikipedia.exceptions.PageError:
                    logger.debug(f"Page not found: {title}")
                    continue
                    
                except Exception as e:
                    logger.warning(f"Error fetching '{title}': {e}")
                    continue
            
            logger.info(f"Successfully retrieved {len(formatted_results)} Wikipedia articles")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Wikipedia search failed: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return []
    
    @with_timeout(60)  # 60s total for search + LLM summarization
    async def search_and_summarize(self, question: str, max_results: int = 2) -> str:
        """
        Search Wikipedia and summarize results using LLM.
        
        Resilience:
        - Timeout: 60s total (search + LLM generation)
        - Fallback: Returns raw Wikipedia snippets if LLM fails
        
        Args:
            question: User's original question
            max_results: Number of search results to use (default: 2 for speed)
            
        Returns:
            Summarized answer based on Wikipedia search results
        """
        # Perform search
        results = self.search(question, max_results=max_results)
        
        if not results:
            return (
                "No encontré información relevante en Wikipedia. "
                "Esto puede deberse a que el tema es muy específico o reciente. "
                "Por favor, intenta reformular tu pregunta o sube documentos relacionados."
            )
        
        # Build context from search results
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"Artículo {i}: {result['title']}\n"
                f"{result['snippet']}\n"
                f"Fuente: {result['link']}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Build optimized prompt for LLM
        prompt = f"""Actúa como un asistente experto en resumir información de Wikipedia de forma precisa y completa.

CONTEXTO DE WIKIPEDIA:
{context}

TU TAREA:
Responde la pregunta del usuario basándote EXCLUSIVAMENTE en la información proporcionada arriba.

REGLAS OBLIGATORIAS:
1. Solo usa información que aparezca explícitamente en los artículos de Wikipedia
2. Si Wikipedia contradice lo que crees saber, confía en Wikipedia
3. Incluye detalles específicos: fechas, nombres completos, lugares, cantidades, resultados
4. Estructura tu respuesta en 3-5 oraciones completas y bien conectadas
5. Sé informativo pero directo - evita relleno innecesario
6. NUNCA inventes, especules o agregues información externa

PREGUNTA DEL USUARIO:
{question}

Proporciona una respuesta detallada y precisa:"""
        
        # Generate summarized answer
        payload = {
            "model": self.llm_service.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.15,  # Very low to stick to Wikipedia content
                "top_p": 0.9,
                "num_predict": 300  # Increased for more detailed responses
            }
        }
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(
                    self.llm_service.generate_url,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"LLM summarization failed with status {response.status_code}")
                    # Fallback: return raw snippets
                    return self._format_raw_results(results, question)
                
                result = response.json()
                answer = result.get("response", "").strip()
                
                if not answer:
                    return self._format_raw_results(results, question)
                
                logger.info("Successfully summarized Wikipedia results")
                return answer
                
        except Exception as e:
            logger.error(f"Error summarizing results: {e}")
            return self._format_raw_results(results, question)
    
    def _format_raw_results(self, results: List[Dict[str, str]], question: str) -> str:
        """
        Format raw search results when LLM summarization fails.
        
        Args:
            results: List of search results
            question: Original question
            
        Returns:
            Formatted string with search results
        """
        answer = f"Según Wikipedia:\n\n"
        
        for i, result in enumerate(results, 1):
            answer += f"**{result['title']}**\n"
            answer += f"{result['snippet']}\n"
            answer += f"Fuente: {result['link']}\n\n"
        
        return answer.strip()
