#!/usr/bin/env python3
"""
Test script to check Supabase database connection
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test Supabase connection and basic operations"""
    try:
        from supabase import create_client, Client
        
        # Get credentials from environment
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        storage_bucket = os.getenv("STORAGE_BUCKET_NAME", "trustbooks-files")
        
        print("🔍 Checking Supabase Configuration...")
        print(f"URL: {supabase_url}")
        print(f"Key: {supabase_key[:20]}..." if supabase_key else "Key: Not set")
        print(f"Storage Bucket: {storage_bucket}")
        print()
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL or SUPABASE_KEY not set in .env file")
            return False
        
        # Create client
        print("🔌 Connecting to Supabase...")
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Successfully connected to Supabase!")
        
        # Test database tables
        print("\n📊 Testing database tables...")
        
        # Test invoices table
        try:
            response = supabase.table("invoices").select("*").limit(1).execute()
            print("✅ Invoices table exists and accessible")
        except Exception as e:
            print(f"❌ Error accessing invoices table: {e}")
            return False
        
        # Test bank_statements table
        try:
            response = supabase.table("bank_statements").select("*").limit(1).execute()
            print("✅ Bank statements table exists and accessible")
        except Exception as e:
            print(f"❌ Error accessing bank_statements table: {e}")
            return False
        
        # Test storage bucket
        print("\n🗂️ Testing storage bucket...")
        try:
            response = supabase.storage.from_(storage_bucket).list()
            print(f"✅ Storage bucket '{storage_bucket}' exists and accessible")
        except Exception as e:
            print(f"❌ Error accessing storage bucket '{storage_bucket}': {e}")
            print("💡 Make sure you've created the storage bucket in Supabase dashboard")
            return False
        
        print("\n🎉 All database tests passed!")
        return True
        
    except ImportError:
        print("❌ Error: supabase package not installed")
        print("Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TrustBooks Backend - Database Connection Test")
    print("=" * 50)
    
    success = test_supabase_connection()
    
    if success:
        print("\n✅ Database connection is working properly!")
        sys.exit(0)
    else:
        print("\n❌ Database connection test failed!")
        sys.exit(1) 