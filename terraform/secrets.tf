# Secrets stored in GCP Secret Manager, injected into Cloud Run at runtime

locals {
  # define which secrets exist based on whether the variable is non-empty
  secret_keys = toset([
    for k, v in {
      "openai-api-key"    = var.openai_api_key
      "anthropic-api-key" = var.anthropic_api_key
      "google-api-key"    = var.google_api_key
      "groq-api-key"      = var.groq_api_key
      "tavily-api-key"    = var.tavily_api_key
    } : k if nonsensitive(v) != ""
  ])

  secret_values = {
    "openai-api-key"    = var.openai_api_key
    "anthropic-api-key" = var.anthropic_api_key
    "google-api-key"    = var.google_api_key
    "groq-api-key"      = var.groq_api_key
    "tavily-api-key"    = var.tavily_api_key
  }
}

resource "google_secret_manager_secret" "api_keys" {
  for_each  = local.secret_keys
  secret_id = each.value
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

resource "google_secret_manager_secret_version" "api_keys" {
  for_each    = local.secret_keys
  secret      = google_secret_manager_secret.api_keys[each.value].id
  secret_data = local.secret_values[each.value]
}

resource "google_secret_manager_secret_iam_member" "api_sa_access" {
  for_each  = local.secret_keys
  secret_id = google_secret_manager_secret.api_keys[each.value].secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api_sa.email}"
  project   = var.project_id
}
