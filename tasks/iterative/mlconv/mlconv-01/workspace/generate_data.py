"""
Generate synthetic credit card fraud dataset.
Run once to create data/train.csv and data/test.csv.
This is called automatically by pipeline.py if data files are missing.
"""

import numpy as np
import pandas as pd
import os

def generate_fraud_dataset(seed=42, n_train=10000, n_test=5000,
                           fraud_rate=0.002, n_features=10):
    """
    Generate a synthetic imbalanced fraud dataset.
    Fraud rate ~0.2% by default (realistic credit card fraud).
    """
    rng = np.random.RandomState(seed)

    def make_split(n, fraud_rate, rng):
        n_fraud = max(2, int(n * fraud_rate))
        n_legit = n - n_fraud

        # Legitimate transactions: centered around 0
        X_legit = rng.randn(n_legit, n_features)
        y_legit = np.zeros(n_legit, dtype=int)

        # Fraudulent transactions: shifted mean, different variance
        X_fraud = rng.randn(n_fraud, n_features) * 1.5 + 2.0
        y_fraud = np.ones(n_fraud, dtype=int)

        X = np.vstack([X_legit, X_fraud])
        y = np.concatenate([y_legit, y_fraud])

        # Shuffle
        idx = rng.permutation(len(y))
        X, y = X[idx], y[idx]

        cols = {f"feature_{i}": X[:, i] for i in range(n_features)}
        cols["label"] = y
        return pd.DataFrame(cols)

    train_df = make_split(n_train, fraud_rate, rng)
    test_df = make_split(n_test, fraud_rate, rng)

    return train_df, test_df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    train_df, test_df = generate_fraud_dataset(seed=42)
    train_df.to_csv("data/train.csv", index=False)
    test_df.to_csv("data/test.csv", index=False)

    print(f"Train set: {len(train_df)} rows")
    print(f"  Fraud: {train_df['label'].sum()} ({train_df['label'].mean()*100:.2f}%)")
    print(f"  Legit: {(train_df['label']==0).sum()}")
    print(f"Test set: {len(test_df)} rows")
    print(f"  Fraud: {test_df['label'].sum()} ({test_df['label'].mean()*100:.2f}%)")
    print("Data saved to data/train.csv and data/test.csv")
