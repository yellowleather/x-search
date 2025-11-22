output "cloud_run_url" {
  description = "URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.tweet_capture_api.uri
}

output "pubsub_topic" {
  description = "Name of the Pub/Sub topic"
  value       = google_pubsub_topic.tweet_likes_raw.name
}

output "firestore_database" {
  description = "Firestore database name"
  value       = google_firestore_database.default.name
}
