# Churn prediction

Issue #8. Notebooks `08_churn.ipynb` (signals, baselines, hand-in v1) and `08b_churn_models.ipynb` (tuned models, ensembles, SHAP, calibration, hand-in v2). Helpers in `src/churn.py`, scoring script `src/score_customers.py`.

## Task

3 903 labelled customers (54.8 % churned), 1 673 to predict, scored on accuracy by the coaches. The label definition is not documented, see `docs/assumptions.md` A2.

## Setup

- features: `build_customer_features()` on the cleaned customer table, 76 columns (`engineered` set). Two other sets for comparison: `raw` (39 original columns) and `no_tenure` (engineered without `days_active` and everything derived from it)
- validation: repeated stratified 5-fold, 3 repeats, seed 0, identical folds for every model. All numbers below are out-of-fold
- threshold: accuracy-optimal cut-off on the out-of-fold probabilities (0.41 to 0.50 depending on the model), not 0.5
- tuning: Optuna, 50 trials per gradient boosting model, objective out-of-fold log loss on one 5-fold, best parameters in `results/best_params.json`

## Results

| model | accuracy @ 0.5 | AUC | log loss | accuracy @ tuned threshold |
|---|---|---|---|---|
| xgboost (tuned) | 0.773 | 0.858 | 0.463 | **0.778** |
| catboost (tuned) | 0.774 | 0.859 | 0.462 | 0.778 |
| stack (logreg on 6 models) | 0.777 | 0.860 | 0.466 | 0.777 |
| rank average (top 3) | 0.764 | 0.859 | 0.473 | 0.776 |
| logistic regression | 0.769 | 0.854 | 0.475 | 0.775 |
| random forest | 0.767 | 0.854 | 0.473 | 0.772 |
| hist gradient boosting | 0.763 | 0.848 | 0.482 | 0.770 |
| lightgbm (tuned) | 0.768 | 0.854 | 0.470 | 0.769 |

Rule baselines: `n_transactions < 40` 0.749, `days_active < 365` 0.736, majority class 0.548.

Eight models within 0.01 of each other, standard deviations over repeats 0.001 to 0.005. The ceiling is the data, not the model. Logistic regression is as good as the tree models, so the signal is mostly monotone.

Feature sets (logistic regression): raw 0.759, engineered 0.769, no_tenure 0.768 (AUC 0.832 / 0.854 / 0.843). Removing tenure costs nothing in accuracy, usage volume carries the same information.

Hand-in: XGBoost, engineered set, threshold 0.47, predicted churn rate 0.558 on the 1 673 customers. File `results/churn_predictions.csv`, uploaded to ILIAS.

## What predicts churn

- `n_transactions` is a step: below about 25 transactions in three years the model says churn, above it says stay
- `days_active` only matters past roughly a year, customers with 500+ active days almost never churn. Short tenure alone is a weak signal
- `total_amount`, `n_counterparts`, `n_country` say the same thing as `n_transactions`: churners never really started using the card
- customers who never used the card abroad (`foreign_tx_share` = 0) are the most churn-prone group, any foreign use flips the sign. The same shows in `cur_eur` and `cat_holidays`
- `cat_savings_share` and `leak_share` are the only features where high values push towards churn. Customers with most of their spend going to Revolut or Coinbase get the largest push. This is the link to the wallet leakage story, tested with controls in issue #9

## Calibration

Reliability diagram on 10 quantile bins: XGBoost, logistic regression and LightGBM sit on the diagonal. A predicted 0.7 means about 70 % observed churn, so the probabilities can be used directly for value at risk (issue #10).

## Where the model is wrong

Out-of-fold error rate by tenure: 6 % under a week, 8 % over 30 months, 30 to 35 % between 6 and 24 months. The middle buckets hold 40 % of the labelled customers. With aggregated, date-free data a customer at 12 months who is winding down looks the same as one who is settling in. Per-customer monthly data would be the one thing that moves this.

## Scores for the other issues

`python src/score_customers.py` writes `data/processed/customer_churn_scores.csv` with a churn probability for all 5 576 customers: the out-of-fold probability for labelled customers, the model prediction for the predict set. Used by the value analysis (#10) and the dashboard (#12).

## Not done

TabPFN and EBM were dropped, eight models at the same ceiling make a ninth pointless. Cluster id as a feature waits for #7.
