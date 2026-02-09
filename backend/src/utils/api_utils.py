"""Utilities for FastAPI endpoints.

This module provides reusable decorators and dependency injection utilities
to reduce boilerplate in API endpoints.
"""

import logging
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from fastapi import HTTPException

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class ServiceError(Exception):
    """Custom exception for service-related errors."""

    def __init__(self, message: str, status_code: int = 503):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def ensure_service(service: Any, service_name: str) -> None:
    """Ensure a service is available, raising ServiceError if not.

    Args:
        service: The service instance to check.
        service_name: Human-readable name for error messages.

    Raises:
        ServiceError: If the service is None or unavailable.
    """
    if service is None:
        raise ServiceError(f"{service_name} service not available", status_code=503)


def handle_api_errors(func: F) -> F:
    """Decorator for consistent error handling in API endpoints.

    Catches ServiceError and converts to appropriate HTTPException.
    Logs all unexpected errors with full context.

    Args:
        func: The async endpoint function to wrap.

    Returns:
        Wrapped function with error handling.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except ServiceError as e:
            logger.error(f"Service error in {func.__name__}: {e.message}")
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail="An unexpected error occurred"
            )

    return wrapper  # type: ignore


def handle_api_errors_sync(func: F) -> F:
    """Synchronous version of handle_api_errors for non-async endpoints."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except HTTPException:
            raise
        except ServiceError as e:
            logger.error(f"Service error in {func.__name__}: {e.message}")
            raise HTTPException(status_code=e.status_code, detail=e.message)
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail="An unexpected error occurred"
            )

    return wrapper  # type: ignore


def validate_positive_int(value: int, name: str, min_val: int = 1, max_val: Optional[int] = None) -> int:
    """Validate that an integer is within acceptable bounds.

    Args:
        value: The value to validate.
        name: Parameter name for error messages.
        min_val: Minimum acceptable value.
        max_val: Maximum acceptable value (optional).

    Returns:
        The validated value.

    Raises:
        HTTPException: If validation fails.
    """
    if value < min_val:
        raise HTTPException(
            status_code=400, detail=f"{name} must be at least {min_val}"
        )
    if max_val is not None and value > max_val:
        raise HTTPException(
            status_code=400, detail=f"{name} must be at most {max_val}"
        )
    return value


def validate_string_length(value: str, name: str, min_len: int = 1, max_len: Optional[int] = None) -> str:
    """Validate string length constraints.

    Args:
        value: The string to validate.
        name: Parameter name for error messages.
        min_len: Minimum acceptable length.
        max_len: Maximum acceptable length (optional).

    Returns:
        The validated string.

    Raises:
        HTTPException: If validation fails.
    """
    if len(value) < min_len:
        raise HTTPException(
            status_code=400, detail=f"{name} must be at least {min_len} characters"
        )
    if max_len is not None and len(value) > max_len:
        raise HTTPException(
            status_code=400, detail=f"{name} must be at most {max_len} characters"
        )
    return value
