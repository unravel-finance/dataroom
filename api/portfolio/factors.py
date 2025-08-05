import pandas as pd
import requests

from api.constants import BASEAPI


def get_portfolio_factors_historical(
    portfolioId: str,
    tickers: list[str],
    API_KEY: str,
) -> pd.Series:
    url = f"{BASEAPI}/portfolio/factors"
    params = {"id": portfolioId, "tickers": ",".join(tickers)}
    headers = {"X-API-KEY": API_KEY}
    response = requests.get(url, headers=headers, params=params)
    assert (
        response.status_code == 200
    ), f"Error fetching factors for {portfolioId}, response: {response.json()}"

    response = response.json()
    return pd.DataFrame(
        response["data"],
        index=pd.to_datetime(response["index"]),
        columns=response["columns"],
    )
