#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
LOCAL_COMPOSE="$ROOT_DIR/.zimaos/bin/docker-compose"
source "$ROOT_DIR/scripts/resolve_compose.sh"
export DOCKER_CONFIG="$ROOT_DIR/.zimaos/docker-config"
mkdir -p "$DOCKER_CONFIG"

resolve_compose "$ROOT_DIR"

"${COMPOSE_CMD[@]}" --env-file .env.zimaos -f docker-compose.zimaos.yml -p assettrack-zimaos ps

api_port="$(grep -E '^API_PORT=' .env.zimaos 2>/dev/null | cut -d= -f2- || true)"
api_port="${api_port:-8080}"

echo ""
echo "Health da API:"
curl -fsS "http://localhost:${api_port}/health" || true
echo ""
