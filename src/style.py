"""One palette and one matplotlib style for every chart in the project.

    from src import style
    style.apply()
    ax.plot(x, y, color=style.C[0])

Categorical colours are assigned in fixed order and never cycled: series 1 is
always C[0], "other" is always GREY. Use at most four named series per chart.
"""

import matplotlib.pyplot as plt

# categorical, fixed order: blue, orange, aqua, yellow, magenta, green
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
GREY = "#9a9891"      # "other", noise, context
ACCENT = C[1]         # the one thing to look at on a slide
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e6e5e1", "#fcfcfb"

RC = {
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "figure.dpi": 110, "savefig.dpi": 150,
    "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.spines.top": False, "axes.spines.right": False,
    "text.color": INK, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "legend.frameon": False,
}


def apply() -> None:
    plt.rcParams.update(RC)


def clean(ax, title: str, ylabel: str = "", xlabel: str = "") -> None:
    """Title, labels, no vertical grid."""
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", visible=False)


def label_end(ax, x, series, name: str, color: str, lw: float = 2) -> None:
    """Line with a direct label at its end instead of a legend entry."""
    ax.plot(x, series, color=color, lw=lw)
    ax.annotate(name, (x[-1], series.iloc[-1]), xytext=(5, 0), textcoords="offset points",
                va="center", color=INK2)


def annotate_bars(ax, values, labels, fontsize: int = 8) -> None:
    """Small text above vertical bars, e.g. n per bar."""
    for i, (v, t) in enumerate(zip(values, labels)):
        ax.annotate(str(t), (i, v), xytext=(0, 3), textcoords="offset points",
                    ha="center", color=INK2, fontsize=fontsize)
