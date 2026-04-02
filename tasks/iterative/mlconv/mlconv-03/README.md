# MLCONV-03: Hyperparameter Sensitivity Tradeoff

## Description

A multi-turn benchmark task testing whether an agent can navigate competing constraints in hyperparameter tuning — specifically, satisfying both an accuracy threshold and a training time budget simultaneously.

The agent must tune a TF-IDF + Logistic Regression sentiment classifier. The current config (max_features=100000, C=10.0, max_iter=1000) achieves 0.91 F1 but takes ~180 seconds. The agent must find a configuration that achieves F1 ≥ 0.85 in ≤ 60 seconds.

Derived from the **Stanford AI Lab Large Movie Review Dataset** (IMDb, Maas et al., 2011):
https://ai.stanford.edu/~amaas/data/sentiment/ — the canonical TF-IDF + LR benchmark
(25,000 train reviews, ~0.88 F1 with max_features=50000, C=1.0 per scikit-learn docs).
The workspace uses a 2,000-sample subset matching the real dataset's vocabulary distribution.
See `PROVENANCE.md` for full dataset origin and derivation notes.

**Citation:** Maas et al., *Learning Word Vectors for Sentiment Analysis*, ACL 2011.

## Why This Requires Multiple Turns

**Turn 1 failure modes:**

The task has well-defined traps that catch naive single-pass optimization:

| What agent tries | Result | Why it fails |
|-----------------|--------|--------------|
| Only reduce C=0.1 | ~15s, F1=0.72 | Regularization too strong, loses accuracy |
| Only reduce max_iter=100 | ~30s, F1=0.78 | Model doesn't converge |
| Only reduce max_features=10000 | ~70s, F1=0.81 | Still slow AND F1 below threshold |
| Reduce max_features=50000 only | ~50s, F1=0.84 | Just misses F1 threshold |

Each single-parameter fix fails at least one constraint.

**Turn 2 (after Verifier feedback):** Verifier's attestation shows which constraint failed. Agent learns to tune both `max_features` AND `C` together to find the sweet spot (50000 features + C=1.0 gives F1=0.87 in ~25s).

## Files

| File | Role |
|------|------|
| `spec.md` | Full specification (Planner reads this) |
| `brief.md` | Short summary (Executor reads this) |
| `workspace/classifier.py` | Hyperparameter config — agent modifies this |
| `workspace/train_and_evaluate.py` | Timing + evaluation — read-only |
| `workspace/generate_data.py` | Data generator |
| `workspace/requirements.txt` | Python dependencies |
| `grader.sh` | Automated grader — outputs 0.0 to 1.0 |
| `generator.py` | Parameterizes seed, n_train, thresholds |

## Expected Scores by Agent Type

| Agent Type | Expected Score | Reason |
|------------|---------------|--------|
| Oracle | 0.50 | Likely tries one parameter at a time, hits one constraint |
| Single-pass | 0.60 | May get F1 right but miss time constraint |
| Multi-turn | 1.0 | Verifier feedback reveals which constraint failed |

## Grading

Run `bash grader.sh` from the task root directory.

- Score 1.0: F1 ≥ 0.85 AND time ≤ 60s
- Score 0.5: F1 ≥ 0.85 but time > 60s (accurate but slow)
- Score 0.25: F1 < 0.85 but time ≤ 60s (fast but inaccurate)
- Score 0.0: both constraints failed

## Stopping Condition

Score = 1.0 when `python train_and_evaluate.py` outputs both constraints satisfied, printing `PASS`.

## Setup

```bash
cd workspace
pip install -r requirements.txt
python train_and_evaluate.py    # check current state (~180s, slow!)
```

## The Fix (Reference Solution)

Edit `classifier.py`:

```python
def get_vectorizer():
    return TfidfVectorizer(
        max_features=50000,    # reduced from 100000
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        ...
    )

def get_classifier():
    return LogisticRegression(
        C=1.0,          # reduced from 10.0
        max_iter=500,   # reduced from 1000
        solver='lbfgs',
        random_state=42,
        n_jobs=1,
    )
```

Expected result: ~0.87 F1, ~25 seconds.

## Parameterization

```bash
python generator.py --seed 42                            # default
python generator.py --seed 99 --n-train 6000            # larger dataset (harder timing)
python generator.py --seed 7 --f1-threshold 0.83        # easier F1 target
python generator.py --seed 42 --time-threshold 45       # stricter time budget
```
