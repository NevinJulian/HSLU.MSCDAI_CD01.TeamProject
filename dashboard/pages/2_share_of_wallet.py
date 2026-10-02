import pandas as pd
import plotly.express as px
import streamlit as st

from shared import GREY, OTHER, PALETTE, color_map, in_range, latest, month_range, require, top_n_plus_other

NONE = "none"
DEFAULT_DRILL = "groceries"
DIMMED = 0.3
FRAME_MS, TRANSITION_MS = 1200, 700

# The animation shows all 16 categories, so it needs more colours than the
# four-series palette: the project palette first (same colours as the other
# charts for the largest categories), then ten more distinct ones.
EXTRA_COLORS = ["#7b5cd6", "#8c564b", "#17becf", "#bcbd22", "#c9302c",
                "#1f3b73", "#a23b72", "#2f6f6f", "#c9a66b", "#6b7a8f"]

st.set_page_config(page_title="Share of wallet", layout="wide")
st.title("Share of wallet")

cat_all = require("sow_category_clean")
cp_all = require("sow_category_counterpart_clean")

order = cat_all.groupby("category")["total_amount"].sum().sort_values(ascending=False).index
ANIM_COLORS = dict(zip(order, PALETTE + EXTRA_COLORS))


def chf_short(v: float) -> str:
    if v >= 1e6:
        return f"{v / 1e6:.2f}M"
    return f"{v / 1e3:.0f}k" if v >= 1e3 else f"{v:,.0f}"


# A click on the ranking chart below sets the focus category. The chart's
# selection survives reruns, so only a *new* click overrides the selectbox.
clicked = None
selection = st.session_state.get("sow_ranking")
if selection and selection.get("selection", {}).get("points"):
    clicked = selection["selection"]["points"][0].get("y")
if clicked and clicked != st.session_state.get("sow_last_click"):
    st.session_state["sow_focus"] = clicked
st.session_state["sow_last_click"] = clicked

left, right = st.columns([2, 1])
focus = left.selectbox(
    "Highlight a category", [NONE, *order], key="sow_focus",
    help="Or click a bar in the ranking. The other categories stay in the chart, so shares are always of the whole wallet.",
)
mode = right.segmented_control("Show", ["share of wallet", "CHF"], default="share of wallet", key="sow_mode")
focus = None if focus == NONE else focus

# KPIs and the first chart sit above the period slider but depend on it, so
# they are filled into containers once the slider has been read.
kpis = st.container()
st.subheader("Category share of wallet over time")
chart = st.container()
start, end = month_range(cat_all["date"], key="sow_period")
st.caption("The period applies to the whole page.")
cat = in_range(cat_all, start, end)
cp = in_range(cp_all, start, end)

totals = cat.groupby("category")["total_amount"].sum().sort_values(ascending=False)
total = totals.sum()
monthly_total = cat.groupby("date")["total_amount"].sum()

with kpis:
    c1, c2, c3 = st.columns(3)
    c1.metric("Card spend in period", f"CHF {total:,.0f}")
    fin = cp[cp["counterpart_type"] == "financial_provider"]["total_amount"].sum()
    c2.metric("To financial providers", f"{fin / total:.1%}", help="Revolut, crypto exchanges and banks as counterpart.")
    if focus:
        c3.metric(
            f"{focus}, share of wallet",
            f"{latest(cat[cat['category'] == focus].groupby('date')['total_amount'].sum(), monthly_total):.1%}",
            help="Last 3 months of the period."
            + (" Revolut moved from savings to cash in 2022Q1, read the two together." if focus in ("cash", "savings") else ""),
        )
    else:
        c3.metric("Categories", f"{len(totals)}")

# ---------------------------------------------------------------- over time
cat_colors = color_map(cat_all, "category", "total_amount")
named = top_n_plus_other(cat, "category", "total_amount", keep=(focus,) if focus else ())
by_cat = named.groupby(["date", "category"], as_index=False)["total_amount"].sum()
by_cat["share"] = by_cat["total_amount"] / by_cat["date"].map(monthly_total)
shown = [c for c in totals.index if c in set(by_cat["category"])] + [OTHER]
colors = {c: cat_colors[c] for c in shown}
if focus and focus not in totals.index[:4]:
    # outside the top four the ranked colour can repeat one already on screen
    taken = {v for k, v in colors.items() if k != focus}
    colors[focus] = next(c for c in PALETTE if c not in taken)

y = "share" if mode != "CHF" else "total_amount"
fig = px.area(by_cat, x="date", y=y, color="category", color_discrete_map=colors, category_orders={"category": shown})
if focus:
    fig.for_each_trace(lambda t: t.update(opacity=1 if t.name == focus else DIMMED))
fig.update_layout(
    yaxis_tickformat=".0%" if y == "share" else ",.0f", yaxis_title=None if y == "share" else "CHF",
    xaxis_title=None, legend_title_text="category",
)
with chart:
    st.plotly_chart(fig, width="stretch")
    st.caption(
        'The four largest categories are named, the rest is "other" in grey. A highlighted category is added '
        "when it is not among them. Shares are always of all card spend in the month."
    )

# ---------------------------------------------------------------- ranking
st.subheader("Ranking in the period")
rank = (totals / total).rename("share").reset_index()
rank_colors = {c: (colors[c] if c == focus else GREY) for c in rank["category"]} if focus else None
fig = px.bar(
    rank, x="share", y="category", orientation="h", color="category" if focus else None,
    color_discrete_map=rank_colors, color_discrete_sequence=[PALETTE[0]],
)
fig.update_layout(
    xaxis_tickformat=".0%", xaxis_title="share of card spend", yaxis={"autorange": "reversed", "title": None},
    showlegend=False, height=460,
)
st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="sow_ranking")
st.caption("Click a bar to highlight that category above and to open it below.")

