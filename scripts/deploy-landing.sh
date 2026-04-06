#!/bin/bash
# scripts/deploy-landing.sh
# Deploy landing page to Dokku

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LANDING_DIR="${SCRIPT_DIR}/../landing/app/dist"
REMOTE_HOST="root@clawtech.ru"
REMOTE_PORT="2233"
APP_NAME="landing"

echo "Deploying landing page to Dokku..."

# Check if dist directory exists
if [[ ! -d "$LANDING_DIR" ]]; then
    echo "Error: $LANDING_DIR not found. Run 'npm run build' first."
    exit 1
fi

# Create static app if not exists
ssh -p "$REMOTE_PORT" "$REMOTE_HOST" "dokku apps:create $APP_NAME 2>/dev/null || true"

# Configure static buildpack
ssh -p "$REMOTE_PORT" "$REMOTE_HOST" "dokku buildpacks:set $APP_NAME https://github.com/dokku/buildpack-nginx.git"

# Deploy using git
cd "$LANDING_DIR"
git init
git add .
git commit -m "Landing deployment $(date)"
git remote remove dokku 2>/dev/null || true
git remote add dokku "dokku@clawtech.ru:$APP_NAME"
git push dokku main --force

echo "Landing deployed successfully!"
echo "URL: https://clawtech.ru"
