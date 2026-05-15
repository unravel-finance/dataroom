"""Monthly returns heatmap — the standard year × month grid + YTD column."""

from __future__ import annotations

import calendar

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize

from scripts.factsheet import theme

MONTHS = list(calendar.month_abbr)[1:]  # Jan..Dec
YTD_COL_LABEL = "YTD"

# RdYlGn — same family the user's reference screenshot uses.
_DIVERGING = LinearSegmentedColormap.from_list(
    "unravel_diverging",
    [
        "#B91C1C",  # strong negative
        "#EF6C4F",
        "#FCD34D",
        "#FEF3C7",
        "#D9F99D",
        "#86EFAC",
        "#0F766E",  # strong positive — brand teal
    ],
)


def _monthly_pct(returns: pd.Series) -> pd.Series:
    return (1.0 + returns.fillna(0.0)).resample("ME").prod() - 1.0


def _ytd(returns: pd.Series) -> pd.Series:
    yearly = (1.0 + returns.fillna(0.0)).groupby(returns.index.year).prod() - 1.0
    yearly.index.name = "year"
    return yearly


def _build_grid(returns: pd.Series) -> tuple[pd.DataFrame, pd.Series]:
    monthly = _monthly_pct(returns)
    grid = pd.DataFrame(
        index=sorted(set(monthly.index.year)),
        columns=list(range(1, 13)),
        dtype="float64",
    )
    for ts, val in monthly.items():
        grid.at[ts.year, ts.month] = val
    grid.columns = MONTHS
    ytd = _ytd(returns)
    return grid, ytd


def _text_color_for(value: float, vmax: float) -> str:
    """White text on darker cells, ink on lighter cells."""
    if pd.isna(value):
        return theme.MUTED
    if abs(value) >= 0.55 * vmax:
        return "#FFFFFF"
    return theme.INK


def _fmt_cell(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value * 100:.2f}"


def render_monthly_heatmap(
    fig: plt.Figure,
    returns: pd.Series,
    rect: tuple[float, float, float, float],
    *,
    title: str = "Monthly Returns (%)",
) -> None:
    """Draw a years × (12 months + YTD) heatmap inside the given figure rect."""
    grid, ytd = _build_grid(returns)
    years = list(grid.index)

    abs_max = float(
        np.nanmax(
            np.abs(
                np.concatenate(
                    [grid.values.flatten(), ytd.values.astype("float64").flatten()]
                )
            )
        )
    )
    if not np.isfinite(abs_max) or abs_max == 0:
        abs_max = 1.0
    norm = Normalize(vmin=-abs_max, vmax=abs_max)

    left, bottom, width, height = rect

    if title:
        # Title above the grid.
        fig.text(
            left,
            bottom + height + 0.022,
            title,
            fontsize=9.5,
            color=theme.INK,
            weight="semibold",
            va="bottom",
        )

    # Two axes: the months grid and the narrow YTD column. They share the
    # same y-axis so years line up.
    months_w = width * (12 / 13.4)  # leave space for YTD column
    gap = width * 0.012
    ytd_w = width - months_w - gap

    ax_grid = fig.add_axes((left, bottom, months_w, height))
    ax_ytd = fig.add_axes((left + months_w + gap, bottom, ytd_w, height))

    # ---- Months grid ----
    matrix = grid.values.astype("float64")
    rows, cols = matrix.shape
    ax_grid.imshow(
        matrix,
        aspect="auto",
        cmap=_DIVERGING,
        norm=norm,
        origin="upper",
        interpolation="nearest",
    )
    # Empty cells (NaN) need a fill — overlay light grey for missing months.
    nan_mask = np.isnan(matrix)
    if nan_mask.any():
        overlay = np.where(nan_mask, 1.0, np.nan)
        ax_grid.imshow(
            overlay,
            aspect="auto",
            cmap=mcolors.ListedColormap(["#F5F5F5"]),
            origin="upper",
            interpolation="nearest",
            alpha=1.0,
        )

    # Cell labels + thin separators
    for r in range(rows):
        for c in range(cols):
            value = matrix[r, c]
            ax_grid.text(
                c,
                r,
                _fmt_cell(value),
                ha="center",
                va="center",
                fontsize=7.5,
                color=_text_color_for(value, abs_max),
            )
    ax_grid.set_xticks(range(cols))
    ax_grid.set_xticklabels(grid.columns, fontsize=7.5, color=theme.MUTED)
    ax_grid.set_yticks(range(rows))
    ax_grid.set_yticklabels(years, fontsize=7.5, color=theme.MUTED)
    ax_grid.tick_params(axis="both", which="both", length=0)
    for spine in ax_grid.spines.values():
        spine.set_visible(False)

    # Inner grid lines for cell separation
    for x in range(cols + 1):
        ax_grid.axvline(x - 0.5, color="white", linewidth=1.2)
    for y in range(rows + 1):
        ax_grid.axhline(y - 0.5, color="white", linewidth=1.2)

    # ---- YTD column ----
    ytd_aligned = pd.Series([ytd.get(y, np.nan) for y in years], index=years).values
    ytd_matrix = ytd_aligned.reshape(-1, 1)
    ax_ytd.imshow(
        ytd_matrix,
        aspect="auto",
        cmap=_DIVERGING,
        norm=norm,
        origin="upper",
        interpolation="nearest",
    )
    for r, value in enumerate(ytd_aligned):
        ax_ytd.text(
            0,
            r,
            _fmt_cell(value),
            ha="center",
            va="center",
            fontsize=7.5,
            weight="bold",
            color=_text_color_for(value, abs_max),
        )
    ax_ytd.set_xticks([0])
    ax_ytd.set_xticklabels([YTD_COL_LABEL], fontsize=7.5, color=theme.MUTED)
    ax_ytd.set_yticks([])
    ax_ytd.tick_params(axis="both", which="both", length=0)
    for spine in ax_ytd.spines.values():
        spine.set_visible(False)
    for y in range(len(years) + 1):
        ax_ytd.axhline(y - 0.5, color="white", linewidth=1.2)
