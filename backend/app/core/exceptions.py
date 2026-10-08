"""Domain Exceptions and Global Exception Handlers for CareArc.

Provides consistent, structured JSON error responses across all endpoints.
"""

from typing import Any, Optional
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError


class CareArcException(Exception):
    """Base domain exception for CareArc."""

    def __init__(self, message: str, details: Optional[Any] = None):
        self.message = message
        self.details = details
        super().__init__(message)


class EntityNotFoundException(CareArcException):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: Optional[str] = None,
        entity_name: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Any] = None,
    ):
        if not message:
            if entity_name and entity_id:
                message = f"{entity_name} with ID '{entity_id}' not found."
            elif entity_name:
                message = f"{entity_name} not found."
            elif entity_id:
                message = f"Resource with ID '{entity_id}' not found."
            else:
                message = "Resource not found."
        super().__init__(message=message, details=details)



class EntityConflictException(CareArcException):
    """Raised when an operation conflicts with existing entity state (e.g. duplicate key)."""
    pass


class ClinicalValidationException(CareArcException):
    """Raised when input violates clinical bounds or domain rules."""
    pass


def setup_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers with the FastAPI application instance."""

    @app.exception_handler(EntityNotFoundException)
    async def not_found_handler(request: Request, exc: EntityNotFoundException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": True,
                "statusCode": 404,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(EntityConflictException)
    async def conflict_handler(request: Request, exc: EntityConflictException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": True,
                "statusCode": 409,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(ClinicalValidationException)
    async def validation_handler(request: Request, exc: ClinicalValidationException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": True,
                "statusCode": 400,
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "statusCode": 500,
                "message": "An unexpected internal server error occurred.",
                "details": str(exc) if request.app.debug else None,
            },
        )
