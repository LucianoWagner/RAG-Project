"""
Pydantic models for request/response validation.

This module defines all data models used in the API endpoints,
ensuring type safety and automatic validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class UploadResponse(BaseModel):
    """Response model for document upload endpoint."""
    
    filename: str = Field(..., description="Name of the uploaded PDF file")
    chunks_processed: int = Field(..., description="Number of text chunks created from the document")
    message: str = Field(..., description="Success message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "document.pdf",
                "chunks_processed": 42,
                "message": "Document processed successfully"
            }
        }


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    
    question: str = Field(
        ..., 
        min_length=1,
        max_length=500,
        description="Natural language question about the documents"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "What is the main topic discussed in the document?"
            }
        }


class SourceChunk(BaseModel):
    """Model representing a retrieved source chunk."""
    
    text: str = Field(..., description="Content of the text chunk")
    score: float = Field(..., description="Similarity score (lower is better for L2 distance)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "The document discusses...",
                "score": 0.342
            }
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    
    answer: str = Field(..., description="Generated answer based on document context")
    sources: List[SourceChunk] = Field(
        default_factory=list,
        description="Source chunks used to generate the answer"
    )
    has_context: bool = Field(
        ..., 
        description="Whether relevant context was found in the documents"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Based on the documents, the main topic is...",
                "sources": [
                    {
                        "text": "The document discusses...",
                        "score": 0.342
                    }
                ],
                "has_context": True
            }
        }


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Overall system status")
    ollama_available: bool = Field(..., description="Whether Ollama service is accessible")
    embedding_model_loaded: bool = Field(..., description="Whether embedding model is loaded")
    vector_store_initialized: bool = Field(..., description="Whether vector store is ready")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "ollama_available": True,
                "embedding_model_loaded": True,
                "vector_store_initialized": True
            }
        }
