# TaskOps architecture

The Flask application serves the dashboard and API at a single origin. Browser mutations send JSON and the UI renders task content as text. A single synchronous Gunicorn worker serves requests in the runtime container and owns the Prometheus registry. Browser traffic enters through the loopback-bound host port. The PostgreSQL service joins only the internal database network.

## Database startup and transactions

PostgreSQL bootstraps the configured database and then creates a login that owns the `taskops` schema. The app uses that schema as its PostgreSQL search path. The application login has no superuser, role creation, or database creation rights. It can create objects in its own schema so startup can apply migrations.

On the first database operation, startup takes a transaction-scoped advisory lock for the current schema. The lock serializes migrations across processes. Each numbered SQL migration and its ledger entry commit together with the other pending migrations. Startup can retry after a failure because a failed transaction rolls back the ledger and schema changes. The optional seed inserts a marker and five tasks atomically. Deleting a seeded task leaves the marker intact.

Each API operation opens a connection with a two-second libpq connection timeout, two-second PostgreSQL statement timeout, and 1.5-second lock timeout. Psycopg closes each connection and commits or rolls back its transaction on context exit. The PostgreSQL volume keeps data across app and database container restarts. A database dump can include the `taskops` schema, its identity sequence, constraints, migrations, seed marker, and tasks. Use a dedicated database when practicing restores.

## Runtime signals

The process endpoints `/health` and `/health/live` remain available during database outages. Readiness and metrics probes check the schema through PostgreSQL and update the database gauge. A future orchestrator can use `/health/live` for liveness and `/health/ready` for traffic readiness. The Docker image and Compose demonstrate those two probe modes.

Build arguments set OCI release labels and default environment values. The app makes release metadata available through `/api/version` and shows the version in the dashboard. Application logs include the release version and a server-generated request ID. Logs normalize routes and omit query parameters, task content, raw exceptions, and credentials.

The Prometheus registry lives in the serving worker. Scrape each deployed instance independently. Configure a compatible multiprocess collection strategy if a future stage uses several workers per container.
