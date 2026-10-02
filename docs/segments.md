# Customer segments

Issue #7, notebook `notebooks/07_segments.ipynb`, code in `src/segments.py`, cluster ids in `data/processed/customer_clusters.csv` (gitignored).

## Method

- 13 features per customer: log transactions, log days active, log amount per transaction, counterparts per transaction, e-commerce share, foreign share, and the spend shares of groceries, restaurants, shopping, holidays, transport, entertainment, communication. Standardised. `total_amount`, `n_counterparts` and `n_categories` left out because they correlate 0.87–0.96 with `n_transactions`
- leakage and the churn label are profile variables only, not inputs
- k-means, `n_init=10`, k from 3 to 9. k = 6 chosen: stable across seeds (ARI 0.99), Davies-Bouldin 1.5, silhouette 0.20, smallest cluster 238. k = 5 is unstable (ARI 0.7), k = 7+ only splits the biggest cluster
- cluster ids renumbered by median spend so 0 is always the largest spender
- checks: HDBSCAN marks 82 % of customers as noise and agrees with k-means on the rest (ARI 0.94). Ward on a 1 000 sample agrees on the big segment and splits the small online ones differently (ARI 0.43)

## The six segments

| id | name | customers | % customers | % spend | median CHF | median tx | median days | e-com | foreign | leak share | churn |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | main account | 2 431 | 44 % | 78 % | 8 773 | 258 | 624 | 0.23 | 0.21 | 0.13 | 32 % |
| 1 | travel card | 469 | 8 % | 11 % | 6 941 | 112 | 453 | 0.37 | 0.66 | 0.06 | 36 % |
| 2 | entertainment only | 323 | 6 % | 5 % | 542 | 13 | 145 | 1.00 | 0.19 | 0.06 | 68 % |
| 3 | online & top-ups | 999 | 18 % | 4 % | 398 | 7 | 112 | 0.95 | 0.58 | 0.35 | 73 % |
| 4 | subscriptions only | 238 | 4 % | 1 % | 184 | 13 | 244 | 1.00 | 0.81 | 0.03 | 71 % |
| 5 | tried once | 1 116 | 20 % | 0 % | 95 | 6 | 37 | 0.00 | 0.00 | 0.05 | 88 % |

Churn rate on the labelled subset of each segment. Leak share = mean `(cat_cash + cat_savings) / spend`, assumption A1.

- **main account**: everything in the mix, 78 % of all spend, the bank's actual customers
- **travel card**: holidays are 36 % of spend, two thirds of transactions abroad. Used when travelling, not at home
- **entertainment only**: 88 % of spend in entertainment (gambling, streaming, gaming), all online
- **online & top-ups**: the feeder segment. Few transactions, almost all online, a third of spend to Revolut, crypto exchanges and cash. Savings share 0.13, ten times the main account
- **subscriptions only**: Apple, Spotify, telco, nothing else
- **tried once**: a grocery shop or two in the first month, then nothing

Three segments (online & top-ups, subscriptions only, tried once) never made YAPEAL their card: 42 % of customers, 5 % of spend, 73 to 88 % churn.

## What YAPEAL could do

| segment | action |
|---|---|
| main account | keep. Retention triggers only when leakage rises |
| travel card | turn it into the main account: salary or standing-order nudge after a trip, fair FX |
| entertainment only | responsible-banking check, gambling limits. Not a growth segment |
| online & top-ups | interest on balances or an in-app savings / crypto product, otherwise they finish moving to Revolut |
| subscriptions only | leave alone, low value and low cost |
| tried once | an onboarding problem, not a retention problem. First-week activation |

## Used by

- #8 churn: cluster id as an optional feature (not yet added)
- #10 value: value at risk per segment
- #12 dashboard: segments page
