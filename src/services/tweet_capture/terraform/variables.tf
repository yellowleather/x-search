variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "jwt_secret_key" {
  description = "Secret key for JWT token signing"
  type        = string
  sensitive   = true
}
