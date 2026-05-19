"""Shared AlphaLens helpers used by both page 1 and page 2 of the factsheet."""

from __future__ import annotations

import warnings

import alphalens
import pandas as pd


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
