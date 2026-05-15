"""Page 1 — narrative + monthly returns heatmap + KPI strip.

Hierarchy (top → bottom):

    header rule
    eyebrow (category)  ·  title  ·  subtitle  ·  badges     | equity sparkline
    pull quote (`effect`)
    overview (2-col)
    PERFORMANCE  ·  monthly returns heatmap
    RISK & RETURN  ·  KPI strip
    disclaimer
    URL  ·  page indicator
"""

from __future__ import annotations

import textwrap
from datetime import date as _date
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scripts.factors_catalog import Factor
from scripts.factsheet import metrics, theme
from scripts.factsheet.heatmap import render_monthly_heatmap

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGO_PNG = REPO_ROOT / "branding" / "unravel-logo.png"

MARGIN_X = 0.07
RIGHT_X = 1.0 - MARGIN_X
COL_WIDTH = RIGHT_X - MARGIN_X

# Width budget for overview text columns. At 8.5pt Mona Sans, ~72ch lets
# each line reach close to the column's right edge so the text block visually
# aligns with the equity sparkline above it.
OVERVIEW_COL_CH = 72


# ---------- low-level helpers -------------------------------------------------


def _wrap(text: str, width: int) -> str:
    return textwrap.fill(text, width=width)


def _wrap_paragraphs(text: str, width: int) -> list[str]:
    """Split on blank lines, wrap each paragraph, return one string per paragraph."""
    return [
        _wrap(p.strip().replace("\n", " "), width=width)
        for p in text.split("\n\n")
        if p.strip()
    ]


def _hline(fig: plt.Figure, y: float, *, lw: float = 0.6, color: str | None = None) -> None:
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [y, y], color=color or theme.HAIR, linewidth=lw
        )
    )


def _format_eyebrow_segments(*segments: str) -> str:
    """Join eyebrow segments with a tracked middle-dot separator.

    Retained as a helper for section-eyebrow strings (right_label etc.); the
    hero block no longer uses it directly.
    """
    return "    \u00b7    ".join(s.upper() for s in segments if s)


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
    # Wordmark next to the icon.
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


# ---------- hero block --------------------------------------------------------


# Hero occupies y in [0.815, 0.925]. Left column = title block; right column =
# equity sparkline.
HERO_LEFT_W = 0.58 * COL_WIDTH


def _draw_hero(fig: plt.Figure, factor: Factor, returns: pd.Series) -> None:
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
    # Subtitle — wrap to the left-column width so it doesn't clash with the
    # sparkline. ~52ch at 11pt fits in roughly 55% of the column width.
    fig.text(
        MARGIN_X,
        0.853,
        _wrap(factor.short_description, width=52),
        fontsize=11,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.4,
    )
    _draw_sparkline(fig, returns)


def _draw_badges(fig: plt.Figure, badges: tuple[str, ...] | list[str], y: float) -> None:
    """Unused in the current page-1 layout (kept for opt-in re-use). Renders
    each badge as a short uppercase label inside a 1pt hairline box."""
    if not badges:
        return
    # Render each badge as a short uppercase label inside a 1pt hairline box.
    # We can't easily measure text in matplotlib without a renderer round-trip,
    # so we approximate width: ~0.0050 figure-units per character at 7pt + pad.
    pad_x = 0.006
    gap = 0.006
    x = MARGIN_X
    for label in badges:
        text = label.upper()
        approx_w = 0.0048 * len(text) + 2 * pad_x
        rect = mpatches.Rectangle(
            (x, y - 0.011),
            approx_w,
            0.020,
            transform=fig.transFigure,
            facecolor=theme.BG,
            edgecolor=theme.HAIR,
            linewidth=0.6,
            zorder=1,
        )
        fig.add_artist(rect)
        fig.text(
            x + approx_w / 2,
            y - 0.001,
            text,
            fontsize=6.8,
            color=theme.SUB_INK,
            ha="center",
            va="center",
            weight="semibold",
        )
        x += approx_w + gap


