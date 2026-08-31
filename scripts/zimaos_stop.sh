#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
LOCAL_COMPOSE="$ROOT_DIR/.zimaos/bin/docker-compose"
export DOCKER_CONFIG="$ROOT_DIR/.zimaos/docker-config"
mkdir -p "$DOCKER_CONFIG"

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
elif [ -x "$LOCAL_COMPOSE" ]; then
  COMPOSE_CMD=("$LOCAL_COMPOSE")
else
  echo "Docker Compose nao encontrado. Rode: ./scripts/zimaos_install_compose.sh"
  exit 1
fi

"${COMPOSE_CMD[@]}" --env-file .env.zimaos -f docker-compose.zimaos.yml -p assettrack-zimaos down

echo "AssetTrack TI parado no perfil ZimaOS. Volumes preservados."
