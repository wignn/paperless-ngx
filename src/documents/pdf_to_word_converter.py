"""
PDF to Word converter with OCR support for Paperless-NGX
"""
import logging
import tempfile
from pathlib import Path
from typing import Optional

from django.conf import settings
from pdf2image import convert_from_path
from PIL import Image

try:
    import pytesseract
    from docx import Document as DocxDocument
    from docx.shared import Inches
    
    CONVERSION_AVAILABLE = True
except ImportError:
    CONVERSION_AVAILABLE = False

logger = logging.getLogger("paperless.pdf_to_word")


class PdfToWordConverter:
    """
    Converter class for converting PDF files to Word documents with OCR support
    """
    
    def __init__(self, ocr_language: str = "eng"):
        """
        Initialize the converter
        
        Args:
            ocr_language: Language code for OCR (default: eng)
        """
        if not CONVERSION_AVAILABLE:
            raise ImportError(
                "PDF to Word conversion requires python-docx and pytesseract. "
                "Please install them: pip install python-docx pytesseract"
            )
        
        self.ocr_language = ocr_language
    
    def convert_pdf_to_word(
        self,
        pdf_path: Path,
        output_path: Optional[Path] = None,
        dpi: int = 300,
        include_images: bool = True,
    ) -> Path:
        """
        Convert a PDF file to a Word document using OCR
        
        Args:
            pdf_path: Path to the input PDF file
            output_path: Path for the output Word file (optional)
            dpi: DPI for image conversion (default: 300)
            include_images: Whether to include images in the Word document
            
        Returns:
            Path to the created Word document
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If conversion fails
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Starting PDF to Word conversion: {pdf_path}")
        
        # Create output path if not specified
        if output_path is None:
            output_path = pdf_path.with_suffix(".docx")
        
        try:
            # Convert PDF to images
            logger.info(f"Converting PDF to images with DPI={dpi}")
            images = convert_from_path(str(pdf_path), dpi=dpi)
            
            # Create Word document
            doc = DocxDocument()
            
            # Process each page
            for page_num, image in enumerate(images, start=1):
                logger.info(f"Processing page {page_num}/{len(images)}")
                
                # Perform OCR on the image
                text = pytesseract.image_to_string(
                    image,
                    lang=self.ocr_language,
                )
                
                # Add page number heading
                doc.add_heading(f"Page {page_num}", level=2)
                
                # Add OCR text
                if text.strip():
                    doc.add_paragraph(text)
                else:
                    doc.add_paragraph("[No text detected on this page]")
                
                # Optionally add image to document
                if include_images:
                    # Save image temporarily
                    with tempfile.NamedTemporaryFile(
                        suffix=".png",
                        delete=False,
                    ) as tmp_img:
                        image.save(tmp_img.name, "PNG")
                        
                        # Add image to document (scaled to fit page)
                        try:
                            doc.add_picture(tmp_img.name, width=Inches(6))
                        except Exception as e:
                            logger.warning(
                                f"Failed to add image for page {page_num}: {e}"
                            )
                        
                        # Clean up temp file
                        Path(tmp_img.name).unlink(missing_ok=True)
                
                # Add page break (except for last page)
                if page_num < len(images):
                    doc.add_page_break()
            
            # Save the Word document
            doc.save(str(output_path))
            logger.info(f"Successfully created Word document: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to convert PDF to Word: {e}")
            raise
    
    def convert_with_layout_detection(
        self,
        pdf_path: Path,
        output_path: Optional[Path] = None,
        dpi: int = 300,
    ) -> Path:
        """
        Convert PDF to Word with layout detection (preserves formatting better)
        
        Args:
            pdf_path: Path to the input PDF file
            output_path: Path for the output Word file (optional)
            dpi: DPI for image conversion (default: 300)
            
        Returns:
            Path to the created Word document
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info(f"Starting layout-aware PDF to Word conversion: {pdf_path}")
        
        # Create output path if not specified
        if output_path is None:
            output_path = pdf_path.with_suffix(".docx")
        
        try:
            # Convert PDF to images
            images = convert_from_path(str(pdf_path), dpi=dpi)
            
            # Create Word document
            doc = DocxDocument()
            
            # Process each page with layout detection
            for page_num, image in enumerate(images, start=1):
                logger.info(f"Processing page {page_num}/{len(images)} with layout detection")
                
                # Get OCR data with layout information
                ocr_data = pytesseract.image_to_data(
                    image,
                    lang=self.ocr_language,
                    output_type=pytesseract.Output.DICT,
                )
                
                # Add page heading
                doc.add_heading(f"Page {page_num}", level=2)
                
                # Group text by blocks/paragraphs
                current_paragraph = []
                last_block_num = -1
                
                for i in range(len(ocr_data["text"])):
                    text = ocr_data["text"][i].strip()
                    block_num = ocr_data["block_num"][i]
                    conf = int(ocr_data["conf"][i])
                    
                    # Skip low confidence or empty text
                    if conf < 0 or not text:
                        continue
                    
                    # New block detected, save previous paragraph
                    if block_num != last_block_num and current_paragraph:
                        doc.add_paragraph(" ".join(current_paragraph))
                        current_paragraph = []
                    
                    current_paragraph.append(text)
                    last_block_num = block_num
                
                # Add remaining paragraph
                if current_paragraph:
                    doc.add_paragraph(" ".join(current_paragraph))
                
                # Add page break
                if page_num < len(images):
                    doc.add_page_break()
            
            # Save document
            doc.save(str(output_path))
            logger.info(f"Successfully created Word document: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to convert PDF to Word with layout detection: {e}")
            raise


def is_conversion_available() -> bool:
    """
    Check if PDF to Word conversion is available
    
    Returns:
        True if required libraries are installed
    """
    return CONVERSION_AVAILABLE
