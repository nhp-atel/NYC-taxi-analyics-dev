"""Load trip data from parquet files."""

from pathlib import Path
from typing import Iterator

import pandas as pd
import pyarrow.parquet as pq

from src.shared.schemas import TripEventRaw


def load_parquet_file(path: str) -> pd.DataFrame:
    """Load parquet file from local path or GCS.

    Args:
        path: Local file path or gs:// URI

    Returns:
        DataFrame with trip data
    """
    if path.startswith("gs://"):
        # PyArrow handles GCS URIs natively
        table = pq.read_table(path)
        return table.to_pandas()
    else:
        local_path = Path(path)
        if not local_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return pd.read_parquet(local_path)


def iter_trip_events(
    df: pd.DataFrame,
    limit: int | None = None,
) -> Iterator[TripEventRaw]:
    """Iterate over DataFrame rows as TripEventRaw objects.

    Args:
        df: DataFrame with trip data
        limit: Maximum number of events to yield

    Yields:
        TripEventRaw objects
    """
    count = 0
    for _, row in df.iterrows():
        if limit is not None and count >= limit:
            break

        try:
            # Convert row to dict, handling NaN values
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
            event = TripEventRaw.model_validate(row_dict)
            yield event
            count += 1
        except Exception as e:
            # Log and skip invalid rows
            print(f"Warning: Skipping invalid row: {e}")
            continue


def load_and_iter_events(
    path: str,
    limit: int | None = None,
) -> Iterator[TripEventRaw]:
    """Load parquet file and iterate over events.

    Args:
        path: Path to parquet file
        limit: Maximum number of events

    Yields:
        TripEventRaw objects
    """
    df = load_parquet_file(path)
    yield from iter_trip_events(df, limit=limit)
