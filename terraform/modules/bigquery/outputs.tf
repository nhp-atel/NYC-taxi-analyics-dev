output "dataset_id" {
  description = "BigQuery dataset ID"
  value       = google_bigquery_dataset.nyc_taxi.dataset_id
}

output "dataset_full_id" {
  description = "BigQuery dataset full ID (project:dataset)"
  value       = "${var.project_id}:${google_bigquery_dataset.nyc_taxi.dataset_id}"
}

output "clean_trips_table_id" {
  description = "Clean trips table ID"
  value       = "${var.project_id}:${google_bigquery_dataset.nyc_taxi.dataset_id}.${google_bigquery_table.clean_trips.table_id}"
}

output "dim_zones_table_id" {
  description = "Zones dimension table ID"
  value       = "${var.project_id}:${google_bigquery_dataset.nyc_taxi.dataset_id}.${google_bigquery_table.dim_zones.table_id}"
}

output "dm_daily_zone_stats_table_id" {
  description = "Daily zone stats mart table ID"
  value       = "${var.project_id}:${google_bigquery_dataset.nyc_taxi.dataset_id}.${google_bigquery_table.dm_daily_zone_stats.table_id}"
}

output "dm_hourly_patterns_table_id" {
  description = "Hourly patterns mart table ID"
  value       = "${var.project_id}:${google_bigquery_dataset.nyc_taxi.dataset_id}.${google_bigquery_table.dm_hourly_patterns.table_id}"
}
