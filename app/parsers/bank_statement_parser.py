import logging
import re
import pandas as pd
from datetime import datetime
from typing import Dict, Any, Optional, List
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from app.parsers.base_parser import BaseParser
from app.config import settings

logger = logging.getLogger(__name__)

class TransactionData(BaseModel):
    txn_date: Optional[str] = Field(None, description="Transaction date in YYYY-MM-DD format")
    description: Optional[str] = Field(None, description="Transaction description")
    debit: Optional[float] = Field(None, description="Debit amount")
    credit: Optional[float] = Field(None, description="Credit amount")
    balance: Optional[float] = Field(None, description="Closing balance")
    account_number: Optional[str] = Field(None, description="Bank account number")
    mode: Optional[str] = Field(None, description="Mode of payment (UPI, NEFT, IMPS, etc.)")
    category: Optional[str] = Field(None, description="Transaction category")
    meta_data: Optional[dict] = Field(None, description="Additional metadata like sender/receiver info")

class BankStatementParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.llm = ChatGoogleGenerativeAI(
            google_api_key=settings.google_api_key,
            model="gemini-pro",
            temperature=0,
            convert_system_message_to_human=True
        )
        self.parser = PydanticOutputParser(pydantic_object=TransactionData)
    
    def _parse_content(self, raw_text: str) -> Dict[str, Any]:
        """Parse bank statement content using Google Gemini"""
        try:
            # Create prompt for bank statement parsing
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at extracting bank statement information from text. 
                Extract the following fields from the provided bank statement text:
                - Transaction date (convert to YYYY-MM-DD format)
                - Description (vendor, UPI, NEFT, etc.)
                - Debit amount (if money is going out)
                - Credit amount (if money is coming in)
                - Closing balance
                - Bank account number
                - Mode of payment (UPI, IMPS, NEFT, etc.)
                - Transaction category
                - Meta data (user account info, sender/receiver info)
                
                If a field is not found, return null for that field.
                For amounts, extract only the numeric value without currency symbols.
                For dates, ensure they are in YYYY-MM-DD format.
                For mode, identify common payment methods like UPI, NEFT, IMPS, RTGS, etc."""),
                ("user", "Please extract bank statement information from this text:\n\n{text}")
            ])
            
            # Get response from Gemini
            chain = prompt | self.llm | self.parser
            result = chain.invoke({"text": raw_text})
            
            # Convert to dictionary
            parsed_data = result.dict()
            
            # Clean and validate data
            parsed_data = self._clean_statement_data(parsed_data)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing bank statement content: {e}")
            # Fallback to basic regex extraction
            return self._fallback_parse(raw_text)
    
    def _clean_statement_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate extracted bank statement data"""
        cleaned_data = {}
        
        # Clean and validate date
        if data.get("txn_date"):
            try:
                date_str = str(data["txn_date"]).strip()
                if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                    cleaned_data["txn_date"] = date_str
            except:
                pass
        
        # Clean description
        if data.get("description"):
            cleaned_data["description"] = str(data["description"]).strip()
        
        # Clean numeric values
        for field in ["debit", "credit", "balance"]:
            if data.get(field):
                try:
                    value = float(str(data[field]).replace(',', ''))
                    cleaned_data[field] = value
                except:
                    pass
        
        # Clean account number
        if data.get("account_number"):
            account_num = str(data["account_number"]).strip()
            # Remove common prefixes and clean
            account_num = re.sub(r'[^\d]', '', account_num)
            if len(account_num) >= 8:  # Minimum account number length
                cleaned_data["account_number"] = account_num
        
        # Clean mode of payment
        if data.get("mode"):
            mode = str(data["mode"]).strip().upper()
            valid_modes = ["UPI", "NEFT", "IMPS", "RTGS", "CASH", "CHEQUE", "CARD"]
            if mode in valid_modes:
                cleaned_data["mode"] = mode
        
        # Clean category
        if data.get("category"):
            cleaned_data["category"] = str(data["category"]).strip()
        
        # Clean meta data
        if data.get("meta_data") and isinstance(data["meta_data"], dict):
            cleaned_data["meta_data"] = data["meta_data"]
        
        return cleaned_data
    
    def _fallback_parse(self, raw_text: str) -> Dict[str, Any]:
        """Fallback parsing using regex patterns"""
        data = {}
        
        # Extract date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{2}-\d{2}-\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, raw_text)
            if match:
                try:
                    date_str = match.group(1)
                    # Try to parse and format date
                    if '/' in date_str:
                        parts = date_str.split('/')
                        if len(parts) == 3:
                            if len(parts[2]) == 2:
                                parts[2] = '20' + parts[2]
                            data["txn_date"] = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
                    elif '-' in date_str:
                        data["txn_date"] = date_str
                    break
                except:
                    continue
        
        # Extract amounts
        amount_patterns = [
            r'debit\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)',
            r'withdrawal\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)',
            r'credit\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)',
            r'deposit\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)',
            r'balance\s*:?\s*[₹$]?\s*([\d,]+\.?\d*)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    if 'debit' in pattern.lower() or 'withdrawal' in pattern.lower():
                        data["debit"] = amount
                    elif 'credit' in pattern.lower() or 'deposit' in pattern.lower():
                        data["credit"] = amount
                    elif 'balance' in pattern.lower():
                        data["balance"] = amount
                except:
                    continue
        
        # Extract account number
        account_patterns = [
            r'account\s*#?\s*:?\s*(\d+)',
            r'acc\s*#?\s*:?\s*(\d+)',
            r'(\d{10,16})'  # Generic account number pattern
        ]
        
        for pattern in account_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                account_num = match.group(1)
                if len(account_num) >= 8:
                    data["account_number"] = account_num
                break
        
        # Extract payment mode
        mode_patterns = [
            r'(UPI|NEFT|IMPS|RTGS|CASH|CHEQUE|CARD)',
            r'payment\s*mode\s*:?\s*(UPI|NEFT|IMPS|RTGS|CASH|CHEQUE|CARD)'
        ]
        
        for pattern in mode_patterns:
            match = re.search(pattern, raw_text, re.IGNORECASE)
            if match:
                data["mode"] = match.group(1).upper()
                break
        
        return data
    
    def parse_csv_statement(self, file_content: bytes) -> List[Dict[str, Any]]:
        """Specialized parsing for CSV bank statements"""
        try:
            df = pd.read_csv(file_content)
            transactions = []
            
            # Common column mappings
            column_mappings = {
                'date': ['Date', 'Transaction Date', 'Txn Date', 'DATE'],
                'description': ['Description', 'Narration', 'Particulars', 'DESCRIPTION'],
                'debit': ['Debit', 'Withdrawal', 'DR', 'DEBIT'],
                'credit': ['Credit', 'Deposit', 'CR', 'CREDIT'],
                'balance': ['Balance', 'Closing Balance', 'BALANCE'],
                'account': ['Account', 'Account Number', 'ACC NO', 'ACCOUNT']
            }
            
            # Map columns
            mapped_columns = {}
            for field, possible_names in column_mappings.items():
                for col in df.columns:
                    if col.upper() in [name.upper() for name in possible_names]:
                        mapped_columns[field] = col
                        break
            
            # Process each row
            for _, row in df.iterrows():
                transaction = {}
                
                # Extract date
                if 'date' in mapped_columns:
                    try:
                        date_val = row[mapped_columns['date']]
                        if pd.notna(date_val):
                            if isinstance(date_val, str):
                                # Try to parse date
                                transaction['txn_date'] = self._parse_date_string(date_val)
                    except:
                        pass
                
                # Extract description
                if 'description' in mapped_columns:
                    desc_val = row[mapped_columns['description']]
                    if pd.notna(desc_val):
                        transaction['description'] = str(desc_val).strip()
                
                # Extract amounts
                if 'debit' in mapped_columns:
                    debit_val = row[mapped_columns['debit']]
                    if pd.notna(debit_val):
                        try:
                            transaction['debit'] = float(str(debit_val).replace(',', ''))
                        except:
                            pass
                
                if 'credit' in mapped_columns:
                    credit_val = row[mapped_columns['credit']]
                    if pd.notna(credit_val):
                        try:
                            transaction['credit'] = float(str(credit_val).replace(',', ''))
                        except:
                            pass
                
                if 'balance' in mapped_columns:
                    balance_val = row[mapped_columns['balance']]
                    if pd.notna(balance_val):
                        try:
                            transaction['balance'] = float(str(balance_val).replace(',', ''))
                        except:
                            pass
                
                # Extract account number
                if 'account' in mapped_columns:
                    acc_val = row[mapped_columns['account']]
                    if pd.notna(acc_val):
                        acc_str = str(acc_val).strip()
                        if re.match(r'\d+', acc_str):
                            transaction['account_number'] = acc_str
                
                if transaction:  # Only add if we have some data
                    transactions.append(transaction)
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error parsing CSV bank statement: {e}")
            return []
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """Parse various date formats to YYYY-MM-DD"""
        try:
            # Common date formats
            formats = [
                '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y',
                '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%m/%d/%y'
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except:
                    continue
            
            return None
        except:
            return None 