import os
import uuid
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.models import UploadResponse, InvoiceResponse, ParsingStatus
from app.database import db
from app.parsers.invoice_parser import InvoiceParser
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload-invoice", response_model=UploadResponse)
async def upload_invoice(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload and parse an invoice file (PDF, CSV, Excel)
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=400, 
                detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
            )
        
        # Check file extension
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Allowed types: {', '.join(settings.allowed_file_types)}"
            )
        
        # Generate unique file path
        file_id = str(uuid.uuid4())
        file_path = f"invoices/{file_id}_{file.filename}"
        
        # Upload file to Supabase storage
        try:
            db.upload_file(
                file_path=file_path,
                file_content=file_content,
                content_type=file.content_type
            )
        except Exception as e:
            logger.error(f"Failed to upload file to storage: {e}")
            raise HTTPException(status_code=500, detail="Failed to upload file to storage")
        
        # Create initial database record
        invoice_data = {
            "id": file_id,
            "file_path": file_path,
            "status": ParsingStatus.PROCESSING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            db.insert_invoice(invoice_data)
        except Exception as e:
            logger.error(f"Failed to create invoice record: {e}")
            raise HTTPException(status_code=500, detail="Failed to create invoice record")
        
        # Start background parsing task
        background_tasks.add_task(
            parse_invoice_background,
            file_id=file_id,
            file_path=file_path,
            file_content=file_content,
            file_extension=file_extension
        )
        
        return UploadResponse(
            message="Invoice uploaded successfully. Parsing in progress.",
            file_id=file_id,
            file_path=file_path,
            status=ParsingStatus.PROCESSING
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_invoice: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def parse_invoice_background(
    file_id: str,
    file_path: str,
    file_content: bytes,
    file_extension: str
):
    """Background task to parse invoice file"""
    try:
        # Initialize parser
        parser = InvoiceParser()
        
        # Parse the file
        parse_result = parser.parse_file(file_path, file_content)
        
        # Extract parsed data
        parsed_data = parse_result.get("parsed_data", {})
        raw_text = parse_result.get("raw_text", "")
        
        # Prepare update data
        update_data = {
            "status": ParsingStatus.PARSED.value,
            "raw_text": raw_text,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Add parsed fields if available
        if parsed_data.get("invoice_number"):
            update_data["invoice_number"] = parsed_data["invoice_number"]
        if parsed_data.get("invoice_date"):
            update_data["invoice_date"] = parsed_data["invoice_date"]
        if parsed_data.get("vendor_name"):
            update_data["vendor_name"] = parsed_data["vendor_name"]
        if parsed_data.get("vendor_gstin"):
            update_data["vendor_gstin"] = parsed_data["vendor_gstin"]
        if parsed_data.get("taxable_value"):
            update_data["taxable_value"] = parsed_data["taxable_value"]
        if parsed_data.get("gst_amount"):
            update_data["gst_amount"] = parsed_data["gst_amount"]
        if parsed_data.get("invoice_total"):
            update_data["invoice_total"] = parsed_data["invoice_total"]
        if parsed_data.get("payment_terms"):
            update_data["payment_terms"] = parsed_data["payment_terms"]
        if parsed_data.get("invoice_currency"):
            update_data["invoice_currency"] = parsed_data["invoice_currency"]
        if parsed_data.get("items"):
            update_data["items"] = parsed_data["items"]
        
        # Update database record
        db.update_invoice_status(file_id, ParsingStatus.PARSED.value, update_data)
        
        logger.info(f"Successfully parsed invoice {file_id}")
        
    except Exception as e:
        logger.error(f"Error parsing invoice {file_id}: {e}")
        # Update status to error
        try:
            db.update_invoice_status(
                file_id, 
                ParsingStatus.ERROR.value,
                {"updated_at": datetime.utcnow().isoformat()}
            )
        except Exception as update_error:
            logger.error(f"Failed to update error status for invoice {file_id}: {update_error}")

@router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices():
    """
    Get all invoices
    """
    try:
        # This would typically fetch from database
        # For now, return empty list
        return []
    except Exception as e:
        logger.error(f"Error fetching invoices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str):
    """
    Get a specific invoice by ID
    """
    try:
        # This would typically fetch from database
        # For now, return 404
        raise HTTPException(status_code=404, detail="Invoice not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching invoice {invoice_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 