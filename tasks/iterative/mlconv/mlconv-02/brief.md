# MLCONV-02: Fix the Leaky Fraud Model

## Your Task

The fraud model achieves 0.99 AUC in training but only 0.61 AUC on the test set. Find and fix the problem so both conditions are met:

- `test_AUC >= 0.85`
- `(train_AUC - test_AUC) < 0.05`

## Files to Work With

- `model.py` — feature pipeline + XGBoost model (modify this)
- `features.py` — feature engineering utilities (implement here)
- `evaluate.py` — run this to check your AUC scores
- `data/train.csv`, `data/test.csv` — dataset

## Quick Start

```bash
pip install -r requirements.txt
python model.py        # train the model
python evaluate.py     # check AUC scores
```

## Current Behavior

```
Train AUC: 0.9900
Test AUC:  0.6100
AUC Gap:   0.3800
FAIL
```

## Target

```
Train AUC: ~0.88
Test AUC:  >= 0.85
AUC Gap:   < 0.05
PASS
```

## Hint

Look carefully at the feature columns in `data/train.csv`. Is every feature truly available at prediction time? Think about when each field would be populated in a real fraud detection system.
