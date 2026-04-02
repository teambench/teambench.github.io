"""
Generator for MLCONV-01: Class Imbalance Discovery.

Parameterizes dataset surface details from a seed so each benchmark run
can have slightly different data characteristics while preserving the
core challenge (class imbalance).

Usage:
    python generator.py --seed 42
    python generator.py --seed 123 --fraud-rate 0.003 --n-features 12
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd


def generate(seed: int, fraud_rate: float = 0.002, n_features: int = 10,
             n_train: int = 5000, n_test: int = 1000,
             f1_threshold: float = 0.80):
    """
    Generate a parameterized fraud detection dataset and update config values.

    Args:
        seed: Random seed for reproducibility
        fraud_rate: Fraction of positive (fraud) samples (default 0.2%)
        n_features: Number of feature columns
        n_train: Number of training samples
        n_test: Number of test samples
        f1_threshold: Target macro-F1 threshold for grading
    """
    rng = np.random.RandomState(seed)

    def make_split(n, fraud_rate, rng, n_features):
        n_fraud = max(2, int(n * fraud_rate))
        n_legit = n - n_fraud

        # Legitimate transactions
        X_legit = rng.randn(n_legit, n_features)
        y_legit = np.zeros(n_legit, dtype=int)

        # Fraudulent transactions — shifted and scaled
        fraud_shift = rng.uniform(1.5, 2.5)
        fraud_scale = rng.uniform(1.2, 1.8)
        X_fraud = rng.randn(n_fraud, n_features) * fraud_scale + fraud_shift
        y_fraud = np.ones(n_fraud, dtype=int)

        X = np.vstack([X_legit, X_fraud])
        y = np.concatenate([y_legit, y_fraud])

        idx = rng.permutation(len(y))
        X, y = X[idx], y[idx]

        cols = {f"feature_{i}": X[:, i] for i in range(n_features)}
        cols["label"] = y
        return pd.DataFrame(cols)

    os.makedirs("workspace/data", exist_ok=True)

    train_df = make_split(n_train, fraud_rate, rng, n_features)
    test_df = make_split(n_test, fraud_rate, rng, n_features)

    train_df.to_csv("workspace/data/train.csv", index=False)
    test_df.to_csv("workspace/data/test.csv", index=False)

    # Update evaluate.py threshold if different from default
    if f1_threshold != 0.80:
        _update_threshold("workspace/evaluate.py", f1_threshold)

    # Update pipeline.py feature columns if n_features changed
    if n_features != 10:
        _update_feature_count("workspace/pipeline.py", n_features)
        _update_feature_count("workspace/evaluate.py", n_features)

    # Print summary
    fraud_count_train = train_df["label"].sum()
    fraud_count_test = test_df["label"].sum()

    print(f"Seed: {seed}")
    print(f"Fraud rate: {fraud_rate*100:.3f}%")
    print(f"Features: {n_features}")
    print(f"Train: {n_train} samples ({fraud_count_train} fraud, "
          f"{fraud_count_train/n_train*100:.2f}%)")
    print(f"Test:  {n_test} samples ({fraud_count_test} fraud, "
          f"{fraud_count_test/n_test*100:.2f}%)")
    print(f"F1 threshold: {f1_threshold}")
    print("Files written: workspace/data/train.csv, workspace/data/test.csv")


def _update_threshold(filepath: str, new_threshold: float):
    """Update the THRESHOLD constant in a Python file."""
    if not os.path.exists(filepath):
        return
    with open(filepath) as f:
        content = f.read()
    import re
    content = re.sub(r'THRESHOLD\s*=\s*[\d.]+',
                     f'THRESHOLD = {new_threshold}', content)
    with open(filepath, 'w') as f:
        f.write(content)


def _update_feature_count(filepath: str, n_features: int):
    """Update feature column range in a Python file."""
    if not os.path.exists(filepath):
        return
    with open(filepath) as f:
        content = f.read()
    import re
    content = re.sub(r'range\(10\)', f'range({n_features})', content)
    with open(filepath, 'w') as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Generate MLCONV-01 dataset")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed (default: 42)")
    parser.add_argument("--fraud-rate", type=float, default=0.002,
                        help="Fraction of fraud samples (default: 0.002)")
    parser.add_argument("--n-features", type=int, default=10,
                        help="Number of feature columns (default: 10)")
    parser.add_argument("--n-train", type=int, default=5000,
                        help="Training set size (default: 5000)")
    parser.add_argument("--n-test", type=int, default=1000,
                        help="Test set size (default: 1000)")
    parser.add_argument("--threshold", type=float, default=0.80,
                        help="Macro-F1 threshold (default: 0.80)")
    args = parser.parse_args()

    generate(
        seed=args.seed,
        fraud_rate=args.fraud_rate,
        n_features=args.n_features,
        n_train=args.n_train,
        n_test=args.n_test,
        f1_threshold=args.threshold,
    )


if __name__ == "__main__":
    main()
