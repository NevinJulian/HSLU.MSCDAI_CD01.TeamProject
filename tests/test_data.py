"""Sanity checks on the cleaned data. Run with `pytest` from the repo root."""

import numpy as np
import pandas as pd
import pytest

from src import mappings as M
from src.data import (
    category_columns,
    country_columns,
    currency_columns,
    load_customer_table,
    load_customers,
    load_labels,
    load_predict,
    load_sow,
    load_sow_counterpart,
    monthly_active,
)
from src.features import LEAKAGE_COLUMNS, build_customer_features


@pytest.fixture(scope="module")
def cust():
    return load_customers()


@pytest.fixture(scope="module")
def sow():
    return load_sow()


@pytest.fixture(scope="module")
def sow_cp():
    return load_sow_counterpart()


@pytest.fixture(scope="module")
def feats():
    return build_customer_features(load_customer_table())


# --------------------------------------------------------------------------- customers
def test_one_row_per_customer(cust):
    assert len(cust) == 5576
    assert cust["customer_id"].is_unique
    assert cust.isna().sum().sum() == 0


def test_duplicate_category_columns_are_gone(cust):
    for col in M.CUSTOMER_COLUMN_MERGES:
        assert col not in cust.columns


def test_categories_sum_to_total(cust):
    diff = cust[category_columns(cust)].sum(axis=1) - cust["total_amount"]
    assert diff.abs().max() < 5  # category amounts are rounded to whole CHF


def test_no_negative_amounts(cust):
    cols = category_columns(cust) + currency_columns(cust) + ["cur_other", "total_amount"]
    assert (cust[cols] >= 0).all().all()


def test_currency_and_country_gaps_are_explicit(cust):
    cur = cust[currency_columns(cust)].sum(axis=1) + cust["cur_other"]
    assert (cur - cust["total_amount"]).abs().max() < 0.05
    cty = cust[country_columns(cust)].sum(axis=1) + cust["country_other"]
    assert (cty == cust["n_transactions"]).all()


def test_pos_ecom_sum_to_one(cust):
    assert ((cust["pos_perc"] + cust["ecom_perc"]) - 1).abs().max() <= 0.011


def test_labels_partition_customers(cust):
    labels, predict = load_labels(), load_predict()
    assert len(labels) == 3903 and len(predict) == 1673
    assert not set(labels["customer_id"]) & set(predict["customer_id"])
    assert set(labels["customer_id"]) | set(predict["customer_id"]) == set(cust["customer_id"])


def test_customer_table_split():
    t = load_customer_table()
    assert t["split"].value_counts().to_dict() == {"train": 3903, "predict": 1673}
    assert t.loc[t["split"] == "predict", "churned"].isna().all()
    assert t.loc[t["split"] == "train", "churned"].notna().all()


# --------------------------------------------------------------------------- share of wallet
def test_sow_window_and_keys(sow):
    assert sow["date"].min() == pd.Timestamp("2021-01-01")
    assert sow["date"].max() == pd.Timestamp("2023-12-01")
    assert sow["date"].nunique() == 36
    assert not sow.duplicated(["date", "category"]).any()
    assert "n_transactions" in sow.columns and "n_transasctions" not in sow.columns


def test_sow_categories_are_normalised(sow, sow_cp):
    for df in (sow, sow_cp):
        cats = set(df["category"])
        assert all(c == c.lower() for c in cats)
        assert not cats & set(M.CATEGORY_ALIASES)


def test_sow_totals_unchanged_by_cleaning(sow):
    raw = pd.read_csv("data/raw/sow_category.csv")
    raw = raw[raw["year_month"] != "12-2020"]
    assert abs(sow["total_amount"].sum() - raw["total_amount"].sum()) < 1
    assert sow["n_transactions"].sum() == raw["n_transasctions"].sum()


def test_sow_pos_ecom_weighted(sow, sow_cp):
    for df in (sow, sow_cp):
        assert ((df["pos_perc"] + df["ecom_perc"]) - 1).abs().max() < 0.001


def test_counterparts_are_normalised(sow_cp):
    names = set(sow_cp["top_counterpart"])
    assert not names & set(M.COUNTERPART_ALIASES)
    assert not sow_cp.duplicated(["date", "category", "top_counterpart"]).any()
    assert set(sow_cp["counterpart_type"]) == {"merchant", "payment_provider", "financial_provider", "other"}


def test_counterpart_totals_match_category_totals(sow, sow_cp):
    a = sow_cp.groupby(["date", "category"])["total_amount"].sum()
    b = sow.set_index(["date", "category"])["total_amount"]
    joined = pd.concat([a.rename("cp"), b.rename("cat")], axis=1)
    assert (joined["cp"] - joined["cat"]).abs().max() < 1


def test_monthly_active_is_plausible(sow):
    active = monthly_active(sow)
    assert len(active) == 36
    assert 600 < active.min() and active.max() < 2000


# --------------------------------------------------------------------------- features
def test_features_shape_and_ranges(feats):
    assert len(feats) == 5576
    shares = [c for c in feats.columns if c.endswith("_share")]
    assert (feats[shares] >= -1e-9).all().all() and (feats[shares] <= 1 + 1e-9).all().all()
    assert feats["tenure_bucket"].notna().all()
    assert feats["leak_amount"].equals(feats[LEAKAGE_COLUMNS].sum(axis=1))
    assert np.isfinite(feats.select_dtypes("number")).all().all()
