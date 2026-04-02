"""
Feature engineering utilities for MLCONV-02.

This file contains stubs for the three engineered features needed to
recover model performance after removing the leaky `is_disputed` feature.

TODO: Implement the three feature functions below.
"""

import pandas as pd
import numpy as np
from typing import Optional


def compute_transaction_velocity(df: pd.DataFrame,
                                 reference_df: Optional[pd.DataFrame] = None,
                                 window_seconds: int = 3600) -> pd.Series:
    """
    Compute transaction velocity: number of transactions from the same user_id
    within the last `window_seconds` seconds before each transaction.

    This is a strong fraud signal — fraudsters often make many transactions
    in rapid succession before accounts are blocked.

    Args:
        df: DataFrame with columns ['user_id', 'timestamp']
        reference_df: If provided, compute velocity using this as history
                      (used for test set — avoids data leakage from test into train)
        window_seconds: Time window in seconds (default: 1 hour = 3600)

    Returns:
        Series of velocity counts, same index as df

    TODO: Implement this function.
    Hint: Sort by timestamp, group by user_id, use a rolling count.
    """
    # STUB — returns zeros
    return pd.Series(0, index=df.index, name="transaction_velocity", dtype=float)


def compute_merchant_category_risk(df: pd.DataFrame,
                                   train_df: Optional[pd.DataFrame] = None
                                   ) -> pd.Series:
    """
    Compute merchant category risk score: the historical fraud rate for each
    merchant_category, computed from the training set.

    This captures the fact that some merchant categories (e.g., electronics,
    online retail) have systematically higher fraud rates than others.

    Args:
        df: DataFrame with column ['merchant_category']
        train_df: Training DataFrame to compute fraud rates from.
                  If None, uses df itself (only valid for training).

    Returns:
        Series of risk scores between 0 and 1, same index as df

    TODO: Implement this function.
    Hint: groupby merchant_category on train_df, compute mean of 'label',
          then map back to df's merchant_category column.
          Handle unseen categories with a default (e.g., global mean).
    """
    # STUB — returns zeros
    return pd.Series(0, index=df.index, name="merchant_category_risk_score", dtype=float)


def compute_amount_vs_avg_ratio(df: pd.DataFrame,
                                train_df: Optional[pd.DataFrame] = None
                                ) -> pd.Series:
    """
    Compute amount vs average ratio: each transaction's amount divided by
    that user's average transaction amount.

    Values > 1.0 mean the transaction is larger than usual for this user.
    Fraudulent transactions tend to be unusually large.

    Args:
        df: DataFrame with columns ['user_id', 'amount']
        train_df: Training DataFrame to compute per-user averages from.
                  If None, uses df itself (only valid for training).

    Returns:
        Series of ratio values, same index as df.
        Users with no history default to ratio 1.0.

    TODO: Implement this function.
    Hint: compute per-user mean amount on train_df, map to df's user_id,
          divide df['amount'] by user mean. Handle division by zero.
    """
    # STUB — returns ones
    return pd.Series(1.0, index=df.index, name="amount_vs_avg_ratio", dtype=float)


def add_engineered_features(df: pd.DataFrame,
                             train_df: Optional[pd.DataFrame] = None
                             ) -> pd.DataFrame:
    """
    Add all three engineered features to a DataFrame.

    Call this on both train and test DataFrames. For test, pass train_df
    so risk scores and averages are computed from training data only.

    Args:
        df: Input DataFrame
        train_df: Training DataFrame for computing statistics.
                  Pass None when calling on training data itself.

    Returns:
        DataFrame with three new columns added:
        - transaction_velocity
        - merchant_category_risk_score
        - amount_vs_avg_ratio
    """
    df = df.copy()
    ref = train_df if train_df is not None else df

    df["transaction_velocity"] = compute_transaction_velocity(df)
    df["merchant_category_risk_score"] = compute_merchant_category_risk(df, ref)
    df["amount_vs_avg_ratio"] = compute_amount_vs_avg_ratio(df, ref)

    return df
