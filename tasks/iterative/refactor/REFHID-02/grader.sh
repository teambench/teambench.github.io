#!/usr/bin/env bash
# Grader for REFHID-02: Config Format Migration INI -> YAML
# Output: a single float on stdout in range [0.0, 1.0]
set -euo pipefail

WORKSPACE="$(cd "$(dirname "$0")/workspace" && pwd)"
TOTAL=10

cd "$WORKSPACE"

if ! python -c "import yaml" &>/dev/null 2>&1; then
    pip install PyYAML -q 2>/dev/null || true
fi
if ! python -m pytest --version &>/dev/null 2>&1; then
    pip install pytest -q 2>/dev/null || true
fi

OUTPUT=$(python -m pytest test/ --tb=no -q 2>&1 || true)

PASSED=$(echo "$OUTPUT" | grep -oP '\d+(?= passed)' | tail -1 || echo 0)
PASSED=${PASSED:-0}

python3 -c "
passed = int('$PASSED')
total = $TOTAL
score = min(1.0, passed / total) if total > 0 else 0.0
print(f'{score:.4f}')
"
