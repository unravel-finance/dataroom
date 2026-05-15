"""Page 2: AlphaLens-based quantitative analysis of the raw factor data."""

from __future__ import annotations

import warnings

import alphalens
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

from scripts.factors_catalog import Factor
from scripts.factsheet import metrics, theme


def _set_year_ticks(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _clean_factor_data(
    factor_data: pd.DataFrame,
    prices: pd.DataFrame,
    quantiles: int = 5,
) -> pd.DataFrame:
    """Run alphalens.utils.get_clean_factor_and_forward_returns on aligned data."""
    cols = factor_data.columns.intersection(prices.columns)
    if cols.empty:
        raise ValueError("No overlapping tickers between factor data and prices")
    signal = factor_data[cols].stack()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        clean = alphalens.utils.get_clean_factor_and_forward_returns(
            signal,
            prices[cols],
            quantiles=quantiles,
            periods=(1, 5, 10),
            max_loss=0.5,
        )
    return clean


MARGIN_X = 0.07
RIGHT_X = 1.0 - MARGIN_X


def _draw_header(fig: plt.Figure, factor: Factor) -> None:
    fig.text(
        MARGIN_X,
        0.963,
        f"Unravel  ·  {factor.name}",
        fontsize=8.5,
        color=theme.INK,
        weight="medium",
        va="center",
    )
    fig.text(
        RIGHT_X,
        0.963,
        "Factor Factsheet",
        fontsize=8.5,
        color=theme.MUTED,
        weight="medium",
        ha="right",
        va="center",
    )
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [0.935, 0.935], color=theme.HAIR, linewidth=0.6
        )
    )

    fig.text(
        MARGIN_X,
        0.895,
        "Cross-Sectional Factor Analysis",
        fontsize=22,
        fontweight="bold",
        color=theme.INK,
        va="top",
    )
    fig.text(
        MARGIN_X,
        0.860,
        (
            "Diagnostics on the raw factor values, independent of any "
            "portfolio construction. The quintile and IC plots show whether "
            "the signal cross-sectionally separates outperformers from "
            "underperformers — and how consistently."
        ),
        fontsize=9.5,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.5,
        wrap=True,
    )


def _draw_footer(fig: plt.Figure, factor: Factor) -> None:
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [0.052, 0.052], color=theme.HAIR, linewidth=0.5
        )
    )
    fig.text(
        MARGIN_X,
        0.032,
        factor.detail_url,
        fontsize=7.5,
        color=theme.SUB_INK,
        weight="medium",
        va="center",
    )
    fig.text(
        RIGHT_X,
        0.032,
        "Page 2 of 2  ·  AlphaLens factor analysis",
        fontsize=7,
        color=theme.MUTED,
        ha="right",
        va="center",
    )


def _quantile_palette(n: int) -> list[str]:
    """Diverging-ish palette: lowest quantile = neg, top = brand teal."""
    cmap = sns.color_palette("RdYlGn", n).as_hex()
    cmap[-1] = theme.ACCENT
    cmap[0] = theme.NEG
    return cmap


def _plot_mean_return_by_quantile(ax: plt.Axes, clean: pd.DataFrame) -> None:
    mean_q, _ = alphalens.performance.mean_return_by_quantile(clean, by_date=False)
    # mean_q is indexed by factor_quantile, columns are period strings
    period_col = mean_q.columns[0]
    values = mean_q[period_col]
    quantiles = values.index.tolist()
    colors = _quantile_palette(len(quantiles))
    bars = ax.bar(
        [str(q) for q in quantiles],
        values.values * 1e4,  # show in bps for readability
        color=colors,
        edgecolor="none",
    )
    ax.axhline(0, color=theme.HAIR, linewidth=0.6)
    ax.set_title("Mean Forward Return by Quantile (bps)", loc="left")
    ax.set_xlabel("Quantile (1 = lowest, 5 = highest)")
    ax.set_ylabel("Mean Return (bps)")
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)


def _plot_cumulative_quantile_returns(ax: plt.Axes, clean: pd.DataFrame) -> None:
    period_col = [c for c in clean.columns if isinstance(c, str) and c.endswith("D")]
    period = period_col[0] if period_col else clean.columns[0]
    by_q = clean.groupby(
        ["date", "factor_quantile"], observed=True
    )[period].mean().unstack(level=1)
    cum = (1.0 + by_q).cumprod()
    colors = _quantile_palette(cum.shape[1])
    for i, q in enumerate(cum.columns):
        ax.plot(cum.index, cum[q].values, label=f"Q{q}", linewidth=1.2, color=colors[i])
    ax.set_title("Cumulative Return by Quantile", loc="left")
    ax.set_ylabel("Growth of $1")
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    ax.legend(loc="upper left", ncol=len(cum.columns), fontsize=7, columnspacing=1.2)
    _set_year_ticks(ax)


def _plot_ic_timeseries(ax: plt.Axes, clean: pd.DataFrame) -> None:
    ic = alphalens.performance.factor_information_coefficient(clean)
    period_col = ic.columns[0]
    series = ic[period_col]
    series_rolling = series.rolling(21, min_periods=5).mean()
    ax.bar(
        series.index,
        series.values,
        color=theme.HAIR,
        edgecolor="none",
        width=2.0,
        zorder=1,
    )
    ax.plot(
        series_rolling.index,
        series_rolling.values,
        color=theme.INK,
        linewidth=1.2,
        zorder=2,
        label="21d MA",
    )
    ax.axhline(0, color=theme.HAIR, linewidth=0.6)
    mean_ic = float(series.mean())
    ax.set_title(
        f"Information Coefficient — mean IC: {mean_ic:.4f}", loc="left"
    )
    ax.set_ylabel("IC")
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    ax.legend(loc="upper right", fontsize=7)
    _set_year_ticks(ax)


