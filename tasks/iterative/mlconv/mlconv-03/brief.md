# MLCONV-03: Fix the Fraud Detector's Recall

## Your Task

The fraud detection classifier in `classifier.py` is too conservative. It flags fraud
with high precision but misses too many real fraud cases. Tune it so it meets **both**
constraints simultaneously:

- **Precision >= 0.90**
- **Recall >= 0.65**

## Files to Work With

- `classifier.py` — model training and threshold config (modify this)
- `train_and_evaluate.py` — run this to check precision and recall
- `data/train.csv`, `data/test.csv` — numeric fraud features

## Quick Start

```bash
pip install -r requirements.txt
python train_and_evaluate.py    # check current precision and recall
```

## Current Behavior

```
Threshold: 0.5
Precision: 0.9710
Recall:    0.6091
FAIL  (recall 0.6091 < 0.65)
```

## Target

```
Precision: >= 0.90
Recall:    >= 0.65
PASS
```

## Constraints

- Keep RandomForest (do not switch model families)
- Modify only `classifier.py`
- Do not modify `train_and_evaluate.py`
