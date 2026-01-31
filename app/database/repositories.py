"""
Repository pattern for data access.

Simplified - only document metadata management.
"""

from typing import List, Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.models import DocumentMetadata
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


# ============================================================================
# DOCUMENT REPOSITORY
# ============================================================================

class DocumentRepository:
    """Repository for document metadata operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_document_upload(
        self,
        filename: str,
        file_hash: str,
        chunks_count: int,
        file_size_bytes: int,
        processing_time_ms: int,
        pages_count: Optional[int] = None,
        extracted_text_length: Optional[int] = None
    ) -> DocumentMetadata:
        """
        Log document upload.
        
        Args:
            filename: Document filename
            file_hash: SHA256 hash
            chunks_count: Number of chunks created
            file_size_bytes: File size
            processing_time_ms: Processing time
            pages_count: Number of pages
            extracted_text_length: Length of extracted text
            
        Returns:
            Created DocumentMetadata instance
        """
        try:
            doc = DocumentMetadata(
                filename=filename,
                file_hash=file_hash,
                chunks_count=chunks_count,
                file_size_bytes=file_size_bytes,
                processing_time_ms=processing_time_ms,
                pages_count=pages_count,
                extracted_text_length=extracted_text_length
            )
            
            self.db.add(doc)
            await self.db.commit()
            await self.db.refresh(doc)
            
            logger.info(f"Document logged: {filename} ({chunks_count} chunks)")
            return doc
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to log document {filename}: {e}")
            raise
    
    async def get_all_documents(self) -> List[DocumentMetadata]:
        """Get all uploaded documents."""
        result = await self.db.execute(
            select(DocumentMetadata).order_by(desc(DocumentMetadata.upload_timestamp))
        )
        return result.scalars().all()
    
    async def get_document_by_hash(self, file_hash: str) -> Optional[DocumentMetadata]:
        """Get document by hash to check for duplicates."""
        result = await self.db.execute(
            select(DocumentMetadata).where(DocumentMetadata.file_hash == file_hash)
        )
        return result.scalar_one_or_none()
    
    async def get_total_chunks(self) -> int:
        """Get total number of chunks across all documents."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.sum(DocumentMetadata.chunks_count))
        )
        total = result.scalar()
        return total if total else 0
    
    async def delete_all_documents(self) -> int:
        """
        Delete all document metadata from database.
        
        Used when clearing all documents from the system.
        Returns the number of deleted rows.
        """
        try:
            from sqlalchemy import delete
            
            result = await self.db.execute(
                delete(DocumentMetadata)
            )
            await self.db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} document records from database")
            return deleted_count
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to delete all documents from database: {e}")
            raise
