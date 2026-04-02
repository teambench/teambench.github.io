"""
Training and evaluation script for MLCONV-03.
Times the training, evaluates on validation set, checks both constraints.

DO NOT MODIFY THIS FILE.
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline

F1_THRESHOLD = 0.85
TIME_THRESHOLD = 60.0  # seconds


def main():
    # Generate data if missing
    if not os.path.exists("data/train.csv") or not os.path.exists("data/val.csv"):
        print("Data not found. Generating dataset...")
        from generate_data import generate_dataset
        os.makedirs("data", exist_ok=True)
        train_df, val_df = generate_dataset(seed=42)
        train_df.to_csv("data/train.csv", index=False)
        val_df.to_csv("data/val.csv", index=False)
        print("Dataset generated.")

    # Load data
    train_df = pd.read_csv("data/train.csv")
    val_df = pd.read_csv("data/val.csv")

    X_train = train_df["text"].values
    y_train = train_df["label"].values
    X_val = val_df["text"].values
    y_val = val_df["label"].values

    print(f"Train: {len(X_train)} samples")
    print(f"Val:   {len(X_val)} samples")

    # Import hyperparameter config
    from classifier import get_vectorizer, get_classifier

    vectorizer = get_vectorizer()
    clf = get_classifier()

    print(f"\nVectorizer: {vectorizer}")
    print(f"Classifier: {clf}")
    print()

    # Time the training
    print("Training...")
    t0 = time.perf_counter()

    vectorizer.fit(X_train)
    X_train_vec = vectorizer.transform(X_train)
    clf.fit(X_train_vec, y_train)

    training_time = time.perf_counter() - t0

    # Evaluate on validation set
    X_val_vec = vectorizer.transform(X_val)
    y_pred = clf.predict(X_val_vec)
    val_f1 = f1_score(y_val, y_pred, average='macro', zero_division=0)

    print(f"Training time: {training_time:.1f} seconds")
    print(f"Validation F1: {val_f1:.4f}")
    print()

    passes_f1 = val_f1 >= F1_THRESHOLD
    passes_time = training_time <= TIME_THRESHOLD

    if passes_f1 and passes_time:
        print(f"PASS  (F1 {val_f1:.4f} >= {F1_THRESHOLD}, "
              f"time {training_time:.1f}s <= {TIME_THRESHOLD}s)")
        sys.exit(0)
    else:
        reasons = []
        if not passes_f1:
            reasons.append(f"F1 {val_f1:.4f} < {F1_THRESHOLD}")
        if not passes_time:
            reasons.append(f"training_time {training_time:.1f}s > {TIME_THRESHOLD}s")
        print(f"FAIL  ({'; '.join(reasons)})")
        sys.exit(1)


if __name__ == "__main__":
    main()
