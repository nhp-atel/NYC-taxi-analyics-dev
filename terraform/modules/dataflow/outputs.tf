output "template_path" {
  description = "GCS path to Flex Template"
  value       = "gs://${var.temp_bucket}/templates/taxi-pipeline.json"
}

output "job_config_path" {
  description = "Local path to job configuration"
  value       = local_file.job_config.filename
}
