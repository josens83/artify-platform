#!/bin/bash

# Check Backup Status and Health
# Displays information about recent backups and their status

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$SCRIPT_DIR/backups}"
LOG_FILE="$SCRIPT_DIR/backup.log"

echo "🔍 Checking backup status..."
echo ""

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    echo "⚠️  Backup directory not found: $BACKUP_DIR"
    echo "Creating directory..."
    mkdir -p "$BACKUP_DIR"
fi

# Count backups
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/artify_backup_*.sql.gz 2>/dev/null | wc -l)
echo "📊 Total backups: $BACKUP_COUNT"

if [ $BACKUP_COUNT -eq 0 ]; then
    echo "⚠️  No backups found!"
    echo ""
    echo "To create a backup:"
    echo "   $SCRIPT_DIR/backup_db.sh"
    exit 0
fi

# Show recent backups
echo ""
echo "📋 Recent backups (last 10):"
echo "─────────────────────────────────────────────────────────"
ls -lht "$BACKUP_DIR"/artify_backup_*.sql.gz 2>/dev/null | head -10 | awk '{printf "%-20s %5s  %s\n", $6" "$7" "$8, $5, $9}'

# Show latest backup info
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/artify_backup_*.sql.gz 2>/dev/null | head -1)
if [ -n "$LATEST_BACKUP" ]; then
    echo ""
    echo "📦 Latest backup:"
    echo "   File: $(basename $LATEST_BACKUP)"
    echo "   Size: $(du -h $LATEST_BACKUP | cut -f1)"
    echo "   Date: $(stat -c %y $LATEST_BACKUP | cut -d'.' -f1)"

    # Check age
    BACKUP_AGE=$(($(date +%s) - $(stat -c %Y $LATEST_BACKUP)))
    HOURS_OLD=$((BACKUP_AGE / 3600))

    if [ $HOURS_OLD -lt 24 ]; then
        echo "   Status: ✅ Fresh (${HOURS_OLD} hours old)"
    elif [ $HOURS_OLD -lt 48 ]; then
        echo "   Status: ⚠️  Aging (${HOURS_OLD} hours old)"
    else
        DAYS_OLD=$((HOURS_OLD / 24))
        echo "   Status: ❌ Old (${DAYS_OLD} days old)"
        echo "   Consider running a new backup!"
    fi
fi

# Check cron job
echo ""
echo "⏰ Cron Job Status:"
if crontab -l 2>/dev/null | grep -q "backup_db.sh"; then
    echo "   ✅ Automatic backup is configured"
    echo ""
    echo "   Schedule:"
    crontab -l 2>/dev/null | grep "backup_db.sh"
else
    echo "   ❌ Automatic backup is NOT configured"
    echo ""
    echo "   To setup automatic backup:"
    echo "      $SCRIPT_DIR/setup_auto_backup.sh"
fi

# Check backup log
if [ -f "$LOG_FILE" ]; then
    echo ""
    echo "📝 Recent backup log (last 20 lines):"
    echo "─────────────────────────────────────────────────────────"
    tail -20 "$LOG_FILE"
else
    echo ""
    echo "📝 No backup log found at: $LOG_FILE"
fi

echo ""
echo "✅ Health check completed"
