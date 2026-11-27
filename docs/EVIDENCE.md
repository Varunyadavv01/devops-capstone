# Capstone evidence gallery

All 71 screenshots are copied unchanged from the supplied Word document and kept in its original order. The PDF embeds the same images. Captions distinguish intermediate states and final results.

[Complete report PDF](Capstone_Report.pdf) | [Report narrative](../REPORT.md) | [CSV index](evidence-index.csv)

| Topic | Evidence | PDF pages |
| --- | --- | --- |
| Application and local environment | E01-E08 | 16-21 |
| Terraform and Ansible | E09-E17 | 22-29 |
| Kubernetes and database configuration | E18-E25 | 29-36 |
| Scaling and recovery | E26-E34 | 36-43 |
| Jenkins and security scanning | E35-E47 | 44-53 |
| Argo CD and GitOps delivery | E48-E54 | 54-60 |
| Monitoring and centralized logging | E55-E62 | 61-67 |
| Runtime security and release switching | E63-E69 | 68-73 |
| Final checks and Git history | E70-E71 | 74-75 |

## E01 WSL environment and Git history

**PDF page 16.** Ubuntu on EAGLE responds to Git, Docker and Compose checks. The initial application commits are visible and the working tree is clean.

![E01: WSL environment and Git history](evidence/E01.png)

## E02 Healthy Compose services

**PDF page 16.** The application and PostgreSQL containers report healthy. The application is published on loopback port 8090.

![E02: Healthy Compose services](evidence/E02.png)

## E03 TaskOps application dashboard

**PDF page 17.** The Compose deployment displays five sample tasks, status counts and a ready backend. Task titles are sample data, not evidence that the named operations were performed.

![E03: TaskOps application dashboard](evidence/E03.png)

## E04 Automated test execution

**PDF page 18.** The isolated Compose test runner reports 46 passed in 0.58 seconds and cleans up its test resources. This timing belongs to this run only.

![E04: Automated test execution](evidence/E04.png)

## E05 Prometheus metrics endpoint

**PDF page 19.** The application exposes HTTP counters and a database-availability gauge through /metrics.

![E05: Prometheus metrics endpoint](evidence/E05.png)

## E06 Structured application log sample

**PDF page 19.** Recent application requests appear as JSON records with timestamps, request IDs, routes, status codes and durations.

![E06: Structured application log sample](evidence/E06.png)

## E07 Compose API and health checks

**PDF page 20.** Health, liveness and database readiness succeed. The initial local image reports version 0.1.0 with no embedded build date or Git SHA.

![E07: Compose API and health checks](evidence/E07.png)

## E08 Infrastructure preflight

**PDF page 21.** Ansible connectivity, Terraform, existing profiles and Docker resources are checked. The Jenkins root URL returns HTTP 403 in this early check.

![E08: Infrastructure preflight](evidence/E08.png)

## E09 Terraform initialization and validation

**PDF page 22.** Terraform initializes successfully and validates the infrastructure configuration.

![E09: Terraform initialization and validation](evidence/E09.png)

## E10 Terraform plan

**PDF page 23.** The plan contains one terraform_data resource with requested profile, CPU and memory inputs. The plan is saved for application.

![E10: Terraform plan](evidence/E10.png)

## E11 Terraform provisions the cluster

**PDF page 24.** The local-exec command starts the dedicated Minikube profile. Terraform reports one resource added.

![E11: Terraform provisions the cluster](evidence/E11.png)

## E12 Cluster health and repeat plan

**PDF page 25.** Minikube components are running, the node is Ready and system pods are Running. A second Terraform plan reports no changes to its managed state.

![E12: Cluster health and repeat plan](evidence/E12.png)

## E13 Ansible local connectivity

**PDF page 26.** The localhost ping module returns pong.

![E13: Ansible local connectivity](evidence/E13.png)

## E14 Ansible configures the cluster

**PDF page 26.** The playbook creates development and production namespaces with quotas and limit ranges. The recap shows ok=6, changed=1 and failed=0.

![E14: Ansible configures the cluster](evidence/E14.png)

