"""Tests for pipeline transforms."""

import json
from datetime import datetime

import pytest

from src.pipeline.transforms.validate import ValidatedEvent

# Note: These tests use direct function calls rather than TestPipeline
# for simplicity. Integration tests would use the full pipeline.
from src.shared.schemas import TripEvent, TripEventRaw
from src.shared.validators import validate_trip_event


def make_trip_event(**kwargs) -> TripEvent:
    """Helper to create a TripEvent."""
    defaults = {
        "VendorID": 1,
        "tpep_pickup_datetime": datetime(2024, 1, 15, 10, 30, 0),
        "tpep_dropoff_datetime": datetime(2024, 1, 15, 10, 45, 0),
        "PULocationID": 132,
        "DOLocationID": 236,
        "passenger_count": 2.0,
        "trip_distance": 5.5,
        "fare_amount": 25.50,
        "tip_amount": 5.0,
        "total_amount": 35.50,
        "payment_type": 1,
    }
    defaults.update(kwargs)
    raw = TripEventRaw(**defaults)
    return TripEvent.from_raw(raw)


class TestParseTransform:
    """Tests for parsing transform logic."""

    def test_parse_valid_json(self):
        """Should parse valid JSON to TripEvent."""
        event = make_trip_event()
        json_bytes = event.to_json().encode("utf-8")

        # Parse back
        data = json.loads(json_bytes.decode("utf-8"))

        # Handle datetime conversion
        data["pickup_datetime"] = datetime.fromisoformat(
            data["pickup_datetime"].replace("Z", "+00:00")
        )
        if data.get("dropoff_datetime"):
            data["dropoff_datetime"] = datetime.fromisoformat(
                data["dropoff_datetime"].replace("Z", "+00:00")
            )
        data["ingestion_timestamp"] = datetime.fromisoformat(
            data["ingestion_timestamp"].replace("Z", "+00:00")
        )

        parsed = TripEvent.model_validate(data)

        assert parsed.trip_id == event.trip_id
        assert parsed.pickup_location_id == event.pickup_location_id

    def test_parse_invalid_json(self):
        """Should fail on invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            json.loads(b"not valid json")

    def test_parse_missing_fields(self):
        """Should fail on missing required fields."""
        from pydantic import ValidationError

        data = {"vendor_id": 1}  # Missing required fields

        with pytest.raises(ValidationError):
            TripEvent.model_validate(data)


class TestValidateTransform:
    """Tests for validation transform logic."""

    def test_validated_event_valid(self):
        """Valid event should have is_valid=True."""
        event = make_trip_event()
        result = validate_trip_event(event)
        validated = ValidatedEvent(event=event, validation=result)

        assert validated.is_valid
        assert len(validated.validation.errors) == 0

    def test_validated_event_invalid(self):
        """Invalid event should have is_valid=False."""
        event = make_trip_event(fare_amount=-10.0)
        result = validate_trip_event(event)
        validated = ValidatedEvent(event=event, validation=result)

        assert not validated.is_valid
        assert len(validated.validation.errors) > 0

    def test_validated_event_to_dict(self):
        """Should convert to dict with validation info."""
        event = make_trip_event()
        result = validate_trip_event(event)
        validated = ValidatedEvent(event=event, validation=result)

        data = validated.to_dict()

        assert "trip_id" in data
        assert "validation_errors" in data
        assert "validation_warnings" in data


class TestDeduplicationLogic:
    """Tests for deduplication logic."""

    def test_same_trip_id(self):
        """Events with same trip_id should be deduplicated."""
        event1 = make_trip_event()
        event2 = make_trip_event()  # Same inputs = same trip_id

        assert event1.trip_id == event2.trip_id

    def test_different_trip_id(self):
        """Events with different inputs should have different trip_ids."""
        event1 = make_trip_event(PULocationID=132)
        event2 = make_trip_event(PULocationID=133)

        assert event1.trip_id != event2.trip_id

    def test_dedup_keeps_first(self):
        """Deduplication should keep first occurrence."""
        events = [
            make_trip_event(),
            make_trip_event(),  # Duplicate
            make_trip_event(PULocationID=100),  # Different
        ]

        # Group by trip_id
        by_id = {}
        for event in events:
            if event.trip_id not in by_id:
                by_id[event.trip_id] = event

        # Should have 2 unique trips
        assert len(by_id) == 2
