"""Chart functions shared by the notebooks and the dashboard."""

from pathlib import Path

import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt
import pandas as pd

from src import style
from src.data import ROOT
from src.events import events

FIGURES = ROOT / "figures"


def save_fig(fig, name: str, folder: str = "") -> Path:
    path = FIGURES / folder / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path


def month_axis(ax) -> None:
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 7]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %y"))


def add_event_markers(ax, affects: str | None = None, label: bool = True) -> None:
    for _, e in events(affects).iterrows():
        if pd.isna(e["end"]):
            ax.axvline(e["start"], color=style.GREY, lw=1, ls=":")
            if label:
                ax.annotate(e["event"], (e["start"], ax.get_ylim()[1]), xytext=(2, -10), textcoords="offset points",
                            fontsize=7, color=style.INK2, rotation=90, va="top")
        else:
            ax.axvspan(e["start"], e["end"], color=style.GREY, alpha=0.12, lw=0)


def active_customers(monthly: pd.DataFrame, ax=None, mark_peak: bool = False):
    ax = ax or plt.subplots(figsize=(8, 3.4))[1]
    ax.plot(monthly.index, monthly["active_customers"], color=style.C[0], lw=2)
    for x in (monthly.index[0], monthly.index[-1]):
        ax.annotate(f"{monthly.loc[x, 'active_customers']:.0f}", (x, monthly.loc[x, "active_customers"]),
                    xytext=(0, 6), textcoords="offset points", ha="center", color=style.INK2)
    if mark_peak:
        x = monthly["active_customers"].idxmax()
        ax.scatter([x], [monthly.loc[x, "active_customers"]], s=20, color=style.C[0], zorder=3)
        ax.annotate(f"peak {monthly.loc[x, 'active_customers']:.0f}", (x, monthly.loc[x, "active_customers"]),
                    xytext=(0, 6), textcoords="offset points", ha="center", color=style.INK2)
    month_axis(ax)
    style.clean(ax, "monthly active customers", "customers")
    return ax


def category_shares(shares: pd.Series, highlight: tuple[str, ...] = ("cash", "savings"), ax=None):
    ax = ax or plt.subplots(figsize=(7, 4.2))[1]
    s = shares.sort_values()
    ax.barh(s.index, s.values, color=[style.ACCENT if c in highlight else style.C[0] for c in s.index])
    for i, v in enumerate(s.values):
        ax.annotate(f"{v:.1f}", (v, i), xytext=(4, 0), textcoords="offset points", va="center", color=style.INK2, fontsize=9)
    style.clean(ax, "where the money goes, % of total card spend")
    ax.grid(axis="y", visible=False)
    return ax


def financial_counterparts(fin: pd.DataFrame, ax=None):
    """Counterparts of cash + savings, share of the two categories, colour by type."""
    ax = ax or plt.subplots(figsize=(7, 3.8))[1]
    g = fin.groupby(["top_counterpart", "counterpart_type"])["total_amount"].sum().reset_index()
    g["share"] = g["total_amount"] / g["total_amount"].sum() * 100
    g = g.sort_values("share")
    colours = {"financial_provider": style.C[0], "payment_provider": style.C[2], "other": style.GREY}
    ax.barh(g["top_counterpart"], g["share"], color=[colours[t] for t in g["counterpart_type"]])
    for i, v in enumerate(g["share"]):
        ax.annotate(f"{v:.0f}", (v, i), xytext=(4, 0), textcoords="offset points", va="center", color=style.INK2, fontsize=9)
    style.clean(ax, "'cash' + 'savings': who gets the money, % of the two categories")
    ax.grid(axis="y", visible=False)
    return ax


def leakage_lines(pct: pd.DataFrame, columns: list[str], title: str, ax=None, ylim: float | None = None):
    """Share lines per quarter with direct labels. pct indexed by quarter Period."""
    ax = ax or plt.subplots(figsize=(8, 3.8))[1]
    x = pct.index.to_timestamp()
    for i, col in enumerate(columns):
        style.label_end(ax, x, pct[col], col, style.C[i])
    style.clean(ax, title, "% of all card spend")
    if ylim:
        ax.set_ylim(0, ylim)
    return ax


def monthly_bar(series: pd.Series, title: str, ylabel: str, color: str = style.C[0], mean_line: bool = True, ax=None):
    ax = ax or plt.subplots(figsize=(8, 3.4))[1]
    ax.bar(series.index, series.values, width=25, color=color)
    if mean_line:
        ax.axhline(series.mean(), color=style.INK2, lw=1, ls="--")
        ax.annotate(f"mean {series.mean():.1f}", (series.index[-1], series.mean()), xytext=(4, 2),
                    textcoords="offset points", fontsize=8, color=style.INK2)
    month_axis(ax)
    style.clean(ax, title, ylabel)
    return ax


