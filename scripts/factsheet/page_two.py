"""Page 2 — AlphaLens-style cross-sectional factor analysis.

Reading order (per the Claude Design critique):
    TL = Mean forward return by quantile  (does the signal separate?)
    TR = IC time-series + IC stats        (is the separation stable?)
    BL = Cumulative return by quantile    (what does it compound to?)
    BR = Q5 − Q1 spread                   (long–short equity curve)
"""

from __future__ import annotations

import textwrap
from datetime import date as _date
from pathlib import Path

import alphalens
import matplotlib.dates as mdates
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

from scripts.factors_catalog import Factor
from scripts.factsheet import metrics, theme
from scripts.factsheet.al_utils import clean_factor_data, quantile_palette

MARGIN_X = 0.07
RIGHT_X = 1.0 - MARGIN_X
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGO_PNG = REPO_ROOT / "branding" / "unravel-logo.png"


def _set_year_ticks(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _draw_header(fig: plt.Figure, factor: Factor) -> None:
    """Header — mirrors page 1: logo + Unravel wordmark left, page label right."""
    wordmark_x = MARGIN_X
    if LOGO_PNG.exists():
        img = mpimg.imread(LOGO_PNG)
        logo_h = 0.022
        aspect = img.shape[1] / img.shape[0]
        logo_w = logo_h * (theme.PAGE_H_IN / theme.PAGE_W_IN) * aspect
        ax_logo = fig.add_axes((MARGIN_X, 0.960 - logo_h / 2, logo_w, logo_h))
        ax_logo.imshow(img, interpolation="bilinear")
        ax_logo.axis("off")
        wordmark_x = MARGIN_X + logo_w + 0.010
    fig.text(
        wordmark_x,
        0.960,
        "Unravel",
        fontsize=13,
        fontweight="bold",
        color=theme.INK,
        va="center",
        family=theme.display_font(),
    )
    fig.text(
        RIGHT_X,
        0.960,
        f"Factor Analysis  ·  {factor.name}",
        fontsize=8,
        color=theme.MUTED,
        ha="right",
        va="center",
    )
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [0.940, 0.940], color=theme.HAIR, linewidth=0.6
        )
    )

    # Title block — same vertical anchor as page 1 so the two pages read as
    # siblings, not as different documents. Shorter wordmark than page 1
    # because the title text is longer.
    fig.text(
        MARGIN_X,
        0.908,
        "Factor Analysis",
        fontsize=36,
        fontweight="bold",
        color=theme.INK,
        va="top",
        family=theme.display_font(),
    )
    fig.text(
        MARGIN_X,
        0.855,
        textwrap.fill(
            (
                "Diagnostics on the raw factor values, independent of "
                "portfolio construction. The quintile and IC plots show "
                "whether the signal cross-sectionally separates "
                "outperformers from underperformers — and how consistently."
            ),
            width=110,
        ),
        fontsize=10,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.55,
    )
    fig.text(
        MARGIN_X,
        0.808,
        textwrap.fill(
            (
                f"Computed on the rolling Top {factor.default_universe} "
                "universe — membership reconstructed point-in-time on each "
                "date to avoid look-ahead bias. The factor itself covers a "
                "much larger universe of tokens (see the raw factor-data "
                "CSV in the data room)."
            ),
            width=128,
        ),
        fontsize=7.5,
        style="italic",
        color=theme.MUTED,
        va="top",
        linespacing=1.4,
    )


def _draw_footer(fig: plt.Figure, factor: Factor) -> None:
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [0.030, 0.030], color=theme.HAIR, linewidth=0.5
        )
    )
    fig.text(
        MARGIN_X,
        0.017,
        factor.detail_url,
        fontsize=7.5,
        color=theme.SUB_INK,
        weight="medium",
        va="center",
    )
    fig.text(
        RIGHT_X,
        0.017,
        f"Page 2 of 2    ·    {_date.today():%b %Y}",
        fontsize=7.5,
        color=theme.MUTED,
        ha="right",
        va="center",
    )


