# MLCONV-01: Fix the Fraud Detection Pipeline

## Your Task

The fraud detection model in `pipeline.py` has poor performance on minority class (fraud) detection. Fix it to achieve **macro-F1 ≥ 0.80** on the test set.

## Files to Work With

- `pipeline.py` — the training script (modify this)
- `evaluate.py` — evaluation script (run this to check your score)
- `data/train.csv`, `data/test.csv` — dataset files
- `requirements.txt` — install dependencies first

## Quick Start

```bash
pip install -r requirements.txt
python pipeline.py       # train the model
python evaluate.py       # check macro-F1 score
```

## Current Behavior

Running `python evaluate.py` currently shows something like:
```
Accuracy: 0.9980
Macro-F1: 0.4100
FAIL
```

## Target

```
Macro-F1: >= 0.80
PASS
```

## Hint

Look at the class distribution in `data/train.csv` — check the `label` column.
