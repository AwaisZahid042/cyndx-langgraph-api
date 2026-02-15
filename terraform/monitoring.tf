# ════════════════════════════════════════════════
# Monitoring & Alerting
# ════════════════════════════════════════════════

# ── Log-based Metric: Error Rate ──
resource "google_logging_metric" "error_rate" {
  name    = "cyndx-api-errors"
  project = var.project_id
  filter  = <<-EOT
    resource.type="cloud_run_revision"
    resource.labels.service_name="${var.service_name}"
    httpRequest.status>=500
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    display_name = "API 5xx Errors"
  }
}

# ── Log-based Metric: Latency from structured logs ──
resource "google_logging_metric" "request_latency" {
  name    = "cyndx-api-latency"
  project = var.project_id
  filter  = <<-EOT
    resource.type="cloud_run_revision"
    resource.labels.service_name="${var.service_name}"
    jsonPayload.latency_ms>0
  EOT

  metric_descriptor {
    metric_kind  = "DELTA"
    value_type   = "DISTRIBUTION"
    unit         = "ms"
    display_name = "API Request Latency"
  }

  value_extractor = "EXTRACT(jsonPayload.latency_ms)"

  bucket_options {
    explicit_buckets {
      bounds = [50, 100, 250, 500, 1000, 2500, 5000, 10000]
    }
  }
}

# ── Alert Policy: Error Rate > 5% over 5 minutes ──
resource "google_monitoring_alert_policy" "error_rate_alert" {
  display_name = "Cyndx API — High Error Rate"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Error rate exceeds 5%"

    condition_threshold {
      filter = <<-EOT
        resource.type="cloud_run_revision"
        AND resource.labels.service_name="${var.service_name}"
        AND metric.type="logging.googleapis.com/user/${google_logging_metric.error_rate.name}"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 5
      duration        = "300s" # 5 minutes

      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  # Notification channels can be added here
  # notification_channels = [google_monitoring_notification_channel.email.name]

  alert_strategy {
    auto_close = "1800s" # Auto-close after 30 minutes
  }

  documentation {
    content   = "The Cyndx LangGraph API error rate has exceeded 5% over a 5-minute window. Check Cloud Run logs for details."
    mime_type = "text/markdown"
  }

  depends_on = [google_logging_metric.error_rate]
}

# ── Alert Policy: P99 Latency > 10s ──
resource "google_monitoring_alert_policy" "latency_alert" {
  display_name = "Cyndx API — High P99 Latency"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "P99 latency exceeds 10 seconds"

    condition_threshold {
      filter = <<-EOT
        resource.type="cloud_run_revision"
        AND resource.labels.service_name="${var.service_name}"
        AND metric.type="run.googleapis.com/request_latencies"
      EOT

      comparison      = "COMPARISON_GT"
      threshold_value = 10000 # 10 seconds in ms
      duration        = "300s"

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
      }
    }
  }

  alert_strategy {
    auto_close = "1800s"
  }

  documentation {
    content   = "The Cyndx LangGraph API P99 latency has exceeded 10 seconds. This may indicate LLM provider slowdowns or resource constraints."
    mime_type = "text/markdown"
  }
}
