#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "${repo_root}"

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "Created .env from .env.example. Example passwords are for local development only."
fi

docker compose config --quiet
docker compose up --build --detach
"${repo_root}/scripts/wait-for-stack.sh"

echo
echo "Environment ready"
echo "Frontend: http://localhost:${FRONTEND_PORT:-5173}"
echo "API docs: http://localhost:${BACKEND_PORT:-8000}/docs"
