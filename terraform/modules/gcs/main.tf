# Bucket for raw trip data
resource "google_storage_bucket" "raw" {
  name     = "${var.project_id}-raw"
  location = var.region
  project  = var.project_id

  # Use standard storage for frequently accessed data
  storage_class = "STANDARD"

  # Enable versioning for data recovery
  versioning {
    enabled = true
  }

  # Lifecycle rules to manage costs
  lifecycle_rule {
    condition {
      age = 90 # Move to nearline after 90 days
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  lifecycle_rule {
    condition {
      age = 365 # Move to coldline after 1 year
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  # Prevent accidental deletion
  force_destroy = false

  uniform_bucket_level_access = true

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
    type        = "raw-data"
  }
}

# Bucket for temporary Dataflow files
resource "google_storage_bucket" "temp" {
  name     = "${var.project_id}-temp"
  location = var.region
  project  = var.project_id

  storage_class = "STANDARD"

  # Auto-delete temp files after 7 days
  lifecycle_rule {
    condition {
      age = 7
    }
    action {
      type = "Delete"
    }
  }

  # Temp bucket can be destroyed
  force_destroy = true

  uniform_bucket_level_access = true

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
    type        = "temp"
  }
}

# IAM bindings for Dataflow service account
resource "google_storage_bucket_iam_member" "dataflow_raw" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.dataflow_service_account}"
}

resource "google_storage_bucket_iam_member" "dataflow_temp" {
  bucket = google_storage_bucket.temp.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${var.dataflow_service_account}"
}
