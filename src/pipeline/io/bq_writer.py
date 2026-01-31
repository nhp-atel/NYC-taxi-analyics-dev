"""BigQuery writer for clean trip events."""

import apache_beam as beam
from apache_beam.io.gcp.bigquery import BigQueryDisposition, WriteToBigQuery

from src.pipeline.transforms.validate import ValidatedEvent

# BigQuery schema for clean_trips table
CLEAN_TRIPS_SCHEMA = {
    "fields": [
        {"name": "trip_id", "type": "STRING", "mode": "REQUIRED"},
        {"name": "pickup_datetime", "type": "TIMESTAMP", "mode": "REQUIRED"},
        {"name": "dropoff_datetime", "type": "TIMESTAMP", "mode": "NULLABLE"},
        {"name": "pickup_date", "type": "DATE", "mode": "REQUIRED"},
        {"name": "pickup_location_id", "type": "INT64", "mode": "REQUIRED"},
        {"name": "dropoff_location_id", "type": "INT64", "mode": "NULLABLE"},
        {"name": "vendor_id", "type": "INT64", "mode": "NULLABLE"},
        {"name": "passenger_count", "type": "INT64", "mode": "NULLABLE"},
        {"name": "trip_distance", "type": "FLOAT64", "mode": "NULLABLE"},
        {"name": "fare_amount", "type": "FLOAT64", "mode": "NULLABLE"},
        {"name": "tip_amount", "type": "FLOAT64", "mode": "NULLABLE"},
        {"name": "total_amount", "type": "FLOAT64", "mode": "NULLABLE"},
        {"name": "payment_type", "type": "INT64", "mode": "NULLABLE"},
        {"name": "ingestion_timestamp", "type": "TIMESTAMP", "mode": "REQUIRED"},
    ]
}


class WriteToBigQueryClean(beam.PTransform):
    """Write validated trip events to BigQuery."""

    def __init__(self, table: str):
        """Initialize BigQuery writer.

        Args:
            table: Table reference in format project:dataset.table
        """
        super().__init__()
        self.table = table

    def expand(self, pcoll):
        """Apply the BigQuery write transform."""
        return (
            pcoll
            | "ToBQRow" >> beam.Map(_to_bq_row)
            | "WriteToBQ" >> WriteToBigQuery(
                table=self.table,
                schema=CLEAN_TRIPS_SCHEMA,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_NEVER,
                method="STREAMING_INSERTS",
                insert_retry_strategy="RETRY_ON_TRANSIENT_ERROR",
            )
        )


def _to_bq_row(validated_event: ValidatedEvent) -> dict:
    """Convert ValidatedEvent to BigQuery row.

    Args:
        validated_event: The validated event

    Returns:
        Dict suitable for BigQuery insert
    """
    return validated_event.event.to_bq_row()
