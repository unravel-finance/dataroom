"""Shared AlphaLens helpers used by both page 1 and page 2 of the factsheet."""

from __future__ import annotations

import warnings

import alphalens
import pandas as pd
import seaborn as sns

from scripts.factsheet import theme


def clean_factor_data(
    factor_data: pd.DataFrame, prices: pd.DataFrame, quantiles: int = 5
) -> pd.DataFrame:
    """AlphaLens-clean (factor, forward-return) frame at periods 1, 5, 10."""
    cols = factor_data.columns.intersection(prices.columns)
    if cols.empty:
        raise ValueError("No overlapping tickers between factor data and prices")
    # Execution lag (+1): the factor on date t is only known at t's close, so
    # the earliest realistic entry is the next bar. AlphaLens already offsets
    # each forward return by its full period window, but it enters at t's own
    # price — a 1-bar look-ahead. Shifting the signal forward one day removes
    # it (factor[t] is paired with the t+1 → t+1+period return).
    signal = factor_data[cols].shift(1).stack()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return alphalens.utils.get_clean_factor_and_forward_returns(
            signal,
            prices[cols],
            quantiles=quantiles,
            periods=(1, 5, 10),
            max_loss=0.5,
        )


def _to_hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in rgb[:3])


def accent_ramp(n: int) -> list[str]:
    """`n` shades of the brand accent, darkest first. Used for grouped series
    (the 1D/5D/10D quantile bars) so they read on-brand instead of grey while
    staying distinguishable by lightness."""
    ramp = sns.light_palette(theme.ACCENT, n_colors=n + 1)[1:][::-1]
    return [_to_hex(rgb) for rgb in ramp]


def quantile_palette(n: int) -> list[str]:
    """Single-hue sequential ramp (light → brand accent) for the n quantile
    lines. One colour scheme instead of five distinct hues — quantiles stay
    distinguishable by lightness while the chart stays on-brand."""
    # Light accent-tinted grey for Q1 up to the brand accent for the top.
    ramp = sns.blend_palette(["#D9D9D9", theme.ACCENT_SOFT, theme.ACCENT], n)
    return [_to_hex(rgb) for rgb in ramp]


def accent_by_magnitude(values, *, floor: float = 0.32) -> list[str]:
    """One brand-accent shade per value, intensity scaled by |value|.

    The largest-magnitude bar gets the full accent; smaller bars fade toward
    a light tint but never below ``floor`` so they stay visible on white."""
    cmap = sns.light_palette(theme.ACCENT, as_cmap=True)
    mags = [abs(float(v)) for v in values]
    vmax = max(mags, default=0.0) or 1.0
    return [_to_hex(cmap(floor + (1.0 - floor) * (m / vmax))) for m in mags]
