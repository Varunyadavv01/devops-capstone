variable "cluster_name" {
  description = "Dedicated TaskOps Kubernetes profile"
  type        = string
  default     = "taskops-capstone"

  validation {
    condition     = var.cluster_name == "taskops-capstone"
    error_message = "Use the dedicated taskops-capstone profile."
  }
}

variable "cluster_cpus" {
  description = "CPU allocation for Minikube"
  type        = number
  default     = 4
}

variable "cluster_memory" {
  description = "Memory allocation in MB"
  type        = number
  default     = 4096
}
