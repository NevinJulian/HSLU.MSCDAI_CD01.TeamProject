# External data

Issue #11, notebook `notebooks/11_external_data.ipynb`, code in `src/external/`, figures in `figures/external/`.

Question: do outside events explain *when* money leaves YAPEAL? Each external series is compared with its counterpart in the SoW files (`src/external/monthly.py:leakage_monthly`). Not used for the churn model, and not compared with churn: the churn label has no date (A2).

```bash
python -m src.external.fetch     # downloads to data/external/, no keys needed
```

`build_external_monthly()` joins everything on `date` (month start) for 2021-01 to 2023-12 and writes `data/external/external_monthly.parquet` and `data/external/events.csv` (the calendar from `src/events.py`). The source CSVs stay in `data/external/` (gitignored), each with a sidecar JSON holding source URL, licence and fetch time.

## Sources

| File | Series | Source | Licence | Transformation | Used for |
|---|---|---|---|---|---|
| `bitcoin` | BTC price, monthly mean and month-end close | Binance public API, `api.binance.com/api/v3/klines`, BTCUSDT, daily | public market data, no key | daily close in USDT (≈ USD), mean and last per month; `btc_chf_mean` = mean × USD/CHF | crypto outflows |
| `fear_greed` | Crypto Fear & Greed index, 0–100 | alternative.me, `api.alternative.me/fng/?limit=0`, daily | free with attribution | monthly mean | crypto outflows |
| `snb_policy_rate` | SNB policy rate, % | SNB data portal, cube `snbgwdzid`, item `LZ`, daily | SNB terms of use, cite the source | last value of the month, forward-filled | bank outflows |
| `snb_savings_rate` | Mean rate on private savings deposits (`S1`) and payment accounts (`S0`), % | SNB data portal, cube `zikrepro`, reference value `M` (mean), monthly | as above | none | bank outflows |
| `fx` | CHF per USD and per EUR | SNB data portal, cube `devkum`, `M0` (monthly average) | as above | none | BTC in CHF, Revolut as a travel card |

First fetched 2026-10-02. Yahoo Finance (`yfinance`) was rate-limited and CoinGecko's free tier only reaches back one year, hence Binance.

The SNB policy rate changed five times in the window: −0.75 % until 2022-06-16, then −0.25 % (2022-06-17), 0.5 % (2022-09-23), 1.0 % (2022-12-16), 1.5 % (2023-03-24), 1.75 % (2023-06-23). Dates are when the new rate applied, the day after each SNB decision.

## Manual sources

Read from `data/external/manual/` when present.

| File | What | How | Licence | Status |
|---|---|---|---|---|
| `google_trends.csv` | Search interest Revolut, Yuh, Neon, Switzerland, monthly, 100 = peak of the query | trends.google.com → Explore, Switzerland, 2020-12 to 2023-12, the three in one query (same scale), *Download CSV*. Read by `read_google_trends()`, columns `trends_revolut`, `trends_yuh`, `trends_neon` | Google Trends, cite, values relative | downloaded 2026-10-02. Revolut and Yuh were picked as topics. **Neon is not usable**: the topic "neon Switzerland AG" drops to 10 in April 2022 and to about 4 from March 2023 on, a change in Google's topic mapping rather than interest. Re-download with the search term "neon bank" if Neon is needed |
| `revolut_mau.xlsx` (or `revolt_mau.xlsx`) | Revolut monthly active users, **Europe**, 2015-03 to 2025-05 | Statista statistic 1616099 (source AppMagic, published June 2025), *Statistic as Excel data file*. Read by `read_statista()`, column `revolut_mau_europe` | campus licence, no redistribution, stays in `data/` | downloaded 2026-10-02, 123 months, no gaps |
| `revolut_downloads_worldwide.xlsx` | Revolut app downloads per month, **worldwide**, 2015-03 to 2026-06 | Statista statistic 1122668 (source AppMagic, published July 2026), as above, column `revolut_downloads_world` | as above | downloaded 2026-10-02, 136 months, no gaps |
| Statista: digital wallet apps by MAU, Switzerland, April 2025 (statistic 1614889) | one snapshot, outside the window, excludes TWINT | | | not used |

## Company context (no time series)

YAPEAL is not listed and publishes no annual report we could find. Revolut serves Swiss customers through Revolut Ltd (UK e-money institution), its annual reports have no country breakdown.

