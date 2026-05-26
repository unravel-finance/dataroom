"""Page 2 (portfolio variant) — portfolio performance & composition view.

The single-factor page-2 (scripts/factsheet/page_two.py) is an AlphaLens
factor-analysis grid; multi-factor portfolios have no single raw factor
to inspect, so we substitute portfolio-level diagnostics here:

    drawdown                — full-width
    monthly returns heatmap — full-width
    rolling Sharpe (90D)    ·  rolling gross exposure  — side-by-side

The header, ABOUT and NOTICE blocks are deliberately styled to match
scripts/factsheet/page_two.py so the two variants feel like one document.
"""

from __future__ import annotations

import textwrap
from datetime import date as _date

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.gridspec import GridSpec
from matplotlib.transforms import Bbox

from scripts.factsheet import metrics, theme
from scripts.factsheet.branding import draw_brand
from scripts.factsheet.buttons import BTN_H, draw_link_button
from scripts.factsheet.justify import _render_justified_block
from scripts.portfolios_catalog import Portfolio

MARGIN_X = 0.07
RIGHT_X = 1.0 - MARGIN_X
COL_WIDTH = RIGHT_X - MARGIN_X

# Rolling window for the Sharpe panel — 90 calendar days reads as
# "quarterly Sharpe" while still being short enough to react to regime
# shifts.
ROLLING_WINDOW = 90

# Reused from page_two — kept verbatim so the two variants of page 2
# remain visually identical at the foot. Importing would create a
# circular-style coupling (page_two also depends on factor-specific
# rendering), so duplicating the strings is the lesser evil.
_NOTICE = (
    "Unless indicated otherwise, this document and all information contained "
    "within — including, without limitation, all methods, processes, "
    "concepts, text, data, graphs and charts (together, the “Content”) — is "
    "the property of Unravel Finance and its affiliates (“Unravel”) or its "
    "licensors. Unravel does not provide investment advice and nothing in "
    "the Content shall be construed as such. In particular, the inclusion, "
    "weighting or exclusion of an asset or exchange does not in any way "
    "suggest or reflect an opinion of Unravel. Financial instruments based "
    "on Unravel factors or indices are in no way sponsored, endorsed, sold "
    "or promoted by Unravel. The Content is provided solely for "
    "informational purposes based upon information generally available to "
    "the public and from sources believed to be reliable. No Content may be "
    "modified, reproduced, reverse engineered, or distributed in any form or "
    "by any means without the prior written consent of Unravel. THE CONTENT "
    "IS PROVIDED ON AN “AS IS” BASIS AND UNRAVEL DISCLAIMS ANY AND ALL "
    "EXPRESS OR IMPLIED WARRANTIES, INCLUDING BUT NOT LIMITED TO ANY "
    "WARRANTIES OF FITNESS FOR A PARTICULAR PURPOSE OR USE, FREEDOM FROM "
    "BUGS, OR SOFTWARE ERRORS OR DEFECTS. In no event shall Unravel be "
    "liable for any direct, indirect, incidental, compensatory, punitive, "
    "special or consequential damages, costs, expenses, legal fees or "
    "losses (including, without limitation, lost income or lost profits and "
    "opportunity costs) in connection with any use of the Content even if "
    "advised of the possibility of such damages. Performance shown is "
    "derived from a model multi-factor portfolio and may include "
    "hypothetical, back-tested results that reflect application of a "
    "methodology with the benefit of hindsight; actual results may differ "
    "materially. Past performance is not an indication or guarantee of "
    "future results."
)

_ABOUT = (
    "Unravel publishes a catalog of cross-sectional, market-neutral crypto "
    "factors — each with point-in-time history and live signals — designed "
    "to be combined into multi-factor portfolios that diversify away "
    "single-factor risk. Full catalog, methodology and API at "
    "unravel.finance; see the materials below."
)

_ABOUT_WRAP = 150


