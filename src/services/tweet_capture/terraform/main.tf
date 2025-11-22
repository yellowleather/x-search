terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Artifact Registry Repository
resource "google_artifact_registry_repository" "cloud_run_source_deploy" {
  location      = var.region
  repository_id = "cloud-run-source-deploy"
  description   = "Docker images for Cloud Run"
  format        = "DOCKER"
}

# Firestore Database
resource "google_firestore_database" "default" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"
}

# Pub/Sub Topic
resource "google_pubsub_topic" "tweet_likes_raw" {
  name = "tweet-likes-raw"

  message_retention_duration = "86400s" # 24 hours
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "tweet_capture_api" {
  name     = "tweet-capture-api"
  location = var.region

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/tweet-capture-api:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      env {
        name  = "PUBSUB_TOPIC"
        value = google_pubsub_topic.tweet_likes_raw.name
      }

      env {
        name = "JWT_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt_secret.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }

  depends_on = [
    google_artifact_registry_repository.cloud_run_source_deploy,
    google_firestore_database.default,
    google_pubsub_topic.tweet_likes_raw,
    google_secret_manager_secret_version.jwt_secret_version,
  ]
}

# Allow unauthenticated access to Cloud Run
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.tweet_capture_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Secret Manager for JWT Secret
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "tweet-capture-jwt-secret"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "jwt_secret_version" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret_key
}

# Grant Cloud Run access to the secret
resource "google_secret_manager_secret_iam_member" "cloud_run_secret_access" {
  secret_id = google_secret_manager_secret.jwt_secret.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# Get project info
data "google_project" "project" {
  project_id = var.project_id
}
