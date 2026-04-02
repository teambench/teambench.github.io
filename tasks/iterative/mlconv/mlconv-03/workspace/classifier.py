"""
Text Classifier Configuration — MLCONV-03
==========================================
Defines the TF-IDF vectorizer and Logistic Regression hyperparameters.

PROBLEM: Current configuration achieves 0.91 F1 but takes ~180 seconds.
Hard constraint: training time MUST be <= 60 seconds AND F1 >= 0.85.

Modify the hyperparameters below to satisfy both constraints simultaneously.

TRAPS to avoid:
- Only reducing C (e.g., C=0.1) makes training fast but F1 drops to ~0.72
- Only reducing max_iter (e.g., 100) causes non-convergence, F1 ~0.78
- Only reducing max_features to 10000 drops F1 to ~0.81, still slow (~70s)

Hint: You need to tune BOTH the vectorizer AND the classifier together.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def get_vectorizer():
    """
    Return the TF-IDF vectorizer.
    Current config: max_features=100000, ngram_range=(1,2) — too slow!
    """
    return TfidfVectorizer(
        max_features=100000,   # TOO HIGH — causes slow training
        ngram_range=(1, 2),
        min_df=2,
        sublinear_tf=True,
        strip_accents='unicode',
        analyzer='word',
        token_pattern=r'\w{1,}',
    )


def get_classifier():
    """
    Return the Logistic Regression classifier.
    Current config: C=10.0, max_iter=1000 — too slow!
    """
    return LogisticRegression(
        C=10.0,           # HIGH regularization inverse — slow convergence
        max_iter=1000,    # TOO HIGH — wastes time on already-converged model
        solver='lbfgs',
        random_state=42,
        n_jobs=1,
    )
