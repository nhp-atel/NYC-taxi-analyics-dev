"""Daily mart builder DAG.

Builds curated data marts from clean_trips table.
Runs at 6 AM UTC daily.
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag
from airflow.models import Variable
from airflow.providers.google.cloud.operators.bigquery import (
    BigQueryInsertJobOperator,
)
from airflow.providers.google.cloud.sensors.bigquery import (
    BigQueryTablePartitionExistenceSensor,
)

# Configuration
PROJECT_ID = Variable.get("PROJECT_ID", default_var="nyc-taxi-analytics-dev")
BQ_DATASET = Variable.get("BQ_DATASET", default_var="nyc_taxi")
REGION = Variable.get("REGION", default_var="us-central1")

# SQL templates directory
SQL_DIR = Path(__file__).parent / "sql"


def load_sql(filename: str) -> str:
    """Load SQL from file."""
    return (SQL_DIR / filename).read_text()


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="daily_mart_builder",
    default_args=default_args,
    description="Build daily data marts from clean_trips",
    schedule="0 6 * * *",  # 6 AM UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["nyc-taxi", "mart", "daily"],
)
def daily_mart_builder():
    """Build daily data marts."""

    # Wait for clean_trips partition to exist
    wait_for_partition = BigQueryTablePartitionExistenceSensor(
        task_id="wait_for_clean_trips_partition",
        project_id=PROJECT_ID,
        dataset_id=BQ_DATASET,
        table_id="clean_trips",
        partition_id="{{ ds_nodash }}",
        poke_interval=300,  # 5 minutes
        timeout=3600,  # 1 hour
        mode="poke",
    )

    # Build daily zone stats mart
    build_zone_stats = BigQueryInsertJobOperator(
        task_id="build_daily_zone_stats",
        configuration={
            "query": {
                "query": load_sql("build_zone_stats.sql"),
                "useLegacySql": False,
                "queryParameters": [
                    {
                        "name": "run_date",
                        "parameterType": {"type": "DATE"},
                        "parameterValue": {"value": "{{ ds }}"},
                    }
                ],
            }
        },
        project_id=PROJECT_ID,
        location=REGION,
    )

    # Build hourly patterns mart
    build_hourly_patterns = BigQueryInsertJobOperator(
        task_id="build_hourly_patterns",
        configuration={
            "query": {
                "query": load_sql("build_hourly_patterns.sql"),
                "useLegacySql": False,
                "queryParameters": [
                    {
                        "name": "run_date",
                        "parameterType": {"type": "DATE"},
                        "parameterValue": {"value": "{{ ds }}"},
                    }
                ],
            }
        },
        project_id=PROJECT_ID,
        location=REGION,
    )

    # Task dependencies
    wait_for_partition >> [build_zone_stats, build_hourly_patterns]


# Instantiate the DAG
dag_instance = daily_mart_builder()
