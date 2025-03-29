from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
from .logger import logger
import traceback

class RequestLoggingMiddleware(BaseHTTPMiddleware):  # Rename to match the import in main.py
    async def dispatch(self, request: Request, call_next):
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        
        # Log initial request
        logger.info("Request started", extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host,
            "query_params": str(request.query_params),
            "headers": {k: v for k, v in request.headers.items() if k.lower() != "authorization"}
        })
        
        try:
            response = await call_next(request)
            
            process_time = time.time() - start_time
            status_code = response.status_code
            
            # Log errors (4xx, 5xx)
            if status_code >= 400:
                logger.error("Request failed", extra={
                    "correlation_id": correlation_id,
                    "status_code": status_code,
                    "method": request.method,
                    "path": request.url.path,
                    "process_time": f"{process_time:.3f}s",
                    "error_type": "HTTP_ERROR"
                })
            else:
                # Log successful requests
                logger.info("Request completed", extra={
                    "correlation_id": correlation_id,
                    "status_code": status_code,
                    "process_time": f"{process_time:.3f}s"
                })
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            # Log unhandled exceptions
            logger.error("Request failed with exception", extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "path": request.url.path,
                "method": request.method,
                "process_time": f"{process_time:.3f}s",
                "traceback": traceback.format_exc()
            })
            raise

__all__ = ['RequestLoggingMiddleware']