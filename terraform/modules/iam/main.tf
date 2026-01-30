# Service account for the event producer
resource "google_service_account" "producer" {
  account_id   = "taxi-producer"
  display_name = "NYC Taxi Event Producer"
  description  = "Service account for publishing trip events to Pub/Sub"
  project      = var.project_id
}

# Service account for Dataflow pipeline
resource "google_service_account" "dataflow" {
  account_id   = "taxi-dataflow"
  display_name = "NYC Taxi Dataflow Pipeline"
  description  = "Service account for Dataflow streaming pipeline"
  project      = var.project_id
}

# Service account for Cloud Run API
resource "google_service_account" "api" {
  account_id   = "taxi-api"
  display_name = "NYC Taxi API"
  description  = "Service account for FastAPI on Cloud Run"
  project      = var.project_id
}

# Producer needs Pub/Sub publisher role
resource "google_project_iam_member" "producer_pubsub" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.producer.email}"
}

# Dataflow needs multiple roles
resource "google_project_iam_member" "dataflow_worker" {
  project = var.project_id
  role    = "roles/dataflow.worker"
  member  = "serviceAccount:${google_service_account.dataflow.email}"
}

resource "google_project_iam_member" "dataflow_pubsub_subscriber" {
  project = var.project_id
  role    = "roles/pubsub.subscriber"
  member  = "serviceAccount:${google_service_account.dataflow.email}"
}

resource "google_project_iam_member" "dataflow_pubsub_viewer" {
  project = var.project_id
  role    = "roles/pubsub.viewer"
  member  = "serviceAccount:${google_service_account.dataflow.email}"
}

resource "google_project_iam_member" "dataflow_pubsub_publisher" {
  project = var.project_id
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.dataflow.email}"
}

resource "google_project_iam_member" "dataflow_bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dataflow.email}"
}

resource "google_project_iam_member" "dataflow_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dataflow.email}"
}

resource "google_project_iam_member" "dataflow_storage_object_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.dataflow.email}"
}

# API needs BigQuery read access
resource "google_project_iam_member" "api_bq_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.api.email}"
}

resource "google_project_iam_member" "api_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.api.email}"
}
