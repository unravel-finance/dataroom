from __future__ import annotations

import pandas as pd


def backtest_portfolio(
    weights: pd.DataFrame,
    underlying: pd.DataFrame,
    transaction_cost: float,
    lag: int,
) -> tuple[pd.Series, pd.DataFrame]:
    """
    Create a vectorized backtest from a portfolio of weights and the underlying returns.

    Parameters:
        weights: pd.DataFrame
            The weights of the portfolio.
        underlying: pd.DataFrame
            The underlying returns.
        transaction_cost: float
            The transaction cost.
        lag: int
            Additional lag to apply to the signal.
    Returns:
        PortfolioBacktestResult
    """
    assert weights.columns.equals(underlying.columns), "Columns must match"
    underlying = underlying.loc[weights.index]
    weights = weights.fillna(0).reindex(underlying.index).ffill()
    weights.columns = underlying.columns
    delta_pos = weights.diff(1).abs().fillna(0.0)
    costs = transaction_cost * delta_pos
    returns = (underlying * weights.shift(1 + lag)) - costs
    portfolio_returns = returns.sum(axis="columns")

    return portfolio_returns, returns


def backtest_factor(
    price_series: pd.Series, signal_series: pd.Series, transaction_cost: float = 0.0005
) -> pd.DataFrame:
    """
    Perform a vectorized backtest on price and signal series.

    Args:
        price_series (pd.Series): Price series of the asset
        signal_series (pd.Series): Signal series between -1 and 1
        transaction_cost (float): Transaction cost as a decimal (e.g., 0.001 for 0.1%)

    Returns:
        pd.DataFrame: DataFrame containing positions, returns, and cumulative returns
    """
    # Forward fill missing values
    price_series = price_series.ffill()
    signal_series = signal_series.ffill()

    # Calculate position changes (when signal changes)
    position_changes = signal_series.diff()

    # Calculate returns including transaction costs
    returns = price_series.pct_change()
    position_returns = (
        signal_series.shift(1) * returns
    )  # Shift to avoid look-ahead bias

    # Apply transaction costs only when position changes
    transaction_costs = abs(position_changes) * transaction_cost

    # Calculate net returns
    net_returns = position_returns - transaction_costs

    # Calculate cumulative returns
    cumulative_returns = (1 + net_returns).cumprod()

    # Create results DataFrame
    return pd.DataFrame(
        {
            "price": price_series,
            "signal": signal_series,
            "position": signal_series,
            "position_changes": position_changes,
            "returns": returns,
            "position_returns": position_returns,
            "transaction_costs": transaction_costs,
            "net_returns": net_returns,
            "cumulative_returns": cumulative_returns,
            "price_rebased": (price_series / price_series.iloc[0]),
        }
    )
