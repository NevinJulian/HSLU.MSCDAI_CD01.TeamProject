# Project description – Customer Data Analytics (YAPEAL)

## Use case

- Stakeholder: YAPEAL, the bank that provided the data
- Classic share of wallet asks "how much of a customer's grocery budget goes to Coop". We turn it around and ask how much of the customer's financial wallet stays at YAPEAL
- The card data shows money flowing out to Revolut, crypto exchanges and traditional banks. We call this wallet leakage

## What we found in the data

- The categories `cash` and `savings` are not cash. The counterparts are Revolut, Binance, Coinbase, PostFinance, UBS
- Revolut alone grows from 3 % to 4 % of all card spend between 2021 and 2023
- Every month about 1 in 20 active customers tops up Revolut
- Among customers with more than a year of tenure, churn rises from 29 % to 70 % with the share of money sent to these providers
- Leakage is therefore a churn signal

## Research questions

1. How much money leaks and to whom (descriptive)
2. Which customer segments leak (clustering)
3. Is leakage a churn signal beyond tenure (predictive, including the churn prediction hand-in on 14.10)
4. What is it worth and what should YAPEAL do (recommendations)

## What I did so far

- Data preparation
  - categories in two spellings merged, duplicate columns merged, counterpart name variants unified, a column typo fixed
  - a stray December 2020 removed
  - gaps in the currency and country columns made explicit
  - SumUp, PayPal and Twint flagged as payment providers, not merchants
  - loaders and tests so the whole team works with the same cleaned data
- Feature engineering
  - ratios (spend per transaction, transactions per day)
  - category shares, a leakage share, international usage
  - log scales and tenure buckets
- Modelling
  - three baselines on identical folds: about 0.77 accuracy and 0.85 AUC
  - tuned LightGBM, XGBoost and CatBoost, two ensembles, SHAP, calibration
  - finding so far: churners are customers who never really started using the card. Removing the tenure features costs almost nothing, so the label is not just recency

## Goal

- A data story for YAPEAL management: where the money leaves, who leaves with it, what it is worth, and three to five concrete actions
- Delivered as a 15-minute presentation with a Streamlit dashboard on 16 or 23 October