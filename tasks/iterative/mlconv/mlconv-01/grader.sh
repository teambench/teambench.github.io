#!/usr/bin/env bash
# Grader for MLCONV-01: Class Imbalance Discovery
# Outputs a score between 0.0 and 1.0 to stdout.

set -euo pipefail

WORKSPACE_DIR="$(dirname "$0")/workspace"
THRESHOLD=0.80

cd "$WORKSPACE_DIR"

# Ensure dependencies are available
if ! python -c "import sklearn, joblib, pandas, numpy" 2>/dev/null; then
    echo "0.0"
    exit 0
fi

# Run pipeline if model doesn't exist
if [ ! -f "model.pkl" ]; then
    python pipeline.py > /dev/null 2>&1 || true
fi

# Run evaluation and capture output
EVAL_OUTPUT=$(python evaluate.py 2>/dev/null || true)

# Parse Macro-F1 from output
MACRO_F1=$(echo "$EVAL_OUTPUT" | grep -oP 'Macro-F1:\s*\K[0-9]+\.[0-9]+' | head -1)

if [ -z "$MACRO_F1" ]; then
    echo "0.0"
    exit 0
fi

# Compute score using Python for float arithmetic
python3 - <<EOF
macro_f1 = float("$MACRO_F1")
threshold = float("$THRESHOLD")
if macro_f1 >= threshold:
    score = 1.0
else:
    score = macro_f1 / threshold
score = max(0.0, min(1.0, score))
print(f"{score:.4f}")
EOF
