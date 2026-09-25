# Assumptions and decisions

Things we decided without being able to prove them from the data or the course material. One entry per decision, newest at the bottom. When an entry is confirmed or overturned, change its status and add the source, do not delete it.

Format: what we assume, what speaks for it, what speaks against it, what changes if it is wrong, status.

---

## A1 · `cash` and `savings` are money moved to other financial providers

**Assumption.** Every transaction in the categories `cash` and `savings` is money leaving YAPEAL for another financial provider (neobank, crypto exchange, bank), not a cash withdrawal at an ATM. `leak_share = (cat_cash + cat_savings) / category sum` therefore measures wallet leakage.

**For.**
- The named counterparts of both categories are financial providers only: Revolut, Binance, Coinbase, PostFinance, UBS, Kantonalbank, Twint. No retailer, no ATM operator appears.
- All of `savings` and the Revolut, Binance, Coinbase and Twint rows in `cash` are 99–100 % e-commerce, which is what a card top-up of an app looks like.
- Revolut moves from `savings` to `cash` in 2022Q1, so the two categories are treated as one group by the source as well.

**Against.**
- The PostFinance, Kantonalbank and UBS rows in `cash` are 0–12 % e-commerce with 140–250 CHF per transaction, and `other` in `cash` (52 % of the category) is 76 % point of sale with 233 CHF per transaction. That pattern is also consistent with ATM withdrawals at those banks' machines.
- The course material does not say how categories are assigned (MCC codes or otherwise). Asked Lukas Stolz on 25.09.2026: cannot be verified from the data.

**If wrong.** Roughly two thirds of `cash` would be real cash. Leakage would be about 5–7 % of card spend instead of 12–17 %, the "traditional banks" line in the leakage chart would become "ATM withdrawals", and `cat_savings_share` would be the clean leakage proxy while `leak_share` overstates it. The churn link stays, because it is driven by `cat_savings_share`.

**Consequence for the work.** We report both: `leak_share` as the headline and `cat_savings_share` as the conservative variant. Every slide that uses leakage numbers carries the footnote "assumes cash and savings are transfers, see A1".

**Status.** Assumed, 25.09.2026. Cannot be verified with the data available.

---

## A2 · Churn label = no transaction for about a year, evaluated after the data window

**Assumption.** `churned = True` means the customer had no card transaction for roughly twelve months, evaluated at a date after the end of the data.

**For.** The churn rate falls monotonically with `days_active` (94 % at ≤ 7 days, 8 % at > 30 months). Customers with `days_active` > 730 are still 29 % churned, which is impossible if the label were "no transaction in the last 12 months of the data window", so the label must have been set later.

**Against.** No definition in the course material. Asked Lukas Stolz on 25.09.2026, no definition available.

**If wrong.** The interpretation of "churn" in the story changes, the model does not: the `no_tenure` feature set reaches the same accuracy as the full set, so the predictions do not rest on the tenure definition.

**Status.** Assumed, 25.09.2026.

---

## A3 · The customer extract ends around August 2023

**Assumption.** `days_active` maxes at 964 while the SoW files span 1 095 days (Jan 2021 to Dec 2023). We assume the customer table was extracted about four months before the SoW tables and treat both as covering "2021–2023".

**If wrong.** Per-customer numbers (spend per month, tenure) are off by a few percent. No conclusion depends on it.

**Status.** Assumed, open question for the coaches.

---

## A4 · `n_customers` can be summed when merging category spellings

**Assumption.** When `Groceries` and `groceries` rows of the same month are merged, `n_customers` is summed, which double counts a customer that appeared under both spellings.

**For.** The capitalised rows hold 1–6 customers and a few hundred CHF against monthly totals in the thousands of customers and millions of CHF.

**If wrong.** Monthly active customers are overstated by at most a handful per month.

**Status.** Decided, 21.09.2026, in `src/data.py`.

---

## A5 · `cat_salary` stays a category of its own

**Assumption.** 23 customers have 4–1 312 CHF in `cat_salary`. We do not know what a salary card transaction is and leave the column as it is rather than folding it into another category.

**If wrong.** Nothing, the amounts are too small to move any share.

**Status.** Decided, 21.09.2026.

---

## A6 · Monthly active customers = max of `n_customers` over categories

**Assumption.** The SoW files have no overall active-customer count. We use the largest category count of a month (usually groceries) as a lower bound and call it "monthly active customers".

**If wrong.** Growth rates are right, absolute levels are a lower bound. Shares and per-customer figures use the same denominator throughout, so comparisons over time hold.

**Status.** Decided, 21.09.2026, `monthly_active()` in `src/data.py`.
