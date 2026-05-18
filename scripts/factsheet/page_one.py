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
import matplotlib.dates as _mdates
import matplotlib.image as mpimg
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.ticker as _mtick
import pandas as pd

from scripts.factors_catalog import Factor
from scripts.factsheet import metrics, theme
from scripts.factsheet.al_utils import accent_by_magnitude
from scripts.factsheet.buttons import draw_link_button
from scripts.factsheet.justify import _render_justified_block

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

    spark_left = MARGIN_X + 0.55 * COL_WIDTH
    spark_w = COL_WIDTH - 0.55 * COL_WIDTH
    spark_bottom = 0.815
    spark_h = 0.085

    fig.text(
        spark_left,
        spark_bottom + spark_h + 0.008,
        "MEAN ALPHA BY QUANTILE  ·  1D (BPS)",
        fontsize=6.5,
        color=theme.MUTED,
        weight="semibold",
        ha="left",
        va="bottom",
    )
    ax = fig.add_axes((spark_left, spark_bottom, spark_w, spark_h))
    ax.bar(
        range(len(quantiles)),
        values,
        color=accent_by_magnitude(values),
        edgecolor="none",
        width=0.55,  # thin bars, clear gaps between buckets
    )
    ax.set_xticks(range(len(quantiles)))
    ax.set_xticklabels([str(q) for q in quantiles])
    ax.set_xlim(-0.5, len(quantiles) - 0.5)
    ax.margins(y=0.05)
    ax.axhline(0, color=theme.SUB_INK, linewidth=1.0, zorder=1)
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
    sub_label_wrap: int = 140,
) -> None:
    """Section divider. Title left + optional caption right + thin rule above.

    When ``sub_label`` is set it sits underneath the title as a muted
    line, wrapped at ``sub_label_wrap`` chars (narrow it when a right-side
    control shares the header row so the text stays clear of it)."""
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
            _wrap(sub_label, width=sub_label_wrap),
            fontsize=7.5,
            color=theme.MUTED,
            va="top",
            linespacing=1.4,
        )


# ---------- tabular performance / risk bands ---------------------------------


def _draw_table_band(
    fig: plt.Figure,
    y_top: float,
    groups: list[dict],
    *,
    gap: float = 0.020,
) -> None:
    """Draw a horizontal band of grouped mini-tables (institutional-factsheet
    style). Each group: {'title': str, 'cols': [(header, value), ...],
    'weight': float}. Layout per group: title → rule → column headers →
    values → rule."""
    total_w = RIGHT_X - MARGIN_X
    n = len(groups)
    avail = total_w - gap * (n - 1)
    sum_w = sum(g["weight"] for g in groups)

    title_y = y_top
    rule1_y = y_top - 0.014
    header_y = y_top - 0.020
    value_y = y_top - 0.038
    rule2_y = y_top - 0.050

    x = MARGIN_X
    for g in groups:
        gw = avail * g["weight"] / sum_w
        fig.text(
            x,
            title_y,
            g["title"],
            fontsize=7.5,
            color=theme.INK,
            weight="semibold",
            va="top",
        )
        fig.add_artist(
            plt.Line2D([x, x + gw], [rule1_y, rule1_y], color=theme.HAIR, linewidth=0.6)
        )
        cols = g["cols"]
        cw = gw / len(cols)
        for j, (hdr, val) in enumerate(cols):
            cx = x + j * cw + cw / 2
            fig.text(
                cx, header_y, hdr, fontsize=6.5, color=theme.MUTED,
                ha="center", va="top",
            )
            fig.text(
                cx, value_y, val, fontsize=9, color=theme.INK,
                ha="center", va="center", family=theme.display_font(),
            )
        fig.add_artist(
            plt.Line2D([x, x + gw], [rule2_y, rule2_y], color=theme.HAIR, linewidth=0.6)
        )
        x += gw + gap


def _draw_performance_band(
    fig: plt.Figure, returns: pd.Series, stats: metrics.Stats, y_top: float
) -> None:
    fig.text(
        MARGIN_X, y_top + 0.022, "PERFORMANCE",
        fontsize=7, color=theme.MUTED, weight="semibold", va="top",
    )
    fig.text(
        RIGHT_X,
        y_top + 0.022,
        (
            f"Report Period Start Date {stats.start:%b %Y}    ·    "
            f"End Date {stats.end:%b %Y}"
        ),
        fontsize=7,
        color=theme.MUTED,
        ha="right",
        va="top",
    )
    gr = metrics.gross_return_by_window(returns)
    ann = metrics.annual_returns(returns)
    ann_labels = sorted(
        ann, key=lambda k: (k == "YTD", k)
    )  # years ascending, YTD last
    _draw_table_band(
        fig,
        y_top,
        [
            {
                "title": "Gross Rate of Return",
                "weight": 5,
                "cols": [
                    (lbl, metrics.fmt_pct(gr[lbl]))
                    for lbl in ("1M", "3M", "1Y", "3Y", "5Y")
                ],
            },
            {
                "title": "Annual Performance (%)",
                "weight": max(len(ann_labels), 3),
                "cols": [
                    (lbl, metrics.fmt_pct(ann[lbl])) for lbl in ann_labels
                ],
            },
            {
                "title": "Since Inception",
                "weight": 1.5,
                "cols": [("SI", metrics.fmt_pct(gr["SI"]))],
            },
        ],
    )


