terraform {
  required_version = ">= 1.4.0"
}

resource "terraform_data" "minikube_cluster" {
  input = {
    profile = var.cluster_name
    cpus    = var.cluster_cpus
    memory  = var.cluster_memory
  }

  triggers_replace = [
    var.cluster_name,
    var.cluster_cpus,
    var.cluster_memory
  ]

  provisioner "local-exec" {
    command = "minikube start -p ${self.input.profile} --driver=docker --container-runtime=containerd --cpus=${self.input.cpus} --memory=${self.input.memory}"
  }

  provisioner "local-exec" {
    when    = destroy
    command = "minikube delete -p ${self.input.profile}"
  }
}
