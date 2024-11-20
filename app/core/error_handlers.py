from fastapi import Request, status
from fastapi.responses import JSONResponse
from .exceptions import EmailAssistantException
from .logging_config import logger

async def email_assistant_exception_handler(request: Request, exc: EmailAssistantException):
    """Handle custom exceptions"""
    logger.error(
        f"Error processing request",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": exc.__class__.__name__,
            "error_message": exc.message,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message
        }
    )

async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    logger.error(
        f"Unexpected error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "error_type": exc.__class__.__name__,
            "error_message": str(exc)
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred"
        }
    )
