#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE=".env.zimaos"
COMPOSE_FILE="docker-compose.zimaos.yml"
PROJECT_NAME="assettrack-zimaos"
LOCAL_COMPOSE="$ROOT_DIR/.zimaos/bin/docker-compose"
export DOCKER_CONFIG="$ROOT_DIR/.zimaos/docker-config"
mkdir -p "$DOCKER_CONFIG"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker nao encontrado."
  exit 1
fi

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

if [ ! -f "$ENV_FILE" ]; then
  cp .env.zimaos.example "$ENV_FILE"
  host_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  host_ip="${host_ip:-IP_DO_ZIMAOS}"
  sed -i "s|http://IP_DO_ZIMAOS:8080/api/v1|http://${host_ip}:8080/api/v1|g" "$ENV_FILE"
  echo "Arquivo $ENV_FILE criado. Revise SECRET_KEY, POSTGRES_PASSWORD e VITE_API_URL antes de expor em producao."
fi

mkdir -p backend/uploads

export VITE_APP_VERSION_CODE="${VITE_APP_VERSION_CODE:-$(date -u +%s)}"
export VITE_APP_VERSION_NAME="${VITE_APP_VERSION_NAME:-$(date -u +%Y.%m.%d.%H%M)}"
export VITE_APP_BUILD_TIMESTAMP="${VITE_APP_BUILD_TIMESTAMP:-$(date -u +%Y-%m-%dT%H:%M:%SZ)}"

api_port="$(grep -E '^API_PORT=' "$ENV_FILE" | cut -d= -f2- || true)"
api_port="${api_port:-8080}"

echo "Subindo AssetTrack TI para ZimaOS..."
"${COMPOSE_CMD[@]}" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d --build

echo "Aguardando API..."
for _ in $(seq 1 30); do
  if curl -fsS "http://localhost:${api_port}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

web_port="$(grep -E '^WEB_PORT=' "$ENV_FILE" | cut -d= -f2- || true)"
web_port="${web_port:-8000}"
host_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
host_ip="${host_ip:-IP_DO_ZIMAOS}"

echo ""
echo "AssetTrack TI iniciado no perfil ZimaOS."
echo "Web:    http://${host_ip}:${web_port}"
echo "API:    http://${host_ip}:${api_port}/api/v1"
echo "Health: http://${host_ip}:${api_port}/health"
echo ""
echo "Comandos uteis:"
echo "  ./scripts/zimaos_status.sh"
echo "  ./scripts/zimaos_stop.sh"
