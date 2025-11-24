"""
Custom Exception Handlers for Artify Platform
Provides centralized error handling with proper logging and user-friendly messages
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from openai import OpenAIError, RateLimitError, APIError
from slowapi.errors import RateLimitExceeded
from logger import get_logger
import traceback

logger = get_logger("exceptions")


class ArtifyException(Exception):
    """Base exception for Artify platform"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class QuotaExceededError(ArtifyException):
    """Raised when user quota is exceeded"""

    def __init__(self, quota_type: str, limit: int, used: int):
        super().__init__(
            message=f"{quota_type} quota exceeded",
            status_code=429,
            error_code="QUOTA_EXCEEDED",
            details={
                "quota_type": quota_type,
                "limit": limit,
                "used": used,
                "available": max(0, limit - used)
            }
        )


class CacheError(ArtifyException):
    """Raised when cache operation fails"""

    def __init__(self, operation: str, key: str, error: str):
        super().__init__(
            message=f"Cache {operation} failed for key: {key}",
            status_code=500,
            error_code="CACHE_ERROR",
            details={
                "operation": operation,
                "key": key,
                "error": str(error)
            }
        )


class VectorDBError(ArtifyException):
    """Raised when vector database operation fails"""

    def __init__(self, operation: str, error: str):
        super().__init__(
            message=f"Vector database {operation} failed",
            status_code=500,
            error_code="VECTOR_DB_ERROR",
            details={
                "operation": operation,
                "error": str(error)
            }
        )


# Exception Handlers

async def artify_exception_handler(request: Request, exc: ArtifyException):
    """Handle custom Artify exceptions"""
    logger.error(
        f"ArtifyException: {exc.error_code} - {exc.message}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path
        }
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors"""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(
        f"Validation error on {request.url.path}",
        extra={
            "errors": errors,
            "path": request.url.path
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {
                    "errors": errors
                }
            }
        }
    )


async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit errors"""
    logger.warning(
        f"Rate limit exceeded for {request.client.host} on {request.url.path}",
        extra={
            "client_ip": request.client.host,
            "path": request.url.path
        }
    )

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Too many requests. Please try again later.",
                "details": {
                    "limit": str(exc.detail)
                }
            }
        }
    )


async def openai_exception_handler(request: Request, exc: OpenAIError):
    """Handle OpenAI API errors"""
    error_message = str(exc)
    error_code = "OPENAI_ERROR"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    if isinstance(exc, RateLimitError):
        error_code = "OPENAI_RATE_LIMIT"
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
        error_message = "OpenAI rate limit exceeded. Please try again later."
    elif isinstance(exc, APIError):
        error_code = "OPENAI_API_ERROR"
        error_message = "OpenAI API error occurred"

    logger.error(
        f"OpenAI error: {error_message}",
        extra={
            "error_code": error_code,
            "path": request.url.path,
            "exception_type": type(exc).__name__
        }
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": error_message,
                "details": {}
            }
        }
    )


async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    logger.error(
        f"Database error: {str(exc)}",
        extra={
            "path": request.url.path,
            "exception_type": type(exc).__name__
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "DATABASE_ERROR",
                "message": "A database error occurred. Please try again later.",
                "details": {}
            }
        }
    )


async def generic_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    # Log full traceback
    logger.critical(
        f"Unhandled exception: {str(exc)}",
        extra={
            "path": request.url.path,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": {}
            }
        }
    )


def register_exception_handlers(app):
    """Register all exception handlers with the FastAPI app"""
    app.add_exception_handler(ArtifyException, artify_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_exception_handler(OpenAIError, openai_exception_handler)
    app.add_exception_handler(SQLAlchemyError, database_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
