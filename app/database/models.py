"""
Database models for RAG PDF System.

Simplified schema - only document metadata tracking.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# ============================================================================
# DOCUMENT METADATA
# ============================================================================

class DocumentMetadata(Base):
    """
    Track uploaded documents and processing metrics.
    
    Purpose:
    - Avoid duplicate uploads (by hash)
    - Track processing performance
    - Document inventory management
    """
    __tablename__ = "document_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, index=True)
    file_hash = Column(String(64), unique=True, nullable=False, index=True)  # SHA256
    chunks_count = Column(Integer, nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    processing_time_ms = Column(Integer, nullable=False)
    pages_count = Column(Integer, nullable=True)
    extracted_text_length = Column(Integer, nullable=True)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<DocumentMetadata(filename='{self.filename}', chunks={self.chunks_count})>"


# ============================================================================
# USER AUTHENTICATION
# ============================================================================

class User(Base):
    """
    User model for authentication.
    
    Security features:
    - Password stored as bcrypt hash (never plain text)
    - Role-based access control ready
    - Account status tracking (is_active)
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)  # bcrypt hash
    role = Column(String(50), default="admin", nullable=False)  # admin, user, etc.
    is_active = Column(Integer, default=1, nullable=False)  # 1=active, 0=disabled
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role}')>"
