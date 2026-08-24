#!/usr/bin/env sh
set -eu

backend_port="${BACKEND_PORT:-8000}"
frontend_port="${FRONTEND_PORT:-5173}"

echo "Container status"
docker compose ps

echo "Backend liveness"
curl --fail --silent "http://localhost:${backend_port}/api/v1/health/live"
echo

echo "Backend readiness (PostgreSQL)"
curl --fail --silent "http://localhost:${backend_port}/api/v1/health/ready"
echo

echo "Frontend"
curl --fail --silent "http://localhost:${frontend_port}" >/dev/null
echo "ok"