| Fact | Value | Source |
|---|---|---|
| YAPEAL FY 2020/21 (to June 2021): loss, revenue, staff | CHF 4.2 m loss, CHF 120 000 revenue, about 50 employees; customer deposits about CHF 2.8 m (31.03.2021) | finews.ch, 23.07.2021, from the company's business report |
| YAPEAL strategy | shift from B2C to B2B4C (banking infrastructure for partners), Abacus invested in 2021, 2022 and 2023 | moneytoday.ch, 13.06.2023 |
| Revolut in Switzerland | about 600 000 customers (June 2023), against Neon 150 000, Yuh 130 000, Zak 60 000 | moneytoday.ch, 13.06.2023 |
| Revolut retail customers worldwide | 26.2 m end of 2022, 38.0 m end of 2023, 45 m June 2024 | Revolut annual reports 2022 and 2023 (assets.revolut.com/pdf/annualreport2022.pdf, …2023.pdf) |

For scale: the YAPEAL extract has 5 576 card customers.

## Method

- **changes, not levels.** Levels of trending series correlate whatever the mechanism. `compare()` reports the level correlation and the correlation of changes (% change for prices, difference for rates and shares), with the external series leading by 0, 1 or 2 months, monthly and quarterly
- **n = 36.** |r| above 0.33 for monthly changes (n = 35) and 0.60 for quarterly changes (n = 11) is different from zero at about the 5 % level (`critical_r()`). Several pairs share one trend, so read a single significant r with care
- **rates as periods.** Five rate steps are too few for a change correlation, the notebook compares period means: negative rates (2021-01 to 2022-05), hikes (2022-06 to 2022-12), positive rates (2023)
- the YAPEAL side is cash + savings by counterpart group (assumption A1). `*_customers_pct` sums `n_customers` over the cash and savings rows, a customer in both in the same month counts twice, as in `notebooks/06_leakage.ipynb`

## Findings (API sources, Google Trends, Statista, 2026-10-02)

| Driver | YAPEAL counterpart | Result |
|---|---|---|
| bitcoin price | outflows to Binance + Coinbase | **yes, with about a month's delay.** Change correlation 0.32 same month, 0.49 one month later. Share of customers paying exchanges 0.43. Peaks 2021Q2 and 2021Q4 match the bitcoin highs |
| Fear & Greed | outflows to exchanges | 0.51 one month later, nothing same month |
| bitcoin, 2022Q2 and 2023 | | **exceptions.** 2022Q2: prices and sentiment at their low, outflows up (dip buying around Terra/Luna). 2023: bitcoin +50 %, outflows kept falling, 2.0 % of spend in 2021 → 0.9 % in 2023 |
| policy rate, savings rate | outflows to banks | **no rate effect visible.** Period means rise (1.4 % → 2.1 % → 2.5 % of spend) but the rise started in 2021H1 (0.7 % → 1.7 %), 18 months before the first hike, and the share of customers paying banks peaked in late 2021 under negative rates |
| bitcoin, EUR/CHF | outflows to Revolut | no link in changes |
| Revolut MAU Europe, downloads worldwide (Statista) | outflows to Revolut | **Revolut grew four times as fast as its share of YAPEAL wallets.** 2021 → 2023 (yearly means): MAU Europe 2.0 m → 5.0 m (+151 %), downloads 0.8 m → 2.0 m a month (+154 %); Revolut's share of YAPEAL spend +34 % (2.9 % → 3.8 %), customers topping up Revolut −3 %. Level r ≈ 0.7 (shared trend), monthly change r = 0.07 |
| Google Trends vs Statista | | Swiss search interest and European MAU move together month by month (change r = 0.55), so Trends is a fair Swiss proxy for Revolut's growth |
| Google Trends "Revolut", Switzerland | outflows to Revolut | **one shared step, not a monthly link.** Search interest stepped up in early 2022 (yearly mean 50 → 77 → 79), Revolut's share of YAPEAL spend too (2.9 % → 3.7 % → 3.8 %), level r = 0.73, change r = 0.24 (noise) |
| Google Trends "Revolut" | customers topping up Revolut | **no link** (r = −0.02, flat around 5 % of active customers): Revolut's popularity rose, the same YAPEAL customers sent more |
| season | outflows to Revolut | **holiday card.** Search interest peaks in July 2022 and 2023 (100, 97), Revolut's share of spend too (4.4 %, 4.8 % against yearly means of 3.7 %, 3.8 %). No summer peak in 2021 |

Wording for the slides: "crypto outflows rise and fall with the bitcoin market", not "bitcoin causes leakage". For Revolut: "Revolut grew 2.5 times over in Europe, YAPEAL's leakage to Revolut by a third. The same one in twenty customers send more each year, especially before the summer holidays". YAPEAL is not losing its card base to Revolut at Revolut's pace; the leakage sits with a small, stable, identifiable group. For banks: "bank outflows grew from 2021, before rates moved", which argues against interest as the reason and is worth raising with YAPEAL.
