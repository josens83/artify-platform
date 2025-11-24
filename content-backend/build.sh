#!/usr/bin/env bash
# Build script for Render.com deployment

set -o errexit  # Exit on error

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📦 Installing dependencies..."
cd "$SCRIPT_DIR"
pip install -r requirements.txt

echo "🔄 Running database migrations..."

# Check if alembic_version table exists
if alembic current 2>/dev/null | grep -q "(head)"; then
    echo "✅ Database is already at head revision"
    alembic upgrade head
elif alembic current 2>/dev/null | grep -q "^[0-9]"; then
    echo "📌 Database has existing revision, upgrading..."
    alembic upgrade head
else
    echo "⚠️  No alembic version found, attempting to stamp current state..."
    # Try to upgrade, if it fails due to existing tables, stamp and retry
    if ! alembic upgrade head 2>&1; then
        echo "⚠️  Initial migration failed (tables may already exist)"
        echo "📌 Stamping database at revision 004 (before new migration)..."
        alembic stamp 004 || true
        echo "🔄 Retrying upgrade to head..."
        alembic upgrade head
    fi
fi

echo "✅ Build completed successfully!"
