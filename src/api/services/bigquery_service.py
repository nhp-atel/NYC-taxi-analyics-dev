"""BigQuery service for data access."""

from datetime import date
from functools import lru_cache
from typing import Any

from google.cloud import bigquery

from src.api.config import APISettings


class BigQueryService:
    """Service for querying BigQuery."""

    def __init__(self, settings: APISettings):
        """Initialize BigQuery service.

        Args:
            settings: API settings
        """
        self.settings = settings
        self.client = bigquery.Client(project=settings.project_id)
        self.dataset = f"{settings.project_id}.{settings.bq_dataset}"

    def check_connection(self) -> bool:
        """Check if BigQuery connection is working.

        Returns:
            True if connection is successful
        """
        try:
            query = "SELECT 1"
            result = self.client.query(query).result()
            list(result)
            return True
        except Exception:
            return False

    def get_zone_stats(self, zone_id: int, stat_date: date) -> dict[str, Any] | None:
        """Get zone statistics for a specific date.

        Args:
            zone_id: NYC TLC zone ID
            stat_date: Statistics date

        Returns:
            Zone stats dict or None if not found
        """
        query = f"""
            SELECT
                zone_id,
                stat_date,
                trip_count,
                total_passengers,
                total_distance,
                total_fare,
                total_tip,
                total_revenue,
                avg_fare,
                avg_distance,
                avg_tip_pct
            FROM `{self.dataset}.dm_daily_zone_stats`
            WHERE zone_id = @zone_id
              AND stat_date = @stat_date
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("zone_id", "INT64", zone_id),
                bigquery.ScalarQueryParameter("stat_date", "DATE", stat_date.isoformat()),
            ]
        )

        result = self.client.query(query, job_config=job_config).result()
        rows = list(result)

        if not rows:
            return None

        row = rows[0]
        return {
            "zone_id": row.zone_id,
            "date": row.stat_date,
            "trip_count": row.trip_count,
            "total_passengers": row.total_passengers,
            "total_distance": row.total_distance,
            "total_fare": row.total_fare,
            "total_tip": row.total_tip,
            "total_revenue": row.total_revenue,
            "avg_fare": row.avg_fare,
            "avg_distance": row.avg_distance,
            "avg_tip_pct": row.avg_tip_pct,
        }

    def get_daily_stats(self, stat_date: date) -> dict[str, Any] | None:
        """Get daily aggregate statistics.

        Args:
            stat_date: Statistics date

        Returns:
            Daily stats dict or None if not found
        """
        # Get aggregate stats
        agg_query = f"""
            SELECT
                stat_date,
                SUM(trip_count) as total_trips,
                SUM(total_revenue) as total_revenue,
                SUM(total_passengers) as total_passengers,
                AVG(avg_fare) as avg_fare,
                AVG(avg_distance) as avg_distance
            FROM `{self.dataset}.dm_daily_zone_stats`
            WHERE stat_date = @stat_date
            GROUP BY stat_date
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("stat_date", "DATE", stat_date.isoformat()),
            ]
        )

        result = self.client.query(agg_query, job_config=job_config).result()
        rows = list(result)

        if not rows:
            return None

        agg_row = rows[0]

        # Get top zones
        top_query = f"""
            SELECT
                zone_id,
                trip_count,
                total_revenue
            FROM `{self.dataset}.dm_daily_zone_stats`
            WHERE stat_date = @stat_date
            ORDER BY trip_count DESC
            LIMIT 10
        """

        result = self.client.query(top_query, job_config=job_config).result()
        top_zones = [
            {
                "zone_id": row.zone_id,
                "trip_count": row.trip_count,
                "total_revenue": row.total_revenue,
            }
            for row in result
        ]

        return {
            "date": agg_row.stat_date,
            "total_trips": agg_row.total_trips,
            "total_revenue": agg_row.total_revenue,
            "total_passengers": agg_row.total_passengers,
            "avg_fare": agg_row.avg_fare,
            "avg_distance": agg_row.avg_distance,
            "top_zones": top_zones,
        }

    def get_hourly_patterns(
        self,
        stat_date: date,
        zone_id: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get hourly trip patterns.

        Args:
            stat_date: Statistics date
            zone_id: Optional zone ID filter

        Returns:
            List of hourly pattern dicts
        """
        if zone_id:
            query = f"""
                SELECT
                    hour_of_day,
                    SUM(trip_count) as trip_count,
                    AVG(avg_fare) as avg_fare
                FROM `{self.dataset}.dm_hourly_patterns`
                WHERE stat_date = @stat_date
                  AND pickup_location_id = @zone_id
                GROUP BY hour_of_day
                ORDER BY hour_of_day
            """
            params = [
                bigquery.ScalarQueryParameter("stat_date", "DATE", stat_date.isoformat()),
                bigquery.ScalarQueryParameter("zone_id", "INT64", zone_id),
            ]
        else:
            query = f"""
                SELECT
                    hour_of_day,
                    SUM(trip_count) as trip_count,
                    AVG(avg_fare) as avg_fare
                FROM `{self.dataset}.dm_hourly_patterns`
                WHERE stat_date = @stat_date
                GROUP BY hour_of_day
                ORDER BY hour_of_day
            """
            params = [
                bigquery.ScalarQueryParameter("stat_date", "DATE", stat_date.isoformat()),
            ]

        job_config = bigquery.QueryJobConfig(query_parameters=params)
        result = self.client.query(query, job_config=job_config).result()

        return [
            {
                "hour": row.hour_of_day,
                "trip_count": row.trip_count,
                "avg_fare": row.avg_fare,
            }
            for row in result
        ]


@lru_cache
def get_bigquery_service(settings: APISettings) -> BigQueryService:
    """Get cached BigQuery service instance."""
    return BigQueryService(settings)
