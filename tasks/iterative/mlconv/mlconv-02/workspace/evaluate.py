"""
Evaluation script for MLCONV-02.
Loads model.pkl and evaluates on both train and test sets.

DO NOT MODIFY THIS FILE.
"""

import sys
import os
import pandas as pd
import numpy as np
import joblib

from sklearn.metrics import roc_auc_score

AUC_THRESHOLD = 0.85
GAP_THRESHOLD = 0.05


def main():
    if not os.path.exists("model.pkl"):
        print("ERROR: model.pkl not found. Run 'python model.py' first.")
        sys.exit(1)

    if not os.path.exists("data/train.csv") or not os.path.exists("data/test.csv"):
        print("ERROR: data files not found. Run 'python model.py' first.")
        sys.exit(1)

    # Load model bundle
    bundle = joblib.load("model.pkl")
    clf = bundle["model"]
    feature_cols = bundle["feature_cols"]

    # Load data
    train_df = pd.read_csv("data/train.csv")
    test_df = pd.read_csv("data/test.csv")

    # Validate feature columns exist
    missing_train = [c for c in feature_cols if c not in train_df.columns]
    missing_test = [c for c in feature_cols if c not in test_df.columns]
    if missing_train or missing_test:
        print(f"ERROR: Missing columns in train: {missing_train}, test: {missing_test}")
        sys.exit(1)

    X_train = train_df[feature_cols].values
    y_train = train_df["label"].values
    X_test = test_df[feature_cols].values
    y_test = test_df["label"].values

    # Predict probabilities
    y_prob_train = clf.predict_proba(X_train)[:, 1]
    y_prob_test = clf.predict_proba(X_test)[:, 1]

    # Compute AUC
    train_auc = roc_auc_score(y_train, y_prob_train)
    test_auc = roc_auc_score(y_test, y_prob_test)
    gap = train_auc - test_auc

    print(f"Features used: {feature_cols}")
    print(f"Train set: {len(y_train)} samples ({y_train.sum()} fraud)")
    print(f"Test set:  {len(y_test)} samples ({y_test.sum()} fraud)")
    print()
    print(f"Train AUC: {train_auc:.4f}")
    print(f"Test AUC:  {test_auc:.4f}")
    print(f"AUC Gap:   {gap:.4f}")
    print()

    passes_auc = test_auc >= AUC_THRESHOLD
    passes_gap = gap < GAP_THRESHOLD

    if passes_auc and passes_gap:
        print(f"PASS  (test_AUC {test_auc:.4f} >= {AUC_THRESHOLD}, "
              f"gap {gap:.4f} < {GAP_THRESHOLD})")
        sys.exit(0)
    else:
        reasons = []
        if not passes_auc:
            reasons.append(f"test_AUC {test_auc:.4f} < {AUC_THRESHOLD}")
        if not passes_gap:
            reasons.append(f"gap {gap:.4f} >= {GAP_THRESHOLD}")
        print(f"FAIL  ({'; '.join(reasons)})")
        sys.exit(1)


if __name__ == "__main__":
    main()
