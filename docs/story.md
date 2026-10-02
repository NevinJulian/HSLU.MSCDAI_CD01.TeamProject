# Story: why YAPEAL, why wallet leakage

Issue #3, notebook `notebooks/03_story.ipynb`, charts in `figures/story/`, chart functions in `src/plots.py`. This is the first third of the presentation: one statement per slide, one chart per statement. Numbers below are the ones to use on slides.

## Stakeholder and premise

**Stakeholder: YAPEAL AG, head of retail product / CRM.** The syllabus asks for recommendations for YAPEAL, and YAPEAL is a young, growing neobank. Context 2026: YAPEAL has shifted its focus to corporate banking, the retail app runs without marketing (IFZ Retail Banking Blog 2026, issue #11). Our pitch: what the 2021–2023 data already said about why retail customers leave.

**Premise: share of wallet turned around.** Classic share of wallet asks how much of a customer's grocery budget goes to Coop. We ask how much of the customer's *financial* wallet stays at YAPEAL. The card data shows money moving on to Revolut, crypto exchanges and other banks. We call this wallet leakage.

**Opening hook:** "Every month, one in twenty of your active customers sends money to Revolut." Used on the first slide, picked up again at S5.

## Statements

| # | Statement | Chart |
|---|---|---|
| S1 | YAPEAL more than doubled its monthly active customers: 689 in January 2021, 1 540 in December 2023, peak 1 648 in July 2023 | `s1_active_customers` |
| S2 | `cash` and `savings` together are 14.2 % of all card spend, more than restaurants (13.3 %) | `s2_category_shares` |
| S3 | `cash` is not cash: every named counterpart of `cash` and `savings` is another financial or payment provider. Revolut alone is 24 % of the two categories | `s3_cash_is_not_cash` |
| S4 | Leakage grows. Revolut's share of all card spend rose from 3.0 % to 4.2 % (2021Q1 → 2023Q4), traditional banks from 0.9 % to 2.6 % | `s4_leakage_grows` |
| S5 | It is steady, not a one-off: on average 5.3 % of monthly active customers top up Revolut, every month for 36 months, no trend | `s5_one_in_twenty` |
| S6 | Customers who send a large part of their spend to other providers churn more, also at equal tenure: from 18 % to 43 % among customers with any leakage | `s6_churn_ladder` |
| S6b | We tested our own finding: the first reading (`savings` only, up to 70 %) overstated the effect. The direction holds, the size does not | `s6b_ladder_correction` |
| S7 | Classic share of wallet works in the data (Coop 30 → 25 %, fuel 40 → 27 % of transport), but it cannot be linked to customers | `s7_alternatives` |
| S8 | Three files, one bridge: only `category` connects the customer file and the monthly counterpart file, and only `cash`/`savings` has homogeneous counterparts. Wallet leakage is the only topic that uses all three files | `s8_data_map` |

## Details per statement

**S1.** Spend per active customer is flat at about 1.4–1.6k CHF a month, so volume growth is customer growth. That is why every later chart uses shares, not CHF totals. The line ends below the peak; the spike in March 2021 is a single month and not explained by the data.

**S2.** The split between `cash` (11.9 %) and `savings` (2.3 %) is not meaningful because Revolut was relabelled from one to the other (see S6b). Always read the two together.

**S3.** Named counterparts: Revolut 24 %, Binance 6 %, PostFinance 6 %, Kantonalbank 4 %, UBS 4 %, Coinbase 3 %, Twint 2 %. `other` is 51 %. Revolut, Binance, Coinbase and Twint are 100 % e-commerce, i.e. card top-ups. The bank rows are point of sale at 140–250 CHF per transaction and could be ATM withdrawals (assumption A1).

**S4.** Crypto follows the market: 1.1 % in 2021Q1, peak 2.7 % in 2021Q4, 0.8 % in 2023Q4. All `cash` + `savings` 11.0 → 16.6 %, online only (Revolut, crypto, Twint) 4.4 → 5.1 %. Revolut volume +130 % from 2021 to 2023: active customers +50 %, CHF per topping-up customer +57 %, share of customers topping up flat. Bitcoin price and SNB rate belong next to this chart as separate panels, not on a second axis (issue #11).

**S5.** Range 4.1–7.4 %. A topping-up customer sends a median of about 980 CHF a month in about three transactions. During the relabelling (Dec 2021 – Apr 2022) customers with transactions in both categories are counted twice; the corrected mean is between 4.9 % and 5.3 %. "One in twenty" holds.

**S6.** Train set, customers active more than a year, n = 1 838, overall churn 30 %. Leakage share = (`cat_cash` + `cat_savings`) / category sum (`leak_share`).

| leakage share | 0 | 0–5 % | 5–20 % | 20–50 % | > 50 % |
|---|---|---|---|---|---|
| churn | 34 % | 18 % | 24 % | 38 % | 43 % |
| n | 827 | 373 | 308 | 186 | 144 |

The zero bin is shown in grey: it mixes customers who never move money out with customers who barely used the card. A little leakage marks an engaged customer, a lot marks a pass-through account. With controls (tenure, activity, spend, e-commerce, foreign use) the odds of churn rise by 10 % per +10 points of leakage share (OR 1.10, 95 % CI 1.07–1.14); leakers churn more in 18 of 21 tenure × spend strata, +5.8 points pooled (`docs/leakage_churn.md`).

Wording for the slide: "customers who send a large part of their spend to other providers churn more, also at equal tenure". Not "leakage causes churn".

**S6b.** Revolut moved from `savings` to `cash` between December 2021 and May 2022 (both categories in parallel from January to April 2022, `savings` empty from May on). The customer file has no dates but uses the same labels, so `cat_savings` holds the Revolut transfers made before the switch. Churned customers were active earlier, so `savings` alone partly measures *when* a customer was active: among customers with leakage, 20 % of the churners' leakage sits in `savings`, 9 % of the stayers'.

| | 0 | 0–5 % | 5–20 % | 20–50 % | > 50 % |
|---|---|---|---|---|---|
| `savings` only | 29 % (n = 1 553) | 27 % (149) | 44 % (75) | 54 % (41) | 70 % (20) |
| `cash` + `savings` | 34 % (827) | 18 % (373) | 24 % (308) | 38 % (186) | 43 % (144) |

The corrected ladder is flatter and rests on more customers per bar. The 29 → 70 % figure in `Projectdescription.md` and in the first version of `docs/leakage_churn.md` is superseded by this.

**S7.** Groceries: Coop 29.8 → 25.1 %, Migros 25.1 → 21.9 %, discounters 12.3 → 13.6 % of grocery spend. Transport: fuel 40.2 → 26.7 %, public transport 12.0 → 14.3 % of transport spend. Each line is a 36-point time series without customers.

**S8.** 5 576 customers, 3 903 with a churn label (70 %), 1 673 to predict. 36 months, 92 named counterparts.

## Expected questions

| question | answer |
|---|---|
| Does leakage cause churn? | We do not claim that. Without per-customer dates the money may leave after the decision to leave (winding down the account). Leakage is a warning signal |
| `other` is half of `cash` + `savings`, what is it? | Counterparts below the threshold of 1 000 transactions, content unknown. Conclusions rest on the named counterparts |
| Are the bank rows transfers or ATM withdrawals? | Unclear (point of sale, 140–250 CHF per transaction). The online-only reading is the conservative one and still grows |
| Why read `cash` and `savings` together? | Revolut was relabelled between the two in 2021/22. See S6b |
| How strong is the churn signal? | Moderate. In the churn model it adds little (AUC 0.855 → 0.858), usage volume explains most. The value is in identifying the segment |
| What does "churned" mean? | Not documented in the data, asked the lecturer (assumption A2) |
| When does the customer extract end? | `days_active` reaches 964 of 1 095 days, so probably around August 2023 |

## Open questions for the lecturer

- What exactly does "churned" mean?
- When does the customer extract end?
- Are the `cash` counterparts transfers or card top-ups?
