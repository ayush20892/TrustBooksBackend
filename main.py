from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from app.routers import invoice_router, bank_statement_router
from app.config import settings
from app.middleware import DebugMiddleware

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

app = FastAPI(
    title="TrustBooks Backend",
    description="File parsing and storage API for invoices and bank statements",
    version="1.0.0"
)

# Add debug middleware
app.add_middleware(DebugMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(invoice_router.router, prefix="/api/v1", tags=["invoices"])
app.include_router(bank_statement_router.router, prefix="/api/v1", tags=["bank-statements"])

@app.get("/")
async def root():
    return {"message": "TrustBooks Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 