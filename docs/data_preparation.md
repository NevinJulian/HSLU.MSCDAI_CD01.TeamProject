# Data preparation

What is cleaned, why, and what it touches. Code: `src/data.py` (loaders), `src/mappings.py` (names and groups), `src/features.py` (customer features), `tests/test_data.py` (checks). The first version of the cleaning lived in `01_clean_data.py`, the rules below extend it to all five files.

Every notebook loads the data through the loaders:

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent))   # when running from notebooks/

from src.data import load_customers, load_customer_table, load_sow, load_sow_counterpart, monthly_active
from src.features import build_customer_features
```

`python src/clean_data.py` writes the same tables as CSV to `data/processed/` for Excel or Power BI.

## The five files

| File | Grain | Rows raw → clean | Key |
|---|---|---|---|
| `customer_data.csv` | customer | 5 576 → 5 576 (42 → 40 columns) | `customer_id` |
| `customer_data_labels.csv` | customer | 3 903 | `customer_id` |
| `customer_data_predict.csv` | customer | 1 673 | `customer_id` |
| `sow_category.csv` | month × category | 647 → 559 (24 → 16 categories) | `date`, `category` |
| `sow_category_counterpart.csv` | month × category × counterpart | 4 691 → 4 495 (96 → 92 counterparts) | `date`, `category`, `top_counterpart` |

No missing values anywhere. Label ids and predict ids do not overlap and together cover all customers. The only link between the customer files and the SoW files is the category name.

## Cleaning rules

### 1. Categories in two spellings (both SoW files)

Eight categories appear a second time capitalised, sometimes in German. They hold a few hundred CHF a month and are always counterpart `other`. Example, August 2022 in `sow_category.csv`:

| year_month | category | n_customers | n_transactions | total_amount |
|---|---|---|---|---|
| 8-2022 | groceries | 1 476 | 15 306 | 334 825.33 |
| 8-2022 | Groceries | 3 | 3 | 29.80 |
| 8-2022 | restaurants | 1 271 | 10 314 | 330 839.45 |
| 8-2022 | Restaurant | 6 | 7 | 205.60 |
| 8-2022 | health | 528 | 962 | 53 121.52 |
| 8-2022 | Health | 1 | 3 | 315.00 |

Fix: lower-case, then map `lebensmittel → groceries`, `restaurant → restaurants`, `hotel → holidays`, `fitness → wellness` (`mappings.CATEGORY_ALIASES`), then re-aggregate the duplicate rows. `pos_perc` and `ecom_perc` are recomputed as amount-weighted averages, not summed. `n_customers` is summed, which can double count a customer that appeared under both spellings in the same month, but the merged rows are three orders of magnitude smaller than the category totals.

Totals affected over the whole window: Restaurant 5 230 CHF, Health 3 103, Shopping 1 362, Groceries 1 214, Hotel 1 302, Lebensmittel 1 097, Holidays 852, Fitness 126. Category and transaction totals per month are unchanged by the merge (tested).

### 2. The same duplicates as columns in `customer_data.csv`

| Column | Folded into | Customers affected | CHF |
|---|---|---|---|
| `cat_restaurant` | `cat_restaurants` | 67 | 4 583 |
| `cat_lebensmittel` | `cat_groceries` | 1 | 1 097 |
| `cat_hotel` | `cat_holidays` | 2 | 1 302 |
| `cat_fitness` | `cat_wellness` | 3 | 124 |

Example: customer 2 has `cat_restaurant` 127 next to `cat_restaurants` 10 689. After the merge `cat_restaurants` is 10 816 and the column is gone. The mapping is the same as for the SoW files, so category names match across all files.

Kept as they are: `cat_salary` (23 customers, 4 CHF to 1 312 CHF each, an odd label for card spend but no obvious home), `cat_education` (41 customers), `cat_wellness` (100 customers).

### 3. Typo `n_transasctions`

Renamed to `n_transactions` in both SoW files.

### 4. December 2020

Three rows, one customer, 378 CHF, one month before the 2021–2023 window. Dropped (`data.START`).

### 5. Counterpart spelling variants

| Variants | Kept as | Note |
|---|---|---|
| `brezelkonig`, `brezelkönig` | `brezelkonig` | 19 667 + 10 345 CHF, both groceries |
| `mcdonalds`, `mcdonald's` | `mcdonalds` | 183 773 + 57 122 CHF |
| `amazon`, `amzn` | `amazon` | `amzn` is the marketplace descriptor, 93 082 CHF shopping |
| `netflix`, `netflix.com` | `netflix` | `netflix` sits in entertainment, `netflix.com` in communication. Name unified, categories kept, the category is the merchant category of the transaction |

