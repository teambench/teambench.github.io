"""
Generate synthetic fraud detection dataset for MLCONV-03.

Design:
- 5000 samples, ~8.8% fraud rate (class imbalance mirrors real fraud datasets)
- 12 numeric features (7 informative, 3 redundant, 2 noise)
- Controlled class overlap: RF at default threshold=0.5 achieves
  precision~0.97 but recall~0.61 (too many fraud cases missed)
- Lowering threshold to 0.30 recovers recall~0.71 but precision drops to ~0.82
- CalibratedClassifierCV(isotonic) + threshold=0.35 achieves both:
  precision~0.90, recall~0.68 (both above target thresholds)

Dataset is fully deterministic (seeded).
"""

import numpy as np
import pandas as pd
import os
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split


def generate_dataset(seed: int = 42):
    """
    Generate train/test splits for the fraud detection task.

    Returns (train_df, test_df) where each DataFrame has columns:
      feature_0 .. feature_11  -- numeric features
      label                    -- 0=legit, 1=fraud
    """
    X, y = make_classification(
        n_samples=5000,
        n_features=12,
        n_informative=7,
        n_redundant=3,
        n_clusters_per_class=2,
        flip_y=0.02,
        weights=[0.92, 0.08],
        random_state=seed,
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=seed, stratify=y
    )

    feature_cols = [f"feature_{i}" for i in range(X.shape[1])]
    train_df = pd.DataFrame(X_train, columns=feature_cols)
    train_df["label"] = y_train.astype(int)

    test_df = pd.DataFrame(X_test, columns=feature_cols)
    test_df["label"] = y_test.astype(int)

    return train_df, test_df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    train_df, test_df = generate_dataset(seed=42)
    train_df.to_csv("data/train.csv", index=False)
    test_df.to_csv("data/test.csv", index=False)
    n_fraud_train = int(train_df["label"].sum())
    n_fraud_test  = int(test_df["label"].sum())
    print(f"Train: {len(train_df)} samples ({n_fraud_train} fraud, "
          f"{n_fraud_train/len(train_df):.1%} rate)")
    print(f"Test:  {len(test_df)} samples ({n_fraud_test} fraud, "
          f"{n_fraud_test/len(test_df):.1%} rate)")
    print("Saved to data/train.csv and data/test.csv")
