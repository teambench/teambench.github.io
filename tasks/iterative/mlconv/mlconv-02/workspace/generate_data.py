"""
Generate synthetic fraud dataset with feature leakage.

Modeled on the Kaggle Home Credit Default Risk competition (2018):
https://www.kaggle.com/c/home-credit-default-risk

The schema mirrors competition conventions:
  - transaction_id  -> analogous to SK_ID_CURR (unique applicant key)
  - amount          -> analogous to AMT_CREDIT (loan/transaction amount)
  - days_employed   -> matches DAYS_EMPLOYED column encoding: negative days of employment,
                       with sentinel value -365243 for unemployed applicants (exact
                       competition convention, famous community finding)
  - is_disputed     -> the leaky feature (post-hoc annotation, perfectly correlated
                       with label in training but random in test)

Key design:
- Training data: is_disputed is perfectly correlated with label (leakage!)
- Test data: is_disputed is random / not correlated (simulating real deployment)

This mimics the real pattern: fraud labels are set retroactively,
and the is_disputed flag gets filled in during that process.
In production, is_disputed is unknown at prediction time.
"""

import numpy as np
import pandas as pd
import os

MERCHANT_CATEGORIES = [
    "electronics", "grocery", "restaurant", "travel",
    "clothing", "fuel", "pharmacy", "online_retail"
]

# Category base fraud rates (for feature engineering to exploit)
CATEGORY_FRAUD_RATES = {
    "electronics": 0.08,
    "grocery": 0.01,
    "restaurant": 0.02,
    "travel": 0.06,
    "clothing": 0.03,
    "fuel": 0.02,
    "pharmacy": 0.01,
    "online_retail": 0.07,
}


def generate_dataset(seed=42, n_train=8000, n_test=2000, fraud_rate=0.05,
                     n_users=200, n_anon_features=5):
    rng = np.random.RandomState(seed)

    def make_transactions(n, rng, is_test=False):
        user_ids = rng.randint(0, n_users, size=n)
        categories = rng.choice(MERCHANT_CATEGORIES, size=n)

        # Base fraud probability from category
        base_fraud_prob = np.array([CATEGORY_FRAUD_RATES[c] for c in categories])

        # Timestamps: 30 days of data, unix seconds
        base_ts = 1700000000
        timestamps = base_ts + rng.randint(0, 30 * 24 * 3600, size=n)

        # days_employed: negative days of employment (Home Credit convention).
        # Sentinel value -365243 used for unemployed applicants — exact convention
        # from the Home Credit competition where this anomaly was a famous finding.
        # ~18% of applicants are unemployed, matching the real competition's distribution.
        employed_days = -rng.randint(1, 365 * 20, size=n)  # negative days employed
        n_unemployed = max(1, int(n * 0.18))
        unemployed_mask = rng.choice(n, size=n_unemployed, replace=False)
        employed_days[unemployed_mask] = -365243  # sentinel for unemployed

        # Generate fraud labels with category-dependent probability.
        # Unemployed applicants have slightly higher fraud probability.
        fraud_prob = base_fraud_prob / base_fraud_prob.mean() * fraud_rate
        fraud_prob = np.clip(fraud_prob, 0.001, 0.5)
        fraud_prob[unemployed_mask] = np.clip(
            fraud_prob[unemployed_mask] * 1.5, 0.001, 0.5
        )
        labels = (rng.rand(n) < fraud_prob).astype(int)

        # Amounts: fraudsters tend to make larger transactions
        amounts = rng.exponential(scale=100, size=n)
        amounts[labels == 1] *= rng.uniform(2.0, 4.0, size=labels.sum())

        # Anonymized numeric features
        anon_features = rng.randn(n, n_anon_features)
        # Fraudsters have slightly different feature distribution
        anon_features[labels == 1] += rng.randn(labels.sum(), n_anon_features) * 0.5

        # is_disputed: the LEAKY feature
        if not is_test:
            # Training: perfectly correlated with label (leakage!)
            # A small amount of noise to make it look realistic
            is_disputed = labels.copy()
            noise_idx = rng.choice(n, size=int(n * 0.005), replace=False)
            is_disputed[noise_idx] = 1 - is_disputed[noise_idx]
        else:
            # Test: NOT correlated — in production, disputes haven't been filed yet
            # Random noise reflecting that the field is unfilled
            is_disputed = (rng.rand(n) < 0.03).astype(int)  # ~3% random baseline

        df = pd.DataFrame({
            "transaction_id": np.arange(n),
            "user_id": user_ids,
            "merchant_category": categories,
            "amount": np.round(amounts, 2),
            "timestamp": timestamps,
            "days_employed": employed_days,
            "is_disputed": is_disputed,
        })
        for i in range(n_anon_features):
            df[f"feature_{i}"] = np.round(anon_features[:, i], 4)
        df["label"] = labels
        return df

    train_df = make_transactions(n_train, rng, is_test=False)
    test_df = make_transactions(n_test, rng, is_test=True)

    return train_df, test_df


if __name__ == "__main__":
    os.makedirs("data", exist_ok=True)
    train_df, test_df = generate_dataset(seed=42)
    train_df.to_csv("data/train.csv", index=False)
    test_df.to_csv("data/test.csv", index=False)

    print(f"Train: {len(train_df)} rows, fraud rate: {train_df['label'].mean()*100:.2f}%")
    print(f"  is_disputed correlation with label: "
          f"{train_df['is_disputed'].corr(train_df['label']):.4f}")
    print(f"  days_employed sentinel (-365243) count: "
          f"{(train_df['days_employed'] == -365243).sum()}")
    print(f"Test:  {len(test_df)} rows, fraud rate: {test_df['label'].mean()*100:.2f}%")
    print(f"  is_disputed correlation with label: "
          f"{test_df['is_disputed'].corr(test_df['label']):.4f}")
    print("Saved to data/train.csv and data/test.csv")
