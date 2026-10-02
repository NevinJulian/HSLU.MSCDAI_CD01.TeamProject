import pandas as pd
import plotly.express as px
import streamlit as st

from shared import PALETTE, apply_filters, require, sidebar_filters

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")

feats = require("customer_features")
sow = require("sow_category_clean")

filters = sidebar_filters(sow)
sow = apply_filters(sow, filters)

labelled = feats[feats["split"] == "train"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Customers", f"{feats['customer_id'].nunique():,}")
c2.metric(
    "Spend per customer",
    f"CHF {feats['total_amount'].sum() / max(feats['customer_id'].nunique(), 1):,.0f}",
)
c3.metric("Churn rate", f"{labelled['churned'].mean():.1%}")
c4.metric("Leakage %", f"{feats['leak_share'].mean():.1%}")

st.subheader("Active customers over time")
sow["date"] = pd.to_datetime(sow["date"])
# n_customers is per category; the max across categories in a month is a lower
# bound on monthly active customers (see src/data.py:monthly_active).
active = sow.groupby("date")["n_customers"].max().reset_index(name="active_customers")
fig = px.line(active, x="date", y="active_customers", color_discrete_sequence=PALETTE)
st.plotly_chart(fig, width="stretch")

with st.expander("Show data"):
    st.dataframe(active)
