from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"


@st.cache_data
def load(name: str) -> pd.DataFrame:
    """Load a cleaned table from data/processed."""
    path = PROCESSED / f"{name}.parquet"
    if not path.exists():
        path = PROCESSED / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"{name} not found in {PROCESSED}. Run `python src/clean_data.py` first."
        )
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)


def require(name: str):
    """Load a table, or render a friendly message and stop the page."""
    try:
        return load(name)
    except FileNotFoundError as exc:
        st.warning(str(exc))
        st.stop()


def sidebar_filters(df: pd.DataFrame) -> dict:
    """Render the global filters and keep them in session_state.

    "category" (sow_category*) and "tenure_bucket" (customer_features) are the
    only grouping columns the processed tables currently expose; "cluster"
    will apply once the segments table (a later issue) lands.
    """
    st.sidebar.header("Filters")

    defaults = {"categories": [], "clusters": [], "tenure": []}
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)

    filters = {}
    if "category" in df.columns:
        filters["categories"] = st.sidebar.multiselect(
            "Category", sorted(df["category"].dropna().unique()), key="categories"
        )
    if "cluster" in df.columns:
        filters["clusters"] = st.sidebar.multiselect(
            "Cluster", sorted(df["cluster"].dropna().unique()), key="clusters"
        )
    if "tenure_bucket" in df.columns:
        filters["tenure"] = st.sidebar.multiselect(
            "Tenure", sorted(df["tenure_bucket"].dropna().unique()), key="tenure"
        )
    return filters


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    out = df
    if filters.get("categories") and "category" in out.columns:
        out = out[out["category"].isin(filters["categories"])]
    if filters.get("clusters") and "cluster" in out.columns:
        out = out[out["cluster"].isin(filters["clusters"])]
    if filters.get("tenure") and "tenure_bucket" in out.columns:
        out = out[out["tenure_bucket"].isin(filters["tenure"])]
    return out