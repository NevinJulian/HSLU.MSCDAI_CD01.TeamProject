# Share of wallet: findings

Source: `notebooks/05_sow.ipynb` (issue 05). Data: `sow_category.csv` and `sow_category_counterpart.csv`, Jan 2021 – Dec 2023, aggregated over all customers. Counterpart shares are taken over merchant spend only (payment providers sumup, paypal, twint and the financial providers are left out, see `docs/data_preparation.md` §6). Leakage numbers assume that `cash` and `savings` are transfers, see `docs/assumptions.md` A1.

## The 5 numbers we quote

| # | Number | What it says | Where |
|---|---|---|---|
| 1 | **49 %** of grocery spend goes to Coop + Migros (top 3: 53 %, HHI 0.26). In restaurants the top 3 hold **7 %** and `other` 90 % | Groceries is a two-player market, restaurants is not. A grocery cashback with Coop or Migros reaches half of the category, nothing comparable exists in restaurants | concentration table |
| 2 | Cash + savings rise from **7.8 % + 5.4 %** of card spend in 2021 to **14.6 % + 0.8 %** in 2023, shopping falls from **20.6 %** to **17.4 %**, groceries from **20.8 %** to **16.1 %** | The wallet shifts from everyday spend to money moved out of YAPEAL | category share per year |
| 3 | Discounters (Lidl, Aldi, Denner) grow from **12.1 %** (2021) to **13.5 %** (2023) of grocery spend, forecast **13.9 %** for 2024 (80 % band 13.2–14.5 %, ETS, backtest MAE 1.0 pp). Coop slips from 27.3 % to 25.6 %, Migros from 23.7 % to 21.9 % | Slow, steady move to discounters while food prices rise (real vs nominal pending issue 11) | groceries stacked area, forecast chart |
| 4 | Revolut takes **2.9 %** of card spend in 2021, **3.9 %** in 2023, forecast **4.2 %** for 2024 (80 % band 3.7–4.8 %, ETS, backtest MAE 0.51 pp) | The single largest leakage counterpart keeps growing, input for issue 06 | forecast chart |
| 5 | Gambling (Interwetten, Swiss Casinos, mycasino.ch, Swisslos, jackpots.ch) is **17.5–30.5 %** of entertainment merchant spend per quarter, 18–25 % on a like-for-like basis without jackpots.ch | One chart for the responsible-banking slide | gambling chart |

## Supporting results

- **Seasonality** (spend per active customer, month-of-year index): December peaks in shopping (1.26), cash (1.34), groceries (1.12). July peaks in holidays (1.59), restaurants (1.40), transport (1.24). Excluding 2021 (Covid) the peaks stay in the same months but flatten (holidays 1.43, restaurants 1.26).
- **Forecast models**: seasonal naive, ETS (additive, damped trend, additive season) and SARIMA(1,0,0)(0,1,0)12, backtest on the last 6 months. Best MAE: Coop 0.30 pp (ETS), Migros 0.76 pp (SARIMA), discounters 1.00 pp (ETS), Revolut 0.51 pp (ETS, all three tie). With 6 test points the ranking is noisy, all models are within a few tenths of a point.
- **Grocery share per customer** (optional): gradient boosting on behaviour features, customers with ≥ 10 transactions, CV R² = 0.46. Big grocery wallets are customers who pay at the till (POS share Q5: 34 % groceries vs 5 % in Q1), with small tickets (amount per transaction Q1: 31 % vs 8 % in Q5) and little foreign use (Q1: 34 % vs 8 % in Q5).
- **Category table** in the notebook: total spend, share of active customers, top counterpart, top-3 concentration, POS vs e-com and trend 2021 → 2023 for all 16 categories.

## Open

- External series (LIK food index, fuel prices, events) from issue 11 are not in the repo yet. Once they are: deflate grocery spend per customer with the LIK food index (real vs nominal discounter gain) and put fuel prices next to the transport fuel share. The discounter share itself is a ratio within groceries and does not need deflating.
- Prophet not used, statsmodels covers the three models.
