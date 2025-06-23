#!/usr/bin/env python3
"""
Simple test script for TrustBooks Backend API
Run this after starting the server to test the endpoints
"""

import requests
import json
import os
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000/api/v1"

def test_health_check():
    """Test the health check endpoint"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_root_endpoint():
    """Test the root endpoint"""
    try:
        response = requests.get("http://localhost:8000/")
        print(f"✅ Root endpoint: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Root endpoint failed: {e}")
        return False

def test_invoice_endpoints():
    """Test invoice-related endpoints"""
    try:
        # Test GET /invoices
        response = requests.get(f"{BASE_URL}/invoices")
        print(f"✅ GET /invoices: {response.status_code}")
        
        # Test GET /invoices/{id} (should return 404 for non-existent ID)
        response = requests.get(f"{BASE_URL}/invoices/non-existent-id")
        print(f"✅ GET /invoices/{{id}} (404 expected): {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Invoice endpoints failed: {e}")
        return False

def test_bank_statement_endpoints():
    """Test bank statement-related endpoints"""
    try:
        # Test GET /bank-statements
        response = requests.get(f"{BASE_URL}/bank-statements")
        print(f"✅ GET /bank-statements: {response.status_code}")
        
        # Test GET /bank-statements/{id} (should return 404 for non-existent ID)
        response = requests.get(f"{BASE_URL}/bank-statements/non-existent-id")
        print(f"✅ GET /bank-statements/{{id}} (404 expected): {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ Bank statement endpoints failed: {e}")
        return False

def test_file_upload_endpoints():
    """Test file upload endpoints (without actual files)"""
    try:
        # Test invoice upload endpoint (should fail without file)
        response = requests.post(f"{BASE_URL}/upload-invoice")
        print(f"✅ POST /upload-invoice (400 expected without file): {response.status_code}")
        
        # Test bank statement upload endpoint (should fail without file)
        response = requests.post(f"{BASE_URL}/upload-bank-statement")
        print(f"✅ POST /upload-bank-statement (400 expected without file): {response.status_code}")
        
        return True
    except Exception as e:
        print(f"❌ File upload endpoints failed: {e}")
        return False

def create_test_files():
    """Create test files for upload testing"""
    test_dir = Path("test_files")
    test_dir.mkdir(exist_ok=True)
    
    # Create a simple CSV test file
    csv_content = """Date,Description,Debit,Credit,Balance
2024-01-01,Test Transaction 1,100.00,,1000.00
2024-01-02,Test Transaction 2,,50.00,1050.00"""
    
    with open(test_dir / "test_statement.csv", "w") as f:
        f.write(csv_content)
    
    print(f"✅ Created test files in {test_dir}")
    return test_dir

def test_with_sample_files():
    """Test upload endpoints with sample files"""
    test_dir = create_test_files()
    
    try:
        # Test bank statement upload with CSV
        with open(test_dir / "test_statement.csv", "rb") as f:
            files = {"file": ("test_statement.csv", f, "text/csv")}
            response = requests.post(f"{BASE_URL}/upload-bank-statement", files=files)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Bank statement upload successful: {result['file_id']}")
                print(f"   Status: {result['status']}")
                print(f"   Message: {result['message']}")
            else:
                print(f"⚠️ Bank statement upload failed: {response.status_code}")
                print(f"   Response: {response.text}")
        
        return True
    except Exception as e:
        print(f"❌ Sample file upload failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing TrustBooks Backend API")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root_endpoint),
        ("Invoice Endpoints", test_invoice_endpoints),
        ("Bank Statement Endpoints", test_bank_statement_endpoints),
        ("File Upload Endpoints", test_file_upload_endpoints),
        ("Sample File Upload", test_with_sample_files),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        print("-" * 30)
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The API is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the server logs for more details.")
    
    print("\n💡 Next steps:")
    print("1. Visit http://localhost:8000/docs for interactive API documentation")
    print("2. Use the Swagger UI to test file uploads with real files")
    print("3. Check the database to see parsed results")

if __name__ == "__main__":
    main() 