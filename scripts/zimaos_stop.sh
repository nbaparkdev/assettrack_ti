#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Docker Compose nao encontrado. Instale o plugin 'docker compose' ou o comando 'docker-compose'."
  exit 1
fi

"${COMPOSE_CMD[@]}" --env-file .env.zimaos -f docker-compose.zimaos.yml -p assettrack-zimaos down

echo "AssetTrack TI parado no perfil ZimaOS. Volumes preservados."
