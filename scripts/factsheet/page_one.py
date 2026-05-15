"""Page 1 of the factsheet: header, narrative, key stats and equity curve."""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

from scripts.factors_catalog import Factor
from scripts.factsheet import metrics, theme

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOGO_SVG = REPO_ROOT / "branding" / "unravel-logo.svg"


def _draw_logo(fig: plt.Figure, x: float, y: float, height: float) -> None:
    """Draw the Unravel wordmark + ticker bars using vector primitives.

    The brand mark is the row of vertical bars (see logo-svg.tsx in
    apps/alpha) — we re-render it geometrically here so the PDF stays self-
    contained without an SVG dependency at runtime.
    """
    ax = fig.add_axes((x, y, height * 6.5, height), zorder=10)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 12)
    ax.axis("off")

    bars = [
        # (x_center, top_height) — eyeballed from logo-svg.tsx
        (0.5, 10.0),
        (3.0, 10.0),
        (5.5, 10.0),
        (8.0, 10.0),
        (10.5, 10.0),
        (13.0, 10.0),
        (15.5, 10.0),
        (18.0, 10.0),
        (20.5, 10.0),
        (23.0, 10.0),
        (25.5, 10.0),
        (28.0, 10.0),
        (30.5, 10.0),
    ]
    for cx, h in bars:
        ax.add_patch(
            Rectangle(
                (cx - 0.45, (12 - h) / 2),
                0.9,
                h,
                facecolor=theme.INK,
                edgecolor="none",
            )
        )
    ax.text(
        35,
        6,
        "Unravel",
        fontsize=18,
        fontweight="bold",
        color=theme.INK,
        va="center",
        ha="left",
    )


def _draw_header(fig: plt.Figure, factor: Factor) -> None:
    _draw_logo(fig, x=0.06, y=0.945, height=0.018)

    fig.text(
        0.94,
        0.965,
        "FACTOR FACTSHEET",
        fontsize=8,
        color=theme.MUTED,
        ha="right",
        va="center",
        weight="semibold",
    )
    fig.text(
        0.94,
        0.945,
        factor.category.upper(),
        fontsize=7.5,
        color=theme.MUTED,
        ha="right",
        va="center",
    )

    # Horizontal rule
    fig.add_artist(
        plt.Line2D(
            [0.06, 0.94], [0.93, 0.93], color=theme.HAIR, linewidth=0.6
        )
    )

    # Title block
    fig.text(
        0.06,
        0.895,
        factor.name,
        fontsize=26,
        fontweight="bold",
        color=theme.INK,
        va="top",
        ha="left",
    )
    fig.text(
        0.06,
        0.855,
        factor.short_description,
        fontsize=11,
        color=theme.SUB_INK,
        va="top",
        ha="left",
        wrap=True,
    )

    # Badges row
    badge_y = 0.825
    badge_x = 0.06
    for badge in factor.badges:
        text = fig.text(
            badge_x + 0.015,
            badge_y,
            badge,
            fontsize=7.5,
            color=theme.SUB_INK,
            va="center",
            ha="left",
            weight="medium",
            bbox=dict(
                boxstyle="round,pad=0.35",
                facecolor=theme.PANEL,
                edgecolor=theme.HAIR,
                linewidth=0.6,
            ),
        )
        # rough advance based on character count
        badge_x += 0.025 + 0.0065 * len(badge)


def _wrap_paragraph(text: str, width: int = 95) -> str:
    paragraphs = [p.strip() for p in text.split("\n\n")]
    wrapped = []
    for para in paragraphs:
        if para.startswith("- ") or para.startswith("  - "):
            # Preserve bullet structure
            wrapped.append(para)
        else:
            wrapped.append(textwrap.fill(para.replace("\n", " "), width=width))
    return "\n\n".join(wrapped)


def _draw_narrative(fig: plt.Figure, factor: Factor) -> None:
    # Section label
    fig.text(
        0.06,
        0.785,
        "WHAT THIS FACTOR CAPTURES",
        fontsize=8,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )

    # Effect — pull-quote
    fig.text(
        0.06,
        0.762,
        textwrap.fill(factor.effect, width=98),
        fontsize=11.5,
        color=theme.INK,
        weight="medium",
        va="top",
        linespacing=1.35,
    )

    # Long description
    fig.text(
        0.06,
        0.665,
        "OVERVIEW",
        fontsize=8,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )
    fig.text(
        0.06,
        0.645,
        _wrap_paragraph(factor.long_description, width=105),
        fontsize=9,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.45,
    )