def small_multiples(panels: list[tuple[pd.Series, str, str]], ncols: int = 2, figsize=(11, 3.2)):
    """Each panel: (series indexed by date, title, ylabel). One y-axis per panel."""
    nrows = -(-len(panels) // ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(figsize[0], figsize[1] * nrows), squeeze=False)
    for ax, (s, title, ylabel) in zip(axes.flat, panels):
        ax.plot(s.index, s.values, color=style.C[0], lw=2)
        month_axis(ax)
        style.clean(ax, title, ylabel)
    for ax in list(axes.flat)[len(panels):]:
        ax.set_visible(False)
    fig.tight_layout()
    return fig, axes


def _num(n: int) -> str:
    """Thousands with a thin space, 1 553 instead of 1,553."""
    return f"{n:,}".replace(",", "\u2009")


def share_lines(pct: pd.DataFrame, columns: list[str], title: str, ylabel: str, ax=None, ylim: float | None = None):
    """Like leakage_lines, but with a free y label and the month axis. pct indexed by quarter Period or date."""
    ax = ax or plt.subplots(figsize=(8, 3.8))[1]
    x = pct.index.to_timestamp() if isinstance(pct.index, pd.PeriodIndex) else pct.index
    for i, col in enumerate(columns):
        style.label_end(ax, x, pct[col], col, style.C[i])
    month_axis(ax)
    style.clean(ax, title, ylabel)
    if ylim:
        ax.set_ylim(0, ylim)
    return ax


def share_panels(panels: list[dict], figsize=(12, 3.6)):
    """Small multiples of share_lines, one y-axis per panel. Each panel is a dict of share_lines arguments."""
    fig, axes = plt.subplots(1, len(panels), figsize=figsize, squeeze=False)
    for ax, kw in zip(axes.flat, panels):
        share_lines(ax=ax, **kw)
    fig.tight_layout(w_pad=6)
    return fig, axes


def churn_ladder(ladder: pd.DataFrame, title: str, xlabel: str, reference: float | None = None,
                 color: str = style.ACCENT, mute_first: bool = False, ax=None):
    """Churn rate per bin. ladder: index = bin labels, columns 'rate' (0-1) and 'n'. reference = overall rate (0-1).
    mute_first greys out the first bin, e.g. the customers without any leakage."""
    ax = ax or plt.subplots(figsize=(7.5, 3.8))[1]
    pos = list(range(len(ladder)))
    rates = ladder["rate"] * 100
    colors = [style.GREY if (mute_first and i == 0) else color for i in pos]
    ax.bar(pos, rates, color=colors, width=0.62)
    for i, r in enumerate(rates):
        ax.annotate(f"{r:.0f} %", (i, r), xytext=(0, 4), textcoords="offset points",
                    ha="center", color=style.INK, fontsize=10, fontweight="bold")
    ax.set_xticks(pos, [f"{b}\nn = {_num(n)}" for b, n in zip(ladder.index.astype(str), ladder["n"])])
    if reference is not None:
        ax.axhline(reference * 100, color=style.INK2, lw=1, ls="--")
        ax.annotate(f"all\n{reference * 100:.0f} %", (1, reference * 100), xycoords=ax.get_yaxis_transform(),
                    xytext=(4, 0), textcoords="offset points", va="center", fontsize=8, color=style.INK2)
    ax.set_ylim(0, rates.max() * 1.18)
    style.clean(ax, title, "% churned", xlabel)
    return ax


def churn_ladder_pair(first: pd.DataFrame, corrected: pd.DataFrame, titles: tuple[str, str], xlabels: tuple[str, str],
                      note: str = "", figsize=(12, 4.2)):
    """Two ladders side by side on one y scale: the first reading in grey, the corrected one in the accent colour."""
    fig, axes = plt.subplots(1, 2, figsize=figsize, sharey=True)
    churn_ladder(first, titles[0], xlabels[0], color=style.GREY, ax=axes[0])
    churn_ladder(corrected, titles[1], xlabels[1], mute_first=True, ax=axes[1])
    top = max(first["rate"].max(), corrected["rate"].max()) * 100 * 1.18
    axes[0].set_ylim(0, top)
    axes[1].tick_params(labelleft=True)
    if note:
        fig.text(0.01, -0.02, note, fontsize=8.5, color=style.INK2, va="top")
    fig.tight_layout(w_pad=4)
    return fig, axes


def data_map(n_customers: int, n_labelled: int, n_predict: int, n_months: int, n_counterparts: int, ax=None):
    """The three data sets and how they connect: customer_id to the labels, only `category` to the monthly data."""
    ax = ax or plt.subplots(figsize=(11, 3.2))[1]
    ax.set_xlim(-0.01, 1.01)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = {
        "labels": (0.02, "churn labels", f"churned yes / no\n{_num(n_labelled)} customers (70 %)\n{_num(n_predict)} to predict"),
        "customers": (0.36, "customer file", f"{_num(n_customers)} customers\ntotals, tenure, spend per category\nno dates, no counterparts"),
        "sow": (0.72, "monthly counterpart file", f"month × category × counterpart\n{n_months} months, {n_counterparts} counterparts\nno customers"),
    }
    w, h, y0 = 0.28, 0.56, 0.24
    for x0, head, body in boxes.values():
        ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=0.02",
                                    fc="white", ec=style.INK2, lw=1))
        ax.text(x0 + 0.015, y0 + h - 0.07, head, fontsize=10.5, fontweight="bold", color=style.INK, va="top")
        ax.text(x0 + 0.015, y0 + h - 0.2, body, fontsize=9, color=style.INK2, va="top", linespacing=1.5)

    yc = y0 + h / 2
    ax.annotate("", (0.36, yc), (0.30, yc), arrowprops=dict(arrowstyle="-", color=style.INK2, lw=1.5))
    ax.text(0.33, yc + 0.03, "customer_id", ha="center", fontsize=8, color=style.INK2)
    ax.annotate("", (0.72, yc), (0.64, yc), arrowprops=dict(arrowstyle="-", color=style.ACCENT, lw=2, ls="--"))
    ax.text(0.68, yc + 0.03, "category", ha="center", fontsize=9, color=style.INK, fontweight="bold")
    ax.text(0.68, y0 - 0.06, "the only link. 'cash' and 'savings' are the one category\nwhose named counterparts are all financial providers",
            ha="center", va="top", fontsize=8, color=style.INK2)
    style.clean(ax, "three files, one bridge")
    return ax
