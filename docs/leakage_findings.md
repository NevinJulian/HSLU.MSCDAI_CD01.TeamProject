# Wallet leakage

Issue #6, notebook `notebooks/06_leakage.ipynb`, charts in `figures/leakage/`, chart functions in `src/plots.py`, event markers in `src/events.py`.

Leakage = spend in `cash` + `savings`, whose named counterparts are all financial providers (assumption A1). Conservative reading: only the 100 % e-commerce counterparts, Revolut, Binance, Coinbase, Twint, which are card top-ups by construction. The bank rows (PostFinance, UBS, Kantonalbank) are point of sale with 140–250 CHF per transaction and could be ATM withdrawals.

## Numbers

| | 2021Q1 | 2023Q4 |
|---|---|---|
| Revolut, % of all card spend | 3.0 | 4.2 |
| crypto exchanges (Binance, Coinbase) | 1.1 (peak 2.7 in 2021Q4) | 0.8 |
| bank rows (PostFinance, UBS, Kantonalbank) | 0.9 | 2.6 |
| Twint | 0.3 | 0.1 |
| online only (Revolut + crypto + Twint) | 4.4 | 5.1 (range 4.4–6.6) |
| all cash + savings (A1) | 11.0 | 16.6 |

- 5.3 % of monthly active customers top up Revolut in a given month, range 4.1–7.4 %, no trend. A topping-up customer sends a median 981 CHF a month in about three transactions
- Revolut amount +130 % from 2021 to 2023: active customers +50 %, CHF per topping-up customer +57 %, share of customers topping up −3 %. It is not spreading, the customers who do it are sending more
- crypto follows the market: peaks in 2021Q2 and 2021Q4 (bitcoin highs), down to under 1 % after the 2022 crashes
- average transfer per transaction rises for Revolut over the three years, stays flat for the banks
- customer side: 44 % of customers have any cash/savings activity, 32 % above 5 % of their spend, 12 % above 50 %. Leakage share is highest in the shortest tenure buckets (the online & top-ups segment from #7)
- forecast: damped-trend exponential smoothing on the monthly Revolut share continues the slow rise to about 4.4 % by end 2024. Backtest MAE 0.5 points, same as a seasonal naive guess, so direction only

## Charts

| file | slide |
|---|---|
| `01_active_customers` | growing neobank |
| `02_category_shares` | where the money goes, cash and savings highlighted |
| `03_financial_counterparts` | cash is not cash |
| `04_leakage_by_destination` | leakage grows, four lines per quarter |
| `05_leakage_two_readings` | A1 vs online only |
| `06_revolut_users` | one in twenty, monthly bars |
| `07_transfer_size` | CHF per transaction by destination |
| `08_decomposition` | more customers or more per customer |
| `09_customer_leakage` | distribution and by tenure |
| `10_revolut_forecast` | 2024 direction |

## Not done

External overlays (bitcoin price, SNB rate) need a network the sandbox did not have. `src/events.py` holds the event dates for markers, `plots.add_event_markers(ax, "crypto")` draws them. The bitcoin and SNB series are one `yfinance` / `data.snb.ch` download each, issue #11.
