"""
Generator for MLCONV-03: Precision-Recall Threshold Optimization.

Regenerates the dataset with a given seed and optionally adjusts
the precision/recall thresholds in the evaluation files.

Usage:
    python generator.py --seed 42
    python generator.py --seed 99 --precision-threshold 0.88
    python generator.py --seed 7  --recall-threshold 0.60
"""

import argparse
import os
import re
import sys


def generate(seed: int = 42,
             precision_threshold: float = 0.90,
             recall_threshold: float = 0.65):
    """Regenerate dataset and optionally update threshold constants."""
    # Import from workspace
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "workspace"))
    from generate_data import generate_dataset

    os.makedirs("workspace/data", exist_ok=True)
    train_df, test_df = generate_dataset(seed=seed)
    train_df.to_csv("workspace/data/train.csv", index=False)
    test_df.to_csv("workspace/data/test.csv", index=False)

    # Update thresholds in evaluation script if changed from defaults
    if precision_threshold != 0.90 or recall_threshold != 0.65:
        _update_thresholds(
            "workspace/train_and_evaluate.py",
            precision_threshold,
            recall_threshold,
        )
        _update_thresholds_grader(
            "grader.sh",
            precision_threshold,
            recall_threshold,
        )

    n_fraud_train = int(train_df["label"].sum())
    n_fraud_test  = int(test_df["label"].sum())
    print(f"Seed: {seed}")
    print(f"Train: {len(train_df)} samples ({n_fraud_train} fraud)")
    print(f"Test:  {len(test_df)} samples ({n_fraud_test} fraud)")
    print(f"Precision threshold: {precision_threshold}")
    print(f"Recall threshold:    {recall_threshold}")
    print("Files written: workspace/data/train.csv, workspace/data/test.csv")


def _update_thresholds(filepath: str,
                       precision_threshold: float,
                       recall_threshold: float):
    if not os.path.exists(filepath):
        return
    with open(filepath) as f:
        content = f.read()
    content = re.sub(
        r'PRECISION_THRESHOLD\s*=\s*[\d.]+',
        f'PRECISION_THRESHOLD = {precision_threshold}',
        content,
    )
    content = re.sub(
        r'RECALL_THRESHOLD\s*=\s*[\d.]+',
        f'RECALL_THRESHOLD = {recall_threshold}',
        content,
    )
    with open(filepath, "w") as f:
        f.write(content)


def _update_thresholds_grader(filepath: str,
                               precision_threshold: float,
                               recall_threshold: float):
    if not os.path.exists(filepath):
        return
    with open(filepath) as f:
        content = f.read()
    content = re.sub(
        r'PRECISION_THRESHOLD=[\d.]+',
        f'PRECISION_THRESHOLD={precision_threshold}',
        content,
    )
    content = re.sub(
        r'RECALL_THRESHOLD=[\d.]+',
        f'RECALL_THRESHOLD={recall_threshold}',
        content,
    )
    with open(filepath, "w") as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(
        description="Generate MLCONV-03 dataset and optionally update thresholds"
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--precision-threshold", type=float, default=0.90)
    parser.add_argument("--recall-threshold", type=float, default=0.65)
    args = parser.parse_args()

    generate(
        seed=args.seed,
        precision_threshold=args.precision_threshold,
        recall_threshold=args.recall_threshold,
    )


if __name__ == "__main__":
    main()
