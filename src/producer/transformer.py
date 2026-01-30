"""Transform raw TLC data to canonical schema."""

from src.shared.schemas import TripEvent, TripEventRaw


def transform_event(raw: TripEventRaw) -> TripEvent | None:
    """Transform a raw TLC event to canonical schema.

    Args:
        raw: Raw event from TLC data

    Returns:
        Transformed TripEvent or None if transformation fails
    """
    try:
        return TripEvent.from_raw(raw)
    except ValueError:
        # Missing required fields
        return None
    except Exception:
        # Unexpected transformation error
        return None


def transform_batch(raw_events: list[TripEventRaw]) -> list[TripEvent]:
    """Transform a batch of raw events.

    Args:
        raw_events: List of raw events

    Returns:
        List of successfully transformed events
    """
    events = []
    for raw in raw_events:
        event = transform_event(raw)
        if event is not None:
            events.append(event)
    return events
