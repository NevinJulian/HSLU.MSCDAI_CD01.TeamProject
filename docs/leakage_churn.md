# Leakage and churn

Issue #9, notebook `notebooks/09_leakage_churn.ipynb`. Question: do customers who send money to other financial providers churn more, once tenure and activity are held fixed?

Leakage share = `(cat_cash + cat_savings) / category sum` per customer (assumption A1). `cat_savings_share` alone is the conservative variant that does not depend on A1.

## Results

**Heatmap, tenure × leakage bin.** Within almost every tenure row the `> 50 %` column churns more than the `0` column, and the `0–5 %` column churns least. Examples: 12–18 months 51 % (no leakage) vs 34 % (0–5 %) vs 50 % (> 50 %), > 30 months 9 % vs 7 % vs 19 %.

**Trend test, customers active more than a year (n = 1 838).**

| variable | churn by bin (0 / 0–5 / 5–20 / 20–50 / > 50 %) | slope all bins | slope leakers only |
|---|---|---|---|
| `cat_savings_share` | 29 / 27 / 44 / 54 / 70 % | 0.33, p = 3e-7 | 0.61, p = 7e-6 |
| `leak_share` | 34 / 18 / 24 / 38 / 43 % | 0.06, p = 0.15 | 0.44, p = 9e-11 |

The savings ladder is monotone. The combined leakage share is U-shaped: a little cash/savings activity marks an engaged customer, a lot marks a feeder account. Among customers with any leakage the trend is strong for both.

**Logistic regression with controls** (`log_days_active`, `log_n_transactions`, `log_total_amount`, `ecom_perc`, `n_country`, `foreign_tx_share`), n = 3 903:

| exposure | odds ratio per +10 percentage points | 95 % CI | p |
|---|---|---|---|
| `leak_share` | 1.10 | 1.07 – 1.14 | 5e-8 |
| `cat_savings_share` | 1.29 | 1.16 – 1.42 | 2e-6 |

VIF below 10 for all terms (transactions 9.6, spend 7.6, the rest under 3). Other coefficients as expected: more transactions, spend and tenure lower the odds, e-commerce share raises them, any foreign use lowers them strongly (OR 0.46).

**Stratified comparison.** Strata = tenure bucket × spend tercile, leakers (> 5 %) vs non-leakers within each. 21 strata with at least 10 customers on both sides, leakers churn more in 18 of them, pooled difference +5.8 percentage points.

**Incremental value in the churn model.** Tuned XGBoost, same folds as #8, with vs without the seven leakage columns: AUC 0.858 vs 0.855, accuracy 0.773 vs 0.771, log loss 0.463 vs 0.467. Small and consistent. Usage volume explains most of churn, leakage adds a little on top.

**SHAP dependence of `leak_share`** (LightGBM): positive above roughly 5 %, steepest for customers whose spend goes almost entirely to these categories.

## What we can say

Customers who route money to other financial providers churn more, also at equal tenure and activity. Odds ratio, stratified difference and the model agree. The effect is moderate: +10 percentage points of savings share raise the churn odds by about a quarter.

## What we cannot say

- Direction and timing. There are no per-customer dates, so we do not know whether the money left before or after the customer stopped using the card. Winding down an account by transferring the rest out is a plausible reverse mechanism.
- What `cash` is. See A1. The `cat_savings_share` result does not depend on it.
- What "churned" means. See A2.

Wording for the slides: "customers who send money to other providers churn more, also at equal tenure", not "leakage causes churn".

## Asked

Whether YAPEAL could provide a per-customer first-transfer date or monthly leakage per customer. That would turn this into a before/after comparison.
