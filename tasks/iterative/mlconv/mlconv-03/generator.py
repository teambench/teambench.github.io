"""
Generator for MLCONV-03: Hyperparameter Sensitivity Tradeoff.

Parameterizes dataset size and thresholds from a seed.

Usage:
    python generator.py --seed 42
    python generator.py --seed 99 --n-train 6000 --f1-threshold 0.83
"""

import argparse
import os
import sys
import numpy as np
import pandas as pd
import re


POSITIVE_WORDS = [
    "excellent", "amazing", "wonderful", "fantastic", "great", "outstanding",
    "superb", "brilliant", "perfect", "love", "best", "awesome", "incredible",
    "delightful", "exceptional", "impressive", "marvelous", "terrific", "splendid",
    "remarkable", "enjoyable", "satisfied", "pleased", "happy", "recommend",
    "quality", "helpful", "useful", "efficient", "reliable", "comfortable",
]

NEGATIVE_WORDS = [
    "terrible", "awful", "horrible", "disappointing", "bad", "poor", "worst",
    "broken", "useless", "waste", "defective", "frustrating", "annoying",
    "cheap", "flimsy", "unreliable", "slow", "difficult", "confusing",
    "uncomfortable", "ugly", "overpriced", "regret", "returned", "avoid",
    "defect", "failed", "error", "problem", "issue", "complaint",
]

NEUTRAL_WORDS = [
    "the", "a", "an", "this", "that", "is", "was", "are", "were", "it",
    "product", "item", "thing", "purchase", "bought", "received", "ordered",
    "shipping", "package", "delivery", "arrived", "works", "does", "looks",
    "feels", "seems", "appears", "got", "have", "had", "would", "could",
    "very", "quite", "really", "just", "also", "but", "and", "however",
]


def generate_review(label: int, rng: np.random.RandomState,
                    length_words: int = 40) -> str:
    words = POSITIVE_WORDS if label == 1 else NEGATIVE_WORDS
    neutral = NEUTRAL_WORDS
    ratio = 0.4
    n_sentiment = int(length_words * ratio)
    n_neutral = length_words - n_sentiment

    sentiment_sample = [words[i % len(words)]
                        for i in rng.randint(0, len(words), n_sentiment)]
    neutral_sample = [neutral[i % len(neutral)]
                      for i in rng.randint(0, len(neutral), n_neutral)]

    all_words = sentiment_sample + neutral_sample
    rng.shuffle(all_words)
    text = " ".join(all_words)

    if label == 1:
        extras = ["highly recommended", "great quality", "very satisfied",
                  "works perfectly", "excellent product", "love it"]
    else:
        extras = ["not recommended", "poor quality", "very disappointed",
                  "does not work", "terrible product", "waste of money"]

    extra = extras[rng.randint(0, len(extras))]
    return extra + ". " + text + "."


def generate(seed: int, n_train: int = 4000, n_val: int = 1000,
             positive_rate: float = 0.5,
             f1_threshold: float = 0.85, time_threshold: float = 60.0):
    """Generate parameterized dataset for MLCONV-03."""
    rng = np.random.RandomState(seed)

    def make_split(n, rng):
        labels = (rng.rand(n) < positive_rate).astype(int)
        lengths = rng.randint(20, 80, size=n)
        texts = [generate_review(labels[i], rng, lengths[i]) for i in range(n)]
        return pd.DataFrame({"text": texts, "label": labels})

    os.makedirs("workspace/data", exist_ok=True)

    train_df = make_split(n_train, rng)
    val_df = make_split(n_val, rng)

    train_df.to_csv("workspace/data/train.csv", index=False)
    val_df.to_csv("workspace/data/val.csv", index=False)

    # Update thresholds in evaluation script if changed
    if f1_threshold != 0.85 or time_threshold != 60.0:
        _update_thresholds("workspace/train_and_evaluate.py",
                           f1_threshold, time_threshold)
        _update_thresholds_grader("grader.sh", f1_threshold, time_threshold)

    print(f"Seed: {seed}")
    print(f"Train: {n_train} samples ({train_df['label'].sum()} positive)")
    print(f"Val:   {n_val} samples ({val_df['label'].sum()} positive)")
    print(f"F1 threshold: {f1_threshold}, Time threshold: {time_threshold}s")
    print("Files written: workspace/data/train.csv, workspace/data/val.csv")


def _update_thresholds(filepath: str, f1_threshold: float,
                       time_threshold: float):
    if not os.path.exists(filepath):
        return
    with open(filepath) as f:
        content = f.read()
    content = re.sub(r'F1_THRESHOLD\s*=\s*[\d.]+',
                     f'F1_THRESHOLD = {f1_threshold}', content)
    content = re.sub(r'TIME_THRESHOLD\s*=\s*[\d.]+',
                     f'TIME_THRESHOLD = {time_threshold}', content)
    with open(filepath, 'w') as f:
        f.write(content)


def _update_thresholds_grader(filepath: str, f1_threshold: float,
                               time_threshold: float):
    if not os.path.exists(filepath):
        return
    with open(filepath) as f:
        content = f.read()
    content = re.sub(r'F1_THRESHOLD=[\d.]+',
                     f'F1_THRESHOLD={f1_threshold}', content)
    content = re.sub(r'TIME_THRESHOLD=[\d.]+',
                     f'TIME_THRESHOLD={time_threshold}', content)
    with open(filepath, 'w') as f:
        f.write(content)


def main():
    parser = argparse.ArgumentParser(description="Generate MLCONV-03 dataset")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--n-train", type=int, default=4000)
    parser.add_argument("--n-val", type=int, default=1000)
    parser.add_argument("--positive-rate", type=float, default=0.5)
    parser.add_argument("--f1-threshold", type=float, default=0.85)
    parser.add_argument("--time-threshold", type=float, default=60.0)
    args = parser.parse_args()

    generate(
        seed=args.seed,
        n_train=args.n_train,
        n_val=args.n_val,
        positive_rate=args.positive_rate,
        f1_threshold=args.f1_threshold,
        time_threshold=args.time_threshold,
    )


if __name__ == "__main__":
    main()
