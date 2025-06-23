from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from enum import Enum
import uuid

class ParsingStatus(str, Enum):
    PARSED = "Parsed"
    ERROR = "Error"
    PROCESSING = "Processing"

class InvoiceBase(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[date] = None
    vendor_name: Optional[str] = None
    vendor_gstin: Optional[str] = None
    taxable_value: Optional[float] = None
    gst_amount: Optional[float] = None
    invoice_total: Optional[float] = None
    payment_terms: Optional[str] = None
    invoice_currency: Optional[str] = None
    items: Optional[List[dict]] = None

class InvoiceCreate(InvoiceBase):
    file_path: str
    raw_text: Optional[str] = None

class InvoiceResponse(InvoiceBase):
    id: str
    file_path: str
    status: ParsingStatus
    raw_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class BankStatementBase(BaseModel):
    txn_date: Optional[date] = None
    description: Optional[str] = None
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: Optional[float] = None
    account_number: Optional[str] = None
    mode: Optional[str] = None
    category: Optional[str] = None
    meta_data: Optional[dict] = None

class BankStatementCreate(BankStatementBase):
    file_path: str
    raw_text: Optional[str] = None

class BankStatementResponse(BankStatementBase):
    id: str
    file_path: str
    status: ParsingStatus
    raw_text: Optional[str] = None
    created_at: datetime
    updated_at: datetime

class UploadResponse(BaseModel):
    message: str
    file_id: str
    file_path: str
    status: ParsingStatus 