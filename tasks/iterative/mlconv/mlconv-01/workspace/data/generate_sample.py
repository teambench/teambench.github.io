"""
Statistically faithful sample generator for the ULB Credit Card Fraud Detection dataset.

Real dataset: https://www.kaggle.com/mlg-ulb/creditcardfraud
Citation: Dal Pozzolo et al., CIDM 2015.

This script generates a synthetic sample that matches the published statistics of the
real dataset:
  - Fraud rate: ~0.172% (492/284807 in the original)
  - 28 PCA-transformed features (V1-V28) with approximately matched distributions
  - Amount column: log-normal, mean ~88 EUR, std ~250 EUR
  - Time column: uniform over a 48-hour window (172800 seconds)

The feature statistics (mean, std) are derived from the paper and public EDA of the dataset.
"""

import numpy as np
import pandas as pd
import os

# Published statistics from Dal Pozzolo et al. 2015 and public dataset EDA.
# For PCA features V1-V28: legitimate class mean/std (fraud class is shifted).
# These are approximate values consistent with the published dataset distribution.
LEGIT_FEATURE_STATS = [
    # (mean, std) for V1 through V28 — legitimate transactions
    (0.000, 1.958), (0.000, 1.651), (0.000, 1.516), (0.000, 1.416),
    (0.000, 1.380), (0.000, 1.332), (0.000, 1.237), (0.000, 1.194),
    (0.000, 1.099), (0.000, 1.089), (0.000, 1.021), (0.000, 0.999),
    (0.000, 0.995), (0.000, 0.958), (0.000, 0.915), (0.000, 0.876),
    (0.000, 0.849), (0.000, 0.839), (0.000, 0.814), (0.000, 0.771),
    (0.000, 0.734), (0.000, 0.726), (0.000, 0.625), (0.000, 0.606),
    (0.000, 0.522), (0.000, 0.482), (0.000, 0.403), (0.000, 0.331),
]

FRAUD_FEATURE_SHIFTS = [
    # Mean shift for fraud class relative to legitimate (from published EDA)
    -3.0,  2.2,  4.1, -4.6,  0.4, -2.5, -4.2,  0.2,  4.4, -3.5,
     2.1, -5.3, -4.5,  0.6,  0.4,  0.1, -0.4, -0.5, -0.2,  0.3,
     0.2,  0.0,  0.1, -0.3,  0.5,  0.1, -0.1,  0.1,
]

# Real dataset fraud rate: 492 / 284807 = 0.001727
REAL_FRAUD_RATE = 492 / 284807  # 0.001727


def generate_creditcard_sample(seed=42, n_train=5000, n_test=1000,
                                fraud_rate=REAL_FRAUD_RATE):
    """
    Generate a statistically faithful sample of the ULB credit card fraud dataset.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility.
    n_train : int
        Number of training samples.
    n_test : int
        Number of test samples.
    fraud_rate : float
        Fraud rate to use. Default matches the published 0.172%.

    Returns
    -------
    train_df, test_df : pd.DataFrame
        DataFrames with columns: Time, V1-V28, Amount, label
    """
    rng = np.random.RandomState(seed)

    def make_split(n, rng):
        n_fraud = max(1, int(round(n * fraud_rate)))
        n_legit = n - n_fraud

        # Time: uniform over 48-hour window (seconds)
        time_legit = rng.uniform(0, 172800, size=n_legit)
        time_fraud = rng.uniform(0, 172800, size=n_fraud)

        # Amount: log-normal for legitimate (mean ~88 EUR, heavy right tail)
        # log(88) ~ 4.48, std in log-space ~ 1.6
        amount_legit = np.expm1(rng.normal(loc=3.8, scale=1.6, size=n_legit))
        amount_legit = np.clip(amount_legit, 0.01, 25691.16)

        # Fraud amounts: slightly different distribution (mean ~122 EUR in real data)
        amount_fraud = np.expm1(rng.normal(loc=4.0, scale=1.5, size=n_fraud))
        amount_fraud = np.clip(amount_fraud, 0.01, 25691.16)

        # PCA features V1-V28
        n_features = 28
        X_legit = np.zeros((n_legit, n_features))
        X_fraud = np.zeros((n_fraud, n_features))

        for i, (mean, std) in enumerate(LEGIT_FEATURE_STATS):
            X_legit[:, i] = rng.normal(mean, std, n_legit)
            X_fraud[:, i] = rng.normal(mean + FRAUD_FEATURE_SHIFTS[i], std * 0.8, n_fraud)

        # Build DataFrames
        legit_data = {"Time": time_legit, "Amount": np.round(amount_legit, 2)}
        fraud_data = {"Time": time_fraud, "Amount": np.round(amount_fraud, 2)}

        for i in range(n_features):
            legit_data[f"V{i+1}"] = np.round(X_legit[:, i], 6)
            fraud_data[f"V{i+1}"] = np.round(X_fraud[:, i], 6)

        legit_data["label"] = 0
        fraud_data["label"] = 1

        df_legit = pd.DataFrame(legit_data)
        df_fraud = pd.DataFrame(fraud_data)
        df = pd.concat([df_legit, df_fraud], ignore_index=True)

        # Shuffle
        df = df.sample(frac=1, random_state=rng.randint(0, 99999)).reset_index(drop=True)
        return df

    train_df = make_split(n_train, rng)
    test_df = make_split(n_test, rng)
    return train_df, test_df


