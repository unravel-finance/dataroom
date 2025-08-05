from collections.abc import Generator
from datetime import datetime

import pandas as pd
import requests
from finml_utils import filter_none, pmap


def _fetch(
    symbol: str, interval: str, limit: int, startTime: datetime, endTime: datetime
):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}&startTime={int(startTime.timestamp() * 1000)}&endTime={int(endTime.timestamp() * 1000)}"
    response = requests.get(url)
    return response.json()


def _fetch_price_binance_all_historical(
    symbol: str, interval: str, limit: int, startTime: datetime, endTime: datetime
) -> Generator[pd.DataFrame, None, None]:
    for date in pd.date_range(
        pd.to_datetime(startTime), pd.to_datetime(endTime), freq=f"{limit}D"
    ):
        data = _fetch(symbol, interval, limit, date, date + pd.Timedelta(days=1000))
        yield data


def fetch_price_binance(symbol: str) -> pd.DataFrame:
    """
    Fetch price data from Binance API
    """
    interval = "1d"
    output = pd.concat(
        [
            pd.DataFrame(data)
            for data in _fetch_price_binance_all_historical(
                symbol=symbol,
                interval=interval,
                limit=1000,
                startTime=datetime(2020, 1, 1),
                endTime=datetime.today(),
            )
        ]
    )
    output.columns = [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ]
    output["timestamp"] = pd.to_datetime(output["timestamp"], unit="ms")
    output = output.set_index("timestamp")
    output = output[~output.index.duplicated(keep="first")]
    return output["close"].rename(symbol).astype(float)


def get_price_series(
    ticker: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.Series:
    """
    Fetch the price series from the Unravel API.

    Args:
        ticker (str): The cryptocurrency ticker symbol (e.g., 'BTC')
        API_KEY (str): The API key to use for the request
        start_date (str | None): Start date in 'YYYY-MM-DD' format
        end_date (str | None): End date in 'YYYY-MM-DD' format

    Returns:
        pd.Series: Time series of the risk signal with datetime index
    """

    price_series = fetch_price_binance(f"{ticker}USDT")

    return price_series[start_date:end_date].squeeze().rename(ticker)


def get_multiple_price_series(
    tickers: list[str],
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    """
    Fetch the price series from the Unravel API.

    Args:
        ticker (list[str]): The cryptocurrency ticker symbols (e.g., ['BTC', 'ETH'])
        start_date (str | None): Start date in 'YYYY-MM-DD' format
        end_date (str | None): End date in 'YYYY-MM-DD' format

    Returns:
        pd.DataFrame: Time series of the risk signal with datetime index
    """

    def safe_single_price_series(t: str):
        try:
            price_series = get_price_series(t, start_date, end_date)
            if price_series.empty:
                print(f"Empty price series for {t}")
                return None
            return price_series
        except Exception:
            print(f"Error fetching price series for {t}")
            return None

    results = pmap(safe_single_price_series, tickers, n_jobs=-1)
    return pd.concat(filter_none(results), axis="columns")[start_date:end_date]
