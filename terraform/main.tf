# ════════════════════════════════════════════════
# Cyndx LangGraph API — Terraform Configuration
# ════════════════════════════════════════════════
# Provider: Google Cloud Platform
# Services: Cloud Run, Secret Manager, Artifact Registry,
#           Cloud Logging, Cloud Monitoring

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }

  # Remote state in GCS (recommended for production)
  # Uncomment and configure for your setup:
  # backend "gcs" {
  #   bucket = "cyndx-terraform-state"
  #   prefix = "langgraph-api"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ── Enable Required GCP APIs ──

resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "secretmanager.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iamcredentials.googleapis.com",
  ])

  project            = var.project_id
  service            = each.value
  disable_on_destroy = false
}
