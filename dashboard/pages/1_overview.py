import plotly.express as px
import streamlit as st

from shared import PALETTE, customers, has_segments, in_range, latest, month_range, require

LEAKAGE_CATEGORIES = ["cash", "savings"]

st.set_page_config(page_title="Overview", layout="wide")
st.title("Overview")

feats = customers()
sow_all = require("sow_category_clean")

kpis = st.container()
st.subheader("Active customers over time")
chart = st.container()
start, end = month_range(sow_all["date"], key="overview_period")
sow = in_range(sow_all, start, end)

# n_customers is per category; the max across categories in a month is a lower
# bound on monthly active customers (src/data.py:monthly_active). Always taken
# over all categories, a category subset would answer a different question.
monthly = sow.groupby("date").agg(active_customers=("n_customers", "max"), spend=("total_amount", "sum"))
leak = sow[sow["category"].isin(LEAKAGE_CATEGORIES)].groupby("date")["total_amount"].sum()
monthly["leak_share"] = (leak / monthly["spend"]).fillna(0)
labelled = feats[feats["split"] == "train"]

with kpis:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Customers", f"{len(feats):,}", help="All customers in the extract, labelled and to predict.")
    c2.metric(
        "Monthly active customers",
        f"{latest(monthly['active_customers']):,.0f}",
        help="Mean of the last 3 months of the period. Lower bound: the largest category count "
        "of the month (docs/assumptions.md, A6).",
    )
    c3.metric(
        "Leakage share of card spend",
        f"{latest(leak, monthly['spend']):.1%}",
        help="cash + savings over all card spend, last 3 months of the period (docs/assumptions.md, A1).",
    )
    c4.metric("Churn rate", f"{labelled['churned'].mean():.1%}", help=f"{len(labelled):,} labelled customers.")

with chart:
    fig = px.line(monthly.reset_index(), x="date", y="active_customers", color_discrete_sequence=PALETTE)
    fig.update_layout(xaxis_title=None, yaxis_title="customers")
    st.plotly_chart(fig, width="stretch")

if has_segments(feats):
    st.subheader("Who the customers are")
    seg = feats.groupby("cluster_name", observed=True).agg(customers=("customer_id", "size"), spend=("total_amount", "sum"))
    seg = (seg / seg.sum()).reset_index().melt("cluster_name", var_name="measure", value_name="share")
    seg["measure"] = seg["measure"].map({"customers": "% of customers", "spend": "% of spend"})
    fig = px.bar(
        seg, x="share", y="cluster_name", color="measure", barmode="group", orientation="h",
        color_discrete_sequence=[PALETTE[0], PALETTE[1]],
    )
    fig.update_layout(xaxis_tickformat=".0%", yaxis={"autorange": "reversed", "title": None}, legend_title_text=None)
    st.plotly_chart(fig, width="stretch")
    st.caption("Segments from notebooks/07_segments.ipynb, see the Segments page.")

with st.expander("Show data"):
    st.dataframe(monthly, width="stretch")
