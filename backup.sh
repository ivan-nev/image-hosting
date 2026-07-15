#!/bin/sh
# backup-script.sh

DB_HOST=${DB_HOST:-db}
DB_NAME=${POSTGRES_DB:-images_db}
DB_USER=${POSTGRES_USER:-postgres}
DB_PASSWORD=${POSTGRES_PASSWORD:-password}
BACKUP_DIR=/backups
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_$DATE.sql.gz"

export PGPASSWORD="$DB_PASSWORD"

echo "Starting backup of $DB_NAME from $DB_HOST..."
if pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    echo "Backup created: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))"
    find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
else
    echo "Backup failed!" >&2
    exit 1
fi
