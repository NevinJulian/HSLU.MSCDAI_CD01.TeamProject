import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import style  # noqa: E402
from src.features import TENURE_LABELS  # noqa: E402

# Issue 12 chart standards: at most four named series, the rest "other", and one
# colour per entity that does not move when a control changes the set of series.
PALETTE, GREY, OTHER, MAX_SERIES = style.C, style.GREY, "other", 4

SOURCES = {
    "processed": (ROOT / "data" / "processed", "Run `python src/clean_data.py` first."),
    "results": (ROOT / "results", "Run notebooks/08_churn.ipynb first."),
}

# Customer attributes a chart can be broken down by. The SoW tables are month x
# category totals without customer ids, so these never apply to them.
BREAKDOWNS = {"tenure": "tenure_bucket", "segment": "cluster_name", "churn status": "churn_status"}
CHURN_STATUS = ["stayed", "churned", "to predict"]


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


def customers() -> pd.DataFrame:
    """customer_features with the segment attached (when notebooks/07_segments.ipynb
    has written customer_clusters) and the breakdown columns in a fixed order."""
    df = require("customer_features").copy()
    try:
        df = df.merge(load("customer_clusters"), on="customer_id", how="left")
    except FileNotFoundError:
        pass
    df["tenure_bucket"] = pd.Categorical(df["tenure_bucket"], TENURE_LABELS, ordered=True)
    df["churned"] = df["churned"].map({True: True, False: False, "True": True, "False": False}).astype("boolean")
    df["churn_status"] = pd.Categorical(
        df["churned"].map({True: "churned", False: "stayed"}).fillna("to predict"), CHURN_STATUS, ordered=True
    )
    if "cluster" in df:
        names = df.drop_duplicates("cluster").sort_values("cluster")["cluster_name"]
        df["cluster_name"] = pd.Categorical(df["cluster_name"], list(names), ordered=True)
    return df


def has_segments(df: pd.DataFrame) -> bool:
    return "cluster_name" in df


def segment_colors(df: pd.DataFrame) -> dict:
    """Segments are numbered by spend (src/segments.py), so cluster id i is always PALETTE[i]."""
    return {name: PALETTE[i % len(PALETTE)] for i, name in enumerate(df["cluster_name"].cat.categories)}


def breakdown_colors(df: pd.DataFrame, col: str) -> dict:
    if col == "cluster_name":
        return segment_colors(df)
    if col == "churn_status":
        return {"stayed": PALETTE[0], "churned": PALETTE[1], "to predict": GREY}
    return {}


def breakdown_options(df: pd.DataFrame) -> dict:
    return {k: v for k, v in BREAKDOWNS.items() if v in df}


def month_range(dates: pd.Series, key: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Slider over the months in `dates`, full window by default. Pages render it
    under the chart it drives and fill the chart from a container created earlier."""
    months = sorted(pd.to_datetime(dates).unique())
    start, end = st.select_slider(
        "Period", options=months, value=(months[0], months[-1]), format_func=lambda d: d.strftime("%b %Y"), key=key
    )
    return pd.Timestamp(start), pd.Timestamp(end)


def in_range(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    out = df.assign(date=pd.to_datetime(df["date"]))
    return out[out["date"].between(start, end)]


def latest(num: pd.Series, den: pd.Series | None = None, n: int = 3) -> float:
    """Value over the last n months of a monthly series, so a KPI is not driven
    by one noisy month (December 2023 is a spike). With `den`, the ratio of sums."""
    if den is not None:
        num = num.reindex(den.index, fill_value=0)
        return num.iloc[-n:].sum() / den.iloc[-n:].sum()
    return num.iloc[-n:].mean()


def top_n_plus_other(df: pd.DataFrame, key: str, value: str, n: int = MAX_SERIES, keep: tuple = ()) -> pd.DataFrame:
    """Keep the n largest values of `key` by `value` (plus anything in `keep`), fold
    everything else into "other"."""
    top = set(df[df[key] != OTHER].groupby(key)[value].sum().nlargest(n).index) | set(keep)
    return df.assign(**{key: df[key].where(df[key].isin(top), OTHER)})


def color_map(df: pd.DataFrame, key: str, value: str) -> dict:
    """One colour per `key`, ranked by total `value` over the *unfiltered* table so a
    group keeps its colour when a control changes which groups are on screen."""
    ranked = df[df[key] != OTHER].groupby(key)[value].sum().sort_values(ascending=False)
    return {**{k: PALETTE[i % len(PALETTE)] for i, k in enumerate(ranked.index)}, OTHER: GREY}
