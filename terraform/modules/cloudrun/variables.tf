variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "api_service_account" {
  description = "API service account email"
  type        = string
}

variable "bq_dataset" {
  description = "BigQuery dataset ID"
  type        = string
}

variable "api_image" {
  description = "Docker image for the API (leave empty for placeholder)"
  type        = string
  default     = ""
}
