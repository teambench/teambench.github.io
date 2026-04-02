#!/usr/bin/env bash
# Grader for MLCONV-03: Precision-Recall Threshold Optimization
# Outputs a score between 0.0 and 1.0 to stdout.

set -euo pipefail

WORKSPACE_DIR="$(dirname "$0")/workspace"
PRECISION_THRESHOLD=0.90
RECALL_THRESHOLD=0.65

cd "$WORKSPACE_DIR"

# Ensure dependencies are available
if ! python -c "import sklearn, pandas, numpy" 2>/dev/null; then
    echo "0.0"
    exit 0
fi

# Run train_and_evaluate and capture output
EVAL_OUTPUT=$(python train_and_evaluate.py 2>/dev/null || true)

# Parse precision and recall
PRECISION=$(echo "$EVAL_OUTPUT" | grep -oP 'Precision:\s*\K[0-9]+\.[0-9]+' | head -1)
RECALL=$(echo "$EVAL_OUTPUT"    | grep -oP 'Recall:\s*\K[0-9]+\.[0-9]+'    | head -1)

if [ -z "$PRECISION" ] || [ -z "$RECALL" ]; then
    echo "0.0"
    exit 0
fi

# Compute score
python3 - <<EOF
precision = float("$PRECISION")
recall    = float("$RECALL")
p_thresh  = float("$PRECISION_THRESHOLD")
r_thresh  = float("$RECALL_THRESHOLD")

passes_precision = precision >= p_thresh
passes_recall    = recall    >= r_thresh

if passes_precision and passes_recall:
    score = 1.0
elif passes_precision and not passes_recall:
    # High precision but recall still too low: partial credit
    score = 0.5
elif passes_recall and not passes_precision:
    # Recall fixed but precision dropped too much: partial credit
    score = 0.5
else:
    score = 0.0

score = max(0.0, min(1.0, score))
print(f"{score:.4f}")
EOF
