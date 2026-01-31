"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.config import get_settings
from src.api.routers import health_router, stats_router, zones_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    settings = get_settings()
    logger.info(f"Starting NYC Taxi API in {settings.environment} mode")
    logger.info(f"Project: {settings.project_id}, Dataset: {settings.bq_dataset}")
    yield
    logger.info("Shutting down NYC Taxi API")


# Create FastAPI app
app = FastAPI(
    title="NYC Taxi Analytics API",
    description="REST API for NYC TLC taxi trip analytics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "detail": str(exc) if get_settings().debug else None,
        },
    )


# Include routers
app.include_router(health_router)
app.include_router(zones_router)
app.include_router(stats_router)


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "NYC Taxi Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


def run():
    """Run the application with uvicorn."""
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=not settings.is_production,
        log_level="info",
    )


if __name__ == "__main__":
    run()
