import pandas as pd
import os
import warnings

from dotenv import load_dotenv

def rebase(prices: pd.Series) -> pd.Series:
    """Rebase a price series to 1.0"""
    return prices / prices.iloc[0]


def to_drawdown(prices: pd.Series) -> pd.Series:
    running_max = prices.cummax()
    drawdowns = (prices - running_max) / running_max
    return drawdowns



def get_env(key: str) -> str | None:
    try:
        load_dotenv()
        return os.environ.get(key)
    except:  # noqa
        warnings.warn(f"Couldn't load {key}")  # noqa
        return None

def filter_none(input_list: list) -> list:
    return [x for x in input_list if x is not None]
