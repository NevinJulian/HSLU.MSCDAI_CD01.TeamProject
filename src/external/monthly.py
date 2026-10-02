"""Monthly tables for the external-data comparison (issue 11).

    from src.external.monthly import build_external_monthly, leakage_monthly, compare
    ext = build_external_monthly()          # external series, one row per month
    leak = leakage_monthly()                # the YAPEAL side, from the SoW files
    table = compare(ext, leak)              # correlations of levels and of changes

build_external_monthly() reads what src/external/fetch.py wrote to data/external/
plus the manual files in data/external/manual/ when they exist, and writes
data/external/external_monthly.parquet and the event calendar of src/events.py
as data/external/events.csv.
"""

import json

import numpy as np
import pandas as pd

from src import mappings as M
from src.data import load_sow, load_sow_counterpart, monthly_active
from src.events import events
from src.external.fetch import EXTERNAL

MANUAL = EXTERNAL / "manual"
START, END = pd.Timestamp("2021-01-01"), pd.Timestamp("2023-12-01")

API_FILES = ["bitcoin", "fear_greed", "snb_policy_rate", "snb_savings_rate", "fx"]
# step series: a value holds until the next change
STEP_COLUMNS = ["snb_policy_rate"]

LEAKAGE_DESTINATIONS = ["revolut", "crypto exchanges", "traditional banks", "twint"]

# Statista exports (campus licence, stay in data/): column name -> accepted file names
STATISTA = {
    "revolut_mau_europe": ["revolut_mau.xlsx", "revolt_mau.xlsx"],      # statistic 1616099, AppMagic, Europe
    "revolut_downloads_world": ["revolut_downloads_worldwide.xlsx"],  # statistic 1122668, AppMagic, worldwide
}


# --------------------------------------------------------------------------- external side
def read_google_trends(path) -> pd.DataFrame:
    """A Google Trends 'Interest over time' CSV export, monthly. Older exports
    start with a 'Category: ...' line and a blank line and name columns
    'Revolut: (Switzerland)', newer ones start with 'Time' and use topic names
    like 'Yuh - Your app. Your money.'. Columns become trends_<first word>,
    '<1' is read as 0.5."""
    with open(path, encoding="utf-8-sig") as f:
        skip = 2 if f.readline().startswith("Category") else 0
    df = pd.read_csv(path, skiprows=skip)
    df = df.rename(columns={df.columns[0]: "date"})
    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp()
    values = {c: "trends_" + "".join(ch for ch in c.split()[0].lower() if ch.isalnum()) for c in df.columns[1:]}
    for c in values:
        df[c] = pd.to_numeric(df[c].replace("<1", "0.5"))
    return df.rename(columns=values)


def read_statista(path, column: str) -> pd.DataFrame:
    """A Statista 'Statistic as Excel data file' export: sheet 'Data', month labels
    in the second column ('Mar 2015' or "Mar '15"), values in the third."""
    raw = pd.read_excel(path, sheet_name="Data", header=None, usecols=[1, 2], names=["label", column])
    raw = raw.dropna()
    labels = raw["label"].astype(str).str.strip()
    dates = pd.to_datetime(labels, format="%b %Y", errors="coerce").fillna(
        pd.to_datetime(labels, format="%b '%y", errors="coerce")
    )
    out = pd.DataFrame({"date": dates, column: pd.to_numeric(raw[column], errors="coerce")}).dropna()
    return out.reset_index(drop=True)


def build_external_monthly(write: bool = True) -> pd.DataFrame:
    """All external series joined on `date`, 2021-01 to 2023-12. Step series are
    forward-filled, every other gap stays NaN."""
    frames = []
    for name in API_FILES:
        path = EXTERNAL / f"{name}.csv"
        if not path.exists():
            raise FileNotFoundError(f"{path} missing. Run `python -m src.external.fetch` first.")
        frames.append(pd.read_csv(path, parse_dates=["date"]).set_index("date"))
    trends = MANUAL / "google_trends.csv"
    if trends.exists():
        frames.append(read_google_trends(trends).set_index("date"))
    for column, names in STATISTA.items():
        path = next((MANUAL / n for n in names if (MANUAL / n).exists()), None)
        if path is not None:
            frames.append(read_statista(path, column).set_index("date"))

    ext = pd.concat(frames, axis=1).sort_index()
    ext[STEP_COLUMNS] = ext[STEP_COLUMNS].ffill()
    ext["btc_chf_mean"] = ext["btc_usd_mean"] * ext["usd_chf"]
    ext = ext.loc[START:END]

    if write:
        ext.to_parquet(EXTERNAL / "external_monthly.parquet")
        events().to_csv(EXTERNAL / "events.csv", index=False)
    return ext


