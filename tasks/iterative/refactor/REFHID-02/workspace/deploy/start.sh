#!/usr/bin/env bash
# Application startup script.
# HIDDEN CONSTRAINT: Parses config/app.ini directly with grep/cut.
# After INI->YAML migration this will break — must be updated to read YAML.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$WORKSPACE_DIR/config/app.ini"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE" >&2
    exit 1
fi

# Parse INI directly — will break after YAML migration
DB_HOST=$(grep "^host" "$CONFIG_FILE" | head -1 | cut -d= -f2 | tr -d ' ')
DB_PORT=$(grep "^port" "$CONFIG_FILE" | head -1 | cut -d= -f2 | tr -d ' ')
APP_PORT=$(grep "^port" "$CONFIG_FILE" | tail -1 | cut -d= -f2 | tr -d ' ')
APP_HOST=$(grep "^host" "$CONFIG_FILE" | grep -v "localhost" | cut -d= -f2 | tr -d ' ' 2>/dev/null || echo "0.0.0.0")

echo "DB_HOST=$DB_HOST"
echo "DB_PORT=$DB_PORT"
echo "APP_PORT=$APP_PORT"
echo "START_OK=true"
