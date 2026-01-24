"""
PDF text extraction service.

This module handles extracting text content from PDF files using pdfplumber,
which provides robust text extraction including tables and complex layouts.
"""

from pathlib import Path
import pdfplumber
from typing import Optional

from app.utils.logger import logger


class PDFService:
    """
    Service for extracting text from PDF documents.
    
    Uses pdfplumber for robust text extraction that handles:
    - Standard text content
    - Tables
    - Complex layouts
    """
    
    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract all text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a single string
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is corrupted or contains no text
        """
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        try:
            logger.info(f"Starting text extraction from: {pdf_path.name}")
            
            with pdfplumber.open(pdf_path) as pdf:
                # Extract text from all pages
                text_parts = []
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_parts.append(page_text)
                        logger.debug(f"Extracted {len(page_text)} characters from page {page_num}")
                    else:
                        logger.warning(f"Page {page_num} contains no extractable text")
                
                # Combine all pages
                full_text = "\n\n".join(text_parts)
                
                if not full_text.strip():
                    logger.error(f"No text could be extracted from {pdf_path.name}")
                    raise ValueError(f"PDF contains no extractable text: {pdf_path.name}")
                
                logger.info(
                    f"Successfully extracted {len(full_text)} characters "
                    f"from {len(pdf.pages)} pages in {pdf_path.name}"
                )
                
                return full_text
                
        except pdfplumber.exceptions.PDFSyntaxError as e:
            logger.error(f"PDF file is corrupted or invalid: {pdf_path.name} - {e}")
            raise ValueError(f"Invalid or corrupted PDF file: {pdf_path.name}")
        except Exception as e:
            logger.error(f"Unexpected error extracting text from {pdf_path.name}: {e}")
            raise
