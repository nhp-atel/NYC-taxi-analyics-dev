"""Pydantic response models for the API."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(default="healthy", description="Health status")


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    status: str = Field(description="Readiness status")
    bigquery: str = Field(description="BigQuery connection status")
    timestamp: datetime = Field(description="Check timestamp")


class ZoneStatsResponse(BaseModel):
    """Zone statistics response."""

    zone_id: int = Field(description="NYC TLC zone ID")
    date: date = Field(description="Statistics date")
    trip_count: int = Field(description="Total trips from this zone")
    total_passengers: int | None = Field(description="Total passengers")
    total_distance: float | None = Field(description="Total trip distance in miles")
    total_fare: float | None = Field(description="Total fare amount")
    total_tip: float | None = Field(description="Total tip amount")
    total_revenue: float | None = Field(description="Total revenue")
    avg_fare: float | None = Field(description="Average fare per trip")
    avg_distance: float | None = Field(description="Average trip distance")
    avg_tip_pct: float | None = Field(description="Average tip percentage")


class TopZone(BaseModel):
    """Top zone summary."""

    zone_id: int = Field(description="Zone ID")
    trip_count: int = Field(description="Number of trips")
    total_revenue: float | None = Field(description="Total revenue")


class DailyStatsResponse(BaseModel):
    """Daily statistics response."""

    date: date = Field(description="Statistics date")
    total_trips: int = Field(description="Total trips for the day")
    total_revenue: float | None = Field(description="Total revenue")
    total_passengers: int | None = Field(description="Total passengers")
    avg_fare: float | None = Field(description="Average fare")
    avg_distance: float | None = Field(description="Average trip distance")
    top_zones: list[TopZone] = Field(description="Top 10 zones by trip count")


class HourlyPattern(BaseModel):
    """Hourly pattern data."""

    hour: int = Field(description="Hour of day (0-23)")
    trip_count: int = Field(description="Number of trips")
    avg_fare: float | None = Field(description="Average fare")


class HourlyPatternsResponse(BaseModel):
    """Hourly patterns response."""

    date: date = Field(description="Statistics date")
    zone_id: int | None = Field(description="Zone ID (null for all zones)")
    patterns: list[HourlyPattern] = Field(description="Hourly patterns")


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    detail: str | None = Field(default=None, description="Additional details")
