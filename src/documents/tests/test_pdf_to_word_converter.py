"""
Unit tests for PDF to Word conversion feature
"""
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from django.test import TestCase

from documents.pdf_to_word_converter import (
    PdfToWordConverter,
    is_conversion_available,
)


class TestPdfToWordConverter(TestCase):
    """Test PDF to Word conversion functionality"""
    
    @pytest.mark.skipif(
        not is_conversion_available(),
        reason="PDF to Word conversion dependencies not installed"
    )
    def test_is_conversion_available(self):
        """Test that conversion availability check works"""
        # Should return True if dependencies are installed
        available = is_conversion_available()
        self.assertIsInstance(available, bool)
    
    @pytest.mark.skipif(
        not is_conversion_available(),
        reason="PDF to Word conversion dependencies not installed"
    )
    def test_converter_initialization(self):
        """Test converter can be initialized"""
        converter = PdfToWordConverter(ocr_language="eng")
        self.assertEqual(converter.ocr_language, "eng")
        
        # Test with different language
        converter_ind = PdfToWordConverter(ocr_language="ind")
        self.assertEqual(converter_ind.ocr_language, "ind")
    
    @pytest.mark.skipif(
        not is_conversion_available(),
        reason="PDF to Word conversion dependencies not installed"
    )
    def test_convert_pdf_to_word_file_not_found(self):
        """Test error handling when PDF file doesn't exist"""
        converter = PdfToWordConverter()
        non_existent_path = Path("/tmp/non_existent_file.pdf")
        
        with self.assertRaises(FileNotFoundError):
            converter.convert_pdf_to_word(non_existent_path)
    
    @pytest.mark.skipif(
        not is_conversion_available(),
        reason="PDF to Word conversion dependencies not installed"
    )
    @patch("documents.pdf_to_word_converter.convert_from_path")
    @patch("documents.pdf_to_word_converter.pytesseract.image_to_string")
    def test_convert_pdf_to_word_basic(
        self,
        mock_ocr,
        mock_pdf_convert,
    ):
        """Test basic PDF to Word conversion"""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            pdf_path = Path(tmp_pdf.name)
            tmp_pdf.write(b"%PDF-1.4 dummy content")
        
        try:
            # Mock PDF to image conversion
            mock_image = MagicMock()
            mock_pdf_convert.return_value = [mock_image]
            
            # Mock OCR result
            mock_ocr.return_value = "Sample text from PDF"
            
            # Create output path
            with tempfile.NamedTemporaryFile(
                suffix=".docx",
                delete=False,
            ) as tmp_docx:
                output_path = Path(tmp_docx.name)
            
            try:
                # Convert
                converter = PdfToWordConverter(ocr_language="eng")
                result = converter.convert_pdf_to_word(
                    pdf_path=pdf_path,
                    output_path=output_path,
                    dpi=200,
                    include_images=False,
                )
                
                # Verify result
                self.assertEqual(result, output_path)
                self.assertTrue(output_path.exists())
                
                # Verify mocks were called
                mock_pdf_convert.assert_called_once()
                mock_ocr.assert_called_once()
                
            finally:
                # Clean up output file
                if output_path.exists():
                    output_path.unlink()
        finally:
            # Clean up input file
            if pdf_path.exists():
                pdf_path.unlink()
    
    @pytest.mark.skipif(
        not is_conversion_available(),
        reason="PDF to Word conversion dependencies not installed"
    )
    @patch("documents.pdf_to_word_converter.convert_from_path")
    @patch("documents.pdf_to_word_converter.pytesseract.image_to_data")
    def test_convert_with_layout_detection(
        self,
        mock_ocr_data,
        mock_pdf_convert,
    ):
        """Test PDF to Word conversion with layout detection"""
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
            pdf_path = Path(tmp_pdf.name)
            tmp_pdf.write(b"%PDF-1.4 dummy content")
        
        try:
            # Mock PDF to image conversion
            mock_image = MagicMock()
            mock_pdf_convert.return_value = [mock_image]
            
            # Mock OCR data with layout info
            mock_ocr_data.return_value = {
                "text": ["Sample", "text", "from", "PDF"],
                "block_num": [0, 0, 1, 1],
                "conf": [95, 95, 90, 90],
            }
            
            # Create output path
            with tempfile.NamedTemporaryFile(
                suffix=".docx",
                delete=False,
            ) as tmp_docx:
                output_path = Path(tmp_docx.name)
            
            try:
                # Convert
                converter = PdfToWordConverter(ocr_language="eng")
                result = converter.convert_with_layout_detection(
                    pdf_path=pdf_path,
                    output_path=output_path,
                    dpi=200,
                )
                
                # Verify result
                self.assertEqual(result, output_path)
                self.assertTrue(output_path.exists())
                
                # Verify mocks were called
                mock_pdf_convert.assert_called_once()
                mock_ocr_data.assert_called_once()
                
            finally:
                # Clean up output file
                if output_path.exists():
                    output_path.unlink()
        finally:
            # Clean up input file
            if pdf_path.exists():
                pdf_path.unlink()
    
    def test_import_error_handling(self):
        """Test that import errors are handled gracefully"""
        # This test checks if the module handles missing dependencies
        with patch("documents.pdf_to_word_converter.CONVERSION_AVAILABLE", False):
            with self.assertRaises(ImportError):
                PdfToWordConverter()
