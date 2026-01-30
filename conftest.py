"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path

import pytest

# Add src to path for imports
ROOT_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return ROOT_DIR


@pytest.fixture(scope="session")
def src_dir():
    """Return the src directory."""
    return ROOT_DIR / "src"


@pytest.fixture(scope="session")
def data_dir():
    """Return the data directory."""
    return ROOT_DIR / "data"


@pytest.fixture
def sample_parquet(data_dir):
    """Return path to sample parquet file if it exists."""
    path = data_dir / "yellow_tripdata_2024-01.parquet"
    if not path.exists():
        pytest.skip("Sample parquet file not downloaded")
    return path
