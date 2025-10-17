# %%

from unravel_client import get_portfolio_factors_historical, get_prices, get_tickers

from analysis.alphalens import factor_analysis
from analysis.utils import get_env

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")
portfolio = "retail_flow"

available_tickers = get_tickers(
    id=portfolio, api_key=UNRAVEL_API_KEY, universe_size="30", exchange=None
)
historical_factors = get_portfolio_factors_historical(
    id=portfolio, tickers=available_tickers, api_key=UNRAVEL_API_KEY
)

underlying = get_prices(tickers=available_tickers, api_key=UNRAVEL_API_KEY)

columns_intersection = historical_factors.columns.intersection(underlying.columns)
factor_analysis(historical_factors[columns_intersection], underlying)

# %%
