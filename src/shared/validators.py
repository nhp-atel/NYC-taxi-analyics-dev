"""Business rule validators for trip events."""

from datetime import datetime, timedelta

from src.shared.schemas import TripEvent, ValidationResult

# Valid NYC taxi zone IDs (1-263 are valid, 264-265 are special)
MIN_ZONE_ID = 1
MAX_ZONE_ID = 265

# Reasonable trip constraints
MAX_TRIP_DISTANCE_MILES = 200
MAX_FARE_AMOUNT = 1000
MAX_TRIP_DURATION_HOURS = 24
MIN_TRIP_DURATION_SECONDS = 30


def validate_trip_event(event: TripEvent) -> ValidationResult:
    """Validate a trip event against business rules.

    Args:
        event: The trip event to validate

    Returns:
        ValidationResult with any errors or warnings
    """
    result = ValidationResult()

    # Validate pickup location
    if not (MIN_ZONE_ID <= event.pickup_location_id <= MAX_ZONE_ID):
        result.add_error(f"Invalid pickup_location_id: {event.pickup_location_id}")

    # Validate dropoff location if present
    if event.dropoff_location_id is not None:
        if not (MIN_ZONE_ID <= event.dropoff_location_id <= MAX_ZONE_ID):
            result.add_error(f"Invalid dropoff_location_id: {event.dropoff_location_id}")

    # Validate fare amount
    if event.fare_amount is not None:
        if event.fare_amount < 0:
            result.add_error(f"Negative fare_amount: {event.fare_amount}")
        elif event.fare_amount > MAX_FARE_AMOUNT:
            result.add_warning(f"Unusually high fare_amount: {event.fare_amount}")

    # Validate tip amount
    if event.tip_amount is not None and event.tip_amount < 0:
        result.add_error(f"Negative tip_amount: {event.tip_amount}")

    # Validate total amount
    if event.total_amount is not None and event.total_amount < 0:
        result.add_error(f"Negative total_amount: {event.total_amount}")

    # Validate trip distance
    if event.trip_distance is not None:
        if event.trip_distance < 0:
            result.add_error(f"Negative trip_distance: {event.trip_distance}")
        elif event.trip_distance > MAX_TRIP_DISTANCE_MILES:
            result.add_warning(f"Unusually long trip_distance: {event.trip_distance}")

    # Validate trip duration
    if event.dropoff_datetime is not None:
        duration = event.dropoff_datetime - event.pickup_datetime
        duration_seconds = duration.total_seconds()

        if duration_seconds < 0:
            result.add_error("dropoff_datetime before pickup_datetime")
        elif duration_seconds < MIN_TRIP_DURATION_SECONDS:
            result.add_warning(f"Very short trip duration: {duration_seconds:.0f} seconds")
        elif duration_seconds > MAX_TRIP_DURATION_HOURS * 3600:
            result.add_warning(f"Very long trip duration: {duration_seconds / 3600:.1f} hours")

    # Validate pickup datetime is not in the future
    now = datetime.utcnow()
    if event.pickup_datetime > now + timedelta(hours=1):
        result.add_error(f"pickup_datetime in future: {event.pickup_datetime}")

    # Validate passenger count
    if event.passenger_count is not None:
        if event.passenger_count < 0:
            result.add_error(f"Negative passenger_count: {event.passenger_count}")
        elif event.passenger_count == 0:
            result.add_warning("Zero passenger_count")

    return result
