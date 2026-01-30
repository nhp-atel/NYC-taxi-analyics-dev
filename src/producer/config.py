"""Configuration for the event producer."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProducerSettings(BaseSettings):
    """Producer configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="PRODUCER_",
        env_file=".env",
        extra="ignore",
    )

    # GCP settings
    project_id: str = Field(default="nyc-taxi-analytics-dev", description="GCP project ID")
    topic_name: str = Field(default="trip-events", description="Pub/Sub topic name")

    # Data source
    source_path: str = Field(
        default="data/yellow_tripdata_2024-01.parquet",
        description="Path to source parquet file (local or gs://)",
    )

    # Publishing settings
    batch_size: int = Field(default=100, ge=1, le=1000, description="Messages per batch")
    rate_limit: float = Field(default=100.0, ge=0.1, description="Messages per second")
    max_messages: int | None = Field(default=None, description="Max messages to publish (None=all)")

    # Behavior
    dry_run: bool = Field(default=False, description="Print messages instead of publishing")
    verbose: bool = Field(default=False, description="Enable verbose logging")

    @property
    def topic_path(self) -> str:
        """Full Pub/Sub topic path."""
        return f"projects/{self.project_id}/topics/{self.topic_name}"


def get_settings() -> ProducerSettings:
    """Get producer settings from environment."""
    return ProducerSettings()
