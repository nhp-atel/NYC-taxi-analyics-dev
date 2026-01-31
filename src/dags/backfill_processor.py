"""Backfill processor DAG.

Manually triggered DAG to backfill data marts for a date range.
"""

from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task
from airflow.models import Variable

# Configuration
PROJECT_ID = Variable.get("PROJECT_ID", default_var="nyc-taxi-analytics-dev")
BQ_DATASET = Variable.get("BQ_DATASET", default_var="nyc_taxi")
REGION = Variable.get("REGION", default_var="us-central1")

SQL_DIR = Path(__file__).parent / "sql"


def load_sql(filename: str) -> str:
    """Load SQL from file."""
    return (SQL_DIR / filename).read_text()


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}


@dag(
    dag_id="backfill_processor",
    default_args=default_args,
    description="Backfill data marts for a date range",
    schedule=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["nyc-taxi", "mart", "backfill"],
    params={
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
    },
)
def backfill_processor():
    """Process backfill for a date range."""

    @task
    def generate_dates(start_date: str, end_date: str) -> list[str]:
        """Generate list of dates to process."""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")

        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)

        return dates

    @task
    def process_zone_stats(date: str) -> str:
        """Process zone stats for a single date."""
        from google.cloud import bigquery

        client = bigquery.Client(project=PROJECT_ID)
        sql = load_sql("build_zone_stats.sql")

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("run_date", "DATE", date)
            ]
        )

        query_job = client.query(sql, job_config=job_config)
        query_job.result()

        return f"Zone stats processed for {date}"

    @task
    def process_hourly_patterns(date: str) -> str:
        """Process hourly patterns for a single date."""
        from google.cloud import bigquery

        client = bigquery.Client(project=PROJECT_ID)
        sql = load_sql("build_hourly_patterns.sql")

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("run_date", "DATE", date)
            ]
        )

        query_job = client.query(sql, job_config=job_config)
        query_job.result()

        return f"Hourly patterns processed for {date}"

    # Get date range from params
    dates = generate_dates(
        start_date="{{ params.start_date }}",
        end_date="{{ params.end_date }}",
    )

    # Process each date (using dynamic task mapping)
    process_zone_stats.expand(date=dates)
    process_hourly_patterns.expand(date=dates)


# Instantiate the DAG
dag_instance = backfill_processor()
