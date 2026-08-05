"""Calibration delta plots."""

from math import ceil

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


COLORS = {"home": "#2563eb", "draw": "#d97706", "away": "#059669"}


def _panel(ax, table, title):
    for outcome, rows in table.groupby("outcome", sort=False):
        ax.plot(rows.avg_pred, rows.error, "o-", ms=3.5, lw=1.4, label=outcome.title(), color=COLORS[outcome])
    ax.axhline(0, color="#4b5563", lw=1, ls="--")
    ax.set(title=title, xlabel="Average inferred probability", ylabel="Actual − inferred probability")
    ax.grid(alpha=0.2)
    ax.legend(frameon=False)


def plot(table, group, title, path):
    """Plot one panel overall or one panel per group."""
    groups = list(table[group].drop_duplicates()) if group else [title]
    columns = min(2, len(groups))
    rows = ceil(len(groups) / columns)
    fig, axes = plt.subplots(rows, columns, figsize=(8 if not group else 12, 5 if not group else 4.5 * rows), squeeze=False)
    for ax, name in zip(axes.flat, groups):
        _panel(ax, table[table[group] == name] if group else table, str(name))
    for ax in axes.flat[len(groups):]:
        ax.set_visible(False)
    if group:
        fig.suptitle(title, fontsize=15)
    fig.tight_layout(rect=(0, 0, 1, 0.97) if group else None)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)
