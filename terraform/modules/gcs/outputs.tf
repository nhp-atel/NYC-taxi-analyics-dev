output "raw_bucket_name" {
  description = "Raw data bucket name"
  value       = google_storage_bucket.raw.name
}

output "raw_bucket_url" {
  description = "Raw data bucket URL"
  value       = google_storage_bucket.raw.url
}

output "temp_bucket_name" {
  description = "Temp bucket name"
  value       = google_storage_bucket.temp.name
}

output "temp_bucket_url" {
  description = "Temp bucket URL"
  value       = google_storage_bucket.temp.url
}
