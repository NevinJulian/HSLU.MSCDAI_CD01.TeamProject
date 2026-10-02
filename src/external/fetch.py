"""Fetches the API sources to data/external/. Usage: python -m src.external.fetch

One function per source. Each writes data/external/<name>.csv with `date` (month
start) and its value columns, plus <name>.json with the source URL, licence and
fetch time. No keys needed. Manual sources (Google Trends, Statista) go into
data/external/manual/ and are read by src/external/monthly.py.
"""

import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXTERNAL = ROOT / "data" / "external"

# one month before and after the SoW window, so lags and changes have a value at the edges
FROM, TO = "2020-12-01", "2024-01-31"
TIMEOUT = 30

SNB_CSV = "https://data.snb.ch/api/cube/{cube}/data/csv/en"
SNB_LICENCE = "SNB data portal, free use with source attribution (data.snb.ch terms of use)"


def _save(df: pd.DataFrame, name: str, url: str, licence: str, note: str) -> Path:
    EXTERNAL.mkdir(parents=True, exist_ok=True)
    path = EXTERNAL / f"{name}.csv"
    df.to_csv(path, index=False)
    meta = {"source": url, "licence": licence, "note": note, "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    path.with_suffix(".json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return path


def _month_start(dates: pd.Series) -> pd.Series:
    return pd.to_datetime(dates).dt.to_period("M").dt.to_timestamp()


def _snb(cube: str, **params) -> pd.DataFrame:
    """An SNB cube as a long table: Date, the dimension columns D0, D1, ..., Value."""
    r = requests.get(SNB_CSV.format(cube=cube), params=params, timeout=TIMEOUT)
    r.raise_for_status()
    # three header lines (cube id, publishing date, blank) before the column names
    df = pd.read_csv(io.StringIO(r.content.decode("utf-8-sig")), sep=";", skiprows=3)
    return df.dropna(subset=["Value"])


# --------------------------------------------------------------------------- crypto
def fetch_bitcoin() -> Path:
    """BTC/USDT daily closes from Binance, as monthly mean and month-end close."""
    url = "https://api.binance.com/api/v3/klines"
    start = int(pd.Timestamp(FROM, tz="UTC").timestamp() * 1000)
    end = int(pd.Timestamp(TO, tz="UTC").timestamp() * 1000)
    rows = []
    while start < end:
        r = requests.get(url, params={"symbol": "BTCUSDT", "interval": "1d", "startTime": start, "endTime": end, "limit": 1000}, timeout=TIMEOUT)
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        rows += batch
        start = batch[-1][0] + 1
    daily = pd.DataFrame({"day": pd.to_datetime([b[0] for b in rows], unit="ms"), "close": [float(b[4]) for b in rows]})
    daily["date"] = _month_start(daily["day"])
    out = daily.groupby("date")["close"].agg(btc_usd_mean="mean", btc_usd_close="last").reset_index()
    return _save(out, "bitcoin", url + "?symbol=BTCUSDT&interval=1d", "Binance public market data API, no key",
                 "daily close in USDT (~USD), monthly mean and last close")


def fetch_fear_greed() -> Path:
    """Crypto Fear & Greed index (0 = extreme fear, 100 = extreme greed), monthly mean."""
    url = "https://api.alternative.me/fng/"
    r = requests.get(url, params={"limit": 0, "format": "json"}, timeout=TIMEOUT)
    r.raise_for_status()
    daily = pd.DataFrame(r.json()["data"])
    daily["day"] = pd.to_datetime(daily["timestamp"].astype(int), unit="s")
    daily = daily[daily["day"].between(FROM, TO)]
    daily["date"] = _month_start(daily["day"])
    out = daily.groupby("date")["value"].apply(lambda s: s.astype(float).mean()).rename("fear_greed").reset_index()
    return _save(out, "fear_greed", url + "?limit=0", "alternative.me, free with attribution",
                 "daily index, monthly mean")


# --------------------------------------------------------------------------- SNB
def fetch_policy_rate() -> Path:
    """SNB policy rate (cube snbgwdzid, LZ), value at month end. Changes on
    2022-06-17, 2022-09-23, 2022-12-16, 2023-03-24, 2023-06-23."""
    df = _snb("snbgwdzid", fromDate=FROM, toDate=TO)
    df = df[df["D0"] == "LZ"].assign(date=lambda d: _month_start(d["Date"]))
    out = df.groupby("date")["Value"].last().rename("snb_policy_rate").reset_index()
    return _save(out, "snb_policy_rate", SNB_CSV.format(cube="snbgwdzid"), SNB_LICENCE,
                 "daily, last value of the month, in %")


def fetch_savings_rate() -> Path:
    """Mean interest rate banks pay on private savings deposits and on payment
    accounts (cube zikrepro, D0 = M, D1 = S1 / S0)."""
    df = _snb("zikrepro", fromDate=FROM[:7], toDate=TO[:7])
    df = df[(df["D0"] == "M") & df["D1"].isin(["S1", "S0"])]
    out = df.pivot_table(index="Date", columns="D1", values="Value").rename(
        columns={"S1": "savings_deposit_rate", "S0": "payment_account_rate"}
    )
    out = out.reset_index().assign(date=lambda d: _month_start(d["Date"])).drop(columns="Date")
    return _save(out[["date", "savings_deposit_rate", "payment_account_rate"]], "snb_savings_rate",
                 SNB_CSV.format(cube="zikrepro"), SNB_LICENCE, "monthly mean over reporting banks, in %")


def fetch_fx() -> Path:
    """CHF per USD and per EUR, monthly average (cube devkum, D0 = M0)."""
    df = _snb("devkum", fromDate=FROM[:7], toDate=TO[:7])
    df = df[(df["D0"] == "M0") & df["D1"].isin(["USD1", "EUR1"])]
    out = df.pivot_table(index="Date", columns="D1", values="Value").rename(columns={"USD1": "usd_chf", "EUR1": "eur_chf"})
    out = out.reset_index().assign(date=lambda d: _month_start(d["Date"])).drop(columns="Date")
    return _save(out[["date", "usd_chf", "eur_chf"]], "fx", SNB_CSV.format(cube="devkum"), SNB_LICENCE,
                 "monthly average, CHF per 1 USD / 1 EUR")


FETCHERS = [fetch_bitcoin, fetch_fear_greed, fetch_policy_rate, fetch_savings_rate, fetch_fx]


def main() -> None:
    for fetch in FETCHERS:
        try:
            print(f"written {fetch().relative_to(ROOT)}")
        except requests.RequestException as exc:
            print(f"FAILED {fetch.__name__}: {exc}")


if __name__ == "__main__":
    main()
