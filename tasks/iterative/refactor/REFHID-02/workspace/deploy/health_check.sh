#!/usr/bin/env bash
# Health check script.
# HIDDEN CONSTRAINT: Parses config/app.ini with awk.
# After INI->YAML migration this will break — must be updated to read YAML.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$WORKSPACE_DIR/config/app.ini"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found: $CONFIG_FILE" >&2
    exit 1
fi

# Parse INI with awk — will break after YAML migration
API_PORT=$(awk -F'=' '/^\[api\]/{found=1} found && /^port/{gsub(/ /,"",$2); print $2; exit}' "$CONFIG_FILE")
API_HOST=$(awk -F'=' '/^\[api\]/{found=1} found && /^host/{gsub(/ /,"",$2); print $2; exit}' "$CONFIG_FILE")

if [ -z "$API_PORT" ]; then
    echo "ERROR: Could not read api.port from config" >&2
    exit 1
fi

echo "HEALTH_CHECK_HOST=$API_HOST"
echo "HEALTH_CHECK_PORT=$API_PORT"
echo "HEALTH_OK=true"
