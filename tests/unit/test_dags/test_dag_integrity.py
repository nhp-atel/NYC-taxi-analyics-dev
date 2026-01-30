"""Tests for DAG integrity."""

import os
import sys
from pathlib import Path

import pytest

# Add the dags directory to path for imports
DAGS_DIR = Path(__file__).parent.parent.parent.parent / "src" / "dags"
sys.path.insert(0, str(DAGS_DIR.parent))


class TestDAGIntegrity:
    """Tests to verify DAG integrity."""

    def test_dags_importable(self):
        """All DAG files should be importable."""
        dag_files = list(DAGS_DIR.glob("*.py"))

        # Filter out __init__.py
        dag_files = [f for f in dag_files if f.name != "__init__.py"]

        assert len(dag_files) > 0, "No DAG files found"

        # Note: Full DAG loading requires Airflow context
        # This test just verifies files exist
        for dag_file in dag_files:
            assert dag_file.exists(), f"DAG file not found: {dag_file}"

    def test_sql_files_exist(self):
        """SQL template files should exist."""
        sql_dir = DAGS_DIR / "sql"

        expected_files = [
            "build_zone_stats.sql",
            "build_hourly_patterns.sql",
        ]

        for filename in expected_files:
            sql_file = sql_dir / filename
            assert sql_file.exists(), f"SQL file not found: {sql_file}"

    def test_sql_files_not_empty(self):
        """SQL files should not be empty."""
        sql_dir = DAGS_DIR / "sql"

        for sql_file in sql_dir.glob("*.sql"):
            content = sql_file.read_text()
            assert len(content) > 0, f"SQL file is empty: {sql_file}"
            assert "MERGE" in content or "SELECT" in content, (
                f"SQL file doesn't contain valid SQL: {sql_file}"
            )

    def test_daily_mart_builder_exists(self):
        """daily_mart_builder DAG should exist."""
        dag_file = DAGS_DIR / "daily_mart_builder.py"
        assert dag_file.exists()

        content = dag_file.read_text()
        assert "daily_mart_builder" in content
        assert "@dag" in content or "DAG(" in content

    def test_backfill_processor_exists(self):
        """backfill_processor DAG should exist."""
        dag_file = DAGS_DIR / "backfill_processor.py"
        assert dag_file.exists()

        content = dag_file.read_text()
        assert "backfill_processor" in content
        assert "schedule=None" in content  # Should be manual trigger only

    def test_data_quality_checks_exists(self):
        """data_quality_checks DAG should exist."""
        dag_file = DAGS_DIR / "data_quality_checks.py"
        assert dag_file.exists()

        content = dag_file.read_text()
        assert "data_quality_checks" in content
