"""
Training and evaluation script for MLCONV-03.
Trains the model, evaluates precision and recall on the test set,
and prints whether the constraints are satisfied.

DO NOT MODIFY THIS FILE.
"""

import sys
import os
import pandas as pd
import numpy as np
from sklearn.metrics import precision_score, recall_score

PRECISION_THRESHOLD = 0.90
RECALL_THRESHOLD    = 0.65


def main():
    # Generate data if missing
    if (not os.path.exists("data/train.csv") or
            not os.path.exists("data/test.csv")):
        print("Data not found. Generating dataset...")
        from generate_data import generate_dataset
        os.makedirs("data", exist_ok=True)
        train_df, test_df = generate_dataset(seed=42)
        train_df.to_csv("data/train.csv", index=False)
        test_df.to_csv("data/test.csv", index=False)
        print("Dataset generated.")

    # Load data
    train_df = pd.read_csv("data/train.csv")
    test_df  = pd.read_csv("data/test.csv")

    feature_cols = [c for c in train_df.columns if c != "label"]
    X_train = train_df[feature_cols].values
    y_train = train_df["label"].values
    X_test  = test_df[feature_cols].values
    y_test  = test_df["label"].values

    print(f"Train: {len(X_train)} samples "
          f"({int(y_train.sum())} fraud, {y_train.mean():.1%} rate)")
    print(f"Test:  {len(X_test)} samples "
          f"({int(y_test.sum())} fraud, {y_test.mean():.1%} rate)")
    print()

    # Import classifier module
    from classifier import train, predict, THRESHOLD

    print(f"Threshold: {THRESHOLD}")
    print("Training...")

    clf = train(X_train, y_train)
    y_pred = predict(clf, X_test)

    precision = precision_score(y_test, y_pred, zero_division=0)
    recall    = recall_score(y_test, y_pred, zero_division=0)

    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    print()

    passes_precision = precision >= PRECISION_THRESHOLD
    passes_recall    = recall    >= RECALL_THRESHOLD

    if passes_precision and passes_recall:
        print(f"PASS  (precision {precision:.4f} >= {PRECISION_THRESHOLD}, "
              f"recall {recall:.4f} >= {RECALL_THRESHOLD})")
        sys.exit(0)
    else:
        reasons = []
        if not passes_precision:
            reasons.append(f"precision {precision:.4f} < {PRECISION_THRESHOLD}")
        if not passes_recall:
            reasons.append(f"recall {recall:.4f} < {RECALL_THRESHOLD}")
        print(f"FAIL  ({'; '.join(reasons)})")
        sys.exit(1)


if __name__ == "__main__":
    main()
