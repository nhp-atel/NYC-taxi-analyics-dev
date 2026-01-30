-- Build hourly trip patterns mart
-- Uses MERGE for idempotent updates (safe for re-runs and backfills)

MERGE `nyc-taxi-analytics-dev.nyc_taxi.dm_hourly_patterns` AS T
USING (
    SELECT
        pickup_date AS stat_date,
        EXTRACT(HOUR FROM pickup_datetime) AS hour_of_day,
        EXTRACT(DAYOFWEEK FROM pickup_datetime) AS day_of_week,
        pickup_location_id,
        COUNT(*) AS trip_count,
        AVG(fare_amount) AS avg_fare,
        AVG(
            TIMESTAMP_DIFF(dropoff_datetime, pickup_datetime, MINUTE)
        ) AS avg_trip_duration_minutes,
        CURRENT_TIMESTAMP() AS updated_at
    FROM `nyc-taxi-analytics-dev.nyc_taxi.clean_trips`
    WHERE pickup_date = @run_date
        AND dropoff_datetime IS NOT NULL
    GROUP BY
        pickup_date,
        EXTRACT(HOUR FROM pickup_datetime),
        EXTRACT(DAYOFWEEK FROM pickup_datetime),
        pickup_location_id
) AS S
ON T.stat_date = S.stat_date
    AND T.hour_of_day = S.hour_of_day
    AND T.day_of_week = S.day_of_week
    AND T.pickup_location_id = S.pickup_location_id
WHEN MATCHED THEN UPDATE SET
    trip_count = S.trip_count,
    avg_fare = S.avg_fare,
    avg_trip_duration_minutes = S.avg_trip_duration_minutes,
    updated_at = S.updated_at
WHEN NOT MATCHED THEN INSERT ROW