`burger` (127 594 CHF, restaurants) is probably Burger King but stays as is.

### 6. Counterparts that are not merchants

Some counterparts are payment providers or other banks, and a "share of wallet" for them means something different. `load_sow_counterpart()` adds `counterpart_type`:

| Type | Counterparts | Meaning |
|---|---|---|
| `payment_provider` | sumup, paypal, twint | a terminal or wallet in front of an unknown merchant. `sumup` in restaurants (235 894 CHF) is many small restaurants, not one company |
| `financial_provider` | revolut, binance, coinbase, postfinance, ubs, kantonalbank | money moved to another financial provider |
| `merchant` | everything else | |
| `other` | `other` | counterparts below 1 000 transactions |

The same company appears in several categories because the category comes from the transaction, not the company: `coop` in groceries (3.12 M), transport (489 k, Coop Pronto) and health (38 k), `migros` in groceries, shopping and restaurants, `uber` in restaurants (Uber Eats) and transport.

### 7. `cash` and `savings` are transfers, not cash

The counterparts of `cash` are revolut 22 %, binance 8 %, postfinance 7 %, kantonalbank 5 %, ubs 5 %, twint 2 %, `other` 52 %. The counterparts of `savings` are revolut and coinbase. Both categories are treated as money leaving the bank for other financial providers. This is an assumption, the bank rows could also be ATM withdrawals, see `docs/assumptions.md` A1. Revolut moves from `savings` to `cash` in 2022Q1 (recategorisation in the source), so the two categories are read together everywhere (`features.LEAKAGE_COLUMNS`, `mappings.LEAKAGE_GROUPS`).

### 8. Gaps in the currency and country columns

The currency columns cover 96.4 % of `total_amount`, the country columns 87.2 % of `n_transactions`. The rest are currencies and countries that were not listed, not missing values. Example: customer 4563, `total_amount` 162 995, listed currencies sum to 116 258, gap 46 737 CHF. Customer 2, 3 087 transactions in 31 countries, 1 904 in the seven listed ones.

Fix: `cur_other` and `country_other` hold the gap, so the columns add up to the totals again (tested).

### 9. Rounding

Category amounts are whole CHF, `total_amount` has cents. The category columns therefore sum to `total_amount` ± 3 CHF. For customers with a tiny total this makes a share against `total_amount` exceed 1 (customer with 0.55 CHF total and a 1 CHF category). Category shares in `features.py` are taken against the category sum, which is 1 by construction. Three customers (672, 682, 3518) have a category sum of 0, their shares are 0. One customer has `pos_perc + ecom_perc` = 1.01, rounding.

### 10. Things that look like problems but are not

- 506 customers have `days_active` = 1 and 426 of those have a single transaction. They are real one-day users, 9 % of the base, kept and flagged (`is_one_day`, `is_single_tx`).
- `n_customers` in `sow_category.csv` is per category. A customer active in three categories is counted three times across rows. `monthly_active()` takes the max over categories as a lower bound for monthly active customers (689 in Jan 2021, 1 646 in Jul 2023). In the counterpart file the sum of `n_customers` over counterparts exceeds the category value by 35 % on average for the same reason.
- `days_active` maxes at 964 days while the SoW window has 1 095. The customer extract probably ends around August 2023. Open question for the coaches.
- 13 customers have a `total_amount` below 1 CHF. Kept.

## Feature table (`features.build_customer_features`)

| Group | Features |
|---|---|
| activity | `tx_per_day`, `amt_per_tx`, `amt_per_day`, `cp_per_tx`, `is_one_day`, `is_single_tx` |
| breadth | `n_categories`, `n_currencies` |
| mix | `cat_<category>_share` for all 16 categories |
| leakage | `leak_amount`, `leak_share`, `has_leak` (cash + savings) |
| international | `foreign_tx_share`, `unmapped_tx_share`, `chf_share`, `foreign_cur_share` |
| scale | `log_n_transactions`, `log_total_amount`, `log_n_counterparts`, `log_days_active`, `log_n_country` |
| tenure | `tenure_bucket`, ordered: ≤7d, 8–30d, 1–3m, 3–6m, 6–12m, 12–18m, 18–24m, 24–30m, >30m |

Nothing in the feature table uses the churn label. `load_customer_table()` attaches `churned` (True/False/<NA>) and `split` (train/predict).

## Checks

`pytest` from the repo root runs 16 checks: row counts, no NaN, ids partition, category columns sum to the total, currency and country columns add up, SoW window 2021-01 to 2023-12 with 36 months, no duplicate keys, category and transaction totals unchanged by the merge, counterpart totals equal category totals per month, pos + ecom = 1, all shares in [0, 1].
