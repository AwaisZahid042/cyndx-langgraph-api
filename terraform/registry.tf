# ════════════════════════════════════════════════
# Artifact Registry — Docker Image Repository
# ════════════════════════════════════════════════

resource "google_artifact_registry_repository" "registry" {
  location      = var.region
  repository_id = "cyndx-registry"
  description   = "Docker images for Cyndx LangGraph API"
  format        = "DOCKER"

  cleanup_policies {
    id     = "keep-recent"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }

  depends_on = [google_project_service.apis]
}
