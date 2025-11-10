#!/usr/bin/env bash
# Build script for Render.com deployment

set -o errexit  # Exit on error

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "📦 Installing dependencies..."
cd "$SCRIPT_DIR"
pip install -r requirements.txt

echo "🔄 Running database migrations..."
alembic upgrade head

echo "✅ Build completed successfully!"
