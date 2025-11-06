from functools import wraps
from fastapi import HTTPException, status, Request
from typing import Callable, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# In-memory storage for rate limiting
# Format: {identifier: {"count": int, "reset_time": datetime}}
rate_limit_store: Dict[str, Dict] = {}

def rate_limit(max_requests: int = 60, window: int = 60):
    """
    Rate limiting decorator for FastAPI routes

    Args:
        max_requests: Maximum number of requests allowed
        window: Time window in seconds

    Usage:
        @router.get("/endpoint")
        @rate_limit(max_requests=10, window=60)
        async def my_endpoint():
            ...
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to get request from kwargs
            request = kwargs.get("request")

            if not request:
                # If no request in kwargs, look in args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break

            # Get client identifier (IP address)
            if request:
                client_ip = request.client.host if request.client else "unknown"
            else:
                client_ip = "unknown"

            # Create unique key for this endpoint and client
            endpoint = func.__name__
            key = f"{endpoint}:{client_ip}"

            # Get current time
            now = datetime.utcnow()

            # Check if key exists in store
            if key in rate_limit_store:
                data = rate_limit_store[key]

                # Check if window has expired
                if now > data["reset_time"]:
                    # Reset the counter
                    rate_limit_store[key] = {
                        "count": 1,
                        "reset_time": now + timedelta(seconds=window)
                    }
                else:
                    # Increment counter
                    data["count"] += 1

                    # Check if limit exceeded
                    if data["count"] > max_requests:
                        reset_in = int((data["reset_time"] - now).total_seconds())
                        logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")

                        raise HTTPException(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            detail=f"Rate limit exceeded. Try again in {reset_in} seconds.",
                            headers={"Retry-After": str(reset_in)}
                        )
            else:
                # First request from this client
                rate_limit_store[key] = {
                    "count": 1,
                    "reset_time": now + timedelta(seconds=window)
                }

            # Call the original function
            return await func(*args, **kwargs)

        return wrapper

    return decorator

def clean_expired_entries():
    """
    Clean up expired entries from rate limit store
    This should be called periodically (e.g., via a background task)
    """
    now = datetime.utcnow()
    expired_keys = [
        key for key, data in rate_limit_store.items()
        if now > data["reset_time"]
    ]

    for key in expired_keys:
        del rate_limit_store[key]

    if expired_keys:
        logger.info(f"Cleaned up {len(expired_keys)} expired rate limit entries")

def get_rate_limit_info(endpoint: str, client_ip: str) -> Dict:
    """
    Get rate limit information for a specific endpoint and client

    Args:
        endpoint: Function name of the endpoint
        client_ip: Client IP address

    Returns:
        Dict with count and reset_time, or None if not found
    """
    key = f"{endpoint}:{client_ip}"
    return rate_limit_store.get(key)

def reset_rate_limit(endpoint: str, client_ip: str):
    """
    Reset rate limit for a specific endpoint and client

    Args:
        endpoint: Function name of the endpoint
        client_ip: Client IP address
    """
    key = f"{endpoint}:{client_ip}"
    if key in rate_limit_store:
        del rate_limit_store[key]
        logger.info(f"Reset rate limit for {client_ip} on {endpoint}")
