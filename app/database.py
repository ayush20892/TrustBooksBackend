from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.supabase: Client = None
        self._connect()
    
    def _connect(self):
        """Initialize Supabase connection"""
        try:
            self.supabase = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("Successfully connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    def upload_file(self, file_path: str, file_content: bytes, content_type: str = None):
        """Upload file to Supabase storage"""
        try:
            response = self.supabase.storage.from_(settings.storage_bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={"content-type": content_type} if content_type else None
            )
            return response
        except Exception as e:
            logger.error(f"Failed to upload file {file_path}: {e}")
            raise
    
    def get_file_url(self, file_path: str):
        """Get public URL for uploaded file"""
        try:
            response = self.supabase.storage.from_(settings.storage_bucket_name).get_public_url(file_path)
            return response
        except Exception as e:
            logger.error(f"Failed to get file URL for {file_path}: {e}")
            raise
    
    def insert_invoice(self, invoice_data: dict):
        """Insert invoice record into database"""
        try:
            response = self.supabase.table("invoices").insert(invoice_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to insert invoice: {e}")
            raise
    
    def insert_bank_statement(self, statement_data: dict):
        """Insert bank statement record into database"""
        try:
            response = self.supabase.table("bank_statements").insert(statement_data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to insert bank statement: {e}")
            raise
    
    def update_invoice_status(self, invoice_id: str, status: str, parsed_data: dict = None):
        """Update invoice parsing status and data"""
        try:
            update_data = {"status": status}
            if parsed_data:
                update_data.update(parsed_data)
            
            response = self.supabase.table("invoices").update(update_data).eq("id", invoice_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to update invoice {invoice_id}: {e}")
            raise
    
    def update_bank_statement_status(self, statement_id: str, status: str, parsed_data: dict = None):
        """Update bank statement parsing status and data"""
        try:
            update_data = {"status": status}
            if parsed_data:
                update_data.update(parsed_data)
            
            response = self.supabase.table("bank_statements").update(update_data).eq("id", statement_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to update bank statement {statement_id}: {e}")
            raise

# Global database instance
db = DatabaseManager() 