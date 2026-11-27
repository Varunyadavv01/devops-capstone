#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

suffix=$(od -An -N8 -tx1 /dev/urandom | tr -d '[:space:]')
compose=(docker compose --env-file .env.example -p "taskops-test-$suffix" -f docker-compose.yml -f compose.test.yml)
export POSTGRES_DB=taskops_test POSTGRES_ADMIN_USER=taskops_test_admin DB_USER=taskops_test_app
export POSTGRES_ADMIN_PASSWORD="$(od -An -N24 -tx1 /dev/urandom | tr -d '[:space:]')"
export DB_PASSWORD="$(od -An -N24 -tx1 /dev/urandom | tr -d '[:space:]')"
export DB_HOST=db DB_PORT=5432 DB_SSLMODE=disable SEED_DEMO=0
export TASKOPS_TEST_DSN="host=db port=5432 dbname=taskops_test user=taskops_test_admin password=$POSTGRES_ADMIN_PASSWORD sslmode=disable"

cleanup() {
  "${compose[@]}" down --volumes
}
trap cleanup EXIT
"${compose[@]}" up -d --wait db
"${compose[@]}" run --rm --build -e TASKOPS_TEST_DSN app
