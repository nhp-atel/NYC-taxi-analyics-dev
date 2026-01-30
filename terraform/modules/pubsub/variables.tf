variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "producer_service_account" {
  description = "Producer service account email"
  type        = string
}

variable "dataflow_service_account" {
  description = "Dataflow service account email"
  type        = string
}
