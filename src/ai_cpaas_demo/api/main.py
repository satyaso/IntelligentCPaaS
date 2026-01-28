"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config.settings import settings

# Create FastAPI app
app = FastAPI(
    title="AI-CPaaS Demo API",
    description="AI-powered Communications Platform as a Service demonstration",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=settings.api.cors_credentials,
    allow_methods=settings.api.cors_methods,
    allow_headers=settings.api.cors_headers,
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI-CPaaS Demo API",
        "version": "0.1.0",
        "variant": settings.variant,
        "environment": settings.environment,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "variant": settings.variant,
        "environment": settings.environment,
    }


# TODO: Add route imports here as they are implemented
# from .routes import prediction, adaptation, guardrail, fatigue, analytics, demo