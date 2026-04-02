# MLCONV-02: Feature Leakage Detection

## Description

A multi-turn benchmark task testing whether an agent can detect data leakage, remove the leaky feature, and then recover model performance through feature engineering.

The agent is given a fraud detection model with a 0.99 train AUC but only 0.61 test AUC — a classic overfitting signature caused by leakage. The `is_disputed` column is perfectly correlated with the label in training (set retroactively after fraud is confirmed) but not in the test set (simulating real deployment conditions).

Modeled on the **Kaggle Home Credit Default Risk** competition (2018):
https://www.kaggle.com/c/home-credit-default-risk — where the `DAYS_EMPLOYED` sentinel
value anomaly (`-365243` for unemployed applicants) was a famous community leakage finding.
The data schema mirrors the competition's column conventions (`SK_ID_CURR`, `AMT_CREDIT`,
`DAYS_EMPLOYED`). See `PROVENANCE.md` for full derivation notes.

## Why This Requires Multiple Turns

**Turn 1 failure modes:**
- Agent removes `is_disputed`, AUC drops to ~0.70, declares "leakage fixed" without checking the 0.85 threshold
- Agent removes `is_disputed` and implements stub feature engineering, AUC improves slightly but not to threshold
- Agent doesn't find the leakage at all, leaves model unchanged

**Turn 2 (after Verifier feedback):** Verifier's attestation.json shows test_AUC < 0.85. Agent must implement the three feature engineering functions in `features.py`:
1. `compute_transaction_velocity` — rolling count of user transactions per hour
2. `compute_merchant_category_risk` — per-category historical fraud rate
3. `compute_amount_vs_avg_ratio` — transaction amount vs user's average

## Files

| File | Role |
|------|------|
| `spec.md` | Full specification (Planner reads this) |
| `brief.md` | Short summary (Executor reads this) |
| `workspace/model.py` | Buggy model with leaky feature — agent modifies |
| `workspace/features.py` | Feature engineering stubs — agent implements |
| `workspace/evaluate.py` | Evaluation script — read-only |
| `workspace/generate_data.py` | Data generator |
| `workspace/requirements.txt` | Python dependencies |
| `grader.sh` | Automated grader — outputs 0.0 to 1.0 |
| `generator.py` | Parameterizes seed, fraud rate, n_users |

## Expected Scores by Agent Type

| Agent Type | Expected Score | Reason |
|------------|---------------|--------|
| Oracle | 0.40 | May remove leakage but skip full feature engineering |
| Single-pass | 0.50 | Removes leakage, partial feature engineering |
| Multi-turn | 1.0 | Verifier feedback triggers complete feature engineering |

## Grading

Run `bash grader.sh` from the task root directory.

- Score 1.0: test_AUC ≥ 0.85 AND gap < 0.05
- Score 0.5: leakage removed, AUC improving but below threshold
- Score 0.3: AUC threshold met but gap still large (still leaking)
- Score 0.0: model not trained or evaluate.py errors

## Stopping Condition

Score = 1.0 when `python evaluate.py` outputs both `Test AUC >= 0.85` and `AUC Gap < 0.05`, printing `PASS`.

## Setup

```bash
cd workspace
pip install -r requirements.txt
python model.py       # generates data + trains baseline (leaky) model
python evaluate.py    # shows train/test AUC and gap
```

## The Fix (Reference Solution)

```python
# In features.py — implement transaction_velocity:
def compute_transaction_velocity(df, reference_df=None, window_seconds=3600):
    result = []
    df_sorted = df.sort_values("timestamp")
    for _, row in df_sorted.iterrows():
        user_txns = df_sorted[
            (df_sorted["user_id"] == row["user_id"]) &
            (df_sorted["timestamp"] < row["timestamp"]) &
            (df_sorted["timestamp"] >= row["timestamp"] - window_seconds)
        ]
        result.append(len(user_txns))
    return pd.Series(result, index=df_sorted.index, name="transaction_velocity").reindex(df.index)

# In model.py — remove is_disputed, add engineered features:
from features import add_engineered_features
train_df = add_engineered_features(train_df)
FEATURE_COLS = ["amount", "feature_0", ..., "transaction_velocity",
                "merchant_category_risk_score", "amount_vs_avg_ratio"]
```

## Parameterization

```bash
python generator.py --seed 42                          # default
python generator.py --seed 99 --fraud-rate 0.08        # higher fraud rate
python generator.py --seed 7 --n-users 500             # more users (harder velocity)
```
