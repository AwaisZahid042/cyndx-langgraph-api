# ── Input Variables ──

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for deployment"
  type        = string
  default     = "us-central1"
}

variable "image_tag" {
  description = "Docker image tag to deploy (commit SHA or 'latest')"
  type        = string
  default     = "latest"
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
  default     = "cyndx-langgraph-api"
}

variable "default_model" {
  description = "Default LLM model"
  type        = string
  default     = "gpt-4o-mini"
}

variable "default_temperature" {
  description = "Default LLM temperature"
  type        = string
  default     = "0.7"
}

variable "max_instances" {
  description = "Maximum Cloud Run instances"
  type        = number
  default     = 10
}

variable "min_instances" {
  description = "Minimum Cloud Run instances (0 = scale to zero)"
  type        = number
  default     = 0
}

# ── Secret values (passed via CI/CD or tfvars, never committed) ──

variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "anthropic_api_key" {
  description = "Anthropic API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "google_api_key" {
  description = "Google Gemini API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "groq_api_key" {
  description = "Groq API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tavily_api_key" {
  description = "Tavily search API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "github_repo" {
  description = "GitHub repository (owner/repo) for Workload Identity Federation"
  type        = string
  default     = "your-username/cyndx-langgraph-api"
}
