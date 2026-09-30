"""Chart functions shared by the notebooks and the dashboard."""

from pathlib import Path

import matplotlib.dates as mdates
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


def active_customers(monthly: pd.DataFrame, ax=None):
    ax = ax or plt.subplots(figsize=(8, 3.4))[1]
    ax.plot(monthly.index, monthly["active_customers"], color=style.C[0], lw=2)
    for x in (monthly.index[0], monthly.index[-1]):
        ax.annotate(f"{monthly.loc[x, 'active_customers']:.0f}", (x, monthly.loc[x, "active_customers"]),
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
