import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import style  # noqa: E402

# Issue 12 chart standards: at most four named series, the rest "other", and one
# colour per entity that does not move when a filter changes the set of series.
PALETTE, GREY, OTHER, MAX_SERIES = style.C, style.GREY, "other", 4

SOURCES = {
    "processed": (ROOT / "data" / "processed", "Run `python src/clean_data.py` first."),
    "results": (ROOT / "results", "Run notebooks/08_churn.ipynb first."),
}


@st.cache_data
def load(name: str, source: str = "processed") -> pd.DataFrame:
    """Load a table from data/processed (cleaned tables) or results (model output)."""
    folder, hint = SOURCES[source]
    path = folder / f"{name}.parquet"
    if not path.exists():
        path = folder / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{name} not found in {folder}. {hint}")
    return pd.read_parquet(path) if path.suffix == ".parquet" else pd.read_csv(path)


def require(name: str, source: str = "processed"):
    """Load a table, or render a friendly message and stop the page."""
    try:
        return load(name, source)
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


def top_n_plus_other(df: pd.DataFrame, key: str, value: str, n: int = MAX_SERIES) -> pd.DataFrame:
    """Keep the n largest values of `key` by `value`, fold everything else into "other"."""
    keep = df[df[key] != OTHER].groupby(key)[value].sum().nlargest(n).index
    return df.assign(**{key: df[key].where(df[key].isin(keep), OTHER)})


def color_map(df: pd.DataFrame, key: str, value: str) -> dict:
    """One colour per `key`, ranked by total `value` over the *unfiltered* table so a
    group keeps its colour when a filter changes which groups are on screen."""
    ranked = df[df[key] != OTHER].groupby(key)[value].sum().sort_values(ascending=False)
    return {**{k: PALETTE[i % len(PALETTE)] for i, k in enumerate(ranked.index)}, OTHER: GREY}
