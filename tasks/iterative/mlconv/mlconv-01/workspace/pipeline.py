"""
Credit Card Fraud Detection Pipeline
=====================================
Trains a RandomForestClassifier on imbalanced fraud data.

PROBLEM: This pipeline ignores class imbalance.
The model achieves ~99.8% accuracy but terrible macro-F1
because it learns to always predict the majority class (legitimate).

TODO: Fix the class imbalance problem.
Hint: Look into class_weight parameter and oversampling techniques.
"""

import pandas as pd
import numpy as np
import joblib
import os

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score

# Generate data if missing
if not os.path.exists("data/train.csv"):
    print("Data not found. Generating dataset...")
    from generate_data import generate_fraud_dataset
    os.makedirs("data", exist_ok=True)
    train_df, test_df = generate_fraud_dataset(seed=42)
    train_df.to_csv("data/train.csv", index=False)
    test_df.to_csv("data/test.csv", index=False)
    print("Dataset generated.")

# Load training data
train_df = pd.read_csv("data/train.csv")

FEATURE_COLS = [f"feature_{i}" for i in range(10)]
TARGET_COL = "label"

X_train = train_df[FEATURE_COLS].values
y_train = train_df[TARGET_COL].values

print(f"Training set: {len(X_train)} samples")
print(f"  Positive (fraud): {y_train.sum()} ({y_train.mean()*100:.2f}%)")
print(f"  Negative (legit): {(y_train==0).sum()} ({(y_train==0).mean()*100:.2f}%)")

# Train classifier — no class imbalance handling (BUG: this is the problem)
clf = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
    # Missing: class_weight='balanced'
)

print("\nTraining model...")
clf.fit(X_train, y_train)

# Quick sanity check on training set
y_pred_train = clf.predict(X_train)
train_acc = accuracy_score(y_train, y_pred_train)
train_f1 = f1_score(y_train, y_pred_train, average='macro')
print(f"Train Accuracy: {train_acc:.4f}")
print(f"Train Macro-F1: {train_f1:.4f}")

# Save model
joblib.dump(clf, "model.pkl")
print("\nModel saved to model.pkl")
print("Run 'python evaluate.py' to evaluate on the test set.")
