"""Monthly returns heatmap — the standard year × month grid + YTD column."""

from __future__ import annotations

import calendar

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import Rectangle

from scripts.factsheet import theme

MONTHS = list(calendar.month_abbr)[1:]  # Jan..Dec
YTD_COL_LABEL = "YTD"

# Diverging ramp — brand teal on the positive end, red-700 on the negative.
# Pivots through a near-neutral cream at zero so empty / near-flat months
# don't visually shout. Endpoint stops match the brand chart palette.
_DIVERGING = LinearSegmentedColormap.from_list(
    "unravel_diverging",
    [
        "#B91C1C",  # red-700        — strong negative
        "#EF6C4F",  # warm red
        "#FCA5A5",  # red-300
        "#FAFAF9",  # near-white     — zero
        "#5EEAD4",  # teal-300
        "#14B8A6",  # teal-500
        "#0D9488",  # teal-600       — strong positive (brand accent)
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


def _text_color_for(cell_rgba: tuple[float, float, float, float]) -> str:
    """WCAG-style relative luminance: white on dark cells, ink on light cells.

    Sampling the actual cell colour beats thresholding on the numeric value:
    the value's distance from zero doesn't tell you how dark its colour is
    (the ramp is asymmetric and we clamp it).
    """
    def _channel(v: float) -> float:
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4

    r, g, b, _a = cell_rgba
    lum = 0.2126 * _channel(r) + 0.7152 * _channel(g) + 0.0722 * _channel(b)
    return "#FFFFFF" if lum < 0.45 else theme.INK


def _fmt_cell(value: float) -> str:
    if pd.isna(value):
        return ""
    # 1 decimal place — a heatmap is for shape recognition, not data tables;
    # extra digits add visual density without adding meaning.
    formatted = f"{value * 100:.1f}"
    return formatted.replace("-", theme.MINUS)


def render_monthly_heatmap(
    fig: plt.Figure,
    returns: pd.Series,
    rect: tuple[float, float, float, float],
    *,
    title: str = "Monthly Returns (%)",
) -> None:
    """Draw a years × (12 months | YTD) heatmap inside the given figure rect.

    The YTD column is visually separated from the months: small gutter, white
    background, ruled outline — it's a summary, not a 13th month.
    """
    grid, ytd = _build_grid(returns)
    years = list(grid.index)

    # Robust vmax: cap at the 95th percentile of |monthly|. A single outlier
    # like 2021's +180% YTD or a heroic month would otherwise bleach the whole
    # ramp and make every other cell read as near-zero. Floor at 15% so the
    # palette still saturates on the typical month.
    flat_monthly = grid.values.astype("float64").flatten()
    flat_monthly = flat_monthly[~np.isnan(flat_monthly)]
    if flat_monthly.size:
        p95 = float(np.percentile(np.abs(flat_monthly), 95))
    else:
        p95 = 0.0
    abs_max = max(0.15, p95)
    norm = Normalize(vmin=-abs_max, vmax=abs_max)

    left, bottom, width, height = rect

    if title:
        fig.text(
            left,
            bottom + height + 0.022,
            title,
            fontsize=9.5,
            color=theme.INK,
            weight="semibold",
            va="bottom",
        )

    # Months grid takes ~12/13 of the width; YTD column lives in the remaining
    # slot with a clear gutter between them.
    months_w = width * (12 / 13.6)
    gutter = width * 0.022
    ytd_w = width - months_w - gutter

    ax_grid = fig.add_axes((left, bottom, months_w, height))
    ax_ytd = fig.add_axes((left + months_w + gutter, bottom, ytd_w, height))

    # ---- Months grid ----
    # Draw every cell as a vector Rectangle instead of imshow. imshow gets
    # embedded in the PDF as a raster and re-sampled by the downstream
    # rasteriser, which leaves faint grey seams; explicit patches tile
    # perfectly and stay crisp at any zoom.
    matrix = grid.values.astype("float64")
    rows, cols = matrix.shape
    for r in range(rows):
        for c in range(cols):
            value = matrix[r, c]
            if np.isnan(value):
                face = "#F5F5F5"  # empty / future month
                txt = ""
                txt_color = theme.MUTED
            else:
                rgba = _DIVERGING(norm(value))
                face = rgba
                txt = _fmt_cell(value)
                txt_color = _text_color_for(rgba)
            ax_grid.add_patch(
                Rectangle(
                    (c - 0.5, r - 0.5),
                    1.0,
                    1.0,
                    facecolor=face,
                    edgecolor="none",
                    antialiased=False,
                )
            )
            if txt:
                # Right-align so column values line up visually even with
                # proportional figures (mpl can't toggle OpenType tnum).
                ax_grid.text(
                    c + 0.42,
                    r,
                    txt,
                    ha="right",
                    va="center",
                    fontsize=7.5,
                    color=txt_color,
                )

    ax_grid.set_xlim(-0.5, cols - 0.5)
    ax_grid.set_ylim(rows - 0.5, -0.5)  # origin upper
    ax_grid.set_xticks(range(cols))
    ax_grid.set_xticklabels(grid.columns, fontsize=7.5, color=theme.MUTED)
    ax_grid.set_yticks(range(rows))
    # Drop the "20" prefix on year labels — repetitive after the first row.
    ax_grid.set_yticklabels(
        [f"’{y % 100:02d}" for y in years], fontsize=8, color=theme.MUTED
    )
    ax_grid.tick_params(axis="both", which="both", length=0)
    ax_grid.grid(False)
    for spine in ax_grid.spines.values():
        spine.set_visible(False)

    # ---- YTD column ----
    ytd_aligned = pd.Series([ytd.get(y, np.nan) for y in years], index=years).values
    # Render with a white background and bold ink text — no heatmap fill.
    # We draw a single Rectangle for the panel and let text float on top.
    for r, value in enumerate(ytd_aligned):
        # Faint background tint based on sign so the column still carries colour
        # cue but doesn't merge with December.
        if pd.notna(value):
            tint = theme.ACCENT_TINT if value >= 0 else theme.NEG_TINT
            ax_ytd.add_patch(
                Rectangle(
                    (-0.5, r - 0.5),
                    1.0,
                    1.0,
                    facecolor=tint,
                    edgecolor="none",
                )
            )
        # Coloured numerals reinforce the sign at-a-glance.
        if pd.isna(value):
            text_color = theme.MUTED
        elif value >= 0:
            text_color = theme.ACCENT
        else:
            text_color = theme.NEG
        ax_ytd.text(
            0.40,
            r,
            _fmt_cell(value),
            ha="right",
            va="center",
            fontsize=8,
            weight="bold",
            color=text_color,
        )

    ax_ytd.set_xlim(-0.5, 0.5)
    ax_ytd.set_ylim(rows - 0.5, -0.5)
    ax_ytd.set_xticks([0])
    ax_ytd.set_xticklabels([YTD_COL_LABEL], fontsize=7.5, color=theme.MUTED, weight="medium")
    ax_ytd.set_yticks([])
    ax_ytd.tick_params(axis="both", which="both", length=0)
    ax_ytd.grid(False)

    # Outline the whole YTD column to separate it from the months grid.
    for spine in ax_ytd.spines.values():
        spine.set_visible(True)
        spine.set_color(theme.HAIR)
        spine.set_linewidth(0.7)
