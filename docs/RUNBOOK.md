# TaskOps execution runbook

This guide explains how to resume the demonstrated lab and how its components were assembled on a fresh environment with the required tools already installed. It describes the source reviewed at commit [`10b0071`](https://github.com/axdy02/devops-capstone/tree/10b0071e5884dec4d65feebd1b34720b25a96cac). The [report](../REPORT.md) records observed results; commands here are instructions, not additional execution evidence.

Use **Ubuntu in WSL2** for the Linux commands below. Start Docker Desktop on Windows and enable integration for Ubuntu first. Keep the project in `~/devops-capstone`.

## 1 Resume an existing lab

Do not recreate secrets, databases, or the cluster when the previous lab already exists.

```bash
cd ~/devops-capstone
docker ps
minikube start -p taskops-capstone
kubectl --context=taskops-capstone get nodes
kubectl --context=taskops-capstone -n taskops-prod get pods,svc,pvc
systemctl is-active jenkins
```

If the Compose application is needed as well, resume it with:

```bash
docker compose up -d --wait
```

Resume monitoring and logging only when needed for the demonstration:

```bash
docker compose -f monitoring/docker-compose.yml up -d
docker compose -f logging/docker-compose.yml up -d
```

Check the monitoring network connection in section 7 if the Kubernetes target is down. After a pod rollout, an old port-forward may stop; restart that forwarding command in its terminal.

## 2 Open the local application and dashboards

Use a separate Ubuntu terminal for each port-forward and leave it running.

Application:

```bash
kubectl --context=taskops-capstone -n taskops-prod \
  port-forward service/taskops 8091:8090
```

Argo CD:

```bash
kubectl --context=taskops-capstone -n argocd \
  port-forward service/argocd-server 8082:443
```

| Component | URL |
| --- | --- |
| Compose TaskOps | http://localhost:8090 |
| Kubernetes TaskOps | http://localhost:8091 |
| Jenkins | http://localhost:8080 |
| Argo CD | https://localhost:8082 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |
| Kibana | http://localhost:5601 |

Use the credentials already configured in Jenkins, Argo CD, and Grafana. Do not paste passwords into the report, GitHub, or screenshots. If a forwarding port is occupied, check the existing terminal before starting another copy.

## 3 Fresh environment prerequisites

The full lab requires Git, OpenSSL, Docker with Compose, Python, Java/Jenkins, Terraform, Ansible, kubectl, Minikube, and netcat. The Jenkins account needs Docker access and a writable Jenkins workspace. Its configured scanner paths must exist:

```text
/var/lib/jenkins/security-tools/bin/bandit
/var/lib/jenkins/security-tools/bin/pip-audit
```

The recorded environment used WSL2 Ubuntu, Docker Desktop, Terraform 1.14.0, Ansible Core 2.20.1, Jenkins 2.580.1, and Java 21. These are recorded versions, not a requirement to downgrade an existing working setup.

Basic verification:

```bash
docker version
docker compose version
terraform version
ansible --version
kubectl version --client
minikube version
```

Run the existing README's [quick start](../README.md#quick-start-for-the-application) to clone the repository, generate `.env` only if absent, and start the Compose application. Do not share `.env` or replace passwords for an existing PostgreSQL volume.

## 4 Provision the dedicated Kubernetes environment

Run this section for a fresh TaskOps environment. Terraform uses `terraform_data` and `local-exec` to start the dedicated Minikube profile; Ansible then applies the namespace and quota policies.

```bash
cd ~/devops-capstone
terraform -chdir=infrastructure/terraform init
terraform -chdir=infrastructure/terraform plan
terraform -chdir=infrastructure/terraform apply

ansible-playbook \
  -i infrastructure/ansible/inventory.ini \
  infrastructure/ansible/configure-cluster.yml

kubectl --context=taskops-capstone get nodes
kubectl --context=taskops-capstone get namespaces -l project=taskops
kubectl --context=taskops-capstone -n taskops-prod get resourcequota,limitrange
minikube -p taskops-capstone ip
```

The profile defaults request 4 CPUs and 4096 MB. `taskops-dev` and `taskops-prod` are namespaces in the same cluster. A repeated unchanged Ansible run should report no configuration changes.

The captured node address was `192.168.67.2`. If the new profile uses another address, update the Kubernetes target in `monitoring/prometheus.yml` and the node address in `APP_TRUSTED_HOSTS` in `kubernetes/configmap.yaml`. Keep both files consistent. Commit intended manifest changes before asking Argo CD to manage them.

### Create the database secret once

An existing database must keep its matching credentials. The following guard preserves an existing Secret and refuses to invent new credentials when an existing database PVC is present:

```bash
if kubectl --context=taskops-capstone -n taskops-prod \
    get secret taskops-db-secret >/dev/null 2>&1; then
  echo "Existing database secret retained"
elif kubectl --context=taskops-capstone -n taskops-prod \
    get pvc postgres-data-taskops-db-0 >/dev/null 2>&1; then
  echo "Database storage already exists. Restore its matching secret before continuing."
else
  kubectl --context=taskops-capstone -n taskops-prod \
    create secret generic taskops-db-secret \
    --from-literal=POSTGRES_ADMIN_USER=taskops_admin \
    --from-literal=POSTGRES_ADMIN_PASSWORD="$(openssl rand -hex 24)" \
    --from-literal=DB_PASSWORD="$(openssl rand -hex 24)"
fi
```

If the guard reports existing storage with no matching Secret, stop this bootstrap step and recover the original credentials. Do not continue by resetting the database password.

Apply the resources and wait for readiness:

```bash
kubectl --context=taskops-capstone apply -f kubernetes/
kubectl --context=taskops-capstone -n taskops-prod \
  rollout status statefulset/taskops-db --timeout=180s
kubectl --context=taskops-capstone -n taskops-prod \
  rollout status deployment/taskops --timeout=180s
kubectl --context=taskops-capstone -n taskops-prod get deployments,statefulsets,pods,svc,pvc
```

The manifests reference public images in `axdy02/taskops`. If a recorded image tag is no longer available, build and publish an image through the configured Jenkins pipeline and update the intended manifest in Git. The PostgreSQL bootstrap runs only for a fresh database volume.

## 5 Jenkins pipeline setup and execution

For an existing Jenkins job, retain its settings and credentials. For a new job:

1. Ensure the Jenkins account can run Docker, Compose, Git, Bandit, and pip-audit. Test Git connectivity from `/tmp` or the Jenkins home, not from an inaccessible personal home directory.
2. Store Docker Hub username/token as a Jenkins username/password credential with ID `dockerhub-credentials`.
3. Store the GitHub username/token with repository contents write access as `github-credentials`.
4. Create a Pipeline job using **Pipeline script from SCM**, Git repository `https://github.com/axdy02/devops-capstone.git`, branch `*/main`, script path `Jenkinsfile`.
5. Match the Git installation name `Default` used by the credentials binding. Install the Pipeline, Git, Credentials Binding, and Timestamper plugins needed by the file.
6. Use the Git SCM excluded-message setting `^GitOps:.*$` for polling so generated manifest commits do not start unnecessary builds. The Jenkinsfile itself skips only the final Update GitOps stage for those commits.
7. Select **Build Now**, inspect the console, and confirm the test, build, publication, and manifest-update results.

The pipeline polls SCM every two minutes using Jenkins' hashed schedule. It performs:

| Stage | Action |
| --- | --- |
| Checkout | Retrieve source and determine the image tag |
| Automated Tests | Run `bash scripts/test.sh` |
| Security Scan | Run Bandit with `-ll -ii` and pip-audit on runtime requirements |
| Docker Build | Build the runtime image with version, commit, and date metadata |
| Container Scan | Generate a HIGH/CRITICAL Trivy report |
| Docker Hub Push | Publish the commit tag and `latest` |
| Update GitOps | Commit the deployment's new image tag and push it to GitHub |

Trivy uses `--exit-code 0`: findings are recorded, not a vulnerability gate. The report is archived in Jenkins. The Pytest result appears in console output; the current pipeline does not publish a JUnit report. Credentials are injected at execution time and are not stored in the repository.

## 6 Connect Argo CD

If Argo CD is already installed in the TaskOps cluster, keep that installation. For a clean cluster, install it once using the [official Argo CD getting-started instructions](https://argo-cd.readthedocs.io/en/stable/getting_started/), with `kubectl` set to the `taskops-capstone` context. The captured lab used Argo CD 3.6.3. Initial account setup should be completed privately; do not put initial passwords into this repository.

Before following those installation commands, explicitly select the dedicated context:

```bash
kubectl config use-context taskops-capstone
```

Then apply the repository's Application resource:

```bash
kubectl --context=taskops-capstone apply \
  -f infrastructure/argocd/application.yaml
kubectl --context=taskops-capstone -n argocd get application taskops
kubectl --context=taskops-capstone -n argocd get pods
```

Open the Argo CD port-forward from section 2 and verify **Synced** and **Healthy** for the expected Git revision. The Application watches `main:kubernetes`, uses automatic sync and self-healing, and leaves automatic pruning disabled.

A refresh updates Argo CD's view of the repository; sync applies the desired state. Argo CD does not automatically manage files in `infrastructure/ansible/` or `deployment-strategies/` with this Application definition.

## 7 Resume monitoring

Prometheus scrapes both the Compose application and a Kubernetes NodePort. Before the Compose scrape works, add `host.docker.internal` to the existing local `.env` trusted-host list without changing its password entries:

```text
APP_TRUSTED_HOSTS=localhost,127.0.0.1,[::1],app,host.docker.internal
```

Apply that application environment change and start monitoring:

```bash
docker compose up -d --force-recreate app
docker compose -f monitoring/docker-compose.yml up -d
```

Prometheus also needs access to the Minikube Docker network. Inspect its current attachment:

```bash
docker inspect --format '{{json .NetworkSettings.Networks}}' taskops-prometheus
```

If `taskops-capstone` is absent, connect it:

```bash
docker network connect taskops-capstone taskops-prometheus
```

This connection was manual in the lab and is not declared in the monitoring Compose file. Recheck it if that container is recreated. Check the Minikube IP as described in section 4 if the Kubernetes target changes.

In Prometheus, open **Status > Targets** and verify jobs `taskops` and `taskops-kubernetes`. In Grafana, use Prometheus URL `http://prometheus:9090` on their shared Compose network.

The demonstrated panel queries were:

```promql
up{job="taskops"}
```

```promql
taskops_database_available
```

```promql
sum(taskops_http_requests_total)
```

```promql
sum(rate(taskops_http_request_duration_seconds_sum[1m]))
/
sum(rate(taskops_http_request_duration_seconds_count[1m]))
```

The availability query above selects the Compose job. Add explicit job filters when comparing environments. Counters reset when workers restart. The Kubernetes Service target can select different Blue pods, so it is not a reliable per-pod aggregate. The existing Grafana named volume retains dashboards; no exported dashboard JSON is included in the source snapshot.

## 8 Collect a logging snapshot

```bash
docker compose -f logging/docker-compose.yml up -d
docker compose -f logging/docker-compose.yml ps
curl -fsS 'http://localhost:9200/_cluster/health?pretty'
```

After Elasticsearch and Logstash are ready, generate normal application activity in the browser and forward the recent Blue application logs:

```bash
bash logging/forward-logs.sh
curl -fsS 'http://localhost:9200/taskops-logs-*/_count?pretty'
```

In Kibana, create or select the data view `taskops-logs-*`, use `@timestamp` as the time field, and inspect records in Discover. Here `@timestamp` is ingestion time; the application also emits its own timestamp field.

The script reads a snapshot of up to 100 recent lines per selected container. It does not keep following new logs, and rerunning it can ingest the same lines again. It selects `app=taskops`, so Green logs are not included. Gunicorn diagnostic lines may appear alongside the application's JSON events.

## 9 Blue-green demonstration

Apply Green separately and verify readiness:

```bash
kubectl --context=taskops-capstone apply \
  -f deployment-strategies/blue-green/green.yaml
kubectl --context=taskops-capstone -n taskops-prod \
  rollout status deployment/taskops-green --timeout=180s
kubectl --context=taskops-capstone -n taskops-prod get deployments
```

Green is outside Argo's watched directory. It shares the PostgreSQL database with Blue and uses a different existing image tag.

To route the main Service to Green, edit **only the Service document** at the end of `kubernetes/deployment.yaml`:

```yaml
spec:
  type: ClusterIP
  selector:
    app: taskops-green
```

Keep the Blue Deployment's selectors and pod labels unchanged. Commit this Service change with a `GitOps:` message and push it; allow Argo CD to synchronize. Verify the build through the actual in-cluster Service:

```bash
kubectl --context=taskops-capstone -n taskops-prod \
  exec deployment/taskops -- python -c \
  'from urllib.request import urlopen; print(urlopen("http://taskops:8090/api/version").read().decode())'
```

For rollback, change that same Service selector back to `app: taskops`, commit, push, and verify again. At the documented revision, Green returns build `475ea41`, while Blue returns `538fca7`. Later Jenkins builds can change Blue's identity.

An existing browser port-forward may remain connected to its original pod, so it should not be the sole proof of a Service switch. The monitoring NodePort and log-forwarding selector remain on Blue. This demonstrates a controlled traffic switch and rollback; it does not measure continuous zero downtime.

## 10 Application configuration and sample data

Compose reads `.env` automatically. Native Python execution requires exported environment variables. Keep credentials private.

| Variable | Default or example | Purpose |
| --- | --- | --- |
| `APP_PORT` | `8090` | Compose host port or native development port |
| `APP_TRUSTED_HOSTS` | `localhost,127.0.0.1,[::1],app` | Allowed HTTP hosts; extend for the monitoring connection |
| `POSTGRES_DB` | `taskops` | Database name |
| `POSTGRES_ADMIN_USER` | `taskops_admin` | Database bootstrap account |
| `POSTGRES_ADMIN_PASSWORD` | Generated locally | Bootstrap account password |
| `DB_USER` | `taskops` | Restricted application login |
| `DB_PASSWORD` | Generated locally | Application database password |
| `DB_HOST` | `db` in Compose | Database hostname; Kubernetes uses `taskops-db` |
| `DB_PORT` | `5432` | Database port |
| `DB_SSLMODE` | `prefer` | Database TLS preference; not a proof that TLS is active |
| `APP_VERSION` | `0.1.0` | Displayed release version |
| `GIT_COMMIT_SHA` | Empty locally, set in CI | Source identity embedded in the image |
| `BUILD_DATE` | Empty locally, set in CI | UTC image build date |
| `LOG_LEVEL` | `INFO` | Application log verbosity |
| `SEED_DEMO` | `1` in the sample configuration | Insert five synthetic tasks once |

`scripts/01-bootstrap.sql` creates the restricted application role and schema on the first initialization of a fresh PostgreSQL volume. Numbered migrations run on the application's first database operation. The seed marker prevents the five sample tasks from being inserted repeatedly. Set `SEED_DEMO=0` before first use if an empty database is desired.

### API reference

A task has `id`, `title`, `description`, `status`, `priority`, `created_at`, and `updated_at`. The title must contain 1-120 characters; descriptions may contain up to 2,000 characters. Valid statuses are `pending`, `in_progress`, and `completed`; priorities are `low`, `medium`, and `high`.

| Method and path | Normal result |
| --- | --- |
| `GET /api/tasks` | Tasks ordered by newest ID; optional `?status=pending` filter |
| `POST /api/tasks` | Create a task, status 201, and a Location header |
| `GET /api/tasks/<id>` | Return the selected task |
| `PUT /api/tasks/<id>` | Replace editable fields; omitted optional fields take defaults |
| `DELETE /api/tasks/<id>` | Delete the task, status 204 |
| `GET /api/stats` | Total and per-status counts |
| `GET /api/version` | Name, application version, source commit, and build date |
| `GET /health` | HTTP health and release metadata |
| `GET /health/live` | Process liveness independent of the database |
| `GET /health/ready` | Database and task-schema readiness |
| `GET /metrics` | Prometheus exposition text |

Read-only checks after starting the Kubernetes port-forward:

```bash
curl -fsS http://localhost:8091/health/ready
curl -fsS http://localhost:8091/api/version
curl -fsS http://localhost:8091/api/stats
```

Example synthetic task creation:

```bash
curl -fsS -X POST http://localhost:8091/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Demonstrate the capstone","description":"Synthetic lab task","status":"pending","priority":"medium"}'
```

Invalid input returns 400; missing IDs return 404; oversized requests return 413; non-JSON bodies return 415; database failures return 503. Responses include a request ID. The app does not provide a user login and is intended for private lab use.

## 11 Tests and native development

The supported full-suite command is:

```bash
bash scripts/test.sh
```

The runner creates a unique Compose project and uses `taskops_test`, with a random schema per integration-test fixture. The captured run passed 46 tests. A later run must be assessed from its own output.

For native development, use Python 3.13 or 3.14 and a separately provisioned PostgreSQL database. First run `scripts/01-bootstrap.sql` as the database owner with its required environment variables exported, then export the app's database connection settings.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python wsgi.py
```

The native development server binds to localhost. Containers use Gunicorn. To run only unit tests in this environment:

```bash
python -m pytest -q tests/test_unit.py
```

The Jenkins runtime audit command is `pip-audit -r requirements.txt` from its configured security-tools environment. The separate development audit can use `pip-audit -r requirements-dev.txt`. These are point-in-time checks against the advisory database, not a guarantee of complete security.

## 12 Common recovery steps

| Symptom | First useful check |
| --- | --- |
| Docker command missing or socket unavailable | Start Docker Desktop and verify Ubuntu WSL integration |
| Kubernetes API connection refused | Start the dedicated profile and run `minikube status -p taskops-capstone` |
| Port-forward stops after deployment | Restart that port-forward in its terminal |
| Port already in use | Reuse the existing forwarding session or select another free local port |
| Prometheus gets HTTP 400 | Check the appropriate trusted-host entry and restart the affected app process |
| Kubernetes monitoring target is down | Check the node IP, NodePort Service, and Prometheus network attachment |
| Database readiness fails | Inspect pod events/logs and confirm the existing Secret still matches the stored database roles |
| Git push rejected with fetch first | Preserve local work, fetch remote changes, and rebase the local commit before a normal push |
| No recent Kibana entries | Check ELK readiness, run the batch-forwarding script, and adjust the Discover time window |

Do not use a forced push to solve a normal fetch-first error. Do not regenerate database credentials, delete volumes, or reset the cluster as a first troubleshooting step.

When finished, the following stops the lab components while retaining their stored resources:

```bash
docker compose -f logging/docker-compose.yml stop
docker compose -f monitoring/docker-compose.yml stop
docker compose stop
minikube stop -p taskops-capstone
```

Use Ctrl+C in each forwarding terminal. Resume with section 1 for the next demonstration.
