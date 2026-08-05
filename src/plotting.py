"""Plotting helpers for market calibration tables."""

from __future__ import annotations

from math import ceil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


COLORS = {"home": "#2563eb", "draw": "#d97706", "away": "#059669"}


def _plot_table(ax: plt.Axes, table: pd.DataFrame, title: str) -> None:
    for outcome, group in table.groupby("outcome", sort=False):
        ax.plot(
            group["avg_pred"],
            group["error"],
            marker="o",
            markersize=3.5,
            linewidth=1.4,
            label=outcome.title(),
            color=COLORS[outcome],
        )
    ax.axhline(0, color="#4b5563", linewidth=1, linestyle="--")
    ax.set_title(title)
    ax.set_xlabel("Average inferred probability")
    ax.set_ylabel("Actual − inferred probability")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)


def plot_calibration(table: pd.DataFrame, title: str, output_path: Path) -> None:
    """Plot Home / Draw / Away calibration deltas for one scope."""
    fig, ax = plt.subplots(figsize=(8, 5))
    _plot_table(ax, table, title)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def plot_grouped_calibration(
    table: pd.DataFrame, group_column: str, title: str, output_path: Path
) -> None:
    """Plot one calibration-delta panel per group."""
    groups = list(table[group_column].drop_duplicates())
    columns = 2
    rows = ceil(len(groups) / columns)
    fig, axes = plt.subplots(rows, columns, figsize=(12, 4.5 * rows), squeeze=False)
    for ax, group_name in zip(axes.flat, groups):
        group = table[table[group_column] == group_name]
        _plot_table(ax, group, str(group_name))
    for ax in axes.flat[len(groups) :]:
        ax.set_visible(False)
    fig.suptitle(title, fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=160, bbox_inches="tight")
    plt.close(fig)
