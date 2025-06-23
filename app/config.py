import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Supabase Configuration
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_key: str = os.getenv("SUPABASE_KEY", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # Google Gemini Configuration
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Storage Configuration
    storage_bucket_name: str = os.getenv("STORAGE_BUCKET_NAME", "trustbooks-files")
    
    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".pdf", ".csv", ".xlsx", ".xls"]
    
    class Config:
        env_file = ".env"

settings = Settings() 