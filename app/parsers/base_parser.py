import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import PyPDF2
import pdfplumber
from openpyxl import load_workbook
from app.config import settings

logger = logging.getLogger(__name__)

class BaseParser(ABC):
    """Base class for all file parsers"""
    
    def __init__(self):
        self.supported_extensions = {
            '.pdf': self._parse_pdf,
            '.csv': self._parse_csv,
            '.xlsx': self._parse_excel,
            '.xls': self._parse_excel
        }
    
    def parse_file(self, file_path: str, file_content: bytes) -> Dict[str, Any]:
        """Main parsing method that routes to appropriate parser based on file extension"""
        try:
            file_extension = os.path.splitext(file_path)[1].lower()
            
            if file_extension not in self.supported_extensions:
                raise ValueError(f"Unsupported file type: {file_extension}")
            
            # Extract text content
            raw_text = self.supported_extensions[file_extension](file_content)
            
            # Parse the extracted text
            parsed_data = self._parse_content(raw_text)
            
            return {
                "raw_text": raw_text,
                "parsed_data": parsed_data,
                "file_type": file_extension
            }
            
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            raise
    
    def _parse_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF files"""
        try:
            # Try pdfplumber first for better text extraction
            with pdfplumber.open(file_content) as pdf:
                text = ""
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                if text.strip():
                    return text
            
            # Fallback to PyPDF2
            pdf_file = PyPDF2.PdfReader(file_content)
            text = ""
            for page in pdf_file.pages:
                text += page.extract_text() + "\n"
            
            return text
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise
    
    def _parse_csv(self, file_content: bytes) -> str:
        """Extract text from CSV files"""
        try:
            # Read CSV content
            df = pd.read_csv(file_content)
            
            # Convert to string representation
            text = df.to_string(index=False)
            return text
            
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise
    
    def _parse_excel(self, file_content: bytes) -> str:
        """Extract text from Excel files"""
        try:
            # Read Excel content
            df = pd.read_excel(file_content)
            
            # Convert to string representation
            text = df.to_string(index=False)
            return text
            
        except Exception as e:
            logger.error(f"Error parsing Excel: {e}")
            raise
    
    @abstractmethod
    def _parse_content(self, raw_text: str) -> Dict[str, Any]:
        """Abstract method to be implemented by specific parsers"""
        pass
    
    def validate_file(self, file_path: str, file_size: int) -> bool:
        """Validate uploaded file"""
        # Check file size
        if file_size > settings.max_file_size:
            raise ValueError(f"File size exceeds maximum allowed size of {settings.max_file_size} bytes")
        
        # Check file extension
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file type: {file_extension}")
        
        return True 