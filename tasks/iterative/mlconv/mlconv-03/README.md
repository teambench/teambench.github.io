# MLCONV-03: Precision-Recall Threshold Optimization

## Description

A multi-turn benchmark task testing whether an agent can navigate the
precision-recall tradeoff in a fraud detection setting. The agent must tune a
RandomForest classifier to simultaneously satisfy a precision floor and a recall
floor — two constraints that pull in opposite directions.

## Why This Requires Multiple Turns

**Turn 1 failure mode:**

The naive fix is to lower the decision threshold from 0.5 to something like 0.3.
This fixes recall but breaks precision:

| What agent tries              | Result                              | Why it fails              |
|-------------------------------|-------------------------------------|---------------------------|
| Default threshold=0.5         | precision=0.97, recall=0.61         | Recall too low (< 0.65)   |
| Lower threshold to 0.30       | precision=0.82, recall=0.71         | Precision too low (< 0.90)|
| Add calibration, thresh=0.35  | precision=0.90, recall=0.68         | Both pass ✓               |

**Turn 2 (after Verifier feedback):** Verifier shows precision dropped below
0.90. Agent adds `CalibratedClassifierCV(method='isotonic')` which reshapes the
probability distribution, allowing threshold=0.35 to achieve both targets.

## Files

| File                          | Role                                            |
|-------------------------------|-------------------------------------------------|
| `spec.md`                     | Full specification (Planner reads this)         |
| `brief.md`                    | Short summary (Executor reads this)             |
| `workspace/classifier.py`     | Threshold + training logic — agent modifies this|
| `workspace/train_and_evaluate.py` | Evaluation script — read-only               |
| `workspace/generate_data.py`  | Deterministic data generator (seed=42)          |
| `workspace/requirements.txt`  | Python dependencies                             |
| `grader.sh`                   | Automated grader — outputs 0.0 to 1.0           |
| `generator.py`                | Parameterizes seed and thresholds               |

## Expected Scores by Agent Type

| Agent Type   | Expected Score | Reason                                                    |
|--------------|----------------|-----------------------------------------------------------|
| Oracle       | 0.50           | Lowers threshold (fixes recall), misses calibration step  |
| Single-pass  | 0.50           | Same — verifier finds precision dropped                   |
| Multi-turn   | 1.00           | Round 2 adds calibration, both constraints satisfied      |

## Grading

Run `bash grader.sh` from the task root directory.

- Score 1.0: precision >= 0.90 AND recall >= 0.65
- Score 0.5: exactly one constraint satisfied
- Score 0.0: neither constraint satisfied

## Stopping Condition

Score = 1.0 when `python train_and_evaluate.py` outputs `PASS`.

## Setup

```bash
cd workspace
pip install -r requirements.txt
python train_and_evaluate.py    # check current state (recall too low!)
```

## The Fix (Reference Solution)

Edit `classifier.py`:

```python
from sklearn.calibration import CalibratedClassifierCV

THRESHOLD = 0.35

def train(X_train, y_train):
    base = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=1)
    clf = CalibratedClassifierCV(base, method='isotonic', cv=3)
    clf.fit(X_train, y_train)
    return clf
```

Expected result: precision~0.90, recall~0.68.