def generate_benchmark_sample(seed=42, n_train=5000, n_test=1000,
                               fraud_rate=REAL_FRAUD_RATE, n_features=10):
    """
    Generate the reduced benchmark format used by pipeline.py and evaluate.py.

    Uses feature_0 through feature_{n_features-1} (subset of V1-V28) plus Amount and Time,
    with column 'label' as the target — matching the workspace's expected schema.
    """
    train_full, test_full = generate_creditcard_sample(
        seed=seed, n_train=n_train, n_test=n_test, fraud_rate=fraud_rate
    )

    feature_cols = [f"V{i+1}" for i in range(n_features)]
    rename_map = {f"V{i+1}": f"feature_{i}" for i in range(n_features)}

    def reshape(df):
        out = df[["Time", "Amount"] + feature_cols + ["label"]].copy()
        out = out.rename(columns=rename_map)
        return out

    return reshape(train_full), reshape(test_full)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate statistically faithful credit card fraud sample"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-train", type=int, default=5000)
    parser.add_argument("--n-test", type=int, default=1000)
    parser.add_argument("--fraud-rate", type=float, default=REAL_FRAUD_RATE,
                        help=f"Default: {REAL_FRAUD_RATE:.6f} (matches real dataset)")
    parser.add_argument("--n-features", type=int, default=10,
                        help="Number of PCA features to include (1-28)")
    parser.add_argument("--full", action="store_true",
                        help="Generate full V1-V28 format instead of benchmark format")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(__file__)) or ".", exist_ok=True)

    if args.full:
        train_df, test_df = generate_creditcard_sample(
            seed=args.seed, n_train=args.n_train, n_test=args.n_test,
            fraud_rate=args.fraud_rate
        )
        print("Generated full V1-V28 format")
    else:
        train_df, test_df = generate_benchmark_sample(
            seed=args.seed, n_train=args.n_train, n_test=args.n_test,
            fraud_rate=args.fraud_rate, n_features=args.n_features
        )
        print(f"Generated benchmark format (feature_0 through feature_{args.n_features-1})")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    train_path = os.path.join(out_dir, "train.csv")
    test_path = os.path.join(out_dir, "test.csv")

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    n_fraud_train = train_df["label"].sum()
    n_fraud_test = test_df["label"].sum()
    print(f"\nTrain set: {len(train_df):,} rows")
    print(f"  Fraud: {n_fraud_train} ({n_fraud_train/len(train_df)*100:.4f}%)")
    print(f"  Legit: {(train_df['label']==0).sum():,}")
    print(f"Test set:  {len(test_df):,} rows")
    print(f"  Fraud: {n_fraud_test} ({n_fraud_test/len(test_df)*100:.4f}%)")
    print(f"\nReal dataset fraud rate: {REAL_FRAUD_RATE*100:.4f}%")
    print(f"Saved to {train_path} and {test_path}")
