-- Build daily zone statistics mart
-- Uses MERGE for idempotent updates (safe for re-runs and backfills)

MERGE `nyc-taxi-analytics-dev.nyc_taxi.dm_daily_zone_stats` AS T
USING (
    SELECT
        pickup_date AS stat_date,
        pickup_location_id AS zone_id,
        COUNT(*) AS trip_count,
        SUM(passenger_count) AS total_passengers,
        SUM(trip_distance) AS total_distance,
        SUM(fare_amount) AS total_fare,
        SUM(tip_amount) AS total_tip,
        SUM(total_amount) AS total_revenue,
        AVG(fare_amount) AS avg_fare,
        AVG(trip_distance) AS avg_distance,
        SAFE_DIVIDE(SUM(tip_amount), NULLIF(SUM(fare_amount), 0)) * 100 AS avg_tip_pct,
        CURRENT_TIMESTAMP() AS updated_at
    FROM `nyc-taxi-analytics-dev.nyc_taxi.clean_trips`
    WHERE pickup_date = @run_date
    GROUP BY pickup_date, pickup_location_id
) AS S
ON T.stat_date = S.stat_date AND T.zone_id = S.zone_id
WHEN MATCHED THEN UPDATE SET
    trip_count = S.trip_count,
    total_passengers = S.total_passengers,
    total_distance = S.total_distance,
    total_fare = S.total_fare,
    total_tip = S.total_tip,
    total_revenue = S.total_revenue,
    avg_fare = S.avg_fare,
    avg_distance = S.avg_distance,
    avg_tip_pct = S.avg_tip_pct,
    updated_at = S.updated_at
WHEN NOT MATCHED THEN INSERT ROW
