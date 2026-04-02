"""
Evaluation script for MLCONV-01.
Loads the trained model from model.pkl and evaluates on data/test.csv.

DO NOT MODIFY THIS FILE.
"""

import sys
import os
import pandas as pd
import numpy as np
import joblib

from sklearn.metrics import accuracy_score, f1_score, classification_report

THRESHOLD = 0.80
FEATURE_COLS = [f"feature_{i}" for i in range(10)]
TARGET_COL = "label"


def main():
    # Check model exists
    if not os.path.exists("model.pkl"):
        print("ERROR: model.pkl not found. Run 'python pipeline.py' first.")
        sys.exit(1)

    # Check test data exists
    if not os.path.exists("data/test.csv"):
        print("ERROR: data/test.csv not found. Run 'python pipeline.py' first.")
        sys.exit(1)

    # Load model
    clf = joblib.load("model.pkl")

    # Load test data
    test_df = pd.read_csv("data/test.csv")
    X_test = test_df[FEATURE_COLS].values
    y_test = test_df[TARGET_COL].values

    # Predict
    y_pred = clf.predict(X_test)

    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)

    print(f"Test set: {len(y_test)} samples")
    print(f"  Positive (fraud): {y_test.sum()}")
    print(f"  Negative (legit): {(y_test==0).sum()}")
    print()
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro-F1: {macro_f1:.4f}")
    print()
    print("Per-class report:")
    print(classification_report(y_test, y_pred, target_names=["legit", "fraud"],
                                zero_division=0))

    if macro_f1 >= THRESHOLD:
        print(f"PASS  (Macro-F1 {macro_f1:.4f} >= {THRESHOLD})")
        sys.exit(0)
    else:
        print(f"FAIL  (Macro-F1 {macro_f1:.4f} < {THRESHOLD})")
        sys.exit(1)


if __name__ == "__main__":
    main()
