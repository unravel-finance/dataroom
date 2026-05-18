"""Page 1 — narrative + monthly returns heatmap + KPI strip + cumulative chart.

Hierarchy (top → bottom):

    header rule
    title  ·  subtitle                                        | quantile-alpha bars
    pull quote (optional, `factor.effect`)
    overview (2-col, justified)
    EXAMPLE TOP N CROSS-SECTIONAL PORTFOLIO
        MONTHLY RETURNS    · monthly heatmap
        RISK & RETURN      · KPI strip
        CUMULATIVE RETURN  · full-width equity curve
    italic disclaimer + About Unravel paragraph
    URL  ·  page indicator
"""

from __future__ import annotations

import textwrap
from datetime import date as _date
from pathlib import Path

import alphalens
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scripts.factors_catalog import Factor
from scripts.factsheet import metrics, theme
from scripts.factsheet.al_utils import quantile_palette
from scripts.factsheet.heatmap import render_monthly_heatmap

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGO_PNG = REPO_ROOT / "branding" / "unravel-logo.png"

MARGIN_X = 0.07
RIGHT_X = 1.0 - MARGIN_X
COL_WIDTH = RIGHT_X - MARGIN_X

# Wrap width for overview body text. Measured: ~60ch at 8.5pt Mona Sans fits
# the 3.46in per-column slot with safe margin (longest lines never overflow
# into the column gutter).
OVERVIEW_COL_CH = 60


# ---------- low-level helpers -------------------------------------------------


def _wrap(text: str, width: int) -> str:
    return textwrap.fill(text, width=width)


def _hline(fig: plt.Figure, y: float, *, lw: float = 0.6, color: str | None = None) -> None:
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [y, y], color=color or theme.HAIR, linewidth=lw
        )
    )


# ---------- header ------------------------------------------------------------


def _draw_logo(fig: plt.Figure) -> None:
    if not LOGO_PNG.exists():
        fig.text(
            MARGIN_X,
            0.960,
            "Unravel",
            fontsize=14,
            fontweight="bold",
            color=theme.INK,
            va="center",
            family=theme.display_font(),
        )
        return
    img = mpimg.imread(LOGO_PNG)
    logo_h = 0.022
    aspect = img.shape[1] / img.shape[0]
    logo_w = logo_h * (theme.PAGE_H_IN / theme.PAGE_W_IN) * aspect
    ax_logo = fig.add_axes((MARGIN_X, 0.960 - logo_h / 2, logo_w, logo_h))
    ax_logo.imshow(img, interpolation="bilinear")
    ax_logo.axis("off")
    fig.text(
        MARGIN_X + logo_w + 0.010,
        0.960,
        "Unravel",
        fontsize=13,
        fontweight="bold",
        color=theme.INK,
        va="center",
        family=theme.display_font(),
    )


def _draw_header(fig: plt.Figure, factor: Factor) -> None:
    _draw_logo(fig)
    fig.text(
        RIGHT_X,
        0.960,
        f"Generated {_date.today():%b %Y}",
        fontsize=8,
        color=theme.MUTED,
        ha="right",
        va="center",
    )
    _hline(fig, 0.940)


# ---------- hero --------------------------------------------------------------


def _draw_hero(
    fig: plt.Figure, factor: Factor, clean: pd.DataFrame | None
) -> None:
    fig.text(
        MARGIN_X - 0.001,
        0.908,
        factor.name,
        fontsize=36,
        fontweight="bold",
        color=theme.INK,
        va="top",
        family=theme.display_font(),
    )
    fig.text(
        MARGIN_X,
        0.853,
        _wrap(factor.short_description, width=52),
        fontsize=11,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.4,
    )
    if clean is not None:
        _draw_top_right_quantile_bars(fig, clean)