def _set_year_ticks(ax: plt.Axes) -> None:
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def _strip_top_right(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(theme.HAIR)
    ax.spines["bottom"].set_color(theme.HAIR)


def _draw_header(fig: plt.Figure, portfolio: Portfolio, page: int) -> None:
    draw_brand(fig, MARGIN_X)
    fig.text(
        RIGHT_X,
        0.960,
        f"{_date.today():%b %Y}    ·    {page} / 2",
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

    title = fig.text(
        MARGIN_X,
        0.920,
        "Portfolio Analysis",
        fontsize=22,
        fontweight="bold",
        color=theme.INK,
        va="top",
        family=theme.display_font(),
    )
    # Centre a secondary "Download Returns (CSV)" CTA on the title row —
    # mirrors the page_two CTA placement.
    renderer = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()
    tbox = title.get_window_extent(renderer)
    (_, ty0) = inv.transform((tbox.x0, tbox.y0))
    (_, ty1) = inv.transform((tbox.x0, tbox.y1))
    title_mid = (ty0 + ty1) / 2.0
    csv_btn_w = 0.21
    csv_btn_h = 0.022
    draw_link_button(
        fig,
        RIGHT_X - csv_btn_w,
        title_mid - csv_btn_h / 2.0,
        csv_btn_w,
        "Download Returns (CSV)",
        portfolio.returns_csv_url,
        primary=False,
        height=csv_btn_h,
        fontsize=7.5,
    )

    n_components = len(portfolio.components or ())
    components_text = (
        ", ".join(portfolio.components)
        if n_components <= 4
        else f"{n_components} orthogonal Unravel factors"
    )
    body = (
        "Portfolio-level diagnostics for the live multi-factor strategy: "
        "the cumulative compounding profile shown on page 1 broken into "
        "its drawdown trajectory, calendar-month returns, rolling "
        f"risk-adjusted return and rolling gross exposure. Constituents: "
        f"{components_text}."
    )
    _render_justified_block(
        fig,
        x_frac=MARGIN_X,
        y_top=0.880,
        column_width_frac=COL_WIDTH,
        text=body,
        fontsize=9.5,
        color=theme.SUB_INK,
        linespacing=1.5,
        wrap_chars=116,
    )


def _section_rule(fig: plt.Figure, y_top: float, label: str) -> None:
    fig.text(
        MARGIN_X,
        y_top,
        label,
        fontsize=8,
        color=theme.INK,
        weight="semibold",
        va="top",
    )
    fig.add_artist(
        plt.Line2D(
            [MARGIN_X, RIGHT_X],
            [y_top - 0.012, y_top - 0.012],
            color=theme.HAIR,
            linewidth=0.6,
        )
    )


def _draw_about_and_notice(fig: plt.Figure, portfolio: Portfolio) -> None:
    """ABOUT UNRAVEL section + NOTICE & DISCLAIMER — same layout & strings
    as scripts/factsheet/page_two._draw_about_and_notice, but with the
    notebook button pointed at the generic multi-factor construction
    notebook (portfolios have no per-factor AlphaLens notebook)."""
    n_lines = textwrap.fill(_NOTICE, width=164).count("\n") + 1
    notice_line_h = (5.8 * 1.42 / 72.0) / theme.PAGE_H_IN
    notice_body_top = 0.038 + n_lines * notice_line_h
    notice_head_y = notice_body_top + 0.018

    _render_justified_block(
        fig,
        x_frac=MARGIN_X,
        y_top=notice_body_top,
        column_width_frac=COL_WIDTH,
        text=_NOTICE,
        fontsize=5.8,
        color=theme.MUTED,
        linespacing=1.42,
        wrap_chars=164,
    )

    btn_gap = 0.02
    btn_w = (COL_WIDTH - btn_gap) / 2

    about_line_h = (7.5 * 1.45 / 72.0) / theme.PAGE_H_IN
    n_about = textwrap.fill(_ABOUT, width=_ABOUT_WRAP).count("\n") + 1

    contact_text = (
        "Have further questions? Book a call with our team "
        "— unravel.finance/booking"
    )
    contact_line_h = (7.5 * 1.4 / 72.0) / theme.PAGE_H_IN
    contact_top = notice_head_y + 0.014 + contact_line_h
    buttons_y = contact_top + 0.010
    about_body_top = buttons_y + BTN_H + 0.012 + n_about * about_line_h
    about_head_y = about_body_top + 0.022

    _section_rule(fig, about_head_y, "ABOUT UNRAVEL")
    fig.text(
        MARGIN_X,
        about_body_top,
        textwrap.fill(_ABOUT, width=_ABOUT_WRAP),
        fontsize=7.5,
        color=theme.SUB_INK,
        va="top",
        linespacing=1.45,
    )

    draw_link_button(
        fig,
        MARGIN_X,
        buttons_y,
        btn_w,
        "View this portfolio on unravel.finance",
        portfolio.detail_url,
        primary=True,
    )
    draw_link_button(
        fig,
        MARGIN_X + btn_w + btn_gap,
        buttons_y,
        btn_w,
        "Replication notebook — multi-factor construction",
        portfolio.notebook_url,
        primary=False,
    )
    from scripts.factors_catalog import BOOKING_URL  # local import — avoids cycle
    contact = fig.text(
        MARGIN_X,
        contact_top,
        contact_text,
        fontsize=7.5,
        color=theme.ACCENT,
        weight="semibold",
        va="top",
    )
    contact.set_url(BOOKING_URL)


# ---------- charts ----------------------------------------------------------


def _plot_drawdown(ax: plt.Axes, returns: pd.Series) -> None:
    dd = metrics.drawdown(returns).dropna()
    if dd.empty:
        ax.axis("off")
        return
    dd_pct = dd * 100.0
    ax.fill_between(
        dd_pct.index,
        dd_pct.values,
        0,
        color=theme.NEG_TINT,
        edgecolor="none",
        zorder=1,
    )
    ax.plot(
        dd_pct.index,
        dd_pct.values,
        color=theme.NEG,
        linewidth=1.0,
        zorder=2,
    )
    ax.axhline(0.0, color=theme.HAIR, linewidth=0.6)
    ax.set_ylabel("Drawdown")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _p: f"{v:.0f}%"))
    ax.set_title("Drawdown", loc="left", color=theme.INK)
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    _strip_top_right(ax)
    _set_year_ticks(ax)
    # Pad the floor so the trough doesn't touch the axis.
    floor = float(dd_pct.min())
    pad = abs(floor) * 0.08 or 1.0
    ax.set_ylim(floor - pad, 1.0)
    ax.margins(x=0)


