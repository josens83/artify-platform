#!/bin/bash

# Database Restore Script for Artify Platform
# Restores database from a backup file

set -e  # Exit on error

# Load environment variables
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "❌ ERROR: No backup file specified"
    echo "Usage: $0 <backup_file.sql.gz>"
    echo ""
    echo "Available backups:"
    ls -lh ./backups/artify_backup_*.sql.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Extract database connection info
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

echo "⚠️  WARNING: This will restore the database from backup"
echo "🗄️  Database: $DB_NAME"
echo "📁 Backup file: $BACKUP_FILE"
echo ""
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Restore cancelled"
    exit 0
fi

echo ""
echo "🔄 Starting database restore..."

# Decompress if needed
TEMP_FILE=""
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "📦 Decompressing backup..."
    TEMP_FILE="/tmp/artify_restore_$(date +%s).sql"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    SQL_FILE="$TEMP_FILE"
else
    SQL_FILE="$BACKUP_FILE"
fi

# Set password
export PGPASSWORD="$DB_PASS"

# Drop and recreate database (WARNING: destructive!)
echo "🗑️  Dropping existing database..."
dropdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" --if-exists "$DB_NAME"

echo "🆕 Creating new database..."
createdb -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"

# Restore from backup
echo "📥 Restoring from backup..."
if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$SQL_FILE"; then
    echo "✅ Restore successful"
else
    echo "❌ Restore failed"
    exit 1
fi

# Clean up temp file
if [ -n "$TEMP_FILE" ]; then
    rm -f "$TEMP_FILE"
fi

# Unset password
unset PGPASSWORD

echo ""
echo "✅ Database restored successfully"
echo "⚠️  Remember to run migrations if needed: alembic upgrade head"