## E15 Namespace resource policies

**PDF page 27.** Both namespaces and their resource policies are present. The production quota allows 15 pods and sets aggregate CPU and memory budgets.

![E15: Namespace resource policies](evidence/E15.png)

## E16 Ansible idempotency

**PDF page 28.** Repeating the playbook reports unchanged resources, ok=6, changed=0 and failed=0.

![E16: Ansible idempotency](evidence/E16.png)

## E17 Infrastructure milestone pushed

**PDF page 29.** The Terraform and Ansible implementation is pushed to GitHub as commit 3e2fec3.

![E17: Infrastructure milestone pushed](evidence/E17.png)

## E18 Images in the Minikube runtime

**PDF page 29.** The initial TaskOps and PostgreSQL images are available inside the cluster runtime.

![E18: Images in the Minikube runtime](evidence/E18.png)

## E19 ConfigMap and Secret metadata

**PDF page 30.** The application ConfigMap and three-key database Secret exist. Only key names and byte counts are displayed.

![E19: ConfigMap and Secret metadata](evidence/E19.png)

## E20 PostgreSQL and persistent storage

**PDF page 31.** The database StatefulSet is ready and its 2 GiB ReadWriteOnce claim is Bound. A headless Service exposes PostgreSQL internally.

![E20: PostgreSQL and persistent storage](evidence/E20.png)

## E21 Database privilege separation

**PDF page 32.** PostgreSQL lists a restricted taskops application role and a separate administrative role. The taskops schema belongs to the application role.

![E21: Database privilege separation](evidence/E21.png)

## E22 Application replicas and endpoints

**PDF page 33.** The application has two ready replicas, the database has one, and the Service has two application endpoints.

![E22: Application replicas and endpoints](evidence/E22.png)

## E23 Kubernetes port forwarding

**PDF page 34.** A local port-forward exposes the Kubernetes application on port 8091 and handles incoming connections.

![E23: Kubernetes port forwarding](evidence/E23.png)

## E24 TaskOps running on Kubernetes

**PDF page 35.** The browser displays the ready TaskOps dashboard through the Kubernetes port-forward.

![E24: TaskOps running on Kubernetes](evidence/E24.png)

## E25 Kubernetes API checks

**PDF page 36.** The Kubernetes-hosted application responds to health, readiness, version and statistics requests.

![E25: Kubernetes API checks](evidence/E25.png)

## E26 Baseline workloads

**PDF page 36.** Before scaling, the application is 2/2 ready, the database is 1/1 ready and the persistent claim remains Bound.

![E26: Baseline workloads](evidence/E26.png)

## E27 Scale from two to four replicas

**PDF page 37.** A manual scaling command changes the application from 2/2 to 4/4 ready replicas.

![E27: Scale from two to four replicas](evidence/E27.png)

## E28 Application pod replacement

**PDF page 38.** A selected application pod is deleted. Kubernetes creates a different pod and restores four ready replicas.

![E28: Application pod replacement](evidence/E28.png)

## E29 Return to two replicas

**PDF page 39.** The application is scaled back to two replicas and the rollout completes.

![E29: Return to two replicas](evidence/E29.png)

## E30 Application before the persistence check

**PDF page 40.** The dashboard remains available after the scaling exercise, with the five initial tasks.

![E30: Application before the persistence check](evidence/E30.png)

## E31 Create a persistence test record

**PDF page 41.** A Kubernetes Persistence Test task is added, increasing the total to six. This is the record used for the following database pod-recreation check.

![E31: Create a persistence test record](evidence/E31.png)

## E32 Recreate the PostgreSQL pod

**PDF page 42.** The database pod is deleted and recreated. The replacement is ready and the same persistent claim remains Bound.

![E32: Recreate the PostgreSQL pod](evidence/E32.png)

## E33 Verify data after pod recreation

**PDF page 42.** Readiness reports the database available and statistics still show six tasks after the database pod is recreated.

![E33: Verify data after pod recreation](evidence/E33.png)

## E34 Kubernetes manifests pushed

