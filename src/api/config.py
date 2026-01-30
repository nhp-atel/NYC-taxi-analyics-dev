"""API configuration settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """API configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="API_",
        env_file=".env",
        extra="ignore",
    )

    # GCP settings
    project_id: str = Field(
        default="nyc-taxi-analytics-dev",
        description="GCP project ID",
    )
    bq_dataset: str = Field(
        default="nyc_taxi",
        description="BigQuery dataset",
    )

    # API settings
    environment: str = Field(
        default="dev",
        description="Environment (dev, staging, prod)",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )

    # Cache settings
    cache_ttl_seconds: int = Field(
        default=300,
        description="Cache TTL in seconds",
    )

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "prod"


def get_settings() -> APISettings:
    """Get API settings from environment."""
    return APISettings()
