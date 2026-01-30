"""Tests for shared schemas."""

from datetime import datetime

import pytest

from src.shared.schemas import (
    TripEvent,
    TripEventRaw,
    generate_trip_id,
)


class TestGenerateTripId:
    """Tests for trip ID generation."""

    def test_deterministic(self):
        """Trip ID should be deterministic for same inputs."""
        dt = datetime(2024, 1, 15, 10, 30, 0)

        id1 = generate_trip_id(
            vendor_id=1,
            pickup_dt=dt,
            dropoff_dt=dt,
            pu_loc=132,
            do_loc=236,
            fare=25.50,
        )
        id2 = generate_trip_id(
            vendor_id=1,
            pickup_dt=dt,
            dropoff_dt=dt,
            pu_loc=132,
            do_loc=236,
            fare=25.50,
        )

        assert id1 == id2

    def test_different_inputs(self):
        """Different inputs should produce different IDs."""
        dt = datetime(2024, 1, 15, 10, 30, 0)

        id1 = generate_trip_id(
            vendor_id=1,
            pickup_dt=dt,
            dropoff_dt=dt,
            pu_loc=132,
            do_loc=236,
            fare=25.50,
        )
        id2 = generate_trip_id(
            vendor_id=2,  # Different vendor
            pickup_dt=dt,
            dropoff_dt=dt,
            pu_loc=132,
            do_loc=236,
            fare=25.50,
        )

        assert id1 != id2

    def test_length(self):
        """Trip ID should be 32 characters."""
        dt = datetime(2024, 1, 15, 10, 30, 0)

        trip_id = generate_trip_id(
            vendor_id=1,
            pickup_dt=dt,
            dropoff_dt=dt,
            pu_loc=132,
            do_loc=236,
            fare=25.50,
        )

        assert len(trip_id) == 32

    def test_handles_none(self):
        """Should handle None values."""
        dt = datetime(2024, 1, 15, 10, 30, 0)

        trip_id = generate_trip_id(
            vendor_id=None,
            pickup_dt=dt,
            dropoff_dt=None,
            pu_loc=132,
            do_loc=None,
            fare=None,
        )

        assert len(trip_id) == 32


class TestTripEventRaw:
    """Tests for TripEventRaw model."""

    def test_parse_valid(self):
        """Should parse valid raw data."""
        data = {
            "VendorID": 1,
            "tpep_pickup_datetime": datetime(2024, 1, 15, 10, 30, 0),
            "tpep_dropoff_datetime": datetime(2024, 1, 15, 10, 45, 0),
            "passenger_count": 2.0,
            "trip_distance": 5.5,
            "PULocationID": 132,
            "DOLocationID": 236,
            "fare_amount": 25.50,
            "tip_amount": 5.0,
            "total_amount": 35.50,
            "payment_type": 1,
        }

        raw = TripEventRaw.model_validate(data)

        assert raw.VendorID == 1
        assert raw.PULocationID == 132
        assert raw.fare_amount == 25.50

    def test_parse_with_nulls(self):
        """Should handle null values."""
        data = {
            "VendorID": 1,
            "tpep_pickup_datetime": datetime(2024, 1, 15, 10, 30, 0),
            "PULocationID": 132,
        }

        raw = TripEventRaw.model_validate(data)

        assert raw.VendorID == 1
        assert raw.passenger_count is None
        assert raw.fare_amount is None

    def test_ignores_extra_fields(self):
        """Should ignore extra fields."""
        data = {
            "VendorID": 1,
            "tpep_pickup_datetime": datetime(2024, 1, 15, 10, 30, 0),
            "PULocationID": 132,
            "extra_field": "ignored",
        }

        raw = TripEventRaw.model_validate(data)

        assert raw.VendorID == 1
        assert not hasattr(raw, "extra_field")


class TestTripEvent:
    """Tests for TripEvent model."""

    def test_from_raw(self):
        """Should transform raw data to TripEvent."""
        raw = TripEventRaw(
            VendorID=1,
            tpep_pickup_datetime=datetime(2024, 1, 15, 10, 30, 0),
            tpep_dropoff_datetime=datetime(2024, 1, 15, 10, 45, 0),
            passenger_count=2.0,
            trip_distance=5.5,
            PULocationID=132,
            DOLocationID=236,
            fare_amount=25.50,
            tip_amount=5.0,
            total_amount=35.50,
            payment_type=1,
        )

        event = TripEvent.from_raw(raw)

        assert event.vendor_id == 1
        assert event.pickup_location_id == 132
        assert event.dropoff_location_id == 236
        assert event.fare_amount == 25.50
        assert event.passenger_count == 2
        assert len(event.trip_id) == 32

    def test_from_raw_missing_required(self):
        """Should raise error for missing required fields."""
        raw = TripEventRaw(
            VendorID=1,
            tpep_pickup_datetime=None,  # Required
            PULocationID=132,
        )

        with pytest.raises(ValueError, match="pickup_datetime is required"):
            TripEvent.from_raw(raw)

    def test_pickup_date(self):
        """Should compute pickup_date correctly."""
        raw = TripEventRaw(
            VendorID=1,
            tpep_pickup_datetime=datetime(2024, 1, 15, 10, 30, 0),
            PULocationID=132,
        )

        event = TripEvent.from_raw(raw)

        assert event.pickup_date == "2024-01-15"

    def test_to_bq_row(self):
        """Should convert to BigQuery row format."""
        raw = TripEventRaw(
            VendorID=1,
            tpep_pickup_datetime=datetime(2024, 1, 15, 10, 30, 0),
            tpep_dropoff_datetime=datetime(2024, 1, 15, 10, 45, 0),
            PULocationID=132,
            DOLocationID=236,
            fare_amount=25.50,
        )

        event = TripEvent.from_raw(raw)
        row = event.to_bq_row()

        assert row["trip_id"] == event.trip_id
        assert row["pickup_date"] == "2024-01-15"
        assert row["pickup_location_id"] == 132
        assert row["fare_amount"] == 25.50
        assert "ingestion_timestamp" in row

    def test_to_json(self):
        """Should serialize to JSON."""
        raw = TripEventRaw(
            VendorID=1,
            tpep_pickup_datetime=datetime(2024, 1, 15, 10, 30, 0),
            PULocationID=132,
        )

        event = TripEvent.from_raw(raw)
        json_str = event.to_json()

        assert event.trip_id in json_str
        assert "pickup_location_id" in json_str
