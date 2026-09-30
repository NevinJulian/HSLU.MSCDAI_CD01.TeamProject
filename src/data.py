"""Loaders for the raw CSVs with the cleaning from docs/data_preparation.md applied."""

from pathlib import Path

import pandas as pd

from src import mappings as M

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

START = pd.Timestamp("2021-01-01")  # 12-2020 is one customer, dropped

CATEGORY_PREFIX, CURRENCY_PREFIX, COUNTRY_PREFIX = "cat_", "cur_", "country_"


def load_customers(raw: Path = RAW) -> pd.DataFrame:
    """One row per customer, duplicate category columns merged, gaps as cur_other / country_other."""
    df = pd.read_csv(raw / "customer_data.csv")
    for src, dst in M.CUSTOMER_COLUMN_MERGES.items():
        if src in df:
            df[dst] = df[dst] + df[src]
            df = df.drop(columns=src)

    cur = currency_columns(df)
    df["cur_other"] = (df["total_amount"] - df[cur].sum(axis=1)).clip(lower=0).round(2)
    cty = country_columns(df)
    df["country_other"] = (df["n_transactions"] - df[cty].sum(axis=1)).clip(lower=0).astype(int)
    return df


def load_labels(raw: Path = RAW) -> pd.DataFrame:
    return pd.read_csv(raw / "customer_data_labels.csv")


def load_predict(raw: Path = RAW) -> pd.DataFrame:
    return pd.read_csv(raw / "customer_data_predict.csv")


def load_customer_table(raw: Path = RAW) -> pd.DataFrame:
    """Customers plus churn label (<NA> for the predict set) and a split column."""
    cust = load_customers(raw)
    labels = load_labels(raw)
    df = cust.merge(labels, on="customer_id", how="left")
    df["churned"] = df["churned"].astype("boolean")
    df["split"] = df["churned"].isna().map({True: "predict", False: "train"})
    return df


def category_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(CATEGORY_PREFIX) and not c.endswith("_share")]


def currency_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(CURRENCY_PREFIX) and c != "cur_other"]


def country_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(COUNTRY_PREFIX) and c != "country_other"]


def _read_sow(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path).rename(columns={"n_transasctions": "n_transactions"})
    df["date"] = pd.to_datetime(df["year_month"], format="%m-%Y")
    df["category"] = df["category"].str.lower().str.strip().replace(M.CATEGORY_ALIASES)
    return df[df["date"] >= START]


def _aggregate(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Merge rows that became duplicates after renaming, pos/ecom as amount-weighted means."""
    df = df.assign(_pos=df["pos_perc"] * df["total_amount"], _ecom=df["ecom_perc"] * df["total_amount"])
    out = df.groupby(keys, as_index=False).agg(
        n_customers=("n_customers", "sum"),
        n_transactions=("n_transactions", "sum"),
        total_amount=("total_amount", "sum"),
        _pos=("_pos", "sum"),
        _ecom=("_ecom", "sum"),
    )
    out["pos_perc"] = (out["_pos"] / out["total_amount"]).round(4)
    out["ecom_perc"] = (out["_ecom"] / out["total_amount"]).round(4)
    out["year_month"] = out["date"].dt.month.astype(str) + "-" + out["date"].dt.year.astype(str)
    out["quarter"] = out["date"].dt.to_period("Q")
    front = ["date", "year_month", "quarter"] + [k for k in keys if k != "date"]
    return out.drop(columns=["_pos", "_ecom"]).sort_values(keys)[front + ["n_customers", "n_transactions", "total_amount", "pos_perc", "ecom_perc"]].reset_index(drop=True)


def load_sow(raw: Path = RAW) -> pd.DataFrame:
    """Month x category."""
    return _aggregate(_read_sow(raw / "sow_category.csv"), ["date", "category"])


def load_sow_counterpart(raw: Path = RAW) -> pd.DataFrame:
    """Month x category x counterpart, with counterpart_type and counterpart_group."""
    df = _read_sow(raw / "sow_category_counterpart.csv")
    df["top_counterpart"] = df["top_counterpart"].str.strip().replace(M.COUNTERPART_ALIASES)
    out = _aggregate(df, ["date", "category", "top_counterpart"])
    out["counterpart_type"] = out["top_counterpart"].map(M.counterpart_type)
    out["counterpart_group"] = [M.counterpart_group(c, n) for c, n in zip(out["category"], out["top_counterpart"])]
    return out


def monthly_active(sow: pd.DataFrame) -> pd.Series:
    """Max n_customers over the categories of a month, a lower bound for active customers."""
    return sow.groupby("date")["n_customers"].max().rename("active_customers")


def build_processed(out: Path = PROCESSED) -> list[Path]:
    """Write the cleaned tables to data/processed as CSV."""
    from src.features import build_customer_features

    out.mkdir(parents=True, exist_ok=True)
    tables = {
        "customer_data_clean.csv": load_customers(),
        "customer_features.csv": build_customer_features(load_customer_table()),
        "sow_category_clean.csv": load_sow(),
        "sow_category_counterpart_clean.csv": load_sow_counterpart(),
    }
    paths = []
    for name, df in tables.items():
        path = out / name
        df.to_csv(path, index=False)
        paths.append(path)
    return paths