def _draw_stat_card(
    fig: plt.Figure, x: float, y: float, w: float, h: float, label: str, value: str
) -> None:
    fig.patches.append(
        Rectangle(
            (x, y),
            w,
            h,
            transform=fig.transFigure,
            facecolor=theme.PANEL,
            edgecolor=theme.HAIR,
            linewidth=0.6,
        )
    )
    fig.text(
        x + w / 2,
        y + h * 0.74,
        label,
        fontsize=7,
        color=theme.MUTED,
        ha="center",
        va="center",
        weight="semibold",
    )
    fig.text(
        x + w / 2,
        y + h * 0.38,
        value,
        fontsize=15,
        color=theme.INK,
        ha="center",
        va="center",
        weight="bold",
    )


def _draw_stat_strip(fig: plt.Figure, stats: metrics.Stats, y: float) -> None:
    fig.text(
        0.06,
        y + 0.075,
        "KEY METRICS",
        fontsize=8,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )

    cards = [
        ("CAGR", metrics.fmt_pct(stats.cagr)),
        ("VOL (ANN.)", metrics.fmt_pct(stats.annual_vol)),
        ("SHARPE", metrics.fmt_ratio(stats.sharpe)),
        ("SORTINO", metrics.fmt_ratio(stats.sortino)),
        ("MAX DD", metrics.fmt_pct(stats.max_drawdown)),
        ("CALMAR", metrics.fmt_ratio(stats.calmar)),
    ]
    n = len(cards)
    left = 0.06
    right = 0.94
    gap = 0.01
    card_w = (right - left - gap * (n - 1)) / n
    card_h = 0.052
    for i, (label, value) in enumerate(cards):
        _draw_stat_card(
            fig,
            x=left + i * (card_w + gap),
            y=y,
            w=card_w,
            h=card_h,
            label=label,
            value=value,
        )


def _draw_equity_chart(
    fig: plt.Figure, returns: pd.Series, stats: metrics.Stats
) -> None:
    fig.text(
        0.06,
        0.235,
        "CUMULATIVE RETURN",
        fontsize=8,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )
    fig.text(
        0.94,
        0.235,
        f"{stats.start:%b %Y} – {stats.end:%b %Y}  •  Unconstrained, Top 40 Universe",
        fontsize=7.5,
        color=theme.MUTED,
        ha="right",
        va="top",
    )

    ax_eq = fig.add_axes((0.06, 0.085, 0.88, 0.14))
    eq = metrics.equity_curve(returns)
    ax_eq.plot(eq.index, eq.values, color=theme.ACCENT, linewidth=1.6)
    ax_eq.fill_between(
        eq.index, 1.0, eq.values, where=(eq.values >= 1.0),
        color=theme.ACCENT, alpha=0.06, linewidth=0
    )
    ax_eq.axhline(1.0, color=theme.HAIR, linewidth=0.5, zorder=0)
    ax_eq.grid(axis="y", linewidth=0.4, alpha=0.7)
    ax_eq.set_ylabel("Growth of $1", fontsize=7.5, color=theme.MUTED)
    ax_eq.xaxis.set_major_locator(mdates.YearLocator())
    ax_eq.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax_eq.spines["left"].set_color(theme.HAIR)
    ax_eq.spines["bottom"].set_color(theme.HAIR)

    # Total return callout
    final = float(eq.iloc[-1])
    ax_eq.text(
        eq.index[-1],
        final,
        f"  {metrics.fmt_signed_pct(stats.total_return)} total",
        fontsize=8,
        color=theme.ACCENT,
        weight="semibold",
        va="center",
        ha="left",
    )


def _draw_footer(fig: plt.Figure, factor: Factor) -> None:
    fig.add_artist(
        plt.Line2D(
            [0.06, 0.94], [0.055, 0.055], color=theme.HAIR, linewidth=0.5
        )
    )
    fig.text(
        0.06,
        0.035,
        f"unravel.finance  •  factor: {factor.portfolio_id}",
        fontsize=7,
        color=theme.MUTED,
        va="center",
    )
    fig.text(
        0.94,
        0.035,
        "Page 1 of 2  •  Narrative & Performance",
        fontsize=7,
        color=theme.MUTED,
        ha="right",
        va="center",
    )


def render_page_one(
    factor: Factor, returns: pd.Series, stats: metrics.Stats
) -> plt.Figure:
    fig = theme.new_page()
    _draw_header(fig, factor)
    _draw_narrative(fig, factor)
    _draw_stat_strip(fig, stats, y=0.31)
    _draw_equity_chart(fig, returns, stats)
    _draw_footer(fig, factor)
    return fig
