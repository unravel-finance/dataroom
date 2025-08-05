import pandas as pd
    
def rebase(prices: pd.Series) -> pd.Series:
    """Rebase a price series to 1.0"""
    return prices / prices.iloc[0]


def to_drawdown(prices: pd.Series) -> pd.Series:
    """
    Calculate drawdowns from a price series.

    Args:
        prices (pd.Series): Time series of prices

    Returns:
        pd.Series: Drawdowns as percentage decline from previous peak
    """
    running_max = prices.cummax()

    drawdowns = (prices - running_max) / running_max

    return drawdowns
