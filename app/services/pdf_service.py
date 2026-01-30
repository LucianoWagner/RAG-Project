"""
PDF text extraction service with OCR support.

This module handles extracting text content from PDF files using pdfplumber
for native PDFs, and Tesseract OCR for scanned documents.
"""

from pathlib import Path
from typing import Optional, Tuple
import pdfplumber

from app.utils.logger import logger
from app.config import settings


class PDFService:
    """
    Service for extracting text from PDF documents.
    
    Supports:
    - Native PDFs (using pdfplumber)
    - Scanned PDFs (using Tesseract OCR as fallback)
    
    The service automatically detects when a PDF contains no extractable
    text and falls back to OCR processing.
    """
    
    def __init__(self):
        """Initialize PDF service and check OCR availability."""
        self.ocr_available = self._check_ocr_availability()
        if self.ocr_available:
            logger.info("PDFService initialized with OCR support enabled")
        else:
            logger.warning("PDFService initialized WITHOUT OCR support")
    
    def _check_ocr_availability(self) -> bool:
        """
        Check if OCR dependencies (Tesseract + Poppler) are available.
        
        Returns:
            True if OCR can be used, False otherwise
        """
        if not settings.ocr_enabled:
            logger.info("OCR is disabled in settings")
            return False
        
        try:
            import pytesseract
            from pdf2image import convert_from_path
            
            # Configure tesseract path if specified
            if settings.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
            
            # Test tesseract is working
            version = pytesseract.get_tesseract_version()
            logger.info(f"Tesseract OCR version {version} detected")
            
            return True
            
        except ImportError as e:
            logger.warning(f"OCR dependencies not installed: {e}")
            return False
        except Exception as e:
            logger.warning(f"OCR not available: {e}")
            return False
    
    def extract_text(self, pdf_path: Path) -> Tuple[str, bool]:
        """
        Extract all text content from a PDF file.
        
        First attempts normal text extraction with pdfplumber.
        If no text is found and OCR is available, falls back to OCR.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Tuple of (extracted_text, used_ocr) where used_ocr indicates
            if OCR was used for extraction
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF is corrupted or contains no extractable text
        """
        if not pdf_path.exists():
            logger.error(f"PDF file not found: {pdf_path}")
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Try normal extraction first
        text = self._extract_with_pdfplumber(pdf_path)
        
        if text.strip():
            logger.info(f"Successfully extracted text with pdfplumber: {len(text)} chars")
            return text, False
        
        # No text found - try OCR if available
        if self.ocr_available:
            logger.info(f"No text found with pdfplumber, attempting OCR for: {pdf_path.name}")
            try:
                ocr_text = self._extract_with_ocr(pdf_path)
                if ocr_text.strip():
                    return ocr_text, True
            except Exception as e:
                logger.error(f"OCR extraction failed: {e}")
        
        # Nothing worked
        error_msg = f"PDF contains no extractable text: {pdf_path.name}"
        if not self.ocr_available:
            error_msg += " (OCR not available for scanned documents)"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    def _extract_with_pdfplumber(self, pdf_path: Path) -> str:
        """
        Extract text using pdfplumber (for native PDFs with embedded text).
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a single string (may be empty for scanned PDFs)
        """
        try:
            logger.info(f"Starting pdfplumber extraction from: {pdf_path.name}")
            
            with pdfplumber.open(pdf_path) as pdf:
                text_parts = []
                
                for page_num, page in enumerate(pdf.pages, start=1):
                    page_text = page.extract_text()
                    
                    if page_text:
                        text_parts.append(page_text)
                        logger.debug(f"Extracted {len(page_text)} characters from page {page_num}")
                    else:
                        logger.debug(f"Page {page_num} contains no extractable text")
                
                full_text = "\n\n".join(text_parts)
                
                logger.info(
                    f"pdfplumber extracted {len(full_text)} characters "
                    f"from {len(pdf.pages)} pages in {pdf_path.name}"
                )
                
                return full_text
                
        except pdfplumber.exceptions.PDFSyntaxError as e:
            logger.error(f"PDF file is corrupted or invalid: {pdf_path.name} - {e}")
            raise ValueError(f"Invalid or corrupted PDF file: {pdf_path.name}")
        except Exception as e:
            logger.error(f"Unexpected error in pdfplumber extraction: {e}")
            # Return empty string to allow OCR fallback
            return ""
    
    def _extract_with_ocr(self, pdf_path: Path) -> str:
        """
        Extract text using OCR (for scanned PDFs).
        
        Converts each PDF page to an image, then uses Tesseract OCR
        to extract text from the images.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from OCR
            
        Raises:
            ValueError: If OCR fails to extract any text
        """
        import pytesseract
        from pdf2image import convert_from_path
        
        logger.info(f"Starting OCR extraction for: {pdf_path.name}")
        
        # Configure tesseract
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        
        # Configure poppler path for pdf2image
        poppler_path = settings.poppler_path if settings.poppler_path else None
        
        try:
            # Convert PDF pages to images (300 DPI for good OCR accuracy)
            logger.info("Converting PDF pages to images...")
            images = convert_from_path(
                pdf_path,
                dpi=300,
                poppler_path=poppler_path
            )
            
            logger.info(f"Converted {len(images)} pages to images")
            
            # Process each page with OCR
            text_parts = []
            total_chars = 0
            
            for page_num, image in enumerate(images, start=1):
                logger.debug(f"Processing page {page_num} with OCR...")
                
                # Apply OCR to image
                page_text = pytesseract.image_to_string(
                    image,
                    lang=settings.ocr_language
                )
                
                if page_text.strip():
                    text_parts.append(page_text)
                    total_chars += len(page_text)
                    logger.debug(f"OCR extracted {len(page_text)} chars from page {page_num}")
                else:
                    logger.warning(f"OCR found no text on page {page_num}")
            
            full_text = "\n\n".join(text_parts)
            
            if not full_text.strip():
                raise ValueError(f"OCR could not extract any text from: {pdf_path.name}")
            
            logger.info(f"OCR successfully extracted {total_chars} characters from {len(images)} pages")
            
            return full_text
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise ValueError(f"OCR extraction failed for {pdf_path.name}: {e}")
