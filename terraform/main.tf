terraform {
  required_version = ">= 1.5.0"
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

# 1. Enable Required GCP APIs
resource "google_project_service" "services" {
  for_each = toset([
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "secretmanager.googleapis.com",
    "vpcaccess.googleapis.com"
  ])
  service            = each.key
  disable_on_destroy = false
}

# 2. VPC Connector for Secure Serverless SQL Connection
resource "google_vpc_access_connector" "connector" {
  name          = "vpc-conn"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = "default"
  depends_on    = [google_project_service.services]
}

# 3. Secret Manager configurations (e.g. Gemini API Key)
resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "gemini-api-key"
  replication {
    auto {}
  }
  depends_on = [google_project_service.services]
}

# 4. Production Cloud SQL Database Instance
resource "google_sql_database_instance" "postgres" {
  name             = "contract-llm-db-instance"
  database_version = "POSTGRES_16"
  region           = var.region
  root_password    = var.db_password
  depends_on       = [google_project_service.services]

  settings {
    tier = "db-f1-micro" # Lightweight production sandbox (scale up for higher traffic)
    ip_configuration {
      ipv4_enabled    = true
      private_network = "projects/${var.project_id}/global/networks/default"
    }
    database_flags {
      name  = "vector.similarity"
      value = "on"
    }
  }
}

resource "google_sql_database" "database" {
  name     = "llm_eval"
  instance = google_sql_database_instance.postgres.name
}

# 5. Cloud Run Service Deployment
resource "google_cloud_run_v2_service" "backend" {
  name     = "contract-llm-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    scaling {
      max_instance_count = 10
      min_instance_count = 0 # Scale to 0 to minimize idle costs
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cloudrun-source-deploy/backend:latest"
      
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }

      ports {
        container_port = 8000
      }

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "DATABASE_URL"
        value = "postgresql://postgres:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/llm_eval"
      }
      env {
        name  = "LLM_PROVIDER"
        value = "gemini"
      }
      env {
        name  = "LLM_MODEL"
        value = "gemini-2.5-flash"
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

# 6. Allow Unauthenticated Access to Cloud Run (Gateway-facing API)
resource "google_cloud_run_v2_service_iam_member" "noauth" {
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
