"""
FarmGrow OCR Service
Extracts text from images in documents.

Primary: Ollama with deepseek-ocr (local, no API keys)
Fallback: EasyOCR
"""
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False


class OCRService:
    """
    OCR service for extracting text from images.
    
    Features:
    - Image text extraction
    - Document page OCR
    - Batch processing
    - Kenyan language support
    """
    
    def __init__(self, ocr_provider: str = "ollama", ollama_service=None):
        """
        Initialize OCR service.
        
        Args:
            ocr_provider: 'ollama' or 'easyocr' (default: ollama)
            ollama_service: Optional Ollama service instance for deepseek-ocr
        """
        self.ocr_provider = ocr_provider
        self.ollama_service = ollama_service
        self.reader = None
        
        # Try to initialize Ollama service if not provided
        if ocr_provider == "ollama" and not ollama_service:
            try:
                from core.ollama_service import OllamaService
                self.ollama_service = OllamaService()
                logger.info("✅ Initialized Ollama OCR service (deepseek-ocr)")
            except Exception as e:
                logger.warning(f"⚠️ Ollama OCR not available: {str(e)}, will use EasyOCR fallback")
                self.ollama_service = None
        
        # Initialize EasyOCR as fallback
        if EASYOCR_AVAILABLE:
            try:
                self.reader = easyocr.Reader(['en', 'sw'])  # English and Swahili
                logger.info("✅ Initialized EasyOCR reader (English, Swahili) as fallback")
            except Exception as e:
                logger.warning(f"Failed to initialize EasyOCR fallback: {str(e)}")
                self.reader = None
        else:
            logger.warning("⚠️ EasyOCR not installed. Install with: pip install easyocr")
    
    async def extract_text_from_image(self, image_path: str) -> str:
        """
        Extract text from image file.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Extracted text
        """
        try:
            # Try Ollama first
            if self.ollama_service:
                try:
                    text = await self.ollama_service.extract_text_from_image(image_path)
                    if text:
                        logger.info(f"✅ OCR via Ollama: extracted {len(text)} characters")
                        return text
                except Exception as e:
                    logger.warning(f"Ollama OCR failed: {str(e)}, trying EasyOCR")
            
            # Fallback to EasyOCR
            if self.reader:
                result = self.reader.readtext(image_path)
                text = "\n".join([detection[1] for detection in result])
                logger.info(f"✅ OCR via EasyOCR: extracted {len(text)} characters")
                return text
            
            logger.warning(f"No OCR provider available")
            return ""
        
        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            return ""
    
    async def extract_text_from_page(self,
                                    pdf_path: str,
                                    page_number: int) -> Optional[str]:
        """
        Extract text from PDF page (if it contains images).
        
        Args:
            pdf_path: Path to PDF
            page_number: Page number (1-indexed)
        
        Returns:
            Extracted text or None
        """
        try:
            # Convert PDF page to image first
            try:
                from pdf2image import convert_from_path
            except ImportError:
                logger.warning("pdf2image not installed. Install with: pip install pdf2image")
                return None
            
            # Convert single page to image
            images = convert_from_path(pdf_path, first_page=page_number, last_page=page_number)
            
            if not images:
                return None
            
            # OCR the image
            image_path = f"/tmp/page_{page_number}.png"
            images[0].save(image_path)
            
            text = await self.extract_text_from_image(image_path)
            return text if text else None
        
        except Exception as e:
            logger.debug(f"Could not OCR page {page_number}: {str(e)}")
            return None
    
    async def extract_text_from_images_batch(self, image_paths: List[str]) -> List[str]:
        """
        Extract text from multiple images.
        
        Args:
            image_paths: List of image file paths
        
        Returns:
            List of extracted texts
        """
        texts = []
        for image_path in image_paths:
            try:
                text = await self.extract_text_from_image(image_path)
                texts.append(text)
            except Exception as e:
                logger.warning(f"Failed to OCR {image_path}: {str(e)}")
                texts.append("")
        
        return texts


# Global instance
_ocr_service_instance: Optional[OCRService] = None


def get_ocr_service(ocr_provider: str = "ollama", ollama_service=None) -> OCRService:
    """Get or create OCR service instance."""
    global _ocr_service_instance
    
    if _ocr_service_instance is None:
        _ocr_service_instance = OCRService(
            ocr_provider=ocr_provider,
            ollama_service=ollama_service
        )
    
    return _ocr_service_instance
