# TaskOps submission checklist

## Prepared in this package

- [x] One complete [capstone PDF](Capstone_Report.pdf) with the problem, design, implementation, testing, results and conclusions.
- [x] All 71 original screenshots, indexed as E01-E71 in the [evidence gallery](EVIDENCE.md).
- [x] Report below the portal's 25 MB limit.
- [x] Updated repository README and [Markdown report](../REPORT.md).
- [x] [Execution runbook](RUNBOOK.md) covering startup, infrastructure, CI/CD, monitoring and troubleshooting.
- [x] [Viva guide](Viva_Guide.pdf) with 28 short questions and a demonstration sequence.
- [x] Captions distinguish transitional errors, completed outcomes and security findings.

## Final actions by the student

- [ ] Upload the package's README, REPORT and docs contents to [the GitHub repository](https://github.com/axdy02/devops-capstone).
- [ ] Open the report and evidence links from the repository's README after committing.
- [ ] Upload **Capstone_Report.pdf** in the capstone PDF field on ZOSMA.
- [ ] Submit **https://github.com/axdy02/devops-capstone** in the GitHub field.
- [ ] Check that both submission fields show the expected submitted result.
- [ ] Before the viva, start the required local services and port-forwards using the runbook.

These are submission and preparation actions; this package has not been uploaded to the college portal or committed to GitHub automatically.

## Evidence coverage

| Requirement | Evidence |
| --- | --- |
| Working app, containerization and tests | E01-E07 |
| Terraform and Ansible infrastructure automation | E09-E17 |
| Kubernetes configuration, Services and persistent storage | E18-E26 |
| Scaling, application recovery and database persistence | E27-E34 |
| Jenkins, credentials, scans and image publication | E35-E47 |
| Argo CD and GitOps delivery | E48-E54 |
| Prometheus, Grafana and ELK | E55-E62 |
| Runtime controls and blue-green release strategy | E63-E69 |
| Final runtime and source-control checks | E70-E71 |

The existing repository already contains synthetic sample data in `migrations/seed_demo.sql`. A sample task named **Test database restore** is application data; it is not evidence that a restore was executed.

## Scope to explain accurately

The supplied results establish a working local teaching platform. Trivy reports unresolved findings without blocking the pipeline; the Bandit result uses confidence filtering. Recovery evidence covers pod replacement, reuse of the existing database PVC and a Service traffic rollback. Independent backup restoration, continuous log collection, production high availability and measured zero downtime are not claimed.

The brief asks broadly for recoverability and production readiness, but does not list a separate named backup/restore experiment. If the faculty asks for proof beyond the supplied run, capture that genuine result before extending the report.
