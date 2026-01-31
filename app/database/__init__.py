"""
Database package for RAG PDF System.

Simplified - only document metadata tracking.
"""

from app.database.database import (
    get_db,
    init_database,
    check_database_health,
    async_session_maker,
    engine
)

from app.database.models import (
    Base,
    DocumentMetadata,
    User
)

from app.database.repositories import (
    DocumentRepository
)

__all__ = [
    # Database
    "get_db",
    "init_database",
    "check_database_health",
    "async_session_maker",
    "engine",
    
    # Models
    "Base",
    "DocumentMetadata",
    "User",
    
    # Repositories
    "DocumentRepository"
]
