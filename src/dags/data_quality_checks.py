"""Data quality checks DAG.

Runs daily to validate data quality in BigQuery tables.
"""

from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.models import Variable
from airflow.operators.python import get_current_context

# Configuration
PROJECT_ID = Variable.get("PROJECT_ID", default_var="nyc-taxi-analytics-dev")
BQ_DATASET = Variable.get("BQ_DATASET", default_var="nyc_taxi")

default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


@dag(
    dag_id="data_quality_checks",
    default_args=default_args,
    description="Run data quality checks on BigQuery tables",
    schedule="0 8 * * *",  # 8 AM UTC (after mart builder)
    start_date=datetime(2024, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["nyc-taxi", "quality", "daily"],
)
def data_quality_checks():
    """Run data quality checks."""

    @task
    def check_row_counts() -> dict:
        """Check row counts for yesterday's partition."""
        from google.cloud import bigquery

        context = get_current_context()
        ds = context["ds"]

        client = bigquery.Client(project=PROJECT_ID)

        checks = {}

        # Check clean_trips
        query = f"""
            SELECT COUNT(*) as count
            FROM `{PROJECT_ID}.{BQ_DATASET}.clean_trips`
            WHERE pickup_date = '{ds}'
        """
        result = client.query(query).result()
        row = list(result)[0]
        checks["clean_trips_count"] = row.count

        # Check zone stats
        query = f"""
            SELECT COUNT(*) as count
            FROM `{PROJECT_ID}.{BQ_DATASET}.dm_daily_zone_stats`
            WHERE stat_date = '{ds}'
        """
        result = client.query(query).result()
        row = list(result)[0]
        checks["zone_stats_count"] = row.count

        # Check hourly patterns
        query = f"""
            SELECT COUNT(*) as count
            FROM `{PROJECT_ID}.{BQ_DATASET}.dm_hourly_patterns`
            WHERE stat_date = '{ds}'
        """
        result = client.query(query).result()
        row = list(result)[0]
        checks["hourly_patterns_count"] = row.count

        print(f"Row counts for {ds}: {checks}")

        # Alert if any table is empty
        if checks["clean_trips_count"] == 0:
            raise ValueError(f"No clean_trips data for {ds}")

        return checks

    @task
    def check_null_rates() -> dict:
        """Check null rates for critical columns."""
        from google.cloud import bigquery

        context = get_current_context()
        ds = context["ds"]

        client = bigquery.Client(project=PROJECT_ID)

        query = f"""
            SELECT
                COUNT(*) as total,
                COUNTIF(pickup_location_id IS NULL) / COUNT(*) * 100 as pickup_null_pct,
                COUNTIF(fare_amount IS NULL) / COUNT(*) * 100 as fare_null_pct,
                COUNTIF(total_amount IS NULL) / COUNT(*) * 100 as total_null_pct,
                COUNTIF(trip_distance IS NULL) / COUNT(*) * 100 as distance_null_pct
            FROM `{PROJECT_ID}.{BQ_DATASET}.clean_trips`
            WHERE pickup_date = '{ds}'
        """

        result = client.query(query).result()
        row = list(result)[0]

        checks = {
            "total_rows": row.total,
            "pickup_null_pct": row.pickup_null_pct,
            "fare_null_pct": row.fare_null_pct,
            "total_null_pct": row.total_null_pct,
            "distance_null_pct": row.distance_null_pct,
        }

        print(f"Null rates for {ds}: {checks}")

        # Alert if null rates exceed thresholds
        if checks["pickup_null_pct"] > 0:
            raise ValueError(f"pickup_location_id has nulls: {checks['pickup_null_pct']:.2f}%")

        if checks["fare_null_pct"] > 10:
            print(f"Warning: High null rate for fare_amount: {checks['fare_null_pct']:.2f}%")

        return checks

    @task
    def check_anomalies() -> dict:
        """Check for data anomalies."""
        from google.cloud import bigquery

        context = get_current_context()
        ds = context["ds"]

        client = bigquery.Client(project=PROJECT_ID)

        query = f"""
            SELECT
                COUNT(*) as total,
                COUNTIF(fare_amount < 0) as negative_fares,
                COUNTIF(trip_distance < 0) as negative_distances,
                COUNTIF(trip_distance > 200) as extreme_distances,
                COUNTIF(fare_amount > 1000) as extreme_fares,
                AVG(fare_amount) as avg_fare,
                AVG(trip_distance) as avg_distance
            FROM `{PROJECT_ID}.{BQ_DATASET}.clean_trips`
            WHERE pickup_date = '{ds}'
        """

        result = client.query(query).result()
        row = list(result)[0]

        checks = {
            "total_rows": row.total,
            "negative_fares": row.negative_fares,
            "negative_distances": row.negative_distances,
            "extreme_distances": row.extreme_distances,
            "extreme_fares": row.extreme_fares,
            "avg_fare": float(row.avg_fare) if row.avg_fare else 0,
            "avg_distance": float(row.avg_distance) if row.avg_distance else 0,
        }

        print(f"Anomaly checks for {ds}: {checks}")

        # Alert on critical anomalies
        if checks["negative_fares"] > 0:
            raise ValueError(f"Found {checks['negative_fares']} negative fares")

        if checks["negative_distances"] > 0:
            raise ValueError(f"Found {checks['negative_distances']} negative distances")

        return checks

    @task
    def generate_report(
        row_counts: dict,
        null_rates: dict,
        anomalies: dict,
    ) -> str:
        """Generate quality report."""
        context = get_current_context()
        ds = context["ds"]

        report = f"""
Data Quality Report for {ds}
============================

Row Counts:
- clean_trips: {row_counts['clean_trips_count']:,}
- zone_stats: {row_counts['zone_stats_count']:,}
- hourly_patterns: {row_counts['hourly_patterns_count']:,}

Null Rates:
- pickup_location_id: {null_rates['pickup_null_pct']:.2f}%
- fare_amount: {null_rates['fare_null_pct']:.2f}%
- total_amount: {null_rates['total_null_pct']:.2f}%
- trip_distance: {null_rates['distance_null_pct']:.2f}%

Anomalies:
- Negative fares: {anomalies['negative_fares']}
- Negative distances: {anomalies['negative_distances']}
- Extreme distances (>200mi): {anomalies['extreme_distances']}
- Extreme fares (>$1000): {anomalies['extreme_fares']}

Averages:
- Average fare: ${anomalies['avg_fare']:.2f}
- Average distance: {anomalies['avg_distance']:.2f} miles

Status: PASSED
"""
        print(report)
        return report

    # Task dependencies
    row_counts = check_row_counts()
    null_rates = check_null_rates()
    anomalies = check_anomalies()

    generate_report(row_counts, null_rates, anomalies)


# Instantiate the DAG
dag_instance = data_quality_checks()
