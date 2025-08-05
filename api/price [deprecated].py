import pandas as pd
import requests

from api.constants import BASEAPI


def get_price_series(
    ticker: str,
    API_KEY: str,
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
    url = f"{BASEAPI}/price"
    params = {"ticker": ticker, "start_date": start_date, "end_date": end_date}
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers, params=params)
    assert (
        response.status_code == 200
    ), f"Error fetching price series for {ticker}, response: {response.json()}"

    response = response.json()
    return pd.Series(response["data"], index=pd.to_datetime(response["index"])).rename(
        ticker
    )
