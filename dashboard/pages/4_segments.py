import pandas as pd
import plotly.express as px
import streamlit as st

from shared import GREY, customers, has_segments, segment_colors

# Categories shown in the spend-mix heatmap, the rest is summed into "other".
MIX_CATEGORIES = ["groceries", "restaurants", "shopping", "holidays", "transport", "entertainment", "communication", "cash", "savings"]
NONE = "none"

st.set_page_config(page_title="Segments", layout="wide")
st.title("Segments")

feats = customers()
if not has_segments(feats):
    st.warning("customer_clusters not found in data/processed. Run notebooks/07_segments.ipynb first.")
    st.stop()

colors = segment_colors(feats)
labelled = feats[feats["split"] == "train"]

prof = feats.groupby("cluster_name", observed=True).agg(
    customers=("customer_id", "size"),
    spend=("total_amount", "sum"),
    median_chf=("total_amount", "median"),
    median_tx=("n_transactions", "median"),
    median_days=("days_active", "median"),
    ecom=("ecom_perc", "median"),
    foreign=("foreign_tx_share", "median"),
    leak_share=("leak_share", "mean"),
    savings_share=("cat_savings_share", "mean"),
)
prof["pct_customers"] = prof["customers"] / prof["customers"].sum()
prof["pct_spend"] = prof["spend"] / prof["spend"].sum()
prof["churn_rate"] = labelled.groupby("cluster_name", observed=True)["churned"].mean()
prof = prof.reset_index()

focus = st.selectbox(
    "Focus on a segment", [NONE, *prof["cluster_name"]], key="seg_focus",
    help="Greys out the other segments in every chart on this page.",
)
focus = None if focus == NONE else focus
shown_colors = {s: (c if focus in (None, s) else GREY) for s, c in colors.items()}

if focus:
    row = prof.set_index("cluster_name").loc[focus]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Customers", f"{int(row['customers']):,}", f"{row['pct_customers']:.0%} of all", delta_color="off")
    m2.metric("Share of spend", f"{row['pct_spend']:.0%}")
    m3.metric(
        "Churn rate", f"{row['churn_rate']:.0%}",
        f"{(row['churn_rate'] - labelled['churned'].mean()) * 100:+.0f} pp vs all", delta_color="inverse",
    )
    m4.metric(
        "Leak share", f"{row['leak_share']:.1%}",
        f"{(row['leak_share'] - feats['leak_share'].mean()) * 100:+.1f} pp vs all", delta_color="inverse",
    )

# ---------------------------------------------------------------- churn vs leakage
st.subheader("Churn and leakage per segment")
fig = px.scatter(
    prof, x="leak_share", y="churn_rate", size="customers", color="cluster_name", text="cluster_name",
    color_discrete_map=shown_colors, size_max=60, hover_data={"customers": ":,", "pct_spend": ":.0%"},
)
fig.update_traces(textposition="top center")
fig.update_layout(
    xaxis_tickformat=".0%", yaxis_tickformat=".0%", xaxis_title="mean leak share", yaxis_title="churn rate",
    showlegend=False, yaxis_range=[0, 1],
)
st.plotly_chart(fig, width="stretch")
st.caption("Bubble size = customers. Churn rate on the labelled customers of each segment.")

# ---------------------------------------------------------------- customers vs spend
st.subheader("Share of customers vs share of spend")
long = prof.melt("cluster_name", ["pct_customers", "pct_spend"], var_name="measure", value_name="share")
long["measure"] = long["measure"].map({"pct_customers": "% of customers", "pct_spend": "% of spend"})
fig = px.bar(
    long, x="share", y="measure", color="cluster_name", orientation="h", color_discrete_map=shown_colors,
    category_orders={"cluster_name": list(colors)},
)
fig.update_layout(xaxis_tickformat=".0%", xaxis_title=None, yaxis_title=None, legend_title_text="segment", height=260)
st.plotly_chart(fig, width="stretch")

# ---------------------------------------------------------------- spend mix
st.subheader("What each segment spends on")
cat_cols = [c for c in feats.columns if c.startswith("cat_") and not c.endswith("_share")]
mix = feats.groupby("cluster_name", observed=True)[cat_cols].sum()
mix.columns = [c.removeprefix("cat_") for c in mix.columns]
mix = mix.div(mix.sum(axis=1), axis=0)
mix = pd.concat([mix[MIX_CATEGORIES], mix.drop(columns=MIX_CATEGORIES).sum(axis=1).rename("other")], axis=1)
fig = px.imshow(mix, text_auto=".0%", aspect="auto", color_continuous_scale=["#fcfcfb", "#2a78d6"], zmin=0, zmax=1)
fig.update_layout(xaxis_title=None, yaxis_title=None, coloraxis_showscale=False)
if focus:
    i = list(mix.index).index(focus)
    fig.add_shape(type="rect", x0=-0.5, x1=len(mix.columns) - 0.5, y0=i - 0.5, y1=i + 0.5, line={"width": 2})
st.plotly_chart(fig, width="stretch")
st.caption("Share of each segment's card spend by category, spend-weighted.")

with st.expander("Profile table"):
    st.dataframe(
        prof.drop(columns="spend").style.format(
            {"pct_customers": "{:.0%}", "pct_spend": "{:.0%}", "churn_rate": "{:.0%}", "leak_share": "{:.1%}",
             "savings_share": "{:.1%}", "ecom": "{:.2f}", "foreign": "{:.2f}", "median_chf": "{:,.0f}"}
        ),
        width="stretch",
    )
    st.caption("Method and segment descriptions: docs/segments.md (Data & method page).")
