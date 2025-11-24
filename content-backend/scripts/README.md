# Database Management Scripts

This directory contains scripts for managing the Artify Platform database.

## Backup Script

### backup_db.sh

Creates timestamped backups of the PostgreSQL database with automatic compression and retention management.

**Features:**
- Timestamped backup files (format: `artify_backup_YYYYMMDD_HHMMSS.sql.gz`)
- Automatic gzip compression
- Configurable retention period (default: 7 days)
- Automatic cleanup of old backups
- Parses connection info from `DATABASE_URL` environment variable

**Usage:**

```bash
cd content-backend/scripts
chmod +x backup_db.sh
./backup_db.sh
```

**Environment Variables:**

- `DATABASE_URL` (required): PostgreSQL connection string
- `BACKUP_DIR` (optional): Backup directory (default: `./backups`)
- `BACKUP_RETENTION_DAYS` (optional): Days to keep backups (default: 7)

**Example:**

```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/artify"
export BACKUP_DIR="/var/backups/artify"
export BACKUP_RETENTION_DAYS=30
./backup_db.sh
```

**Output:**

```
🔄 Starting database backup...
📅 Timestamp: 20250107_143022
🗄️  Database: artify
📁 Backup directory: ./backups
✅ Backup successful: artify_backup_20250107_143022.sql
📦 Compressed: artify_backup_20250107_143022.sql.gz
💾 Size: 2.3M
🧹 Cleaning up backups older than 7 days...
📋 Current backups:
-rw-r--r-- 1 user user 2.3M Jan  7 14:30 artify_backup_20250107_143022.sql.gz
✅ Backup process completed
```

## Restore Script

### restore_db.sh

Restores the database from a backup file.

**⚠️ WARNING:** This script will DROP and recreate the entire database. Use with caution!

**Usage:**

```bash
cd content-backend/scripts
chmod +x restore_db.sh
./restore_db.sh ./backups/artify_backup_20250107_143022.sql.gz
```

**Features:**
- Interactive confirmation prompt
- Automatic decompression of .gz files
- Drops existing database and recreates it
- Restores all tables, indexes, and data

**Example:**

```bash
./restore_db.sh ./backups/artify_backup_20250107_143022.sql.gz
```

**Output:**

```
⚠️  WARNING: This will restore the database from backup
🗄️  Database: artify
📁 Backup file: ./backups/artify_backup_20250107_143022.sql.gz

Are you sure you want to continue? (yes/no): yes

🔄 Starting database restore...
📦 Decompressing backup...
🗑️  Dropping existing database...
🆕 Creating new database...
📥 Restoring from backup...
✅ Restore successful
✅ Database restored successfully
⚠️  Remember to run migrations if needed: alembic upgrade head
```

## Automated Backups

### Quick Setup ⭐ NEW

Use the automated setup script:

```bash
chmod +x setup_auto_backup.sh
./setup_auto_backup.sh
```

This will:
- Configure daily backups at 2:00 AM
- Setup logging to `backup.log`
- Verify script permissions
- Check for existing cron jobs

### Manual Cron Setup

Alternatively, configure manually:

```bash
# Edit crontab
crontab -e

# Add this line (adjust path as needed)
0 2 * * * cd /home/user/artify-platform/content-backend/scripts && ./backup_db.sh >> /var/log/artify-backup.log 2>&1
```

### Check Backup Status ⭐ NEW

Monitor your backups easily:

```bash
chmod +x check_backup_status.sh
./check_backup_status.sh
```

This shows:
- Total number of backups
- Recent backup list with sizes
- Latest backup age and status
- Cron job configuration
- Recent backup logs

**Example output:**
```
🔍 Checking backup status...

📊 Total backups: 15

📋 Recent backups (last 10):
Nov 24 02:00:00   2.3M  artify_backup_20251124_020000.sql.gz
Nov 23 02:00:00   2.1M  artify_backup_20251123_020000.sql.gz

📦 Latest backup:
   File: artify_backup_20251124_020000.sql.gz
   Size: 2.3M
   Date: 2025-11-24 02:00:00
   Status: ✅ Fresh (3 hours old)

⏰ Cron Job Status:
   ✅ Automatic backup is configured
```

## Supabase Backups

If using Supabase for production:

1. **Automatic Backups:** Supabase Pro plan includes automatic daily backups with 7-day retention
2. **Manual Backups:** Use the Supabase Dashboard → Database → Backups
3. **Export via CLI:**

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref your-project-ref

# Create backup
supabase db dump -f backup.sql
```

## Best Practices

1. **Regular Backups:** Schedule automated backups daily
2. **Test Restores:** Periodically test restore process on non-production database
3. **Multiple Locations:** Store backups in multiple locations (local + cloud)
4. **Before Migrations:** Always backup before running database migrations
5. **Before Major Changes:** Backup before deploying significant code changes
6. **Monitor Size:** Watch backup sizes and adjust retention as needed

## Troubleshooting

### pg_dump not found

Install PostgreSQL client tools:

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-client

# macOS
brew install postgresql
```

### Permission Denied

Make scripts executable:

```bash
chmod +x backup_db.sh restore_db.sh
```

### Connection Failed

Verify `DATABASE_URL` is set correctly:

```bash
echo $DATABASE_URL
```

Format should be: `postgresql://user:password@host:port/database`
