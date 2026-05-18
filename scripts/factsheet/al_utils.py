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
    signal = factor_data[cols].stack()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return alphalens.utils.get_clean_factor_and_forward_returns(
            signal,
            prices[cols],
            quantiles=quantiles,
            periods=(1, 5, 10),
            max_loss=0.5,
        )


def quantile_palette(n: int) -> list[str]:
    """Single-hue sequential ramp (light → brand teal) for the n quantile
    lines. One colour scheme instead of five distinct hues — quantiles stay
    distinguishable by lightness while the chart stays on-brand."""
    # Light teal-tinted grey for Q1 up to the brand teal for the top quantile.
    ramp = sns.blend_palette(["#D9D9D9", theme.ACCENT_SOFT, theme.ACCENT], n)
    return [
        "#%02x%02x%02x" % tuple(int(round(c * 255)) for c in rgb) for rgb in ramp
    ]
