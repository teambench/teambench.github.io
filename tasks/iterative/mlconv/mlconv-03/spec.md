# MLCONV-03: Precision-Recall Threshold Optimization

## Overview

You are given a fraud detection classifier based on RandomForest. The current
configuration uses a default probability threshold of 0.5, which achieves high
precision (0.97) but unacceptably low recall (0.61) — it rejects too many real
fraud cases.

Your task is to optimize the classifier so it simultaneously achieves:

1. **Precision >= 0.90** (at most 10% of flagged transactions are false alarms)
2. **Recall >= 0.65** (catch at least 65% of real fraud cases)

## Dataset

Synthetic fraud detection data with 12 numeric features, ~8.8% fraud rate.
Generated deterministically from `generate_data.py` (seed=42).

- `data/train.csv` — 3750 samples for training
- `data/test.csv`  — 1250 samples for evaluation

## Current Problem

`classifier.py` uses `THRESHOLD = 0.5`. At this threshold:

| Metric    | Value | Target  | Status |
|-----------|-------|---------|--------|
| Precision | 0.971 | >= 0.90 | PASS   |
| Recall    | 0.609 | >= 0.65 | FAIL   |

The model is too conservative — it only flags transactions it is very confident
about, missing ~39% of real fraud.

## Required Fix

**Trap 1 (Round 1 failure):** Simply lowering threshold to 0.30:
- Recall = 0.71 (above target)
- Precision = 0.82 (below target — too many false alarms)

**Round 2 fix:** Add probability calibration + threshold=0.35:

```python
from sklearn.calibration import CalibratedClassifierCV

THRESHOLD = 0.35

def train(X_train, y_train):
    base = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=1)
    clf = CalibratedClassifierCV(base, method='isotonic', cv=3)
    clf.fit(X_train, y_train)
    return clf
```

Expected result: precision~0.90, recall~0.68 — both constraints satisfied.

## Evaluation

Run `python train_and_evaluate.py` — outputs precision and recall:

```
Threshold: 0.35
Precision: 0.9036
Recall:    0.6818
PASS  (precision 0.9036 >= 0.90, recall 0.6818 >= 0.65)
```

## Files

| File                  | Purpose                                      |
|-----------------------|----------------------------------------------|
| `classifier.py`       | Threshold + training logic — modify this     |
| `train_and_evaluate.py` | Evaluation script — do not modify          |
| `generate_data.py`    | Data generator (deterministic, seed=42)      |
| `data/train.csv`      | Training data (numeric features + label)     |
| `data/test.csv`       | Test data (numeric features + label)         |
| `requirements.txt`    | Python dependencies                          |

## Constraints

- Must use RandomForest (do not switch model families)
- Modify only `classifier.py`
- Do not modify `train_and_evaluate.py`
- `CalibratedClassifierCV` and threshold adjustment are the intended solution

## Grading

- Score 1.0: precision >= 0.90 AND recall >= 0.65
- Score 0.5: exactly one constraint met (either precision OR recall, not both)
- Score 0.0: neither constraint met

## Stopping Condition

Score = 1.0 when `python train_and_evaluate.py` prints `PASS`.
