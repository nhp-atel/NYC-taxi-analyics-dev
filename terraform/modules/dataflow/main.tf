# Note: Dataflow jobs are typically deployed via gcloud/SDK rather than Terraform
# This module sets up the Flex Template and job configuration

# Flex template container image location
locals {
  template_image = "gcr.io/${var.project_id}/taxi-pipeline:latest"
  template_path  = "gs://${var.temp_bucket}/templates/taxi-pipeline.json"
}

# Dataflow Flex Template metadata
resource "google_storage_bucket_object" "flex_template" {
  name   = "templates/taxi-pipeline.json"
  bucket = var.temp_bucket
  content = jsonencode({
    image = local.template_image
    sdkInfo = {
      language = "PYTHON"
    }
    metadata = {
      name        = "NYC Taxi Trip Pipeline"
      description = "Streaming pipeline for NYC taxi trip data"
      parameters = [
        {
          name       = "input_subscription"
          label      = "Pub/Sub subscription"
          helpText   = "Pub/Sub subscription to read trip events from"
          regexes    = ["projects/[^/]+/subscriptions/[a-zA-Z0-9-]+"]
          isOptional = false
        },
        {
          name       = "output_table"
          label      = "BigQuery output table"
          helpText   = "BigQuery table to write clean trips (project:dataset.table)"
          regexes    = ["[^:]+:[^.]+\\.[a-zA-Z0-9_]+"]
          isOptional = false
        },
        {
          name       = "dlq_topic"
          label      = "Dead letter queue topic"
          helpText   = "Pub/Sub topic for failed messages"
          regexes    = ["projects/[^/]+/topics/[a-zA-Z0-9-]+"]
          isOptional = false
        },
        {
          name       = "raw_output_path"
          label      = "Raw output GCS path"
          helpText   = "GCS path for raw event archives"
          regexes    = ["gs://[^/]+/.+"]
          isOptional = true
        }
      ]
    }
  })
}

# Store job configuration for reference
resource "local_file" "job_config" {
  filename = "${path.module}/job-config.json"
  content = jsonencode({
    project                 = var.project_id
    region                  = var.region
    service_account         = var.dataflow_service_account
    temp_location           = "gs://${var.temp_bucket}/temp"
    staging_location        = "gs://${var.temp_bucket}/staging"
    input_subscription      = var.input_subscription
    output_table            = var.output_table
    dlq_topic               = var.dlq_topic
    max_num_workers         = 2
    machine_type            = "n1-standard-2"
    use_public_ips          = false
    enable_streaming_engine = true
  })
}
