#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
LOCAL_COMPOSE="$ROOT_DIR/.zimaos/bin/docker-compose"
source "$ROOT_DIR/scripts/resolve_compose.sh"
export DOCKER_CONFIG="$ROOT_DIR/.zimaos/docker-config"
mkdir -p "$DOCKER_CONFIG"

resolve_compose "$ROOT_DIR"

"${COMPOSE_CMD[@]}" --env-file .env.zimaos -f docker-compose.zimaos.yml -p assettrack-zimaos down

echo "AssetTrack TI parado no perfil ZimaOS. Volumes preservados."
