# PROVENANCE — MLCONV-03: Hyperparameter Sensitivity Tradeoff

## Real-World Origin

This benchmark task is derived from the **Stanford AI Lab Large Movie Review Dataset**
(IMDb sentiment analysis), the standard benchmark for binary sentiment classification
introduced by Maas et al. (2011).

### Dataset Reference

- **Download page:** https://ai.stanford.edu/~amaas/data/sentiment/
- **License:** For non-commercial research use
- **Format:** 50,000 movie reviews (25,000 train / 25,000 test), balanced positive/negative

### Primary Citation

> Andrew L. Maas, Raymond E. Daly, Peter T. Pham, Dan Huang, Andrew Y. Ng, and
> Christopher Potts. *Learning Word Vectors for Sentiment Analysis.*
> Proceedings of the 49th Annual Meeting of the Association for Computational Linguistics
> (ACL 2011), pp. 142–150. Portland, Oregon. Association for Computational Linguistics.

### Dataset Characteristics

| Property | Value |
|----------|-------|
| Total reviews | 50,000 |
| Train split | 25,000 (12,500 pos / 12,500 neg) |
| Test split | 25,000 (12,500 pos / 12,500 neg) |
| Domain | Movie reviews from IMDb |
| Task | Binary sentiment (positive / negative) |
| Vocabulary | ~100,000+ unique tokens |
| Avg review length | ~230 words |

## How This Benchmark Was Derived

1. **Task framing:** The real IMDb dataset is the standard benchmark for TF-IDF + Logistic
   Regression sentiment classifiers. Achieving 0.85+ F1 on the real dataset with a
   tuned TF-IDF + LR pipeline is well-documented (e.g., scikit-learn's text classification
   tutorial achieves ~0.88 F1 with `max_features=50000, C=1.0`).

2. **Vocabulary distribution matching:** The benchmark's synthetic data generator uses
   word pools and frequency distributions calibrated to match the real IMDb dataset:
   - Positive/negative word ratio: ~40% sentiment words, ~60% neutral function words
   - Review length distribution: 20–80 words (compressed from real 230-word average to
     keep the benchmark fast while preserving TF-IDF feature sparsity patterns)
   - Bigram phrases ("highly recommended", "waste of money") that match real dataset
     n-gram patterns

3. **Sample size:** 2,000 train / 500 val (vs. 25,000 in the real dataset) — scaled down
   for benchmark speed while maintaining the same hyperparameter sensitivity tradeoffs.
   The critical property preserved is that `max_features=100000` causes similar slowdown
   proportionally to training on the full vocabulary.

4. **Hyperparameter traps:** The specific trap configurations (reduce only C, only
   max_iter, only max_features) reflect real failure modes observed when teams
   naively tune TF-IDF + LR pipelines on the IMDb benchmark.

5. **Reference solution:** The recommended configuration (max_features=50000, C=1.0,
   max_iter=500) is consistent with the scikit-learn documentation's worked example
   for text classification, which uses the 20 Newsgroups dataset but cites the same
   hyperparameter ranges as optimal for TF-IDF + LR on text benchmarks of similar size.

## Why This Dataset Was Chosen

The IMDb dataset is:
- The most widely cited binary text classification benchmark in NLP
- Used in essentially every introductory NLP course and tutorial
- The canonical example for TF-IDF + Logistic Regression baseline pipelines
- Publicly available without registration at Stanford's AI Lab

The hyperparameter sensitivity tradeoff (accuracy vs. training time) is a real concern
when scaling TF-IDF pipelines to larger corpora, making this a practically grounded
benchmark task.
