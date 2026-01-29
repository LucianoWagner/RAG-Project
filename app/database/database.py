"""
Database connection and session management.

Provides async SQLAlchemy engine and session factory.

NEW: Integrated resilience patterns:
- Retry with exponential backoff for connection failures
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError, DBAPIError
from sqlalchemy import text
from app.config import settings
from app.utils.logging_config import get_logger
from app.database.models import Base
from app.utils.resilience import with_retry

logger = get_logger(__name__)


# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL query logging
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Additional connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=False,  # Manual flush control
    autocommit=False  # Manual commit control
)


@with_retry(max_attempts=3, min_wait=2, max_wait=10, exceptions=(OperationalError, DBAPIError))
async def init_database():
    """
    Initialize database: create all tables.
    
    Resilience:
    - Retry: Up to 3 attempts with exponential backoff (2s, 4s, 8s)
    - Handles transient connection failures during startup
    
    Note: In production, use Alembic migrations instead.
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def get_db() -> AsyncSession:
    """
    Dependency injection for FastAPI endpoints.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        @app.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


@with_retry(max_attempts=2, min_wait=1, max_wait=3, exceptions=(OperationalError,))
async def check_database_health() -> bool:
    """
    Check if database is accessible.
    
    Resilience:
    - Retry: 2 attempts for transient connection issues
    
    Returns:
        True if healthy
    """
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
