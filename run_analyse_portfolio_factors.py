# %%

from finml_utils import get_env

from analysis.alphalens import simplified_factor_analysis
from analysis.price import get_multiple_price_series
from api.portfolio.factors import get_portfolio_factors_historical
from api.portfolio.tickers import get_tickers

UNRAVEL_API_KEY = get_env("UNRAVEL_API_KEY")
portfolio = "momentum_enhanced"

available_tickers = get_tickers(portfolio, UNRAVEL_API_KEY, universe_size="20")
historical_factors = get_portfolio_factors_historical(
    portfolio, available_tickers, UNRAVEL_API_KEY
)

underlying = get_multiple_price_series(available_tickers)


simplified_factor_analysis(historical_factors.loc[:, underlying.columns], underlying)
