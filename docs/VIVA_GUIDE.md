# TaskOps — Simple Viva and Demo Guide

This guide describes the demonstration on 27 November 2026. Evidence IDs refer to screenshots in the capstone report. Practise the workflow in your own words.

## One-minute introduction

“My project is TaskOps, a small task-management application built with Flask and PostgreSQL. Users can create, update, filter and delete tasks. I used this simple application to demonstrate a complete DevOps workflow. GitHub stores the code. Jenkins checks for changes, runs tests and security scans, builds a Docker image and pushes it to Docker Hub. Jenkins then updates the Kubernetes image reference in Git. Argo CD reads that change and deploys it to my local Minikube cluster. Terraform starts the cluster, and Ansible configures its namespaces and resource policies. Prometheus and Grafana show metrics, while the ELK stack makes application logs searchable. I also demonstrated scaling, pod recovery, persistent storage, and switching traffic between Blue and Green deployments.”

## The workflow to remember

**Code commit → Jenkins tests and scans → Docker image → Docker Hub → image reference committed to Git → Argo CD → Kubernetes.**

Monitoring observes the running application. Logging helps explain individual events. Git-driven traffic switching provides a simple rollback demonstration. [E04, E47, E54, E59, E62, E69]

## 28 short viva questions

### Application and CI

**1. What problem does TaskOps solve?**  
It keeps tasks, descriptions, priorities and statuses in one place. The application is deliberately small so I can explain the delivery pipeline clearly. PostgreSQL keeps the task data beyond one application process.

**2. Which languages did you use?**  
Python for the Flask backend, HTML/CSS/JavaScript for the interface, SQL for database tables, shell scripts for commands, YAML for configuration, HCL for Terraform and a Groovy-based Jenkinsfile for the pipeline.

**3. Why use Git and GitHub?**  
Git records changes and lets me trace a version. GitHub hosts the repository that Jenkins and Argo CD read. The history shows separate commits for application features and infrastructure work. [E70]

**4. What is CI/CD in this project?**  
CI checks and packages changes through Jenkins. Deployment uses GitOps: Jenkins updates the desired image in Git, then Argo CD reconciles that configuration with Kubernetes. The successful chain is demonstrated in E54.

**5. What are the Jenkins stages?**  
Checkout, Automated Tests, Security Scan, Docker Build, Container Scan, Docker Hub Push and Update GitOps. The job polls Git approximately every two minutes using `H/2 * * * *`.

**6. What do the automated tests check?**  
Unit tests check smaller behaviours such as validation and release metadata. Integration tests exercise the API with a real test PostgreSQL database, including CRUD, filtering, constraints and readiness recovery. The recorded local run passed 46 tests. [E04]

**7. Can tests delete my demonstration data?**  
The test script uses a separate, randomly named Compose project and `taskops_test` database. It removes that test project's volumes afterwards. It is designed to keep test resources separate from the running demonstration database.

### Containers and infrastructure

**8. What is the difference between an image and a container?**  
An image packages the application and dependencies. A container is a running instance of that image. The Dockerfile creates the image; Docker or Kubernetes starts instances from it.

**9. Why use both Compose and Kubernetes?**  
Compose provides a straightforward local application/database setup and separate monitoring/logging stacks. Kubernetes demonstrates orchestration: replicas, health probes, Services, persistent volumes and automated deployment reconciliation.

**10. Why tag images with a Git SHA?**  
The SHA connects a built image to its source commit. The application also exposes its embedded SHA at `/api/version`. This distinguishes builds even though they all use the application version label `0.1.0`.

**11. What exactly does Terraform do here?**  
It uses a `terraform_data` resource and `local-exec` to run Minikube commands. This automates local cluster creation; it is not a cloud provider deployment or a complete tracker of every Kubernetes object. [E09–E12]

**12. What does Ansible do?**  
It verifies the cluster and applies development/production namespaces, quotas and limits. Repeating the unchanged playbook reports `changed=0`, demonstrating idempotency for these tasks. [E14, E16]

**13. What is Minikube?**  
It runs a local Kubernetes cluster. My profile is `taskops-capstone`. Development and production namespaces are logical areas of the same lab cluster, not two independently hosted production environments.

### Kubernetes and GitOps

**14. What do a Deployment and Service do?**  
The Deployment maintains the requested application replicas. A Service provides a stable endpoint and selects matching pods by labels. The main `taskops` Service is also where I switch Blue/Green traffic.

**15. Why use a StatefulSet and PVC for PostgreSQL?**  
The StatefulSet provides stable database pod identity. The PersistentVolumeClaim requests storage that remains available when the pod is recreated. My database uses one replica and a 2Gi claim. [E20, E32]

**16. How did you demonstrate scaling and recovery?**  
I manually scaled the application from two to four replicas, deleted one application pod and observed its replacement, then returned to two replicas. This proves manual scaling and pod replacement, not automatic load-based scaling. [E27–E29]

**17. What are the health probes?**  
Startup and liveness use `/health/live` to check the application process. Readiness uses `/health/ready` to check that the application can use its database. Kubernetes uses readiness to decide whether a pod should receive Service traffic.

**18. What is GitOps, and what does Argo CD watch?**  
Git holds the desired deployment configuration. Argo CD watches `main`, specifically the `kubernetes` directory, and reconciles it automatically. It does not automatically manage every directory or every container in the repository.

