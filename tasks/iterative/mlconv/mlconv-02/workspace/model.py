"""
Fraud Detection Model — MLCONV-02
===================================
XGBoost classifier for fraud detection.

PROBLEM: This model includes 'is_disputed' as a feature.
is_disputed is set AFTER fraud is confirmed (post-hoc label) — it's not
available at prediction time. This causes massive train/test AUC gap.

Steps to fix:
1. Remove 'is_disputed' from FEATURE_COLS
2. Implement feature engineering in features.py
3. Add engineered features to the pipeline
"""

import os
import pandas as pd
import numpy as np
import joblib

from xgboost import XGBClassifier
from sklearn.metrics import roc_auc_score

# Generate data if missing
if not os.path.exists("data/train.csv"):
    print("Data not found. Generating dataset...")
    from generate_data import generate_dataset
    os.makedirs("data", exist_ok=True)
    train_df, test_df = generate_dataset(seed=42)
    train_df.to_csv("data/train.csv", index=False)
    test_df.to_csv("data/test.csv", index=False)
    print("Dataset generated.")

# Load data
train_df = pd.read_csv("data/train.csv")

# Feature columns — BUG: 'is_disputed' is a leaky feature!
# It is perfectly correlated with the label in training data
# but not available at prediction time (it's set post-hoc).
FEATURE_COLS = [
    "is_disputed",      # <-- REMOVE THIS (leakage!)
    "amount",
    "feature_0",
    "feature_1",
    "feature_2",
    "feature_3",
    "feature_4",
]
TARGET_COL = "label"

X_train = train_df[FEATURE_COLS].values
y_train = train_df[TARGET_COL].values

print(f"Training set: {len(X_train)} samples")
print(f"  Fraud: {y_train.sum()} ({y_train.mean()*100:.2f}%)")
print(f"  Features: {FEATURE_COLS}")

# Train XGBoost classifier
clf = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    random_state=42,
    eval_metric="auc",
    verbosity=0,
)

print("\nTraining model...")
clf.fit(X_train, y_train)

# Training AUC
y_prob_train = clf.predict_proba(X_train)[:, 1]
train_auc = roc_auc_score(y_train, y_prob_train)
print(f"Train AUC: {train_auc:.4f}")

# Save model and feature list
joblib.dump({"model": clf, "feature_cols": FEATURE_COLS}, "model.pkl")
print("\nModel saved to model.pkl")
print("Run 'python evaluate.py' to see train and test AUC.")
