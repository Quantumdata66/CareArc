"""CareArc FastAPI Main Application Entrypoint.

Configures middleware, exception handlers, and routing.
"""

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.api.v1.router import api_router


def create_application() -> FastAPI:
    """Application factory for the CareArc backend."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # Configure CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register custom exception handlers
    setup_exception_handlers(app)

    # Register API v1 routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Root and health probe endpoints
    @app.get("/health", status_code=status.HTTP_200_OK, tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring and uptime verification."""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/", status_code=status.HTTP_200_OK, tags=["Root"])
    async def root() -> dict[str, str]:
        """Root welcome endpoint."""
        return {
            "message": "CareArc Clinical Intelligence Backend API",
            "docsUrl": "/docs",
            "version": settings.VERSION,
        }

    return app


app = create_application()
