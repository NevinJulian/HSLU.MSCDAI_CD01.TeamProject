import pandas as pd
import plotly.express as px
import streamlit as st

from shared import PALETTE, apply_filters, color_map, require, sidebar_filters, top_n_plus_other

LEAKAGE_CATEGORIES = ["cash", "savings"]

st.set_page_config(page_title="Wallet leakage", layout="wide")
st.title("Wallet leakage")
st.caption(
    "Assumes cash and savings are transfers to other financial providers rather than "
    "ATM withdrawals (docs/assumptions.md, A1). leak_share is the headline, "
    "cat_savings_share the conservative variant."
)

feats = require("customer_features")
cp = require("sow_category_counterpart_clean")

filters = sidebar_filters(feats)
feats = apply_filters(feats, filters)

if feats.empty:
    st.info("No customers for the current filter.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Customers with leakage", f"{feats['has_leak'].mean():.1%}")
c2.metric("Avg leak share", f"{feats['leak_share'].mean():.1%}")
c3.metric("Avg savings share", f"{feats['cat_savings_share'].mean():.1%}")
c4.metric("Leaked amount", f"CHF {feats['leak_amount'].sum():,.0f}")

st.subheader("Where the money goes")
leak = cp[cp["category"].isin(LEAKAGE_CATEGORIES)].copy()
leak["date"] = pd.to_datetime(leak["date"])
by_group = (
    top_n_plus_other(leak, "counterpart_group", "total_amount")
    .groupby(["date", "counterpart_group"], as_index=False)["total_amount"]
    .sum()
)
fig = px.area(
    by_group,
    x="date",
    y="total_amount",
    color="counterpart_group",
    color_discrete_map=color_map(leak, "counterpart_group", "total_amount"),
)
fig.update_layout(legend_title_text="destination", yaxis_title="CHF")
st.plotly_chart(fig, width="stretch")
st.caption("Population-level and not affected by the tenure filter, which applies to customers only.")

st.subheader("Leakage by tenure")
# Ordered by mean days_active so the buckets come out in tenure order without
# restating the bin labels from src/features.py.
by_tenure = (
    feats.groupby("tenure_bucket", as_index=False)
    .agg(leak_share=("leak_share", "mean"), days=("days_active", "mean"), customers=("customer_id", "size"))
    .sort_values("days")
)
fig = px.bar(
    by_tenure,
    x="tenure_bucket",
    y="leak_share",
    hover_data=["customers"],
    color_discrete_sequence=PALETTE,
)
fig.update_layout(yaxis_tickformat=".0%", xaxis_title="tenure bucket")
st.plotly_chart(fig, width="stretch")

with st.expander("Show data"):
    st.dataframe(by_tenure, width="stretch")
