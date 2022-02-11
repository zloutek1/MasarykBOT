import datetime
from typing import Optional, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap

__all__ = ["generate_heatmap"]

MONTHS: List[str] = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]
DAYS: List[str] = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
COLORS = [
    [0.09, 0.11, 0.13, 1],
    [0.05, 0.27, 0.16, 1],
    [0.00, 0.43, 0.20, 1],
    [0.15, 0.65, 0.25, 1],
    [0.22, 0.83, 0.33, 1],
]
GITHUB_CMAP = ListedColormap(
    np.concatenate([
        np.linspace(x, y, 64) for x, y in zip(COLORS, COLORS[1:])
    ])
)


def plot_heatmap(series: pd.Series, cmap: Optional[str] = None) -> plt.Axes:
    cmap = GITHUB_CMAP if cmap is None else plt.get_cmap(cmap)

    num_weeks = len(series) // 7 + 1
    heatmap = np.zeros((7, num_weeks))
    ticks = {}

    for i, (date, value) in enumerate(series.items()):
        # set tick label to corresponding month
        if date.day == 1:
            ticks[i // 7] = MONTHS[date.month - 1]

        # equals to heatmap[day, week]
        heatmap[6 - i % 7, i // 7] = value

    last_week = (len(series) - 1) // 7
    # amount of reamining days in the current week
    remaining = 6 - datetime.date.today().weekday()
    # blank out remaning days
    cmap.set_under("#2f3136")
    for i in range(remaining):
        heatmap[i, last_week] = -1

    # get the coordinates, offset by 0.5 to align the ticks.
    y = np.arange(8) - 0.5
    x = np.arange(num_weeks + 1) - 0.5

    ax = plt.gca()
    mesh = ax.pcolormesh(x, y, heatmap, edgecolor="#2f3136", cmap=cmap, lw=2.5)

    ax.set_xticks(list(ticks.keys()))
    ax.set_xticklabels(list(ticks.values()))
    ax.xaxis.tick_top()

    ax.set_yticks(range(len(DAYS)))
    ax.set_yticklabels(reversed(DAYS))
    for label in ax.yaxis.get_ticklabels()[::2]:
        label.set_visible(False)

    plt.rcParams.update({"ytick.color": "white", "xtick.color": "white"})

    plt.sca(ax)
    plt.sci(mesh)

    return ax


def generate_heatmap(series: pd.Series, cmap: Optional[str] = None) -> plt.Figure:
    """
    series must have a DatimeIndex as index
    """
    assert isinstance(series.index, pd.DatetimeIndex)

    figsize = plt.figaspect(7 / 56)
    fig = plt.figure(figsize=figsize, facecolor="#2f3136")
    ax = plot_heatmap(series, cmap)

    minimum = series.min()
    maximum = series.max()
    plt.colorbar(ticks=np.linspace(minimum, maximum, 5, dtype=int), pad=0.02)

    # remove all undesired graphics
    for side in ("top", "right", "left", "bottom"):
        ax.spines[side].set_visible(False)
    plt.tick_params(length=0, width=0)

    # force cells to be squares
    ax.set_aspect("equal")
    plt.clim(minimum, maximum)

    return fig
