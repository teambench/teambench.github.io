# MLCONV-03: Hyperparameter Sensitivity Tradeoff

## Overview

This task is derived from the **Stanford AI Lab Large Movie Review Dataset** (Maas et al., 2011 —
https://ai.stanford.edu/~amaas/data/sentiment/), the canonical benchmark for binary sentiment
classification. The workspace uses a 2,000-sample subset matching the real dataset's vocabulary
distribution (positive/negative word ratios, bigram phrase patterns, review length distribution).

You are given a TF-IDF + Logistic Regression sentiment classifier. The current configuration achieves **0.91 F1** but takes **~180 seconds** to train. Your task is to optimize the hyperparameters so the model meets **both** constraints simultaneously:

1. **Validation F1 ≥ 0.85**
2. **Training time ≤ 60 seconds**

## Current Problem

The current hyperparameters in `classifier.py` are over-configured:

```python
TfidfVectorizer(max_features=100000, ngram_range=(1, 2))
LogisticRegression(C=10.0, max_iter=1000, solver='lbfgs')
```

This configuration is accurate but far too slow. Simple reductions cause traps:

- **Trap A:** Reduce only `C` to 0.1 → Fast training (~15s) but F1 drops to 0.72 (under threshold)
- **Trap B:** Reduce only `max_iter` to 100 → Faster but model doesn't converge, F1 = 0.78
- **Trap C:** Reduce only `max_features` to 10000 → F1 drops to 0.81, training still takes ~70s

## Required Fix

The correct configuration that meets both constraints:

```python
TfidfVectorizer(max_features=50000, ngram_range=(1, 2))
LogisticRegression(C=1.0, max_iter=500, solver='lbfgs')
```

This achieves approximately:
- F1: ~0.87 (above threshold)
- Training time: ~25 seconds (well under limit)

Other valid combinations also exist — the grader checks the actual measured values.

## Evaluation

Run `python train_and_evaluate.py` — outputs F1 and training time:

```
Vectorizer: TfidfVectorizer(max_features=..., ngram_range=...)
Classifier: LogisticRegression(C=..., max_iter=...)
Training time: XX.X seconds
Validation F1: X.XXXX
PASS  (or FAIL)
```

**Pass conditions (both must be true):**
1. `validation_f1 >= 0.85`
2. `training_time_seconds <= 60`

## Files

| File | Purpose |
|------|---------|
| `classifier.py` | Hyperparameter config — modify this |
| `train_and_evaluate.py` | Timing + evaluation script — do not modify |
| `data/train.csv` | Training text data |
| `data/val.csv` | Validation data |
| `requirements.txt` | Python dependencies |

## Constraints

- Must use TF-IDF + Logistic Regression (do not switch models)
- Modify only `classifier.py`
- Do not modify `train_and_evaluate.py`
- Training must complete within a single process (no distributed training)
- Allowed hyperparameters to tune: `max_features`, `ngram_range`, `C`, `max_iter`, `solver`

## Grading

- Score 1.0: F1 ≥ 0.85 AND time ≤ 60s
- Score 0.5: F1 ≥ 0.85 but time > 60s (accurate but too slow)
- Score 0.25: F1 < 0.85 but time ≤ 60s (fast but inaccurate)
- Score 0.0: both constraints failed
