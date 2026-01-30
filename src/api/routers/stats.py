"""Daily and hourly statistics endpoints."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.config import APISettings, get_settings
from src.api.schemas import DailyStatsResponse, ErrorResponse
from src.api.schemas.responses import HourlyPatternsResponse
from src.api.services.bigquery_service import BigQueryService

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get(
    "/daily/{stat_date}",
    response_model=DailyStatsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Date not found"},
    },
)
async def get_daily_stats(
    stat_date: date,
    settings: Annotated[APISettings, Depends(get_settings)],
) -> DailyStatsResponse:
    """Get aggregate daily statistics.

    Args:
        stat_date: Date for statistics (YYYY-MM-DD)

    Returns:
        Daily aggregate statistics including top zones
    """
    bq_service = BigQueryService(settings)
    result = bq_service.get_daily_stats(stat_date)

    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for {stat_date}",
        )

    return DailyStatsResponse(**result)


@router.get(
    "/hourly/{stat_date}",
    response_model=HourlyPatternsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Date not found"},
    },
)
async def get_hourly_patterns(
    stat_date: date,
    zone_id: Annotated[
        int | None,
        Query(description="Optional zone ID filter"),
    ] = None,
    settings: Annotated[APISettings, Depends(get_settings)] = None,
) -> HourlyPatternsResponse:
    """Get hourly trip patterns for a date.

    Args:
        stat_date: Date for statistics (YYYY-MM-DD)
        zone_id: Optional zone ID to filter by

    Returns:
        Hourly trip patterns
    """
    if zone_id is not None and (zone_id < 1 or zone_id > 265):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid zone_id: {zone_id}. Must be between 1 and 265.",
        )

    bq_service = BigQueryService(settings)
    patterns = bq_service.get_hourly_patterns(stat_date, zone_id)

    if not patterns:
        raise HTTPException(
            status_code=404,
            detail=f"No hourly data found for {stat_date}",
        )

    return HourlyPatternsResponse(
        date=stat_date,
        zone_id=zone_id,
        patterns=patterns,
    )
