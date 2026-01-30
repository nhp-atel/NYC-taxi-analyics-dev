"""Validation transform for trip events."""

from dataclasses import dataclass
from typing import Any

import apache_beam as beam

from src.shared.schemas import TripEvent, ValidationResult
from src.shared.validators import validate_trip_event


@dataclass
class ValidatedEvent:
    """Trip event with validation results."""

    event: TripEvent
    validation: ValidationResult

    @property
    def is_valid(self) -> bool:
        """Check if event passed validation."""
        return self.validation.is_valid

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            **self.event.model_dump(),
            "validation_errors": self.validation.errors,
            "validation_warnings": self.validation.warnings,
        }


class ValidateTripEvent(beam.PTransform):
    """Validate trip events against business rules."""

    def expand(self, pcoll):
        """Apply the validation transform."""
        return pcoll | "Validate" >> beam.ParDo(_ValidateTripEventFn())


class _ValidateTripEventFn(beam.DoFn):
    """DoFn to validate trip events."""

    def process(self, event: TripEvent):
        """Validate a single event.

        Args:
            event: TripEvent to validate

        Yields:
            ValidatedEvent with validation results
        """
        validation = validate_trip_event(event)
        yield ValidatedEvent(event=event, validation=validation)


class FilterValid(beam.PTransform):
    """Filter to only valid events."""

    def expand(self, pcoll):
        """Apply the filter."""
        return pcoll | "FilterValid" >> beam.Filter(lambda ve: ve.is_valid)


class FilterInvalid(beam.PTransform):
    """Filter to only invalid events."""

    def expand(self, pcoll):
        """Apply the filter."""
        return pcoll | "FilterInvalid" >> beam.Filter(lambda ve: not ve.is_valid)
