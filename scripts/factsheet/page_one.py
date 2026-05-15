"""Page 1 of the factsheet — narrative + monthly-returns performance grid.

Layout (top-down):
    1. Header band: logo on the left, "Factor Factsheet" eyebrow on the right.
    2. Title block: factor name, single-line tagline, illustrative-portfolio
       disclaimer.
    3. The Edge: a pull-quote describing what the factor captures.
    4. Overview: the long-form description.
    5. Monthly Returns heatmap.
    6. KPI strip (CAGR / Vol / Sharpe / Max DD / Sortino / Calmar).
    7. Footer with site URL.
"""

from __future__ import annotations

import textwrap
from datetime import date as _date
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Rectangle

from scripts.factors_catalog import Factor
from scripts.factsheet import metrics, theme
from scripts.factsheet.heatmap import render_monthly_heatmap

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGO_PNG = REPO_ROOT / "branding" / "unravel-logo.png"

# ---- Layout grid (figure-fraction coordinates) ----
MARGIN_X = 0.07
RIGHT_X = 1.0 - MARGIN_X


def _draw_logo(fig: plt.Figure) -> None:
    """Place the Unravel brand mark + wordmark in the top-left of the page."""
    wordmark_x = MARGIN_X

    if LOGO_PNG.exists():
        img = mpimg.imread(LOGO_PNG)
        # Square mark — width/height in figure fraction calibrated so the
        # rendered logo is ~0.55in (visible without dominating the page).
        mark_h = 0.046
        mark_w = mark_h * (theme.PAGE_H_IN / theme.PAGE_W_IN)
        # Vertically centred on y=0.962 (the wordmark baseline-centre).
        ax_logo = fig.add_axes(
            (MARGIN_X, 0.962 - mark_h / 2, mark_w, mark_h)
        )
        ax_logo.imshow(img, interpolation="bilinear")
        ax_logo.axis("off")
        wordmark_x = MARGIN_X + mark_w + 0.012

    fig.text(
        wordmark_x,
        0.962,
        "Unravel",
        fontsize=15,
        fontweight="bold",
        color=theme.INK,
        va="center",
        ha="left",
    )


def _draw_header(fig: plt.Figure) -> None:
    _draw_logo(fig)
    fig.text(
        RIGHT_X,
        0.963,
        "Factor Factsheet",
        fontsize=8.5,
        color=theme.MUTED,
        ha="right",
        va="center",
        weight="medium",
    )
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [0.935, 0.935], color=theme.HAIR, linewidth=0.6
        )
    )


def _wrap(text: str, width: int) -> str:
    return textwrap.fill(text, width=width)


def _wrap_paragraphs(text: str, width: int) -> str:
    return "\n\n".join(_wrap(p.strip().replace("\n", " "), width) for p in text.split("\n\n") if p.strip())


def _draw_title_block(fig: plt.Figure, factor: Factor) -> None:
    fig.text(
        MARGIN_X,
        0.895,
        factor.name,
        fontsize=28,
        fontweight="bold",
        color=theme.INK,
        va="top",
    )
    fig.text(
        MARGIN_X,
        0.853,
        _wrap(factor.tagline, width=85),
        fontsize=11,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.4,
    )


def _draw_disclaimer(fig: plt.Figure, y: float) -> None:
    """Make explicit that the displayed portfolio is illustrative."""
    text = (
        "All performance figures below are for an illustrative single-factor "
        "portfolio constructed from this factor over the Top 40 universe — "
        "long the highest-ranked assets, short the lowest, rebalanced daily. "
        "It is not a tradable product; we publish it to demonstrate the edge "
        "the underlying factor captures in isolation."
    )
    fig.text(
        MARGIN_X,
        y,
        _wrap(text, width=110),
        fontsize=8.5,
        style="italic",
        color=theme.MUTED,
        va="top",
        linespacing=1.45,
    )


def _draw_section_label(fig: plt.Figure, x: float, y: float, label: str) -> None:
    fig.text(
        x,
        y,
        label,
        fontsize=8,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )


def _draw_effect(fig: plt.Figure, factor: Factor, y_label: float, y_body: float) -> None:
    _draw_section_label(fig, MARGIN_X, y_label, "THE EDGE")
    fig.text(
        MARGIN_X,
        y_body,
        _wrap(factor.effect, width=98),
        fontsize=10.5,
        color=theme.INK,
        weight="medium",
        va="top",
        linespacing=1.45,
    )


def _draw_overview(fig: plt.Figure, factor: Factor, y_label: float, y_body: float) -> None:
    _draw_section_label(fig, MARGIN_X, y_label, "OVERVIEW")
    fig.text(
        MARGIN_X,
        y_body,
        _wrap_paragraphs(factor.long_description, width=108),
        fontsize=9,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.5,
    )


def _draw_kpi_strip(fig: plt.Figure, stats: metrics.Stats, y: float) -> None:
    cards = [
        ("CAGR", metrics.fmt_pct(stats.cagr)),
        ("Volatility", metrics.fmt_pct(stats.annual_vol)),
        ("Sharpe", metrics.fmt_ratio(stats.sharpe)),
        ("Sortino", metrics.fmt_ratio(stats.sortino)),
        ("Max Drawdown", metrics.fmt_pct(stats.max_drawdown)),
        ("Calmar", metrics.fmt_ratio(stats.calmar)),
    ]
    n = len(cards)
    width = RIGHT_X - MARGIN_X
    card_w = width / n
    card_h = 0.052
    for i, (label, value) in enumerate(cards):
        x = MARGIN_X + i * card_w
        # Subtle column separators rather than card chrome — feels more designed.
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
            x + card_w / 2,
            y + card_h * 0.72,
            label,
            fontsize=7.5,
            color=theme.MUTED,
            ha="center",
            va="center",
            weight="medium",
        )
        fig.text(
            x + card_w / 2,
            y + card_h * 0.32,
            value,
            fontsize=16,
            color=theme.INK,
            ha="center",
            va="center",
            weight="bold",
        )
    # Top + bottom rules to anchor the strip
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [y + card_h, y + card_h], color=theme.HAIR, linewidth=0.5
        )
    )
    fig.add_artist(
        plt.Line2D([MARGIN_X, RIGHT_X], [y, y], color=theme.HAIR, linewidth=0.5)
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
        f"Page 1 of 2  ·  Generated {_date.today():%b %Y}",
        fontsize=7,
        color=theme.MUTED,
        ha="right",
        va="center",
    )


def render_page_one(
    factor: Factor, returns: pd.Series, stats: metrics.Stats
) -> plt.Figure:
    fig = theme.new_page()
    _draw_header(fig)
    _draw_title_block(fig, factor)
    _draw_disclaimer(fig, y=0.798)

    # Narrative columns
    _draw_effect(fig, factor, y_label=0.735, y_body=0.715)
    _draw_overview(fig, factor, y_label=0.605, y_body=0.585)

    # Heatmap (centerpiece)
    fig.text(
        MARGIN_X,
        0.345,
        "MONTHLY RETURNS (%)",
        fontsize=8,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )
    fig.text(
        RIGHT_X,
        0.345,
        f"{stats.start:%b %Y} – {stats.end:%b %Y}",
        fontsize=7.5,
        color=theme.MUTED,
        ha="right",
        va="top",
    )
    render_monthly_heatmap(
        fig,
        returns,
        rect=(MARGIN_X, 0.155, RIGHT_X - MARGIN_X, 0.17),
        title="",
    )

    # KPI strip below the heatmap
    _draw_kpi_strip(fig, stats, y=0.085)
    _draw_footer(fig, factor)
    return fig
