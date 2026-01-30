# Main topic for trip events
resource "google_pubsub_topic" "trip_events" {
  name    = "trip-events"
  project = var.project_id

  message_retention_duration = "86400s" # 24 hours

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
  }
}

# Dead letter queue topic for failed messages
resource "google_pubsub_topic" "dlq" {
  name    = "trip-events-dlq"
  project = var.project_id

  message_retention_duration = "604800s" # 7 days

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
    type        = "dlq"
  }
}

# Subscription for Dataflow pipeline
resource "google_pubsub_subscription" "dataflow" {
  name    = "dataflow-subscription"
  topic   = google_pubsub_topic.trip_events.id
  project = var.project_id

  # Retain unacked messages for 7 days
  message_retention_duration = "604800s"

  # Allow redelivery after 600 seconds
  ack_deadline_seconds = 600

  # Expire subscription after 31 days of inactivity
  expiration_policy {
    ttl = "2678400s"
  }

  # Dead letter policy
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dlq.id
    max_delivery_attempts = 5
  }

  # Retry policy
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
    consumer    = "dataflow"
  }
}

# Subscription for DLQ monitoring
resource "google_pubsub_subscription" "dlq_monitor" {
  name    = "dlq-monitor-subscription"
  topic   = google_pubsub_topic.dlq.id
  project = var.project_id

  message_retention_duration = "604800s"
  ack_deadline_seconds       = 60

  expiration_policy {
    ttl = "2678400s"
  }

  labels = {
    environment = "dev"
    service     = "taxi-analytics"
    type        = "monitoring"
  }
}

# IAM binding for producer to publish
resource "google_pubsub_topic_iam_member" "producer_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.trip_events.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.producer_service_account}"
}

# IAM binding for Dataflow to subscribe
resource "google_pubsub_subscription_iam_member" "dataflow_subscriber" {
  project      = var.project_id
  subscription = google_pubsub_subscription.dataflow.name
  role         = "roles/pubsub.subscriber"
  member       = "serviceAccount:${var.dataflow_service_account}"
}

# IAM binding for Dataflow to publish to DLQ
resource "google_pubsub_topic_iam_member" "dataflow_dlq_publisher" {
  project = var.project_id
  topic   = google_pubsub_topic.dlq.name
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${var.dataflow_service_account}"
}