def _percent_formatter(ax: plt.Axes, axis: str = "y") -> None:
    """Format an axis as percent, with the real minus sign."""
    fmt = mtick.PercentFormatter(decimals=0)
    getattr(ax, f"{axis}axis").set_major_formatter(fmt)


def _strip_top_right(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(theme.HAIR)
    ax.spines["bottom"].set_color(theme.HAIR)


# ---- AlphaLens helpers ------------------------------------------------------

# We always pin the analysis to the 1-day forward return — that's the
# non-overlapping series, the one AlphaLens' default cumulative_returns()
# treats as `cumprod` without smoothing, and the one our daily-rebalanced
# illustrative portfolio uses on page 1.
PERIOD = "1D"


def _forward_return_period(clean: pd.DataFrame) -> str:
    """Return the column name to use as the forward-return — '1D' if AlphaLens
    produced it, otherwise the shortest forward-return column available."""
    fwd_cols = list(alphalens.utils.get_forward_returns_columns(clean.columns))
    if PERIOD in fwd_cols:
        return PERIOD
    # Sort by the numeric prefix so we get the shortest period.
    def _days(col: str) -> int:
        try:
            return int(str(col).rstrip("D"))
        except ValueError:
            return 10**9

    return sorted(fwd_cols, key=_days)[0]


def _mean_ic(clean: pd.DataFrame, period: str) -> float:
    ic = alphalens.performance.factor_information_coefficient(clean)
    return float(ic[period].mean())


# ---- Charts -----------------------------------------------------------------


def _plot_mean_return_by_quantile(ax: plt.Axes, clean: pd.DataFrame) -> None:
    """Overall mean forward return by quantile across all forward-return periods.

    Grouped bars per quantile, one colour per period (1D, 5D, 10D) — matches
    AlphaLens' plot_quantile_returns_bar exactly. `demeaned=True` so the bars
    are the alpha contribution, not raw absolute returns.
    """
    mean_q, _ = alphalens.performance.mean_return_by_quantile(
        clean, by_date=False, demeaned=True
    )
    periods = [c for c in mean_q.columns if str(c).endswith("D")]
    if not periods:
        periods = list(mean_q.columns)

    quantiles = list(mean_q.index)
    n_q = len(quantiles)
    n_p = len(periods)
    # Fill ~96% of each quantile slot so the bars use the available width.
    group_w = 0.96
    bar_w = group_w / max(n_p, 1)
    x_base = np.arange(n_q)
    # Single colour scheme — three shades of grey (dark = shortest period).
    grey_shades = [theme.INK, theme.MUTED, "#BDBDBD"][:n_p]
    for i, period in enumerate(periods):
        offset = (i - (n_p - 1) / 2) * bar_w
        ax.bar(
            x_base + offset,
            mean_q[period].values * 1e4,  # → bps
            width=bar_w,
            color=grey_shades[i],
            edgecolor="none",
            label=str(period),
        )
    ax.axhline(0, color=theme.HAIR, linewidth=0.6)
    ax.set_xticks(x_base)
    ax.set_xticklabels([str(q) for q in quantiles])
    ax.set_xlim(-0.5, n_q - 0.5)  # bars span the full panel width
    ax.margins(y=0.02)
    ax.set_title(
        "Mean Forward Return by Quantile  ·  demeaned",
        loc="left",
        color=theme.INK,
    )
    ax.set_xlabel("Quantile  (1 = lowest factor value, 5 = highest)")
    ax.set_ylabel("Alpha (bps / period)")
    ax.legend(loc="upper left", fontsize=7, ncol=n_p)
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    _strip_top_right(ax)


def _plot_ic_with_stats(ax: plt.Axes, clean: pd.DataFrame) -> None:
    """Daily IC time-series with 21-day MA and the long-run mean as a baseline."""
    period = _forward_return_period(clean)
    ic = alphalens.performance.factor_information_coefficient(clean)[period]
    rolling = ic.rolling(21, min_periods=5).mean()
    mean_ic = float(ic.mean())
    std_ic = float(ic.std())
    ir = mean_ic / std_ic if std_ic > 0 else float("nan")
    hit_rate = float((ic.dropna() > 0).mean())

    ax.bar(
        ic.index,
        ic.values,
        color=theme.HAIR,
        edgecolor="none",
        width=2.0,
        zorder=1,
    )
    # 21-day moving average — visual stability cue.
    ax.plot(
        rolling.index,
        rolling.values,
        color=theme.ACCENT,
        linewidth=1.4,
        zorder=2,
        label="21-day MA",
    )
    # Mean IC as a horizontal reference — standard AlphaLens IC plot.
    ax.axhline(
        mean_ic,
        color=theme.INK,
        linewidth=0.9,
        linestyle=(0, (3, 2)),
        zorder=3,
        label=f"Mean  {metrics.fmt_ratio(mean_ic, 4)}",
    )
    ax.axhline(0, color=theme.HAIR, linewidth=0.6)
    ax.set_ylabel("IC")
    # Fixed, symmetric scale so the chart reads consistently across factors
    # and the daily-IC noise band doesn't dominate the panel.
    ax.set_ylim(-0.3, 0.3)
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    ax.legend(loc="upper right", fontsize=7)
    _strip_top_right(ax)
    _set_year_ticks(ax)

    stats_line = (
        f"Mean {metrics.fmt_ratio(mean_ic, 4)}  ·  "
        f"Std {metrics.fmt_ratio(std_ic, 4)}  ·  "
        f"IR {metrics.fmt_ratio(ir, 2)}  ·  "
        f"{metrics.fmt_pct(hit_rate)} positive  ·  {period}"
    )
    ax.set_title(
        "Information Coefficient (Spearman)",
        loc="left",
        color=theme.INK,
        pad=18,
    )
    ax.text(
        0.0,
        1.02,
        stats_line,
        transform=ax.transAxes,
        fontsize=8,
        color=theme.SUB_INK,
        va="bottom",
        ha="left",
    )


def _quantile_daily_returns(clean: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """AlphaLens' canonical per-date / per-quantile mean (demeaned) forward
    returns. Returns a wide DataFrame indexed by date, columns are quantiles,
    plus the period name we used."""
    period = _forward_return_period(clean)
    mean_quant_daily, _ = alphalens.performance.mean_return_by_quantile(
        clean, by_date=True, demeaned=True
    )
    by_q = mean_quant_daily[period].unstack(level="factor_quantile")
    return by_q, period


def _plot_cumulative_quantile_returns(ax: plt.Axes, clean: pd.DataFrame) -> None:
    """Cumulative-return path per quantile, using AlphaLens' cumulative_returns
    helper so the math is identical to AlphaLens' plot_cumulative_returns_by_quantile.

    Log-scale y-axis — AlphaLens uses the same convention for this chart so
    that strong-spread factors don't squish Q2/Q3/Q4 against the x-axis when
    Q5 compounds to a large multiple (or Q1 collapses to a fraction).
    """
    by_q, period = _quantile_daily_returns(clean)
    cum = by_q.apply(alphalens.performance.cumulative_returns)
    colors = quantile_palette(cum.shape[1])
    for i, q in enumerate(cum.columns):
        ax.plot(
            cum.index,
            cum[q].values,
            label=f"Q{q}",
            linewidth=1.2,
            color=colors[i],
        )
    ax.set_yscale("log")
    ax.axhline(1.0, color=theme.HAIR, linewidth=0.5)
    ax.set_title(
        f"Cumulative Alpha by Quantile  ·  demeaned, {period}",
        loc="left",
        color=theme.INK,
    )
    ax.set_ylabel("Growth of 1.00  (log scale)")
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    ax.legend(loc="upper left", ncol=len(cum.columns), fontsize=7, columnspacing=1.2)
    _strip_top_right(ax)
    _set_year_ticks(ax)


def _plot_top_minus_bottom(ax: plt.Axes, clean: pd.DataFrame) -> None:
    """Top-minus-bottom quantile mean return — matches AlphaLens'
    plot_top_minus_bottom_quantile_mean_return: the daily spread (in bps) plus
    a 21-day moving average. We previously rendered this as a cumulative
    equity curve, but that produced a 5-year compounded multiple that's
    visually disconnected from the AlphaLens reference output (and the
    underlying daily spread of ~20 bps for retail_flow).

    Direction is picked from the historical quantile P&L — the chart
    always reads in the profitable direction.
    """
    by_q, period = _quantile_daily_returns(clean)
    if by_q.shape[1] < 2:
        ax.axis("off")
        return
    top_q = by_q.columns.max()
    bot_q = by_q.columns.min()
    if by_q[top_q].mean() >= by_q[bot_q].mean():
        long_q, short_q = top_q, bot_q
    else:
        long_q, short_q = bot_q, top_q

    spread_bps = (by_q[long_q] - by_q[short_q]) * 1e4
    ma = spread_bps.rolling(21, min_periods=5).mean()

    # Daily spread as soft grey bars (AlphaLens uses thin vertical lines).
    ax.bar(
        spread_bps.index,
        spread_bps.values,
        color=theme.HAIR,
        edgecolor="none",
        width=2.0,
        zorder=1,
    )
    # 21-day MA in brand teal — the signal we're really after.
    ax.plot(
        ma.index,
        ma.values,
        color=theme.ACCENT,
        linewidth=1.4,
        zorder=2,
        label="21-day MA",
    )
    mean_spread = float(spread_bps.mean())
    ax.axhline(
        mean_spread,
        color=theme.INK,
        linewidth=0.9,
        linestyle=(0, (3, 2)),
        zorder=3,
        label=f"Mean  {mean_spread:+.1f} bps".replace("-", theme.MINUS),
    )
    ax.axhline(0, color=theme.HAIR, linewidth=0.6)
    ax.set_title(
        f"Top minus Bottom Quantile Spread  (long Q{long_q}, short Q{short_q})",
        loc="left",
        color=theme.INK,
    )
    ax.set_ylabel(f"Spread ({period}, bps)")
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    ax.legend(loc="upper right", fontsize=7)
    _strip_top_right(ax)
    _set_year_ticks(ax)


def _empty_quant_page(factor: Factor, reason: str) -> plt.Figure:
    fig = theme.new_page()
    _draw_header(fig, factor)
    fig.text(
        0.5,
        0.5,
        f"Quantitative analysis unavailable\n\n{reason}",
        fontsize=11,
        color=theme.MUTED,
        ha="center",
        va="center",
    )
    _draw_footer(fig, factor)
    return fig


def render_page_two(
    factor: Factor, factor_data: pd.DataFrame, prices: pd.DataFrame
) -> plt.Figure:
    try:
        clean = clean_factor_data(factor_data, prices)
    except Exception as exc:  # noqa: BLE001
        return _empty_quant_page(factor, f"AlphaLens preparation failed: {exc}")

    fig = theme.new_page()
    _draw_header(fig, factor)

    # Three rows. Rows 1 and 2 span both columns — the grouped quantile bar
    # chart needs the width for its 3-period bars, and the log-scale
    # cumulative-by-quantile chart needs it to show all five lines without
    # squashing. Row 3 splits into IC and long-short side by side.
    gs = GridSpec(
        nrows=3,
        ncols=2,
        figure=fig,
        left=MARGIN_X,
        right=RIGHT_X,
        top=0.745,
        bottom=0.090,
        hspace=0.65,
        wspace=0.28,
        height_ratios=[1.0, 1.0, 1.0],
    )

    plotters = [
        (gs[0, :], _plot_mean_return_by_quantile, "Quantile means"),
        (gs[1, :], _plot_cumulative_quantile_returns, "Cumulative quantile"),
        (gs[2, 0], _plot_ic_with_stats, "IC"),
        (gs[2, 1], _plot_top_minus_bottom, "Long–short"),
    ]
    for slot, fn, label in plotters:
        ax = fig.add_subplot(slot)
        try:
            fn(ax, clean)
        except Exception as exc:  # noqa: BLE001
            ax.axis("off")
            ax.text(
                0.5,
                0.5,
                f"{label} unavailable: {exc}",
                ha="center",
                va="center",
                fontsize=8,
                color=theme.MUTED,
            )

    _draw_footer(fig, factor)
    return fig
