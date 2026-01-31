"""Tests for trip event validators."""

from datetime import datetime

from src.shared.schemas import TripEvent, TripEventRaw
from src.shared.validators import validate_trip_event


def make_event(**kwargs) -> TripEvent:
    """Helper to create a TripEvent with defaults."""
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


class TestValidateTripEvent:
    """Tests for trip event validation."""

    def test_valid_event(self):
        """Valid event should pass validation."""
        event = make_event()
        result = validate_trip_event(event)

        assert result.is_valid
        assert len(result.errors) == 0

    def test_invalid_pickup_location(self):
        """Invalid pickup location should fail validation."""
        event = make_event(PULocationID=999)
        # Need to bypass pydantic validation for this test
        event.pickup_location_id = 999

        result = validate_trip_event(event)

        assert not result.is_valid
        assert any("pickup_location_id" in e for e in result.errors)

    def test_negative_fare(self):
        """Negative fare should fail validation."""
        event = make_event(fare_amount=-10.0)
        result = validate_trip_event(event)

        assert not result.is_valid
        assert any("fare_amount" in e for e in result.errors)

    def test_extreme_fare_warning(self):
        """Very high fare should add warning."""
        event = make_event(fare_amount=2000.0)
        result = validate_trip_event(event)

        assert result.is_valid  # Still valid, just a warning
        assert any("fare_amount" in w for w in result.warnings)

    def test_negative_tip(self):
        """Negative tip should fail validation."""
        event = make_event(tip_amount=-5.0)
        result = validate_trip_event(event)

        assert not result.is_valid
        assert any("tip_amount" in e for e in result.errors)

    def test_negative_distance(self):
        """Negative distance should fail validation."""
        event = make_event(trip_distance=-1.0)
        result = validate_trip_event(event)

        assert not result.is_valid
        assert any("trip_distance" in e for e in result.errors)

    def test_extreme_distance_warning(self):
        """Very long distance should add warning."""
        event = make_event(trip_distance=250.0)
        result = validate_trip_event(event)

        assert result.is_valid
        assert any("trip_distance" in w for w in result.warnings)

    def test_dropoff_before_pickup(self):
        """Dropoff before pickup should fail validation."""
        event = make_event(
            tpep_pickup_datetime=datetime(2024, 1, 15, 10, 30, 0),
            tpep_dropoff_datetime=datetime(2024, 1, 15, 10, 0, 0),
        )
        result = validate_trip_event(event)

        assert not result.is_valid
        assert any("before pickup" in e for e in result.errors)

    def test_very_short_trip_warning(self):
        """Very short trip should add warning."""
        event = make_event(
            tpep_pickup_datetime=datetime(2024, 1, 15, 10, 30, 0),
            tpep_dropoff_datetime=datetime(2024, 1, 15, 10, 30, 10),  # 10 seconds
        )
        result = validate_trip_event(event)

        assert result.is_valid
        assert any("short trip" in w for w in result.warnings)

    def test_zero_passenger_warning(self):
        """Zero passengers should add warning."""
        event = make_event(passenger_count=0.0)
        result = validate_trip_event(event)

        assert result.is_valid
        assert any("passenger_count" in w for w in result.warnings)

    def test_negative_passengers(self):
        """Negative passengers should fail validation."""
        event = make_event(passenger_count=-1.0)
        result = validate_trip_event(event)

        assert not result.is_valid
        assert any("passenger_count" in e for e in result.errors)
