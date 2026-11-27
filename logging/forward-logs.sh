#!/usr/bin/env bash
set -euo pipefail

kubectl --context=taskops-capstone \
  -n taskops-prod logs \
  -l app=taskops \
  --all-containers=true \
  --tail=100 |
  nc -q 1 localhost 5003
