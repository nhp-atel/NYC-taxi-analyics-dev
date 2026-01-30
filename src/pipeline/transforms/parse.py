"""Parse transform for trip events."""

import json
from datetime import datetime
from typing import Any

import apache_beam as beam
from apache_beam import pvalue

from src.shared.schemas import TripEvent


class ParseTripEvent(beam.PTransform):
    """Parse JSON messages into TripEvent objects.

    Outputs:
        - valid: Successfully parsed TripEvent objects
        - dlq: Failed messages for dead letter queue
    """

    VALID_TAG = "valid"
    DLQ_TAG = "dlq"

    def expand(self, pcoll):
        """Apply the parse transform."""
        return pcoll | "ParseJSON" >> beam.ParDo(
            _ParseTripEventFn()
        ).with_outputs(self.DLQ_TAG, main=self.VALID_TAG)


class _ParseTripEventFn(beam.DoFn):
    """DoFn to parse JSON into TripEvent."""

    def process(self, element: bytes):
        """Parse a single message.

        Args:
            element: Raw message bytes

        Yields:
            TripEvent for valid messages, or error dict for DLQ
        """
        try:
            # Decode and parse JSON
            data = json.loads(element.decode("utf-8"))

            # Handle datetime fields
            if isinstance(data.get("pickup_datetime"), str):
                data["pickup_datetime"] = datetime.fromisoformat(
                    data["pickup_datetime"].replace("Z", "+00:00")
                )
            if isinstance(data.get("dropoff_datetime"), str):
                data["dropoff_datetime"] = datetime.fromisoformat(
                    data["dropoff_datetime"].replace("Z", "+00:00")
                )
            if isinstance(data.get("ingestion_timestamp"), str):
                data["ingestion_timestamp"] = datetime.fromisoformat(
                    data["ingestion_timestamp"].replace("Z", "+00:00")
                )

            # Parse into TripEvent
            event = TripEvent.model_validate(data)
            yield event

        except json.JSONDecodeError as e:
            yield pvalue.TaggedOutput(
                ParseTripEvent.DLQ_TAG,
                {
                    "error": "json_decode_error",
                    "message": str(e),
                    "raw": element.decode("utf-8", errors="replace")[:1000],
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
        except Exception as e:
            yield pvalue.TaggedOutput(
                ParseTripEvent.DLQ_TAG,
                {
                    "error": "parse_error",
                    "message": str(e),
                    "raw": element.decode("utf-8", errors="replace")[:1000],
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
