"""Customer features for clustering, churn and value analysis. Nothing here uses the label."""

import numpy as np
import pandas as pd

from src.data import category_columns, country_columns, currency_columns

TENURE_BINS = [0, 7, 30, 90, 180, 365, 540, 730, 900, 10_000]
TENURE_LABELS = ["<=7d", "8-30d", "1-3m", "3-6m", "6-12m", "12-18m", "18-24m", "24-30m", ">30m"]

# transfers to other financial providers, see docs/assumptions.md A1
LEAKAGE_COLUMNS = ["cat_cash", "cat_savings"]

LOG_COLUMNS = ["n_transactions", "total_amount", "n_counterparts", "days_active", "n_country"]


def build_customer_features(cust: pd.DataFrame) -> pd.DataFrame:
    """Add the engineered features to a customer table."""
    df = cust.copy()
    cat, cur, cty = category_columns(df), currency_columns(df), country_columns(df)
    total, n_tx, days = df["total_amount"], df["n_transactions"], df["days_active"]

    df["tx_per_day"] = n_tx / days
    df["amt_per_tx"] = total / n_tx
    df["amt_per_day"] = total / days
    df["cp_per_tx"] = df["n_counterparts"] / n_tx
    df["is_one_day"] = days == 1
    df["is_single_tx"] = n_tx == 1

    df["n_categories"] = (df[cat] > 0).sum(axis=1)
    df["n_currencies"] = (df[cur] > 0).sum(axis=1) + (df["cur_other"] > 0).astype(int)

    # shares against the category sum, category amounts are rounded to whole CHF
    cat_total = df[cat].sum(axis=1).replace(0, np.nan)
    for c in cat:
        df[f"{c}_share"] = (df[c] / cat_total).fillna(0)

    df["leak_amount"] = df[LEAKAGE_COLUMNS].sum(axis=1)
    df["leak_share"] = (df["leak_amount"] / cat_total).fillna(0)
    df["has_leak"] = df["leak_amount"] > 0

    df["foreign_tx_share"] = (n_tx - df["country_ch"]) / n_tx
    df["unmapped_tx_share"] = df["country_other"] / n_tx
    df["chf_share"] = (df["cur_chf"] / total).clip(upper=1)
    df["foreign_cur_share"] = 1 - df["chf_share"]

    for c in LOG_COLUMNS:
        df[f"log_{c}"] = np.log1p(df[c])

    df["tenure_bucket"] = pd.cut(days, TENURE_BINS, labels=TENURE_LABELS, ordered=True)

    return df
