#!/bin/bash

# Configuration
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
BACKUP_DIR="$ROOT_DIR/backups"
DB_USER="user"
DB_NAME="assettrack"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Perform Backup
echo "Starting backup of ${DB_NAME}..."
if ! docker compose ps -q db >/dev/null 2>&1; then
  echo "❌ Docker Compose não está disponível ou o serviço db não foi encontrado."
  exit 1
fi

docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' | gzip > "$FILENAME"

if [ $? -eq 0 ]; then
  echo "✅ Backup successful: $FILENAME"
else
  echo "❌ Backup failed!"
  rm -f "$FILENAME"
  exit 1
fi

# Rotate Backups (Keep last 7 days)
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +7 -delete

echo "Done."