**PDF page 43.** The deployment and storage manifests are committed and pushed as 9e95297.

![E34: Kubernetes manifests pushed](evidence/E34.png)

## E35 Jenkins service status

**PDF page 44.** The service status is active. Later screenshots provide the actual pipeline execution evidence.

![E35: Jenkins service status](evidence/E35.png)

## E36 Jenkins directory-permission diagnosis

**PDF page 44.** Java, Buildx and Git respond for the Jenkins user. The Git check fails from the private user directory; E38 shows the successful check from /tmp.

![E36: Jenkins directory-permission diagnosis](evidence/E36.png)

## E37 Jenkins credentials area

**PDF page 45.** The Jenkins credentials administration page is open during setup. Credential values are not displayed.

![E37: Jenkins credentials area](evidence/E37.png)

## E38 Jenkins connectivity and workspace access

**PDF page 46.** From /tmp, the Jenkins user can read the repository HEAD, write to its own home directory and invoke Docker Buildx.

![E38: Jenkins connectivity and workspace access](evidence/E38.png)

## E39 Security tool versions

**PDF page 46.** Bandit 1.9.4, pip-audit 2.10.1 and Trivy 0.76.2 are available to Jenkins.

![E39: Security tool versions](evidence/E39.png)

## E40 Bandit threshold result

**PDF page 47.** The -ll -ii scan reports no findings at its selected threshold. The metrics still list five medium-severity, low-confidence findings.

![E40: Bandit threshold result](evidence/E40.png)

## E41 Dependency audit result

**PDF page 47.** pip-audit reports no known vulnerabilities for requirements.txt at the time of this scan.

![E41: Dependency audit result](evidence/E41.png)

## E42 Jenkinsfile committed

**PDF page 48.** The automated Jenkins pipeline is committed and pushed as acc1a0c.

![E42: Jenkinsfile committed](evidence/E42.png)

## E43 Jenkins pipeline execution

**PDF page 49.** Jenkins console output records the automated build and test workflow. Additional scan and completion details follow.

![E43: Jenkins pipeline execution](evidence/E43.png)

## E44 Trivy report summary

**PDF page 50.** The recorded image scan lists 46 Debian findings and five Python-package findings. Other listed runtime package entries show zero findings in this report.

![E44: Trivy report summary](evidence/E44.png)

## E45 Trivy operating-system findings

**PDF page 51.** The operating-system section records 44 high and two critical package-vulnerability findings. These are reported findings, not remediation evidence.

![E45: Trivy operating-system findings](evidence/E45.png)

## E46 Trivy Python-package findings

**PDF page 52.** The Python section records five high-severity findings. Package provenance and practical exploitability require separate assessment.

![E46: Trivy Python-package findings](evidence/E46.png)

## E47 Jenkins successful completion

**PDF page 53.** The console records image publication and a successful CI run. The configured Trivy stage reports findings without making them a blocking gate.

![E47: Jenkins successful completion](evidence/E47.png)

## E48 Argo CD installation in progress

**PDF page 54.** Argo CD workloads and Services are created. Several pods are still starting in this early capture; later Healthy and Synced screenshots show completion.

![E48: Argo CD installation in progress](evidence/E48.png)

## E49 Argo CD initial dashboard

**PDF page 55.** The Argo CD dashboard is accessible before the TaskOps Application is added.

![E49: Argo CD initial dashboard](evidence/E49.png)

## E50 Argo CD application resources

**PDF page 56.** TaskOps appears Healthy and Synced with its Kubernetes resources displayed in the application graph.

![E50: Argo CD application resources](evidence/E50.png)

## E51 Jenkins GitOps integration pushed

**PDF page 57.** The pipeline update that writes the deployment image back to Git is pushed as 475ea41.

![E51: Jenkins GitOps integration pushed](evidence/E51.png)

## E52 Jenkins GitOps run

**PDF page 58.** Jenkins console output records the delivery workflow after GitOps integration.

![E52: Jenkins GitOps run](evidence/E52.png)

## E53 GitOps image update observed

