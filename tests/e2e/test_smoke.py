"""Smoke tests for deployed services.

These tests are run against deployed infrastructure.
"""

import os

import pytest

# Skip all tests if API URL not set
API_URL = os.getenv("API_URL", "http://localhost:8000")


class TestSmokeTests:
    """Smoke tests for deployed services."""

    @pytest.mark.skipif(
        not os.getenv("RUN_SMOKE_TESTS"),
        reason="Smoke tests not enabled",
    )
    def test_api_health(self):
        """API health endpoint should respond."""
        import httpx

        response = httpx.get(f"{API_URL}/health", timeout=10)
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.skipif(
        not os.getenv("RUN_SMOKE_TESTS"),
        reason="Smoke tests not enabled",
    )
    def test_api_readiness(self):
        """API readiness endpoint should respond."""
        import httpx

        response = httpx.get(f"{API_URL}/health/readiness", timeout=10)
        assert response.status_code == 200

    @pytest.mark.skipif(
        not os.getenv("RUN_SMOKE_TESTS"),
        reason="Smoke tests not enabled",
    )
    def test_api_docs(self):
        """API docs should be accessible."""
        import httpx

        response = httpx.get(f"{API_URL}/docs", timeout=10)
        assert response.status_code == 200
