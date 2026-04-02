#!/usr/bin/env bash
# Grader for INCRCA-01: Cascading Timeout Misattribution
# Outputs a score between 0.0 and 1.0 to stdout.
#
# Usage: bash grader.sh [workspace_dir]
#   workspace_dir defaults to ./workspace

set -euo pipefail

WORKSPACE="${1:-$(dirname "$0")/workspace}"
WORKSPACE="$(realpath "$WORKSPACE")"

if [[ ! -d "$WORKSPACE" ]]; then
    echo "ERROR: workspace directory not found: $WORKSPACE" >&2
    echo "0.0"
    exit 1
fi

# Run the SLO test from within the workspace directory
cd "$WORKSPACE"

# Capture output of slo_test.py
SLO_OUTPUT=$(python test/integration/slo_test.py 2>/dev/null) || true

# Extract ERROR_RATE from output
ERROR_RATE=$(echo "$SLO_OUTPUT" | grep -oP 'ERROR_RATE=\K[0-9]+(\.[0-9]+)?' | head -1)

if [[ -z "$ERROR_RATE" ]]; then
    echo "ERROR: could not parse ERROR_RATE from slo_test.py output" >&2
    echo "$SLO_OUTPUT" >&2
    echo "0.0"
    exit 0
fi

# Score based on error rate
# Use Python for float comparison
SCORE=$(python3 - <<EOF
rate = float("$ERROR_RATE")
if rate < 0.1:
    print("1.0")
elif rate < 5.0:
    print("0.5")
else:
    print("0.0")
EOF
)

echo "$SCORE"
