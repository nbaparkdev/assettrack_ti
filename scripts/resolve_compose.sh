#!/bin/bash

# Select a Compose v2 implementation. Compose v1.29 is incompatible with
# current Docker Engine versions and fails while recreating named volumes.
resolve_compose() {
  local root_dir="${1:-$(pwd)}"
  local local_compose="$root_dir/.zimaos/bin/docker-compose"

  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
  elif [ -x "$local_compose" ] && "$local_compose" version 2>/dev/null | grep -qE 'Docker Compose version v?2\.'; then
    COMPOSE_CMD=("$local_compose")
  elif command -v docker-compose >/dev/null 2>&1 && docker-compose version 2>/dev/null | grep -qE 'Docker Compose version v?2\.'; then
    COMPOSE_CMD=(docker-compose)
  else
    echo "Docker Compose v2 nao encontrado. O docker-compose 1.29.x nao e compativel com este Docker." >&2
    echo "Rode: ./scripts/zimaos_install_compose.sh" >&2
    return 1
  fi
}
