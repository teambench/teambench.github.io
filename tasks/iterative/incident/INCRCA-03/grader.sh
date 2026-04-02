#!/usr/bin/env bash
# Grader for INCRCA-03: Memory Leak
# Outputs a score between 0.0 and 1.0 to stdout.
#
# Usage: bash grader.sh [workspace_dir]

set -euo pipefail

WORKSPACE="${1:-$(dirname "$0")/workspace}"
WORKSPACE="$(realpath "$WORKSPACE")"

if [[ ! -d "$WORKSPACE" ]]; then
    echo "ERROR: workspace directory not found: $WORKSPACE" >&2
    echo "0.0"
    exit 1
fi

cd "$WORKSPACE"

# Install dependencies quietly if needed
if ! python3 -c "import pytest, psutil" 2>/dev/null; then
    pip install -r requirements.txt -q 2>/dev/null || true
fi

# Run pytest and capture output
PYTEST_OUTPUT=$(python3 -m pytest test/test_memory.py -v --tb=no -q 2>&1) || true

# Extract passed count
PASSED=$(echo "$PYTEST_OUTPUT" | grep -oP '(\d+) passed' | grep -oP '\d+' | tail -1)
PASSED="${PASSED:-0}"
TOTAL=8

SCORE=$(python3 - <<EOF
passed = int("$PASSED")
total = $TOTAL
score = passed / total
print(f"{score:.4f}")
EOF
)

echo "$SCORE"
