from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
from typing import Callable
import asyncio
from fastapi.responses import JSONResponse
from .exceptions import RateLimitError
from .logger import logger

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        rate_limit_per_second: int = 10
    ):
        super().__init__(app)
        self.rate_limit = rate_limit_per_second
        self.requests = {}

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        client_ip = request.client.host
        current_time = time.time()
        
        # Clean old requests
        self.requests = {
            ip: reqs for ip, reqs in self.requests.items()
            if current_time - reqs[-1] < 1
        }
        
        # Check rate limit
        if client_ip in self.requests:
            requests = self.requests[client_ip]
            if len(requests) >= self.rate_limit:
                raise RateLimitError()
            requests.append(current_time)
        else:
            self.requests[client_ip] = [current_time]
        
        return await call_next(request)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = (time.time() - start_time) * 1000
        logger.info(
            f"Request processed",
            extra={
                "path": request.url.path,
                "method": request.method,
                "process_time_ms": round(process_time, 2),
                "status_code": response.status_code
            }
        )
        
        return response

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                f"Unhandled error",
                extra={
                    "path": request.url.path,
                    "method": request.method,
                    "error": str(e)
                },
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
