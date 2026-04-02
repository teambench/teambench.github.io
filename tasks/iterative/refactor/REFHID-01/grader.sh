#!/usr/bin/env bash
# Grader for REFHID-01: Service Extraction with Hidden Subscribers
# Output: a single float on stdout in range [0.0, 1.0]
set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")/workspace" && pwd)"
TOTAL=12

cd "$WORKSPACE"

# Ensure pytest is available
if ! python -m pytest --version &>/dev/null 2>&1; then
    pip install pytest -q 2>/dev/null || true
fi

# Run tests and capture JSON report
REPORT_FILE="$(mktemp /tmp/refhid01_report.XXXXXX.json)"
python -m pytest test/ \
    --tb=no \
    -q \
    --json-report \
    --json-report-file="$REPORT_FILE" \
    2>/dev/null || true

# Install pytest-json-report if needed
if [ ! -s "$REPORT_FILE" ]; then
    pip install pytest-json-report -q 2>/dev/null || true
    python -m pytest test/ \
        --tb=no \
        -q \
        --json-report \
        --json-report-file="$REPORT_FILE" \
        2>/dev/null || true
fi

# Parse passed count from JSON report
PASSED=0
if [ -s "$REPORT_FILE" ]; then
    PASSED=$(python3 -c "
import json, sys
with open('$REPORT_FILE') as f:
    data = json.load(f)
print(data.get('summary', {}).get('passed', 0))
" 2>/dev/null || echo 0)
else
    # Fallback: parse pytest stdout directly
    OUTPUT=$(python -m pytest test/ --tb=no -q 2>&1 || true)
    PASSED=$(echo "$OUTPUT" | grep -oP '^\d+ passed' | grep -oP '^\d+' || echo 0)
fi

rm -f "$REPORT_FILE"

# Compute score
python3 -c "
passed = int('$PASSED')
total = $TOTAL
score = min(1.0, passed / total) if total > 0 else 0.0
print(f'{score:.4f}')
"
