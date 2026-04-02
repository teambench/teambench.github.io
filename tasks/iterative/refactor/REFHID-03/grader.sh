#!/usr/bin/env bash
# Grader for REFHID-03: ORM Migration with Unsupported Patterns
# Output: a single float on stdout in range [0.0, 1.0]
set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")/workspace" && pwd)"
TOTAL=10

cd "$WORKSPACE"

# Ensure pytest is available
if ! python -m pytest --version &>/dev/null 2>&1; then
    pip install pytest -q 2>/dev/null || true
fi

# Ensure SQLAlchemy is available (needed for pre-migration fallback)
if ! python -c "import sqlalchemy" &>/dev/null 2>&1; then
    pip install SQLAlchemy -q 2>/dev/null || true
fi

REPORT_FILE="$(mktemp /tmp/refhid03_report.XXXXXX.json)"
python -m pytest test/ \
    --tb=no \
    -q \
    --json-report \
    --json-report-file="$REPORT_FILE" \
    2>/dev/null || true

if [ ! -s "$REPORT_FILE" ]; then
    pip install pytest-json-report -q 2>/dev/null || true
    python -m pytest test/ \
        --tb=no \
        -q \
        --json-report \
        --json-report-file="$REPORT_FILE" \
        2>/dev/null || true
fi

PASSED=0
if [ -s "$REPORT_FILE" ]; then
    PASSED=$(python3 -c "
import json
with open('$REPORT_FILE') as f:
    data = json.load(f)
print(data.get('summary', {}).get('passed', 0))
" 2>/dev/null || echo 0)
else
    OUTPUT=$(python -m pytest test/ --tb=no -q 2>&1 || true)
    PASSED=$(echo "$OUTPUT" | grep -oP '^\d+ passed' | grep -oP '^\d+' || echo 0)
fi

rm -f "$REPORT_FILE"

python3 -c "
passed = int('$PASSED')
total = $TOTAL
score = min(1.0, passed / total) if total > 0 else 0.0
print(f'{score:.4f}')
"
