"""Checks on the external-data tables. Skipped until `python -m src.external.fetch` has run."""

import pandas as pd
import pytest

from src.external.fetch import EXTERNAL
from src.external.monthly import API_FILES, build_external_monthly, compare, leakage_monthly, read_google_trends, read_statista

fetched = pytest.mark.skipif(
    not all((EXTERNAL / f"{n}.csv").exists() for n in API_FILES), reason="run python -m src.external.fetch first"
)


@fetched
def test_external_monthly_covers_the_window():
    ext = build_external_monthly(write=False)
    assert len(ext) == 36
    assert ext.index.min() == pd.Timestamp("2021-01-01") and ext.index.max() == pd.Timestamp("2023-12-01")
    assert ext.index.is_unique
    assert not ext[["btc_usd_mean", "fear_greed", "snb_policy_rate", "savings_deposit_rate", "usd_chf"]].isna().any().any()


@fetched
def test_policy_rate_steps():
    ext = build_external_monthly(write=False)
    assert ext.loc["2021-01-01", "snb_policy_rate"] == -0.75
    assert ext.loc["2023-12-01", "snb_policy_rate"] == 1.75
    assert ext["snb_policy_rate"].is_monotonic_increasing


def test_leakage_monthly_shares():
    leak = leakage_monthly()
    assert len(leak) == 36
    parts = leak[["revolut_share", "crypto_exchanges_share", "traditional_banks_share", "twint_share"]].sum(axis=1)
    assert (parts <= leak["leak_all_share"] + 1e-9).all()
    assert leak["leak_all_share"].between(0, 1).all()


def test_leakage_monthly_same_from_processed_tables():
    """The dashboard builds the leakage series from the CSVs in data/processed."""
    from src.data import PROCESSED

    sow_csv, cp_csv = PROCESSED / "sow_category_clean.csv", PROCESSED / "sow_category_counterpart_clean.csv"
    if not (sow_csv.exists() and cp_csv.exists()):
        pytest.skip("run python src/clean_data.py first")
    from_files = leakage_monthly(pd.read_csv(sow_csv), pd.read_csv(cp_csv))
    pd.testing.assert_frame_equal(from_files, leakage_monthly(), check_freq=False)


def test_read_google_trends(tmp_path):
    path = tmp_path / "google_trends.csv"
    path.write_text("Category: All categories\n\nMonth,Revolut: (Switzerland),Yuh: (Switzerland)\n2021-01,40,<1\n2021-02,42,3\n")
    df = read_google_trends(path)
    assert list(df.columns) == ["date", "trends_revolut", "trends_yuh"]
    assert df["trends_yuh"].tolist() == [0.5, 3]


def test_read_google_trends_topic_export(tmp_path):
    path = tmp_path / "google_trends.csv"
    path.write_text('"Time","Revolut","Yuh - Your app. Your money.","neon Switzerland AG"\n"2021-01-01",55,0,30\n')
    df = read_google_trends(path)
    assert list(df.columns) == ["date", "trends_revolut", "trends_yuh", "trends_neon"]
    assert df["date"].iloc[0] == pd.Timestamp("2021-01-01")


def test_compare_finds_a_known_lag():
    idx = pd.date_range("2021-01-01", periods=36, freq="MS")
    x = pd.Series(range(36), index=idx, dtype=float) ** 1.5
    ext = pd.DataFrame({"btc_chf_mean": 100 + x})
    leak = pd.DataFrame({"y": (100 + x).pct_change().shift(1).fillna(0).cumsum()}, index=idx)
    row = compare(ext, leak, [("btc_chf_mean", "y")]).iloc[0]
    assert row["r_change_lag1"] > 0.99


def test_read_statista_both_date_formats(tmp_path):
    rows = [[None, None, None], [None, "Monthly active users", None], [None, "Mar 2015", 265], [None, "Apr 2015", 437]]
    rows2 = [[None, None, None], [None, "Downloads", None], [None, "Mar '15", 175], [None, "Apr '15", 263]]
    for name, data, col in [("mau.xlsx", rows, "mau"), ("dl.xlsx", rows2, "dl")]:
        path = tmp_path / name
        with pd.ExcelWriter(path) as xw:
            pd.DataFrame([["x"]]).to_excel(xw, sheet_name="Overview", header=False, index=False)
            pd.DataFrame(data).to_excel(xw, sheet_name="Data", header=False, index=False)
        df = read_statista(path, col)
        assert df["date"].tolist() == [pd.Timestamp("2015-03-01"), pd.Timestamp("2015-04-01")]
        assert df[col].tolist() == [data[2][2], data[3][2]]
