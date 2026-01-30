variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "dataflow_service_account" {
  description = "Dataflow service account email"
  type        = string
}

variable "temp_bucket" {
  description = "GCS bucket for temporary files"
  type        = string
}

variable "input_subscription" {
  description = "Pub/Sub subscription ID for input"
  type        = string
}

variable "output_table" {
  description = "BigQuery table ID for output"
  type        = string
}

variable "dlq_topic" {
  description = "Pub/Sub topic ID for dead letter queue"
  type        = string
}
