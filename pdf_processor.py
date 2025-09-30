from PyPDF2 import PdfReader
import io
import logging

class PDFProcessor:
    """Handles PDF file processing and text extraction"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_file) -> str:
        """
        Extract text from a PDF file
        Args:
            pdf_file: A file-like object containing PDF data
        Returns:
            str: Extracted text from the PDF
        """
        try:
            # Create PDF reader object
            pdf_reader = PdfReader(pdf_file)
            
            # Extract text from all pages
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            logging.error(f"Error extracting text from PDF: {str(e)}")
            raise Exception(f"Failed to process PDF file: {str(e)}")