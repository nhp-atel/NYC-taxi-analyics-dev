"""Canonical data schemas for NYC Taxi Analytics."""

from datetime import datetime
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field, computed_field, model_validator


class TripEventRaw(BaseModel):
    """Raw trip event as received from NYC TLC data."""

    VendorID: int | None = None
    tpep_pickup_datetime: datetime | None = None
    tpep_dropoff_datetime: datetime | None = None
    passenger_count: float | None = None
    trip_distance: float | None = None
    RatecodeID: float | None = None
    store_and_fwd_flag: str | None = None
    PULocationID: int | None = None
    DOLocationID: int | None = None
    payment_type: int | None = None
    fare_amount: float | None = None
    extra: float | None = None
    mta_tax: float | None = None
    tip_amount: float | None = None
    tolls_amount: float | None = None
    improvement_surcharge: float | None = None
    total_amount: float | None = None
    congestion_surcharge: float | None = None
    airport_fee: float | None = None

    model_config = {"extra": "ignore"}


class TripEvent(BaseModel):
    """Canonical trip event schema used throughout the pipeline."""

    trip_id: str = Field(..., description="Deterministic SHA256 hash for deduplication")
    vendor_id: int | None = Field(None, ge=1, le=6)
    pickup_datetime: datetime
    dropoff_datetime: datetime | None = None
    pickup_location_id: int = Field(..., ge=1, le=265)
    dropoff_location_id: int | None = Field(None, ge=1, le=265)
    passenger_count: int | None = Field(None, ge=0, le=9)
    trip_distance: float | None = Field(None, ge=0)
    fare_amount: float | None = Field(None)
    tip_amount: float | None = Field(None, ge=0)
    total_amount: float | None = Field(None)
    payment_type: int | None = Field(None, ge=0, le=6)
    ingestion_timestamp: datetime = Field(default_factory=datetime.utcnow)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def pickup_date(self) -> str:
        """Partition key for BigQuery."""
        return self.pickup_datetime.strftime("%Y-%m-%d")

    def to_bq_row(self) -> dict[str, Any]:
        """Convert to BigQuery row format."""
        return {
            "trip_id": self.trip_id,
            "pickup_datetime": self.pickup_datetime.isoformat(),
            "dropoff_datetime": self.dropoff_datetime.isoformat() if self.dropoff_datetime else None,
            "pickup_date": self.pickup_date,
            "pickup_location_id": self.pickup_location_id,
            "dropoff_location_id": self.dropoff_location_id,
            "vendor_id": self.vendor_id,
            "passenger_count": self.passenger_count,
            "trip_distance": self.trip_distance,
            "fare_amount": self.fare_amount,
            "tip_amount": self.tip_amount,
            "total_amount": self.total_amount,
            "payment_type": self.payment_type,
            "ingestion_timestamp": self.ingestion_timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return self.model_dump_json()

    @classmethod
    def from_raw(cls, raw: TripEventRaw) -> "TripEvent":
        """Transform raw TLC data to canonical schema."""
        if raw.tpep_pickup_datetime is None:
            raise ValueError("pickup_datetime is required")
        if raw.PULocationID is None:
            raise ValueError("pickup_location_id is required")

        trip_id = generate_trip_id(
            vendor_id=raw.VendorID,
            pickup_dt=raw.tpep_pickup_datetime,
            dropoff_dt=raw.tpep_dropoff_datetime,
            pu_loc=raw.PULocationID,
            do_loc=raw.DOLocationID,
            fare=raw.fare_amount,
        )

        return cls(
            trip_id=trip_id,
            vendor_id=raw.VendorID,
            pickup_datetime=raw.tpep_pickup_datetime,
            dropoff_datetime=raw.tpep_dropoff_datetime,
            pickup_location_id=raw.PULocationID,
            dropoff_location_id=raw.DOLocationID,
            passenger_count=int(raw.passenger_count) if raw.passenger_count else None,
            trip_distance=raw.trip_distance,
            fare_amount=raw.fare_amount,
            tip_amount=raw.tip_amount,
            total_amount=raw.total_amount,
            payment_type=raw.payment_type,
        )


class ValidationResult(BaseModel):
    """Result of validating a trip event."""

    is_valid: bool = True
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add a validation error."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a validation warning."""
        self.warnings.append(message)


def generate_trip_id(
    vendor_id: int | None,
    pickup_dt: datetime | None,
    dropoff_dt: datetime | None,
    pu_loc: int | None,
    do_loc: int | None,
    fare: float | None,
) -> str:
    """Generate deterministic trip ID from immutable attributes for deduplication."""
    components = [
        str(vendor_id or ""),
        pickup_dt.isoformat() if pickup_dt else "",
        dropoff_dt.isoformat() if dropoff_dt else "",
        str(pu_loc or ""),
        str(do_loc or ""),
        f"{fare:.2f}" if fare is not None else "",
    ]
    hash_input = "|".join(components)
    return sha256(hash_input.encode()).hexdigest()[:32]