def sources() -> pd.DataFrame:
    """The sidecar JSONs as one table, for docs/external_data.md."""
    rows = [{"file": p.stem, **json.loads(p.read_text(encoding="utf-8"))} for p in sorted(EXTERNAL.glob("*.json"))]
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- YAPEAL side
def leakage_monthly() -> pd.DataFrame:
    """Per month: card spend, active customers, and per leakage destination the
    amount, its share of all card spend and the customers sending money there
    (also as % of monthly active). cash + savings, assumption A1."""
    sow, cp = load_sow(), load_sow_counterpart()
    out = sow.groupby("date")["total_amount"].sum().rename("spend").to_frame().join(monthly_active(sow))

    fin = cp[cp["category"].isin(["cash", "savings"])]
    out["leak_all_share"] = fin.groupby("date")["total_amount"].sum() / out["spend"]
    online = fin[fin["top_counterpart"].isin(M.LEAKAGE_ONLINE)]
    out["leak_online_share"] = online.groupby("date")["total_amount"].sum() / out["spend"]

    grouped = fin[fin["counterpart_group"].isin(LEAKAGE_DESTINATIONS)]
    # n_customers is per category row: a customer topping up Revolut under cash
    # and savings in the same month counts twice, as in notebooks/06_leakage
    agg = grouped.groupby(["date", "counterpart_group"]).agg(chf=("total_amount", "sum"), customers=("n_customers", "sum"))
    for dest in LEAKAGE_DESTINATIONS:
        key = dest.replace(" ", "_")
        d = agg.xs(dest, level="counterpart_group")
        out[f"{key}_chf"] = d["chf"]
        out[f"{key}_share"] = d["chf"] / out["spend"]
        out[f"{key}_customers_pct"] = d["customers"] / out["active_customers"]
    return out.fillna({c: 0 for c in out.columns if c.endswith(("_chf", "_share"))})


# --------------------------------------------------------------------------- comparison
def compare(ext: pd.DataFrame, leak: pd.DataFrame, pairs: list[tuple[str, str]], lags=(0, 1, 2),
            freq: str = "M") -> pd.DataFrame:
    """Pearson correlation for each (external, leakage) pair: of levels, and of
    changes (% change for prices, difference for rates and shares), with the
    external series leading by `lags` periods. freq "Q" averages to quarters.

    Levels of trending series correlate whatever the mechanism, read the change
    columns. n is 36 months or 12 quarters, so |r| below ~0.33 (months) or ~0.58
    (quarters) is within noise at the 5 % level."""
    both = ext.join(leak, how="inner")
    if freq == "Q":
        both = both.groupby(both.index.to_period("Q")).mean()
    rows = []
    for x, y in pairs:
        dx = both[x].pct_change() if _is_price(x) else both[x].diff()
        dy = both[y].diff()
        row = {"external": x, "leakage": y, "n": int(both[[x, y]].dropna().shape[0]), "r_level": both[x].corr(both[y])}
        for lag in lags:
            row[f"r_change_lag{lag}"] = dx.shift(lag).corr(dy)
        rows.append(row)
    return pd.DataFrame(rows).round(2)


def _is_price(col: str) -> bool:
    return col.startswith("btc_") or col in ("usd_chf", "eur_chf")


def critical_r(n: int, z: float = 1.96) -> float:
    """|r| above which a correlation is different from 0 at roughly the 5 % level."""
    return float(np.tanh(z / np.sqrt(n - 3)))
