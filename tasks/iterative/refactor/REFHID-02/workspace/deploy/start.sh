#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$WORKSPACE_DIR/config/app.ini"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE" >&2
    exit 1
fi
DB_HOST=$(grep "^host" "$CONFIG_FILE" | head -1 | cut -d= -f2 | tr -d ' ')
DB_PORT=$(grep "^port" "$CONFIG_FILE" | head -1 | cut -d= -f2 | tr -d ' ')
APP_PORT=$(grep "^port" "$CONFIG_FILE" | tail -1 | cut -d= -f2 | tr -d ' ')
echo "DB_HOST=$DB_HOST"
echo "DB_PORT=$DB_PORT"
echo "APP_PORT=$APP_PORT"
echo "START_OK=true"
