import pandas as pd
import plotly.express as px
import streamlit as st

from shared import OTHER, apply_filters, color_map, require, sidebar_filters, top_n_plus_other

st.set_page_config(page_title="Share of wallet", layout="wide")
st.title("Share of wallet")

cat_all = require("sow_category_clean")
cp_all = require("sow_category_counterpart_clean")

filters = sidebar_filters(cat_all)
cat = apply_filters(cat_all, filters)
cp = apply_filters(cp_all, filters)

if cat.empty:
    st.info("No rows for the current filter.")
    st.stop()

cat["date"] = pd.to_datetime(cat["date"])
total = cat["total_amount"].sum()

c1, c2, c3 = st.columns(3)
c1.metric("Spend in scope", f"CHF {total:,.0f}")
c2.metric("Counterparts", f"{cp['top_counterpart'].nunique():,}")
c3.metric(
    "To financial providers",
    f"{cp.groupby('counterpart_type')['total_amount'].sum().get('financial_provider', 0.0) / total:.1%}",
)

st.subheader("Category share of wallet")
by_cat = (
    top_n_plus_other(cat, "category", "total_amount")
    .groupby(["date", "category"], as_index=False)["total_amount"]
    .sum()
)
by_cat["share"] = by_cat["total_amount"] / by_cat.groupby("date")["total_amount"].transform("sum")
cat_colors = color_map(cat_all, "category", "total_amount")
fig = px.area(
    by_cat,
    x="date",
    y="share",
    color="category",
    color_discrete_map=cat_colors,
    category_orders={"category": [c for c in cat_colors if c in set(by_cat["category"])]},
)
fig.update_layout(yaxis_tickformat=".0%", legend_title_text="category")
st.plotly_chart(fig, width="stretch")
st.caption('"other" is the remaining categories, stacked last and in grey so the named ones stay readable.')

st.subheader("Inside a category")
choices = sorted(cat["category"].unique())
choice = st.selectbox("Category", choices, index=choices.index("groceries") if "groceries" in choices else 0)

inside = cp[cp["category"] == choice].copy()
inside["date"] = pd.to_datetime(inside["date"])
# Counterpart groups only exist for cash, savings, groceries, transport and
# entertainment (src/mappings.py); elsewhere every counterpart maps to "other",
# so fall back to the counterparts themselves.
dim = "counterpart_group" if (inside["counterpart_group"] != OTHER).any() else "top_counterpart"

by_cp = (
    top_n_plus_other(inside, dim, "total_amount")
    .groupby(["date", dim], as_index=False)["total_amount"]
    .sum()
)
by_cp["share"] = by_cp["total_amount"] / by_cp.groupby("date")["total_amount"].transform("sum")
cp_colors = color_map(cp_all[cp_all["category"] == choice], dim, "total_amount")
fig = px.area(
    by_cp,
    x="date",
    y="share",
    color=dim,
    color_discrete_map=cp_colors,
    category_orders={dim: [c for c in cp_colors if c in set(by_cp[dim])]},
)
fig.update_layout(yaxis_tickformat=".0%", legend_title_text=dim.replace("_", " "))
st.plotly_chart(fig, width="stretch")
st.caption(
    f"{choice} broken down by {dim.replace('_', ' ')}, as a share of {choice} spend. "
    '"other" is the counterparts the source file never names, not a merchant.'
)

st.subheader(f"Top counterparts in {choice}")
top = (
    inside.groupby(["top_counterpart", "counterpart_type"], as_index=False)["total_amount"]
    .sum()
    .nlargest(15, "total_amount")
)
fig = px.bar(
    top,
    x="total_amount",
    y="top_counterpart",
    color="counterpart_type",
    orientation="h",
    color_discrete_map=color_map(cp_all, "counterpart_type", "total_amount"),
)
fig.update_layout(yaxis={"categoryorder": "total ascending"}, legend_title_text="type", xaxis_title="CHF")
st.plotly_chart(fig, width="stretch")

with st.expander("Show data"):
    st.dataframe(by_cat, width="stretch")
