"""Deduplication transform for trip events."""

from typing import Iterable

import apache_beam as beam
from apache_beam import window
from apache_beam.transforms.trigger import AccumulationMode, AfterWatermark, AfterProcessingTime
from apache_beam.utils.timestamp import Duration

from src.pipeline.transforms.validate import ValidatedEvent


class DeduplicateByTripId(beam.PTransform):
    """Deduplicate trip events by trip_id within a window.

    Uses windowing to limit state size while still catching duplicates
    within a reasonable time range.
    """

    def __init__(
        self,
        window_size_seconds: int = 86400,  # 24 hours
        allowed_lateness_seconds: int = 21600,  # 6 hours
    ):
        """Initialize deduplication transform.

        Args:
            window_size_seconds: Size of fixed windows in seconds
            allowed_lateness_seconds: Allowed lateness for late data
        """
        super().__init__()
        self.window_size_seconds = window_size_seconds
        self.allowed_lateness_seconds = allowed_lateness_seconds

    def expand(self, pcoll):
        """Apply the deduplication transform."""
        return (
            pcoll
            # Assign timestamps from pickup_datetime
            | "WithTimestamps" >> beam.Map(
                lambda ve: beam.window.TimestampedValue(
                    ve, ve.event.pickup_datetime.timestamp()
                )
            )
            # Apply fixed windows with late data handling
            | "Window" >> beam.WindowInto(
                window.FixedWindows(self.window_size_seconds),
                allowed_lateness=Duration(seconds=self.allowed_lateness_seconds),
                trigger=AfterWatermark(
                    late=AfterProcessingTime(60)  # Fire every minute for late data
                ),
                accumulation_mode=AccumulationMode.DISCARDING,
            )
            # Key by trip_id
            | "KeyByTripId" >> beam.Map(lambda ve: (ve.event.trip_id, ve))
            # Deduplicate - keep first occurrence
            | "GroupByKey" >> beam.GroupByKey()
            | "TakeFirst" >> beam.FlatMap(_take_first)
        )


def _take_first(kv: tuple[str, Iterable[ValidatedEvent]]) -> Iterable[ValidatedEvent]:
    """Take the first event from a group.

    Args:
        kv: Tuple of (trip_id, iterable of events)

    Yields:
        The first event
    """
    trip_id, events = kv
    first = None
    for event in events:
        if first is None:
            first = event
        break  # Only take the first one
    if first is not None:
        yield first
