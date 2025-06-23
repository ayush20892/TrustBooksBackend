import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from app.parsers.base_parser import BaseParser
from app.config import settings

logger = logging.getLogger(__name__)

class InvoiceData(BaseModel):
    invoice_number: Optional[str] = Field(None, description="Invoice number or ID")
    invoice_date: Optional[str] = Field(None, description="Invoice date in YYYY-MM-DD format")
    vendor_name: Optional[str] = Field(None, description="Name of the vendor or supplier")
    vendor_gstin: Optional[str] = Field(None, description="Vendor's GSTIN number")
    taxable_value: Optional[float] = Field(None, description="Taxable amount before GST")
    gst_amount: Optional[float] = Field(None, description="GST amount")
    invoice_total: Optional[float] = Field(None, description="Total invoice amount including tax")
    payment_terms: Optional[str] = Field(None, description="Payment terms if mentioned")
    invoice_currency: Optional[str] = Field(None, description="Currency of the invoice")
    items: Optional[list] = Field(None, description="List of items with descriptions and amounts")

class InvoiceParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=settings.google_api_key,
            model="gemini-pro",
            temperature=0,
            convert_system_message_to_human=True
        )
        self.parser = PydanticOutputParser(pydantic_object=InvoiceData)
    
    def _parse_content(self, raw_text: str) -> Dict[str, Any]:
        """Parse invoice content using Google Gemini"""
        try:
            # Create prompt for invoice parsing
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at extracting invoice information from text. 
                Extract the following fields from the provided invoice text:
                - Invoice number
                - Invoice date (convert to YYYY-MM-DD format)
                - Vendor name
                - Vendor GSTIN
                - Taxable value (amount before GST)
                - GST amount
                - Invoice total
                - Payment terms
                - Currency
                - List of items (if available)
                
                If a field is not found, return null for that field.
                For amounts, extract only the numeric value without currency symbols.
                For dates, ensure they are in YYYY-MM-DD format."""),
                ("user", "Please extract invoice information from this text:\n\n{text}")
            ])
            
            # Get response from Gemini
            chain = prompt | self.llm | self.parser
            result = chain.invoke({"text": raw_text})
            
            # Convert to dictionary
            parsed_data = result.dict()
            
            # Clean and validate data
            parsed_data = self._clean_invoice_data(parsed_data)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing invoice content: {e}")
            # Fallback to basic regex extraction
            return self._fallback_parse(raw_text)
    
    def _clean_invoice_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate extracted invoice data"""
        cleaned_data = {}
        
        # Clean invoice number
        if data.get("invoice_number"):
            cleaned_data["invoice_number"] = str(data["invoice_number"]).strip()
        
        # Clean and validate date
        if data.get("invoice_date"):
            try:
                # Try to parse the date
                date_str = str(data["invoice_date"]).strip()
                if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                    cleaned_data["invoice_date"] = date_str
            except:
                pass
        
        # Clean vendor name
        if data.get("vendor_name"):
            cleaned_data["vendor_name"] = str(data["vendor_name"]).strip()
        
        # Clean GSTIN
        if data.get("vendor_gstin"):
            gstin = str(data["vendor_gstin"]).strip()
            if re.match(r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}\d{1}[Z]{1}[A-Z\d]{1}$', gstin):
                cleaned_data["vendor_gstin"] = gstin
        
        # Clean numeric values
        for field in ["taxable_value", "gst_amount", "invoice_total"]:
            if data.get(field):
                try:
                    value = float(str(data[field]).replace(',', ''))
                    cleaned_data[field] = value
                except:
                    pass
        
        # Clean other fields
        for field in ["payment_terms", "invoice_currency"]:
            if data.get(field):
                cleaned_data[field] = str(data[field]).strip()
        
        # Clean items list
        if data.get("items") and isinstance(data["items"], list):
            cleaned_data["items"] = data["items"]
        
        return cleaned_data
    
    def _fallback_parse(self, raw_text: str) -> Dict[str, Any]:
        """Fallback parsing using regex patterns"""
        data = {}
        
        # Extract invoice number patterns
        invoice_patterns = [
            r'invoice\s*#?\s*:?\s*([A-Z0-9\-_]+)',
            r'invoice\s*number\s*:?\s*([A-Z0-9\-_]+)',
            r'bill\s*#?\s*:?\s*([A-Z0-9\-_]+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                data["invoice_number"] = match.group(1).strip()
                break
        
        # Extract amounts
        amount_patterns = [
            r'total\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)',
            r'amount\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)',
            r'grand\s*total\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                try:
                    data["invoice_total"] = float(match.group(1).replace(',', ''))
                    break
                except:
                    continue
        
        # Extract GST amount
        gst_patterns = [
            r'gst\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)',
            r'cgst\s*\+?\s*sgst\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)'
        ]
        
        for pattern in gst_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                try:
                    data["gst_amount"] = float(match.group(1).replace(',', ''))
                    break
                except:
                    continue
        
        return data 