**PDF page 59.** The repository contains the generated GitOps deployment commit while the rollout is being checked. E54 captures the completed target image rollout.

![E53: GitOps image update observed](evidence/E53.png)

## E54 GitOps rollout verified

**PDF page 60.** Argo CD is Synced and Healthy. The application is running axdy02/taskops:475ea41 and the rollout completes.

![E54: GitOps rollout verified](evidence/E54.png)

## E55 Monitoring services started

**PDF page 61.** Prometheus and Grafana start as separate Docker Compose services on localhost ports 9090 and 3000.

![E55: Monitoring services started](evidence/E55.png)

## E56 Compose scrape target UP

**PDF page 62.** Prometheus reports its TaskOps Compose endpoint UP.

![E56: Compose scrape target UP](evidence/E56.png)

## E57 Grafana Prometheus data source

**PDF page 63.** Grafana lists the Prometheus data source used by the dashboard.

![E57: Grafana Prometheus data source](evidence/E57.png)

## E58 Grafana application dashboard

**PDF page 64.** The dashboard shows application status, database availability, total HTTP requests and average response time. The readings are a demonstration snapshot.

![E58: Grafana application dashboard](evidence/E58.png)

## E59 Both Prometheus targets UP

**PDF page 65.** Prometheus reports both the Compose target and Kubernetes NodePort target UP.

![E59: Both Prometheus targets UP](evidence/E59.png)

## E60 ELK services and cluster health

**PDF page 66.** Elasticsearch, Logstash and Kibana are running. The single-node Elasticsearch cluster reports green at this early check.

![E60: ELK services and cluster health](evidence/E60.png)

## E61 Centralized log count

**PDF page 66.** Elasticsearch contains 115 documents in the TaskOps log index with zero failed shards for the count request.

![E61: Centralized log count](evidence/E61.png)

## E62 Kibana log inspection

**PDF page 67.** Kibana displays the ingested TaskOps events. Structured HTTP logs coexist with server diagnostics and JSON parse-failure entries.

![E62: Kibana log inspection](evidence/E62.png)

## E63 Runtime security controls

**PDF page 68.** The capture shows Secret metadata, a non-root UID of 10001, read-only root filesystem, dropped capabilities, resource quotas and .env ignored by Git.

![E63: Runtime security controls](evidence/E63.png)

## E64 Blue and Green ready

**PDF page 69.** Both environments have two replicas. Blue initially uses f341dbd, Green uses 475ea41, and the main Service initially selects Blue.

![E64: Blue and Green ready](evidence/E64.png)

## E65 Traffic switched to Green

**PDF page 69.** The Service selects taskops-green. An in-cluster request to the Service returns Git revision 475ea41; the rollout status is still progressing in this capture.

![E65: Traffic switched to Green](evidence/E65.png)

## E66 Green switch synchronized

**PDF page 70.** Argo CD shows the Green-routing Git revision 83eef67 as Healthy and Synced.

![E66: Green switch synchronized](evidence/E66.png)

## E67 Rollback committed to Git

**PDF page 71.** The Service selector is changed back to taskops and pushed in rollback commit 6b01807.

![E67: Rollback committed to Git](evidence/E67.png)

## E68 Rollback synchronized

**PDF page 72.** Argo CD shows rollback revision 6b01807 as Healthy and Synced.

![E68: Rollback synchronized](evidence/E68.png)

## E69 Blue response after rollback

**PDF page 73.** The Service again selects Blue. The in-cluster response identifies the current Blue image as 538fca7, which was updated during the exercise.

![E69: Blue response after rollback](evidence/E69.png)

## E70 Final runtime and repository checks

**PDF page 74.** Both application environments and the database are running, Argo CD is Synced and Healthy, the supporting containers are listed and the Git history shows successive milestones.

![E70: Final runtime and repository checks](evidence/E70.png)

## E71 Final documentation commit pushed

**PDF page 75.** Commit 10b0071 is pushed and the working tree is clean. The new documentation package is prepared against this source revision.

![E71: Final documentation commit pushed](evidence/E71.png)
