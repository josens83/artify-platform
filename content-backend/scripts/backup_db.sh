#!/bin/bash

# Database Backup Script for Artify Platform
# Creates timestamped backups of PostgreSQL database

set -e  # Exit on error

# Load environment variables
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="artify_backup_${TIMESTAMP}.sql"

# Extract database connection info from DATABASE_URL
# Format: postgresql://user:password@host:port/database
DB_URL="${DATABASE_URL}"

if [ -z "$DB_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    exit 1
fi

# Parse DATABASE_URL
DB_USER=$(echo $DB_URL | sed -n 's|.*://\([^:]*\):.*|\1|p')
DB_PASS=$(echo $DB_URL | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
DB_HOST=$(echo $DB_URL | sed -n 's|.*@\([^:]*\):.*|\1|p')
DB_PORT=$(echo $DB_URL | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
DB_NAME=$(echo $DB_URL | sed -n 's|.*/\([^?]*\).*|\1|p')

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "🔄 Starting database backup..."
echo "📅 Timestamp: $TIMESTAMP"
echo "🗄️  Database: $DB_NAME"
echo "📁 Backup directory: $BACKUP_DIR"

# Perform backup
export PGPASSWORD="$DB_PASS"

if pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-acl \
    --file="$BACKUP_DIR/$BACKUP_FILE"; then

    echo "✅ Backup successful: $BACKUP_FILE"

    # Compress backup
    gzip "$BACKUP_DIR/$BACKUP_FILE"
    echo "📦 Compressed: ${BACKUP_FILE}.gz"

    # Calculate size
    SIZE=$(du -h "$BACKUP_DIR/${BACKUP_FILE}.gz" | cut -f1)
    echo "💾 Size: $SIZE"

else
    echo "❌ Backup failed"
    exit 1
fi

# Clean up old backups
echo "🧹 Cleaning up backups older than $RETENTION_DAYS days..."
find "$BACKUP_DIR" -name "artify_backup_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# List current backups
echo ""
echo "📋 Current backups:"
ls -lh "$BACKUP_DIR"/artify_backup_*.sql.gz 2>/dev/null || echo "No backups found"

echo ""
echo "✅ Backup process completed"

# Unset password
unset PGPASSWORD
