"""Health check endpoints."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.config import APISettings, get_settings
from src.api.schemas import HealthResponse, ReadinessResponse
from src.api.services.bigquery_service import BigQueryService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Simple health check endpoint.

    Returns:
        Health status
    """
    return HealthResponse(status="healthy")


@router.get("/health/readiness", response_model=ReadinessResponse)
async def readiness_check(
    settings: Annotated[APISettings, Depends(get_settings)],
) -> ReadinessResponse:
    """Readiness check with dependency verification.

    Checks BigQuery connectivity.

    Returns:
        Readiness status with component health
    """
    bq_service = BigQueryService(settings)

    if bq_service.check_connection():
        bq_status = "connected"
    else:
        bq_status = "disconnected"

    status = "ready" if bq_status == "connected" else "not_ready"

    return ReadinessResponse(
        status=status,
        bigquery=bq_status,
        timestamp=datetime.utcnow(),
    )
