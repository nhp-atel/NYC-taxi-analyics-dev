"""GCS writer for raw trip events."""


import apache_beam as beam
from apache_beam.io import WriteToText

from src.pipeline.transforms.validate import ValidatedEvent


class WriteToGCSRaw(beam.PTransform):
    """Write raw trip events to GCS for archival."""

    def __init__(self, output_path: str):
        """Initialize GCS writer.

        Args:
            output_path: GCS path prefix (e.g., gs://bucket/raw/trips)
        """
        super().__init__()
        self.output_path = output_path

    def expand(self, pcoll):
        """Apply the GCS write transform."""
        return (
            pcoll
            | "ToJSON" >> beam.Map(_to_json)
            | "WriteToGCS" >> WriteToText(
                file_path_prefix=self.output_path,
                file_name_suffix=".json",
                num_shards=0,  # Auto-determine shards
            )
        )


def _to_json(validated_event: ValidatedEvent) -> str:
    """Convert ValidatedEvent to JSON string.

    Args:
        validated_event: The validated event

    Returns:
        JSON string
    """
    return validated_event.event.to_json()
