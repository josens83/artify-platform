#!/bin/bash

# Setup Automatic Backup Cron Job for Artify Platform
# This script configures a daily backup at 2:00 AM

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup_db.sh"

echo "🔧 Setting up automatic database backups..."
echo "📁 Script location: $BACKUP_SCRIPT"

# Check if backup script exists
if [ ! -f "$BACKUP_SCRIPT" ]; then
    echo "❌ ERROR: backup_db.sh not found at $BACKUP_SCRIPT"
    exit 1
fi

# Make sure backup script is executable
chmod +x "$BACKUP_SCRIPT"
echo "✅ Backup script is executable"

# Create cron job entry
CRON_JOB="0 2 * * * $BACKUP_SCRIPT >> $SCRIPT_DIR/backup.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$BACKUP_SCRIPT"; then
    echo "⚠️  Cron job already exists"
    echo ""
    echo "Current cron jobs for backup:"
    crontab -l 2>/dev/null | grep "$BACKUP_SCRIPT"
    echo ""
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Cancelled"
        exit 0
    fi

    # Remove existing cron job
    crontab -l 2>/dev/null | grep -v "$BACKUP_SCRIPT" | crontab -
    echo "🗑️  Removed existing cron job"
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
echo "✅ Cron job added successfully"

echo ""
echo "📅 Backup Schedule:"
echo "   - Time: 2:00 AM daily"
echo "   - Script: $BACKUP_SCRIPT"
echo "   - Log: $SCRIPT_DIR/backup.log"
echo ""
echo "📋 Current cron jobs:"
crontab -l 2>/dev/null

echo ""
echo "✅ Automatic backup setup completed!"
echo ""
echo "To view backup logs:"
echo "   tail -f $SCRIPT_DIR/backup.log"
echo ""
echo "To manually run backup:"
echo "   $BACKUP_SCRIPT"
echo ""
echo "To remove automatic backup:"
echo "   crontab -e"
echo "   (then delete the line with: $BACKUP_SCRIPT)"
