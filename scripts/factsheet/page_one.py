"""Page 1 — narrative + monthly returns heatmap + KPI strip.

Hierarchy:
    eyebrow → title → subtitle → overview → divider → heatmap → KPI strip → footer
"""

from __future__ import annotations

import textwrap
from datetime import date as _date
from pathlib import Path

import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import pandas as pd

from scripts.factors_catalog import Factor
from scripts.factsheet import metrics, theme
from scripts.factsheet.heatmap import render_monthly_heatmap

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGO_PNG = REPO_ROOT / "branding" / "unravel-logo.png"

MARGIN_X = 0.07
RIGHT_X = 1.0 - MARGIN_X
PROSE_COL_WIDTH_CH = 78  # ~65 cpl plus a bit of slack for hyphenation


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
        )
        return
    img = mpimg.imread(LOGO_PNG)
    logo_h = 0.022
    aspect = img.shape[1] / img.shape[0]
    logo_w = logo_h * (theme.PAGE_H_IN / theme.PAGE_W_IN) * aspect
    ax_logo = fig.add_axes((MARGIN_X, 0.960 - logo_h / 2, logo_w, logo_h))
    ax_logo.imshow(img, interpolation="bilinear")
    ax_logo.axis("off")


def _wrap(text: str, width: int) -> str:
    return textwrap.fill(text, width=width)


def _wrap_paragraphs(text: str, width: int) -> str:
    return "\n\n".join(
        _wrap(p.strip().replace("\n", " "), width)
        for p in text.split("\n\n")
        if p.strip()
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
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [0.935, 0.935], color=theme.HAIR, linewidth=0.6
        )
    )


def _draw_title_block(fig: plt.Figure, factor: Factor) -> None:
    # Eyebrow: tiny uppercase metadata above the title.
    fig.text(
        MARGIN_X,
        0.905,
        f"FACTOR FACTSHEET  ·  {factor.portfolio_id.upper()}  ·  TOP 40 UNIVERSE",
        fontsize=7.5,
        color=theme.MUTED,
        weight="semibold",
        va="bottom",
        # Approximate letter-spacing via spaces in the source string is ugly;
        # we lean on the all-caps + semi-bold + colour to make the eyebrow read
        # as metadata rather than as a sentence.
    )
    fig.text(
        MARGIN_X,
        0.895,
        factor.name,
        fontsize=42,
        fontweight="bold",
        color=theme.INK,
        va="top",
        family=theme.display_font(),
    )
    fig.text(
        MARGIN_X,
        0.823,
        _wrap(factor.short_description, width=70),
        fontsize=11.5,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.45,
    )


def _draw_overview(fig: plt.Figure, factor: Factor, y: float) -> None:
    fig.text(
        MARGIN_X,
        y,
        _wrap_paragraphs(factor.long_description, width=PROSE_COL_WIDTH_CH),
        fontsize=9,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.5,
    )


def _draw_section_eyebrow(
    fig: plt.Figure, y: float, label: str, right_label: str = ""
) -> None:
    """Small-caps section divider — title left, optional caption right, thin rule."""
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [y + 0.012, y + 0.012], color=theme.HAIR, linewidth=0.6
        )
    )
    fig.text(
        MARGIN_X,
        y,
        label,
        fontsize=8,
        color=theme.MUTED,
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


def _draw_kpi_strip(fig: plt.Figure, stats: metrics.Stats, y: float) -> None:
    """KPI strip — label/value ratio ~1:2.8 so the value scans fast."""
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
    card_h = 0.072
    for i, (label, value) in enumerate(cards):
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
            x + card_w / 2,
            y + card_h * 0.80,
            label.upper(),
            fontsize=8,
            color=theme.MUTED,
            ha="center",
            va="center",
            weight="semibold",
        )
        fig.text(
            x + card_w / 2,
            y + card_h * 0.36,
            value,
            fontsize=26,
            color=theme.INK,
            ha="center",
            va="center",
            weight="bold",
            family=theme.display_font(),
        )
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [y + card_h, y + card_h], color=theme.HAIR, linewidth=0.6
        )
    )
    fig.add_artist(
        plt.Line2D([MARGIN_X, RIGHT_X], [y, y], color=theme.HAIR, linewidth=0.6)
    )


def _draw_disclaimer_and_footer(fig: plt.Figure, factor: Factor) -> None:
    """Demoted disclaimer + footer. Disclaimer reads as a footnote, not a paragraph."""
    note = (
        "Note — Performance shown is for an illustrative single-factor portfolio "
        "(long top-ranked, short bottom-ranked across the Top 40 universe, rebalanced "
        "daily). Provided to demonstrate the underlying factor's signal; not a "
        "tradable product."
    )
    fig.text(
        MARGIN_X,
        0.057,
        _wrap(note, width=140),
        fontsize=7.5,
        style="italic",
        color=theme.MUTED,
        va="top",
        linespacing=1.45,
    )
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X], [0.029, 0.029], color=theme.HAIR, linewidth=0.5
        )
    )
    fig.text(
        MARGIN_X,
        0.016,
        factor.detail_url,
        fontsize=7.5,
        color=theme.SUB_INK,
        weight="medium",
        va="center",
    )
    fig.text(
        RIGHT_X,
        0.016,
        f"Page 1 of 2  ·  {_date.today():%b %Y}",
        fontsize=7.5,
        color=theme.MUTED,
        ha="right",
        va="center",
    )


def render_page_one(
    factor: Factor, returns: pd.Series, stats: metrics.Stats
) -> plt.Figure:
    fig = theme.new_page()
    _draw_header(fig, factor)
    _draw_title_block(fig, factor)

    # Overview body — wraps to ~78 cpl. With 9pt body and 1.5 leading this
    # fits the longest description in the catalogue inside the upper band.
    _draw_overview(fig, factor, y=0.770)

    # Performance section
    _draw_section_eyebrow(
        fig,
        y=0.395,
        label="PERFORMANCE",
        right_label=f"{stats.start:%b %Y} – {stats.end:%b %Y}",
    )
    render_monthly_heatmap(
        fig,
        returns,
        rect=(MARGIN_X, 0.205, RIGHT_X - MARGIN_X, 0.175),
        title="",
    )

    # Risk & return strip
    _draw_section_eyebrow(fig, y=0.182, label="RISK & RETURN")
    _draw_kpi_strip(fig, stats, y=0.100)

    _draw_disclaimer_and_footer(fig, factor)
    return fig
