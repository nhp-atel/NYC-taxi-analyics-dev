"""Tests for the FastAPI application."""

import datetime as dt
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.config import APISettings
from src.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    return APISettings(
        project_id="test-project",
        bq_dataset="test_dataset",
        environment="test",
    )


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_check(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_readiness_check_with_mock(self, client):
        """Readiness endpoint should check BigQuery."""
        with patch("src.api.routers.health.BigQueryService") as mock_bq:
            mock_instance = MagicMock()
            mock_instance.check_connection.return_value = True
            mock_bq.return_value = mock_instance

            response = client.get("/health/readiness")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ready"
            assert data["bigquery"] == "connected"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client):
        """Root endpoint should return API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "NYC Taxi Analytics API"
        assert data["version"] == "1.0.0"
        assert "docs" in data
        assert "health" in data


class TestZoneStatsEndpoint:
    """Tests for zone stats endpoint."""

    def test_zone_stats_success(self, client):
        """Should return zone stats for valid request."""
        mock_data = {
            "zone_id": 132,
            "date": dt.date(2024, 1, 15),
            "trip_count": 1234,
            "total_passengers": 2500,
            "total_distance": 5500.0,
            "total_fare": 25000.0,
            "total_tip": 5000.0,
            "total_revenue": 35000.0,
            "avg_fare": 20.26,
            "avg_distance": 4.46,
            "avg_tip_pct": 20.0,
        }

        with patch("src.api.routers.zones.BigQueryService") as mock_bq:
            mock_instance = MagicMock()
            mock_instance.get_zone_stats.return_value = mock_data
            mock_bq.return_value = mock_instance

            response = client.get("/api/v1/zones/132/stats?date=2024-01-15")

            assert response.status_code == 200
            data = response.json()
            assert data["zone_id"] == 132
            assert data["trip_count"] == 1234

    def test_zone_stats_not_found(self, client):
        """Should return 404 for missing data."""
        with patch("src.api.routers.zones.BigQueryService") as mock_bq:
            mock_instance = MagicMock()
            mock_instance.get_zone_stats.return_value = None
            mock_bq.return_value = mock_instance

            response = client.get("/api/v1/zones/132/stats?date=2024-01-15")

            assert response.status_code == 404

    def test_zone_stats_invalid_zone(self, client):
        """Should return 400 for invalid zone ID."""
        response = client.get("/api/v1/zones/999/stats?date=2024-01-15")

        assert response.status_code == 400
        data = response.json()
        assert "Invalid zone_id" in data["detail"]


class TestDailyStatsEndpoint:
    """Tests for daily stats endpoint."""

    def test_daily_stats_success(self, client):
        """Should return daily stats for valid request."""
        mock_data = {
            "date": dt.date(2024, 1, 15),
            "total_trips": 456789,
            "total_revenue": 5000000.0,
            "total_passengers": 800000,
            "avg_fare": 22.5,
            "avg_distance": 4.5,
            "top_zones": [
                {"zone_id": 132, "trip_count": 5000, "total_revenue": 100000.0},
                {"zone_id": 236, "trip_count": 4500, "total_revenue": 90000.0},
            ],
        }

        with patch("src.api.routers.stats.BigQueryService") as mock_bq:
            mock_instance = MagicMock()
            mock_instance.get_daily_stats.return_value = mock_data
            mock_bq.return_value = mock_instance

            response = client.get("/api/v1/stats/daily/2024-01-15")

            assert response.status_code == 200
            data = response.json()
            assert data["total_trips"] == 456789
            assert len(data["top_zones"]) == 2

    def test_daily_stats_not_found(self, client):
        """Should return 404 for missing data."""
        with patch("src.api.routers.stats.BigQueryService") as mock_bq:
            mock_instance = MagicMock()
            mock_instance.get_daily_stats.return_value = None
            mock_bq.return_value = mock_instance

            response = client.get("/api/v1/stats/daily/2024-01-15")

            assert response.status_code == 404


class TestResponseSchemas:
    """Tests for response schemas."""

    def test_zone_stats_response_schema(self):
        """ZoneStatsResponse should have correct fields."""
        from src.api.schemas import ZoneStatsResponse

        data = ZoneStatsResponse(
            zone_id=132,
            date=dt.date(2024, 1, 15),
            trip_count=1234,
            total_passengers=2500,
            total_distance=5500.0,
            total_fare=25000.0,
            total_tip=5000.0,
            total_revenue=35000.0,
            avg_fare=20.26,
            avg_distance=4.46,
            avg_tip_pct=20.0,
        )

        assert data.zone_id == 132
        assert data.trip_count == 1234

    def test_daily_stats_response_schema(self):
        """DailyStatsResponse should have correct fields."""
        from src.api.schemas import DailyStatsResponse, TopZone

        data = DailyStatsResponse(
            date=dt.date(2024, 1, 15),
            total_trips=456789,
            total_revenue=5000000.0,
            total_passengers=800000,
            avg_fare=22.5,
            avg_distance=4.5,
            top_zones=[
                TopZone(zone_id=132, trip_count=5000, total_revenue=100000.0),
            ],
        )

        assert data.total_trips == 456789
        assert len(data.top_zones) == 1
