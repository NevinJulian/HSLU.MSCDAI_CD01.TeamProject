import pandas as pd
import plotly.express as px
import streamlit as st

from shared import (
    GREY, PALETTE, breakdown_colors, breakdown_options, color_map, customers, in_range, latest, month_range, require,
    top_n_plus_other,
)

LEAKAGE_CATEGORIES = ["cash", "savings"]
MEASURES = {
    "leak share (cash + savings)": "leak_share",
    "savings share (conservative)": "cat_savings_share",
}
# Same bins as docs/leakage_churn.md
LEAK_BINS = [-0.001, 0, 0.05, 0.20, 0.50, 1.001]
LEAK_LABELS = ["0", "0–5 %", "5–20 %", "20–50 %", "> 50 %"]
NONE = "none"

st.set_page_config(page_title="Wallet leakage", layout="wide")
st.title("Wallet leakage")
st.caption(
    "Assumes cash and savings are transfers to other financial providers rather than "
    "ATM withdrawals (docs/assumptions.md, A1). The savings share alone does not depend on it."
)

feats = customers()
cp_all = require("sow_category_counterpart_clean")

# ---------------------------------------------------------------- population, over time
# KPIs and the chart sit above the period slider but depend on it, so they are
# filled into containers once the slider has been read.
kpis = st.container()
st.subheader("Where the money goes")
mode = st.segmented_control("Show", ["share of card spend", "CHF"], default="share of card spend", key="leak_mode")
chart = st.container()
start, end = month_range(cp_all["date"], key="leak_period")
st.caption("The period applies to this chart and the first two figures at the top.")

cp = in_range(cp_all, start, end)
monthly_total = cp.groupby("date")["total_amount"].sum()
leak = cp[cp["category"].isin(LEAKAGE_CATEGORIES)]

with kpis:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Leaked in period", f"CHF {leak['total_amount'].sum():,.0f}")
    c2.metric(
        "Share of card spend",
        f"{latest(leak.groupby('date')['total_amount'].sum(), monthly_total):.1%}",
        help="Last 3 months of the period.",
    )
    c3.metric("Customers with any leakage", f"{feats['has_leak'].mean():.0%}", help="Over the whole window, all customers.")
    c4.metric("Avg customer leak share", f"{feats['leak_share'].mean():.1%}", help="Mean of the per-customer share.")

by_group = (
    top_n_plus_other(leak, "counterpart_group", "total_amount")
    .groupby(["date", "counterpart_group"], as_index=False)["total_amount"]
    .sum()
)
by_group["share"] = by_group["total_amount"] / by_group["date"].map(monthly_total)
colors = color_map(cp_all[cp_all["category"].isin(LEAKAGE_CATEGORIES)], "counterpart_group", "total_amount")
y = "total_amount" if mode == "CHF" else "share"
fig = px.area(
    by_group, x="date", y=y, color="counterpart_group", color_discrete_map=colors,
    category_orders={"counterpart_group": [g for g in colors if g in set(by_group["counterpart_group"])]},
)
fig.update_layout(
    legend_title_text="destination", xaxis_title=None,
    yaxis_title="CHF" if y == "total_amount" else "share of all card spend",
    yaxis_tickformat=",.0f" if y == "total_amount" else ".1%",
)
with chart:
    st.plotly_chart(fig, width="stretch")
    st.caption('"other" is cash and savings spend whose counterpart the source file does not name.')

# ---------------------------------------------------------------- customers
st.subheader("Who leaks")
st.caption("Per customer, over the whole window.")
chart = st.container()
options = breakdown_options(feats)
left, mid, right = st.columns(3)
by_label = left.selectbox("Break down by", list(options), index=1 if "segment" in options else 0, key="leak_by")
measure_label = mid.selectbox("Measure", list(MEASURES), key="leak_measure")
by, measure = options[by_label], MEASURES[measure_label]
group = right.selectbox(
    "Compare a group with all customers", [NONE, *feats[by].cat.categories], key=f"leak_group_{by}"
)

per_group = feats.groupby(by, observed=True).agg(
    value=(measure, "mean"), customers=("customer_id", "size")
).reset_index()
overall = feats[measure].mean()
group_colors = breakdown_colors(feats, by)
if group != NONE:
    group_colors = {g: (group_colors.get(g, PALETTE[0]) if g == group else GREY) for g in per_group[by]}
fig = px.bar(
    per_group, x=by, y="value", hover_data=["customers"], color=by if group_colors else None,
    color_discrete_map=group_colors, color_discrete_sequence=[PALETTE[0]],
)
fig.add_hline(y=overall, line_dash="dot", line_color=GREY, annotation_text=f"all customers {overall:.1%}")
fig.update_layout(yaxis_tickformat=".0%", yaxis_title=measure_label, xaxis_title=None, showlegend=False)
with chart:
    st.plotly_chart(fig, width="stretch")

if group != NONE:
    sub = feats[feats[by] == group]
    lab, lab_all = sub[sub["split"] == "train"], feats[feats["split"] == "train"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Customers", f"{len(sub):,}", f"{len(sub) / len(feats):.0%} of all", delta_color="off")
    for col, (name, c) in zip((m2, m3), MEASURES.items()):
        col.metric(
            name, f"{sub[c].mean():.1%}", f"{(sub[c].mean() - feats[c].mean()) * 100:+.1f} pp vs all",
            delta_color="inverse",
        )
    # a churn status group churns at 0 or 100 % by definition
    if len(lab) and by != "churn_status":
        m4.metric(
            "Churn rate", f"{lab['churned'].mean():.0%}",
            f"{(lab['churned'].mean() - lab_all['churned'].mean()) * 100:+.0f} pp vs all", delta_color="inverse",
            help=f"{len(lab):,} labelled customers in the group.",
        )

# ---------------------------------------------------------------- churn signal
st.subheader("Leakage as a churn signal")
left, right = st.columns([2, 1])
min_days = left.slider(
    "Only customers active for at least (days)", 0, 900, 365, step=30, key="leak_min_days",
    help="New customers churn a lot whatever they do. Raising this shows the leakage effect is not just tenure.",
)
signal_label = right.selectbox("Measure", list(MEASURES), index=1, key="leak_signal")
signal = MEASURES[signal_label]

lab = feats[(feats["split"] == "train") & (feats["days_active"] > min_days)].copy()
if lab.empty:
    st.info("No labelled customers with that much tenure.")
    st.stop()
lab["bin"] = pd.cut(lab[signal], LEAK_BINS, labels=LEAK_LABELS)
ladder = lab.groupby("bin", observed=False).agg(churn_rate=("churned", "mean"), customers=("customer_id", "size"))
ladder = ladder.reset_index()
fig = px.bar(
    ladder, x="bin", y="churn_rate", text=ladder["customers"].map(lambda n: f"n = {n:,}"),
    color_discrete_sequence=[PALETTE[1]],
)
base = lab["churned"].mean()
fig.add_hline(y=base, line_dash="dot", line_color=GREY, annotation_text=f"all {len(lab):,} customers {base:.0%}")
fig.update_traces(textposition="outside")
fig.update_layout(yaxis_tickformat=".0%", yaxis_title="churn rate", xaxis_title=signal_label, yaxis_range=[0, 1])
st.plotly_chart(fig, width="stretch")
st.caption(
    "Labelled customers only. Customers who send money to other providers churn more, also at equal "
    "tenure. This is an association, not a cause: the data has no per-customer dates (docs/leakage_churn.md)."
)

with st.expander("Show data"):
    st.dataframe(per_group, width="stretch")
    st.dataframe(ladder, width="stretch")
