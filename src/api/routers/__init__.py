"""API routers."""

from src.api.routers.health import router as health_router
from src.api.routers.zones import router as zones_router
from src.api.routers.stats import router as stats_router

__all__ = ["health_router", "zones_router", "stats_router"]
