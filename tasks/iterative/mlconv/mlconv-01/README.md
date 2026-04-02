# MLCONV-01: Class Imbalance Discovery

## Description

A multi-turn benchmark task testing whether an agent can diagnose and fix a class imbalance problem in a machine learning pipeline.

The agent is given a credit card fraud detection pipeline (`pipeline.py`) that achieves 0.998 accuracy but only 0.41 macro-F1. The key insight is that accuracy is misleading when classes are highly imbalanced — the model simply predicts "legitimate" for everything.

Derived from the **ULB Credit Card Fraud Detection** dataset (Dal Pozzolo et al., 2015):
https://www.kaggle.com/mlg-ulb/creditcardfraud — real fraud rate: 0.172% (492/284,807 transactions).
See `PROVENANCE.md` for full dataset origin and derivation notes.

## Why This Requires Multiple Turns

**Turn 1 failure mode:** The agent runs `python pipeline.py && python evaluate.py`, sees "Accuracy: 0.9980", and declares success without checking macro-F1. Or the agent checks macro-F1, sees 0.41, adds only `class_weight='balanced'` but skips SMOTE — this gets F1 to ~0.65, still failing.

**Turn 2 (after Verifier feedback):** Agent sees Verifier's attestation noting macro-F1 = 0.41 < 0.80. Agent must now:
1. Add `class_weight='balanced'` to RandomForestClassifier
2. Apply SMOTE from imbalanced-learn before training
3. Retrain and verify F1 ≥ 0.80

## Files

| File | Role |
|------|------|
| `spec.md` | Full specification (Planner reads this) |
| `brief.md` | Short summary (Executor reads this) |
| `workspace/pipeline.py` | Buggy training script — agent modifies this |
| `workspace/evaluate.py` | Evaluation script — read-only |
| `workspace/generate_data.py` | Data generator (called by pipeline.py if needed) |
| `workspace/requirements.txt` | Python dependencies |
| `grader.sh` | Automated grader — outputs 0.0 to 1.0 |
| `generator.py` | Parameterizes seed, fraud rate, n_features |

## Expected Scores by Agent Type

| Agent Type | Expected Score | Reason |
|------------|---------------|--------|
| Oracle (GPT-4) | 0.30–0.50 | May over-rely on accuracy metric |
| Single-pass | 0.40–0.55 | Likely misses SMOTE or class_weight |
| Multi-turn | 1.0 | Verifier feedback triggers correct fix |

## Stopping Condition

Score = 1.0 when `python evaluate.py` outputs `Macro-F1 >= 0.80` and prints `PASS`.

## Grading

Run `bash grader.sh` from the task root directory.

- Score 1.0: macro-F1 ≥ 0.80
- Partial credit: macro-F1 / 0.80 (capped at 1.0)
- Score 0.0: model not trained or evaluate.py errors

## Setup

```bash
cd workspace
pip install -r requirements.txt
python pipeline.py    # generates data + trains baseline model
python evaluate.py    # shows current macro-F1
```

## The Fix (Reference Solution)

```python
from imblearn.over_sampling import SMOTE

smote = SMOTE(random_state=42)
X_resampled, y_resampled = smote.fit_resample(X_train, y_train)

clf = RandomForestClassifier(
    n_estimators=100,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
clf.fit(X_resampled, y_resampled)
```

## Parameterization

```bash
# Default run (seed=42, fraud_rate=0.2%, 10 features)
python generator.py --seed 42

# Harder variant (more severe imbalance)
python generator.py --seed 99 --fraud-rate 0.001 --threshold 0.80

# Easier variant
python generator.py --seed 7 --fraud-rate 0.01 --threshold 0.75
```
