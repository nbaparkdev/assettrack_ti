#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose --env-file .env.zimaos -f docker-compose.zimaos.yml -p assettrack-zimaos ps

api_port="$(grep -E '^API_PORT=' .env.zimaos 2>/dev/null | cut -d= -f2- || true)"
api_port="${api_port:-8080}"

echo ""
echo "Health da API:"
curl -fsS "http://localhost:${api_port}/health" || true
echo ""
