variable "project_id" {
  type        = string
  description = "The Google Cloud Project ID to deploy resources in"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "The target GCP region"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Password for the Postgres database instance root user"
}
