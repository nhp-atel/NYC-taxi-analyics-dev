"""Zone statistics endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.config import APISettings, get_settings
from src.api.schemas import ZoneStatsResponse, ErrorResponse
from src.api.services.bigquery_service import BigQueryService

router = APIRouter(prefix="/api/v1/zones", tags=["zones"])


@router.get(
    "/{zone_id}/stats",
    response_model=ZoneStatsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Zone or date not found"},
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
    },
)
async def get_zone_stats(
    zone_id: int,
    stat_date: Annotated[date, Query(alias="date", description="Statistics date (YYYY-MM-DD)")],
    settings: Annotated[APISettings, Depends(get_settings)],
) -> ZoneStatsResponse:
    """Get statistics for a specific zone on a specific date.

    Args:
        zone_id: NYC TLC zone ID (1-265)
        stat_date: Date for statistics

    Returns:
        Zone statistics for the specified date
    """
    # Validate zone_id range
    if zone_id < 1 or zone_id > 265:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid zone_id: {zone_id}. Must be between 1 and 265.",
        )

    bq_service = BigQueryService(settings)
    result = bq_service.get_zone_stats(zone_id, stat_date)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for zone {zone_id} on {stat_date}",
        )

    return ZoneStatsResponse(**result)
