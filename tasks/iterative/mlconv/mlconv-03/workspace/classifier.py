"""
Fraud Detection Classifier -- MLCONV-03
========================================
Trains a RandomForest on the fraud dataset and predicts using a fixed
probability threshold.

PROBLEM: The current threshold=0.5 is too conservative.
  precision=0.97  (good -- few false alarms)
  recall=0.61     (BAD  -- misses ~39% of real fraud cases)

Hard constraints:
  precision >= 0.90  AND  recall >= 0.65

Modify this file to satisfy both constraints simultaneously.

TRAPS to avoid:
- Only lowering threshold to 0.30: recall=0.71 but precision drops to 0.82
  (precision below target)
- Only adding calibration without adjusting threshold: precision stays high
  but recall barely improves
- Setting threshold too low (< 0.25): recall improves but precision collapses

Hint: combine CalibratedClassifierCV(method='isotonic') with threshold=0.35.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV


# ── Threshold for converting predicted probabilities to labels ──────────────
# Baseline: 0.5  →  precision=0.97, recall=0.61  (recall too low -- FAILS)
# Fix:      0.35 with calibration  →  both constraints satisfied
THRESHOLD = 0.5


def get_classifier():
    """
    Return an untrained classifier object.
    The returned object must implement fit(X, y) and predict_proba(X).
    """
    return RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        n_jobs=1,
    )


def train(X_train, y_train):
    """
    Train the classifier and return the fitted model.
    Modify this function to add probability calibration if needed.
    """
    clf = get_classifier()
    clf.fit(X_train, y_train)
    return clf


def predict(clf, X):
    """
    Predict binary labels using THRESHOLD applied to predicted probabilities.
    Returns array of 0/1 predictions.
    """
    proba = clf.predict_proba(X)[:, 1]
    return (proba >= THRESHOLD).astype(int)
