"""Pub/Sub publisher with batching and rate limiting."""

from concurrent import futures
from typing import Callable

from google.cloud import pubsub_v1

from src.producer.rate_limiter import RateLimiter
from src.shared.schemas import TripEvent


class TripEventPublisher:
    """Publisher for trip events to Pub/Sub."""

    def __init__(
        self,
        project_id: str,
        topic_name: str,
        rate_limit: float = 100.0,
        batch_size: int = 100,
    ) -> None:
        """Initialize the publisher.

        Args:
            project_id: GCP project ID
            topic_name: Pub/Sub topic name
            rate_limit: Messages per second
            batch_size: Messages per batch
        """
        self.project_id = project_id
        self.topic_name = topic_name
        self.topic_path = f"projects/{project_id}/topics/{topic_name}"
        self.rate_limiter = RateLimiter(rate=rate_limit, burst=batch_size)
        self.batch_size = batch_size

        # Configure batch settings
        batch_settings = pubsub_v1.types.BatchSettings(
            max_messages=batch_size,
            max_latency=0.1,  # 100ms max latency
        )

        self.publisher = pubsub_v1.PublisherClient(batch_settings=batch_settings)
        self._futures: list[futures.Future] = []
        self._published_count = 0
        self._error_count = 0

    def _get_callback(
        self,
        event: TripEvent,
    ) -> Callable[[futures.Future], None]:
        """Create a callback for publish result.

        Args:
            event: The event being published

        Returns:
            Callback function
        """

        def callback(future: futures.Future) -> None:
            try:
                future.result()
                self._published_count += 1
            except Exception as e:
                self._error_count += 1
                print(f"Error publishing event {event.trip_id}: {e}")

        return callback

    def publish(self, event: TripEvent) -> futures.Future:
        """Publish a single event.

        Args:
            event: Trip event to publish

        Returns:
            Future for the publish operation
        """
        self.rate_limiter.acquire(1)

        data = event.to_json().encode("utf-8")
        future = self.publisher.publish(
            self.topic_path,
            data,
            trip_id=event.trip_id,
            pickup_date=event.pickup_date,
        )
        future.add_done_callback(self._get_callback(event))
        self._futures.append(future)

        return future

    def publish_batch(self, events: list[TripEvent]) -> list[futures.Future]:
        """Publish a batch of events.

        Args:
            events: List of trip events

        Returns:
            List of futures
        """
        return [self.publish(event) for event in events]

    def flush(self) -> None:
        """Wait for all pending publishes to complete."""
        futures.wait(self._futures, return_when=futures.ALL_COMPLETED)
        self._futures.clear()

    def close(self) -> None:
        """Close the publisher."""
        self.flush()
        self.publisher.stop()

    @property
    def stats(self) -> dict:
        """Get publishing statistics."""
        return {
            "published": self._published_count,
            "errors": self._error_count,
            "pending": len(self._futures),
        }


class DryRunPublisher:
    """Mock publisher for testing without Pub/Sub."""

    def __init__(self, verbose: bool = False) -> None:
        """Initialize dry-run publisher.

        Args:
            verbose: Print each event
        """
        self.verbose = verbose
        self._published_count = 0

    def publish(self, event: TripEvent) -> None:
        """Simulate publishing an event.

        Args:
            event: Trip event to publish
        """
        self._published_count += 1
        if self.verbose:
            print(f"[DRY-RUN] Would publish: {event.trip_id}")

    def publish_batch(self, events: list[TripEvent]) -> None:
        """Simulate publishing a batch.

        Args:
            events: List of events
        """
        for event in events:
            self.publish(event)

    def flush(self) -> None:
        """No-op for dry run."""
        pass

    def close(self) -> None:
        """No-op for dry run."""
        pass

    @property
    def stats(self) -> dict:
        """Get publishing statistics."""
        return {
            "published": self._published_count,
            "errors": 0,
            "pending": 0,
        }
