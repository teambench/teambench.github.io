# PROVENANCE — MLCONV-01: Class Imbalance Discovery

## Real-World Origin

This benchmark task is derived from the **ULB Machine Learning Group Credit Card Fraud
Detection** dataset, one of the most widely studied imbalanced classification benchmarks
in applied ML research.

### Dataset Reference

- **Kaggle page:** https://www.kaggle.com/mlg-ulb/creditcardfraud
- **License:** CC BY-SA 4.0
- **Original contributors:** Worldline and the Machine Learning Group of ULB (Université
  Libre de Bruxelles)

### Primary Citation

> Andrea Dal Pozzolo, Olivier Caelen, Reid A. Johnson and Gianluca Bontempi.
> *Calibrating Probability with Undersampling for Unbalanced Classification.*
> In Symposium on Computational Intelligence and Data Mining (CIDM), IEEE, 2015.

### Dataset Characteristics (from the paper)

| Property | Value |
|----------|-------|
| Transactions | 284,807 over 2 days |
| Fraudulent | 492 (0.172%) |
| Features | V1–V28 (PCA), Time, Amount |
| Cardholders | European, September 2013 |

## How This Benchmark Was Derived

1. **Core insight preserved:** The 0.172% fraud rate makes accuracy a misleading metric —
   a classifier that always predicts "legitimate" achieves 99.83% accuracy while being
   completely useless at catching fraud. This is the central learning objective.

2. **Feature reduction:** The real dataset has 28 PCA features plus Time and Amount. The
   benchmark uses 10 features (feature_0–feature_9, derived from V1–V10) to keep training
   fast for the benchmark environment, while preserving the distributional separation
   between fraud and legitimate classes.

3. **Sample size:** Reduced from 284,807 to 5,000 train / 1,000 test for fast iteration
   in a benchmark setting (target: < 30 seconds per training run).

4. **Fraud rate:** Kept at ~0.172% to match the real dataset's imbalance ratio, which is
   the key property that makes `class_weight='balanced'` + SMOTE necessary.

5. **Synthetic generation:** Because the Kaggle dataset requires license acceptance, the
   workspace uses `workspace/data/generate_sample.py`, which generates a statistically
   faithful synthetic sample using published statistics from the Dal Pozzolo et al. paper.

## Why This Dataset Was Chosen

The Credit Card Fraud dataset is the canonical benchmark for class imbalance in binary
classification. Its properties make it ideal for testing whether an agent understands
that high accuracy does not imply good model performance when classes are severely
imbalanced — a real and common pitfall in production ML systems.

The SMOTE + class_weight fix required by this task is the standard industry approach
documented in the `imbalanced-learn` library, which itself cites this dataset extensively
in its documentation and papers.