**19. What do Synced and Healthy mean?**  
Synced means the tracked live configuration matches the desired Git configuration. Healthy describes resource health. They are useful checks, but I also verify the running image and application response. E53 shows why checking the live image matters; E54 confirms convergence.

### Security and observability

**20. How are credentials handled?**  
Registry and Git credentials are stored in Jenkins credentials. Database passwords are injected through a Kubernetes Secret. Local `.env` is ignored by Git. My evidence displays only secret key names/sizes or masked credentials. [E37, E63]

**21. What do Bandit and pip-audit check?**  
Bandit checks Python source for security patterns; pip-audit checks known dependency vulnerabilities. My Bandit gate uses `-ll -ii`: five medium-severity, low-confidence findings were filtered out. The requirements audit reported no known vulnerabilities at that time. [E40–E41]

**22. Why did Jenkins pass with Trivy findings?**  
The Trivy stage is report-only using `--exit-code 0`. Its report showed 49 HIGH and two CRITICAL package-vulnerability findings. I archived the findings; I am not claiming the image was vulnerability-free. A stricter pipeline could block releases. [E44–E47]

**23. What is the difference between Prometheus and Grafana?**  
Prometheus collects metrics; Grafana queries and plots them. My dashboard shows application status, database health, requests and response time. Both Compose and Kubernetes scrape targets were UP. The Kubernetes target is a Service endpoint, not independently labelled per-pod monitoring. [E58–E59]

**24. How does your logging work?**  
A script sends a finite batch of Kubernetes logs to Logstash. Elasticsearch stores them and Kibana searches them. I demonstrated 115 indexed documents. This is not a continuously running collector; some Gunicorn text lines also have JSON parse-failure tags. [E61–E62]

### Deployment strategy and honest limits

**25. How does Blue-Green switching work?**  
Both deployments are ready simultaneously. Changing the main Service selector directs traffic to Blue or Green without changing the client endpoint. I committed the selector change to Git, let Argo synchronize it, and verified an internal Service response. [E64–E66]

**26. Was Green a newer release, and did rollback restore the original version?**  
Green used an older existing build, `475ea41`, to demonstrate routing. Rollback returned traffic to Blue, which by then ran `538fca7`. It demonstrated environment switching, not a new feature or restoration of the exact initial Blue binary. [E69]

**27. Is persistent storage the same as a backup?**  
No. My test showed data surviving database pod replacement using the same PVC. An independent backup and tested restore would protect against additional failures, such as volume loss. I did not demonstrate that full backup/restore process. [E31–E33]

**28. Is this production-ready or proven zero downtime?**  
It is a working local teaching prototype. I demonstrated successful releases and traffic switching, but did not continuously measure downtime. It has one cluster node, one database pod and no user authentication. Production use would need stronger availability, security and recovery measures.

## Four-to-six-minute demonstration

Have the services and necessary port-forwards running before the viva. Use existing successful builds and captured switch evidence so a fresh image download does not consume the demonstration.

| Time | Show | Explain |
|---|---|---|
| 0:00–0:45 | TaskOps dashboard; create one clearly labelled demo task | Flask API and PostgreSQL persistence |
| 0:45–1:30 | GitHub files and Jenkins successful console | Code, tests, scans, image build and publication |
| 1:30–2:15 | Argo CD Healthy/Synced and Kubernetes workloads | Git desired state and actual ready pods |
| 2:15–3:00 | Prometheus targets and Grafana dashboard | Metrics collection versus visualization |
| 3:00–3:45 | Kibana task logs | Searchable events; explain batch forwarding |
| 3:45–5:00 | Green switch/rollback evidence and current selector | Stable Service, two environments and build SHA verification |
| 5:00–5:30 | Persistence evidence and conclusion | Pod recovery demonstrated; backup remains separate |

Useful read-only checks in Ubuntu WSL:

```bash
kubectl --context=taskops-capstone -n taskops-prod get deploy,pods,svc,pvc
kubectl --context=taskops-capstone -n argocd get applications
curl -fsS http://localhost:8091/health/ready
curl -fsS http://localhost:8091/api/version
```

An existing `kubectl port-forward` can remain attached to an earlier selected pod. For Blue/Green routing evidence, use the in-cluster Service request shown in E65/E69.

## Ports used in the demonstration

| Endpoint | Port |
|---|---:|
| Compose application | 8090 |
| Kubernetes application through local port-forward | 8091 |
| Jenkins | 8080 |
| Argo CD through local port-forward | 8082 |
| Prometheus / Grafana | 9090 / 3000 |
| Elasticsearch / Kibana | 9200 / 5601 |
| Logstash TCP input | 5003 |
| Kubernetes metrics NodePort | 30090 |
| PostgreSQL inside its network | 5432 |

## Source reference

Configuration statements were checked against [repository revision 10b0071](https://github.com/axdy02/devops-capstone/tree/10b0071e5884dec4d65feebd1b34720b25a96cac), especially the [Jenkinsfile](https://github.com/axdy02/devops-capstone/blob/10b0071e5884dec4d65feebd1b34720b25a96cac/Jenkinsfile), [Argo CD application](https://github.com/axdy02/devops-capstone/blob/10b0071e5884dec4d65feebd1b34720b25a96cac/infrastructure/argocd/application.yaml) and [log forwarding script](https://github.com/axdy02/devops-capstone/blob/10b0071e5884dec4d65feebd1b34720b25a96cac/logging/forward-logs.sh). Execution results come from the supplied screenshots, not a new run.
