#!/bin/bash

# ==========================================
# AssetTrack TI - Reset do Banco de Dados
# ==========================================
# Remove e recria o volume PostgreSQL. Use somente quando realmente necessário.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DO_BACKUP=false
for arg in "$@"; do
  case "$arg" in
    --backup) DO_BACKUP=true ;;
    --help|-h)
      echo "Uso: $0 [--backup]"
      echo "  --backup  Faz backup antes de remover o banco"
      exit 0
      ;;
    *) echo "Parâmetro desconhecido: $arg"; exit 1 ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker não encontrado."
  exit 1
fi
if ! command -v curl >/dev/null 2>&1; then
  echo "❌ curl não encontrado."
  exit 1
fi

echo "⚠️ ATENÇÃO: todos os dados do banco serão removidos permanentemente."
read -rp "Digite 'SIM' para confirmar: " CONFIRM
if [ "$CONFIRM" != "SIM" ]; then
  echo "Cancelado."
  exit 0
fi

if [ "$DO_BACKUP" = true ]; then
  "$ROOT_DIR/scripts/backup.sh"
fi

docker compose down --remove-orphans

# Remover somente o volume do PostgreSQL. Os volumes de Redis e backups são preservados.
PROJECT_NAME="${COMPOSE_PROJECT_NAME:-$(basename "$ROOT_DIR" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9_- ' '_' | sed 's/[[:space:]]*$//')}"
DB_VOLUME="${PROJECT_NAME}_postgres_data"
if docker volume inspect "$DB_VOLUME" >/dev/null 2>&1; then
  docker volume rm "$DB_VOLUME"
fi

docker compose up -d db

echo "⏳ Aguardando PostgreSQL..."
for i in $(seq 1 60); do
  if docker compose exec -T db pg_isready -U "${POSTGRES_USER:-user}" -d "${POSTGRES_DB:-assettrack}" >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 60 ]; then
    echo "❌ Timeout aguardando PostgreSQL."
    exit 1
  fi
  sleep 2
done

docker compose up -d --build api web

echo "⏳ Aguardando API..."
for i in $(seq 1 60); do
  if curl -fsS http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ Banco recriado e aplicação disponível."
    exit 0
  fi
  sleep 2
done

echo "⚠️ A aplicação iniciou, mas a API ainda não respondeu. Consulte: docker compose logs api"
exit 1
