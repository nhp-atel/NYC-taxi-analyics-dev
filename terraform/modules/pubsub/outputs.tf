output "topic_id" {
  description = "Trip events topic ID"
  value       = google_pubsub_topic.trip_events.id
}

output "topic_name" {
  description = "Trip events topic name"
  value       = google_pubsub_topic.trip_events.name
}

output "dlq_topic_id" {
  description = "Dead letter queue topic ID"
  value       = google_pubsub_topic.dlq.id
}

output "dlq_topic_name" {
  description = "Dead letter queue topic name"
  value       = google_pubsub_topic.dlq.name
}

output "dataflow_subscription_id" {
  description = "Dataflow subscription ID"
  value       = google_pubsub_subscription.dataflow.id
}

output "dataflow_subscription_name" {
  description = "Dataflow subscription name"
  value       = google_pubsub_subscription.dataflow.name
}
