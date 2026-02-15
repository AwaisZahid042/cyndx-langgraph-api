# ════════════════════════════════════════════════
# IAM — Service Accounts & Least Privilege
# ════════════════════════════════════════════════

# ── Cloud Run Service Account ──
# Purpose-built SA for the application (NOT default compute SA)

resource "google_service_account" "api_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Cyndx LangGraph API Service Account"
  description  = "Dedicated service account for Cloud Run API service"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

# Least-privilege IAM roles for the API service account
resource "google_project_iam_member" "api_sa_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_sa_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

resource "google_project_iam_member" "api_sa_metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.api_sa.email}"
}

# ── CI/CD Service Account ──
# Used by GitHub Actions via Workload Identity Federation

resource "google_service_account" "cicd_sa" {
  account_id   = "${var.service_name}-cicd"
  display_name = "Cyndx CI/CD Service Account"
  description  = "Service account for GitHub Actions CI/CD pipeline"
  project      = var.project_id

  depends_on = [google_project_service.apis]
}

# CI/CD needs to deploy Cloud Run services
resource "google_project_iam_member" "cicd_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

# CI/CD needs to push Docker images
resource "google_project_iam_member" "cicd_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

# CI/CD needs to act as the API service account during deploy
resource "google_project_iam_member" "cicd_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

# CI/CD needs to manage secrets (for terraform apply)
resource "google_project_iam_member" "cicd_secret_admin" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}
