output "producer_service_account_email" {
  description = "Producer service account email"
  value       = google_service_account.producer.email
}

output "dataflow_service_account_email" {
  description = "Dataflow service account email"
  value       = google_service_account.dataflow.email
}

output "api_service_account_email" {
  description = "API service account email"
  value       = google_service_account.api.email
}
