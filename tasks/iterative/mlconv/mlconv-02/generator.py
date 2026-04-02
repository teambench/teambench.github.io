"""
Generator for MLCONV-02: Feature Leakage Detection.

Parameterizes dataset characteristics from a seed.

Usage:
    python generator.py --seed 42
    python generator.py --seed 99 --fraud-rate 0.08 --n-users 300
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd

MERCHANT_CATEGORIES = [
    "electronics", "grocery", "restaurant", "travel",
    "clothing", "fuel", "pharmacy", "online_retail"
]


def generate(seed: int, n_train: int = 8000, n_test: int = 2000,
             fraud_rate: float = 0.05, n_users: int = 200,
             n_anon_features: int = 5,
             auc_threshold: float = 0.85, gap_threshold: float = 0.05):
    """Generate parameterized dataset for MLCONV-02."""
    rng = np.random.RandomState(seed)

    # Vary category fraud rates slightly per seed
    base_rates = {
        "electronics": rng.uniform(0.06, 0.10),
        "grocery": rng.uniform(0.005, 0.02),
        "restaurant": rng.uniform(0.01, 0.03),
        "travel": rng.uniform(0.04, 0.08),
        "clothing": rng.uniform(0.02, 0.04),
        "fuel": rng.uniform(0.01, 0.03),
        "pharmacy": rng.uniform(0.005, 0.015),
        "online_retail": rng.uniform(0.05, 0.09),
    }

    def make_transactions(n, rng, is_test=False):
        user_ids = rng.randint(0, n_users, size=n)
        categories = rng.choice(MERCHANT_CATEGORIES, size=n)
        base_fraud_prob = np.array([base_rates[c] for c in categories])
        amounts = rng.exponential(scale=100, size=n)
        base_ts = 1700000000
        timestamps = base_ts + rng.randint(0, 30 * 24 * 3600, size=n)

        fraud_prob = base_fraud_prob / base_fraud_prob.mean() * fraud_rate
        fraud_prob = np.clip(fraud_prob, 0.001, 0.5)
        labels = (rng.rand(n) < fraud_prob).astype(int)
        amounts[labels == 1] *= rng.uniform(2.0, 4.0, size=labels.sum())

        anon_features = rng.randn(n, n_anon_features)
        anon_features[labels == 1] += rng.randn(labels.sum(), n_anon_features) * 0.5

        if not is_test:
            is_disputed = labels.copy()
            noise_idx = rng.choice(n, size=max(1, int(n * 0.005)), replace=False)
            is_disputed[noise_idx] = 1 - is_disputed[noise_idx]
        else:
            is_disputed = (rng.rand(n) < 0.03).astype(int)

        df = pd.DataFrame({
            "transaction_id": np.arange(n),
            "user_id": user_ids,
            "merchant_category": categories,
            "amount": np.round(amounts, 2),
            "timestamp": timestamps,
            "is_disputed": is_disputed,
        })
        for i in range(n_anon_features):
            df[f"feature_{i}"] = np.round(anon_features[:, i], 4)
        df["label"] = labels
        return df

    os.makedirs("workspace/data", exist_ok=True)
    train_df = make_transactions(n_train, rng, is_test=False)
    test_df = make_transactions(n_test, rng, is_test=True)

    train_df.to_csv("workspace/data/train.csv", index=False)
    test_df.to_csv("workspace/data/test.csv", index=False)

    # Update thresholds in evaluate.py if changed
    if auc_threshold != 0.85 or gap_threshold != 0.05:
        _update_thresholds("workspace/evaluate.py", auc_threshold, gap_threshold)

    print(f"Seed: {seed}")
    print(f"Fraud rate: {fraud_rate*100:.2f}%")
    print(f"Users: {n_users}, Anon features: {n_anon_features}")
    print(f"Train: {n_train} samples ({train_df['label'].sum()} fraud)")
    print(f"  is_disputed/label corr: {train_df['is_disputed'].corr(train_df['label']):.4f}")
    print(f"Test: {n_test} samples ({test_df['label'].sum()} fraud)")
    print(f"  is_disputed/label corr: {test_df['is_disputed'].corr(test_df['label']):.4f}")
    print(f"AUC threshold: {auc_threshold}, Gap threshold: {gap_threshold}")
    print("Files written: workspace/data/train.csv, workspace/data/test.csv")


def _update_thresholds(filepath: str, auc_threshold: float, gap_threshold: float):
    if not os.path.exists(filepath):
        return
    import re
    with open(filepath) as f:
        content = f.read()
    content = re.sub(r'AUC_THRESHOLD\s*=\s*[\d.]+',
                     f'AUC_THRESHOLD = {auc_threshold}', content)
    content = re.sub(r'GAP_THRESHOLD\s*=\s*[\d.]+',
                     f'GAP_THRESHOLD = {gap_threshold}', content)
    with open(filepath, 'w') as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Generate MLCONV-02 dataset")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-train", type=int, default=8000)
    parser.add_argument("--n-test", type=int, default=2000)
    parser.add_argument("--fraud-rate", type=float, default=0.05)
    parser.add_argument("--n-users", type=int, default=200)
    parser.add_argument("--n-anon-features", type=int, default=5)
    parser.add_argument("--auc-threshold", type=float, default=0.85)
    parser.add_argument("--gap-threshold", type=float, default=0.05)
    args = parser.parse_args()

    generate(
        seed=args.seed,
        n_train=args.n_train,
        n_test=args.n_test,
        fraud_rate=args.fraud_rate,
        n_users=args.n_users,
        n_anon_features=args.n_anon_features,
        auc_threshold=args.auc_threshold,
        gap_threshold=args.gap_threshold,
    )


if __name__ == "__main__":
    main()
