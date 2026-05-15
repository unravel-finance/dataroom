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
    """Diverging palette: lowest quantile = brand red, top = brand teal."""
    palette = sns.color_palette("RdYlGn", n).as_hex()
    palette[-1] = theme.ACCENT
    palette[0] = theme.NEG
    return palette
