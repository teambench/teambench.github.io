# MLCONV-03: Speed Up the Text Classifier

## Your Task

The sentiment classifier in `classifier.py` is too slow for production. Tune the hyperparameters so it meets **both** constraints:

- **Validation F1 ≥ 0.85**
- **Training time ≤ 60 seconds**

## Files to Work With

- `classifier.py` — hyperparameters are defined here (modify this)
- `train_and_evaluate.py` — run this to check F1 and training time
- `data/train.csv`, `data/val.csv` — text data

## Quick Start

```bash
pip install -r requirements.txt
python train_and_evaluate.py    # check current F1 and time
```

## Current Behavior

```
Training time: ~180.0 seconds
Validation F1: 0.9100
FAIL  (training_time 180.0 > 60)
```

## Target

```
Training time: <= 60 seconds
Validation F1: >= 0.85
PASS
```

## Constraints

- Keep TF-IDF + Logistic Regression (don't switch model families)
- Only modify `classifier.py`
- Do not modify `train_and_evaluate.py`
