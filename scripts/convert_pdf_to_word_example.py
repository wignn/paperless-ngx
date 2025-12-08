#!/usr/bin/env python3
"""
Example script to convert PDF documents to Word using Paperless-NGX API

Usage:
    python convert_pdf_to_word_example.py --token YOUR_API_TOKEN --document-id 123
    python convert_pdf_to_word_example.py -t YOUR_TOKEN -d 123 -l ind --dpi 600
"""

import argparse
import sys
from pathlib import Path

import requests


def convert_pdf_to_word(
    base_url: str,
    api_token: str,
    document_id: int,
    output_file: str = None,
    ocr_language: str = "eng",
    dpi: int = 300,
    include_images: bool = True,
    layout_detection: bool = False,
):
    """
    Convert a PDF document to Word format using Paperless-NGX API
    
    Args:
        base_url: Base URL of Paperless-NGX instance (e.g., http://localhost:8000)
        api_token: API authentication token
        document_id: ID of the document to convert
        output_file: Output filename (optional, defaults to document_{id}.docx)
        ocr_language: Language code for OCR (default: eng)
        dpi: DPI for image conversion (default: 300)
        include_images: Include images in Word document (default: True)
        layout_detection: Use layout detection (default: False)
    
    Returns:
        Path to the downloaded Word file
    """
    # Build URL
    url = f"{base_url}/api/documents/{document_id}/convert-to-word/"
    
    # Build query parameters
    params = {
        "ocr_language": ocr_language,
        "dpi": dpi,
        "include_images": str(include_images).lower(),
        "layout_detection": str(layout_detection).lower(),
    }
    
    # Set headers
    headers = {
        "Authorization": f"Token {api_token}",
    }
    
    print(f"Converting document {document_id} from PDF to Word...")
    print(f"Parameters: OCR Language={ocr_language}, DPI={dpi}, "
          f"Include Images={include_images}, Layout Detection={layout_detection}")
    
    try:
        # Make request
        response = requests.get(url, params=params, headers=headers, stream=True)
        
        # Check for errors
        if response.status_code == 200:
            # Determine output filename
            if output_file is None:
                output_file = f"document_{document_id}.docx"
            
            # Save file
            output_path = Path(output_file)
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✓ Successfully converted and saved to: {output_path}")
            print(f"  File size: {output_path.stat().st_size / 1024:.2f} KB")
            return output_path
            
        elif response.status_code == 400:
            print(f"✗ Error: {response.text}")
            print("  - Check if the document is a PDF")
            print("  - Verify parameter values are valid")
            return None
            
        elif response.status_code == 403:
            print("✗ Error: Insufficient permissions")
            print("  - Check if you have permission to view this document")
            return None
            
        elif response.status_code == 404:
            print(f"✗ Error: Document {document_id} not found")
            return None
            
        elif response.status_code == 500:
            print(f"✗ Server Error: {response.text}")
            print("  - Check if required dependencies are installed")
            print("  - Check server logs for details")
            return None
            
        else:
            print(f"✗ Unexpected error: {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"✗ Connection Error: Could not connect to {base_url}")
        print("  - Check if Paperless-NGX is running")
        print("  - Verify the base URL is correct")
        return None
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF documents to Word using Paperless-NGX API"
    )
    
    parser.add_argument(
        "-u", "--url",
        default="http://localhost:8000",
        help="Base URL of Paperless-NGX instance (default: http://localhost:8000)"
    )
    
    parser.add_argument(
        "-t", "--token",
        required=True,
        help="API authentication token"
    )
    
    parser.add_argument(
        "-d", "--document-id",
        type=int,
        required=True,
        help="ID of the document to convert"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output filename (default: document_{id}.docx)"
    )
    
    parser.add_argument(
        "-l", "--language",
        default="eng",
        help="OCR language code (default: eng). Examples: eng, ind, fra, deu"
    )
    
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for image conversion (default: 300, range: 200-600)"
    )
    
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Do not include images in Word document"
    )
    
    parser.add_argument(
        "--layout-detection",
        action="store_true",
        help="Use layout detection to preserve formatting"
    )
    
    args = parser.parse_args()
    
    # Validate DPI
    if args.dpi < 72 or args.dpi > 1200:
        print("Warning: DPI should typically be between 72 and 1200")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    # Convert document
    result = convert_pdf_to_word(
        base_url=args.url,
        api_token=args.token,
        document_id=args.document_id,
        output_file=args.output,
        ocr_language=args.language,
        dpi=args.dpi,
        include_images=not args.no_images,
        layout_detection=args.layout_detection,
    )
    
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
