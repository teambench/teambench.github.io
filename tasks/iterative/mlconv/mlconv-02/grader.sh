#!/usr/bin/env bash
# Grader for MLCONV-02: Feature Leakage Detection
# Outputs a score between 0.0 and 1.0 to stdout.

set -euo pipefail

WORKSPACE_DIR="$(dirname "$0")/workspace"
AUC_THRESHOLD=0.85
GAP_THRESHOLD=0.05

cd "$WORKSPACE_DIR"

# Ensure dependencies are available
if ! python -c "import sklearn, xgboost, joblib, pandas, numpy" 2>/dev/null; then
    echo "0.0"
    exit 0
fi

# Run model training if model.pkl doesn't exist
if [ ! -f "model.pkl" ]; then
    python model.py > /dev/null 2>&1 || true
fi

# Run evaluation and capture output
EVAL_OUTPUT=$(python evaluate.py 2>/dev/null || true)

# Parse Test AUC and Gap
TEST_AUC=$(echo "$EVAL_OUTPUT" | grep -oP 'Test AUC:\s*\K[0-9]+\.[0-9]+' | head -1)
AUC_GAP=$(echo "$EVAL_OUTPUT" | grep -oP 'AUC Gap:\s*\K[0-9]+\.[0-9]+' | head -1)

if [ -z "$TEST_AUC" ] || [ -z "$AUC_GAP" ]; then
    echo "0.0"
    exit 0
fi

# Score calculation
python3 - <<EOF
test_auc = float("$TEST_AUC")
gap = float("$AUC_GAP")
auc_threshold = float("$AUC_THRESHOLD")
gap_threshold = float("$GAP_THRESHOLD")

passes_auc = test_auc >= auc_threshold
passes_gap = gap < gap_threshold

if passes_auc and passes_gap:
    score = 1.0
elif passes_gap and not passes_auc:
    # Leakage fixed but AUC not recovered
    score = 0.5 * (test_auc / auc_threshold)
elif passes_auc and not passes_gap:
    # AUC met but still overfitting (leakage not fully fixed)
    score = 0.3
else:
    # Neither condition met
    score = max(0.0, test_auc / auc_threshold * 0.4)

score = max(0.0, min(1.0, score))
print(f"{score:.4f}")
EOF
