# Cloud Run runtime SA
resource "google_service_account" "api_sa" {
  account_id   = "${var.service_name}-sa"
  display_name = "Cyndx LangGraph API Service Account"
  description  = "Dedicated service account for Cloud Run API service"
  project      = var.project_id
  depends_on   = [google_project_service.apis]
}

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

# CI/CD SA
resource "google_service_account" "cicd_sa" {
  account_id   = "${var.service_name}-cicd"
  display_name = "Cyndx CI/CD Service Account"
  description  = "Service account for GitHub Actions CI/CD pipeline"
  project      = var.project_id
  depends_on   = [google_project_service.apis]
}

resource "google_project_iam_member" "cicd_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

resource "google_project_iam_member" "cicd_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

resource "google_project_iam_member" "cicd_secret_admin" {
  project = var.project_id
  role    = "roles/secretmanager.admin"
  member  = "serviceAccount:${google_service_account.cicd_sa.email}"
}

# IMPORTANT: least privilege actAs only on runtime SA (replace project-level iam.serviceAccountUser)
resource "google_service_account_iam_member" "cicd_act_as_api_sa" {
  service_account_id = google_service_account.api_sa.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.cicd_sa.email}"
}