def _draw_top_right_quantile_bars(fig: plt.Figure, clean: pd.DataFrame) -> None:
    """Mini quantile-alpha chart — 5 bars (Q1..Q5) of demeaned 1D mean
    forward return. Sits where the sparkline used to. Same data source as the
    full-width bar chart on page 2."""
    try:
        mean_q, _ = alphalens.performance.mean_return_by_quantile(
            clean, by_date=False, demeaned=True
        )
    except Exception:  # noqa: BLE001 — degrade gracefully
        return
    period = "1D" if "1D" in mean_q.columns else mean_q.columns[0]
    values = mean_q[period].values * 1e4  # → bps
    quantiles = list(mean_q.index)
    colors = quantile_palette(len(quantiles))

    spark_left = MARGIN_X + 0.66 * COL_WIDTH
    spark_w = COL_WIDTH - 0.66 * COL_WIDTH
    spark_bottom = 0.840
    spark_h = 0.060

    fig.text(
        spark_left,
        spark_bottom + spark_h + 0.012,
        "MEAN ALPHA BY QUANTILE  ·  1D (BPS)",
        fontsize=6.5,
        color=theme.MUTED,
        weight="semibold",
        ha="left",
        va="bottom",
    )
    ax = fig.add_axes((spark_left, spark_bottom, spark_w, spark_h))
    ax.bar(
        [str(q) for q in quantiles],
        values,
        color=colors,
        edgecolor="none",
        width=0.78,
    )
    ax.axhline(0, color=theme.HAIR, linewidth=0.5)
    ax.tick_params(axis="x", which="both", length=0, labelsize=6.5, colors=theme.MUTED, pad=1)
    ax.tick_params(axis="y", which="both", length=0, labelsize=6.0, colors=theme.MUTED)
    for spine_name in ("top", "right", "left"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_color(theme.HAIR)
    ax.spines["bottom"].set_linewidth(0.5)


# ---------- pull quote --------------------------------------------------------


def _draw_pull_quote(fig: plt.Figure, factor: Factor) -> None:
    if not factor.effect:
        return
    y_top = 0.788
    y_bot = 0.728
    _hline(fig, y_top, lw=0.6)
    _hline(fig, y_bot, lw=0.6)
    mark_x = MARGIN_X
    mark_w = 0.0035
    fig.add_artist(
        mpatches.Rectangle(
            (mark_x, y_bot + 0.010),
            mark_w,
            y_top - y_bot - 0.020,
            transform=fig.transFigure,
            facecolor=theme.ACCENT,
            edgecolor="none",
            zorder=2,
        )
    )
    fig.text(
        mark_x + mark_w + 0.010,
        y_top - 0.012,
        _wrap(factor.effect, width=88),
        fontsize=12,
        color=theme.INK,
        va="top",
        linespacing=1.35,
        family=theme.display_font(),
        weight="regular",
    )


# ---------- justified overview body -------------------------------------------


def _measure_text_width_frac(
    fig: plt.Figure, text: str, fontsize: float
) -> float:
    """Width of `text` rendered at `fontsize`, in figure-fraction units."""
    renderer = fig.canvas.get_renderer()
    t = fig.text(0, 0, text, fontsize=fontsize)
    px = t.get_window_extent(renderer=renderer).width
    t.remove()
    return px / (fig.dpi * theme.PAGE_W_IN)


def _render_justified_line(
    fig: plt.Figure,
    x_frac: float,
    y_frac: float,
    line: str,
    fontsize: float,
    color: str,
    column_width_frac: float,
) -> None:
    """Render `line` filling exactly `column_width_frac`, distributing extra
    space evenly between words. Single-word lines fall back to left-align."""
    words = line.split()
    if len(words) <= 1:
        fig.text(x_frac, y_frac, line, fontsize=fontsize, color=color, va="top")
        return
    word_widths = [_measure_text_width_frac(fig, w, fontsize) for w in words]
    total_word_w = sum(word_widths)
    gap = (column_width_frac - total_word_w) / (len(words) - 1)
    # Safety: if the line is already wider than the column, don't try to
    # compress (gap would go negative) — just render left-aligned.
    if gap < 0:
        fig.text(x_frac, y_frac, line, fontsize=fontsize, color=color, va="top")
        return
    cur = x_frac
    for word, w in zip(words, word_widths):
        fig.text(cur, y_frac, word, fontsize=fontsize, color=color, va="top")
        cur += w + gap


def _render_justified_block(
    fig: plt.Figure,
    x_frac: float,
    y_top: float,
    column_width_frac: float,
    text: str,
    *,
    fontsize: float,
    color: str,
    linespacing: float,
    wrap_chars: int,
    paragraph_gap: float = 0.6,
) -> None:
    """Render `text` as a justified column. Last line of each paragraph stays
    ragged-right (typographic convention)."""
    line_height_frac = (fontsize * linespacing / 72.0) / theme.PAGE_H_IN
    paragraph_gap_frac = line_height_frac * paragraph_gap

    paragraphs = [
        p.strip().replace("\n", " ") for p in text.split("\n\n") if p.strip()
    ]
    y = y_top
    for p_idx, paragraph in enumerate(paragraphs):
        lines = textwrap.wrap(paragraph, width=wrap_chars, break_long_words=False)
        for i, line in enumerate(lines):
            is_last = i == len(lines) - 1
            if is_last:
                fig.text(x_frac, y, line, fontsize=fontsize, color=color, va="top")
            else:
                _render_justified_line(
                    fig, x_frac, y, line, fontsize, color, column_width_frac
                )
            y -= line_height_frac
        if p_idx < len(paragraphs) - 1:
            y -= paragraph_gap_frac


def _draw_overview(fig: plt.Figure, factor: Factor, y_top: float) -> None:
    """Two justified columns of the long description, paragraphs balanced by
    rough line count."""
    paragraphs = [
        p.strip().replace("\n", " ")
        for p in factor.long_description.split("\n\n")
        if p.strip()
    ]
    if not paragraphs:
        return
    # Balance the two columns by visual line count.
    line_counts = [
        len(textwrap.wrap(p, width=OVERVIEW_COL_CH, break_long_words=False))
        for p in paragraphs
    ]
    total = sum(line_counts)
    running = 0
    split = len(paragraphs)
    for i, n in enumerate(line_counts):
        if running + n >= total / 2:
            split = i + 1
            break
        running += n
    left_text = "\n\n".join(paragraphs[:split])
    right_text = "\n\n".join(paragraphs[split:])

    col_gap = 0.022
    col_w = (COL_WIDTH - col_gap) / 2

    _render_justified_block(
        fig,
        x_frac=MARGIN_X,
        y_top=y_top,
        column_width_frac=col_w,
        text=left_text,
        fontsize=8.5,
        color=theme.SUB_INK,
        linespacing=1.55,
        wrap_chars=OVERVIEW_COL_CH,
    )
    _render_justified_block(
        fig,
        x_frac=MARGIN_X + col_w + col_gap,
        y_top=y_top,
        column_width_frac=col_w,
        text=right_text,
        fontsize=8.5,
        color=theme.SUB_INK,
        linespacing=1.55,
        wrap_chars=OVERVIEW_COL_CH,
    )


# ---------- section divider ---------------------------------------------------


def _draw_section_eyebrow(
    fig: plt.Figure,
    y: float,
    label: str,
    *,
    right_label: str = "",
    sub_label: str = "",
) -> None:
    """Section divider. Title left + optional caption right + thin rule above.

    When ``sub_label`` is set it sits underneath the title as a muted
    one-liner."""
    _hline(fig, y + 0.013, lw=0.6)
    fig.text(
        MARGIN_X,
        y,
        label.upper(),
        fontsize=8,
        color=theme.INK,
        weight="semibold",
        va="top",
    )
    if right_label:
        fig.text(
            RIGHT_X,
            y,
            right_label,
            fontsize=8,
            color=theme.MUTED,
            va="top",
            ha="right",
        )
    if sub_label:
        # Wrap to the full text column so the sub-label never spills past
        # the right margin even on factors with long universe descriptions.
        fig.text(
            MARGIN_X,
            y - 0.013,
            _wrap(sub_label, width=140),
            fontsize=7.5,
            color=theme.MUTED,
            va="top",
            linespacing=1.4,
        )


# ---------- KPI strip ---------------------------------------------------------


def _draw_kpi_strip(fig: plt.Figure, stats: metrics.Stats, y: float) -> None:
    """Six-card KPI strip. Slightly compressed (h=0.065) so the cumulative
    chart fits below the strip on the same page."""
    cards = [
        ("CAGR",          metrics.fmt_pct(stats.cagr),         "since inception"),
        ("Volatility",    metrics.fmt_pct(stats.annual_vol),   "annualised"),
        ("Sharpe",        metrics.fmt_ratio(stats.sharpe),     "vs. RFR = 0"),
        ("Sortino",       metrics.fmt_ratio(stats.sortino),    "downside-only"),
        ("Max Drawdown",  metrics.fmt_pct(stats.max_drawdown), "peak-to-trough"),
    ]
    n = len(cards)
    card_w = COL_WIDTH / n
    card_h = 0.065
    for i, (label, value, sub) in enumerate(cards):
        x = MARGIN_X + i * card_w
        if i > 0:
            fig.add_artist(
                plt.Line2D(
                    [x, x],
                    [y, y + card_h],
                    color=theme.HAIR,
                    linewidth=0.5,
                )
            )
        fig.text(
            x + 0.012,
            y + card_h - 0.006,
            label.upper(),
            fontsize=7.0,
            color=theme.MUTED,
            ha="left",
            va="top",
            weight="semibold",
        )
        fig.text(
            x + 0.012,
            y + card_h * 0.48,
            value,
            fontsize=16,
            color=theme.INK,
            ha="left",
            va="center",
            weight="bold",
            family=theme.display_font(),
        )
        fig.text(
            x + 0.012,
            y + 0.006,
            sub,
            fontsize=6.5,
            color=theme.MUTED,
            ha="left",
            va="bottom",
        )
    _hline(fig, y + card_h, lw=0.6)
    _hline(fig, y, lw=0.6)


# ---------- cumulative-return chart (below KPI strip) -------------------------


def _draw_cumulative_chart(
    fig: plt.Figure, returns: pd.Series, rect: tuple[float, float, float, float]
) -> None:
    r = returns.dropna()
    if r.empty:
        return
    eq = (1.0 + r).cumprod()
    left, bottom, width, height = rect

    ax = fig.add_axes((left, bottom, width, height))
    x = np.arange(len(eq))
    y_arr = eq.values
    ax.axhline(1.0, color=theme.HAIR, linewidth=0.6, linestyle=(0, (1.5, 1.5)))
    ax.fill_between(
        x, 1.0, y_arr, where=(y_arr >= 1.0),
        color=theme.ACCENT, alpha=0.10, linewidth=0,
    )
    ax.fill_between(
        x, 1.0, y_arr, where=(y_arr < 1.0),
        color=theme.NEG, alpha=0.08, linewidth=0,
    )
    ax.plot(x, y_arr, color=theme.INK, linewidth=1.1)
    ax.scatter([x[-1]], [y_arr[-1]], s=18, color=theme.ACCENT, zorder=3, linewidth=0)

    years = sorted({d.year for d in eq.index})
    tick_positions: list[int] = []
    tick_labels: list[str] = []
    for y0 in years:
        mask = eq.index.year == y0
        if mask.any():
            tick_positions.append(int(np.argmax(mask)))
            tick_labels.append(f"’{y0 % 100:02d}")
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize=7, color=theme.MUTED)
    ax.tick_params(axis="x", which="both", length=2, pad=2, colors=theme.MUTED)
    ax.set_yticks([])
    for spine_name in ("top", "left", "right"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_color(theme.HAIR)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.set_xlim(0, len(eq) - 1)
    ax.set_ylim(min(0.92, float(y_arr.min()) * 0.98), float(y_arr.max()) * 1.10)


# ---------- disclaimer + about + footer ---------------------------------------


def _draw_disclaimer_and_footer(fig: plt.Figure, factor: Factor) -> None:
    # --- About Unravel — a visible, labelled block (not fine print) ---
    _hline(fig, 0.092, lw=0.6)
    fig.text(
        MARGIN_X,
        0.082,
        "ABOUT UNRAVEL",
        fontsize=7.5,
        color=theme.INK,
        weight="semibold",
        va="top",
    )
    about = (
        "Unravel publishes a catalog of cross-sectional, market-neutral "
        "crypto factors — each with point-in-time historical data and live "
        "signals. Explore the full catalog, methodology and API at "
        "unravel.finance."
    )
    fig.text(
        MARGIN_X + 0.155,
        0.082,
        _wrap(about, width=118),
        fontsize=8,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.45,
    )

    # --- Legal fine print ---
    note = (
        "Note — Performance is for an illustrative single-factor portfolio "
        f"(positions sized proportionally to the factor signal across the "
        f"Top {factor.default_universe} universe, rebalanced daily); "
        "demonstrative only, not a tradable product. Past performance is "
        "not indicative of future results."
    )
    fig.text(
        MARGIN_X,
        0.042,
        _wrap(note, width=185),
        fontsize=6.3,
        style="italic",
        color=theme.MUTED,
        va="top",
        linespacing=1.35,
    )
    _hline(fig, 0.024, lw=0.5)
    fig.text(
        MARGIN_X,
        0.012,
        factor.detail_url,
        fontsize=7.5,
        color=theme.SUB_INK,
        weight="medium",
        va="center",
    )
    fig.text(
        RIGHT_X,
        0.012,
        f"Page 1 of 2    ·    {_date.today():%b %Y}",
        fontsize=7.5,
        color=theme.MUTED,
        ha="right",
        va="center",
    )


# ---------- entry point -------------------------------------------------------


def render_page_one(
    factor: Factor,
    returns: pd.Series,
    stats: metrics.Stats,
    clean: pd.DataFrame | None = None,
) -> plt.Figure:
    """Render page 1.

    `clean` is the AlphaLens-cleaned (factor, forward returns) frame used by
    the top-right quantile-alpha bar chart. When None (e.g. during synthetic
    smoke tests) the bars are skipped gracefully and the rest of the page
    still renders.
    """
    fig = theme.new_page()
    _draw_header(fig, factor)
    _draw_hero(fig, factor, clean)
    _draw_pull_quote(fig, factor)

    overview_top = 0.712 if factor.effect else 0.790
    _draw_overview(fig, factor, y_top=overview_top)

    _draw_section_eyebrow(
        fig,
        y=0.495,
        label=f"Example Top {factor.default_universe} cross-sectional portfolio",
        right_label=(
            f"Inception {stats.start:%b %Y}    ·    "
            f"Updated {stats.end:%b %Y}"
        ),
        sub_label=(
            "Long and short the full Top "
            f"{factor.default_universe} universe, with position sizes "
            "scaled by the factor's cross-sectional strength. "
            "Rebalanced daily."
        ),
    )

    # Monthly returns heatmap
    fig.text(
        MARGIN_X,
        0.450,
        "MONTHLY RETURNS",
        fontsize=7,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )
    render_monthly_heatmap(
        fig,
        returns,
        rect=(MARGIN_X, 0.300, COL_WIDTH, 0.140),
        title="",
    )

    # Risk & return KPI strip
    fig.text(
        MARGIN_X,
        0.282,
        "RISK & RETURN",
        fontsize=7,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )
    _draw_kpi_strip(fig, stats, y=0.205)

    # Cumulative return — full width below the KPI strip
    fig.text(
        MARGIN_X,
        0.187,
        "CUMULATIVE RETURN",
        fontsize=7,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )
    _draw_cumulative_chart(
        fig, returns, rect=(MARGIN_X, 0.115, COL_WIDTH, 0.062)
    )

    _draw_disclaimer_and_footer(fig, factor)
    return fig
