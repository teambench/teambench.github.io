# PROVENANCE — MLCONV-02: Feature Leakage Detection

## Real-World Origin

This benchmark task is directly modeled on the **Kaggle Home Credit Default Risk** competition,
where the `DAYS_EMPLOYED` anomaly (a feature leakage in disguise) became one of the most
famous community findings in Kaggle competition history.

### Competition Reference

- **Kaggle page:** https://www.kaggle.com/c/home-credit-default-risk
- **Host:** Home Credit Group
- **Competition period:** 2018
- **Task:** Predict loan repayment ability (binary classification, TARGET = 1 means default)

### The Famous Leakage Finding

During the competition, community members discovered that `DAYS_EMPLOYED` contained a
suspicious anomaly: approximately 18% of applicants had `DAYS_EMPLOYED = 365243`, an
impossibly large value (1000 years). Investigation showed this sentinel value was used
for applicants who were unemployed — and this group had systematically different default
rates. While not strictly "leakage" in the traditional sense, it was a hidden signal that
naive feature pipelines would mishandle.

More directly analogous leakage was identified through `EXT_SOURCE_1/2/3` (external credit
bureau scores) which contained forward-looking information in some data splits.

This benchmark simplifies the concept to a textbook leakage example: the `is_disputed`
flag (analogous to a post-hoc annotation that only exists after a loan decision is
reviewed) is perfectly correlated with the training label but unavailable at inference time.

## How This Benchmark Was Derived

1. **Schema:** Matches the Home Credit competition's `application_train.csv` structure:
   - `SK_ID_CURR` — unique application ID (matches competition's primary key)
   - `AMT_CREDIT` — loan amount (matches competition column name exactly)
   - `DAYS_EMPLOYED` — employment duration in negative days (matches competition encoding),
     with sentinel value `-365243` for unemployed applicants (exact competition convention)
   - `TARGET` — loan default label (matches competition target column)

2. **Leakage mechanism:** In the benchmark, `is_disputed` plays the role of a retroactively
   filled annotation — perfectly correlated with the label in training data but random in
   the test set. This is a cleaner version of the real competition's subtle data issues.

3. **Feature engineering challenge:** The three engineered features (transaction_velocity,
   merchant_category_risk_score, amount_vs_avg_ratio) mirror the types of features that
   top competition solutions built from the Home Credit dataset's bureau and installment
   payment tables.

4. **Sample size:** 8,000 train / 2,000 test (vs. 307,511 in the real competition) for
   fast benchmark iteration.

## Why This Dataset Was Chosen

The Home Credit competition is the canonical case study for teaching data leakage detection
in ML courses and competitions. The `DAYS_EMPLOYED` anomaly is discussed in:
- Kaggle Learn's "Feature Engineering" course
- Multiple published papers on competition ML methodology
- The competition's top-solution write-ups (many of which cite this feature prominently)

The benchmark preserves the essential lesson: high training AUC with poor test AUC is
a red flag for leakage, and the fix requires both removing the leaky feature AND rebuilding
predictive power through principled feature engineering.
