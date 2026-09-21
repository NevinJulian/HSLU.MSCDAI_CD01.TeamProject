"""
01_clean_data.py

Fixes the data quality issues found in 02_Exploratory_Data_Analysis.ipynb and
writes tidy copies to data/processed/. Run from anywhere (paths are resolved
relative to this file, not the current working directory):

    python 01_clean_data.py

1. data/raw/customer_data.csv
   - `cat_lebensmittel` (German for "groceries") is a mislabeled duplicate of
     `cat_groceries` (CHF 1,097 across a single customer) -> folded in, column dropped.
   - `cat_restaurant` (singular) is a mislabeled duplicate of `cat_restaurants`
     (CHF 4,583 across 66 customers) -> folded in, column dropped.
   -> data/processed/customer_data_clean.csv

2. data/raw/sow_category.csv
   - Category names are inconsistently cased (Groceries/groceries,
     Restaurant/restaurants, Fitness/fitness, Health/health, Holidays/holidays,
     Hotel, Shopping, Lebensmittel) -> lower-cased, lebensmittel/restaurant
     folded into groceries/restaurants, then re-aggregated per
     year_month/category. pos_perc/ecom_perc are recomputed as amount-weighted
     averages (not summed), since they are percentages, not amounts.
   - The noisy `12-2020` stub (~CHF 370 total, one month before the stated
     2021-2023 window) is dropped entirely.
   -> data/processed/sow_category_clean.csv

Caveat: this file only has month/category-level aggregates, not customer-level
detail, so when duplicate-case rows are merged, n_customers/n_transasctions are
summed as a best-effort approximation. If the same customer happened to appear
under both the mislabeled and the correct casing in the same month (unlikely
given how small these rows are), they'd be counted twice. Given the volumes
involved (a few thousand CHF against multi-million-CHF monthly totals), this
does not meaningfully affect any of the SOW analysis.
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

CATEGORY_ALIASES = {"lebensmittel": "groceries", "restaurant": "restaurants"}


def clean_customer_data():
    df = pd.read_csv(RAW / "customer_data.csv")
    before_cols = df.shape[1]

    moves = {"cat_lebensmittel": "cat_groceries", "cat_restaurant": "cat_restaurants"}
    for src, dst in moves.items():
        moved_amount = df[src].sum()
        affected = int((df[src] > 0).sum())
        df[dst] = df[dst] + df[src]
        df = df.drop(columns=[src])
        print(f"  merged {src} -> {dst}  (CHF {moved_amount:,.2f} across {affected} customer(s))")

    out_path = PROCESSED / "customer_data_clean.csv"
    df.to_csv(out_path, index=False)
    print(f"[customer_data] {before_cols} -> {df.shape[1]} columns, {len(df)} rows")
    print(f"[customer_data] written to {out_path.relative_to(ROOT)}")
    return df


def clean_sow_category():
    df = pd.read_csv(RAW / "sow_category.csv")
    before_rows = len(df)

    def parse_ym(s):
        m, y = s.split("-")
        return int(y) * 12 + int(m)

    df["_ym_sort"] = df["year_month"].apply(parse_ym)
    cutoff = parse_ym("12-2020")

    dropped = df[df["_ym_sort"] <= cutoff]
    if len(dropped):
        print(
            f"  dropping {len(dropped)} row(s) for year_month <= 12-2020 "
            f"(CHF {dropped['total_amount'].sum():,.2f} total, noise before the 2021-2023 window)"
        )
    df = df[df["_ym_sort"] > cutoff].copy()

    before_categories = df["category"].nunique()
    df["category"] = df["category"].str.lower().str.strip().replace(CATEGORY_ALIASES)
    after_categories = df["category"].nunique()
    print(f"  normalized category casing/aliases: {before_categories} -> {after_categories} distinct categories")

    # amount-weighted average for the percentage columns, not a plain sum
    df["_pos_amount"] = df["pos_perc"] * df["total_amount"]
    df["_ecom_amount"] = df["ecom_perc"] * df["total_amount"]

    agg = (
        df.groupby(["year_month", "category", "_ym_sort"], as_index=False)
        .agg(
            n_customers=("n_customers", "sum"),
            n_transasctions=("n_transasctions", "sum"),
            total_amount=("total_amount", "sum"),
            _pos_amount=("_pos_amount", "sum"),
            _ecom_amount=("_ecom_amount", "sum"),
        )
    )
    agg["pos_perc"] = (agg["_pos_amount"] / agg["total_amount"]).round(4)
    agg["ecom_perc"] = (agg["_ecom_amount"] / agg["total_amount"]).round(4)
    agg = agg.sort_values(["_ym_sort", "category"]).drop(columns=["_ym_sort", "_pos_amount", "_ecom_amount"])

    out_path = PROCESSED / "sow_category_clean.csv"
    agg.to_csv(out_path, index=False)
    print(f"[sow_category] {before_rows} -> {len(agg)} rows")
    print(f"[sow_category] written to {out_path.relative_to(ROOT)}")
    return agg


def main():
    print("Cleaning customer_data.csv ...")
    clean_customer_data()
    print()
    print("Cleaning sow_category.csv ...")
    clean_sow_category()


if __name__ == "__main__":
    main()
