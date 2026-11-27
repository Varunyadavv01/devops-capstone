output "cluster_name" {
  description = "Provisioned Kubernetes profile"
  value       = terraform_data.minikube_cluster.output.profile
}

output "cluster_cpus" {
  value = terraform_data.minikube_cluster.output.cpus
}

output "cluster_memory_mb" {
  value = terraform_data.minikube_cluster.output.memory
}
