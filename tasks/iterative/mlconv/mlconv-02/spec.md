# MLCONV-02: Feature Leakage Detection

## Overview

This task is modeled on the **Kaggle Home Credit Default Risk** competition
(https://www.kaggle.com/c/home-credit-default-risk), where the `DAYS_EMPLOYED` anomaly
(sentinel value `-365243` for unemployed applicants) was a famous community finding about
hidden signals in feature data.

You are given a fraud detection model that achieves **0.99 AUC on the training set** but only **0.61 AUC on the held-out test set**. This large gap indicates a serious problem. Your task is to find and fix the data leakage, then engineer new features to achieve:

- **test_AUC ≥ 0.85**
- **(train_AUC - test_AUC) < 0.05** (gap must be small — no more overfitting)

## The Leakage

The feature `is_disputed` is included in the training data. This field is set by the bank **after** a transaction is reported as fraud — it is a post-hoc label, not information available at transaction time. In the training set, `is_disputed` is perfectly correlated with fraud. In the test set (real-world deployment), this field is not reliably set.

**Step 1:** Remove `is_disputed` from the feature set.

After removing it, AUC drops to approximately **0.70** — the model loses its cheat sheet.

## Required Fix

After removing the leakage, you must engineer **at least 3 new features** to recover AUC to ≥ 0.85:

### Suggested Features (implement these in `features.py`)

1. **`transaction_velocity`** — Number of transactions from the same `user_id` within the last hour (use `timestamp` column). High velocity is a fraud signal.

2. **`merchant_category_risk_score`** — Mean fraud rate per `merchant_category` computed on the training set. Map each transaction's category to its historical fraud rate.

3. **`amount_vs_avg_ratio`** — Transaction amount divided by the user's average transaction amount. Unusually large transactions relative to history are suspicious.

## Evaluation

Run `python evaluate.py` — outputs both train and test AUC:

```
Train AUC: X.XXXX
Test AUC:  X.XXXX
AUC Gap:   X.XXXX
PASS  (or FAIL)
```

**Pass conditions (both must be true):**
1. `test_AUC >= 0.85`
2. `(train_AUC - test_AUC) < 0.05`

## Files

| File | Purpose |
|------|---------|
| `model.py` | Feature pipeline + XGBoost model — modify this |
| `features.py` | Feature engineering utilities — implement here |
| `evaluate.py` | Evaluation script — do not modify |
| `data/train.csv` | Training data (contains leaky `is_disputed` feature) |
| `data/test.csv` | Held-out test data |
| `requirements.txt` | Python dependencies |

## Constraints

- Must remove `is_disputed` from all feature pipelines
- Must implement the 3 new features in `features.py`
- Model must be saved to `model.pkl`
- Do not modify `evaluate.py`
- Allowed libraries: scikit-learn, xgboost, pandas, numpy, joblib

## Column Reference

Training data columns (schema matches Home Credit competition's `application_train.csv` conventions):
- `transaction_id` — unique ID (analogous to `SK_ID_CURR`)
- `user_id` — anonymized user identifier
- `merchant_category` — category string (e.g., "electronics", "grocery")
- `amount` — transaction amount in USD (analogous to `AMT_CREDIT`)
- `timestamp` — Unix timestamp of transaction
- `days_employed` — employment duration in negative days; value `-365243` is a sentinel
  for unemployed applicants (exact convention from the Home Credit competition)
- `is_disputed` — **LEAKY FEATURE**: post-hoc dispute flag (remove this!)
- `feature_0` through `feature_4` — anonymized numeric features
- `label` — fraud label (0=legit, 1=fraud)

See `PROVENANCE.md` for full dataset origin and derivation notes.
