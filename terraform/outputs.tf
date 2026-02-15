# ── Outputs ──

output "service_url" {
  description = "Cloud Run service URL"
  value       = google_cloud_run_v2_service.api.uri
}

output "service_name" {
  description = "Cloud Run service name"
  value       = google_cloud_run_v2_service.api.name
}

output "api_sa_email" {
  description = "API service account email"
  value       = google_service_account.api_sa.email
}

output "cicd_sa_email" {
  description = "CI/CD service account email"
  value       = google_service_account.cicd_sa.email
}

output "registry_url" {
  description = "Artifact Registry URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.registry.repository_id}"
}

output "wif_provider" {
  description = "Workload Identity Federation provider (use in GitHub secrets)"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "swagger_url" {
  description = "Swagger/OpenAPI docs URL"
  value       = "${google_cloud_run_v2_service.api.uri}/docs"
}
