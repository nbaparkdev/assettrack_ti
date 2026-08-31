#!/bin/bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose --env-file .env.zimaos -f docker-compose.zimaos.yml -p assettrack-zimaos down

echo "AssetTrack TI parado no perfil ZimaOS. Volumes preservados."
