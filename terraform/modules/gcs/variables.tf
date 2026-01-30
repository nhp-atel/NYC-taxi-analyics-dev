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
