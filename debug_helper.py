#!/usr/bin/env python3
"""
Debug helper utilities for TrustBooks Backend
"""

import json
import logging
from typing import Any, Dict
from datetime import datetime

# Configure debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def debug_request(request_data: Dict[str, Any], label: str = "REQUEST"):
    """Debug helper to log request data"""
    print(f"\n🔍 {label} DEBUG:")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Data: {json.dumps(request_data, indent=2, default=str)}")
    print("=" * 50)

def debug_response(response_data: Dict[str, Any], label: str = "RESPONSE"):
    """Debug helper to log response data"""
    print(f"\n📤 {label} DEBUG:")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Data: {json.dumps(response_data, indent=2, default=str)}")
    print("=" * 50)

def debug_database_operation(operation: str, table: str, data: Dict[str, Any] = None):
    """Debug helper to log database operations"""
    print(f"\n🗄️ DATABASE DEBUG:")
    print("=" * 50)
    print(f"Operation: {operation}")
    print(f"Table: {table}")
    if data:
        print(f"Data: {json.dumps(data, indent=2, default=str)}")
    print("=" * 50)

def debug_file_operation(operation: str, file_path: str, file_size: int = None):
    """Debug helper to log file operations"""
    print(f"\n📁 FILE DEBUG:")
    print("=" * 50)
    print(f"Operation: {operation}")
    print(f"File: {file_path}")
    if file_size:
        print(f"Size: {file_size} bytes")
    print("=" * 50)

def debug_error(error: Exception, context: str = ""):
    """Debug helper to log errors"""
    print(f"\n❌ ERROR DEBUG:")
    print("=" * 50)
    print(f"Context: {context}")
    print(f"Error Type: {type(error).__name__}")
    print(f"Error Message: {str(error)}")
    print("=" * 50)

# Example usage in your code:
"""
# In your route handlers, you can use these like:

from debug_helper import debug_request, debug_response, debug_database_operation

@router.post("/upload-invoice")
async def upload_invoice(file: UploadFile):
    # Debug the incoming request
    debug_request({
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(await file.read())
    }, "INVOICE UPLOAD")
    
    # Your processing logic here...
    
    # Debug the response
    debug_response({
        "status": "success",
        "file_id": file_id
    }, "INVOICE UPLOAD RESPONSE")
    
    # Debug database operation
    debug_database_operation("INSERT", "invoices", invoice_data)
""" 