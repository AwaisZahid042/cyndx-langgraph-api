# ════════════════════════════════════════════════
# Secret Manager — Secure API Key Storage
# ════════════════════════════════════════════════
# Secrets are injected into Cloud Run at runtime.
# Never in source code, Dockerfiles, or Terraform state.

locals {
  secrets = {
    openai-api-key    = var.openai_api_key
    anthropic-api-key = var.anthropic_api_key
    google-api-key    = var.google_api_key
    groq-api-key      = var.groq_api_key
    tavily-api-key    = var.tavily_api_key
  }

  # Only create secrets that have values
  active_secrets = {
    for k, v in local.secrets : k => v if v != ""
  }
}

# Create a secret for each API key
resource "google_secret_manager_secret" "api_keys" {
  for_each  = local.active_secrets
  secret_id = each.key
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Store the actual secret values
resource "google_secret_manager_secret_version" "api_keys" {
  for_each    = local.active_secrets
  secret      = google_secret_manager_secret.api_keys[each.key].id
  secret_data = each.value
}

# Grant the API service account access to read secrets
resource "google_secret_manager_secret_iam_member" "api_sa_access" {
  for_each  = local.active_secrets
  secret_id = google_secret_manager_secret.api_keys[each.key].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api_sa.email}"
  project   = var.project_id
}
