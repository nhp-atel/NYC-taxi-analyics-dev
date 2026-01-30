output "pubsub_topic_id" {
  description = "Pub/Sub topic ID for trip events"
  value       = module.pubsub.topic_id
}

output "pubsub_subscription_id" {
  description = "Pub/Sub subscription ID for Dataflow"
  value       = module.pubsub.dataflow_subscription_id
}

output "raw_bucket_name" {
  description = "GCS bucket for raw data"
  value       = module.gcs.raw_bucket_name
}

output "temp_bucket_name" {
  description = "GCS bucket for temporary data"
  value       = module.gcs.temp_bucket_name
}

output "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  value       = module.bigquery.dataset_id
}

output "clean_trips_table_id" {
  description = "BigQuery clean trips table ID"
  value       = module.bigquery.clean_trips_table_id
}

output "producer_service_account" {
  description = "Producer service account email"
  value       = module.iam.producer_service_account_email
}

output "dataflow_service_account" {
  description = "Dataflow service account email"
  value       = module.iam.dataflow_service_account_email
}

output "api_service_account" {
  description = "API service account email"
  value       = module.iam.api_service_account_email
}

output "api_url" {
  description = "Cloud Run API URL"
  value       = module.cloudrun.service_url
}
