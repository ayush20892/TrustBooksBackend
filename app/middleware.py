import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class DebugMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses for debugging"""
    
    async def dispatch(self, request: Request, call_next):
        # Log request details
        start_time = time.time()
        
        # Get request body for debugging (only for non-GET requests)
        body = None
        if request.method != "GET":
            try:
                body = await request.body()
                # Log body (be careful with sensitive data)
                if len(body) < 1000:  # Only log small bodies
                    logger.debug(f"Request body: {body.decode()}")
            except Exception as e:
                logger.debug(f"Could not read request body: {e}")
        
        logger.info(f"🔍 REQUEST: {request.method} {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")
        logger.debug(f"Query params: {dict(request.query_params)}")
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response details
        logger.info(f"📤 RESPONSE: {response.status_code} - {process_time:.3f}s")
        logger.debug(f"Response headers: {dict(response.headers)}")
        
        # Add custom header for debugging
        response.headers["X-Process-Time"] = str(process_time)
        
        return response 