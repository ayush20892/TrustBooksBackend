# TrustBooks Backend New

A FastAPI-based backend service for parsing and storing invoices and bank statements using AI-powered extraction with Google Gemini.

## Features

- **File Upload**: Accept PDF, CSV, and Excel files via multipart/form-data
- **AI-Powered Parsing**: Uses Google Gemini models via LangChain for intelligent field extraction
- **Supabase Integration**: File storage and database management
- **Background Processing**: Asynchronous file parsing with status tracking
- **Comprehensive Field Extraction**: Extracts all relevant fields from invoices and bank statements

## Invoice Parsing

Extracts the following fields from invoice documents:

- Invoice number
- Invoice date
- Vendor name
- Vendor GSTIN
- Taxable value
- GST amount
- Invoice total
- Payment terms
- Invoice currency
- Item list (if available)

## Bank Statement Parsing

Extracts the following fields from bank statements:

- Transaction date
- Description (vendor, UPI, NEFT, etc.)
- Debit/Credit amounts
- Closing balance
- Bank account number
- Mode of payment (UPI, IMPS, NEFT, etc.)
- Transaction category
- Meta data (user account info, sender/receiver info)

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Supabase**: Backend-as-a-Service for database and file storage
- **Google Gemini**: AI-powered text extraction and parsing
- **LangChain**: Framework for building LLM applications
- **Pandas**: Data manipulation for CSV/Excel files
- **PyPDF2/pdfplumber**: PDF text extraction
- **Pydantic**: Data validation and serialization

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd TrustBooksBackend
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Copy the environment example file and configure your variables:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key

# Storage Configuration
STORAGE_BUCKET_NAME=your_storage_bucket_name
```

### 4. Get Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add the API key to your `.env` file

### 5. Database Setup

1. Create a new Supabase project
2. Run the SQL schema in your Supabase SQL editor:

```sql
-- Copy and execute the contents of database_schema.sql
```

3. Create a storage bucket named `trustbooks-files` (or update the bucket name in your .env)

### 6. Run the Application

```bash
# Development mode
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

### Base URL

```
http://localhost:8000/api/v1
```

### Endpoints

#### Upload Invoice

```http
POST /upload-invoice
Content-Type: multipart/form-data

file: [PDF/CSV/Excel file]
```

**Response:**

```json
{
  "message": "Invoice uploaded successfully. Parsing in progress.",
  "file_id": "uuid-string",
  "file_path": "invoices/uuid_filename.pdf",
  "status": "Processing"
}
```

#### Upload Bank Statement

```http
POST /upload-bank-statement
Content-Type: multipart/form-data

file: [PDF/CSV/Excel file]
```

**Response:**

```json
{
  "message": "Bank statement uploaded successfully. Parsing in progress.",
  "file_id": "uuid-string",
  "file_path": "bank_statements/uuid_filename.csv",
  "status": "Processing"
}
```

#### Get Invoices

```http
GET /invoices
```

#### Get Invoice by ID

```http
GET /invoices/{invoice_id}
```

#### Get Bank Statements

```http
GET /bank-statements
```

#### Get Bank Statement by ID

```http
GET /bank-statements/{statement_id}
```

### Interactive API Documentation

Once the server is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## File Processing Pipeline

1. **File Upload**: Client uploads file via multipart/form-data
2. **Validation**: File size and type validation
3. **Storage**: File uploaded to Supabase storage
4. **Database Record**: Initial record created with "Processing" status
5. **Background Parsing**: Asynchronous parsing using Google Gemini models
6. **Field Extraction**: Relevant fields extracted using AI
7. **Database Update**: Parsed data stored in database
8. **Status Update**: Record status updated to "Parsed" or "Error"

## Supported File Formats

- **PDF**: Using PyPDF2 and pdfplumber for text extraction
- **CSV**: Using Pandas for structured data parsing
- **Excel**: Using Pandas for .xlsx and .xls files

## Error Handling

The application includes comprehensive error handling:

- File validation errors (size, type)
- Storage upload failures
- Parsing errors with fallback mechanisms
- Database operation failures
- AI model errors with regex fallback

## Development

### Project Structure

```
TrustBooksBackend/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration and environment variables
│   ├── database.py        # Supabase database operations
│   ├── models.py          # Pydantic models
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── base_parser.py # Base parser class
│   │   ├── invoice_parser.py
│   │   └── bank_statement_parser.py
│   └── routers/
│       ├── __init__.py
│       ├── invoice_router.py
│       └── bank_statement_router.py
├── main.py                # FastAPI application entry point
├── requirements.txt       # Python dependencies
├── database_schema.sql    # Database schema
├── env.example           # Environment variables template
└── README.md
```

### Adding New Parsers

1. Create a new parser class inheriting from `BaseParser`
2. Implement the `_parse_content` method
3. Add the parser to the appropriate router
4. Update the database schema if needed

### Testing

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest
```

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

Ensure all environment variables are properly set in your production environment:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `SUPABASE_SERVICE_KEY`
- `GOOGLE_API_KEY`
- `STORAGE_BUCKET_NAME`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
