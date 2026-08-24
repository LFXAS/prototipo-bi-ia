#!/usr/bin/env bash
set -euo pipefail

timeout_seconds=${STACK_TIMEOUT_SECONDS:-600}
deadline=$((SECONDS + timeout_seconds))

echo "Waiting for the four runtime services to become healthy..."

while (( SECONDS < deadline )); do
    unhealthy=""
    for service in postgres sqlserver backend frontend; do
        container_id=$(docker compose ps --quiet "${service}")
        if [[ -z "${container_id}" ]]; then
            unhealthy="${unhealthy}${unhealthy:+,}${service}"
            continue
        fi

        service_health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}")
        if [[ "${service_health}" != "healthy" ]]; then
            unhealthy="${unhealthy}${unhealthy:+,}${service}"
        fi
    done

    if [[ -z "${unhealthy}" ]]; then
        curl --fail --silent "http://localhost:${BACKEND_PORT:-8000}/api/v1/health/ready" >/dev/null
        echo "All services are healthy."
        exit 0
    fi

    echo "Still waiting: ${unhealthy}"
    sleep 10
done

docker compose ps
docker compose logs --tail=120 postgres sqlserver backend frontend
echo "The environment did not become healthy within ${timeout_seconds} seconds." >&2
exit 1
