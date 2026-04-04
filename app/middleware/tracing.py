from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4
import time
from app.core.logging import logger

class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        # Set request_id in request state to pass it down
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # We can simulate context variables here, or just basic logging
        extra = {"request_id": request_id}
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            logger.info(
                f"Completed request: {request.method} {request.url.path} - {response.status_code}",
                extra=extra
            )
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra=extra,
                exc_info=True
            )
            raise
