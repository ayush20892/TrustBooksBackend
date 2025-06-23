import os
import uuid
import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.models import UploadResponse, BankStatementResponse, ParsingStatus
from app.database import db
from app.parsers.bank_statement_parser import BankStatementParser
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/upload-bank-statement", response_model=UploadResponse)
async def upload_bank_statement(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Upload and parse a bank statement file (PDF, CSV, Excel)
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
        file_path = f"bank_statements/{file_id}_{file.filename}"
        
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
        statement_data = {
            "id": file_id,
            "file_path": file_path,
            "status": ParsingStatus.PROCESSING.value,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        try:
            db.insert_bank_statement(statement_data)
        except Exception as e:
            logger.error(f"Failed to create bank statement record: {e}")
            raise HTTPException(status_code=500, detail="Failed to create bank statement record")
        
        # Start background parsing task
        background_tasks.add_task(
            parse_bank_statement_background,
            file_id=file_id,
            file_path=file_path,
            file_content=file_content,
            file_extension=file_extension
        )
        
        return UploadResponse(
            message="Bank statement uploaded successfully. Parsing in progress.",
            file_id=file_id,
            file_path=file_path,
            status=ParsingStatus.PROCESSING
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upload_bank_statement: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

async def parse_bank_statement_background(
    file_id: str,
    file_path: str,
    file_content: bytes,
    file_extension: str
):
    """Background task to parse bank statement file"""
    try:
        # Initialize parser
        parser = BankStatementParser()
        
        # For CSV files, use specialized parsing
        if file_extension == '.csv':
            transactions = parser.parse_csv_statement(file_content)
            if transactions:
                # Process multiple transactions
                for i, transaction in enumerate(transactions):
                    transaction_id = f"{file_id}_txn_{i}"
                    transaction_data = {
                        "id": transaction_id,
                        "file_path": file_path,
                        "status": ParsingStatus.PARSED.value,
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    transaction_data.update(transaction)
                    
                    # Insert transaction record
                    db.insert_bank_statement(transaction_data)
                
                # Update main record status
                db.update_bank_statement_status(
                    file_id, 
                    ParsingStatus.PARSED.value,
                    {"updated_at": datetime.utcnow().isoformat()}
                )
            else:
                # Fallback to general parsing
                parse_result = parser.parse_file(file_path, file_content)
                await _update_statement_data(file_id, parse_result)
        else:
            # Use general parsing for PDF and Excel
            parse_result = parser.parse_file(file_path, file_content)
            await _update_statement_data(file_id, parse_result)
        
        logger.info(f"Successfully parsed bank statement {file_id}")
        
    except Exception as e:
        logger.error(f"Error parsing bank statement {file_id}: {e}")
        # Update status to error
        try:
            db.update_bank_statement_status(
                file_id, 
                ParsingStatus.ERROR.value,
                {"updated_at": datetime.utcnow().isoformat()}
            )
        except Exception as update_error:
            logger.error(f"Failed to update error status for bank statement {file_id}: {update_error}")

async def _update_statement_data(file_id: str, parse_result: dict):
    """Helper function to update bank statement data"""
    parsed_data = parse_result.get("parsed_data", {})
    raw_text = parse_result.get("raw_text", "")
    
    # Prepare update data
    update_data = {
        "status": ParsingStatus.PARSED.value,
        "raw_text": raw_text,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    # Add parsed fields if available
    if parsed_data.get("txn_date"):
        update_data["txn_date"] = parsed_data["txn_date"]
    if parsed_data.get("description"):
        update_data["description"] = parsed_data["description"]
    if parsed_data.get("debit"):
        update_data["debit"] = parsed_data["debit"]
    if parsed_data.get("credit"):
        update_data["credit"] = parsed_data["credit"]
    if parsed_data.get("balance"):
        update_data["balance"] = parsed_data["balance"]
    if parsed_data.get("account_number"):
        update_data["account_number"] = parsed_data["account_number"]
    if parsed_data.get("mode"):
        update_data["mode"] = parsed_data["mode"]
    if parsed_data.get("category"):
        update_data["category"] = parsed_data["category"]
    if parsed_data.get("meta_data"):
        update_data["meta_data"] = parsed_data["meta_data"]
    
    # Update database record
    db.update_bank_statement_status(file_id, ParsingStatus.PARSED.value, update_data)

@router.get("/bank-statements", response_model=List[BankStatementResponse])
async def get_bank_statements():
    """
    Get all bank statements
    """
    try:
        # This would typically fetch from database
        # For now, return empty list
        return []
    except Exception as e:
        logger.error(f"Error fetching bank statements: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/bank-statements/{statement_id}", response_model=BankStatementResponse)
async def get_bank_statement(statement_id: str):
    """
    Get a specific bank statement by ID
    """
    try:
        # This would typically fetch from database
        # For now, return 404
        raise HTTPException(status_code=404, detail="Bank statement not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching bank statement {statement_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error") 