def _draw_sparkline(fig: plt.Figure, returns: pd.Series) -> None:
    """Equity curve in the hero's right column.

    X-axis is calendar years; the curve is the cumulative compounded return
    of the daily series. The endpoint is annotated with total return.
    """
    r = returns.dropna()
    if r.empty:
        return
    eq = (1.0 + r).cumprod()
    spark_left = MARGIN_X + 0.66 * COL_WIDTH
    spark_w = COL_WIDTH - 0.66 * COL_WIDTH
    spark_bottom = 0.840
    spark_h = 0.052

    fig.text(
        spark_left,
        spark_bottom + spark_h + 0.012,
        "CUMULATIVE RETURN",
        fontsize=6.8,
        color=theme.MUTED,
        weight="semibold",
        ha="left",
        va="bottom",
    )
    ax = fig.add_axes((spark_left, spark_bottom, spark_w, spark_h))
    x = np.arange(len(eq))
    y_arr = eq.values
    # Reference line at 1× (no money made / lost).
    ax.axhline(1.0, color=theme.HAIR, linewidth=0.6, linestyle=(0, (1.5, 1.5)))
    ax.fill_between(x, 1.0, y_arr, where=(y_arr >= 1.0), color=theme.ACCENT, alpha=0.10, linewidth=0)
    ax.fill_between(x, 1.0, y_arr, where=(y_arr < 1.0), color=theme.NEG, alpha=0.08, linewidth=0)
    ax.plot(x, y_arr, color=theme.INK, linewidth=1.1)
    ax.scatter([x[-1]], [y_arr[-1]], s=16, color=theme.ACCENT, zorder=3, linewidth=0)

    # Year ticks along the bottom — start of each calendar year present.
    years = sorted({d.year for d in eq.index})
    tick_positions: list[int] = []
    tick_labels: list[str] = []
    for y0 in years:
        mask = eq.index.year == y0
        if mask.any():
            tick_positions.append(int(np.argmax(mask)))
            tick_labels.append(f"\u2019{y0 % 100:02d}")
    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, fontsize=6.5, color=theme.MUTED)
    ax.tick_params(axis="x", which="both", length=2, pad=2, colors=theme.MUTED)
    ax.set_yticks([])
    for spine_name in ("top", "left", "right"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_color(theme.HAIR)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.set_xlim(0, len(eq) - 1)
    ax.set_ylim(min(0.92, float(y_arr.min()) * 0.98), float(y_arr.max()) * 1.10)

    # Total-return annotation next to the endpoint.
    total_pct = (float(eq.iloc[-1]) - 1.0) * 100
    sign = "+" if total_pct >= 0 else theme.MINUS
    ax.annotate(
        f"{sign}{abs(total_pct):.0f}%",
        xy=(x[-1], float(eq.iloc[-1])),
        xytext=(-4, 8),
        textcoords="offset points",
        fontsize=9,
        color=theme.ACCENT,
        weight="bold",
        ha="right",
        va="bottom",
        family=theme.display_font(),
    )


# ---------- pull quote --------------------------------------------------------


def _draw_pull_quote(fig: plt.Figure, factor: Factor) -> None:
    if not factor.effect:
        return
    y_top = 0.788
    y_bot = 0.728
    # Rules top and bottom — same hairline weight as section dividers.
    _hline(fig, y_top, lw=0.6)
    _hline(fig, y_bot, lw=0.6)
    # Teal vertical mark on the left.
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


# ---------- overview (2 column) -----------------------------------------------


def _draw_overview(fig: plt.Figure, factor: Factor, y_top: float, y_bot: float) -> None:
    """Render the long description across two columns.

    We split paragraphs in half between the columns by visual line count so the
    columns balance roughly evenly.
    """
    paragraphs = _wrap_paragraphs(factor.long_description, width=OVERVIEW_COL_CH)
    if not paragraphs:
        return
    # Estimate line count for each paragraph and find the split index.
    line_counts = [p.count("\n") + 1 for p in paragraphs]
    total = sum(line_counts)
    running = 0
    split = len(paragraphs)
    for i, n in enumerate(line_counts):
        if running + n >= total / 2:
            split = i + 1
            break
        running += n
    left = "\n\n".join(paragraphs[:split])
    right = "\n\n".join(paragraphs[split:])

    col_gap = 0.022
    col_w = (COL_WIDTH - col_gap) / 2
    fig.text(
        MARGIN_X,
        y_top,
        left,
        fontsize=8.5,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.55,
    )
    fig.text(
        MARGIN_X + col_w + col_gap,
        y_top,
        right,
        fontsize=8.5,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.55,
    )
    _ = y_bot  # kept for future overflow handling


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
    one-liner — used to frame the heatmap with the illustrative-portfolio
    note in professional, single-sentence copy.
    """
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
        fig.text(
            MARGIN_X,
            y - 0.013,
            sub_label,
            fontsize=7.5,
            color=theme.MUTED,
            va="top",
            linespacing=1.4,
        )


# ---------- KPI strip ---------------------------------------------------------


def _draw_kpi_strip(fig: plt.Figure, stats: metrics.Stats, y: float) -> None:
    """Six-card KPI strip. Label / value ratio ~1:2.6 — value scans fast."""
    cards = [
        ("CAGR",          metrics.fmt_pct(stats.cagr),         "since inception"),
        ("Volatility",    metrics.fmt_pct(stats.annual_vol),   "annualised"),
        ("Sharpe",        metrics.fmt_ratio(stats.sharpe),     "vs. RFR = 0"),
        ("Sortino",       metrics.fmt_ratio(stats.sortino),    "downside-only"),
        ("Max Drawdown",  metrics.fmt_pct(stats.max_drawdown), "peak-to-trough"),
        ("Calmar",        metrics.fmt_ratio(stats.calmar),     "return / drawdown"),
    ]
    n = len(cards)
    card_w = COL_WIDTH / n
    card_h = 0.085
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
        # Label — top-left of the card.
        fig.text(
            x + 0.012,
            y + card_h - 0.008,
            label.upper(),
            fontsize=7.2,
            color=theme.MUTED,
            ha="left",
            va="top",
            weight="semibold",
        )
        # Value — left-aligned beneath, large.
        fig.text(
            x + 0.012,
            y + card_h * 0.45,
            value,
            fontsize=22,
            color=theme.INK,
            ha="left",
            va="center",
            weight="bold",
            family=theme.display_font(),
        )
        # Sub — caption under the value.
        fig.text(
            x + 0.012,
            y + 0.008,
            sub,
            fontsize=6.5,
            color=theme.MUTED,
            ha="left",
            va="bottom",
        )
    _hline(fig, y + card_h, lw=0.6)
    _hline(fig, y, lw=0.6)


# ---------- footer ------------------------------------------------------------


def _draw_disclaimer_and_footer(fig: plt.Figure, factor: Factor) -> None:
    note = (
        "Note — Performance shown is for an illustrative single-factor portfolio "
        "(long top-ranked, short bottom-ranked across the Top 40 universe, "
        "rebalanced daily). Provided to demonstrate the underlying factor's "
        "signal; not a tradable product."
    )
    fig.text(
        MARGIN_X,
        0.058,
        _wrap(note, width=150),
        fontsize=7,
        style="italic",
        color=theme.MUTED,
        va="top",
        linespacing=1.45,
    )
    _hline(fig, 0.030, lw=0.5)
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
        f"Page 1 of 2    \u00b7    {_date.today():%b %Y}",
        fontsize=7.5,
        color=theme.MUTED,
        ha="right",
        va="center",
    )


# ---------- entry point -------------------------------------------------------


def render_page_one(
    factor: Factor, returns: pd.Series, stats: metrics.Stats
) -> plt.Figure:
    fig = theme.new_page()
    _draw_header(fig, factor)
    _draw_hero(fig, factor, returns)
    _draw_pull_quote(fig, factor)

    # Overview starts immediately below the pull-quote slot when present,
    # otherwise right under the hero. Avoids a 1in-tall dead zone for
    # catalog entries (like retail_flow) with no `effect` populated.
    overview_top = 0.712 if factor.effect else 0.790
    _draw_overview(fig, factor, y_top=overview_top, y_bot=0.475)

    # Performance section. The sub_label is the professional context line
    # for the illustrative single-factor portfolio whose monthly returns the
    # heatmap is showing.
    _draw_section_eyebrow(
        fig,
        y=0.485,
        label="Monthly returns",
        right_label=f"{stats.start:%b %Y} \u2014 {stats.end:%b %Y}",
        sub_label=(
            "Illustrative cross-sectional portfolio \u2014 long top-ranked, "
            "short bottom-ranked across the Top "
            f"{factor.default_universe}, rebalanced daily."
        ),
    )
    render_monthly_heatmap(
        fig,
        returns,
        rect=(MARGIN_X, 0.300, COL_WIDTH, 0.155),
        title="",
    )

    # Risk & return strip. Pushed down enough that the section rule clears the
    # heatmap's x-axis tick row.
    _draw_section_eyebrow(
        fig,
        y=0.255,
        label="Risk & return",
    )
    _draw_kpi_strip(fig, stats, y=0.150)

    _draw_disclaimer_and_footer(fig, factor)
    return fig
