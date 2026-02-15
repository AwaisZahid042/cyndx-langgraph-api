# ════════════════════════════════════════════════
# Cloud Run — Serverless Compute
# ════════════════════════════════════════════════

resource "google_cloud_run_v2_service" "api" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  # Ensure image exists before deploying
  depends_on = [
    google_artifact_registry_repository.registry,
    google_project_service.apis,
  ]

  template {
    # Use dedicated service account (not default compute SA)
    service_account = google_service_account.api_sa.email

    # Scaling configuration
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/cyndx-registry/${var.service_name}:${var.image_tag}"

      # Resource limits
      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
        cpu_idle = true # Scale down CPU when idle (cost saving)
      }

      # Port
      ports {
        container_port = 8080
      }

      # ── Environment Variables (non-sensitive) ──
      env {
        name  = "APP_NAME"
        value = "Cyndx LangGraph API"
      }
      env {
        name  = "APP_VERSION"
        value = "1.0.0"
      }
      env {
        name  = "LOG_LEVEL"
        value = "INFO"
      }
      env {
        name  = "DEFAULT_MODEL"
        value = var.default_model
      }
      env {
        name  = "DEFAULT_TEMPERATURE"
        value = var.default_temperature
      }
      env {
        name  = "RATE_LIMIT_ENABLED"
        value = "true"
      }
      env {
        name  = "OTEL_ENABLED"
        value = "true"
      }
      env {
        name  = "OTEL_SERVICE_NAME"
        value = var.service_name
      }

      # ── Secrets (injected from Secret Manager at runtime) ──
      dynamic "env" {
        for_each = contains(keys(local.active_secrets), "openai-api-key") ? [1] : []
        content {
          name = "OPENAI_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.api_keys["openai-api-key"].secret_id
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = contains(keys(local.active_secrets), "anthropic-api-key") ? [1] : []
        content {
          name = "ANTHROPIC_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.api_keys["anthropic-api-key"].secret_id
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = contains(keys(local.active_secrets), "google-api-key") ? [1] : []
        content {
          name = "GOOGLE_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.api_keys["google-api-key"].secret_id
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = contains(keys(local.active_secrets), "groq-api-key") ? [1] : []
        content {
          name = "GROQ_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.api_keys["groq-api-key"].secret_id
              version = "latest"
            }
          }
        }
      }

      dynamic "env" {
        for_each = contains(keys(local.active_secrets), "tavily-api-key") ? [1] : []
        content {
          name = "TAVILY_API_KEY"
          value_source {
            secret_key_ref {
              secret  = google_secret_manager_secret.api_keys["tavily-api-key"].secret_id
              version = "latest"
            }
          }
        }
      }

      # Startup probe
      startup_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 10
        timeout_seconds       = 3
      }

      # Liveness probe
      liveness_probe {
        http_get {
          path = "/health"
          port = 8080
        }
        period_seconds    = 30
        failure_threshold = 3
        timeout_seconds   = 3
      }
    }

    # Request timeout (LLM calls can be slow)
    timeout = "300s"

    # Max concurrent requests per instance
    max_instance_request_concurrency = 80
  }

  # Traffic routing — all traffic to latest revision
  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# ── Allow Public Access (unauthenticated) ──
# Required for reviewers to test the API

resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