# Diverging red→white→accent ramp keyed to ±max(|monthly return|), so the
# heatmap reads at a glance: red = drawdown month, accent = strong month.
_HEATMAP_CMAP = LinearSegmentedColormap.from_list(
    "unravel_heatmap",
    [theme.NEG, "#FFFFFF", theme.ACCENT],
    N=256,
)


def _plot_monthly_heatmap(ax: plt.Axes, returns: pd.Series) -> None:
    monthly = metrics.monthly_returns(returns).dropna()
    if monthly.empty:
        ax.axis("off")
        return
    df = pd.DataFrame(
        {
            "year": monthly.index.year,
            "month": monthly.index.month,
            "value": monthly.values,
        }
    )
    pivot = df.pivot(index="year", columns="month", values="value")
    pivot = pivot.reindex(columns=range(1, 13))
    # Years descending — newest on top, common quant-tear-sheet convention.
    pivot = pivot.sort_index(ascending=False)

    values = pivot.to_numpy(dtype=float)
    vmax = float(np.nanmax(np.abs(values))) if values.size else 0.0
    vmax = vmax if vmax > 0 else 0.01

    # pcolormesh + edgecolors="face" keeps adjacent cells flush — imshow
    # leaves sub-pixel seams in PDF vector output that read as faint
    # gridlines across the heatmap. rasterized=True flattens the patch
    # collection so the seams can't sneak back in at print time.
    n_rows, n_cols = values.shape
    x_edges = np.arange(n_cols + 1) - 0.5
    y_edges = np.arange(n_rows + 1) - 0.5
    mesh = ax.pcolormesh(
        x_edges,
        y_edges,
        values,
        cmap=_HEATMAP_CMAP,
        vmin=-vmax,
        vmax=vmax,
        shading="flat",
        edgecolors="face",
        linewidth=0,
        rasterized=True,
    )
    ax.invert_yaxis()
    ax.set_xlim(x_edges[0], x_edges[-1])
    ax.set_ylim(y_edges[-1], y_edges[0])
    ax.set_xticks(range(12))
    ax.set_xticklabels(
        ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
         "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    )
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([str(y) for y in pivot.index])
    ax.tick_params(axis="both", which="both", length=0, labelsize=7)
    # Belt-and-suspenders: the theme's rcParams configure grid styling
    # for other panels; explicitly disable it here so nothing can render
    # over the cells.
    ax.grid(False, which="both")
    for spine in ax.spines.values():
        spine.set_visible(False)
    # Cell labels — small, only when there's a value.
    n_rows, n_cols = values.shape
    for i in range(n_rows):
        for j in range(n_cols):
            v = values[i, j]
            if np.isnan(v):
                continue
            # White text on the strongest cells, ink otherwise — chosen by
            # cell magnitude (not sign) so contrast stays readable on the
            # red and accent extremes alike.
            tcolor = "#FFFFFF" if abs(v) > 0.55 * vmax else theme.INK
            ax.text(
                j,
                i,
                metrics.fmt_signed_pct(v, digits=1),
                ha="center",
                va="center",
                fontsize=6.5,
                color=tcolor,
            )
    ax.set_title(
        "Monthly Returns  ·  calendar-month, compounded",
        loc="left",
        color=theme.INK,
    )
    # Slim colourbar to the right — anchored to the axes so it doesn't
    # collide with the panel border.
    cbar = ax.figure.colorbar(
        mesh, ax=ax, pad=0.012, fraction=0.018, aspect=22
    )
    cbar.outline.set_visible(False)
    cbar.ax.tick_params(labelsize=6, length=0, colors=theme.MUTED)
    cbar.ax.yaxis.set_major_formatter(
        mtick.FuncFormatter(lambda v, _p: f"{v * 100:+.0f}%")
    )


def _plot_rolling_sharpe(ax: plt.Axes, returns: pd.Series) -> None:
    r = returns.dropna()
    if len(r) < ROLLING_WINDOW + 1:
        ax.axis("off")
        ax.text(
            0.5, 0.5,
            f"<{ROLLING_WINDOW} days of history",
            ha="center", va="center", fontsize=8, color=theme.MUTED,
            transform=ax.transAxes,
        )
        return
    rolling_mean = r.rolling(ROLLING_WINDOW, min_periods=ROLLING_WINDOW // 2).mean()
    rolling_std = r.rolling(ROLLING_WINDOW, min_periods=ROLLING_WINDOW // 2).std()
    sharpe = (rolling_mean / rolling_std) * np.sqrt(metrics.TRADING_DAYS)
    sharpe = sharpe.dropna()

    ax.fill_between(
        sharpe.index,
        sharpe.values,
        0,
        where=sharpe.values >= 0,
        color=theme.ACCENT_TINT,
        edgecolor="none",
        zorder=1,
    )
    ax.fill_between(
        sharpe.index,
        sharpe.values,
        0,
        where=sharpe.values < 0,
        color=theme.NEG_TINT,
        edgecolor="none",
        zorder=1,
    )
    ax.plot(
        sharpe.index,
        sharpe.values,
        color=theme.ACCENT,
        linewidth=1.2,
        zorder=2,
    )
    ax.axhline(0.0, color=theme.HAIR, linewidth=0.6)
    mean_sharpe = float(sharpe.mean())
    ax.axhline(
        mean_sharpe,
        color=theme.INK,
        linewidth=0.9,
        linestyle=(0, (3, 2)),
        zorder=3,
        label=f"Mean  {metrics.fmt_ratio(mean_sharpe, 2)}",
    )
    ax.set_title(
        f"Rolling Sharpe  ·  {ROLLING_WINDOW}-day, annualised",
        loc="left",
        color=theme.INK,
    )
    ax.set_ylabel("Sharpe")
    ax.legend(loc="upper right", fontsize=7)
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    _strip_top_right(ax)
    _set_year_ticks(ax)
    ax.margins(x=0)


def _plot_rolling_exposure(ax: plt.Axes, weights: pd.DataFrame | None) -> None:
    """Rolling gross exposure (sum of |w|) — for adaptive portfolios this
    reveals when the risk overlay has dialled exposure down; for non-adaptive
    portfolios it sits flat near 1.0 (or 2.0 for fully-invested long-short).

    Skips gracefully when weights weren't fetched (degraded mode)."""
    if weights is None or weights.empty:
        ax.axis("off")
        ax.text(
            0.5, 0.5,
            "Weights unavailable",
            ha="center", va="center", fontsize=8, color=theme.MUTED,
            transform=ax.transAxes,
        )
        return
    gross = weights.abs().sum(axis=1)
    gross = gross.dropna()
    if gross.empty:
        ax.axis("off")
        return
    gross_pct = gross * 100.0
    ax.fill_between(
        gross_pct.index,
        gross_pct.values,
        0,
        color=theme.ACCENT_TINT,
        edgecolor="none",
        zorder=1,
    )
    ax.plot(
        gross_pct.index,
        gross_pct.values,
        color=theme.ACCENT,
        linewidth=1.0,
        zorder=2,
    )
    ax.axhline(0.0, color=theme.HAIR, linewidth=0.6)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _p: f"{v:.0f}%"))
    ax.set_title(
        "Rolling Gross Exposure  ·  Σ|w|",
        loc="left",
        color=theme.INK,
    )
    ax.set_ylabel("Gross")
    ax.set_ylim(0, max(float(gross_pct.max()) * 1.08, 50.0))
    ax.grid(axis="y", linewidth=0.4, alpha=0.6)
    _strip_top_right(ax)
    _set_year_ticks(ax)
    ax.margins(x=0)


# ---------- entry point ------------------------------------------------------


def render_page_two(
    portfolio: Portfolio,
    returns: pd.Series,
    weights: pd.DataFrame | None,
) -> plt.Figure:
    fig = theme.new_page()
    _draw_header(fig, portfolio, 2)

    # Three rows: drawdown, monthly heatmap (taller — denser content),
    # bottom split into rolling Sharpe + rolling gross exposure.
    gs = GridSpec(
        nrows=3,
        ncols=2,
        figure=fig,
        left=MARGIN_X,
        right=RIGHT_X,
        top=0.803,
        bottom=0.345,
        hspace=0.65,
        wspace=0.22,
        height_ratios=[0.95, 1.55, 0.85],
    )

    ax_dd = fig.add_subplot(gs[0, :])
    try:
        _plot_drawdown(ax_dd, returns)
    except Exception as exc:  # noqa: BLE001
        ax_dd.axis("off")
        ax_dd.text(
            0.5, 0.5, f"Drawdown unavailable: {exc}",
            ha="center", va="center", fontsize=8, color=theme.MUTED,
        )

    ax_mh = fig.add_subplot(gs[1, :])
    try:
        _plot_monthly_heatmap(ax_mh, returns)
    except Exception as exc:  # noqa: BLE001
        ax_mh.axis("off")
        ax_mh.text(
            0.5, 0.5, f"Monthly returns unavailable: {exc}",
            ha="center", va="center", fontsize=8, color=theme.MUTED,
        )

    ax_rs = fig.add_subplot(gs[2, 0])
    try:
        _plot_rolling_sharpe(ax_rs, returns)
    except Exception as exc:  # noqa: BLE001
        ax_rs.axis("off")
        ax_rs.text(
            0.5, 0.5, f"Rolling Sharpe unavailable: {exc}",
            ha="center", va="center", fontsize=8, color=theme.MUTED,
        )

    ax_re = fig.add_subplot(gs[2, 1])
    try:
        _plot_rolling_exposure(ax_re, weights)
    except Exception as exc:  # noqa: BLE001
        ax_re.axis("off")
        ax_re.text(
            0.5, 0.5, f"Exposure unavailable: {exc}",
            ha="center", va="center", fontsize=8, color=theme.MUTED,
        )

    _draw_about_and_notice(fig, portfolio)
    return fig


def charts_bbox(fig: plt.Figure) -> Bbox | None:
    """Tight bounding box around just the analysis charts — used to render
    the page-2 preview thumbnail. Mirrors page_two.charts_bbox."""
    chart_axes = [
        ax for ax in fig.get_axes() if ax.get_subplotspec() is not None
    ]
    if not chart_axes:
        return None
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    boxes = [
        bb
        for ax in chart_axes
        if (bb := ax.get_tightbbox(renderer)) is not None
    ]
    if not boxes:
        return None
    bb_in = Bbox.union(boxes).transformed(fig.dpi_scale_trans.inverted())
    pad = 0.12
    return Bbox.from_extents(
        bb_in.x0 - pad,
        bb_in.y0 - pad,
        bb_in.x1 + pad,
        bb_in.y1 + pad,
    )
