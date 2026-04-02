#!/usr/bin/env bash
# Grader for MLCONV-03: Hyperparameter Sensitivity Tradeoff
# Outputs a score between 0.0 and 1.0 to stdout.

set -euo pipefail

WORKSPACE_DIR="$(dirname "$0")/workspace"
F1_THRESHOLD=0.85
TIME_THRESHOLD=60.0

cd "$WORKSPACE_DIR"

# Ensure dependencies are available
if ! python -c "import sklearn, pandas, numpy" 2>/dev/null; then
    echo "0.0"
    exit 0
fi

# Run train_and_evaluate and capture output
EVAL_OUTPUT=$(python train_and_evaluate.py 2>/dev/null || true)

# Parse F1 and training time
VAL_F1=$(echo "$EVAL_OUTPUT" | grep -oP 'Validation F1:\s*\K[0-9]+\.[0-9]+' | head -1)
TRAIN_TIME=$(echo "$EVAL_OUTPUT" | grep -oP 'Training time:\s*\K[0-9]+\.[0-9]+' | head -1)

if [ -z "$VAL_F1" ] || [ -z "$TRAIN_TIME" ]; then
    echo "0.0"
    exit 0
fi

# Compute score
python3 - <<EOF
val_f1 = float("$VAL_F1")
train_time = float("$TRAIN_TIME")
f1_threshold = float("$F1_THRESHOLD")
time_threshold = float("$TIME_THRESHOLD")

passes_f1 = val_f1 >= f1_threshold
passes_time = train_time <= time_threshold

if passes_f1 and passes_time:
    score = 1.0
elif passes_f1 and not passes_time:
    # Accurate but too slow: partial credit, penalized by time overage
    time_ratio = min(train_time / time_threshold, 5.0)
    score = 0.5 / time_ratio
elif passes_time and not passes_f1:
    # Fast but inaccurate
    score = 0.25 * (val_f1 / f1_threshold)
else:
    score = 0.0

score = max(0.0, min(1.0, score))
print(f"{score:.4f}")
EOF