def _plot_top_minus_bottom(ax: plt.Axes, clean: pd.DataFrame) -> None:
    period_col = [c for c in clean.columns if isinstance(c, str) and c.endswith("D")]
    period = period_col[0] if period_col else clean.columns[0]
    by_q = clean.groupby(
        ["date", "factor_quantile"], observed=True
    )[period].mean().unstack(level=1)
    if by_q.shape[1] < 2:
        ax.axis("off")
        return
    top_q = by_q.columns.max()
    bot_q = by_q.columns.min()
    spread = by_q[top_q] - by_q[bot_q]
    eq = (1.0 + spread).cumprod()
    ax.plot(eq.index, eq.values, color=theme.ACCENT, linewidth=1.4)
    ax.fill_between(
        eq.index, 1.0, eq.values, where=(eq.values >= 1.0),
        color=theme.ACCENT, alpha=0.07, linewidth=0
    )
    ax.axhline(1.0, color=theme.HAIR, linewidth=0.5)
    ax.set_title(
        f"Top minus Bottom Quantile (Q{top_q} − Q{bot_q})", loc="left"
    )
    ax.set_ylabel("Growth of $1")
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    _set_year_ticks(ax)


def _ic_summary(clean: pd.DataFrame) -> dict[str, float]:
    ic = alphalens.performance.factor_information_coefficient(clean)
    period_col = ic.columns[0]
    s = ic[period_col].dropna()
    if s.empty:
        return {}
    mean_ic = float(s.mean())
    std_ic = float(s.std())
    return {
        "mean_ic": mean_ic,
        "std_ic": std_ic,
        "ir": mean_ic / std_ic if std_ic > 0 else float("nan"),
        "hit_rate": float((s > 0).mean()),
    }


def _draw_ic_panel(fig: plt.Figure, clean: pd.DataFrame) -> None:
    summary = _ic_summary(clean)
    if not summary:
        return
    cards = [
        ("Mean IC", f"{summary['mean_ic']:.4f}"),
        ("IC Std", f"{summary['std_ic']:.4f}"),
        ("IR (Mean / Std)", f"{summary['ir']:.2f}"),
        ("IC Hit-Rate", metrics.fmt_pct(summary["hit_rate"])),
    ]
    n = len(cards)
    width = RIGHT_X - MARGIN_X
    card_w = width / n
    h = 0.05
    y = 0.78
    # Top + bottom rules — column-separator style, no card chrome.
    fig.add_artist(
        plt.Line2D([MARGIN_X, RIGHT_X], [y + h, y + h], color=theme.HAIR, linewidth=0.5)
    )
    fig.add_artist(
        plt.Line2D([MARGIN_X, RIGHT_X], [y, y], color=theme.HAIR, linewidth=0.5)
    )
    for i, (label, value) in enumerate(cards):
        x = MARGIN_X + i * card_w
        if i > 0:
            fig.add_artist(
                plt.Line2D(
                    [x, x], [y, y + h], color=theme.HAIR, linewidth=0.5
                )
            )
        fig.text(
            x + card_w / 2,
            y + h * 0.72,
            label,
            fontsize=7.5,
            color=theme.MUTED,
            ha="center",
            va="center",
            weight="medium",
        )
        fig.text(
            x + card_w / 2,
            y + h * 0.32,
            value,
            fontsize=15,
            color=theme.INK,
            ha="center",
            va="center",
            weight="bold",
        )


def _empty_quant_page(
    factor: Factor, reason: str
) -> plt.Figure:
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
        clean = _clean_factor_data(factor_data, prices)
    except Exception as exc:  # noqa: BLE001
        return _empty_quant_page(factor, f"AlphaLens preparation failed: {exc}")

    fig = theme.new_page()
    _draw_header(fig, factor)
    _draw_ic_panel(fig, clean)

    gs = GridSpec(
        nrows=2,
        ncols=2,
        figure=fig,
        left=MARGIN_X,
        right=RIGHT_X,
        top=0.73,
        bottom=0.085,
        hspace=0.45,
        wspace=0.28,
    )

    try:
        _plot_ic_timeseries(fig.add_subplot(gs[0, 0]), clean)
    except Exception as exc:  # noqa: BLE001
        ax = fig.add_subplot(gs[0, 0])
        ax.axis("off")
        ax.text(0.5, 0.5, f"IC unavailable: {exc}", ha="center", va="center")

    try:
        _plot_mean_return_by_quantile(fig.add_subplot(gs[0, 1]), clean)
    except Exception as exc:  # noqa: BLE001
        ax = fig.add_subplot(gs[0, 1])
        ax.axis("off")
        ax.text(0.5, 0.5, f"Quantile return unavailable: {exc}", ha="center", va="center")

    try:
        _plot_cumulative_quantile_returns(fig.add_subplot(gs[1, 0]), clean)
    except Exception as exc:  # noqa: BLE001
        ax = fig.add_subplot(gs[1, 0])
        ax.axis("off")
        ax.text(0.5, 0.5, f"Cumulative quantile unavailable: {exc}", ha="center", va="center")

    try:
        _plot_top_minus_bottom(fig.add_subplot(gs[1, 1]), clean)
    except Exception as exc:  # noqa: BLE001
        ax = fig.add_subplot(gs[1, 1])
        ax.axis("off")
        ax.text(0.5, 0.5, f"Top–Bottom unavailable: {exc}", ha="center", va="center")

    _draw_footer(fig, factor)
    return fig