# ---------------------------------------------------------------- animation
st.subheader("All categories over time")
left, right = st.columns(2)
step = left.segmented_control(
    "Step", ["quarter", "month"], default="quarter", key="sow_anim_step",
    help="Quarters smooth out single noisy months such as December 2023.",
)
values = right.segmented_control("Values", ["share of wallet", "CHF"], default="share of wallet", key="sow_anim_values")
freq, fmt = ("M", "%b %Y") if step == "month" else ("Q", "%Y Q%q")
x = "total_amount" if values == "CHF" else "share"

frames = cat.assign(period=cat["date"].dt.to_period(freq))
frames = frames.groupby(["period", "category"])["total_amount"].sum().unstack(fill_value=0)
frames = frames.reindex(columns=totals.index, fill_value=0)
shares = frames.div(frames.sum(axis=1), axis=0)
frames = pd.concat([frames.stack().rename("total_amount"), shares.stack().rename("share")], axis=1).reset_index()
frames = frames.sort_values(["period", "category"])
frames["label"] = frames["period"].map(lambda p: p.strftime(fmt))
frames["text"] = frames[x].map(chf_short if x == "total_amount" else "{:.1%}".format)

fig = px.bar(
    frames, x=x, y="category", orientation="h", animation_frame="label", color="category",
    color_discrete_map=ANIM_COLORS, text="text", range_x=[0, frames[x].max() * 1.18],
    category_orders={"category": list(totals.index)}, hover_data={"label": False, "text": False},
)
if focus:
    fig.for_each_trace(lambda t: t.update(opacity=1 if t.name == focus else DIMMED))
fig.update_traces(textposition="outside", cliponaxis=False)
fig.update_layout(
    xaxis_tickformat=",.0f" if x == "total_amount" else ".0%",
    xaxis_title="CHF per " + (step or "quarter") if x == "total_amount" else "share of card spend",
    yaxis={"autorange": "reversed", "title": None}, showlegend=False, height=560,
)
# the current period, large in the corner of every frame
labels = list(dict.fromkeys(frames["label"]))
stamp = {"x": 0.98, "y": 0.04, "xref": "paper", "yref": "paper", "xanchor": "right", "showarrow": False,
         "font": {"size": 34, "color": GREY}}
fig.update_layout(annotations=[{**stamp, "text": labels[0]}])
for frame in fig.frames:
    frame.layout = {"annotations": [{**stamp, "text": frame.name}]}
fig.layout.sliders[0].currentvalue = {"prefix": "", "font": {"size": 16}}
play = fig.layout.updatemenus[0].buttons[0].args[1]
play["frame"]["duration"], play["transition"]["duration"] = FRAME_MS, TRANSITION_MS
st.plotly_chart(fig, width="stretch")
st.caption(
    "Press play. Categories keep the order of the whole period, so a bar that grows or shrinks is easy to follow. "
    "During 2022 savings shrinks while cash grows: Revolut moved from savings to cash in the source "
    "from 2022Q1, so read the two bars together."
)

# ---------------------------------------------------------------- drill-down
drill = focus or DEFAULT_DRILL
st.subheader(f"Inside {drill}")
inside = cp[cp["category"] == drill]
# Counterpart groups only exist for cash, savings, groceries, transport and
# entertainment (src/mappings.py); elsewhere every counterpart maps to "other",
# so fall back to the counterparts themselves.
dim = "counterpart_group" if (inside["counterpart_group"] != OTHER).any() else "top_counterpart"

by_cp = top_n_plus_other(inside, dim, "total_amount").groupby(["date", dim], as_index=False)["total_amount"].sum()
by_cp["share"] = by_cp["total_amount"] / by_cp.groupby("date")["total_amount"].transform("sum")
cp_colors = color_map(cp_all[cp_all["category"] == drill], dim, "total_amount")
fig = px.area(
    by_cp, x="date", y="share" if mode != "CHF" else "total_amount", color=dim, color_discrete_map=cp_colors,
    category_orders={dim: [c for c in cp_colors if c in set(by_cp[dim])]},
)
fig.update_layout(
    yaxis_tickformat=".0%" if mode != "CHF" else ",.0f", yaxis_title=None if mode != "CHF" else "CHF",
    xaxis_title=None, legend_title_text=dim.replace("_", " "),
)
st.plotly_chart(fig, width="stretch")
if dim == "counterpart_group":
    st.caption(
        f"{drill} by counterpart group, as a share of {drill} spend. Groups are defined for cash, savings, "
        'groceries, transport and entertainment only (src/mappings.py). "other" is counterparts the source '
        "file does not name, plus named ones without a group and groups beyond the largest four."
    )
elif (inside["top_counterpart"] == OTHER).all():
    st.caption(f"The source file names no counterparts in {drill}, all of it is \"other\".")
else:
    st.caption(
        f"No counterpart groups are defined for {drill}, so the largest named counterparts are shown. "
        '"other" is counterparts the source file does not name, plus everything beyond the largest four.'
    )

top = (
    inside.groupby(["top_counterpart", "counterpart_type"], as_index=False)["total_amount"]
    .sum()
    .nlargest(15, "total_amount")
)
fig = px.bar(
    top, x="total_amount", y="top_counterpart", color="counterpart_type", orientation="h",
    color_discrete_map=color_map(cp_all, "counterpart_type", "total_amount"),
)
fig.update_layout(
    title=f"Top counterparts in {drill}", yaxis={"categoryorder": "total ascending", "title": None},
    legend_title_text="type", xaxis_title="CHF",
)
st.plotly_chart(fig, width="stretch")

with st.expander("Show data"):
    st.dataframe(by_cat, width="stretch")
