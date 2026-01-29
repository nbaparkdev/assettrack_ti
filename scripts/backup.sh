#!/bin/bash

# Configuration
BACKUP_DIR="./backups"
DB_CONTAINER="assettrack_ti-db-1"
DB_USER="user"
DB_NAME="assettrack"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="${BACKUP_DIR}/backup_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Perform Backup
echo "Starting backup of ${DB_NAME}..."
docker exec -t "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$FILENAME"

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