def _draw_risk_band(
    fig: plt.Figure, returns: pd.Series, stats: metrics.Stats, y_top: float
) -> None:
    fig.text(
        MARGIN_X, y_top + 0.022, "RISK & RETURN PROFILE",
        fontsize=7, color=theme.MUTED, weight="semibold", va="top",
    )
    vol = metrics.realized_vol_by_window(returns)
    rtr = metrics.return_to_risk_by_window(returns)
    mdd, mdd_date = metrics.max_drawdown_with_date(returns)
    _draw_table_band(
        fig,
        y_top,
        [
            {
                "title": "Realised Volatility (annualised)",
                "weight": 4,
                "cols": [
                    (lbl, metrics.fmt_pct(vol[lbl]))
                    for lbl in ("1M", "3M", "1Y", "3Y")
                ],
            },
            {
                "title": "Return-to-Risk Ratio",
                "weight": 4,
                "cols": [
                    (lbl, metrics.fmt_ratio(rtr[lbl]))
                    for lbl in ("1M", "3M", "1Y", "3Y")
                ],
            },
            {
                "title": "Max Drawdown",
                "weight": 2.4,
                "cols": [
                    ("%", metrics.fmt_pct(mdd)),
                    ("Date", mdd_date.strftime("%Y-%m-%d") if mdd_date else "—"),
                ],
            },
        ],
    )


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
    # Clean single line, no fills — elegant, index-chart style.
    ax.plot(
        eq.index,
        eq.values,
        color=theme.ACCENT,
        linewidth=1.3,
        solid_capstyle="round",
        solid_joinstyle="round",
    )
    ax.axhline(1.0, color=theme.HAIR, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=theme.HAIR, linewidth=0.5, alpha=0.7)

    ax.yaxis.set_major_locator(_mtick.MaxNLocator(4, prune="lower"))
    ax.yaxis.set_major_formatter(
        _mtick.FuncFormatter(lambda v, _pos: f"{v:.1f}×")
    )
    ax.tick_params(
        axis="y", which="both", length=0, labelsize=6.5,
        colors=theme.MUTED, pad=2,
    )
    ax.xaxis.set_major_locator(_mdates.YearLocator())
    ax.xaxis.set_major_formatter(_mdates.DateFormatter("%Y"))
    ax.tick_params(
        axis="x", which="both", length=0, labelsize=6.5,
        colors=theme.MUTED, pad=3,
    )
    for spine_name in ("top", "left", "right"):
        ax.spines[spine_name].set_visible(False)
    ax.spines["bottom"].set_color(theme.HAIR)
    ax.spines["bottom"].set_linewidth(0.6)
    ax.set_xlim(eq.index[0], eq.index[-1])
    ax.set_ylim(bottom=min(0.9, float(eq.min()) * 0.95))
    ax.margins(x=0)


# ---------- disclaimer + about + footer ---------------------------------------


def _draw_disclaimer_and_footer(fig: plt.Figure, factor: Factor) -> None:
    # Short illustrative-portfolio note (the full Notice & Disclaimer and the
    # About Unravel block live on page 2).
    note = (
        "Note — Performance is for an illustrative single-factor portfolio "
        f"(positions sized proportionally to the factor signal across the "
        f"Top {factor.default_universe} universe, rebalanced daily); "
        "demonstrative only, not a tradable product. Past performance is "
        "not indicative of future results."
    )
    fig.text(
        MARGIN_X,
        0.052,
        _wrap(note, width=185),
        fontsize=6.3,
        style="italic",
        color=theme.MUTED,
        va="top",
        linespacing=1.35,
    )
    _hline(fig, 0.030, lw=0.5)
    fig.text(
        MARGIN_X,
        0.018,
        factor.detail_url,
        fontsize=7.5,
        color=theme.SUB_INK,
        weight="medium",
        va="center",
    )
    fig.text(
        RIGHT_X,
        0.018,
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
        y=0.520,
        label=f"Example Top {factor.default_universe} cross-sectional portfolio",
        sub_label=(
            "Long and short the dynamic, rolling Top "
            f"{factor.default_universe} universe (point-in-time), "
            "sized by the factor's cross-sectional strength. "
            "Rebalanced daily."
        ),
        # Narrow wrap so the 2-line caption stays on the left, clear of the
        # download button sharing the header row.
        sub_label_wrap=72,
    )
    # Secondary download — daily returns CSV for this illustrative portfolio.
    # Right of the section header, vertically centred on the title row.
    ret_btn_w = 0.19
    ret_btn_h = 0.018
    draw_link_button(
        fig,
        RIGHT_X - ret_btn_w,
        0.520 - 0.00475 - ret_btn_h / 2,
        ret_btn_w,
        "Download Returns (CSV)",
        factor.returns_csv_url,
        primary=False,
        height=ret_btn_h,
        fontsize=7,
    )

    # Performance + risk tabular bands (replace the heatmap & KPI strip)
    _draw_performance_band(fig, returns, stats, y_top=0.453)
    _draw_risk_band(fig, returns, stats, y_top=0.363)

    # Cumulative return — full width below the tables
    fig.text(
        MARGIN_X,
        0.295,
        "CUMULATIVE RETURN",
        fontsize=7,
        color=theme.MUTED,
        weight="semibold",
        va="top",
    )
    _draw_cumulative_chart(
        fig, returns, rect=(MARGIN_X, 0.118, COL_WIDTH, 0.167)
    )

    _draw_disclaimer_and_footer(fig, factor)
    return fig
