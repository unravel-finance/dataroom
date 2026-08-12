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



_MISSING_ENV_HELP = (
    "{key} is not set, so every Unravel API call below would fail with "
    "`401 Unauthorized` (PGRST116, 'The result contains 0 rows') -- the key "
    "is resolved server-side and an absent one matches no row.\n"
    "  Colab: add {key} in the Secrets (key icon) panel.\n"
    "  Local: put {key}=<your key> in a .env file in the repository root, "
    "or export it before starting Jupyter.\n"
    "Get a key by signing up at https://unravel.finance"
)


def get_env(key: str) -> str:
    """Read `key` from the environment (or a .env file), raising if unset.

    Returning None on a missing key looks harmless but isn't: `requests`
    *drops* a header whose value is None, so the call goes out with no
    X-API-KEY at all and comes back as an opaque PostgREST 401 several
    cells later. Failing here names the actual problem instead.
    """
    try:
        load_dotenv()
    except Exception:  # noqa: BLE001
        warnings.warn(f"Couldn't load a .env file while resolving {key}")  # noqa
    value = (os.environ.get(key) or "").strip()
    if not value:
        raise RuntimeError(_MISSING_ENV_HELP.format(key=key))
    return value

def filter_none(input_list: list) -> list:
    return [x for x in input_list if x is not None]
